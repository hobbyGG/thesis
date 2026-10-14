from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from .acceleration import preintegrate_acceleration_to_radar, remove_static_bias
from .config import AlgorithmConfig
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


def effective_carrier_frequency_hz(capture: CapturePackage) -> float:
    """Carrier frequency at the centre of the sampled fast-time aperture."""
    radar_meta = capture.radar_metadata
    carrier_frequency_hz = float(radar_meta.get("start_frequency_hz", 77.0e9))
    adc_rate_hz = float(radar_meta.get("adc_sample_rate_hz", 0.0))
    chirp_slope_hz_per_s = float(radar_meta.get("chirp_slope_hz_per_s", 0.0))
    adc_start_time_s = float(radar_meta.get("adc_start_time_s", 0.0))
    if adc_rate_hz > 0.0 and chirp_slope_hz_per_s != 0.0:
        center_sample = (capture.frontend.num_adc_samples - 1) / 2.0
        aperture_center_s = adc_start_time_s + center_sample / adc_rate_hz
        carrier_frequency_hz += chirp_slope_hz_per_s * aperture_center_s
    return carrier_frequency_hz


def extract_targets(capture: CapturePackage):
    """Range-FFT, DBF and first-frame target detection over the whole record."""
    from .frontend import extract_dbf_targets_streaming, range_angle_process
    from .selection import detect_target_bins

    stream_cube = np.asarray(capture.adc_cube)
    if stream_cube.shape[0] != np.asarray(capture.radar_time_ns).size:
        raise ValueError("radar stream length and timestamp length do not match")
    first = range_angle_process(stream_cube[:1], capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(
        first.cube, first.angle_axis_deg, max_candidates=5
    )
    targets = extract_dbf_targets_streaming(
        stream_cube, range_bins, angle_bins, capture.frontend
    )
    return targets, detection


def build_radar_input(targets, detection, radar_time_ns) -> tuple[RadarInput, Any]:
    """Recursive circle fit, target selection and the radar measurement input."""
    from .phase import recursive_circle_phase
    from .selection import select_targets

    radar_time_ns = np.asarray(radar_time_ns, dtype=np.int64)
    wrapped, centers, radii, circle_residual, normalized_iq = recursive_circle_phase(
        targets.slow_time
    )
    targets = replace(targets, wrapped_phase_rad=wrapped)
    sample_period_s = (
        float(np.median(np.diff(radar_time_ns)) * 1.0e-9) if radar_time_ns.size > 1 else 1.0
    )
    selected, initial_r = select_targets(targets)
    radar = RadarInput(
        targets.measured_beta,
        targets.wrapped_phase_rad,
        targets.available_mask,
        selected,
        initial_r,
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
    return radar, targets


def build_acceleration_input(radar_time_ns, adxl_time_ns, adxl_accel_mps2) -> tuple[AccelerationInput, float]:
    """Static-offset removal and preintegration over the radar intervals."""
    structural_accel, static_bias = remove_static_bias(
        radar_time_ns,
        adxl_time_ns,
        adxl_accel_mps2,
        AlgorithmConfig().cold_start_duration_s,
    )
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns, adxl_time_ns, structural_accel
    )
    return AccelerationInput(adxl_time_ns, structural_accel, preintegration), static_bias


def build_algorithm_inputs(capture: CapturePackage):
    radar_time_ns = np.asarray(capture.radar_time_ns, dtype=np.int64)
    targets, detection = extract_targets(capture)
    radar, targets = build_radar_input(targets, detection, radar_time_ns)
    acceleration, static_bias = build_acceleration_input(
        radar_time_ns, capture.adxl_time_ns, capture.adxl_acceleration_mps2[:, 0]
    )
    radar.extra["adxl_static_bias_mps2"] = static_bias
    radar_rate = (
        1.0 / np.median(np.diff(radar_time_ns) * 1.0e-9) if radar_time_ns.size > 1 else 1.0
    )
    return radar, acceleration, targets, radar_rate
