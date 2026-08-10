from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="measured_bridge_point4_transverse",
        motion_profile="measured_bridge",
        duration_s=4.0,
        sample_rate_hz=100.0,
        cold_start_duration_s=0.20,
        measured_bridge_tdms_path="datafile/20250320test12.tdms",
        measured_bridge_laser_channel="3-4",
        measured_bridge_acceleration_channel="1-5",
        measured_bridge_event_window_s=(15.33, 19.33),
        measured_bridge_analysis_band_hz=(0.2, 80.0),
        measured_bridge_powerline_hz=(50.0, 100.0, 150.0),
        measured_bridge_laser_truth_preprocessing="none",
        measured_bridge_laser_scale_m_per_v=1.0e-3,
        measured_bridge_acceleration_source="laser_derived",
        measured_bridge_derived_accel_preprocessing="bandpass_notch",
        measured_bridge_derived_accel_band_hz=(0.2, 30.0),
        measured_bridge_derived_accel_noise_std_mps2=0.02,
        measured_bridge_accel_scale_mps2_per_v=1.0,
        measured_bridge_accel_sign=-1.0,
        measured_bridge_time_shift_s=-0.01,
        num_targets=5,
        target_angles_deg=(5.0, 15.0, 25.0, 35.0, 45.0),
        target_snr_db=(20.0, 17.0, 14.0, 11.0, 8.0),
        target_amplitudes=(1.0, 0.95, 0.9, 0.85, 0.8),
        target_range_bins=(8, 24, 40, 56, 72),
    )
