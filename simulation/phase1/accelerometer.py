from dataclasses import dataclass

import numpy as np

from .config import Phase1Config
from .truth import TruthSignal


@dataclass(frozen=True)
class AccelerometerObservation:
    true_mps2: np.ndarray
    measured_mps2: np.ndarray
    bias_mps2: np.ndarray
    noise_mps2: np.ndarray


def _apply_sync_error(truth: TruthSignal, sync_error_s: float) -> np.ndarray:
    if sync_error_s == 0.0:
        return truth.a_mps2
    shifted_t = truth.t - sync_error_s
    return np.interp(shifted_t, truth.t, truth.a_mps2, left=truth.a_mps2[0], right=truth.a_mps2[-1])


def simulate_accelerometer(truth: TruthSignal, config: Phase1Config) -> AccelerometerObservation:
    """Generate measured acceleration with white noise, constant bias, and linear drift."""

    synced_true = _apply_sync_error(truth, config.accel_sync_error_s)
    rng = np.random.default_rng(config.seed + 4)
    noise = rng.normal(0.0, config.accel_noise_std_mps2, size=truth.t.shape)
    drift = config.accel_drift_mps2 * (truth.t / truth.t[-1]) if truth.t.size > 1 else 0.0
    bias = np.full_like(truth.t, config.accel_bias_mps2) + drift
    measured = synced_true + bias + noise

    return AccelerometerObservation(
        true_mps2=truth.a_mps2,
        measured_mps2=measured,
        bias_mps2=bias,
        noise_mps2=noise,
    )
