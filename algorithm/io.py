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
    chirp_item = radar_manifest.get("arrays", {}).get("chirp_cube")
    chirp_cube = (
        np.load(radar_dir / chirp_item["file"], allow_pickle=False, mmap_mode="r")
        if isinstance(chirp_item, dict)
        else None
    )
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
    if adc_timing is None and "coherent_aperture_center_offset_s" in radar_meta:
        # Use the configured aperture center; this is not measured synchronization.
        radar_time_ns = radar_time_ns + round(radar_meta["coherent_aperture_center_offset_s"] * 1.0e9)
    frontend = FrontendConfig(
        num_virtual_rx=int(radar_meta["virtual_antennas"]),
        num_adc_samples=int(radar_meta["adc_samples_per_chirp"]),
        num_range_bins=int(radar_meta["adc_samples_per_chirp"]),
        num_angle_bins=int(radar_meta.get("angle_bins", 64)),
        range_resolution_m=float(radar_meta["range_resolution_m"]),
        virtual_array_positions_wavelengths=tuple(
            float(value) for value in radar_meta.get("virtual_array_positions_wavelengths", ())
        ),
        angle_estimation_method="local_music_ml",
    )
    truth_q = truth_t = None
    truth_dir = root / "truth"
    if (truth_dir / "displacement_m.npy").is_file():
        truth_q = np.load(truth_dir / "displacement_m.npy", allow_pickle=False)
        truth_t = np.load(truth_dir / "time_ns.npy", allow_pickle=False)
    return CapturePackage(
        root=root,
        adc_cube=adc_cube,
        frame_times_s=frame_times_s,
        radar_time_ns=radar_time_ns,
        adxl_time_ns=adxl_time_ns,
        adxl_acceleration_mps2=adxl_accel,
        frontend=frontend,
        truth_displacement_m=truth_q,
        truth_time_ns=truth_t,
        chirp_cube=chirp_cube,
        radar_metadata=dict(radar_meta),
    )


def _radar_timestamps(capture: CapturePackage, radar_mode: str) -> np.ndarray:
    if radar_mode == "frame":
        return capture.radar_time_ns
    if radar_mode != "chirp":
        raise ValueError("radar_mode must be `frame` or `chirp`")
    if capture.chirp_cube is None:
        raise ValueError("chirp radar mode requires radar/algorithm_input/chirp_cube.npy")

    loops = capture.chirp_cube.shape[1]
    loop_interval = capture.radar_metadata.get("loop_start_interval_s")
    if loop_interval is None:
        raise ValueError("chirp radar mode requires radar.loop_start_interval_s metadata")
    loop_interval_s = float(loop_interval)
    # Frame IQ represents the center of the coherent aperture.  Loop samples
    # cluster around that center; they do not uniformly fill the frame period.
    loop_offsets_ns = np.rint((np.arange(loops) - (loops - 1) / 2.0) * loop_interval_s * 1.0e9).astype(np.int64)
    return (capture.radar_time_ns[:, None] + loop_offsets_ns[None, :]).reshape(-1)


def build_algorithm_inputs(capture: CapturePackage, *, radar_mode: str = "frame"):
    from .frontend import extract_loop_targets, extract_targets, range_angle_process
    from .selection import detect_target_bins, select_targets

    radar_time_ns = _radar_timestamps(capture, radar_mode)
    # Freeze the same target locations and geometry for both observation modes.
    processed = range_angle_process(capture.adc_cube, capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(processed.cube, processed.angle_axis_deg, max_candidates=5)
    targets = extract_targets(processed, range_bins, angle_bins, capture.frontend)
    if radar_mode == "chirp":
        targets = extract_loop_targets(capture.chirp_cube, targets, capture.frontend)
    radar_rate = 1.0 / np.median(np.diff(radar_time_ns) * 1.0e-9)
    structural_accel = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(radar_time_ns, capture.adxl_time_ns, structural_accel)
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured = np.r_[interval_average[0], interval_average]
    acceleration = AccelerationInput(capture.adxl_time_ns, structural_accel, measured, preintegration)
    selected, initial_r, scores = select_targets(targets)
    radar = RadarInput(targets.measured_beta, targets.wrapped_phase_rad, targets.available_mask, selected, initial_r, scores, {
        "angle_deg": targets.angle_deg,
        "range_bins": targets.range_bins,
        "angle_bins": targets.angle_bins,
        "range_m": targets.range_m,
        "detection": detection,
        "radar_time_ns": radar_time_ns,
        "radar_mode": radar_mode,
        "frame_period_s": float(np.median(np.diff(capture.radar_time_ns)) * 1.0e-9),
    })
    return radar, acceleration, targets, radar_rate
