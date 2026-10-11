from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .config import AlgorithmConfig
from .io import build_algorithm_inputs, load_capture_package
from .kalman import run_fixed_beta_kalman


def run(
    input_dir: str | Path,
    output: str | Path,
    *,
    radar_mode: str = "chirp",
    range_fft_method: str = "fft",
    range_window: str = "hamming",
) -> tuple[Path, Path]:
    capture = load_capture_package(
        input_dir,
        range_fft_method=range_fft_method,
        range_window=range_window,
    )
    radar, acceleration, targets, radar_rate = build_algorithm_inputs(capture, radar_mode=radar_mode)
    # FMCW phase is referenced to the centre of the sampled fast-time
    # aperture.  Use that effective carrier for the phase-to-displacement
    # conversion instead of the nominal synthesizer start frequency.
    radar_meta = capture.radar_metadata
    carrier_frequency_hz = float(radar_meta.get("start_frequency_hz", 77.0e9))
    adc_rate_hz = float(radar_meta.get("adc_sample_rate_hz", 0.0))
    chirp_slope_hz_per_s = float(radar_meta.get("chirp_slope_hz_per_s", 0.0))
    adc_start_time_s = float(radar_meta.get("adc_start_time_s", 0.0))
    if adc_rate_hz > 0.0 and chirp_slope_hz_per_s != 0.0:
        if capture.frontend.range_fft_method == "apfft":
            center_sample = (capture.frontend.num_adc_samples + 1) // 2 - 1
        else:
            center_sample = (capture.frontend.num_adc_samples - 1) / 2.0
        aperture_center_s = adc_start_time_s + float(center_sample) / adc_rate_hz
        carrier_frequency_hz += chirp_slope_hz_per_s * aperture_center_s
    config = AlgorithmConfig(
        sample_rate_hz=float(radar_rate),
        carrier_frequency_hz=carrier_frequency_hz,
    )
    result = run_fixed_beta_kalman(radar, acceleration, config)
    output_path = Path(output)
    if output_path.suffix != ".npz":
        output_path = output_path / "algorithm_result.npz"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    radar_time_ns = np.asarray(radar.extra["radar_time_ns"], dtype=np.int64)
    arrays = {
        "time_s": (radar_time_ns - radar_time_ns[0]).astype(float) * 1.0e-9,
        "radar_time_ns": radar_time_ns,
        "q_hat_m": result.q_hat_m,
        "theta_hat_rad": result.theta_hat_rad,
        "theta_dot_hat_radps": result.theta_dot_hat_radps,
        "los_corrected_phase_rad": result.los_corrected_phase_rad,
        "beta_hat": result.beta_hat,
        "r_theta_history": result.r_theta_history,
        "innovation_rad": result.innovation_rad,
        "radar_wrapped_phase_rad": radar.wrapped_phase_rad,
        "radar_measured_beta": radar.measured_beta,
        "radar_circle_center": np.asarray(radar.extra["circle_center"]),
        "radar_circle_radius": np.asarray(radar.extra["circle_radius"]),
        "radar_circle_residual": np.asarray(radar.extra["circle_residual"]),
        "radar_iq_normalized": np.asarray(radar.extra["normalized_iq"]),
        "selected_target_indices": radar.selected_indices,
        "target_angle_deg": np.asarray(targets.angle_deg, dtype=float),
        "target_range_m": np.asarray(targets.range_m, dtype=float),
    }
    truth_aligned = None
    if capture.truth_displacement_m is not None and capture.truth_time_ns is not None:
        truth_aligned = np.interp(
            radar_time_ns.astype(float),
            np.asarray(capture.truth_time_ns, dtype=float),
            np.asarray(capture.truth_displacement_m, dtype=float),
        )
        arrays["truth_displacement_m"] = truth_aligned
        arrays["truth_time_ns"] = radar_time_ns
    np.savez(output_path, **arrays)
    summary = {
        "schema": "thesis.algorithm-result",
        "schema_version": 1,
        "input_package": str(capture.root),
        "result_file": output_path.name,
        "method": result.method_name,
        "radar_mode": radar_mode,
        "radar_samples": int(radar_time_ns.size),
        "radar_frames": int(capture.radar_time_ns.size),
        "adxl_samples": int(capture.adxl_time_ns.size),
        "selected_targets": int(radar.selected_indices.size),
        "target_detection": radar.extra["detection"],
        "range_fft_method": capture.frontend.range_fft_method,
        "range_window": capture.frontend.range_window,
        "effective_carrier_frequency_hz": config.carrier_frequency_hz,
    }
    if truth_aligned is not None:
        truth = truth_aligned
        estimate = np.asarray(result.q_hat_m, dtype=float)
        # Use one physical reference for both modes.  The chirp stream is not
        # uniformly sampled, so defining the reference by sample count would
        # give it a different cold-start interval from the frame stream.
        frame_time_ns = np.asarray(capture.radar_time_ns, dtype=np.int64)
        frame_truth = np.interp(
            frame_time_ns.astype(np.float64),
            np.asarray(capture.truth_time_ns, dtype=np.float64),
            np.asarray(capture.truth_displacement_m, dtype=float),
        )
        frame_elapsed_s = (frame_time_ns.astype(np.float64) - float(frame_time_ns[0])) * 1.0e-9
        frame_warm = frame_elapsed_s <= float(config.cold_start_duration_s)
        if not np.any(frame_warm):
            frame_warm[0] = True
        reference = float(np.mean(frame_truth[frame_warm]))
        centered_truth = truth - reference
        summary["truth_rmse_m"] = float(np.sqrt(np.mean((estimate - centered_truth) ** 2)))

        # A chirp run has 16 times as many output samples as a frame run.  A
        # direct RMSE over those samples is useful for checking the native
        # chirp stream, but it is not a fair frame-rate comparison.  Report a
        # second metric after sampling the estimate at the frame aperture
        # centers; this is the metric to use when comparing ``frame`` and
        # ``chirp`` runs.
        frame_estimate = np.interp(
            frame_time_ns.astype(np.float64),
            radar_time_ns.astype(np.float64),
            estimate,
        )
        summary["truth_rmse_frame_grid_m"] = float(
            np.sqrt(np.mean((frame_estimate - (frame_truth - reference)) ** 2))
        )
    summary_path = output_path.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the thesis displacement algorithm on a capture package.")
    parser.add_argument("--input", required=True, type=Path, help="capture package directory")
    parser.add_argument("--output", required=True, type=Path, help="result .npz path or output directory")
    parser.add_argument("--radar-mode", choices=("frame", "chirp"), default="chirp")
    parser.add_argument("--range-fft-method", choices=("fft", "apfft"), default="fft")
    parser.add_argument(
        "--range-window",
        choices=("none", "hamming", "hann", "blackman"),
        default="hamming",
    )
    args = parser.parse_args()
    result, summary = run(
        args.input,
        args.output,
        radar_mode=args.radar_mode,
        range_fft_method=args.range_fft_method,
        range_window=args.range_window,
    )
    print(f"saved result: {result}")
    print(f"saved summary: {summary}")


if __name__ == "__main__":
    main()
