"""Rebuild a minimal, explicitly scoped validation scratch workspace.

This module is deliberately outside the tracked experiment packages.  It uses
the current package builder's private export helpers so the generated data is
still a normal capture package, while keeping the requested stratum and
calibration/test bookkeeping local to this untracked directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper_bridge_simulation import package_builder as pb  # noqa: E402


RADAR_FRAMES = 400
RADAR_RATE_HZ = 100.0
DURATION_S = RADAR_FRAMES / RADAR_RATE_HZ
CALIBRATION_FRAMES = 200
REFERENCE_RATE_HZ = 3000.0
ADXL_RATE_HZ = 1000.0
MOTION_FREQUENCY_HZ = 1.0
PROXY_ANGLE_DEG = 15.0
GUARD_MULTIPLIER = 1.25
ZERO_EPSILON_M = 1.0e-15
SEED_VALUES = tuple(range(20261001, 20261041))
STRATA = (
    ("stationary", 0.0),
    ("low_motion_0p005mm", 0.005),
    ("low_motion_0p010mm", 0.010),
    ("low_motion_0p020mm", 0.020),
    ("low_motion_0p050mm", 0.050),
)


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_evidence() -> dict[str, object]:
    tracked = (
        "paper_bridge_simulation/package_builder.py",
        "paper_bridge_simulation/response.py",
        "algorithm/io.py",
        "algorithm/run.py",
        "algorithm/frontend.py",
        "algorithm/selection.py",
        "algorithm/kalman.py",
    )
    status = subprocess.run(
        ["git", "status", "--short", "--branch"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    return {
        "repository": str(ROOT),
        "git_head": head,
        "git_status_before": status,
        "git_status_before_scratch": Path(__file__).with_name("baseline_git_status.txt").read_text(encoding="utf-8"),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "source_sha256": {name: _sha256(ROOT / name) for name in tracked},
    }


def git_status() -> str:
    return subprocess.run(
        ["git", "status", "--short", "--branch"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout


def _motion_arrays(requested_rms_mm: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return 3 kHz truth/proxy/acceleration arrays with realized RMS logged later."""
    count = round(DURATION_S * REFERENCE_RATE_HZ)
    time_s = np.arange(count, dtype=float) / REFERENCE_RATE_HZ
    if requested_rms_mm == 0.0:
        q_true = np.zeros(count, dtype=float)
        acceleration = np.zeros(count, dtype=float)
    else:
        raw = np.sin(2.0 * np.pi * MOTION_FREQUENCY_HZ * time_s)
        target_rms_m = requested_rms_mm * 1.0e-3
        q_true = raw * (target_rms_m / float(np.sqrt(np.mean(raw * raw))))
        acceleration = -(2.0 * np.pi * MOTION_FREQUENCY_HZ) ** 2 * q_true
    q_proxy = q_true * np.cos(np.deg2rad(PROXY_ANGLE_DEG))
    return time_s, q_true, q_proxy, acceleration


