"""Run a 2-seed x 5-stratum calibration-only geometry smoke comparison.

All files are scratch-only.  Each trial uses the current capture-package
builder, freezes RA geometry from ADC frames 0:200, and runs the retained
fixed-beta Kalman only on frames 200:400.  The current full-window route is
run beside it on the same truth-free package for an explicitly qualified
comparison.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from algorithm.run import run as run_full_window  # noqa: E402
from paper_bridge_simulation import package_builder as pb  # noqa: E402
from spatial_recovery_rebuilt.calibration_only.calibration_only_route import (  # noqa: E402
    CALIBRATION_FRAMES,
    RADAR_FRAMES,
    calibration_geometry,
    run_calibration_only,
)
from spatial_recovery_rebuilt.rebuild_validation import (  # noqa: E402
    _json,
    _write_scratch_package,
    freeze_guards,
    verify_frozen_test,
    verify_package,
)


SEEDS = (20261001, 20261002)
STRATA = (
    ("stationary", 0.0),
    ("low_motion_0p005mm", 0.005),
    ("low_motion_0p010mm", 0.010),
    ("low_motion_0p020mm", 0.020),
    ("low_motion_0p050mm", 0.050),
)
TEST_SLICE = slice(CALIBRATION_FRAMES, RADAR_FRAMES)
SUCCESS_THRESHOLD_MM = 0.010


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_array_prefix(path: Path, count: int) -> str:
    values = np.load(path, allow_pickle=False, mmap_mode="r")
    return _sha256_bytes(np.asarray(values[:count]).tobytes(order="C"))


def _copy_truth_free(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("truth", "paper_response_metadata.json"))


def _truth_reference(capture) -> tuple[np.ndarray, float]:
    frame_truth = np.interp(
        capture.radar_time_ns.astype(np.float64),
        np.asarray(capture.truth_time_ns, dtype=np.float64),
        np.asarray(capture.truth_displacement_m, dtype=float),
    )
    elapsed = (capture.radar_time_ns.astype(np.float64) - float(capture.radar_time_ns[0])) * 1.0e-9
    warm = elapsed <= 0.20
    return frame_truth, float(np.mean(frame_truth[warm]))


def _score(q_hat: np.ndarray, test_truth: np.ndarray, reference: float, accepted: bool) -> dict[str, object]:
    q_hat = np.asarray(q_hat, dtype=float)
    error = q_hat - (test_truth - reference)
    finite = error[np.isfinite(error)]
    rmse_m = float(np.sqrt(np.mean(finite * finite))) if finite.size else None
    return {
        "test_sample_count": int(test_truth.size),
        "finite_test_samples": int(finite.size),
        "test_sample_coverage": float(finite.size / test_truth.size) if test_truth.size else 0.0,
        "test_rmse_m": rmse_m,
        "test_rmse_mm": rmse_m * 1.0e3 if rmse_m is not None else None,
        "accepted": bool(accepted),
        "all_trial_success": bool(accepted and rmse_m is not None and rmse_m * 1.0e3 <= SUCCESS_THRESHOLD_MM),
    }


def _geometry_probe(source: Path) -> dict[str, object]:
    """Show test-only ADC changes do not change calibration-only geometry."""
    adc_rel = Path("radar") / "algorithm_input" / "adc_cube.npy"
    with tempfile.TemporaryDirectory(prefix="calibration-only-geometry-probe-") as temporary:
        root = Path(temporary)
        baseline = root / "baseline"
        perturbed = root / "perturbed"
        _copy_truth_free(source, baseline)
        _copy_truth_free(source, perturbed)
        manifest = json.loads((perturbed / adc_rel.parent / "manifest.json").read_text(encoding="utf-8"))
        adc_path = perturbed / adc_rel.parent / manifest["arrays"]["adc_cube"]["file"]
        adc = np.load(adc_path, allow_pickle=False)
        calibration_before = np.asarray(adc[:CALIBRATION_FRAMES]).tobytes(order="C")
        test_before = np.asarray(adc[CALIBRATION_FRAMES:]).tobytes(order="C")
        n = np.arange(adc.shape[-1], dtype=float)
        adc[CALIBRATION_FRAMES:] += 20.0 * np.exp(2j * np.pi * 100.0 * n / adc.shape[-1])[None, None, :]
        np.save(adc_path, adc, allow_pickle=False)
        calibration_after = np.asarray(adc[:CALIBRATION_FRAMES]).tobytes(order="C")
        test_after = np.asarray(adc[CALIBRATION_FRAMES:]).tobytes(order="C")
        base_geometry = calibration_geometry(load_capture_package(baseline))["geometry"]
        pert_geometry = calibration_geometry(load_capture_package(perturbed))["geometry"]
        return {
            "truth_present_in_estimator_copies": bool((baseline / "truth").exists() or (perturbed / "truth").exists()),
            "calibration_frames_unchanged": calibration_before == calibration_after,
            "test_frames_changed": test_before != test_after,
            "calibration_adc_sha256_before": _sha256_bytes(calibration_before),
            "calibration_adc_sha256_after": _sha256_bytes(calibration_after),
            "test_adc_sha256_before": _sha256_bytes(test_before),
            "test_adc_sha256_after": _sha256_bytes(test_after),
            "baseline_geometry_hash": base_geometry["geometry_hash"],
            "perturbed_geometry_hash": pert_geometry["geometry_hash"],
            "frozen_target_angle_beta_unchanged": base_geometry == pert_geometry,
            "perturbation": "diagnostic complex tone added only to ADC frames 200:399; guard not evaluated on perturbed copy",
        }


def _run_trial(output: Path, stratum: str, requested_rms_mm: float, seed: int) -> dict[str, object]:
    trial_id = f"{stratum}__seed{seed}"
    trial_dir = output / "trials" / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"calibration-only-{trial_id}-", dir=str(output / "_work")))
    package = work / "capture"
    estimator_package = work / "estimator_input"
    started = time.monotonic()
    try:
        realized = _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
        package_contract = verify_package(package)
        guards = freeze_guards(package)
        frozen_guard = verify_frozen_test(package, guards)
        _copy_truth_free(package, estimator_package)

        truth_capture = load_capture_package(package)
        truth_frame, reference = _truth_reference(truth_capture)
        test_truth = truth_frame[TEST_SLICE]
        calibration_adc = package / "radar" / "algorithm_input" / "adc_cube.npy"
        calibration_adc_hash = _sha256_array_prefix(calibration_adc, CALIBRATION_FRAMES)
        calibration_adxl = package / "adxl355" / "algorithm_input" / "acceleration_mps2.npy"
        calibration_adxl_hash = _sha256_array_prefix(calibration_adxl, CALIBRATION_FRAMES * 10)

        full_result_path = work / "full_window_result.npz"
        _, full_summary_path = run_full_window(estimator_package, full_result_path, radar_mode="frame")
        full_result = np.load(full_result_path, allow_pickle=False)
        full_capture = load_capture_package(estimator_package)
        full_geometry = {
            "target_count": int(full_result["selected_target_indices"].size),
            "target_angle_deg": full_result["target_angle_deg"].astype(float).tolist(),
            "measured_beta": full_result["radar_measured_beta"].astype(float).tolist(),
            "selected_indices": full_result["selected_target_indices"].astype(int).tolist(),
        }
        full_score = _score(full_result["q_hat_m"][TEST_SLICE], test_truth, reference, True)

        cal_result, cal_radar, frozen = run_calibration_only(
            full_capture, AlgorithmConfig(sample_rate_hz=100.0)
        )
        cal_score = _score(cal_result.q_hat_m, test_truth, reference, True)
        record = {
            "schema": "spatial_recovery_rebuilt.calibration_only_trial",
            "trial_id": trial_id,
            "stratum": stratum,
            "seed": seed,
            "realized_rms": realized,
            "package_contract": package_contract,
            "frozen_guard": frozen_guard,
            "guard_semantics": {
                "limits_source": "calibration ADC/ADXL only",
                "calibration_frames": [0, 199],
                "test_frames_checked": [200, 399],
                "test_adxl_samples_checked": [2000, 3999],
            },
            "score_reference": {
                "definition": "truth interpolated on physical radar frame grid; mean where elapsed <= 0.20 s",
                "warm_reference_sample_count": 21,
                "reference_m": reference,
                "test_frames_scored": [200, 399],
                "truth_used_post_run_only": True,
            },
            "calibration_input_hashes": {
                "adc_frames_0_199_sha256": calibration_adc_hash,
                "adxl_samples_0_1999_sha256": calibration_adxl_hash,
            },
            "full_window_route": {
                "geometry_source_frames": [0, 399],
                "kalman_input_frames": [0, 399],
                "method": json.loads(full_summary_path.read_text(encoding="utf-8")).get("method"),
                "geometry": full_geometry,
                "score": full_score,
            },
            "calibration_only_route": {
                "geometry_source_frames": [0, 199],
                "phase_input_frames": [200, 399],
                "kalman_input_frames": [200, 399],
                "cold_start_scope": "fresh Kalman state on the 200 test samples; retained filter cold-start logic",
                "geometry": frozen["geometry"],
                "score": cal_score,
                "test_samples_finite": bool(np.isfinite(cal_result.q_hat_m).all()),
                "test_target_count": int(cal_radar.selected_indices.size),
            },
            "difference": {
                "test_rmse_delta_calibration_only_minus_full_window_mm": (
                    cal_score["test_rmse_mm"] - full_score["test_rmse_mm"]
                    if cal_score["test_rmse_mm"] is not None and full_score["test_rmse_mm"] is not None else None
                ),
                "target_count_equal": int(cal_radar.selected_indices.size) == int(full_result["selected_target_indices"].size),
                "full_window_and_calibration_only_are_state_matched": False,
                "reason": "full-window route filters 400 samples; calibration-only route starts the retained Kalman on test frames 200:399",
            },
            "completed_at": _now(),
            "duration_s": time.monotonic() - started,
        }
        _json(trial_dir / "trial.json", record)
        return record
    except Exception as exc:
        record = {
            "schema": "spatial_recovery_rebuilt.calibration_only_trial",
            "trial_id": trial_id,
            "stratum": stratum,
            "seed": seed,
            "status": "error",
            "error": f"{type(exc).__name__}:{exc}",
            "completed_at": _now(),
            "duration_s": time.monotonic() - started,
        }
        _json(trial_dir / "trial.json", record)
        return record
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _aggregate(records: list[dict[str, object]]) -> dict[str, object]:
    complete = [row for row in records if "full_window_route" in row and "calibration_only_route" in row]
    def route_summary(name: str) -> dict[str, object]:
        scores = [row[name]["score"] for row in complete]
        rms = [float(s["test_rmse_mm"]) for s in scores if s.get("test_rmse_mm") is not None]
        return {
            "trials": len(scores),
            "finite_test_coverage": float(sum(int(s["finite_test_samples"]) for s in scores) / max(1, sum(int(s["test_sample_count"]) for s in scores))),
            "accepted_only_rmse_mm_mean_of_trials": float(np.mean(rms)) if rms else None,
            "all_trial_successes": sum(bool(s["all_trial_success"]) for s in scores),
            "all_trial_success_rate": float(sum(bool(s["all_trial_success"]) for s in scores) / len(scores)) if scores else 0.0,
        }
    deltas = [row["difference"]["test_rmse_delta_calibration_only_minus_full_window_mm"] for row in complete]
    return {
        "schema": "spatial_recovery_rebuilt.calibration_only_smoke_summary",
        "trial_count": len(records),
        "completed_trials": len(complete),
        "error_trials": len(records) - len(complete),
        "seed_values": list(SEEDS),
        "strata": [name for name, _ in STRATA],
        "routes": {
            "full_window": route_summary("full_window_route"),
            "calibration_only": route_summary("calibration_only_route"),
        },
        "rmse_delta_mm_mean": float(np.mean(deltas)) if deltas else None,
        "geometry_probe": None,
        "comparison_caveat": "RMSE comparison uses the same post-run 21-frame reference and test slice, but Kalman state histories differ because full-window sees 400 samples while calibration-only starts on 200 test samples.",
    }


def main() -> None:
    output = Path(__file__).resolve().parent / "smoke"
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing calibration-only smoke: {output}")
    output.mkdir(parents=True)
    (output / "_work").mkdir()
    manifest = {
        "schema": "spatial_recovery_rebuilt.calibration_only_smoke",
        "protocol": "2 seeds x 5 strata; 200 calibration + 200 test",
        "claims_parity_with_lost_workspace": False,
        "seeds": list(SEEDS),
        "strata": [{"name": name, "requested_q_true_rms_mm": rms} for name, rms in STRATA],
        "calibration_frames": [0, 199],
        "test_frames": [200, 399],
        "started_at": _now(),
        "status": "running",
    }
    _json(output / "run_manifest.json", manifest)
    records: list[dict[str, object]] = []
    for stratum, rms in STRATA:
        for seed in SEEDS:
            print(f"running {stratum} seed={seed}", flush=True)
            records.append(_run_trial(output, stratum, rms, seed))
    summary = _aggregate(records)
    source_probe = SCRATCH / "smoke" / "capture_low_motion_0p005mm_seed20261001"
    if source_probe.is_dir():
        summary["geometry_probe"] = _geometry_probe(source_probe)
    summary["completed_at"] = _now()
    _json(output / "summary.json", summary)
    manifest["status"] = "completed"
    manifest["completed_at"] = summary["completed_at"]
    _json(output / "run_manifest.json", manifest)
    shutil.rmtree(output / "_work", ignore_errors=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
