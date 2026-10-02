"""Scratch-only calibration-fenced RA route.

The retained algorithm API builds geometry from the complete ADC cube.  This
module deliberately bypasses that helper: detection, local MUSIC/ML, target
selection, and angle-derived beta are run on frames 0:200 only.  Test frames
are projected onto that frozen geometry and are the only observations passed
to the retained fixed-beta Kalman filter.
"""

from __future__ import annotations

import hashlib
import json
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.acceleration import preintegrate_acceleration_to_radar  # noqa: E402
from algorithm.frontend import range_angle_process  # noqa: E402
from algorithm.kalman import run_fixed_beta_kalman  # noqa: E402
from algorithm.selection import detect_target_bins, select_targets  # noqa: E402
from algorithm.types import AccelerationInput, RadarInput  # noqa: E402


CALIBRATION_FRAMES = 200
RADAR_FRAMES = 400


def _geometry_hash(geometry: dict[str, object]) -> str:
    encoded = json.dumps(geometry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _project_fixed_geometry(processed, range_bins: np.ndarray, angle_deg: np.ndarray) -> np.ndarray:
    """Project snapshots at fixed calibration range/angle geometry."""
    ranges = np.asarray(range_bins, dtype=int)
    angles = np.asarray(angle_deg, dtype=float)
    slow = np.empty((ranges.size, processed.snapshots.shape[0]), dtype=complex)
    for range_bin in np.unique(ranges):
        indices = np.flatnonzero(ranges == range_bin)
        steering = np.exp(
            2j * np.pi * processed.positions_wavelengths[:, None]
            * np.sin(np.deg2rad(angles[indices]))[None, :]
        )
        snapshots = processed.snapshots[:, int(range_bin), :].T
        slow[indices] = np.linalg.pinv(steering, rcond=1.0e-8) @ snapshots
    return slow


def calibration_geometry(capture) -> dict[str, object]:
    """Estimate and freeze geometry using calibration ADC frames only."""
    if capture.adc_cube.shape[0] != RADAR_FRAMES:
        raise ValueError(f"expected {RADAR_FRAMES} radar frames, got {capture.adc_cube.shape[0]}")
    processed = range_angle_process(capture.adc_cube[:CALIBRATION_FRAMES], capture.frontend)
    range_bins, angle_bins, detection = detect_target_bins(
        processed.cube, processed.angle_axis_deg, max_candidates=5
    )
    from algorithm.frontend import extract_targets  # local import keeps route explicit

    targets = extract_targets(processed, range_bins, angle_bins, capture.frontend)
    selected, initial_r, scores = select_targets(targets)
    geometry = {
        "range_bins": targets.range_bins.astype(int).tolist(),
        "angle_bins": targets.angle_bins.astype(int).tolist(),
        "range_m": targets.range_m.astype(float).tolist(),
        "angle_deg": targets.angle_deg.astype(float).tolist(),
        "measured_beta": targets.measured_beta.astype(float).tolist(),
        "selected_indices": selected.astype(int).tolist(),
        "selection_scores": scores.astype(float).tolist(),
        "initial_r": initial_r.astype(float).tolist(),
        "detection": detection,
        "calibration_frame_range": [0, CALIBRATION_FRAMES - 1],
        "geometry_hash": "",
    }
    geometry["geometry_hash"] = _geometry_hash(geometry)
    return {
        "geometry": geometry,
        "range_bins": targets.range_bins,
        "angle_bins": targets.angle_bins,
        "range_m": targets.range_m,
        "angle_deg": targets.angle_deg,
        "measured_beta": targets.measured_beta,
        "selected_indices": selected,
        "selection_scores": scores,
        "initial_r": initial_r,
    }


def build_calibration_only_inputs(capture):
    """Build a test-only RadarInput/AccelerationInput from frozen geometry."""
    frozen = calibration_geometry(capture)
    adc_test = np.asarray(capture.adc_cube[CALIBRATION_FRAMES:RADAR_FRAMES], dtype=complex)
    range_fft = np.fft.fft(adc_test, n=capture.frontend.num_range_bins, axis=2)
    snapshots = np.transpose(range_fft, (0, 2, 1))

    positions = (
        np.asarray(capture.frontend.virtual_array_positions_wavelengths, dtype=float)
        if capture.frontend.virtual_array_positions_wavelengths
        else np.arange(capture.frontend.num_virtual_rx, dtype=float) * capture.frontend.antenna_spacing_wavelengths
    )
    slow = _project_fixed_geometry(
        SimpleNamespace(snapshots=snapshots, positions_wavelengths=positions),
        frozen["range_bins"], frozen["angle_deg"],
    )
    available = np.isfinite(slow.real) & np.isfinite(slow.imag) & (np.abs(slow) > 0.0)
    wrapped = np.angle(slow)
    wrapped[~available] = np.nan
    radar_time_ns = np.asarray(capture.radar_time_ns[CALIBRATION_FRAMES:RADAR_FRAMES], dtype=np.int64)
    if radar_time_ns.size != RADAR_FRAMES - CALIBRATION_FRAMES:
        raise ValueError("unexpected test radar time count")
    adxl_start = CALIBRATION_FRAMES * 10
    structural_accel = np.asarray(capture.adxl_acceleration_mps2[adxl_start:, 0], dtype=float)
    adxl_time_ns = np.asarray(capture.adxl_time_ns[adxl_start:], dtype=np.int64)
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns, adxl_time_ns, structural_accel
    )
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured = np.r_[interval_average[0], interval_average]
    acceleration = AccelerationInput(
        adxl_time_ns, structural_accel, measured, preintegration
    )
    radar = RadarInput(
        np.asarray(frozen["measured_beta"], dtype=float),
        wrapped,
        available,
        np.asarray(frozen["selected_indices"], dtype=int),
        np.asarray(frozen["initial_r"], dtype=float),
        np.asarray(frozen["selection_scores"], dtype=float),
        {
            "angle_deg": np.asarray(frozen["angle_deg"], dtype=float),
            "range_bins": np.asarray(frozen["range_bins"], dtype=int),
            "angle_bins": np.asarray(frozen["angle_bins"], dtype=int),
            "range_m": np.asarray(frozen["range_m"], dtype=float),
            "detection": frozen["geometry"]["detection"],
            "radar_time_ns": radar_time_ns,
            "radar_mode": "frame_calibration_only",
            "frame_period_s": float(np.median(np.diff(capture.radar_time_ns)) * 1.0e-9),
            "geometry_source": "adc_frames_0_199_only",
        },
    )
    return radar, acceleration, frozen


def run_calibration_only(capture, config):
    """Run the retained Kalman on test-only observations and frozen geometry."""
    radar, acceleration, frozen = build_calibration_only_inputs(capture)
    result = run_fixed_beta_kalman(radar, acceleration, config)
    return result, radar, frozen
