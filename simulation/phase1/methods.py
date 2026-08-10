"""Backward-compatible imports for Phase 1 method implementations."""

from .algorithm import (
    MethodResult,
    _circular_mean,
    _estimate_target_biases,
    _initial_state_from_cold_start,
    _phase_accel_input,
    _phase_to_displacement,
    _run_structural_phase_kalman,
    calibrated_process_noise_intensity,
    cold_start_reference_mean,
    cold_start_sample_count,
    estimate_proposed_full_pipeline,
    estimate_proposed_full_pipeline_aoa_fixed_beta,
    estimate_proposed_full_pipeline_calibrated,
    estimate_proposed_full_pipeline_beta_confidence,
    estimate_proposed_full_pipeline_beta_confidence_r,
    estimate_proposed_full_pipeline_posterior_r,
    estimate_proposed_full_pipeline_doc_strict,
    estimate_proposed as _estimate_proposed_algorithm,
    run_structural_phase_kalman,
)
from .baselines import (
    estimate_itoh_ls,
    estimate_ma_style_iterative_beta_range_bin,
    estimate_multitarget_aoa_fixed_beta,
    estimate_multitarget_fixed,
    estimate_multitarget_true_beta_fixed_r,
    estimate_oracle,
    estimate_range_bin_itoh,
    estimate_range_bin_only_mixed_phase,
    estimate_selected_aoa_fixed_beta,
    estimate_single_target_ma_style,
)
from .ma2026 import estimate_ma2026_reproduction, estimate_ma2026_target


def estimate_proposed(first, second, config):
    if hasattr(first, "q_m"):
        from .accelerometer import simulate_accelerometer
        from .radar import to_algorithm_radar_input

        truth = first
        radar = second
        return _estimate_proposed_algorithm(
            to_algorithm_radar_input(radar),
            simulate_accelerometer(truth, config),
            config,
        )
    return _estimate_proposed_algorithm(first, second, config)

__all__ = [
    "MethodResult",
    "_circular_mean",
    "_estimate_target_biases",
    "_initial_state_from_cold_start",
    "_phase_accel_input",
    "_phase_to_displacement",
    "_run_structural_phase_kalman",
    "calibrated_process_noise_intensity",
    "cold_start_reference_mean",
    "cold_start_sample_count",
    "estimate_itoh_ls",
    "estimate_ma_style_iterative_beta_range_bin",
    "estimate_ma2026_reproduction",
    "estimate_ma2026_target",
    "estimate_multitarget_aoa_fixed_beta",
    "estimate_multitarget_fixed",
    "estimate_multitarget_true_beta_fixed_r",
    "estimate_oracle",
    "estimate_proposed",
    "estimate_proposed_full_pipeline",
    "estimate_proposed_full_pipeline_aoa_fixed_beta",
    "estimate_proposed_full_pipeline_beta_confidence",
    "estimate_proposed_full_pipeline_calibrated",
    "estimate_proposed_full_pipeline_beta_confidence_r",
    "estimate_proposed_full_pipeline_posterior_r",
    "estimate_proposed_full_pipeline_doc_strict",
    "estimate_range_bin_itoh",
    "estimate_range_bin_only_mixed_phase",
    "estimate_selected_aoa_fixed_beta",
    "estimate_single_target_ma_style",
    "run_structural_phase_kalman",
]
