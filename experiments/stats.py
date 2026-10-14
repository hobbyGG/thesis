"""Paired statistics over simulation cases."""

from __future__ import annotations

import itertools

import numpy as np

# RMSE values are clipped to this range before forming ratios; a failed run
# (non-finite estimate) is scored at the cap.
CAP_UM = 1.0e4
FLOOR_UM = 1.0e-2


def clipped(values_um) -> np.ndarray:
    values = np.asarray(values_um, dtype=float)
    return np.clip(np.where(np.isfinite(values), values, CAP_UM), FLOOR_UM, CAP_UM)


def sign_flip_p(x, *, draws: int = 100_000, seed: int = 0) -> float:
    """Two-sided sign-flip test of mean(x) = 0 (exact for n <= 12)."""
    x = np.asarray(x, dtype=float)
    observed = abs(x.mean())
    if x.size <= 12:
        signs = np.asarray(list(itertools.product((-1.0, 1.0), repeat=x.size)))
        return float(np.mean(np.abs(signs @ x) / x.size >= observed - 1.0e-12))
    flips = np.random.default_rng(seed).choice((-1.0, 1.0), size=(draws, x.size))
    return float((1 + np.sum(np.abs(flips @ x) / x.size >= observed - 1.0e-12)) / (1 + draws))


def bootstrap_mean_ci(x, *, draws: int = 10_000, seed: int = 0) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    index = np.random.default_rng(seed).integers(0, x.size, size=(draws, x.size))
    low, high = np.percentile(x[index].mean(axis=1), [2.5, 97.5])
    return float(low), float(high)


def paired_gain(method_um, baseline_um) -> dict:
    """Reduction of the geometric-mean RMSE ratio of a method against a baseline.

    gain = 1 - exp(mean(log(method / baseline))): positive when the method is
    better.  The interval is a bootstrap over cases, p a sign-flip test on the
    log ratios.
    """
    log_ratio = np.log(clipped(method_um) / clipped(baseline_um))
    low, high = bootstrap_mean_ci(log_ratio)
    return {
        "n": int(log_ratio.size),
        "gain": float(1.0 - np.exp(log_ratio.mean())),
        "gain_low": float(1.0 - np.exp(high)),
        "gain_high": float(1.0 - np.exp(low)),
        "p": sign_flip_p(log_ratio),
    }


def wilson_interval(failures: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    p = failures / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


def median_iqr(values_um) -> tuple[float, float, float]:
    low, middle, high = np.percentile(clipped(values_um), [25, 50, 75])
    return float(middle), float(low), float(high)
