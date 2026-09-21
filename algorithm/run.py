from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .config import AlgorithmConfig
from .io import build_algorithm_inputs, load_capture_package
from .kalman import run_fixed_beta_kalman


def run(input_dir: str | Path, output: str | Path) -> tuple[Path, Path]:
    capture = load_capture_package(input_dir)
    radar, acceleration, targets, radar_rate = build_algorithm_inputs(capture)
    config = AlgorithmConfig(sample_rate_hz=float(radar_rate))
    result = run_fixed_beta_kalman(radar, acceleration, config)
    output_path = Path(output)
    if output_path.suffix != ".npz":
        output_path = output_path / "algorithm_result.npz"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        "time_s": (capture.radar_time_ns - capture.radar_time_ns[0]).astype(float) * 1.0e-9,
        "radar_time_ns": capture.radar_time_ns,
        "q_hat_m": result.q_hat_m,
        "theta_hat_rad": result.theta_hat_rad,
        "theta_dot_hat_radps": result.theta_dot_hat_radps,
        "los_corrected_phase_rad": result.los_corrected_phase_rad,
        "beta_hat": result.beta_hat,
        "r_theta_history": result.r_theta_history,
        "innovation_rad": result.innovation_rad,
        "radar_wrapped_phase_rad": radar.wrapped_phase_rad,
        "radar_measured_beta": radar.measured_beta,
        "selected_target_indices": radar.selected_indices,
        "target_angle_deg": np.asarray(targets.angle_deg, dtype=float),
        "target_range_m": np.asarray(targets.range_m, dtype=float),
    }
    if capture.truth_displacement_m is not None:
        arrays["truth_displacement_m"] = capture.truth_displacement_m
        arrays["truth_time_ns"] = capture.truth_time_ns
    np.savez(output_path, **arrays)
    summary = {
        "schema": "thesis.algorithm-result",
        "schema_version": 1,
        "input_package": str(capture.root),
        "result_file": output_path.name,
        "method": result.method_name,
        "radar_frames": int(capture.radar_time_ns.size),
        "adxl_samples": int(capture.adxl_time_ns.size),
        "selected_targets": int(radar.selected_indices.size),
        "target_detection": radar.extra["detection"],
    }
    if capture.truth_displacement_m is not None:
        truth = np.asarray(capture.truth_displacement_m, dtype=float)
        estimate = np.asarray(result.q_hat_m, dtype=float)
        reference = float(np.mean(truth[: max(1, round(config.cold_start_duration_s * radar_rate))]))
        summary["truth_rmse_m"] = float(np.sqrt(np.mean((estimate - (truth - reference)) ** 2)))
    summary_path = output_path.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the thesis displacement algorithm on a capture package.")
    parser.add_argument("--input", required=True, type=Path, help="capture package directory")
    parser.add_argument("--output", required=True, type=Path, help="result .npz path or output directory")
    args = parser.parse_args()
    result, summary = run(args.input, args.output)
    print(f"saved result: {result}")
    print(f"saved summary: {summary}")


if __name__ == "__main__":
    main()
