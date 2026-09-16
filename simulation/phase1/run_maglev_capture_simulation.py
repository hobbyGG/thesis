"""CLI for the single measured magnetic-levitation capture simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .maglev_capture_simulator import generate_maglev_capture_package
from .run_captured import run_captured_algorithm


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the fixed 卡3激光位移/3-4 magnetic-levitation beam "
            "capture simulation. No other scenario is supported."
        )
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--run-algorithm",
        action="store_true",
        help="Run Phase-1 with the required explicit simulation opt-in.",
    )
    parser.add_argument(
        "--method", choices=("adaptive_beta", "fixed_beta"), default="fixed_beta"
    )
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        generated = generate_maglev_capture_package(
            args.output,
            duration_s=args.duration,
            seed=args.seed,
            overwrite=args.overwrite,
        )
        result_path = None
        summary_path = None
        if args.run_algorithm:
            result_path, summary_path = run_captured_algorithm(
                generated.directory,
                method=args.method,
                overwrite=args.overwrite,
                allow_simulation=True,
            )
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(f"saved simulation package: {generated.directory}")
    print(f"saved manifest: {generated.manifest_path}")
    print(f"radar frames: {generated.radar_frames}")
    print(f"ADXL samples: {generated.adxl_samples}")
    if result_path is not None and summary_path is not None:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        print(f"saved algorithm result: {result_path}")
        print(f"truth RMSE (m): {summary['truth_displacement_rmse_m']}")
        print(
            "acceleration truth RMSE (m/s^2): "
            f"{summary['truth_acceleration_rmse_mps2']}"
        )


if __name__ == "__main__":
    main()
