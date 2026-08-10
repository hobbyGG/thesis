from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="literature_vitals_same_radial_distance",
        num_targets=2,
        target_angles_deg=(-20.0, 20.0),
        target_range_bins=(20, 20),
        target_snr_db=(22.0, 18.0),
        target_amplitudes=(1.0, 0.95),
        frontend_num_virtual_rx=8,
        frontend_num_angle_bins=64,
        frontend_angle_window="hann",
        nominal_frequencies_hz=(0.35, 0.85, 1.25),
        frequency_jitter_hz=0.0,
        component_amplitudes_mm=(0.35, 0.06, 0.03),
    )
