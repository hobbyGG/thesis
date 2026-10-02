"""Audit a minimal observable-only RO input bundle; no baseline is run.

This supplements the earlier truth-free package-copy smoke by also removing
simulation source labels and angular metadata from the allowed input surface.
It uses an existing smoke capture, performs only per-channel range FFT shape
checks, and deliberately does not select bins, fit beta, or call the Kalman.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "spatial_recovery_rebuilt/smoke/capture_low_motion_0p005mm_seed20261001"
OUTPUT = Path(__file__).with_name("input_isolation_strict.json")
RADAR_KEYS = (
    "frames", "frame_rate_hz", "frame_period_s", "virtual_antennas",
    "adc_samples_per_chirp", "start_frequency_hz", "range_resolution_m",
    "chirp_slope_hz_per_s", "adc_sample_rate_hz", "chirp_cube_semantics",
)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_hash(value: np.ndarray) -> str:
    return sha(np.ascontiguousarray(value).tobytes(order="C"))


def git(args: list[str]) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def allowed_config(manifest: dict) -> dict:
    return {key: manifest["radar"][key] for key in RADAR_KEYS if key in manifest["radar"]}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"refusing to overwrite retained audit: {OUTPUT}")
    started = datetime.now(timezone.utc).isoformat()
    before = git(["status", "--short", "--branch"])
    radar_dir = SOURCE / "radar/algorithm_input"
    adxl_dir = SOURCE / "adxl355/algorithm_input"
    manifest = json.loads((radar_dir / "manifest.json").read_text())
    adxl_manifest = json.loads((adxl_dir / "manifest.json").read_text())
    timeline = json.loads((SOURCE / "sync/timeline.json").read_text())
    adc_path = radar_dir / manifest["arrays"]["adc_cube"]["file"]
    acceleration_path = adxl_dir / adxl_manifest["arrays"]["acceleration_mps2"]["file"]
    adxl_time_path = adxl_dir / adxl_manifest["arrays"]["estimated_sample_monotonic_ns"]["file"]
    radar_time_path = SOURCE / "sync" / timeline["adc_array"]["file"]
    config = allowed_config(manifest)
    # A tripwire for hidden metadata leakage: alter forbidden manifest fields
    # in memory.  The whitelisted observable config must remain identical.
    poison = json.loads(json.dumps(manifest))
    poison["source"] = {"target_angles_deg": [-89.0], "target_range_bins": [1], "q_proxy": "forbidden"}
    poison["radar"]["angle_bins"] = 123
    poison["radar"]["virtual_array_positions_wavelengths"] = [999.0]
    config_bytes = json.dumps(config, sort_keys=True).encode()
    ignored_metadata_unchanged = config == allowed_config(poison)
    with tempfile.TemporaryDirectory(prefix="ro-input-strict-") as temporary:
        bundle = Path(temporary)
        files = {
            "adc_cube.npy": adc_path,
            "acceleration_mps2.npy": acceleration_path,
            "adxl_time_ns.npy": adxl_time_path,
            "radar_time_ns.npy": radar_time_path,
        }
        for name, source in files.items():
            shutil.copy2(source, bundle / name)
        (bundle / "observable_config.json").write_text(json.dumps(config, indent=2) + "\n")
        adc = np.load(bundle / "adc_cube.npy", allow_pickle=False)
        accel = np.load(bundle / "acceleration_mps2.npy", allow_pickle=False)
        radar_time = np.load(bundle / "radar_time_ns.npy", allow_pickle=False)
        adxl_time = np.load(bundle / "adxl_time_ns.npy", allow_pickle=False)
        assert adc.shape == (400, 8, 256)
        assert accel.shape == (4000, 3)
        assert radar_time.shape == (400,)
        assert adxl_time.shape == (4000,)
        cal_fft = np.fft.fft(adc[:200], axis=-1)
        test_fft = np.fft.fft(adc[200:], axis=-1)
        cal_before = array_hash(adc[:200])
        test_before = array_hash(adc[200:])
        # Only exercise the array fence.  No beta or geometry estimator exists
        # here, so this must not be described as a frozen-beta proof.
        adc[200:] *= np.exp(0.7j)
        cal_after = array_hash(adc[:200])
        test_after = array_hash(adc[200:])
        visible = sorted(path.name for path in bundle.iterdir())
        report = {
            "schema": "spatial_recovery_rebuilt.ro_input_isolation_strict",
            "status": "passed",
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "source_package": str(SOURCE),
            "git_head": git(["rev-parse", "HEAD"]),
            "git_status_before": before,
            "git_status_after": git(["status", "--short", "--branch"]),
            "script_sha256": sha(Path(__file__).read_bytes()),
            "source_adc_file_sha256": sha(adc_path.read_bytes()),
            "visible_files": visible,
            "observable_config": config,
            "observable_config_sha256": sha(config_bytes),
            "boundary_checks": {
                "truth_and_q_proxy_absent": not any("truth" in name or "q_proxy" in name for name in visible),
                "simulation_source_labels_absent": "source" not in config,
                "angular_metadata_absent": not any("angle" in key or "positions" in key for key in config),
                "poisoned_forbidden_metadata_has_no_effect": ignored_metadata_unchanged,
                "all_8_raw_channels_retained": adc.shape[1] == 8,
                "calibration_adc_unchanged_under_test_only_perturbation": cal_before == cal_after,
                "test_adc_changed": test_before != test_after,
            },
            "array_contract": {
                "adc_shape": list(adc.shape), "adc_dtype": str(adc.dtype),
                "calibration_range_fft_shape": list(cal_fft.shape),
                "test_range_fft_shape": list(test_fft.shape),
                "all_range_fft_values_finite": bool(np.isfinite(cal_fft).all() and np.isfinite(test_fft).all()),
                "radar_time_count": int(radar_time.size), "adxl_shape": list(accel.shape),
            },
            "input_hashes": {
                "calibration_adc_before": cal_before, "calibration_adc_after": cal_after,
                "test_adc_before": test_before, "test_adc_after": test_after,
                "calibration_adxl": array_hash(accel[:2000]), "test_adxl": array_hash(accel[2000:]),
                "calibration_radar_time": array_hash(radar_time[:200]), "test_radar_time": array_hash(radar_time[200:]),
            },
            "operations_invoked": ["numpy range FFT independently for all channels", "input hash and whitelist checks"],
            "operations_not_invoked": ["range-bin selection", "beta fit", "angle/DBF/MUSIC/ML", "phase estimator", "Kalman", "RMSE scoring"],
            "baseline_implemented": False,
            "fairness_established": False,
            "frozen_beta_verified": False,
            "full_run_started": False,
            "interpretation": "Input isolation only; channel selection, beta identifiability and correlated-observation weighting remain design blockers.",
        }
        assert all(report["boundary_checks"].values())
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": report["status"], "output": str(OUTPUT), "boundary_checks": report["boundary_checks"]}, indent=2))


if __name__ == "__main__":
    main()
