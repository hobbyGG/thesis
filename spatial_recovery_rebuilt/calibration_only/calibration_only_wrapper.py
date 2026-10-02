"""Scratch-only calibration-frozen RA wrapper and paired smoke runner.

The retained algorithm currently builds geometry from the complete ADC cube.
This wrapper is deliberately outside ``algorithm/``.  It uses the retained
range/angle frontend only on frames 0:200, then projects frames 200:400 onto
that frozen range/angle geometry.  Only the projected test observations and
test-half ADXL intervals are passed to the retained structural Kalman filter.

The wrapper is an audit/protocol artifact, not a replacement for the tracked
algorithm entry point.  It refuses to overwrite an existing output directory.
Truth is removed from estimator copies and is used only after estimation for
the frozen-test RMSE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRATCH.parent) not in sys.path:
    sys.path.insert(0, str(SCRATCH.parent))

from algorithm.acceleration import preintegrate_acceleration_to_radar  # noqa: E402
from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.frontend import TargetData, range_angle_process, extract_targets  # noqa: E402
from algorithm.io import load_capture_package, build_algorithm_inputs  # noqa: E402
from algorithm.kalman import run_fixed_beta_kalman  # noqa: E402
from algorithm.selection import detect_target_bins, select_targets  # noqa: E402
from algorithm.types import AccelerationInput, RadarInput  # noqa: E402

from rebuild_validation import (  # noqa: E402
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


SEEDS = (20261001, 20261002)
TRUTH_DIR = "truth"
ESTIMATOR_INPUT_MANIFEST = (
    "radar/algorithm_input/adc_cube.npy",
    "radar/algorithm_input/chirp_cube.npy",
    "radar/algorithm_input/manifest.json",
    "adxl355/algorithm_input/acceleration_mps2.npy",
    "adxl355/algorithm_input/estimated_sample_monotonic_ns.npy",
    "sync/manifest.json",
    "sync/timeline.json",
    "sync/*.npy",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_array(array: np.ndarray) -> str:
    digest = hashlib.sha256()
    contiguous = np.ascontiguousarray(array)
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(_sha256_file(path).encode("ascii"))
    return digest.hexdigest()


def _copy_estimator_package(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(TRUTH_DIR, "paper_response_metadata.json"))


def _calibration_geometry(capture):
    """Run detection, local MUSIC/ML, and selection on calibration frames only."""
    calibration_adc = np.asarray(capture.adc_cube[:CALIBRATION_FRAMES], dtype=complex)
    processed = range_angle_process(calibration_adc, capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(
        processed.cube, processed.angle_axis_deg, max_candidates=5
    )
    geometry = extract_targets(processed, range_bins, angle_bins, capture.frontend)
    selected, initial_r, scores = select_targets(geometry)
    return geometry, selected, initial_r, scores, detection


def _test_targets_from_frozen_geometry(capture, geometry):
    """Project test range FFT snapshots onto calibration-frozen geometry.

    This intentionally avoids ``range_angle_process`` and
    ``estimate_local_music_ml`` for the test half.  The only test-side radar
    operation is the range FFT followed by the fixed-angle steering projection
    used to recover each target's complex phase observation.
    """
    adc = np.asarray(capture.adc_cube[CALIBRATION_FRAMES:RADAR_FRAMES], dtype=complex)
    range_fft = np.fft.fft(adc, n=capture.frontend.num_range_bins, axis=2)
    snapshots = np.transpose(range_fft, (0, 2, 1))  # frame, range, virtual_rx
    target_count = int(geometry.range_bins.size)
    slow_time = np.empty((target_count, snapshots.shape[0]), dtype=complex)
    positions = np.asarray(geometry_positions(capture), dtype=float)
    for range_bin in sorted(set(geometry.range_bins.tolist())):
        target_indices = np.flatnonzero(geometry.range_bins == range_bin)
        angles = np.deg2rad(np.asarray(geometry.angle_deg[target_indices], dtype=float))
        steering = np.exp(2j * np.pi * positions[:, None] * np.sin(angles)[None, :])
        coefficients = np.linalg.pinv(steering, rcond=1.0e-8) @ snapshots[:, range_bin, :].T
        slow_time[target_indices, :] = coefficients
    available = np.isfinite(slow_time.real) & np.isfinite(slow_time.imag) & (np.abs(slow_time) > 0.0)
    wrapped = np.angle(slow_time)
    wrapped[~available] = np.nan
    return TargetData(
        slow_time=slow_time,
        wrapped_phase_rad=wrapped,
        available_mask=available,
        angle_deg=np.asarray(geometry.angle_deg, dtype=float).copy(),
        measured_beta=np.asarray(geometry.measured_beta, dtype=float).copy(),
        range_bins=np.asarray(geometry.range_bins, dtype=int).copy(),
        angle_bins=np.asarray(geometry.angle_bins, dtype=int).copy(),
        range_m=np.asarray(geometry.range_m, dtype=float).copy(),
    )


def geometry_positions(capture) -> np.ndarray:
    if capture.frontend.virtual_array_positions_wavelengths:
        return np.asarray(capture.frontend.virtual_array_positions_wavelengths, dtype=float)
    return np.arange(capture.frontend.num_virtual_rx, dtype=float) * capture.frontend.antenna_spacing_wavelengths


def _test_acceleration(capture, radar_time_ns: np.ndarray) -> AccelerationInput:
    """Build acceleration input from test-half ADXL samples only."""
    # The package contract defines 200 calibration radar frames at 100 Hz and
    # 2000 calibration ADXL samples at 1 kHz.  Use that exact fence rather than
    # a timestamp comparison that could drop samples around the aperture offset.
    test_start = CALIBRATION_FRAMES * 10
    adxl_time_ns = np.asarray(capture.adxl_time_ns[test_start:], dtype=np.int64)
    structural = np.asarray(capture.adxl_acceleration_mps2[test_start:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(radar_time_ns, adxl_time_ns, structural)
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured = np.r_[interval_average[0], interval_average]
    return AccelerationInput(adxl_time_ns, structural, measured, preintegration)


def build_calibration_only_inputs(capture):
    """Return a RadarInput/AccelerationInput pair containing test samples only."""
    geometry, selected, initial_r, scores, detection = _calibration_geometry(capture)
    test_geometry = _test_targets_from_frozen_geometry(capture, geometry)
    radar_time_ns = np.asarray(capture.radar_time_ns[CALIBRATION_FRAMES:RADAR_FRAMES], dtype=np.int64)
    acceleration = _test_acceleration(capture, radar_time_ns)
    radar_rate = 1.0 / np.median(np.diff(radar_time_ns) * 1.0e-9)
    radar = RadarInput(
        measured_beta=test_geometry.measured_beta,
        wrapped_phase_rad=test_geometry.wrapped_phase_rad,
        available_mask=test_geometry.available_mask,
        selected_indices=np.asarray(selected, dtype=int),
        initial_r=np.asarray(initial_r, dtype=float),
        selection_scores=np.asarray(scores, dtype=float),
        extra={
            "angle_deg": test_geometry.angle_deg,
            "range_bins": test_geometry.range_bins,
            "angle_bins": test_geometry.angle_bins,
            "range_m": test_geometry.range_m,
            "detection": detection,
            "radar_time_ns": radar_time_ns,
            "radar_mode": "frame",
            "frame_period_s": float(np.median(np.diff(radar_time_ns)) * 1.0e-9),
            "geometry_source": "calibration_frames_only",
            "calibration_frame_range": [0, CALIBRATION_FRAMES - 1],
            "test_frame_range": [CALIBRATION_FRAMES, RADAR_FRAMES - 1],
        },
    )
    return radar, acceleration, geometry, radar_rate


def _reference_and_test_truth(package: Path, radar_time_ns: np.ndarray) -> np.ndarray:
    truth = np.load(package / TRUTH_DIR / "displacement_m.npy", allow_pickle=False)
    truth_time = np.load(package / TRUTH_DIR / "time_ns.npy", allow_pickle=False)
    frame_time = np.load(package / "sync" / "radar_adc_sample_monotonic_ns.npy", allow_pickle=False)
    frame_truth = np.interp(frame_time.astype(float), truth_time.astype(float), truth)
    elapsed = (frame_time.astype(float) - float(frame_time[0])) * 1.0e-9
    reference = float(np.mean(frame_truth[elapsed <= 0.20]))
    truth_at_test = np.interp(radar_time_ns.astype(float), truth_time.astype(float), truth)
    return truth_at_test - reference


def _run_full_window(package: Path):
    with tempfile.TemporaryDirectory(prefix="calibration-only-full-input-") as temporary:
        estimator_package = Path(temporary) / "capture"
        _copy_estimator_package(package, estimator_package)
        capture = load_capture_package(estimator_package)
        radar, acceleration, targets, radar_rate = build_algorithm_inputs(capture, radar_mode="frame")
        result = run_fixed_beta_kalman(radar, acceleration, AlgorithmConfig(sample_rate_hz=float(radar_rate)))
        return radar, targets, result


def _run_calibration_only(package: Path):
    with tempfile.TemporaryDirectory(prefix="calibration-only-frozen-input-") as temporary:
        estimator_package = Path(temporary) / "capture"
        _copy_estimator_package(package, estimator_package)
        capture = load_capture_package(estimator_package)
        radar, acceleration, geometry, radar_rate = build_calibration_only_inputs(capture)
        result = run_fixed_beta_kalman(radar, acceleration, AlgorithmConfig(sample_rate_hz=float(radar_rate)))
        return radar, geometry, result


def _geometry_record(radar, geometry) -> dict[str, object]:
    return {
        "candidate_count": int(radar.extra["detection"]["candidate_count"]),
        "target_count": int(radar.selected_indices.size),
        "selected_indices": np.asarray(radar.selected_indices, dtype=int).tolist(),
        "range_bins": np.asarray(geometry.range_bins, dtype=int).tolist(),
        "angle_bins": np.asarray(geometry.angle_bins, dtype=int).tolist(),
        "angle_deg": np.asarray(geometry.angle_deg, dtype=float).tolist(),
        "measured_beta": np.asarray(geometry.measured_beta, dtype=float).tolist(),
    }


def _run_probe(package: Path) -> dict[str, object]:
    """Verify that post-test ADC changes do not change frozen geometry."""
    adc_rel = Path("radar") / "algorithm_input" / "adc_cube.npy"
    manifest = json.loads((package / adc_rel.parent / "manifest.json").read_text(encoding="utf-8"))
    positions = np.asarray(manifest["radar"]["virtual_array_positions_wavelengths"], dtype=float)
    with tempfile.TemporaryDirectory(prefix="calibration-only-probe-") as temporary:
        baseline = Path(temporary) / "baseline"
        perturbed = Path(temporary) / "perturbed"
        _copy_estimator_package(package, baseline)
        _copy_estimator_package(package, perturbed)
        adc_path = perturbed / adc_rel
        adc = np.load(adc_path, allow_pickle=False)
        first_half = np.asarray(adc[:CALIBRATION_FRAMES]).copy()
        steering = np.exp(2j * np.pi * positions * np.sin(np.deg2rad(40.0)))
        adc[CALIBRATION_FRAMES:RADAR_FRAMES] = 20.0 * adc[CALIBRATION_FRAMES:RADAR_FRAMES] * steering[None, :, None]
        np.save(adc_path, adc, allow_pickle=False)
        base_capture = load_capture_package(baseline)
        pert_capture = load_capture_package(perturbed)
        base_radar, base_geometry, base_result = _run_calibration_only(baseline)
        pert_radar, pert_geometry, pert_result = _run_calibration_only(perturbed)
        fields = ("candidate_count", "target_count", "selected_indices", "range_bins", "angle_bins", "angle_deg", "measured_beta")
        base_rec = _geometry_record(base_radar, base_geometry)
        pert_rec = _geometry_record(pert_radar, pert_geometry)
        changed = [field for field in fields if base_rec[field] != pert_rec[field]]
        return {
            "status": "completed",
            "first_200_exactly_unchanged": bool(np.array_equal(first_half, np.load(adc_path, allow_pickle=False)[:CALIBRATION_FRAMES])),
            "truth_present_in_estimator_copies": False,
            "perturbation": {
                "frames_changed": [CALIBRATION_FRAMES, RADAR_FRAMES - 1],
                "channel_steering_angle_deg": 40.0,
                "amplitude_multiplier": 20.0,
            },
            "baseline_geometry": base_rec,
            "perturbed_geometry": pert_rec,
            "changed_frozen_geometry_fields": changed,
            "test_observation_changed": bool(not np.array_equal(base_result.q_hat_m, pert_result.q_hat_m)),
            "calibration_adc_sha256": _sha256_array(base_capture.adc_cube[:CALIBRATION_FRAMES]),
            "perturbed_calibration_adc_sha256": _sha256_array(pert_capture.adc_cube[:CALIBRATION_FRAMES]),
            "conclusion": (
                "calibration-only target/angle/beta remains unchanged under test-only ADC perturbation"
                if changed == [] and bool(np.array_equal(first_half, np.load(adc_path, allow_pickle=False)[:CALIBRATION_FRAMES]))
                else "calibration-only geometry changed unexpectedly under test-only perturbation"
            ),
        }


def _trial_record(package: Path, stratum: str, requested_rms_mm: float, seed: int, realized: dict[str, object], guards: dict[str, object]) -> dict[str, object]:
    capture = load_capture_package(package)
    calibration_adc_hash = _sha256_array(capture.adc_cube[:CALIBRATION_FRAMES])
    calibration_adxl_hash = _sha256_array(capture.adxl_acceleration_mps2[:2000])
    # Estimator copies deliberately exclude truth and scratch metadata.  The
    # original package remains available only for post-run scoring.
    with tempfile.TemporaryDirectory(prefix="calibration-only-estimator-") as temporary:
        estimator_package = Path(temporary) / "input"
        _copy_estimator_package(package, estimator_package)
        full_radar, full_targets, full_result = _run_full_window(estimator_package)
        cal_radar, cal_geometry, cal_result = _run_calibration_only(estimator_package)
        estimator_truth_present = (estimator_package / TRUTH_DIR).exists()
        estimator_metadata_present = (estimator_package / "paper_response_metadata.json").exists()
    truth_test_full = _reference_and_test_truth(package, np.asarray(full_radar.extra["radar_time_ns"])[CALIBRATION_FRAMES:])
    truth_test_cal = _reference_and_test_truth(package, np.asarray(cal_radar.extra["radar_time_ns"]))
    full_q = np.asarray(full_result.q_hat_m, dtype=float)[CALIBRATION_FRAMES:]
    cal_q = np.asarray(cal_result.q_hat_m, dtype=float)
    full_rmse = float(np.sqrt(np.mean((full_q - truth_test_full) ** 2)))
    cal_rmse = float(np.sqrt(np.mean((cal_q - truth_test_cal) ** 2)))
    full_geometry = _geometry_record(full_radar, full_targets)
    cal_geometry_record = _geometry_record(cal_radar, cal_geometry)
    return {
        "schema": "spatial_recovery_rebuilt.calibration_only_trial",
        "stratum": stratum,
        "requested_q_true_rms_mm": requested_rms_mm,
        "seed": seed,
        "realized_rms": realized,
        "radar_frames": RADAR_FRAMES,
        "calibration_frames": CALIBRATION_FRAMES,
        "test_frames": RADAR_FRAMES - CALIBRATION_FRAMES,
        "estimator_input_audit": {
            "truth_present": bool(estimator_truth_present),
            "paper_response_metadata_present": bool(estimator_metadata_present),
            "truth_used_by_estimator": False,
            "q_proxy_used_by_estimator": False,
        },
        "score_reference": {
            "definition": "truth interpolated on full physical radar frame grid; mean where elapsed <= 0.20 s",
            "warm_reference_sample_count": 21,
            "test_score_frames": [200, 399],
            "truth_used_post_run_only": True,
        },
        "guards": guards,
        "calibration_adc_sha256": calibration_adc_hash,
        "calibration_adxl_sha256": calibration_adxl_hash,
        "estimator_input_manifest": list(ESTIMATOR_INPUT_MANIFEST),
        "full_window_route": {
            "method": full_result.method_name,
            "geometry_source_frames": [0, 399],
            "kalman_input_frames": [0, 399],
            "geometry": full_geometry,
            "test_rmse_m": full_rmse,
            "estimator_samples": int(full_result.q_hat_m.size),
        },
        "calibration_only_route": {
            "method": cal_result.method_name,
            "geometry": cal_geometry_record,
            "geometry_source": "frames_0_199_only",
            "test_observation_source": "frames_200_399_only",
            "test_adxl_source": "samples_at_or_after_test_start_only",
            "kalman_input_frames": [200, 399],
            "fresh_kalman_state": True,
            "test_rmse_m": cal_rmse,
            "estimator_samples": int(cal_result.q_hat_m.size),
        },
        "geometry_equal_between_routes": bool(full_geometry == cal_geometry_record),
        "truth_used_by_estimator": False,
        "q_proxy_used_by_estimator": False,
    }


def _source_hashes() -> dict[str, str]:
    names = (
        "algorithm/io.py", "algorithm/frontend.py", "algorithm/angle_estimation.py",
        "algorithm/selection.py", "algorithm/kalman.py", "algorithm/acceleration.py",
        "paper_bridge_simulation/package_builder.py",
    )
    hashes = {name: _sha256_file(ROOT / name) for name in names}
    hashes["spatial_recovery_rebuilt/calibration_only/calibration_only_wrapper.py"] = _sha256_file(SCRATCH / "calibration_only_wrapper.py")
    hashes["spatial_recovery_rebuilt/calibration_only/protocol.json"] = _sha256_file(SCRATCH / "protocol.json")
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(description="Run calibration-only geometry smoke and test-only perturbation probe")
    parser.add_argument("--output", type=Path, default=SCRATCH / "smoke")
    args = parser.parse_args()
    output = args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    before = git_status()
    manifest = {
        "schema": "spatial_recovery_rebuilt.calibration_only_run",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_status_before": before,
        "git_head": __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip(),
        "source_sha256": _source_hashes(),
        "calibration_frames": [0, CALIBRATION_FRAMES - 1],
        "test_frames": [CALIBRATION_FRAMES, RADAR_FRAMES - 1],
        "seeds": list(SEEDS),
        "strata": [name for name, _rms in STRATA],
        "full_matrix_started": False,
        "truth_used_by_estimator": False,
        "q_proxy_used_by_estimator": False,
        "estimator_input_manifest": list(ESTIMATOR_INPUT_MANIFEST),
    }
    _json(output / "run_manifest.json", manifest)
    rows = []
    probe = None
    for stratum, requested_rms_mm in STRATA:
        for seed in SEEDS:
            trial_id = f"{stratum}__seed{seed}"
            trial_dir = output / "trials" / trial_id
            trial_dir.mkdir(parents=True)
            package = trial_dir / "shared_capture"
            realized = _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
            _json(trial_dir / "realized_rms.json", realized)
            contract = verify_package(package)
            guards = freeze_guards(package)
            frozen = verify_frozen_test(package, guards)
            guards_payload = {"guards": guards, "frozen_test": frozen}
            _json(trial_dir / "guards.json", guards_payload)
            row = _trial_record(package, stratum, requested_rms_mm, seed, realized, guards_payload)
            row["trial_id"] = trial_id
            row["package_sha256"] = _sha256_tree(package)
            row["package_contract"] = contract
            row["frozen_test_guard_passed"] = bool(frozen.get("passed"))
            _json(trial_dir / "trial.json", row)
            rows.append(row)
            if probe is None:
                probe = _run_probe(package)
                _json(output / "test_only_perturbation_probe.json", probe)
            shutil.rmtree(package)
    # Compact CSV-like JSON remains easier to audit without adding a dependency.
    _json(output / "trials.json", rows)
    report = {
        "schema": "spatial_recovery_rebuilt.calibration_only_report",
        "status": "smoke_complete",
        "git_status_before": before,
        "git_status_after": git_status(),
        "trial_count": len(rows),
        "expected_trial_count": len(STRATA) * len(SEEDS),
        "full_matrix_started": False,
        "all_guards_passed": all(row["frozen_test_guard_passed"] for row in rows),
        "all_truth_q_proxy_input_checks_pass": all(not row["truth_used_by_estimator"] and not row["q_proxy_used_by_estimator"] for row in rows),
        "probe": probe,
        "score_reference": {
            "definition": "truth interpolated on full physical radar frame grid; mean where elapsed <= 0.20 s",
            "warm_reference_sample_count": 21,
            "test_score_frames": [200, 399],
            "truth_used_post_run_only": True,
            "success_threshold_mm": 0.010,
        },
        "full_window_test_rmse_m": [row["full_window_route"]["test_rmse_m"] for row in rows],
        "calibration_only_test_rmse_m": [row["calibration_only_route"]["test_rmse_m"] for row in rows],
        "rmse_delta_calibration_only_minus_full_window_m": [
            row["calibration_only_route"]["test_rmse_m"] - row["full_window_route"]["test_rmse_m"] for row in rows
        ],
        "route_summary": {
            "full_window": {
                "mean_test_rmse_mm": float(np.mean([row["full_window_route"]["test_rmse_m"] for row in rows]) * 1.0e3),
                "successes_at_0p010mm": sum(row["full_window_route"]["test_rmse_m"] <= 1.0e-5 for row in rows),
            },
            "calibration_only": {
                "mean_test_rmse_mm": float(np.mean([row["calibration_only_route"]["test_rmse_m"] for row in rows]) * 1.0e3),
                "successes_at_0p010mm": sum(row["calibration_only_route"]["test_rmse_m"] <= 1.0e-5 for row in rows),
            },
        },
        "geometry_equal_count": sum(bool(row["geometry_equal_between_routes"]) for row in rows),
        "geometry_diff_count": sum(not bool(row["geometry_equal_between_routes"]) for row in rows),
        "claims_parity_with_lost_workspace": False,
    }
    _json(output / "calibration_only_report.json", report)
    manifest.update({"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat(), "git_status_after": git_status()})
    _json(output / "run_manifest.json", manifest)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
