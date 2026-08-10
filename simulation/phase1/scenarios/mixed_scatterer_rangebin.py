from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="mixed_scatterer_rangebin",
        enable_mixed_scatterer_target=True,
        mixed_target_index=0,
        mixed_scatterer_betas=(1.0 / 0.95, 1.0 / 0.35),
        mixed_scatterer_amplitudes=(0.7, 0.6),
        mixed_scatterer_biases_rad=(0.0, 1.2),
    )
