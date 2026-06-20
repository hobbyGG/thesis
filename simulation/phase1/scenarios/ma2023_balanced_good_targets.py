from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="ma2023_balanced_good_targets",
        nominal_frequencies_hz=(0.3, 0.5, 1.0),
        frequency_jitter_hz=0.0,
        component_amplitudes_mm=(0.5, 0.3, 0.2),
        quiet_start_duration_s=0.10,
        num_targets=5,
        target_angles_deg=(5.0, 12.0, 19.0, 26.0, 33.0),
        target_snr_db=(35.0, 35.0, 35.0, 35.0, 35.0),
        target_amplitudes=(1.0, 0.98, 0.96, 0.94, 0.92),
        target_range_bins=(31, 33, 35, 42, 48),
    )
