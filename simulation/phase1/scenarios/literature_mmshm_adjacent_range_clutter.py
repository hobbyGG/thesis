from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="literature_mmshm_adjacent_range_clutter",
        num_targets=2,
        target_angles_deg=(15.0, 30.0),
        target_range_bins=(18, 19),
        target_snr_db=(22.0, 18.0),
        target_amplitudes=(1.0, 0.9),
        frontend_num_virtual_rx=8,
        frontend_num_angle_bins=64,
        frontend_angle_window="hann",
        component_amplitudes_mm=(0.28, 0.14, 0.07),
    )
