from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Phase1Config:
    """Configuration for the first-stage algorithm-level simulation."""

    duration_s: float = 5.0
    sample_rate_hz: float = 1000.0
    seed: int = 2026

    nominal_frequencies_hz: Sequence[float] = (20.0, 40.0, 60.0)
    frequency_jitter_hz: float = 10.0
    component_amplitudes_mm: Sequence[float] = (0.08, 0.04, 0.02)

    carrier_frequency_hz: float = 77.0e9
    num_targets: int = 5
    target_angles_deg: Sequence[float] = (10.0, 25.0, 40.0, 55.0, 70.0)
    target_snr_db: Sequence[float] = (25.0, 20.0, 15.0, 10.0, 5.0)
    target_amplitudes: Sequence[float] = field(default_factory=lambda: (1.0, 0.9, 0.8, 0.7, 0.6))

    accel_noise_std_mps2: float = 0.02
    accel_bias_mps2: float = 0.0
    accel_drift_mps2: float = 0.0
    accel_sync_error_s: float = 0.0

    scenario_name: str = "nominal_multifrequency"

    process_noise_intensity: float = 5.0
    initial_state_variance: float = 25.0
    initial_rate_variance: float = 25.0
    initial_measurement_variance: float = 9.0
    min_measurement_variance: float = 1.0e-4
    max_measurement_variance: float = 25.0
    adaptive_r_forgetting: float = 0.95

    kappa_window_samples: int = 80
    kappa_update_start_s: float = 0.25
    kappa_min_abs: float = 0.05
    kappa_max_abs: float = 1.2

    aoa_error_deg: float = 0.0

    degraded_target_indices: Sequence[int] = ()
    degradation_start_s: float = 2.0
    degradation_end_s: float = 3.2
    degradation_snr_drop_db: float = 20.0

    dropout_target_indices: Sequence[int] = ()
    dropout_start_s: float = 2.0
    dropout_end_s: float = 3.2

    enable_mixed_scatterer_target: bool = False
    mixed_target_index: int = 0
    mixed_scatterer_kappas: Sequence[float] = (0.95, 0.35)
    mixed_scatterer_amplitudes: Sequence[float] = (0.7, 0.6)
    mixed_scatterer_biases_rad: Sequence[float] = (0.0, 1.2)

    def wavelength_m(self) -> float:
        return 299_792_458.0 / self.carrier_frequency_hz
