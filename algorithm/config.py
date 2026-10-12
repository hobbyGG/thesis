from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmConfig:
    """Parameters used by the retained structural estimator."""

    carrier_frequency_hz: float = 77.0e9
    # The retained acquisition profile emits four MIMO loops per frame at about 885 Hz.
    # ``run`` still replaces this with the measured package rate.
    sample_rate_hz: float = 1.0 / 1.130134e-3
    process_noise_intensity: float = 5.0e4
    initial_state_variance: float = 25.0
    initial_rate_variance: float = 400.0
    initial_measurement_variance: float = 9.0
    min_measurement_variance: float = 1.0e-4
    max_measurement_variance: float = 25.0
    adaptive_r_forgetting: float = 0.95
    cold_start_duration_s: float = 0.20
    cold_start_r_mode: str = "residual"
    radar_mount: str = "downward"

    # Conditional beta correction.  AoA geometry remains the default; ADXL
    # matching is allowed to replace only targets that pass all three gates.
    beta_snr_min_db: float = 15.0
    beta_adxl_excitation_min_m: float = 5.0e-6
    beta_adxl_excitation_duration_s: float = 0.10
    beta_discrepancy_min_relative: float = 0.01
    beta_min_discrepant_targets: int = 2
    beta_match_min_sxx: float = 1.0e-24
    beta_min: float = 0.5
    beta_max: float = 2.0

    def wavelength_m(self) -> float:
        return 299_792_458.0 / self.carrier_frequency_hz
