from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="literature_maglev_modal_response",
        motion_profile="literature_maglev_modal",
        duration_s=5.0,
        sample_rate_hz=200.0,
        nominal_frequencies_hz=(7.7737, 11.5742, 26.5642),
        frequency_jitter_hz=0.0,
        component_amplitudes_mm=(0.10, 0.055, 0.025),
        truth_peak_displacement_mm=1.8,
        quiet_start_duration_s=0.10,
        vehicle_event_center_s=2.45,
        vehicle_event_width_s=0.75,
        accel_noise_std_mps2=0.03,
        num_targets=5,
        target_angles_deg=(8.0, 18.0, 28.0, 38.0, 50.0),
        target_snr_db=(26.0, 24.0, 22.0, 20.0, 18.0),
        target_amplitudes=(1.0, 0.95, 0.9, 0.85, 0.8),
        target_range_bins=(12, 24, 36, 48, 60),
    )
