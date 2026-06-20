from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026Config:
    """Parameters used by the Ma 2026 reproduction and simulation adapter."""

    beta_grid_min: float = 0.5
    beta_grid_max: float = 2.0
    beta_grid_step: float = 0.001
    highpass_cutoff_hz: float = 0.5
    conversion_band_low_hz: float = 0.5
    conversion_band_high_hz: float = 30.0
    alpha_highpass_cutoff_hz: float = 0.5
    alpha_band_low_hz: float = 0.5
    alpha_band_high_hz: float = 3.0
    q_exponent_min: int = 0
    q_exponent_max: int = 20
    measurement_noise_r: float = 1.0
    calibration_max_samples: int = 1200
    max_rangebin_targets: int = 5
    rangebin_threshold_ratio: float = 0.1


def beta_grid(config: Ma2026Config = Ma2026Config()) -> np.ndarray:
    step = float(config.beta_grid_step)
    if step <= 0.0:
        raise ValueError("beta_grid_step must be positive")
    count = int(round((float(config.beta_grid_max) - float(config.beta_grid_min)) / step)) + 1
    return float(config.beta_grid_min) + step * np.arange(count, dtype=float)


def q_grid(config: Ma2026Config = Ma2026Config()) -> np.ndarray:
    exponents = np.arange(int(config.q_exponent_min), int(config.q_exponent_max) + 1, dtype=float)
    return 10.0**exponents
