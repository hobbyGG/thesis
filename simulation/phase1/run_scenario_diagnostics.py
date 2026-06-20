import argparse
from pathlib import Path

from .scenario_diagnostics import write_scenario_diagnostics
from .scenarios import build_phase1_scenarios


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
        help="Compatibility flag; the local TDMS-driven semi-measured bridge scenario is included by default.",
    )
    parser.add_argument(
        "--exclude-measured-bridge",
        action="store_true",
        help="Exclude the local TDMS-driven semi-measured bridge scenario.",
    )
    args = parser.parse_args()

    written = write_scenario_diagnostics(
        build_phase1_scenarios(include_measured_bridge=not args.exclude_measured_bridge),
        args.output_dir,
    )
    print(f"parameters: {written['parameters_csv']}")
    print(f"summary: {written['summary_md']}")
    print(f"plots: {written['plots_dir']}")


if __name__ == "__main__":
    main()
