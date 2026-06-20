"""Backward-compatible imports for Phase 1 scenario input assembly."""

from .scenario_inputs import (
    FrontendViews,
    RadarViews,
    ScenarioInputs,
    best_target_index,
    build_frontend_views,
    build_scenario_inputs,
    evaluation_reference_indices,
    frontend_available_threshold,
    frontend_candidate_bins,
    frontend_views_to_artifacts,
    nearest_scatterer_reference,
    range_bin_only_mixed_input,
    range_bin_only_reference_bin,
    selected_frontend_algorithm_input,
    slice_frontend_targets,
)

__all__ = [
    "FrontendViews",
    "RadarViews",
    "ScenarioInputs",
    "best_target_index",
    "build_frontend_views",
    "build_scenario_inputs",
    "evaluation_reference_indices",
    "frontend_available_threshold",
    "frontend_candidate_bins",
    "frontend_views_to_artifacts",
    "nearest_scatterer_reference",
    "range_bin_only_mixed_input",
    "range_bin_only_reference_bin",
    "selected_frontend_algorithm_input",
    "slice_frontend_targets",
]
