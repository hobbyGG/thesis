from dataclasses import replace

from .config import Phase1Config


def build_phase1_scenarios():
    base = Phase1Config()
    return [
        replace(base, scenario_name="nominal_multifrequency"),
        replace(
            base,
            scenario_name="strong_wrapping",
            component_amplitudes_mm=(0.45, 0.25, 0.12),
            target_snr_db=(30.0, 25.0, 20.0, 15.0, 10.0),
        ),
        replace(
            base,
            scenario_name="aoa_error_bootstrap",
            aoa_error_deg=10.0,
            kappa_update_start_s=0.2,
            kappa_window_samples=80,
        ),
        replace(
            base,
            scenario_name="target_snr_drop",
            degraded_target_indices=(0, 1),
            degradation_start_s=1.6,
            degradation_end_s=3.4,
            degradation_snr_drop_db=25.0,
        ),
        replace(
            base,
            scenario_name="target_dropout",
            dropout_target_indices=(0,),
            dropout_start_s=1.6,
            dropout_end_s=3.4,
        ),
        replace(
            base,
            scenario_name="mixed_scatterer_rangebin",
            enable_mixed_scatterer_target=True,
            mixed_target_index=0,
            mixed_scatterer_kappas=(0.95, 0.35),
            mixed_scatterer_amplitudes=(0.7, 0.6),
            mixed_scatterer_biases_rad=(0.0, 1.2),
        ),
        replace(
            base,
            scenario_name="low_snr_multitarget",
            target_snr_db=(12.0, 10.0, 8.0, 6.0, 4.0),
        ),
    ]
