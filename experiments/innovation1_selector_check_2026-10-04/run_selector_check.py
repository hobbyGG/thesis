#!/usr/bin/env python3
"""Truth-free same-range route selector scratch check; NumPy only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
V2_ROOT = ROOT.parent / "same_range_merge_mechanism_v2"
LAMBDA_MM, FS, N, M, CAL = 4.0, 100.0, 256, 8, 128
NOISE_SIGMA = 10 ** (-35 / 20) / np.sqrt(2)
GRID = np.arange(-60, 60.001, 0.25)
POS = np.arange(M) - (M - 1) / 2
CASES = {
    "close_benign": ([25, 29], [1, 0.8], [0.15, -0.30]),
    "separated_benign": ([-10, 45], [1, 0.8], [0.15, -0.30]),
    "separated_unequal": ([-10, 45], [1, 0.5], [0.15, -0.30]),
    "close_destructive": ([25, 29], [1, 1], [0, np.pi]),
    "coincident_cancel": ([27, 27], [1, 1], [0, np.pi]),
    "symmetric_control": ([-25, 25], [1, 0.8], [0.15, -0.30]),
}


def steering(angles):
    return np.exp(1j * np.pi * POS[:, None] * np.sin(np.deg2rad(np.atleast_1d(angles)))[None, :])


DICT = steering(GRID)


def generate(case_name, seed):
    """Generator truth/data pair; truth is not passed to selector()."""
    angles, amps, phases = CASES[case_name]
    rng = np.random.default_rng(seed)
    p = rng.uniform(-np.pi, np.pi)
    t = np.arange(N) / FS
    q = 0.8 * np.sin(2 * np.pi * 3 * t + p) + 0.2 * np.sin(2 * np.pi * 5 * t + 0.43 - 0.2 * p)
    c = np.cos(np.deg2rad(angles))
    sources = np.array(amps)[None, :] * np.exp(
        1j * (np.array(phases)[None, :] + 4 * np.pi / LAMBDA_MM * q[:, None] * c[None, :])
    )
    z = sources @ steering(angles).T
    z += NOISE_SIGMA * (rng.standard_normal(z.shape) + 1j * rng.standard_normal(z.shape))
    return z, q


def _prominence(power, index):
    """Small deterministic prominence calculation for isolated local peaks."""
    height = power[index]
    left = index - 1
    while left > 0 and power[left] <= height:
        left -= 1
    right = index + 1
    last = len(power) - 1
    while right < last and power[right] <= height:
        right += 1
    left_base = np.min(power[left : index + 1])
    right_base = np.min(power[index : right + 1])
    return float(height - max(left_base, right_base))


def geometry(cal_iq):
    # Same covariance sign and threshold constants as corrected v2.
    R = cal_iq.T @ cal_iq.conj() / len(cal_iq)
    power = np.maximum(np.einsum("mg,mn,ng->g", DICT.conj(), R, DICT).real / M**2, 0)
    local = [
        i for i in range(1, len(power) - 1)
        if power[i] > power[i - 1] and power[i] >= power[i + 1]
    ]
    prominence_floor = max(power.max() * 0.01, 1e-15)
    candidates = [i for i in local if _prominence(power, i) >= prominence_floor]
    # scipy.find_peaks(distance=48) keeps the highest peaks first.
    candidates.sort(key=lambda i: power[i], reverse=True)
    kept = []
    for index in candidates:
        if all(abs(index - previous) >= 48 for previous in kept):
            kept.append(index)
    kept.sort(key=lambda i: power[i], reverse=True)
    if not kept:
        return [], power
    kept = [i for i in kept if power[i] >= 0.18 * power[kept[0]]][:2]
    return GRID[kept].tolist(), power


def route_from_geometry(iq, angles, mode):
    """Route estimation only; no truth, scene metadata, or score is accepted."""
    cal, test = iq[:CAL], iq[CAL:]
    out = {"mode": mode, "angles_deg": angles, "covered": False, "failure": None}
    if not angles:
        return dict(out, failure="no_calibration_angle_peak"), None
    if mode == "split_ls":
        if len(angles) < 2:
            return dict(out, failure="fewer_than_two_calibration_angle_peaks"), None
        A = steering(angles)
        condition = float(np.linalg.cond(A))
        out["steering_condition"] = condition
        if condition > 20:
            return dict(out, failure="ill_conditioned_split"), None
        E = np.linalg.pinv(A).T
        used = np.array(angles)
    elif mode == "merge":
        E = steering([angles[0]]).conj() / M
        used = np.array([angles[0]])
    else:
        raise ValueError(mode)
    ycal, y = cal @ E, test @ E
    gains = np.linalg.norm(E, axis=0)
    floor = 5 * NOISE_SIGMA * gains
    out["min_test_abs"] = np.abs(y).min(axis=0).tolist()
    out["noise_gain"] = gains.tolist()
    out["amplitude_floor"] = floor.tolist()
    if np.any(np.abs(y).min(axis=0) < floor):
        return dict(out, failure="test_amplitude_guard"), None
    c = np.cos(np.deg2rad(used))
    if np.any(c <= 0.05):
        return dict(out, failure="geometry_guard"), None
    phase = np.unwrap(np.angle(y * np.conj(y[0, :])[None, :]), axis=0)
    qs = phase * LAMBDA_MM / (4 * np.pi * c[None, :])
    weights = np.mean(np.abs(ycal) ** 2, axis=0)
    weights = weights / weights.sum()
    qhat = qs @ weights
    out["weights"] = weights.tolist()
    out["covered"] = bool(np.all(np.isfinite(qhat)))
    if not out["covered"]:
        out["failure"] = "nonfinite"
    return out, qhat


def selector(iq):
    """Truth-free selector: calibration IQ and frozen constants only."""
    angles, power = geometry(iq[:CAL])
    decision = {
        "selected_route": None,
        "angles_deg": angles,
        "candidate_count": len(angles),
        "selector_failure": None,
    }
    if not angles:
        decision["selector_failure"] = "no_calibration_angle_peak"
        return decision, None, None
    if len(angles) == 1:
        mode = "merge"
    else:
        condition = float(np.linalg.cond(steering(angles)))
        decision["steering_condition"] = condition
        if condition > 20:
            decision["selector_failure"] = "ill_conditioned_split"
            return decision, None, None
        mode = "split_ls"
    decision["selected_route"] = mode
    route, qhat = route_from_geometry(iq, angles, mode)
    if not route["covered"]:
        decision["selector_failure"] = route["failure"]
    return decision, route, qhat


def score(route, qhat, truth):
    """Post-run only: truth enters here, after route selection and estimation."""
    result = dict(route)
    if not route["covered"]:
        result.update(rmse_mm=None, max_abs_error_mm=None, high_error_gt_0p01mm=None)
        return result
    reference = truth[CAL:] - truth[CAL]
    error = qhat - reference
    rmse = float(np.sqrt(np.mean(error**2)))
    result.update(
        rmse_mm=rmse,
        max_abs_error_mm=float(np.max(np.abs(error))),
        high_error_gt_0p01mm=bool(rmse > 0.01),
    )
    return result


def unit_checks():
    theta = 25.0
    t = np.arange(N) / FS
    q = 0.3 * np.sin(2 * np.pi * 3 * t)
    x = np.exp(1j * 4 * np.pi / LAMBDA_MM * q * np.cos(np.deg2rad(theta)))[:, None] @ steering([theta]).T
    angles, power = geometry(x[:CAL])
    assert angles and angles[0] == theta, (theta, angles)
    direct = np.mean(np.abs(x[:CAL] @ DICT.conj() / M) ** 2, axis=0)
    covariance_error = float(np.max(np.abs(direct - power)))
    assert covariance_error < 1e-12, covariance_error
    decision, route, qhat = selector(x)
    assert decision["selected_route"] == "merge" and route["covered"]
    rmse = float(np.sqrt(np.mean((qhat - (q[CAL:] - q[CAL])) ** 2)))
    assert rmse < 1e-12, rmse
    return {
        "positive_angle_check_deg": angles[0],
        "covariance_vs_direct_max_abs": covariance_error,
        "single_source_noiseless_rmse_mm": rmse,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=212)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    checks = unit_checks()
    rows = []
    for case_name in CASES:
        iq, truth = generate(case_name, args.seed)
        angles, _ = geometry(iq[:CAL])
        independent = {}
        for mode in ("merge", "split_ls"):
            route, qhat = route_from_geometry(iq, angles, mode)
            independent[mode] = score(route, qhat, truth)
        decision, selected_route, selected_qhat = selector(iq)
        if selected_route is None:
            selected = {
                "mode": None,
                "covered": False,
                "failure": decision["selector_failure"],
                "rmse_mm": None,
                "max_abs_error_mm": None,
                "high_error_gt_0p01mm": None,
            }
        else:
            selected = score(selected_route, selected_qhat, truth)
        rows.append({
            "case": case_name,
            "seed": args.seed,
            "selector": decision,
            "selected": selected,
            "independent": independent,
        })
    payload = {
        "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "one new seed truth-free same-range route selector check",
        "seed": args.seed,
        "truth_free_selector": True,
        "truth_access_stage": "post-run score only",
        "constants": {"lambda_mm": LAMBDA_MM, "fs_hz": FS, "samples": N, "sensors": M, "cal_samples": CAL, "noise_sigma": NOISE_SIGMA},
        "unit_checks": checks,
        "rows": rows,
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"unit_checks": checks, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
