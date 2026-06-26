import argparse
from pathlib import Path

from .evaluate import evaluate_all_scenarios
from .method_registry import all_method_specs, default_method_specs
from .reporting import write_validation_report
from .scenarios import build_all_phase1_scenarios, build_phase1_scenarios


def main():
    parser = argparse.ArgumentParser(description="Run phase-1 algorithm validation.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("simulation/outputs/phase1_validation"),
        help="Directory for validation reports.",
    )
    parser.add_argument(
        "--include-measured-bridge",
        action="store_true",
        help="Include the local TDMS-driven semi-measured bridge scenario as an optional diagnostic case.",
    )
    parser.add_argument(
        "--exclude-measured-bridge",
        action="store_true",
        help="Compatibility no-op; the local TDMS-driven semi-measured bridge scenario is excluded by default.",
    )
    parser.add_argument(
        "--method-set",
        choices=("paper", "all"),
        default="paper",
        help="Use the clean paper method set by default; pass 'all' for diagnostic and deprecated methods too.",
    )
    parser.add_argument(
        "--scenario-set",
        choices=("paper", "all"),
        default="paper",
        help="Use the clean paper scenario set by default; pass 'all' for diagnostic and appendix scenarios too.",
    )
    args = parser.parse_args()

    method_specs = all_method_specs() if args.method_set == "all" else default_method_specs()
    scenario_builder = build_all_phase1_scenarios if args.scenario_set == "all" else build_phase1_scenarios
    summary = evaluate_all_scenarios(
        scenario_builder(include_measured_bridge=args.include_measured_bridge and not args.exclude_measured_bridge),
        method_specs=method_specs,
    )
    written = write_validation_report(summary, args.output_dir)
    print(f"metrics: {written['metrics_csv']}")
    print(f"gates: {written['gates_json']}")
    print(f"summary: {written['summary_md']}")
    failed = [gate for gate in summary["gates"] if not gate["passed"]]
    print(f"feasibility gates passed: {len(summary['gates']) - len(failed)}/{len(summary['gates'])}")
    if failed:
        print("failed gates:")
        for gate in failed:
            print(f"- {gate['name']}: value={gate['value']} threshold={gate['threshold']}")


if __name__ == "__main__":
    main()
