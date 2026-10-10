#!/usr/bin/env python3
"""Bounded calibration-only profile-LS vs Bartlett synthetic experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
LAMBDA_MM = 4.0
FS_HZ = 100.0
N_FRAMES = 256
CAL_FRAMES = 128
WARM_PREFIX = 20
M = 8
POS = np.arange(M, dtype=float) - (M - 1) / 2.0
GRID = np.arange(-60.0, 60.0001, 0.25)
NOISE_SIGMA = 10 ** (-35 / 20) / np.sqrt(2.0)
SEEDS = {
    4101: {"theta_true_deg": 17.37, "beta_scale": 1.000, "position_error": [0.0] * M},
    4102: {"theta_true_deg": 17.83, "beta_scale": 1.015, "position_error": [0.0, 0.015, -0.010, 0.020, -0.012, 0.008, -0.018, 0.005]},
    4103: {"theta_true_deg": 18.21, "beta_scale": 0.985, "position_error": [0.0, 0.015, -0.010, 0.020, -0.012, 0.008, -0.018, 0.005]},
}


def steering(theta_deg, positions=POS):
    return np.exp(1j * np.pi * np.asarray(positions) * np.sin(np.deg2rad(theta_deg)))


def generate(seed, cfg):
    rng = np.random.default_rng(seed)
    phase_seed = float(rng.uniform(-np.pi, np.pi))
    time = np.arange(N_FRAMES) / FS_HZ
    q = 0.8 * np.sin(2 * np.pi * 3 * time + phase_seed) + 0.2 * np.sin(
        2 * np.pi * 5 * time + 0.43 - 0.2 * phase_seed
    )
    theta = float(cfg["theta_true_deg"])
    actual_a = steering(theta, POS + np.asarray(cfg["position_error"], dtype=float))
    phase = 4 * np.pi / LAMBDA_MM * q * float(cfg["beta_scale"]) * np.cos(np.deg2rad(theta))
    source = np.exp(1j * phase)[:, None] * actual_a[None, :]
    iq = source + NOISE_SIGMA * (rng.standard_normal(source.shape) + 1j * rng.standard_normal(source.shape))
    return iq, q


def bartlett_power(cal_iq, theta_deg):
    nominal = steering(theta_deg)
    covariance = cal_iq.T @ cal_iq.conj() / len(cal_iq)
    return float(np.maximum((nominal.conj() @ covariance @ nominal).real / M**2, 0.0))


def bartlett_angle(cal_iq):
    power = np.asarray([bartlett_power(cal_iq, theta) for theta in GRID])
    index = int(np.argmax(power))
    return float(GRID[index]), float(power[index]), power


def profile_objective(cal_iq, theta_deg):
    nominal = steering(theta_deg)
    coeff = cal_iq @ nominal.conj() / np.vdot(nominal, nominal)
    residual = cal_iq - coeff[:, None] * nominal[None, :]
    denom = max(float(np.vdot(cal_iq, cal_iq).real), 1e-30)
    return float(np.vdot(residual, residual).real / denom)


def profile_angle(cal_iq, bartlett_theta):
    lo = max(-60.0, bartlett_theta - 1.5)
    hi = min(60.0, bartlett_theta + 1.5)
    candidates = np.arange(lo, hi + 0.0001, 0.01)
    objective = np.asarray([profile_objective(cal_iq, theta) for theta in candidates])
    index = int(np.argmin(objective))
    return float(candidates[index]), float(objective[index]), float(objective.min()), float(lo), float(hi)


def estimate_test(iq, theta_hat, start_index):
    test = iq[CAL_FRAMES:]
    nominal = steering(theta_hat)
    extraction = test @ nominal.conj() / M
    gain = float(np.linalg.norm(nominal.conj() / M))
    floor = 5.0 * NOISE_SIGMA * gain
    min_abs = float(np.abs(extraction).min())
    result = {"theta_hat_deg": theta_hat, "min_test_abs": min_abs, "amplitude_floor": floor, "covered": False, "failure": None}
    if min_abs < floor:
        result["failure"] = "test_amplitude_guard"
        return result, None
    phase = np.unwrap(np.angle(extraction * np.conj(extraction[start_index])))
    q_hat = phase * LAMBDA_MM / (4 * np.pi * np.cos(np.deg2rad(theta_hat)))
    result["covered"] = bool(np.all(np.isfinite(q_hat)))
    if not result["covered"]:
        result["failure"] = "nonfinite"
    return result, q_hat


def score(q_hat, truth, start_index, full_start=None):
    if q_hat is None:
        return {"rmse_mm": None, "dynamic_proxy_delta_rmse_mm": None, "score_samples": 0}
    q_hat = q_hat - q_hat[start_index]
    truth_ref = truth[CAL_FRAMES + start_index]
    target = truth[CAL_FRAMES + start_index:] - truth_ref
    error = q_hat[start_index:] - target
    delta_error = np.diff(q_hat[start_index:]) - np.diff(target)
    return {
        "rmse_mm": float(np.sqrt(np.mean(error**2))),
        "dynamic_proxy_delta_rmse_mm": float(np.sqrt(np.mean(delta_error**2))),
        "score_samples": int(error.size),
        "score_start_frame": int(CAL_FRAMES + start_index),
    }


def run_route(iq, truth, method, init):
    cal = iq[:CAL_FRAMES]
    theta_b, bartlett_peak, _ = bartlett_angle(cal)
    if method == "bartlett":
        theta_hat, objective = theta_b, None
    elif method == "profile_ls":
        theta_hat, objective, _, bound_lo, bound_hi = profile_angle(cal, theta_b)
    else:
        raise ValueError(method)
    start = 0 if init == "cold" else WARM_PREFIX
    estimate_result, q_hat = estimate_test(iq, theta_hat, start)
    if estimate_result["covered"]:
        scored = score(q_hat, truth, start)
        paired = score(q_hat, truth, WARM_PREFIX)
    else:
        scored = {"rmse_mm": None, "dynamic_proxy_delta_rmse_mm": None, "score_samples": 0, "score_start_frame": CAL_FRAMES + start}
        paired = {"rmse_mm": None, "dynamic_proxy_delta_rmse_mm": None, "score_samples": 0, "score_start_frame": CAL_FRAMES + WARM_PREFIX}
    row = {"method": method, "init": init, "bartlett_theta_deg": theta_b, "bartlett_peak": bartlett_peak, "theta_hat_deg": theta_hat, "profile_objective": objective, "score_start_frame": CAL_FRAMES + start, "guard": estimate_result, "metrics": scored, "paired_metrics_start_frame_148": paired}
    if method == "profile_ls":
        row["profile_bounds_deg"] = [bound_lo, bound_hi]
    return row


def main():
    rows = []
    for seed, cfg in SEEDS.items():
        iq, truth = generate(seed, cfg)
        for method in ("bartlett", "profile_ls"):
            for init in ("cold", "warm"):
                rows.append({"seed": seed, "config": cfg, "result": run_route(iq, truth, method, init)})
    payload = {
        "schema": "new_synthetic_heldout_profile_ls_vs_bartlett",
        "status": "NEW_SYNTHETIC_HELD_OUT_EXPERIMENT",
        "historical_400_402_recovery": False,
        "truth_free_geometry": True,
        "truth_access": "post_run_scoring_only",
        "seeds": sorted(SEEDS),
        "rows": rows,
        "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    out = ROOT / "results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"seeds": sorted(SEEDS), "rows": len(rows), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
