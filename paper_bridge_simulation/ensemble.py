"""Randomised scenario ensemble for the Monte-Carlo experiment.

``draw_case(seed)`` returns one ``(Scenario, Impairments)`` pair.  Every bound
below is an explicit simulation assumption (documented in the package README);
none is calibrated against a measured static capture yet.  A seed fixes the
whole case for a fixed generator version. Reports retain the trial impairments
so later changes in random draws cannot relabel old measurements.
"""

from __future__ import annotations

import numpy as np

from .package_builder import RANGE_RESOLUTION_M, TARGET_AMPLITUDES
from .response import EXCITATION_WEIGHTS, GUIDEWAY_SPAN_M
from .scenario import Impairments, Scenario

TARGET_COUNT = 5
# Longest target range kept clear of the 11.16 m unambiguous beat-range limit
# (the multipath replica sits 0.08 m behind its target).
MAX_TARGET_RANGE_M = 10.9
# Two targets are separate peaks of the range-angle map when they differ by at
# least this many range bins or this many degrees (about the 8-element beamwidth).
MIN_RANGE_SEPARATION_BINS = 2.5
MIN_ANGLE_SEPARATION_DEG = 14.0


def _log_uniform(rng: np.random.Generator, low: float, high: float) -> float:
    return float(np.exp(rng.uniform(np.log(low), np.log(high))))


def _draw_geometry(rng: np.random.Generator) -> tuple[np.ndarray, float]:
    while True:
        magnitude = np.sort(rng.uniform(2.0, 28.0, TARGET_COUNT))
        angles = magnitude * rng.choice((-1.0, 1.0), TARGET_COUNT)
        height = float(rng.uniform(8.0, 10.0))
        ranges = height / np.cos(np.deg2rad(angles))
        if ranges.max() > MAX_TARGET_RANGE_M:
            continue
        range_gap = np.abs(ranges[:, None] - ranges[None, :]) / RANGE_RESOLUTION_M
        angle_gap = np.abs(angles[:, None] - angles[None, :])
        unresolved = (range_gap < MIN_RANGE_SEPARATION_BINS) & (angle_gap < MIN_ANGLE_SEPARATION_DEG)
        if not np.any(np.triu(unresolved, k=1)):
            return angles, height


def draw_case(seed: int) -> tuple[Scenario, Impairments]:
    rng = np.random.default_rng([seed, 99])

    # Structure: one train passage in a 4 s record.
    speed_kmh = float(rng.uniform(250.0, 350.0))
    train_length_m = float(rng.uniform(40.0, 125.0))
    passage_duration_s = (train_length_m + GUIDEWAY_SPAN_M) / (speed_kmh / 3.6)
    structure = {
        "speed_kmh": speed_kmh,
        "peak_deflection_m": float(rng.uniform(0.6e-3, 2.2e-3)),
        "passage_duration_s": float(passage_duration_s),
        "event_starts_s": (float(rng.uniform(0.5, 1.3)),),
        "dynamic_acceleration_peak_mps2": float(rng.uniform(0.2, 0.8)),
        "excitation_weights": tuple(float(w) for w in EXCITATION_WEIGHTS * rng.uniform(0.5, 1.5, EXCITATION_WEIGHTS.size)),
        "excitation_phases_rad": tuple(float(p) for p in rng.uniform(0.0, 2.0 * np.pi, EXCITATION_WEIGHTS.size)),
        "ambient_acceleration_rms_mps2": _log_uniform(rng, 0.5e-3, 5.0e-3),
        "ambient_seed": int(rng.integers(2**31)),
    }

    # Radar scene: amplitudes fall with the off-nadir angle as in the reference scene.
    angles, height = _draw_geometry(rng)
    amplitudes = TARGET_AMPLITUDES * rng.uniform(0.6, 1.4, TARGET_COUNT)
    snr_db = rng.uniform(18.0, 32.0, TARGET_COUNT)
    scene = {
        "height_m": height,
        "target_angles_deg": tuple(float(a) for a in angles),
        "target_amplitudes": tuple(float(a) for a in amplitudes),
        "target_snr_db": tuple(float(s) for s in snr_db),
        "static_names": ("sandy_ground", "tree_line"),
        "static_ranges_m": tuple(float(r) for r in rng.uniform(9.0, 10.9, 2)),
        "static_angles_deg": tuple(float(a) for a in rng.uniform(-35.0, 35.0, 2)),
        "static_amplitudes": tuple(float(a) for a in rng.uniform(0.01, 0.03, 2)),
    }

    swaying = rng.random() < 0.5
    sway_count = int(rng.integers(1, 3))
    sway_targets = tuple(int(t) for t in np.sort(rng.choice(TARGET_COUNT, sway_count, replace=False)))
    sway_std_m = _log_uniform(rng, 2.0e-6, 40.0e-6)
    impairments = Impairments(
        snr_offset_db=float(rng.uniform(-10.0, 0.0)),
        # Uncalibrated radar geometry/profile mismatch.  The generated signal
        # uses the perturbed values while the algorithm receives nominal
        # values in the manifest.
        radar_mount_angle_error_deg=float(np.clip(rng.normal(0.0, 0.5), -2.0, 2.0)),
        radar_array_spacing_error=float(np.clip(rng.normal(0.0, 0.01), -0.03, 0.03)),
        radar_chirp_slope_error=float(np.clip(rng.normal(0.0, 0.001), -0.003, 0.003)),
        # Not calibrated against a measured static capture and the dominant
        # error source of the radar chain, so reports stratify by it.  Ratios
        # near 1 put the IQ circle through the origin and fail every method;
        # the sensitivity study covers that end.
        iq_offset_ratio=_log_uniform(rng, 0.02, 0.5),
        target_sway_std_m=sway_std_m if swaying else 0.0,
        target_sway_targets=sway_targets,
        adxl_bias_x_mps2=float(rng.uniform(-0.6, 0.6)),
        adxl_bias_walk_mps2_per_sqrt_s=_log_uniform(rng, 1.0e-4, 5.0e-3),
        adxl_noise_scale=float(rng.uniform(1.0, 2.0)),
        adxl_scale_error=float(np.clip(rng.normal(0.0, 0.01), -0.03, 0.03)),
        adxl_tilt_gain_mps2_per_m=float(rng.choice((-1.0, 1.0)) * rng.uniform(0.0, 0.2) * 9.80665),
        adxl_timestamp_offset_s=float(np.clip(rng.normal(0.0, 0.5e-3), -2.0e-3, 2.0e-3)),
        adxl_timestamp_jitter_std_s=float(rng.uniform(0.0, 100.0e-6)),
        adxl_clock_phase_s=float(rng.uniform(0.0, 2.0e-3)),
        adxl_odr_error=float(rng.uniform(-0.003, 0.003)),
    )
    return Scenario(**structure, **scene), impairments
