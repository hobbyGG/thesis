"""Public evaluation facade for Phase 1 validation."""

from .gates import build_gate_results
from .pipeline import evaluate_scenario


def evaluate_all_scenarios(scenarios):
    all_rows = []
    artifacts_by_scenario = {}
    for scenario in scenarios:
        rows, artifacts = evaluate_scenario(scenario)
        all_rows.extend(rows)
        artifacts_by_scenario[scenario.scenario_name] = artifacts
    return {
        "rows": all_rows,
        "gates": build_gate_results(all_rows, artifacts_by_scenario),
        "artifacts": artifacts_by_scenario,
    }


__all__ = [
    "build_gate_results",
    "evaluate_all_scenarios",
    "evaluate_scenario",
]
