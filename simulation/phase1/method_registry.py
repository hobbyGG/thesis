from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from .algorithm import (
    MethodResult,
    estimate_proposed,
    estimate_proposed_full_pipeline,
    estimate_proposed_full_pipeline_doc_strict,
    estimate_proposed_full_pipeline_kappa_confidence,
    estimate_proposed_full_pipeline_posterior_r,
)
from .baselines import (
    estimate_itoh_ls,
    estimate_ma_style_iterative_beta_range_bin,
    estimate_multitarget_aoa_fixed_kappa,
    estimate_multitarget_true_kappa_fixed_r,
    estimate_oracle,
    estimate_range_bin_itoh,
    estimate_range_bin_only_mixed_phase,
    estimate_selected_aoa_fixed_kappa,
    estimate_single_target_ma_style,
)
from .scenario_inputs import ScenarioInputs
from .ma2026 import estimate_ma2026_reproduction
from .radar import RadarAlgorithmInput
from .selection import select_targets_from_measurements


MethodRunner = Callable[[ScenarioInputs], MethodResult]
ReferenceResolver = Callable[[ScenarioInputs], np.ndarray]


@dataclass(frozen=True)
class MethodSpec:
    name: str
    run: MethodRunner
    target_reference_indices: Optional[ReferenceResolver] = None
    role: str = "paper"
    status: str = "active"


def all_method_specs() -> tuple[MethodSpec, ...]:
    return (
        MethodSpec("oracle", _run_oracle, role="reference"),
        MethodSpec("range_bin_itoh", _run_range_bin_itoh, _one_unmatched_reference, role="paper"),
        MethodSpec("itoh_ls", _run_itoh_ls, role="diagnostic", status="deprecated"),
        MethodSpec(
            "single_target_ma_style",
            _run_single_target_ma_style,
            role="diagnostic",
            status="deprecated",
        ),
        MethodSpec(
            "range_bin_only_mixed_phase",
            _run_range_bin_only_mixed_phase,
            _one_unmatched_reference,
            role="ablation",
        ),
        MethodSpec(
            "ma_style_iterative_beta_range_bin",
            _run_ma_style_iterative_beta_range_bin,
            _one_unmatched_reference,
            role="diagnostic",
        ),
        MethodSpec("ma2026_reproduction", _run_ma2026_reproduction, _ma2026_unmatched_reference, role="paper"),
        MethodSpec(
            "multitarget_true_kappa_fixed_r",
            _run_multitarget_true_kappa_fixed_r,
            role="diagnostic",
        ),
        MethodSpec(
            "multitarget_aoa_fixed_kappa",
            _run_multitarget_aoa_fixed_kappa,
            role="diagnostic",
        ),
        MethodSpec(
            "selected_aoa_fixed_kappa",
            _run_selected_aoa_fixed_kappa,
            _frontend_target_references,
            role="paper",
        ),
        MethodSpec("proposed", _run_proposed, role="diagnostic", status="deprecated"),
        MethodSpec(
            "proposed_full_pipeline",
            _run_proposed_full_pipeline,
            _frontend_target_references,
            role="diagnostic",
            status="deprecated",
        ),
        MethodSpec(
            "proposed_full_pipeline_kappa_confidence",
            _run_proposed_full_pipeline_kappa_confidence,
            _frontend_target_references,
            role="paper",
        ),
        MethodSpec(
            "proposed_full_pipeline_posterior_r",
            _run_proposed_full_pipeline_posterior_r,
            _frontend_target_references,
            role="ablation",
        ),
        MethodSpec(
            "proposed_full_pipeline_doc_strict",
            _run_proposed_full_pipeline_doc_strict,
            _frontend_target_references,
            role="diagnostic",
            status="deprecated",
        ),
    )


def paper_method_specs() -> tuple[MethodSpec, ...]:
    return tuple(spec for spec in all_method_specs() if spec.status == "active" and spec.role in {"paper", "reference"})


def diagnostic_method_specs() -> tuple[MethodSpec, ...]:
    return tuple(spec for spec in all_method_specs() if spec.role in {"diagnostic", "ablation"})


def default_method_specs() -> tuple[MethodSpec, ...]:
    return paper_method_specs()


def run_method_specs(inputs: ScenarioInputs, method_specs: Optional[Sequence[MethodSpec]] = None):
    specs = tuple(method_specs) if method_specs is not None else default_method_specs()
    return [spec.run(inputs) for spec in specs]


