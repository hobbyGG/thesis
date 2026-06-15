import argparse
from pathlib import Path

from .evaluate import evaluate_all_scenarios
from .reporting import write_validation_report
from .scenarios import build_phase1_scenarios


def main():
    parser = argparse.ArgumentParser(description="Run phase-1 algorithm validation.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("simulation/outputs/phase1_validation"),
        help="Directory for validation reports.",
    )
    args = parser.parse_args()

    summary = evaluate_all_scenarios(build_phase1_scenarios())
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
