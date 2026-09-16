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
    frontend_num_tx: int = 3
    frontend_num_rx: int = 4
    # IWR1843-like azimuth frontend: 3TX/4RX hardware, 8 virtual azimuth
    # channels used for the 1-D azimuth Angle FFT in Phase 1.
    frontend_num_virtual_rx: int = 8
    frontend_num_angle_bins: int = 64
    frontend_angle_window: str = "hann"
    # Direct target-angle estimator.  ``fft`` is retained as the legacy
    # baseline; the new default performs a local, continuous angle fit after
    # FFT range/angle gating and does not run any downstream beta adaptation.
    frontend_angle_estimation_method: str = "local_music_ml"
    frontend_angle_search_half_width_u: float = 0.12
    frontend_angle_music_grid_size: int = 129
    frontend_angle_max_snapshots: int = 512
    num_targets: int = 5
    target_angles_deg: Sequence[float] = (10.0, 25.0, 40.0, 55.0, 70.0)
    target_snr_db: Sequence[float] = (20.0, 15.0, 12.0, 9.0, 6.0)
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

    scenario_name: str = "literature_maglev_modal_response"
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

    # Legacy online-beta ablation controls. The public capture-facing
    # beta-confidence entry no longer uses these fields for beta updates.
    beta_window_samples: int = 80
    beta_update_start_s: float = 0.25
    beta_bootstrap_prior_weight: float = 500.0
    # These variance controls remain for the legacy beta-confidence-R ablation.
    beta_confidence_initial_variance: float = 0.04
    beta_confidence_min_variance: float = 1.0e-6
    beta_confidence_max_variance: float = 0.25
    beta_confidence_forgetting: float = 0.90
    beta_identifiability_min_samples: int = 8
    beta_identifiability_min_los_energy: float = 1.0e-3
    beta_identifiability_min_theta_energy: float = 1.0e-3
    beta_identifiability_min_abs_corr: float = 0.35
    beta_identifiability_max_residual_ratio: float = 0.75
    beta_update_gain: float = 0.25
    beta_update_max_relative_step: float = 0.20
    beta_update_reference_mode: str = "accel_fft_reference"
    beta_accel_reference_low_hz: float = 1.0
    beta_accel_reference_high_hz: float = 120.0
    beta_anchor_min_abs_corr: float = 0.70
    beta_anchor_min_theta_energy: float = 1.0e-3
    beta_anchor_min_anchor_energy: float = 1.0e-3
    beta_anchor_min_scale: float = 0.75
    beta_anchor_max_scale: float = 1.35
    beta_common_aoa_bias_search_deg: float = 15.0
    beta_common_aoa_bias_step_deg: float = 0.05
    # The capture-facing adaptive-beta path is a batch pre-calibration.  It
    # never feeds a target's Kalman posterior back into that target's beta.
    beta_calibration_strategy: str = "independent_prepass_frozen"
    beta_calibration_fraction: float = 0.5
    beta_calibration_min_block_samples: int = 80
    beta_calibration_min_angle_span_deg: float = 8.0
    beta_calibration_min_holdout_improvement: float = 0.01
    beta_calibration_max_wrapped_phase_step_rad: float = 2.5132741228718345
    beta_calibration_min_delta_standard_score: float = 1.0
    # When enabled (the default), a common-AoA candidate is not applied unless
    # the independent native-timestamp ADXL stage also validates it.
    beta_calibration_use_adxl: bool = True
    beta_calibration_adxl_min_block_samples: int = 120
    beta_calibration_adxl_min_holdout_improvement: float = 0.02
    beta_calibration_min_coherence: float = 0.60
    beta_calibration_max_abs_delay_s: float = 0.05
    beta_calibration_delay_step_s: float = 5.0e-4
    beta_calibration_max_relative_change: float = 0.25
    beta_calibration_min_relative_scale_targets: int = 3
    beta_calibration_min_relative_rank1_fraction: float = 0.90
    beta_calibration_scale_mode: str = "aoa_anchored_relative"
    beta_min_abs: float = 1.0 / 1.2
    beta_max_abs: float = 1.0 / 0.05

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
    mixed_scatterer_betas: Sequence[float] = (1.0 / 0.95, 1.0 / 0.35)
    mixed_scatterer_amplitudes: Sequence[float] = (0.7, 0.6)
    mixed_scatterer_biases_rad: Sequence[float] = (0.0, 1.2)

    def wavelength_m(self) -> float:
        return 299_792_458.0 / self.carrier_frequency_hz