def _write_scratch_package(
    output: Path, *, stratum_name: str, requested_rms_mm: float, seed: int
) -> dict[str, object]:
    """Build a current-contract package from scratch-only q_true arrays."""
    reference_time_s, q_true, q_proxy, acceleration = _motion_arrays(requested_rms_mm)
    count = RADAR_FRAMES
    frame_time_s = np.arange(count, dtype=float) / RADAR_RATE_HZ + pb.RADAR_APERTURE_CENTER_OFFSET_S
    loop_offsets_s = (
        np.arange(pb.RADAR_LOOPS_PER_FRAME, dtype=float)
        - (pb.RADAR_LOOPS_PER_FRAME - 1) / 2.0
    ) * pb.RADAR_LOOP_START_INTERVAL_S
    tx_offsets_s = (
        np.arange(pb.RADAR_TX_CHIRPS_PER_LOOP, dtype=float)
        - (pb.RADAR_TX_CHIRPS_PER_LOOP - 1) / 2.0
    ) * (pb.RADAR_IDLE_TIME_S + pb.RADAR_RAMP_END_TIME_S)
    tx_time_s = (
        frame_time_s[:, None, None]
        + loop_offsets_s[None, :, None]
        + tx_offsets_s[None, None, :]
    )
    tx_q = np.interp(tx_time_s, reference_time_s, q_true)
    adxl_time_s = np.arange(round(DURATION_S * ADXL_RATE_HZ), dtype=float) / ADXL_RATE_HZ
    frame_a = np.interp(adxl_time_s, reference_time_s, acceleration)

    with tempfile.TemporaryDirectory(prefix="spatial-recovery-package-") as temporary:
        staging = Path(temporary) / "package"
        staging.mkdir()
        pb._radar_package(staging, tx_q, seed)
        pb._adxl_package(staging, frame_a, seed)
        sync = staging / "sync"
        sync.mkdir()
        radar_time = pb.BASE_TIME_NS + np.arange(count, dtype=np.int64) * round(1.0e9 / RADAR_RATE_HZ)
        np.save(sync / "radar_frame_monotonic_ns.npy", radar_time, allow_pickle=False)
        radar_adc_time = radar_time + round(pb.RADAR_APERTURE_CENTER_OFFSET_S * 1.0e9)
        np.save(sync / "radar_adc_sample_monotonic_ns.npy", radar_adc_time, allow_pickle=False)
        _json(sync / "timeline.json", {
            "schema_version": 1, "status": "complete", "sync_mode": "software_timestamp",
            "timestamp_quality": "synthetic_scratch_schedule", "hardware_validated": False,
            "clock": "CLOCK_MONOTONIC", "unit": "nanoseconds", "frame_count": count,
            "nominal_frame_period_ns": round(1.0e9 / RADAR_RATE_HZ),
            "radar_algorithm_manifest": "../radar/algorithm_input/manifest.json",
            "radar_packet_integrity_complete": True,
            "array": {"file": "radar_frame_monotonic_ns.npy", "dtype": "int64", "shape": [count], "axes": ["radar_frame"]},
            "adc_array": {"file": "radar_adc_sample_monotonic_ns.npy", "dtype": "int64", "shape": [count]},
            "provenance": {"source": "spatial_recovery_rebuilt", "semantics": "synthetic nominal schedule"},
        })
        _json(sync / "manifest.json", {
            "schema_version": 1, "status": "complete", "sync_mode": "software_timestamp",
            "timestamp_quality": "synthetic_scratch_schedule", "hardware_validated": False,
            "clock": {"alignment_clock": "CLOCK_MONOTONIC", "unit": "nanoseconds"},
            "files": {"radar": {"algorithm_input_manifest": "radar/algorithm_input/manifest.json"},
                      "adxl355": {"algorithm_input_manifest": "adxl355/algorithm_input/manifest.json"},
                      "sync": {"timeline_manifest": "sync/timeline.json", "radar_frame_monotonic_ns": "sync/radar_frame_monotonic_ns.npy"}},
            "validation": {"status": "complete", "radar_finalized": True, "adxl355_finalized": True, "sync_timeline_exported": True},
            "timestamp_semantics": {"radar": "synthetic nominal schedule", "adxl355": "synthetic nominal sample schedule"},
        })
        truth = staging / "truth"
        truth.mkdir()
        np.save(truth / "displacement_m.npy", q_true, allow_pickle=False)
        np.save(truth / "q_true_m.npy", q_true, allow_pickle=False)
        np.save(truth / "q_proxy_m.npy", q_proxy, allow_pickle=False)
        np.save(truth / "time_ns.npy", pb.BASE_TIME_NS + np.rint(reference_time_s * 1.0e9).astype(np.int64), allow_pickle=False)
        np.save(truth / "acceleration_mps2.npy", frame_a, allow_pickle=False)
        np.save(truth / "adxl_time_ns.npy", pb.BASE_TIME_NS + np.arange(frame_a.size, dtype=np.int64) * round(1.0e9 / ADXL_RATE_HZ), allow_pickle=False)
        _json(staging / "paper_response_metadata.json", {
            "source_type": "spatial_recovery_rebuilt_scratch",
            "stratum": stratum_name,
            "requested_q_true_rms_mm": requested_rms_mm,
            "motion_frequency_hz": MOTION_FREQUENCY_HZ,
            "q_proxy_definition": "q_true*cos(15 degrees)",
            "truth_is_post_run_only": True,
            "claims_parity_with_lost_workspace": False,
        })
        _json(staging / "status.json", {
            "schema_version": 1, "status": "complete", "source_type": "spatial_recovery_rebuilt_scratch",
            "stratum": stratum_name, "seed": seed,
        })
        if output.exists():
            shutil.rmtree(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.replace(output)

    realized = {
        "stratum": stratum_name,
        "seed": seed,
        "requested_q_true_rms_mm": requested_rms_mm,
        "q_true_rms_m": float(np.sqrt(np.mean(q_true * q_true))),
        "q_proxy_rms_m": float(np.sqrt(np.mean(q_proxy * q_proxy))),
        "q_true_rms_mm": float(np.sqrt(np.mean(q_true * q_true)) * 1.0e3),
        "q_proxy_rms_mm": float(np.sqrt(np.mean(q_proxy * q_proxy)) * 1.0e3),
        "q_true_rms_calibration_m": float(np.sqrt(np.mean(q_true[:6000] * q_true[:6000]))),
        "q_true_rms_test_m": float(np.sqrt(np.mean(q_true[6000:] * q_true[6000:]))),
        "q_proxy_rms_calibration_m": float(np.sqrt(np.mean(q_proxy[:6000] * q_proxy[:6000]))),
        "q_proxy_rms_test_m": float(np.sqrt(np.mean(q_proxy[6000:] * q_proxy[6000:]))),
        "q_true_max_abs_m": float(np.max(np.abs(q_true))),
        "q_proxy_max_abs_m": float(np.max(np.abs(q_proxy))),
        "reference_samples": int(q_true.size),
        "radar_frames": RADAR_FRAMES,
        "calibration_frames": CALIBRATION_FRAMES,
        "test_frames": RADAR_FRAMES - CALIBRATION_FRAMES,
    }
    return realized


def verify_package(package: Path) -> dict[str, object]:
    radar_dir = package / "radar" / "algorithm_input"
    adxl_dir = package / "adxl355" / "algorithm_input"
    radar_manifest = json.loads((radar_dir / "manifest.json").read_text(encoding="utf-8"))
    adxl_manifest = json.loads((adxl_dir / "manifest.json").read_text(encoding="utf-8"))
    chirp = np.load(radar_dir / radar_manifest["arrays"]["chirp_cube"]["file"], allow_pickle=False)
    adc = np.load(radar_dir / radar_manifest["arrays"]["adc_cube"]["file"], allow_pickle=False)
    frame_times = np.load(radar_dir / radar_manifest["arrays"]["frame_times_s"]["file"], allow_pickle=False)
    adxl = np.load(adxl_dir / adxl_manifest["arrays"]["acceleration_mps2"]["file"], allow_pickle=False)
    adxl_times = np.load(adxl_dir / adxl_manifest["arrays"]["estimated_sample_monotonic_ns"]["file"], allow_pickle=False)
    truth = np.load(package / "truth" / "q_true_m.npy", allow_pickle=False)
    proxy = np.load(package / "truth" / "q_proxy_m.npy", allow_pickle=False)
    sync = json.loads((package / "sync" / "timeline.json").read_text(encoding="utf-8"))
    radar_time = np.load(package / "sync" / sync["array"]["file"], allow_pickle=False)
    checks = {
        "radar_schema": radar_manifest.get("schema") == "mmwavecapture.algorithm-input",
        "radar_complete": bool(radar_manifest.get("packet_integrity", {}).get("complete")),
        "radar_frames_400": chirp.shape == (RADAR_FRAMES, 16, 8, 256),
        "adc_shape": adc.shape == (RADAR_FRAMES, 8, 256),
        "adc_is_loop_mean": bool(np.allclose(adc, np.mean(chirp, axis=1), rtol=0.0, atol=2.0e-6)),
        "radar_rate_100_hz": float(radar_manifest["radar"]["frame_rate_hz"]) == RADAR_RATE_HZ,
        "frame_time_count": frame_times.size == RADAR_FRAMES,
        "adxl_4000": adxl.shape == (4000, 3),
        "adxl_time_monotonic": bool(np.all(np.diff(adxl_times) > 0)),
        "sync_time_monotonic": bool(np.all(np.diff(radar_time) > 0)) and radar_time.size == RADAR_FRAMES,
        "truth_reference_count": truth.size == round(DURATION_S * REFERENCE_RATE_HZ),
        "proxy_shape": proxy.shape == truth.shape,
    }
    if not all(checks.values()):
        raise RuntimeError(f"package contract failed: {checks}")
    return checks


def freeze_guards(package: Path) -> dict[str, object]:
    """Compute and write guards before reading any frozen-test values."""
    # Guards deliberately use only observable capture arrays.  Truth arrays
    # are loaded later for post-run RMS logging and never set the guard limits.
    radar_dir = package / "radar" / "algorithm_input"
    adxl_dir = package / "adxl355" / "algorithm_input"
    radar_manifest = json.loads((radar_dir / "manifest.json").read_text(encoding="utf-8"))
    adxl_manifest = json.loads((adxl_dir / "manifest.json").read_text(encoding="utf-8"))
    adc = np.load(radar_dir / radar_manifest["arrays"]["adc_cube"]["file"], allow_pickle=False)
    acceleration = np.load(adxl_dir / adxl_manifest["arrays"]["acceleration_mps2"]["file"], allow_pickle=False)
    calibration_adc = adc[:CALIBRATION_FRAMES]
    calibration_acceleration = acceleration[:CALIBRATION_FRAMES * int(ADXL_RATE_HZ / RADAR_RATE_HZ)]
    finite = bool(np.all(np.isfinite(calibration_adc)) and np.all(np.isfinite(calibration_acceleration)))
    adc_max = float(np.max(np.abs(calibration_adc)))
    acceleration_max = float(np.max(np.abs(calibration_acceleration)))
    guards = {
        "source": "calibration_capture_arrays_only",
        "frozen_before_test": True,
        "calibration_frame_range": [0, CALIBRATION_FRAMES - 1],
        "calibration_adxl_sample_count": int(calibration_acceleration.shape[0]),
        "finite_calibration": finite,
        "adc_abs_limit": max(ZERO_EPSILON_M, GUARD_MULTIPLIER * adc_max),
        "acceleration_abs_limit_mps2": max(ZERO_EPSILON_M, GUARD_MULTIPLIER * acceleration_max),
        "time_monotonic_required": True,
    }
    _json(package / "guards.json", guards)
    return guards


def verify_frozen_test(package: Path, guards: dict[str, object]) -> dict[str, object]:
    radar_dir = package / "radar" / "algorithm_input"
    adxl_dir = package / "adxl355" / "algorithm_input"
    radar_manifest = json.loads((radar_dir / "manifest.json").read_text(encoding="utf-8"))
    adxl_manifest = json.loads((adxl_dir / "manifest.json").read_text(encoding="utf-8"))
    adc = np.load(radar_dir / radar_manifest["arrays"]["adc_cube"]["file"], allow_pickle=False)
    acceleration = np.load(adxl_dir / adxl_manifest["arrays"]["acceleration_mps2"]["file"], allow_pickle=False)
    test_adc = adc[CALIBRATION_FRAMES:]
    test_acceleration = acceleration[CALIBRATION_FRAMES * int(ADXL_RATE_HZ / RADAR_RATE_HZ):]
    timeline = json.loads((package / "sync" / "timeline.json").read_text(encoding="utf-8"))
    radar_time = np.load(package / "sync" / timeline["array"]["file"], allow_pickle=False)
    test_radar_time = radar_time[CALIBRATION_FRAMES:]
    result = {
        "test_frame_range": [CALIBRATION_FRAMES, RADAR_FRAMES - 1],
        "test_adxl_sample_count": int(test_acceleration.shape[0]),
        "finite_test_capture_arrays": bool(np.all(np.isfinite(test_adc)) and np.all(np.isfinite(test_acceleration))),
        "test_radar_time_monotonic": bool(np.all(np.diff(test_radar_time) > 0)),
        "adc_within_frozen_limit": bool(np.max(np.abs(test_adc)) <= float(guards["adc_abs_limit"]) + ZERO_EPSILON_M),
        "acceleration_within_frozen_limit": bool(np.max(np.abs(test_acceleration)) <= float(guards["acceleration_abs_limit_mps2"]) + ZERO_EPSILON_M),
    }
    result["passed"] = all(bool(value) for key, value in result.items() if key not in {"test_frame_range", "test_adxl_sample_count"})
    if not result["passed"]:
        raise RuntimeError(f"frozen test guard failed: {result}")
    _json(package / "frozen_test_guard_result.json", result)
    return result


def run_algorithm(package: Path, result_path: Path) -> dict[str, object]:
    command = [sys.executable, "-m", "algorithm.run", "--input", str(package), "--output", str(result_path)]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    summary_path = result_path.with_suffix(".json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return {"command": command, "stdout": completed.stdout, "summary": summary}


def smoke(output: Path) -> dict[str, object]:
    source = source_evidence()
    package = output / "capture_low_motion_0p005mm_seed20261001"
    realized = _write_scratch_package(package, stratum_name="low_motion_0p005mm", requested_rms_mm=0.005, seed=SEED_VALUES[0])
    contract = verify_package(package)
    guards = freeze_guards(package)
    frozen_test = verify_frozen_test(package, guards)
    _json(package / "rms_log.json", realized)
    algorithm = run_algorithm(package, output / "algorithm_result.npz")
    report = {
        "status": "smoke_passed",
        "claims_parity_with_lost_workspace": False,
        "source_evidence": source,
        "protocol": {
            "radar_frames": RADAR_FRAMES,
            "radar_rate_hz": RADAR_RATE_HZ,
            "calibration_frames": CALIBRATION_FRAMES,
            "test_frames": RADAR_FRAMES - CALIBRATION_FRAMES,
            "stratum": "low_motion_0p005mm",
            "seed": SEED_VALUES[0],
        },
        "realized_rms": realized,
        "contract_checks": contract,
        "frozen_test": frozen_test,
        "algorithm": algorithm,
        "full_40_seed_run_safe_to_start": True,
        "full_run_scope": "not run; retain compact logs and process one package at a time",
    }
    report["source_evidence"]["git_status_after"] = git_status()
    _json(output / "smoke_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the spatial validation scratch protocol")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true", help="run one 400-frame, one-stratum smoke test")
    args = parser.parse_args()
    if not args.smoke:
        parser.error("only --smoke is enabled; the 40-seed matrix is intentionally not started")
    args.output.mkdir(parents=True, exist_ok=True)
    _json(args.output / "protocol.json", json.loads((Path(__file__).with_name("protocol.json")).read_text(encoding="utf-8")))
    report = smoke(args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output), "full_40_seed_run_safe_to_start": report["full_40_seed_run_safe_to_start"]}, indent=2))


if __name__ == "__main__":
    main()
