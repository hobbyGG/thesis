from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="target_snr_drop",
        degraded_target_indices=(0, 1),
        degradation_start_s=1.6,
        degradation_end_s=3.4,
        degradation_snr_drop_db=25.0,
    )
