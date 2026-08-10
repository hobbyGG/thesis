from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from .algorithm import (
    MethodResult,
    estimate_proposed_full_pipeline_aoa_fixed_beta,
    estimate_proposed_full_pipeline_beta_confidence,
)
from .baselines import (
    estimate_multitarget_aoa_fixed_beta,
    estimate_oracle,
    estimate_range_bin_itoh,
    estimate_range_bin_only_mixed_phase,
    estimate_selected_aoa_fixed_beta,
)
from .scenario_inputs import ScenarioInputs
from .ma2026 import estimate_ma2026_reproduction


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
        MethodSpec(
            "range_bin_only_mixed_phase",
            _run_range_bin_only_mixed_phase,
            _one_unmatched_reference,
            role="ablation",
        ),
        MethodSpec("ma2026_reproduction", _run_ma2026_reproduction, _ma2026_unmatched_reference, role="paper"),
        MethodSpec(
            "multitarget_aoa_fixed_beta",
            _run_multitarget_aoa_fixed_beta,
            role="ablation",
        ),
        MethodSpec(
            "selected_aoa_fixed_beta",
            _run_selected_aoa_fixed_beta,
            _frontend_target_references,
            role="paper",
        ),
        MethodSpec(
            "proposed_full_pipeline_aoa_fixed_beta",
            _run_proposed_full_pipeline_aoa_fixed_beta,
            _frontend_target_references,
            role="paper",
        ),
        MethodSpec(
            "proposed_full_pipeline_beta_confidence",
            _run_proposed_full_pipeline_beta_confidence,
            _frontend_target_references,
            role="paper",
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


def _run_range_bin_itoh(inputs: ScenarioInputs):
    return estimate_range_bin_itoh(
        inputs.radar.range_bin_only,
        inputs.scenario,
    )


def _run_range_bin_only_mixed_phase(inputs: ScenarioInputs):
    return estimate_range_bin_only_mixed_phase(
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


def _run_multitarget_aoa_fixed_beta(inputs: ScenarioInputs):
    return estimate_multitarget_aoa_fixed_beta(
        inputs.radar.target_algorithm,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_selected_aoa_fixed_beta(inputs: ScenarioInputs):
    return estimate_selected_aoa_fixed_beta(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline_aoa_fixed_beta(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline_aoa_fixed_beta(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
    )


def _run_proposed_full_pipeline_beta_confidence(inputs: ScenarioInputs):
    return estimate_proposed_full_pipeline_beta_confidence(
        inputs.radar.selected_frontend,
        inputs.accelerometer,
        inputs.scenario,
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
