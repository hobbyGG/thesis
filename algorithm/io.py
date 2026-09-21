from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .acceleration import preintegrate_acceleration_to_radar
from .types import AccelerationInput, CapturePackage, FrontendConfig, RadarInput


def _manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _array(directory: Path, manifest: dict[str, Any], name: str) -> np.ndarray:
    item = manifest["arrays"][name]
    return np.load(directory / item["file"], allow_pickle=False)


def load_capture_package(root: str | Path) -> CapturePackage:
    root = Path(root)
    radar_dir = root / "radar" / "algorithm_input"
    adxl_dir = root / "adxl355" / "algorithm_input"
    radar_manifest = _manifest(radar_dir / "manifest.json")
    adxl_manifest = _manifest(adxl_dir / "manifest.json")
    adc_cube = _array(radar_dir, radar_manifest, "adc_cube")
    frame_times_s = _array(radar_dir, radar_manifest, "frame_times_s")
    adxl_accel = _array(adxl_dir, adxl_manifest, "acceleration_mps2")
    adxl_time_ns = _array(adxl_dir, adxl_manifest, "estimated_sample_monotonic_ns")
    sync_dir = root / "sync"
    timeline = _manifest(sync_dir / "timeline.json")
    radar_time_ns = np.load(sync_dir / timeline["array"]["file"], allow_pickle=False)
    adc_timing = timeline.get("adc_array")
    if adc_timing is not None:
        radar_time_ns = np.load(sync_dir / adc_timing["file"], allow_pickle=False)
    radar_meta = radar_manifest["radar"]
    frontend = FrontendConfig(
        num_virtual_rx=int(radar_meta["virtual_antennas"]),
        num_adc_samples=int(radar_meta["adc_samples_per_chirp"]),
        num_range_bins=int(radar_meta["adc_samples_per_chirp"]),
        num_angle_bins=int(radar_meta.get("angle_bins", 64)),
        range_resolution_m=float(radar_meta["range_resolution_m"]),
        angle_estimation_method="local_music_ml",
    )
    truth_q = truth_t = None
    truth_dir = root / "truth"
    if (truth_dir / "displacement_m.npy").is_file():
        truth_q = np.load(truth_dir / "displacement_m.npy", allow_pickle=False)
        truth_t = np.load(truth_dir / "time_ns.npy", allow_pickle=False)
    return CapturePackage(root, adc_cube, frame_times_s, radar_time_ns, adxl_time_ns, adxl_accel, frontend, truth_q, truth_t)


def build_algorithm_inputs(capture: CapturePackage):
    from .frontend import extract_targets, range_angle_process
    from .selection import detect_target_bins, select_targets

    processed = range_angle_process(capture.adc_cube, capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(processed.cube, processed.angle_axis_deg, max_candidates=5)
    targets = extract_targets(processed, range_bins, angle_bins, capture.frontend)
    radar_rate = 1.0 / np.median(np.diff(capture.radar_time_ns) * 1.0e-9)
    structural_accel = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(capture.radar_time_ns, capture.adxl_time_ns, structural_accel)
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured = np.r_[interval_average[0], interval_average]
    acceleration = AccelerationInput(capture.adxl_time_ns, structural_accel, measured, preintegration)
    selected, initial_r, scores = select_targets(targets, measured, radar_rate)
    radar = RadarInput(targets.measured_beta, targets.wrapped_phase_rad, targets.available_mask, selected, initial_r, scores, {
        "angle_deg": targets.angle_deg,
        "range_bins": targets.range_bins,
        "angle_bins": targets.angle_bins,
        "range_m": targets.range_m,
        "detection": detection,
        "radar_time_ns": capture.radar_time_ns,
    })
    return radar, acceleration, targets, radar_rate
