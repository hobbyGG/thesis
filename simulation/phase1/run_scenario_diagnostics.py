import argparse
from pathlib import Path

from .scenario_diagnostics import write_scenario_diagnostics
from .scenarios import build_all_phase1_scenarios, build_phase1_scenarios


def main():
    parser = argparse.ArgumentParser(description="Write Phase-1 scenario parameter tables and truth plots.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("simulation/outputs/phase1_scenario_diagnostics"),
        help="Directory for scenario diagnostics.",
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
        "--scenario-set",
        choices=("paper", "all"),
        default="all",
        help="Write all scenario diagnostics by default; pass 'paper' for only the main paper scenarios.",
    )
    args = parser.parse_args()

    scenario_builder = build_phase1_scenarios if args.scenario_set == "paper" else build_all_phase1_scenarios
    written = write_scenario_diagnostics(
        scenario_builder(include_measured_bridge=args.include_measured_bridge and not args.exclude_measured_bridge),
        args.output_dir,
    )
    print(f"parameters: {written['parameters_csv']}")
    print(f"summary: {written['summary_md']}")
    print(f"plots: {written['plots_dir']}")


if __name__ == "__main__":
    main()
