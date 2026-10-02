"""Strict calibration-only P1 matrix (scratch-only).

This runner deliberately calls the existing calibration_only route and never
runs the retained full-window route.  Each estimator receives a truth-free
copy.  Geometry is frozen from ADC frames 0:200; test phase/Kalman input is
frames 200:400 only.  Raw capture packages are deleted after each trial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from spatial_recovery_rebuilt.rebuild_validation import (  # noqa: E402
    CALIBRATION_FRAMES,
    RADAR_FRAMES,
    STRATA,
    _json,
    _write_scratch_package,
    freeze_guards,
    git_status,
    verify_frozen_test,
    verify_package,
)
from spatial_recovery_rebuilt.calibration_only import calibration_only_wrapper as cow  # noqa: E402
from spatial_recovery_rebuilt.calibration_only.calibration_only_route import (  # noqa: E402
    run_calibration_only,
)

FULL_SEEDS = tuple(range(7200, 7240))
SMOKE_SEEDS = FULL_SEEDS[:2]
SUCCESS_THRESHOLD_MM = 0.010
TEST_SAMPLE_COUNT = RADAR_FRAMES - CALIBRATION_FRAMES
TEST_SLICE = slice(CALIBRATION_FRAMES, RADAR_FRAMES)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_array_prefix(path: Path, count: int) -> str:
    values = np.load(path, allow_pickle=False, mmap_mode="r")
    return _sha256_bytes(np.asarray(values[:count]).tobytes(order="C"))


def _score(q_hat: np.ndarray, truth_test_centered: np.ndarray) -> dict[str, object]:
    q_hat = np.asarray(q_hat, dtype=float)
    truth_test_centered = np.asarray(truth_test_centered, dtype=float)
    if q_hat.size != TEST_SAMPLE_COUNT or truth_test_centered.size != TEST_SAMPLE_COUNT:
        raise ValueError(f"unexpected test sizes q_hat={q_hat.shape} truth={truth_test_centered.shape}")
    error = q_hat - truth_test_centered
    finite = error[np.isfinite(error)]
    rmse_m = float(np.sqrt(np.mean(finite * finite))) if finite.size else None
    bias_m = float(np.mean(finite)) if finite.size else None
    return {
        "test_sample_count": TEST_SAMPLE_COUNT,
        "finite_test_samples": int(finite.size),
        "test_sample_coverage": float(finite.size / TEST_SAMPLE_COUNT),
        "test_rmse_m": rmse_m,
        "test_rmse_mm": rmse_m * 1.0e3 if rmse_m is not None else None,
        "test_bias_m": bias_m,
        "test_bias_mm": bias_m * 1.0e3 if bias_m is not None else None,
        "all_trial_success": bool(rmse_m is not None and rmse_m * 1.0e3 <= SUCCESS_THRESHOLD_MM),
    }


def _run_trial(output: Path, stratum: str, requested_rms_mm: float, seed: int) -> dict[str, object]:
    trial_id = f"{stratum}__seed{seed:04d}"
    trial_dir = output / "trials" / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    work_root = output / "_work"
    work_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"strict-{trial_id}-", dir=str(work_root)))
    package = work / "capture"
    estimator_package = work / "estimator_input"
    base: dict[str, object] = {
        "schema": "spatial_recovery_rebuilt.strict_calibration_only_trial",
        "trial_id": trial_id,
        "stratum": stratum,
        "seed": seed,
        "requested_q_true_rms_mm": requested_rms_mm,
        "geometry_source_frames": [0, 199],
        "phase_input_frames": [200, 399],
        "kalman_input_frames": [200, 399],
        "test_target_detection_executed": False,
        "test_geometry_operations": ["range_fft", "fixed_angle_steering_projection"],
        "forbidden_test_geometry_operations": ["detect_target_bins", "extract_targets", "estimate_local_music_ml", "select_targets", "angle_derived_beta_update"],
        "guards_fixed_before_test": True,
        "truth_used_post_run_only": True,
        "q_proxy_used_by_estimator": False,
        "started_at": _now(),
    }
    try:
        realized = _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
        base["realized_rms"] = realized
        contract = verify_package(package)
        base["package_contract"] = contract
        guards = freeze_guards(package)
        base["guards"] = guards
        frozen_guard = verify_frozen_test(package, guards)
        base["frozen_guard"] = frozen_guard
        # Keep only estimator input files; truth and response metadata are omitted.
        cow._copy_estimator_package(package, estimator_package)
        truth_free = not (estimator_package / "truth").exists() and not (estimator_package / "paper_response_metadata.json").exists()
        base["truth_free_estimator_copy"] = truth_free
        if not truth_free:
            raise RuntimeError("estimator copy unexpectedly contains truth or paper metadata")
        # Run only the strict calibration-frozen route. No full-window route is called.
        capture = load_capture_package(estimator_package)
        result, radar, frozen = run_calibration_only(capture, AlgorithmConfig(sample_rate_hz=100.0))
        q_hat = np.asarray(result.q_hat_m, dtype=float)
        truth_centered = cow._reference_and_test_truth(package, np.asarray(radar.extra["radar_time_ns"], dtype=np.int64))
        score = _score(q_hat, truth_centered)
        accepted = bool(frozen_guard.get("passed")) and bool(truth_free)
        finite_accepted = bool(accepted and score["finite_test_samples"] == TEST_SAMPLE_COUNT)
        calibration_adc = package / "radar" / "algorithm_input" / "adc_cube.npy"
        calibration_adxl = package / "adxl355" / "algorithm_input" / "acceleration_mps2.npy"
        base.update({
            "status": "accepted" if accepted else "rejected",
            "accepted": accepted,
            "accepted_finite_test": finite_accepted,
            "metrics": score,
            "all_trial_success": bool(finite_accepted and score["all_trial_success"]),
            "calibration_input_hashes": {
                "adc_frames_0_199_sha256": _sha256_array_prefix(calibration_adc, CALIBRATION_FRAMES),
                "adxl_samples_0_1999_sha256": _sha256_array_prefix(calibration_adxl, CALIBRATION_FRAMES * 10),
            },
            "route_audit": {
                "geometry_source_frames": [0, 199],
                "phase_input_frames": [200, 399],
                "kalman_input_frames": [200, 399],
                "fresh_kalman_state": True,
                "test_target_detection_executed": False,
                "test_target_count": int(np.asarray(radar.selected_indices).size),
                "frozen_geometry_hash": frozen["geometry"]["geometry_hash"],
                "frozen_geometry_frame_range": frozen["geometry"]["calibration_frame_range"],
            },
        })
    except Exception as exc:
        base.update({
            "status": "error",
            "accepted": False,
            "accepted_finite_test": False,
            "all_trial_success": False,
            "rejection_reasons": [f"{type(exc).__name__}:{exc}"],
            "metrics": {
                "test_sample_count": TEST_SAMPLE_COUNT,
                "finite_test_samples": 0,
                "test_sample_coverage": 0.0,
                "test_rmse_m": None,
                "test_rmse_mm": None,
                "test_bias_m": None,
                "test_bias_mm": None,
                "all_trial_success": False,
            },
        })
    finally:
        shutil.rmtree(work, ignore_errors=True)
    base["duration_s"] = time.monotonic() - started
    base["completed_at"] = _now()
    _json(trial_dir / "trial.json", base)
    return base


def _aggregate(records: list[dict[str, object]], seed_values: tuple[int, ...]) -> dict[str, object]:
    accepted = [r for r in records if r.get("accepted") is True]
    finite_accepted = [r for r in records if r.get("accepted_finite_test") is True]
    rms = [float(r["metrics"]["test_rmse_m"]) for r in finite_accepted if r["metrics"].get("test_rmse_m") is not None]
    biases = [float(r["metrics"]["test_bias_m"]) for r in finite_accepted if r["metrics"].get("test_bias_m") is not None]
    pooled_errors_sq = []
    # Recompute pooled RMSE from per-trial RMSE with equal 200-frame weighting.
    for r in finite_accepted:
        m = r["metrics"]
        if m.get("test_rmse_m") is not None:
            pooled_errors_sq.extend([float(m["test_rmse_m"]) ** 2] * TEST_SAMPLE_COUNT)
    by_stratum: dict[str, object] = {}
    for name, _rms in STRATA:
        rows = [r for r in records if r.get("stratum") == name]
        acc = [r for r in rows if r.get("accepted") is True]
        frms = [float(r["metrics"]["test_rmse_m"]) for r in rows if r.get("accepted_finite_test") is True and r["metrics"].get("test_rmse_m") is not None]
        by_stratum[name] = {
            "trials": len(rows),
            "accepted": len(acc),
            "acceptance_coverage": float(len(acc) / len(rows)) if rows else 0.0,
            "accepted_only_rmse_mm_mean_of_trials": float(np.mean(frms) * 1.0e3) if frms else None,
            "all_trial_successes": int(sum(bool(r.get("all_trial_success")) for r in rows)),
            "all_trial_success_rate": float(sum(bool(r.get("all_trial_success")) for r in rows) / len(rows)) if rows else 0.0,
        }
    total = len(records)
    return {
        "schema": "spatial_recovery_rebuilt.strict_calibration_only_matrix_summary",
        "protocol": "P1 strict calibration-frozen route; 200 calibration + 200 test; no full-window comparison",
        "claims_parity_with_lost_workspace": False,
        "seed_range": [seed_values[0], seed_values[-1]],
        "seed_values": list(seed_values),
        "strata": [name for name, _ in STRATA],
        "trial_count": total,
        "expected_trial_count": len(seed_values) * len(STRATA),
        "accepted_trials": len(accepted),
        "abstention_or_error_trials": total - len(accepted),
        "acceptance_coverage": float(len(accepted) / total) if total else 0.0,
        "finite_test_sample_coverage_with_abstentions_zero": float(sum(int(r.get("metrics", {}).get("finite_test_samples", 0)) for r in records) / max(1, total * TEST_SAMPLE_COUNT)),
        "accepted_only_rmse_mm_pooled": float(np.sqrt(np.mean(pooled_errors_sq)) * 1.0e3) if pooled_errors_sq else None,
        "accepted_only_rmse_mm_mean_of_trials": float(np.mean(rms) * 1.0e3) if rms else None,
        "accepted_only_bias_mm_mean_of_trials": float(np.mean(biases) * 1.0e3) if biases else None,
        "all_trial_successes_with_abstentions_counted_as_failure": int(sum(bool(r.get("all_trial_success")) for r in records)),
        "all_trial_success_rate_with_abstentions_counted_as_failure": float(sum(bool(r.get("all_trial_success")) for r in records) / total) if total else 0.0,
        "by_stratum": by_stratum,
        "caveats": {
            "cold_start": "Every trial starts a fresh retained Kalman state on test frames 200:399; first 0.20 s of that test state uses retained cold-start logic, so comparison to any full-window warm state would be state-mismatched.",
            "bias": "RMSE uses post-run truth only and a 21-frame warm reference; reported bias is diagnostic and does not establish unbiasedness or online deployment.",
            "R": "The retained Kalman adaptive R settings are unchanged; this matrix does not independently calibrate or identify measurement-noise R.",
            "deployment": "Scratch synthetic-package calibration-only evidence; no online deployment or parity claim.",
        },
    }


def run_matrix(output: Path, seed_values: tuple[int, ...], mode: str) -> dict[str, object]:
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "trials").mkdir()
    (output / "_work").mkdir()
    (output / "_tmp").mkdir()
    # Keep package_builder staging on the same filesystem as the output;
    # cross-device rename from /tmp would otherwise fail in this sandbox.
    tempfile.tempdir = str(output / "_tmp")
    status_before = git_status()
    source_sha = cow._source_hashes()
    source_sha["spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/run_strict_matrix.py"] = _sha256_bytes(SCRATCH.joinpath("run_strict_matrix.py").read_bytes())
    manifest = {
        "schema": "spatial_recovery_rebuilt.strict_calibration_only_matrix_run",
        "status": "running",
        "mode": mode,
        "seed_values": list(seed_values),
        "strata": [{"name": name, "requested_q_true_rms_mm": rms} for name, rms in STRATA],
        "trial_count": len(seed_values) * len(STRATA),
        "geometry_source_frames": [0, 199],
        "phase_input_frames": [200, 399],
        "kalman_input_frames": [200, 399],
        "truth_free_estimator_copy": True,
        "guards_fixed_before_test": True,
        "test_target_detection_executed": False,
        "full_window_route_called": False,
        "source_sha256": source_sha,
        "git_status_before": status_before,
        "started_at": _now(),
    }
    _json(output / "run_manifest.json", manifest)
    records: list[dict[str, object]] = []
    probe = None
    completed = 0
    for stratum, requested_rms_mm in STRATA:
        for seed in seed_values:
            rec = _run_trial(output, stratum, requested_rms_mm, seed)
            records.append(rec)
            completed += 1
            if probe is None:
                # Rebuild one disposable package solely for test-only perturbation audit.
                with tempfile.TemporaryDirectory(prefix="strict-probe-") as td:
                    package = Path(td) / "capture"
                    _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
                    probe = cow._run_probe(package)
                _json(output / "test_only_perturbation_probe.json", probe)
            if completed == 1 or completed % 10 == 0 or completed == len(seed_values) * len(STRATA):
                print(f"completed {completed}/{len(seed_values) * len(STRATA)}: {rec['trial_id']} status={rec['status']}", flush=True)
            _json(output / "progress.json", {"status": "running", "completed_trials": completed, "expected_trials": len(seed_values) * len(STRATA), "last_trial": rec["trial_id"], "updated_at": _now()})
    summary = _aggregate(records, seed_values)
    summary["completed_at"] = _now()
    summary["test_only_perturbation_probe"] = probe
    summary["git_status_after"] = git_status()
    _json(output / "summary.json", summary)
    # A compact copy of all trial metadata is convenient for independent review.
    _json(output / "trials.json", records)
    manifest.update({"status": "completed", "completed_at": summary["completed_at"], "git_status_after": summary["git_status_after"]})
    _json(output / "run_manifest.json", manifest)
    _json(output / "progress.json", {"status": "completed", "completed_trials": len(records), "expected_trials": len(records), "updated_at": _now()})
    shutil.rmtree(output / "_work", ignore_errors=True)
    shutil.rmtree(output / "_tmp", ignore_errors=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "full"), default="full")
    args = parser.parse_args()
    seeds = SMOKE_SEEDS if args.mode == "smoke" else FULL_SEEDS
    summary = run_matrix(args.output, seeds, args.mode)
    print(json.dumps({"status": "completed", "mode": args.mode, "output": str(args.output), "trial_count": summary["trial_count"], "accepted_trials": summary["accepted_trials"], "accepted_only_rmse_mm_pooled": summary["accepted_only_rmse_mm_pooled"], "all_trial_success_rate": summary["all_trial_success_rate_with_abstentions_counted_as_failure"]}, indent=2))


if __name__ == "__main__":
    main()
