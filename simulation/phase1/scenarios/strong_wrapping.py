from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="strong_wrapping",
        motion_profile="cold_start_ramp_strong_wrapping",
        truth_peak_displacement_mm=5.0,
        nominal_frequencies_hz=(2.0, 5.0, 12.0),
        frequency_jitter_hz=0.0,
        component_amplitudes_mm=(0.25, 0.55, 0.35),
        target_snr_db=(30.0, 25.0, 20.0, 15.0, 10.0),
    )
