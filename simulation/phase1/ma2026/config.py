from dataclasses import dataclass

import numpy as np

@dataclass(frozen=True)
class Ma2026Config:
    """Parameters used by the Ma 2026 reproduction and simulation adapter."""

    alpha_highpass_cutoff_hz: float = 0.5
    alpha_band_low_hz: float = 0.5
    alpha_band_high_hz: float = 3.0
    q_exponent_min: int = 0
    q_exponent_max: int = 20
    measurement_noise_r: float = 1.0
    calibration_max_samples: int = 1200
    max_rangebin_targets: int = 5
    rangebin_threshold_ratio: float = 0.1


def q_grid(config: Ma2026Config = Ma2026Config()) -> np.ndarray:
    exponents = np.arange(int(config.q_exponent_min), int(config.q_exponent_max) + 1, dtype=float)
    return 10.0**exponents
