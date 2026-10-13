from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmConfig:
    """Parameters used by the retained structural estimator."""

    carrier_frequency_hz: float = 77.0e9
    # The retained acquisition profile emits four MIMO loops per frame at 500 Hz.
    # ``run`` still replaces this with the measured package rate.
    sample_rate_hz: float = 500.0
    process_noise_intensity: float = 5.0e4
    initial_state_variance: float = 25.0
    initial_rate_variance: float = 400.0
    initial_measurement_variance: float = 9.0
    min_measurement_variance: float = 1.0e-4
    max_measurement_variance: float = 25.0
    adaptive_r_forgetting: float = 0.95
    cold_start_duration_s: float = 0.20
    cold_start_r_mode: str = "residual"

    def wavelength_m(self) -> float:
        return 299_792_458.0 / self.carrier_frequency_hz
