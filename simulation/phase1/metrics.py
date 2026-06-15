from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FeasibilityGate:
    name: str
    metric: str
    max_value: float


def _valid_pair(estimate, truth):
    estimate_arr = np.asarray(estimate, dtype=float)
    truth_arr = np.asarray(truth, dtype=float)
    valid = np.isfinite(estimate_arr) & np.isfinite(truth_arr)
    return estimate_arr[valid], truth_arr[valid]


def displacement_metrics(estimate_m, truth_m):
    estimate, truth = _valid_pair(estimate_m, truth_m)
    if estimate.size == 0:
        return {"rmse_mm": float("nan"), "mae_mm": float("nan"), "max_error_mm": float("nan")}
    error_mm = (estimate - truth) * 1.0e3
    return {
        "rmse_mm": float(np.sqrt(np.mean(error_mm**2))),
        "mae_mm": float(np.mean(np.abs(error_mm))),
        "max_error_mm": float(np.max(np.abs(error_mm))),
    }


def phase_rmse_rad(estimate_rad, truth_rad):
    estimate, truth = _valid_pair(estimate_rad, truth_rad)
    if estimate.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((estimate - truth) ** 2)))


def interval_mask(t, start_s, end_s):
    arr = np.asarray(t, dtype=float)
    return (arr >= float(start_s)) & (arr <= float(end_s))


def convergence_time_s(t, estimate, truth, relative_tol=0.05, sustain_samples=20):
    t_arr = np.asarray(t, dtype=float)
    est = np.asarray(estimate, dtype=float)
    ref = np.asarray(truth, dtype=float)
    denom = np.maximum(np.abs(ref), 1.0e-12)
    ok = np.abs(est) / denom <= float(relative_tol)
    required = int(sustain_samples)
    if required <= 1:
        matches = np.flatnonzero(ok)
        return float(t_arr[matches[0]]) if matches.size else float("nan")
    for idx in range(0, ok.size - required + 1):
        if np.all(ok[idx : idx + required]):
            return float(t_arr[idx])
    return float("nan")


def evaluate_gate(metrics, gate):
    value = float(metrics.get(gate.metric, float("nan")))
    passed = np.isfinite(value) and value <= float(gate.max_value)
    return {
        "name": gate.name,
        "metric": gate.metric,
        "value": value,
        "max_value": gate.max_value,
        "passed": bool(passed),
    }
