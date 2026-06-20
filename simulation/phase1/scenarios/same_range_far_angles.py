from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="same_range_far_angles",
        num_targets=4,
        target_angles_deg=(0.0, 45.0, 25.0, 65.0),
        target_snr_db=(36.0, 36.0, 32.0, 32.0),
        target_amplitudes=(1.0, 0.95, 0.9, 0.85),
        target_range_bins=(12, 12, 12, 12),
        component_amplitudes_mm=(0.32, 0.15, 0.075),
    )
