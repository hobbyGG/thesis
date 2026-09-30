"""One A20 target-count ablation on an unchanged saved capture package."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithm.config import AlgorithmConfig
from algorithm.io import build_algorithm_inputs, load_capture_package
from algorithm.kalman import run_fixed_beta_kalman
from algorithm.phase import itoh_unwrap


def experiment(input_dir: Path, output: Path) -> dict:
    capture = load_capture_package(input_dir)
    frame_time = capture.radar_time_ns
    elapsed = (frame_time - frame_time[0]).astype(float) * 1.0e-9
    truth = np.interp(frame_time, capture.truth_time_ns, capture.truth_displacement_m)
    truth = truth - np.mean(truth[elapsed < 0.2])
    observation = json.loads((input_dir / "radar/algorithm_input/manifest.json").read_text())["source"]
    rows = []
    saved = {"radar_frame_time_ns": frame_time, "truth_displacement_m": truth}
    for mode in ("frame", "chirp"):
        radar, acceleration, targets, rate = build_algorithm_inputs(capture, radar_mode=mode)
        config = AlgorithmConfig(sample_rate_hz=rate)
        time = radar.extra["radar_time_ns"]
        warm = (time - time[0]) * 1.0e-9 < config.cold_start_duration_s
        # Rank only the measured phase stability in the static cold-start.
        # Geometry correction matters: equal LOS SNR can give unequal q error.
        variance = np.asarray([
            np.var(itoh_unwrap(row[warm]) * beta)
            for row, beta in zip(radar.wrapped_phase_rad, radar.measured_beta)
        ])
        order = radar.selected_indices[np.argsort(variance[radar.selected_indices])]
        frame_estimates = []
        for count in range(1, order.size + 1):
            selected = order[:count]
            result = run_fixed_beta_kalman(replace(radar, selected_indices=selected), acceleration, config)
            estimate = np.interp(frame_time, time, result.q_hat_m)
            error = estimate - truth
            frame_estimates.append(estimate)
            rows.append({
                "mode": mode, "targets": count,
                "selected_range_bins": targets.range_bins[selected].tolist(),
                "selected_angles_deg": targets.angle_deg[selected].tolist(),
                "cold_start_variance_rad2": variance[selected].tolist(),
                "initial_r_rad2": result.extra["initial_r"][selected].tolist(),
                "rmse_frame_grid_um": float(np.sqrt(np.mean(error**2)) * 1.0e6),
                "rmse_after_cold_start_um": float(np.sqrt(np.mean(error[elapsed >= 0.2]**2)) * 1.0e6),
                "rmse_passage_um": float(np.sqrt(np.mean(error[elapsed >= 0.5]**2)) * 1.0e6),
                "median_r_rad2": np.median(result.r_theta_history[selected][:, elapsed_native(time) >= 0.5], axis=1).tolist(),
            })
        saved[f"{mode}_q_hat_m"] = np.asarray(frame_estimates)
    summary = {"input_package": str(input_dir), "duration_s": float(elapsed[-1]),
               "target_source": observation,
               "ranking": "ascending structural-phase variance in measured static first 0.2 s; no truth or supplied SNR used",
               "evaluation": "same frame aperture times, same truth reference, same ADC/chirp and ADXL data for every target count",
               "method": "unchanged fixed_geometry_beta_structural_kalman",
               "rows": rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
    np.savez(output.with_suffix(".npz"), **saved)
    return summary


def elapsed_native(time: np.ndarray) -> np.ndarray:
    return (time - time[0]).astype(float) * 1.0e-9


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = experiment(args.input, args.output)
    for row in result["rows"]:
        print(row["mode"], row["targets"], row["selected_range_bins"],
              f"{row['rmse_frame_grid_um']:.4f} um", f"passage {row['rmse_passage_um']:.4f} um")