def target_reference_by_method(inputs: ScenarioInputs, method_specs: Optional[Sequence[MethodSpec]] = None):
    specs = tuple(method_specs) if method_specs is not None else default_method_specs()
    references = {}
    for spec in specs:
        if spec.target_reference_indices is not None:
            references[spec.name] = spec.target_reference_indices(inputs)
    return references


def _run_oracle(inputs: ScenarioInputs):
    return estimate_oracle(inputs.truth, inputs.radar.target_level, inputs.scenario)


def _run_itoh_ls(inputs: ScenarioInputs):
    return estimate_itoh_ls(
        inputs.truth,
        inputs.radar.target_level,
        inputs.scenario,
        target_index=inputs.radar.best_target_index,
    )


def _run_range_bin_itoh(inputs: ScenarioInputs):
    return estimate_range_bin_itoh(
        inputs.radar.range_bin_only,
        inputs.scenario,
    )


def _run_single_target_ma_style(inputs: ScenarioInputs):
    return estimate_single_target_ma_style(
        inputs.truth,
        inputs.radar.target_level,
        inputs.accelerometer,
        inputs.scenario,
        target_index=inputs.radar.best_target_index,
    )


def _run_range_bin_only_mixed_phase(inputs: ScenarioInputs):
    return estimate_range_bin_only_mixed_phase(
        inputs.radar.range_bin_only,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_ma_style_iterative_beta_range_bin(inputs: ScenarioInputs):
    return estimate_ma_style_iterative_beta_range_bin(
        inputs.radar.range_bin_only,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_ma2026_reproduction(inputs: ScenarioInputs):
    return estimate_ma2026_reproduction(
        inputs.radar.ma2026_rangebin,
        inputs.accelerometer,
        inputs.scenario,
        inputs.ma2026_config,
    )


def _run_multitarget_true_kappa_fixed_r(inputs: ScenarioInputs):
    return estimate_multitarget_true_kappa_fixed_r(
        inputs.truth,
        inputs.radar.target_level,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_multitarget_aoa_fixed_kappa(inputs: ScenarioInputs):
    return estimate_multitarget_aoa_fixed_kappa(
        inputs.radar.target_algorithm,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_selected_aoa_fixed_kappa(inputs: ScenarioInputs):
    return estimate_selected_aoa_fixed_kappa(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed(inputs: ScenarioInputs):
    return estimate_proposed(
        inputs.radar.target_algorithm,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline_kappa_confidence(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline_kappa_confidence(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline_posterior_r(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline_posterior_r(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline_doc_strict(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline_doc_strict(
        _doc_strict_frontend_input(inputs),
        inputs.accelerometer,
        inputs.scenario,
    )


def _doc_strict_frontend_input(inputs: ScenarioInputs):
    targets = inputs.frontend.frontend_targets
    selected = select_targets_from_measurements(
        iq=targets.slow_time,
        wrapped_phase_rad=targets.wrapped_phase_rad,
        available_mask=targets.available_mask,
        measured_kappa=targets.measured_kappa,
        measured_acceleration_mps2=inputs.accelerometer.measured_mps2,
        sample_rate_hz=inputs.scenario.sample_rate_hz,
        initial_measurement_variance=inputs.scenario.initial_measurement_variance,
        min_measurement_variance=inputs.scenario.min_measurement_variance,
        max_measurement_variance=inputs.scenario.max_measurement_variance,
    )
    return RadarAlgorithmInput(
        measured_kappa=targets.measured_kappa.copy(),
        wrapped_phase_rad=targets.wrapped_phase_rad.copy(),
        available_mask=targets.available_mask.copy(),
        selected_indices=selected.selected_indices.copy(),
        initial_r=np.full(targets.measured_kappa.shape, inputs.scenario.max_measurement_variance, dtype=float),
        selection_scores=selected.quality_score.copy(),
    )


def _one_unmatched_reference(inputs: ScenarioInputs):
    del inputs
    return np.array([-1], dtype=int)


def _ma2026_unmatched_reference(inputs: ScenarioInputs):
    return np.full(
        inputs.radar.ma2026_rangebin.wrapped_phase_rad.shape[0],
        -1,
        dtype=int,
    )


def _frontend_target_references(inputs: ScenarioInputs):
    return inputs.frontend.target_reference_indices
