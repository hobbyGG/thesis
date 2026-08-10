from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="literature_mmwbats_same_range_aliasing",
        num_targets=2,
        target_angles_deg=(15.0, 30.0),
        target_range_bins=(18, 18),
        target_snr_db=(22.0, 18.0),
        target_amplitudes=(1.0, 0.95),
        frontend_num_virtual_rx=8,
        frontend_num_angle_bins=64,
        frontend_angle_window="hann",
        component_amplitudes_mm=(0.28, 0.14, 0.07),
    )
