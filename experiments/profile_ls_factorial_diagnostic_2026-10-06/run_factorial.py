#!/usr/bin/env python3
"""Matched factor diagnostic using the prior bounded profile-LS implementation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

BASE = Path(__file__).resolve().parents[1] / "profile_ls_synthetic_heldout_2026-10-06"
sys.path.insert(0, str(BASE))
import run_experiment as base  # noqa: E402

ROOT = Path(__file__).resolve().parent
SEEDS = [4201, 4202, 4203]
THETA_TRUE = 17.37
POSITION_ERROR = np.array([0.0, 0.015, -0.010, 0.020, -0.012, 0.008, -0.018, 0.005])
FACTORS = {
    "offgrid_only": {"beta_scale": 1.0, "position_error": np.zeros(base.M)},
    "offgrid_beta": {"beta_scale": 1.015, "position_error": np.zeros(base.M)},
    "offgrid_array": {"beta_scale": 1.0, "position_error": POSITION_ERROR},
}


def common_random_block(seed):
    rng = np.random.default_rng(seed)
    phase_seed = float(rng.uniform(-np.pi, np.pi))
    time = np.arange(base.N_FRAMES) / base.FS_HZ
    q = 0.8 * np.sin(2 * np.pi * 3 * time + phase_seed) + 0.2 * np.sin(2 * np.pi * 5 * time + 0.43 - 0.2 * phase_seed)
    noise = rng.standard_normal((base.N_FRAMES, base.M)) + 1j * rng.standard_normal((base.N_FRAMES, base.M))
    return phase_seed, q, noise


def generate_factor(q, noise, factor):
    cfg = FACTORS[factor]
    actual_a = base.steering(THETA_TRUE, base.POS + cfg["position_error"])
    phase = 4 * np.pi / base.LAMBDA_MM * q * cfg["beta_scale"] * np.cos(np.deg2rad(THETA_TRUE))
    source = np.exp(1j * phase)[:, None] * actual_a[None, :]
    return source + base.NOISE_SIGMA * noise


def metrics(iq, q, method, init, beta_scale):
    cal = iq[: base.CAL_FRAMES]
    theta_b, peak, _ = base.bartlett_angle(cal)
    if method == "bartlett":
        theta_hat, objective = theta_b, None
    else:
        theta_hat, objective, _, lo, hi = base.profile_angle(cal, theta_b)
    estimator_start = 0 if init == "cold" else base.WARM_PREFIX
    score_start = base.WARM_PREFIX
    guard, q_hat = base.estimate_test(iq, theta_hat, estimator_start)
    row = {"method": method, "init": init, "theta_bartlett_deg": theta_b, "theta_hat_deg": theta_hat, "angle_error_deg": theta_hat - THETA_TRUE, "bartlett_peak": peak, "profile_objective": objective, "guard": guard, "estimator_reference_frame": base.CAL_FRAMES + estimator_start, "score_start_frame": base.CAL_FRAMES + score_start}
    if method == "profile_ls":
        row["profile_bounds_deg"] = [max(-60.0, theta_b - 1.5), min(60.0, theta_b + 1.5)]
    if not guard["covered"]:
        row.update(metrics={"rmse_mm": None, "dynamic_proxy_delta_rmse_mm": None, "phase_bias_rad": None, "phase_rmse_rad": None, "score_samples": 0}, conversion_ratio=None)
        return row
    # Rebase both routes at frame 148 so cold and legal warm routes share a
    # paired scoring window while retaining their distinct estimator reference.
    q_hat = q_hat - q_hat[score_start]
    target = q[score_start + base.CAL_FRAMES:] - q[score_start + base.CAL_FRAMES]
    error = q_hat[score_start:] - target
    delta_error = np.diff(q_hat[score_start:]) - np.diff(target)
    true_phase = 4 * np.pi / base.LAMBDA_MM * beta_scale * np.cos(np.deg2rad(THETA_TRUE)) * target
    phase_hat = 4 * np.pi / base.LAMBDA_MM * np.cos(np.deg2rad(theta_hat)) * q_hat[score_start:]
    phase_error = phase_hat - true_phase
    ratio = beta_scale * np.cos(np.deg2rad(THETA_TRUE)) / np.cos(np.deg2rad(theta_hat))
    row["conversion_ratio"] = float(ratio)
    row["metrics"] = {"rmse_mm": float(np.sqrt(np.mean(error**2))), "dynamic_proxy_delta_rmse_mm": float(np.sqrt(np.mean(delta_error**2))), "phase_bias_rad": float(np.mean(phase_error)), "phase_rmse_rad": float(np.sqrt(np.mean(phase_error**2))), "score_samples": int(error.size)}
    return row


def main():
    rows = []
    for seed in SEEDS:
        phase_seed, q, noise = common_random_block(seed)
        for factor in FACTORS:
            iq = generate_factor(q, noise, factor)
            for method in ("bartlett", "profile_ls"):
                for init in ("cold", "warm"):
                    row = metrics(iq, q, method, init, FACTORS[factor]["beta_scale"])
                    rows.append({"seed": seed, "factor": factor, "phase_seed": phase_seed, "result": row})
    payload = {"schema": "profile_ls_matched_factorial_diagnostic", "status": "NEW_SYNTHETIC_MATCHED_FACTORIAL", "historical_400_402_recovery": False, "truth_free_geometry": True, "truth_access": "post_run_scoring_only", "seeds": SEEDS, "factors": {k: {"beta_scale": float(v["beta_scale"]), "position_error": v["position_error"].tolist()} for k, v in FACTORS.items()}, "rows": rows, "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest(), "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "dependency_sha256": hashlib.sha256((BASE / "run_experiment.py").read_bytes()).hexdigest()}
    out = ROOT / "results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"rows": len(rows), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
