"""Minimal 20-frame causal geometry/beta rolling-loop smoke.

Scratch only: this file intentionally stops before the retained fixed-beta
Kalman because that API takes one beta vector for an entire run.  The purpose
is to validate that online geometry updates can be produced causally from the
current frontend without exposing truth, q_proxy, or paper metadata to the
estimator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.frontend import extract_targets, range_angle_process  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from algorithm.selection import detect_target_bins, select_targets  # noqa: E402
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402


WINDOW_FRAMES = 20
OUTPUT_FRAMES = 20
RADAR_RATE_HZ = 100.0
FORBIDDEN_RELATIVE_PATHS = (
    Path("truth"),
    Path("paper_response_metadata.json"),
)


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256_array(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes(order="C")).hexdigest()


def _copy_estimator_only(source: Path, destination: Path) -> None:
    """Copy the capture contract while excluding evaluation/paper artifacts."""
    def ignore(path: str, names: list[str]) -> set[str]:
        current = Path(path)
        ignored: set[str] = set()
        if current == source and "truth" in names:
            ignored.add("truth")
        if current == source and "paper_response_metadata.json" in names:
            ignored.add("paper_response_metadata.json")
        return ignored

    shutil.copytree(source, destination, ignore=ignore)
    for relative in FORBIDDEN_RELATIVE_PATHS:
        if (destination / relative).exists():
            raise AssertionError(f"forbidden estimator artifact copied: {relative}")


def _geometry_hash(range_bins: np.ndarray, angle_bins: np.ndarray, angle_deg: np.ndarray,
                   beta: np.ndarray, selected: np.ndarray) -> str:
    payload = {
        "range_bins": np.asarray(range_bins, dtype=int).tolist(),
        "angle_bins": np.asarray(angle_bins, dtype=int).tolist(),
        "angle_deg": np.asarray(angle_deg, dtype=float).tolist(),
        "beta": np.asarray(beta, dtype=float).tolist(),
        "selected": np.asarray(selected, dtype=int).tolist(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _run_loop(capture, *, window_frames: int, output_frames: int,
              first_output_frame: int) -> list[dict[str, object]]:
    if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
        raise AssertionError("truth reached estimator CapturePackage")
    if first_output_frame < window_frames - 1:
        raise ValueError("first_output_frame must have a complete causal window")
    if capture.adc_cube.shape[0] <= first_output_frame + output_frames - 1:
        raise ValueError("capture does not contain enough radar frames for requested loop")
    rows: list[dict[str, object]] = []
    for output_index in range(output_frames):
        frame_index = first_output_frame + output_index
        window_start = frame_index - window_frames + 1
        window_stop = frame_index + 1
        if window_stop != frame_index + 1 or window_start < 0:
            raise AssertionError("invalid causal fence")
        processed = range_angle_process(capture.adc_cube[window_start:window_stop], capture.frontend)
        range_bins, angle_bins, detection = detect_target_bins(
            processed.cube, processed.angle_axis_deg, max_candidates=5
        )
        targets = extract_targets(processed, range_bins, angle_bins, capture.frontend)
        selected, initial_r, scores = select_targets(targets)
        current_phase = np.asarray(targets.wrapped_phase_rad[:, -1], dtype=float)
        available = np.asarray(targets.available_mask[:, -1], dtype=bool)
        beta = np.asarray(targets.measured_beta, dtype=float)
        if not np.isfinite(beta).all():
            raise AssertionError(f"non-finite beta at frame {frame_index}")
        if not np.isfinite(current_phase[available]).all():
            raise AssertionError(f"non-finite current phase at frame {frame_index}")
        rows.append({
            "output_index": output_index,
            "frame_index": frame_index,
            "window_frame_range": [window_start, frame_index],
            "window_size": window_stop - window_start,
            "future_frame_count": 0,
            "candidate_count": int(detection["candidate_count"]),
            "target_count": int(targets.range_bins.size),
            "selected_indices": np.asarray(selected, dtype=int).tolist(),
            "range_bins": np.asarray(targets.range_bins, dtype=int).tolist(),
            "angle_bins": np.asarray(targets.angle_bins, dtype=int).tolist(),
            "angle_deg": np.asarray(targets.angle_deg, dtype=float).tolist(),
            "beta": beta.tolist(),
            "current_phase_rad": current_phase.tolist(),
            "current_available_count": int(np.sum(available)),
            "geometry_hash": _geometry_hash(
                targets.range_bins, targets.angle_bins, targets.angle_deg, beta, selected
            ),
            "selection_score_min": float(np.min(scores)) if scores.size else None,
            "initial_r": np.asarray(initial_r, dtype=float).tolist(),
        })
    return rows


def _apply_test_only_perturbation(estimator_input: Path, *, start_frame: int,
                                  amplitude: float) -> dict[str, object]:
    """Perturb only estimator-copy ADC frames for a geometry-fence diagnostic."""
    manifest_path = estimator_input / "radar" / "algorithm_input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adc_path = manifest_path.parent / manifest["arrays"]["adc_cube"]["file"]
    adc = np.asarray(np.load(adc_path, allow_pickle=False), dtype=np.complex128)
    if start_frame < 0 or start_frame >= adc.shape[0]:
        raise ValueError("perturb_start_frame is outside the estimator ADC array")
    sample_index = np.arange(adc.shape[-1], dtype=float)
    tone = amplitude * np.exp(2j * np.pi * 100.0 * sample_index / adc.shape[-1])
    adc[start_frame:] += tone[None, None, :]
    np.save(adc_path, adc, allow_pickle=False)
    return {
        "enabled": True,
        "start_frame": int(start_frame),
        "end_frame": int(adc.shape[0] - 1),
        "amplitude": float(amplitude),
        "excluded_from_guard_and_rmse": True,
    }


def run_smoke(output: Path, *, seed: int = 20261001, requested_rms_mm: float = 0.0,
              window_frames: int = WINDOW_FRAMES, output_frames: int = OUTPUT_FRAMES,
              first_output_frame: int = WINDOW_FRAMES - 1,
              perturb_start_frame: int | None = None,
              perturb_amplitude: float = 20.0) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    protocol_path = Path(__file__).with_name("protocol.json")
    _json(output / "protocol.json", json.loads(protocol_path.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix="online-geometry-loop-") as temporary:
        root = Path(temporary)
        generated = root / "generated_with_evaluation_artifacts"
        estimator_input = root / "estimator_input_truth_free"
        _write_scratch_package(
            generated,
            stratum_name="stationary" if requested_rms_mm == 0.0 else "low_motion_scratch",
            requested_rms_mm=requested_rms_mm,
            seed=seed,
        )
        _copy_estimator_only(generated, estimator_input)
        perturbation = {"enabled": False}
        if perturb_start_frame is not None:
            perturbation = _apply_test_only_perturbation(
                estimator_input, start_frame=perturb_start_frame, amplitude=perturb_amplitude
            )
        capture = load_capture_package(estimator_input)
        rows = _run_loop(
            capture,
            window_frames=window_frames,
            output_frames=output_frames,
            first_output_frame=first_output_frame,
        )

        beta_first = np.asarray(rows[0]["beta"], dtype=float)
        beta_last = np.asarray(rows[-1]["beta"], dtype=float)
        beta_shape_equal = beta_first.shape == beta_last.shape
        beta_delta = np.abs(beta_last - beta_first) if beta_shape_equal else None
        report = {
            "schema": "online_geometry_loop_scratch_report",
            "status": "smoke_passed",
            "scope": "geometry_and_beta_update_only",
            "window_frames": window_frames,
            "output_frames": output_frames,
            "seed": seed,
            "requested_rms_mm": requested_rms_mm,
            "perturbation": perturbation,
            "first_output_frame": first_output_frame,
            "estimator_input": {
                "truth_present": (estimator_input / "truth").exists(),
                "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
                "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
                "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
                "estimator_root_sha256": _sha256_array(capture.adc_cube),
            },
            "causal_checks": {
                "all_windows_size_20": all(int(row["window_size"]) == window_frames for row in rows),
                "all_windows_end_at_current_frame": all(
                    row["window_frame_range"][1] == row["frame_index"] for row in rows
                ),
                "future_frame_count_zero": all(int(row["future_frame_count"]) == 0 for row in rows),
                "first_frame": int(rows[0]["frame_index"]),
                "last_frame": int(rows[-1]["frame_index"]),
            },
            "online_geometry": {
                "geometry_updates": len(rows),
                "geometry_hash_changes": int(sum(a["geometry_hash"] != b["geometry_hash"] for a, b in zip(rows, rows[1:]))),
                "target_count_first": int(beta_first.size),
                "target_count_last": int(beta_last.size),
                "target_count_changed": bool(not beta_shape_equal),
                "beta_first": beta_first.tolist(),
                "beta_last": beta_last.tolist(),
                "beta_abs_delta_first_to_last": beta_delta.tolist() if beta_delta is not None else None,
                "max_beta_abs_delta": float(np.max(beta_delta)) if beta_delta is not None and beta_delta.size else None,
                "all_beta_finite": bool(all(np.isfinite(np.asarray(row["beta"], dtype=float)).all() for row in rows)),
                "all_current_phase_available_finite": bool(all(row["current_available_count"] > 0 for row in rows)),
            },
            "kalman": {
                "run": False,
                "reason": "tracked run_fixed_beta_kalman accepts one beta vector for a whole run; online beta_t requires a stateful step API",
            },
        }
        _json(output / "rolling_geometry.json", rows)
        _json(output / "smoke_report.json", report)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a 20-frame causal geometry/beta scratch smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261001)
    parser.add_argument("--requested-rms-mm", type=float, default=0.0)
    parser.add_argument("--window-frames", type=int, default=WINDOW_FRAMES)
    parser.add_argument("--output-frames", type=int, default=OUTPUT_FRAMES)
    parser.add_argument("--first-output-frame", type=int, default=WINDOW_FRAMES - 1)
    parser.add_argument("--perturb-start-frame", type=int, default=None)
    parser.add_argument("--perturb-amplitude", type=float, default=20.0)
    args = parser.parse_args()
    if args.window_frames != WINDOW_FRAMES or args.output_frames != OUTPUT_FRAMES:
        parser.error("this prototype is intentionally fixed at a 20-frame window and 20 outputs")
    report = run_smoke(
        args.output,
        seed=args.seed,
        requested_rms_mm=args.requested_rms_mm,
        window_frames=args.window_frames,
        output_frames=args.output_frames,
        first_output_frame=args.first_output_frame,
        perturb_start_frame=args.perturb_start_frame,
        perturb_amplitude=args.perturb_amplitude,
    )
    print(json.dumps({"status": report["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
