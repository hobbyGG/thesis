from .evaluation import method_rows
from .method_registry import default_method_specs, run_method_specs, target_reference_by_method
from .scenario_inputs import build_scenario_inputs


def evaluate_scenario(scenario, method_specs=None):
    inputs = build_scenario_inputs(scenario)
    specs = tuple(method_specs) if method_specs is not None else default_method_specs()
    results = run_method_specs(inputs, specs)
    rows = method_rows(
        inputs.scenario,
        inputs.truth,
        inputs.radar.target_level,
        results,
        target_reference_by_method=target_reference_by_method(inputs, specs),
    )
    artifacts = inputs.artifacts()
    artifacts["results"] = results
    return rows, artifacts
