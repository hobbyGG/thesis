import argparse
from pathlib import Path

from .extended_experiments import run_extended_experiments, write_extended_experiment_report


def _parse_int_list(text):
    return tuple(int(item.strip()) for item in text.split(",") if item.strip())


def _parse_float_list(text):
    return tuple(float(item.strip()) for item in text.split(",") if item.strip())


def main():
    parser = argparse.ArgumentParser(description="Run Phase-1 extended paper experiments.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("simulation/outputs/phase1_extended_validation"),
        help="Directory for extended experiment tables.",
    )
    parser.add_argument(
        "--seeds",
        default="2026,2027,2028,2029,2030",
        help="Comma-separated random seeds for Monte Carlo runs.",
    )
    parser.add_argument(
        "--aoa-errors-deg",
        default="0,3,6,10,15",
        help="Comma-separated AoA error levels in degrees.",
    )
    parser.add_argument(
        "--snr-floors-db",
        default="4,6,8,10,12",
        help="Comma-separated minimum target SNR levels for sensitivity runs.",
    )
    args = parser.parse_args()

    summary = run_extended_experiments(
        seeds=_parse_int_list(args.seeds),
        aoa_errors_deg=_parse_float_list(args.aoa_errors_deg),
        snr_floors_db=_parse_float_list(args.snr_floors_db),
    )
    written = write_extended_experiment_report(summary, args.output_dir)
    print(f"monte carlo: {written['monte_carlo_csv']}")
    print(f"monte carlo summary: {written['monte_carlo_summary_csv']}")
    print(f"ablation: {written['ablation_csv']}")
    print(f"aoa sensitivity: {written['sensitivity_aoa_csv']}")
    print(f"snr sensitivity: {written['sensitivity_snr_csv']}")
    print(f"summary: {written['summary_md']}")


if __name__ == "__main__":
    main()
