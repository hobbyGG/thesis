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
    )
    truth_q = truth_t = None
    truth_dir = root / "truth"
    if (truth_dir / "displacement_m.npy").is_file():
        truth_q = np.load(truth_dir / "displacement_m.npy", allow_pickle=False)
        truth_t = np.load(truth_dir / "time_ns.npy", allow_pickle=False)
    return CapturePackage(
        root=root,
        adc_cube=adc_cube,
        radar_time_ns=radar_time_ns,
        adxl_time_ns=adxl_time_ns,
        adxl_acceleration_mps2=adxl_accel,
        frontend=frontend,
        truth_displacement_m=truth_q,
        truth_time_ns=truth_t,
        radar_metadata=dict(radar_meta),
    )


def build_algorithm_inputs(capture: CapturePackage):
    from .frontend import extract_dbf_targets_streaming, range_angle_process
    from .phase import causal_iq_circle_phase
    from .selection import detect_target_bins, select_targets

    radar_time_ns = np.asarray(capture.radar_time_ns, dtype=np.int64)
    stream_cube = np.asarray(capture.adc_cube)
    if stream_cube.shape[0] != radar_time_ns.size:
        raise ValueError("radar stream length and timestamp length do not match")

    first = range_angle_process(stream_cube[:1], capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(
        first.cube, first.angle_axis_deg, max_candidates=5
    )
    targets = extract_dbf_targets_streaming(
        stream_cube, range_bins, angle_bins, capture.frontend
    )
    wrapped, centers, radii, circle_residual, normalized_iq = causal_iq_circle_phase(
        targets.slow_time
    )
    targets = type(targets)(
        slow_time=targets.slow_time,
        wrapped_phase_rad=wrapped,
        available_mask=targets.available_mask,
        angle_deg=targets.angle_deg,
        measured_beta=targets.measured_beta,
        range_bins=targets.range_bins,
        angle_bins=targets.angle_bins,
        range_m=targets.range_m,
    )
    if radar_time_ns.size > 1:
        radar_rate = 1.0 / np.median(np.diff(radar_time_ns) * 1.0e-9)
        sample_period_s = float(np.median(np.diff(radar_time_ns)) * 1.0e-9)
    else:
        radar_rate = 1.0
        sample_period_s = 1.0
    structural_accel = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns, capture.adxl_time_ns, structural_accel
    )
    acceleration = AccelerationInput(
        capture.adxl_time_ns, structural_accel, preintegration
    )
    selected, initial_r, scores = select_targets(targets)
    radar = RadarInput(
        targets.measured_beta,
        targets.wrapped_phase_rad,
        targets.available_mask,
        selected,
        initial_r,
        scores,
        {
            "angle_deg": targets.angle_deg,
            "range_bins": targets.range_bins,
            "angle_bins": targets.angle_bins,
            "range_m": targets.range_m,
            "detection": detection,
            "radar_time_ns": radar_time_ns,
            "sample_period_s": sample_period_s,
            "circle_center": centers,
            "circle_radius": radii,
            "circle_residual": circle_residual,
            "normalized_iq": normalized_iq,
        },
    )
    return radar, acceleration, targets, radar_rate
