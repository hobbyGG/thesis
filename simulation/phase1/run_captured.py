"""Run the Phase-1 asynchronous fusion algorithm on a completed capture."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from .algorithm import (
    cold_start_reference_mean,
    estimate_direct_aoa_fixed_beta,
    estimate_proposed_full_pipeline_aoa_fixed_beta,
    estimate_proposed_full_pipeline_beta_confidence,
)
from .capture_reader import (
    build_captured_algorithm_input,
    load_captured_fusion_input,
)
from .config import Phase1Config


METHODS = {
    "adaptive_beta": estimate_proposed_full_pipeline_beta_confidence,
    "fixed_beta": estimate_proposed_full_pipeline_aoa_fixed_beta,
    "direct_aoa_fixed_beta": estimate_direct_aoa_fixed_beta,
}


def _integer_list(value: Optional[str], label: str) -> Optional[tuple[int, ...]]:
    if value is None:
        return None
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(not part for part in parts):
        raise ValueError(f"{label} must be a comma-separated integer list")
    try:
        parsed = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"{label} must be a comma-separated integer list") from exc
    if any(item < 0 for item in parsed):
        raise ValueError(f"{label} cannot contain negative indices")
    return parsed


def _phase1_config(captured, algorithm_input) -> Phase1Config:
    radar = captured.fusion_capture.radar.manifest["radar"]
    duration_s = float(
        int(captured.radar_time_ns[-1]) - int(captured.radar_time_ns[0])
    ) * 1.0e-9
    cold_start_duration_s = Phase1Config().cold_start_duration_s
    if bool(getattr(captured, "is_simulation", False)):
        manifest = captured.fusion_capture.timeline.combined_manifest
        contract = manifest.get("algorithm_contract")
        if not isinstance(contract, dict):
            raise RuntimeError("simulation algorithm contract is missing")
        cold_start_duration_s = float(contract["cold_start_duration_s"])
    beta_scale_mode = (
        "adxl_absolute"
        if str(
            getattr(captured, "calibration_mode", "unknown_unvalidated")
        )
        == "validated"
        else "aoa_anchored_relative"
    )
    return Phase1Config(
        duration_s=duration_s,
        sample_rate_hz=float(algorithm_input.effective_radar_rate_hz),
        cold_start_duration_s=cold_start_duration_s,
        carrier_frequency_hz=float(radar.get("start_frequency_hz", 77.0e9)),
        adc_sample_rate_hz=float(radar["adc_sample_rate_hz"]),
        chirp_duration_s=float(radar["ramp_end_time_s"]),
        chirps_per_frame=int(radar["physical_chirps_per_frame"]),
        adc_samples_per_chirp=int(radar["adc_samples_per_chirp"]),
        frontend_num_tx=len(radar["tx_indices"]),
        frontend_num_rx=len(radar["rx_indices"]),
        frontend_num_virtual_rx=int(captured.frontend_config.num_virtual_rx),
        frontend_num_angle_bins=int(captured.frontend_config.num_angle_bins),
        num_targets=int(algorithm_input.radar.wrapped_phase_rad.shape[0]),
        beta_calibration_scale_mode=beta_scale_mode,
    )


def _atomic_save_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        with temporary.open("wb") as stream:
            np.savez_compressed(stream, **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _numeric_result_diagnostics(extra: object) -> dict[str, np.ndarray]:
    if not isinstance(extra, dict):
        return {}
    arrays = {}
    for name, value in extra.items():
        if not isinstance(name, str) or not name:
            continue
        candidate = np.asarray(value)
        if candidate.dtype.kind not in "biufc":
            continue
        arrays[f"diagnostic_{name}"] = candidate
    return arrays


def _validated_result_arrays(result: object, target_shape: tuple[int, int]):
    frame_count = target_shape[1]
    vectors = {
        "q_hat_m": np.asarray(result.q_hat_m, dtype=float),
        "theta_hat_rad": np.asarray(result.theta_hat_rad, dtype=float),
        "theta_dot_hat_radps": np.asarray(result.theta_dot_hat_radps, dtype=float),
        "beta_hat": np.asarray(result.beta_hat, dtype=float),
    }
    for name in ("q_hat_m", "theta_hat_rad", "theta_dot_hat_radps"):
        if vectors[name].shape != (frame_count,):
            raise RuntimeError(
                f"algorithm result {name} must have shape ({frame_count},)"
            )
        if np.any(~np.isfinite(vectors[name])):
            raise RuntimeError(f"algorithm result {name} contains non-finite values")
    if vectors["beta_hat"].shape != (target_shape[0],):
        raise RuntimeError(
            "algorithm result beta_hat must have one value per radar target"
        )
    if np.any(~np.isfinite(vectors["beta_hat"])):
        raise RuntimeError("algorithm result beta_hat contains non-finite values")

    matrices = {
        "los_corrected_phase_rad": np.asarray(
            result.los_corrected_phase_rad,
            dtype=float,
        ),
        "r_theta_history": np.asarray(result.r_theta_history, dtype=float),
        "innovation_rad": np.asarray(result.innovation_rad, dtype=float),
    }
    for name, value in matrices.items():
        if value.shape != target_shape:
            raise RuntimeError(
                f"algorithm result {name} must have shape {target_shape}"
            )
    return {**vectors, **matrices}


def run_captured_algorithm(
    capture_path: Path,
    *,
    output_path: Optional[Path] = None,
    method: str = "direct_aoa_fixed_beta",
    max_adxl_gap_ns: Optional[int] = None,
    nominal_adxl_axis: str = "x",
    nominal_adxl_sign: int = 1,
    require_calibrated: bool = False,
    range_bins: Optional[Sequence[int]] = None,
    angle_bins: Optional[Sequence[int]] = None,
    overwrite: bool = False,
    allow_simulation: bool = False,
) -> tuple[Path, Path]:
    """Run capture fusion, with direct calibrated AoA as the CLI default.

    The adaptive-beta option uses fail-closed independent pre-calibration and
    freezes the accepted or fallback beta before filtering from frame zero.
    """

    if method not in METHODS:
        raise ValueError(f"method must be one of {tuple(METHODS)}")
    if not isinstance(nominal_adxl_axis, str):
        raise ValueError("nominal_adxl_axis must be x, y, or z")
    nominal_adxl_axis = nominal_adxl_axis.strip().lower()
    if nominal_adxl_axis not in ("x", "y", "z"):
        raise ValueError("nominal_adxl_axis must be x, y, or z")
    if (
        isinstance(nominal_adxl_sign, (bool, np.bool_))
        or not isinstance(nominal_adxl_sign, (int, np.integer))
        or int(nominal_adxl_sign) not in (-1, 1)
    ):
        raise ValueError("nominal_adxl_sign must be -1 or 1")
    nominal_adxl_sign = int(nominal_adxl_sign)
    if not isinstance(require_calibrated, (bool, np.bool_)):
        raise ValueError("require_calibrated must be boolean")
    if not isinstance(overwrite, (bool, np.bool_)):
        raise ValueError("overwrite must be boolean")
    if not isinstance(allow_simulation, (bool, np.bool_)):
        raise ValueError("allow_simulation must be boolean")
    if (range_bins is None) != (angle_bins is None):
        raise ValueError("range_bins and angle_bins must be provided together")

    captured = load_captured_fusion_input(
        capture_path,
        max_adxl_gap_ns=max_adxl_gap_ns,
        require_fusion_ready=bool(require_calibrated),
        require_algorithm_ready=True,
        nominal_adxl_axis=nominal_adxl_axis,
        nominal_adxl_sign=nominal_adxl_sign,
        allow_simulation=bool(allow_simulation),
    )
    # Direct AoA captures must use the continuous local MUSIC/ML estimator.
    # Keep the loaded configuration untouched for the explicit legacy methods.
    if method == "direct_aoa_fixed_beta":
        captured = replace(
            captured,
            frontend_config=replace(
                captured.frontend_config,
                angle_estimation_method="local_music_ml",
            ),
        )
    destination = (
        Path(output_path)
        if output_path is not None
        else captured.source_directory / "algorithm" / "phase1_result.npz"
    )
    if destination.suffix == "":
        destination = destination.with_suffix(".npz")
    elif destination.suffix.lower() != ".npz":
        raise ValueError("output path must end with .npz")
    summary_path = destination.with_suffix(".json")
    for candidate in (destination, summary_path):
        if candidate.exists() and not overwrite:
            raise FileExistsError(
                f"refusing to overwrite {candidate}; pass overwrite=true"
            )

    algorithm_input = build_captured_algorithm_input(
        captured,
        range_bins=range_bins,
        angle_bins=angle_bins,
    )
    config = _phase1_config(captured, algorithm_input)
    result = METHODS[method](
        algorithm_input.radar,
        algorithm_input.acceleration,
        config,
    )

    preintegration = algorithm_input.acceleration.preintegration
    target_shape = tuple(algorithm_input.radar.wrapped_phase_rad.shape)
    if len(target_shape) != 2:
        raise RuntimeError("radar wrapped phase must have target and frame axes")
    result_arrays = _validated_result_arrays(result, target_shape)
    radar_extra = getattr(algorithm_input.radar, "extra", None)
    detection_diagnostics = (
        radar_extra.get("target_detection", {"mode": "unavailable"})
        if isinstance(radar_extra, dict)
        else {"mode": "unavailable"}
    )
    arrays = {
        "radar_time_ns": np.asarray(captured.radar_time_ns, dtype=np.int64),
        "radar_reference_time_ns": np.asarray(
            captured.fusion_capture.radar_reference_monotonic_ns,
            dtype=np.int64,
        ),
        "time_s": (
            np.asarray(captured.radar_time_ns, dtype=np.int64)
            - np.int64(captured.radar_time_ns[0])
        ).astype(np.float64)
        * 1.0e-9,
        **result_arrays,
        "radar_wrapped_phase_rad": np.asarray(
            algorithm_input.radar.wrapped_phase_rad,
            dtype=float,
        ),
        "radar_available_mask": np.asarray(
            algorithm_input.radar.available_mask,
            dtype=bool,
        ),
        "radar_measured_beta": np.asarray(
            algorithm_input.radar.measured_beta,
            dtype=float,
        ),
        "radar_initial_r_theta": np.asarray(
            algorithm_input.radar.initial_r,
            dtype=float,
        ),
        "radar_selection_scores": np.asarray(
            algorithm_input.radar.selection_scores,
            dtype=float,
        ),
        "radar_calibration_target_indices": np.asarray(
            algorithm_input.radar.calibration_indices,
            dtype=np.int64,
        ),
        "radar_target_slow_time_iq": np.asarray(
            algorithm_input.frontend_targets.slow_time,
            dtype=np.complex128,
        ),
        "selected_target_indices": np.asarray(
            algorithm_input.radar.selected_indices,
            dtype=np.int64,
        ),
        "target_range_bins": np.asarray(
            algorithm_input.frontend_targets.range_bins,
            dtype=np.int64,
        ),
        "target_angle_bins": np.asarray(
            algorithm_input.frontend_targets.angle_bins,
            dtype=np.int64,
        ),
        "target_range_m": np.asarray(
            algorithm_input.frontend_targets.range_m,
            dtype=float,
        ),
        "target_angle_deg": np.asarray(
            algorithm_input.frontend_targets.angle_deg,
            dtype=float,
        ),
        "adxl_time_ns": np.asarray(
            algorithm_input.acceleration.native_time_ns,
            dtype=np.int64,
        ),
        "adxl_drdy_time_ns": np.asarray(
            captured.fusion_capture.adxl_drdy_monotonic_ns,
            dtype=np.uint64,
        ),
        "adxl_structure_acceleration_mps2": np.asarray(
            algorithm_input.acceleration.native_mps2,
            dtype=float,
        ),
        "interval_delta_v_mps": np.asarray(
            preintegration.delta_v_mps,
            dtype=float,
        ),
        "interval_delta_q_m": np.asarray(
            preintegration.delta_q_m,
            dtype=float,
        ),
        "interval_duration_s": np.asarray(
            preintegration.duration_s,
            dtype=float,
        ),
    }
    for name in (
        "candidate_count_before_dynamic_range",
        "candidate_count_after_dynamic_range",
        "candidate_count_after_limit",
    ):
        value = detection_diagnostics.get(name)
        if value is not None:
            arrays[f"detection_{name}"] = np.asarray(value, dtype=np.int64)
    truth_q = getattr(captured, "truth_displacement_m", None)
    truth_time = getattr(captured, "truth_time_ns", None)
    displacement_rmse_m = None
    truth_displacement_reference_m = None
    acceleration_rmse_mps2 = None
    if truth_q is not None or truth_time is not None:
        if truth_q is None or truth_time is None:
            raise RuntimeError("simulation truth time and displacement must coexist")
        truth_q_array = np.asarray(truth_q, dtype=np.float64)
        truth_time_array = np.asarray(truth_time, dtype=np.int64)
        if (
            truth_q_array.shape != (target_shape[1],)
            or truth_time_array.shape != (target_shape[1],)
            or not np.array_equal(truth_time_array, captured.radar_time_ns)
        ):
            raise RuntimeError("simulation truth does not match the radar timeline")
        arrays["truth_time_ns"] = truth_time_array
        arrays["truth_displacement_m"] = truth_q_array
        truth_displacement_reference_m = cold_start_reference_mean(
            truth_q_array,
            config,
        )
        truth_q_relative = truth_q_array - truth_displacement_reference_m
        arrays["truth_displacement_relative_m"] = truth_q_relative
        arrays["truth_displacement_reference_m"] = np.asarray(
            truth_displacement_reference_m,
            dtype=np.float64,
        )
        displacement_rmse_m = float(
            np.sqrt(
                np.mean(
                    (result_arrays["q_hat_m"] - truth_q_relative) ** 2
                )
            )
        )
    truth_acceleration = getattr(
        captured.fusion_capture,
        "simulation_truth_acceleration_mps2",
        None,
    )
    truth_adxl_time = getattr(
        captured.fusion_capture,
        "simulation_truth_adxl_time_ns",
        None,
    )
    if truth_acceleration is not None or truth_adxl_time is not None:
        if truth_acceleration is None or truth_adxl_time is None:
            raise RuntimeError(
                "simulation acceleration truth and timeline must coexist"
            )
        truth_acceleration_array = np.asarray(
            truth_acceleration,
            dtype=np.float64,
        )
        truth_adxl_time_array = np.asarray(truth_adxl_time, dtype=np.int64)
        measured_acceleration = arrays["adxl_structure_acceleration_mps2"]
        if (
            truth_acceleration_array.shape != measured_acceleration.shape
            or truth_adxl_time_array.shape != measured_acceleration.shape
            or not np.array_equal(
                truth_adxl_time_array,
                arrays["adxl_time_ns"],
            )
        ):
            raise RuntimeError(
                "simulation acceleration truth does not match the ADXL timeline"
            )
        arrays["truth_adxl_time_ns"] = truth_adxl_time_array
        arrays["truth_acceleration_mps2"] = truth_acceleration_array
        acceleration_rmse_mps2 = float(
            np.sqrt(
                np.mean(
                    (measured_acceleration - truth_acceleration_array) ** 2
                )
            )
        )
    if captured.fusion_capture.radar_adc_sample_monotonic_ns is not None:
        arrays["radar_adc_time_ns"] = np.asarray(
            captured.fusion_capture.radar_adc_sample_monotonic_ns,
            dtype=np.int64,
        )
    arrays.update(_numeric_result_diagnostics(getattr(result, "extra", None)))
    _atomic_save_npz(destination, arrays)

    fusion_capture = captured.fusion_capture
    result_extra = (
        result.extra if isinstance(getattr(result, "extra", None), dict) else {}
    )
    beta_calibration_accepted = result_extra.get("beta_calibration_accepted")
    beta_calibration_any_accepted = result_extra.get(
        "beta_calibration_any_accepted"
    )
    beta_calibration_common_accepted = result_extra.get(
        "beta_calibration_common_aoa_accepted"
    )
    beta_calibration_adxl_accepted = result_extra.get(
        "beta_calibration_adxl_accepted"
    )
    beta_calibration_adxl_any_accepted = result_extra.get(
        "beta_calibration_adxl_any_accepted"
    )
    beta_calibration_accepted_mask = result_extra.get(
        "beta_calibration_accepted_mask"
    )
    beta_calibration_reason_by_target = result_extra.get(
        "beta_calibration_adxl_reason_by_target"
    )
    beta_calibration_adxl_eligible_mask = result_extra.get(
        "beta_calibration_adxl_relative_adxl_eligible_mask"
    )
    beta_calibration_rank1_fraction = result_extra.get(
        "beta_calibration_adxl_relative_fold_rank1_fraction"
    )
    beta_calibration_fold_common_scale = result_extra.get(
        "beta_calibration_adxl_fold_common_scale"
    )
    summary = {
        "schema": "phase1.captured-fusion-result",
        "schema_version": 1,
        "status": "complete",
        "capture_directory": str(captured.source_directory),
        "result_file": destination.name,
        "result_arrays": sorted(arrays),
        "method_key": method,
        "method": result.method_name,
        "algorithm_ready": bool(fusion_capture.algorithm_ready),
        "simulation_ready": bool(
            getattr(fusion_capture, "simulation_ready", False)
        ),
        "simulation_opt_in": bool(allow_simulation),
        "is_simulation": bool(getattr(captured, "is_simulation", False)),
        "calibrated_fusion_ready": bool(fusion_capture.fusion_ready),
        "timing_mode": captured.timing_mode,
        "calibration_mode": captured.calibration_mode,
        "warnings": list(captured.warnings),
        "radar_frames": int(captured.radar_time_ns.size),
        "adxl_samples": int(algorithm_input.acceleration.native_time_ns.size),
        "selected_targets": int(algorithm_input.radar.selected_indices.size),
        "result_samples": int(np.asarray(result.q_hat_m).size),
        "effective_radar_rate_hz": float(
            algorithm_input.effective_radar_rate_hz
        ),
        "max_adxl_gap_ns": int(captured.max_adxl_gap_ns),
        "nominal_adxl_axis": nominal_adxl_axis,
        "nominal_adxl_sign": nominal_adxl_sign,
        "range_bins_override": (
            None if range_bins is None else [int(value) for value in range_bins]
        ),
        "angle_bins_override": (
            None if angle_bins is None else [int(value) for value in angle_bins]
        ),
        "require_calibrated": bool(require_calibrated),
        "source_timestamp_quality": (
            fusion_capture.provenance.radar_timestamp_quality
        ),
        "cold_start_duration_s": float(config.cold_start_duration_s),
        "truth_displacement_reference": (
            None if truth_q is None else "cold_start_mean"
        ),
        "truth_displacement_reference_m": truth_displacement_reference_m,
        "truth_displacement_rmse_m": displacement_rmse_m,
        "truth_acceleration_rmse_mps2": acceleration_rmse_mps2,
        "target_detection": detection_diagnostics,
        "adaptive_r_mode": result_extra.get("adaptive_r_mode"),
        "beta_calibration_strategy": result_extra.get(
            "beta_calibration_strategy"
        ),
        "beta_calibration_used_stage": result_extra.get(
            "beta_calibration_used_stage"
        ),
        "beta_calibration_accepted": (
            None
            if beta_calibration_accepted is None
            else bool(beta_calibration_accepted)
        ),
        "beta_calibration_any_accepted": (
            None
            if beta_calibration_any_accepted is None
            else bool(beta_calibration_any_accepted)
        ),
        "beta_calibration_accepted_count": result_extra.get(
            "beta_calibration_accepted_count"
        ),
        "beta_calibration_all_selected_accepted": result_extra.get(
            "beta_calibration_all_selected_accepted"
        ),
        "beta_calibration_accepted_mask": (
            None
            if beta_calibration_accepted_mask is None
            else [
                bool(value)
                for value in np.asarray(
                    beta_calibration_accepted_mask,
                    dtype=bool,
                ).reshape(-1)
            ]
        ),
        "beta_calibration_reason": result_extra.get("beta_calibration_reason"),
        "beta_calibration_common_aoa_accepted": (
            None
            if beta_calibration_common_accepted is None
            else bool(beta_calibration_common_accepted)
        ),
        "beta_calibration_common_aoa_reason": result_extra.get(
            "beta_calibration_common_aoa_reason"
        ),
        "beta_calibration_adxl_accepted": (
            None
            if beta_calibration_adxl_accepted is None
            else bool(beta_calibration_adxl_accepted)
        ),
        "beta_calibration_adxl_any_accepted": (
            None
            if beta_calibration_adxl_any_accepted is None
            else bool(beta_calibration_adxl_any_accepted)
        ),
        "beta_calibration_adxl_all_accepted": result_extra.get(
            "beta_calibration_adxl_all_accepted"
        ),
        "beta_calibration_adxl_reason": result_extra.get(
            "beta_calibration_adxl_reason"
        ),
        "beta_calibration_adxl_reason_by_target": (
            None
            if beta_calibration_reason_by_target is None
            else [str(value) for value in beta_calibration_reason_by_target]
        ),
        "beta_calibration_adxl_scale_mode_requested": result_extra.get(
            "beta_calibration_adxl_scale_mode_requested"
        ),
        "beta_calibration_adxl_scale_mode": result_extra.get(
            "beta_calibration_adxl_scale_mode"
        ),
        "beta_calibration_adxl_eligible_mask": (
            None
            if beta_calibration_adxl_eligible_mask is None
            else [
                bool(value)
                for value in np.asarray(
                    beta_calibration_adxl_eligible_mask,
                    dtype=bool,
                ).reshape(-1)
            ]
        ),
        "beta_calibration_relative_fold_rank1_fraction": (
            None
            if beta_calibration_rank1_fraction is None
            else [
                None if not np.isfinite(value) else float(value)
                for value in np.asarray(
                    beta_calibration_rank1_fraction,
                    dtype=float,
                ).reshape(-1)
            ]
        ),
        "beta_calibration_adxl_fold_common_scale": (
            None
            if beta_calibration_fold_common_scale is None
            else [
                None if not np.isfinite(value) else float(value)
                for value in np.asarray(
                    beta_calibration_fold_common_scale,
                    dtype=float,
                ).reshape(-1)
            ]
        ),
    }
    _atomic_write_json(summary_path, summary)
    return destination, summary_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the asynchronous Phase-1 radar/ADXL355 fusion algorithm on "
            "one completed synchronized capture."
        )
    )
    parser.add_argument("capture_path", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Result .npz path; default is CAPTURE_PATH/algorithm/phase1_result.npz.",
    )
    parser.add_argument(
        "--method",
        choices=tuple(METHODS),
        default="direct_aoa_fixed_beta",
        help=(
            "direct_aoa_fixed_beta uses the frontend direct-AoA estimate and "
            "freezes geometry beta; fixed_beta is the legacy FFT-AoA baseline; "
            "adaptive_beta is an explicit legacy pre-calibration comparison."
        ),
    )
    parser.add_argument("--adxl-axis", choices=("x", "y", "z"), default="x")
    parser.add_argument(
        "--adxl-sign",
        choices=(-1, 1),
        default=1,
        type=int,
        help="Sign of the selected structural axis before fixture calibration.",
    )
    parser.add_argument(
        "--max-adxl-gap-ms",
        type=float,
        help="Maximum accepted ADXL timestamp gap; default is inferred from data.",
    )
    parser.add_argument("--range-bins", help="Optional comma-separated range bins.")
    parser.add_argument("--angle-bins", help="Optional comma-separated angle bins.")
    parser.add_argument(
        "--require-calibrated",
        action="store_true",
        help="Reject captures lacking the stricter timing/value calibration gate.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing matching .npz/.json result pair.",
    )
    parser.add_argument(
        "--allow-simulation",
        action="store_true",
        help=(
            "Explicitly permit the fixed magnetic-levitation simulation package. "
            "Synthetic packages are rejected by default."
        ),
    )
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        max_gap_ns = None
        if args.max_adxl_gap_ms is not None:
            if not np.isfinite(args.max_adxl_gap_ms) or args.max_adxl_gap_ms <= 0:
                raise ValueError("--max-adxl-gap-ms must be finite and positive")
            max_gap_ns = int(round(args.max_adxl_gap_ms * 1_000_000.0))
        range_bins = _integer_list(args.range_bins, "--range-bins")
        angle_bins = _integer_list(args.angle_bins, "--angle-bins")
        output, summary = run_captured_algorithm(
            args.capture_path,
            output_path=args.output,
            method=args.method,
            max_adxl_gap_ns=max_gap_ns,
            nominal_adxl_axis=args.adxl_axis,
            nominal_adxl_sign=args.adxl_sign,
            require_calibrated=args.require_calibrated,
            range_bins=range_bins,
            angle_bins=angle_bins,
            overwrite=args.overwrite,
            allow_simulation=args.allow_simulation,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    summary_payload = json.loads(summary.read_text(encoding="utf-8"))
    for warning in summary_payload.get("warnings", ()):
        print(f"warning: {warning}", file=sys.stderr)
    print(f"saved result: {output}")
    print(f"saved summary: {summary}")


if __name__ == "__main__":
    main()
