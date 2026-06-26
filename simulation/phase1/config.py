from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass(frozen=True)
class Phase1Config:
    """Configuration for the first-stage algorithm-level simulation.

    ``sample_rate_hz`` is the slow-time frame/phase/Kalman rate. It is not the
    MHz-level ADC fast-time sampling rate used inside a chirp.
    """

    duration_s: float = 5.0
    sample_rate_hz: float = 100.0
    seed: int = 2026

    nominal_frequencies_hz: Sequence[float] = (2.0, 5.0, 12.0)
    frequency_jitter_hz: float = 1.0
    component_amplitudes_mm: Sequence[float] = (0.08, 0.04, 0.02)
    motion_profile: str = "multifrequency"
    truth_peak_displacement_mm: Optional[float] = None
    quiet_start_duration_s: float = 0.0
    vehicle_event_center_s: float = 2.0
    vehicle_event_width_s: float = 0.4

    carrier_frequency_hz: float = 77.0e9
    adc_sample_rate_hz: float = 6.0e6
    chirp_duration_s: float = 60.0e-6
    chirps_per_frame: int = 4
    adc_samples_per_chirp: int = 256
    num_targets: int = 5
    target_angles_deg: Sequence[float] = (10.0, 25.0, 40.0, 55.0, 70.0)
    target_snr_db: Sequence[float] = (25.0, 20.0, 15.0, 10.0, 5.0)
    target_amplitudes: Sequence[float] = field(default_factory=lambda: (1.0, 0.9, 0.8, 0.7, 0.6))
    target_range_bins: Sequence[int] = ()

    accel_noise_std_mps2: float = 0.02
    accel_bias_mps2: float = 0.0
    accel_drift_mps2: float = 0.0
    accel_sync_error_s: float = 0.0

    measured_bridge_tdms_path: str = "datafile/20250320test12.tdms"
    measured_bridge_laser_group: str = "卡3激光位移"
    measured_bridge_laser_channel: str = "3-4"
    measured_bridge_acceleration_group: str = "卡1梁振动"
    measured_bridge_acceleration_channel: str = "1-5"
    measured_bridge_event_window_s: tuple[float, float] = (15.33, 19.33)
    measured_bridge_analysis_band_hz: tuple[float, float] = (0.2, 10.0)
    measured_bridge_powerline_hz: Sequence[float] = (50.0, 100.0, 150.0)
    measured_bridge_powerline_half_width_hz: float = 1.0
    measured_bridge_laser_truth_preprocessing: str = "none"
    measured_bridge_laser_scale_m_per_v: float = 1.0e-3
    measured_bridge_acceleration_source: str = "tdms"
    measured_bridge_derived_accel_preprocessing: str = "bandpass_notch"
    measured_bridge_derived_accel_band_hz: tuple[float, float] = (0.2, 30.0)
    measured_bridge_derived_accel_noise_std_mps2: float = 0.02
    measured_bridge_accel_scale_mps2_per_v: float = 1.0
    measured_bridge_accel_sign: float = -1.0
    measured_bridge_time_shift_s: float = -0.01

    scenario_name: str = "nominal_multifrequency"
    cold_start_duration_s: float = 0.05

    process_noise_intensity: float = 5.0
    calibrated_process_noise_intensity: Optional[float] = None
    calibrated_q_candidates: Sequence[float] = (
        1.0,
        5.0,
        10.0,
        50.0,
        100.0,
        500.0,
        1.0e3,
        5.0e3,
        1.0e4,
        5.0e4,
        1.0e5,
        5.0e5,
        1.0e6,
    )
    calibrated_q_tie_break_value: float = 5.0e4
    initial_state_variance: float = 25.0
    initial_rate_variance: float = 400.0
    initial_measurement_variance: float = 9.0
    min_measurement_variance: float = 1.0e-4
    max_measurement_variance: float = 25.0
    adaptive_r_forgetting: float = 0.95

    kappa_window_samples: int = 80
    kappa_update_start_s: float = 0.25
    kappa_bootstrap_prior_weight: float = 500.0
    kappa_confidence_initial_variance: float = 0.04
    kappa_confidence_min_variance: float = 1.0e-6
    kappa_confidence_max_variance: float = 0.25
    kappa_confidence_forgetting: float = 0.90
    kappa_min_abs: float = 0.05
    kappa_max_abs: float = 1.2

    aoa_error_deg: float = 0.0
    frontend_aoa_error_bias_deg: Optional[float] = None
    frontend_aoa_error_std_deg: float = 0.0

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
