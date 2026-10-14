"""One simulation trial: generate a package, run the estimator and its baselines.

All methods share the same radar front end (range FFT, DBF, IQ-circle phase,
frozen AoA beta); they differ only in how the structural phase is estimated.
Truth is used for scoring only.
"""

from __future__ import annotations

import tempfile
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np

from paper_bridge_simulation.package_builder import (
    Impairments,
    PEAK_DEFLECTION_M,
    _adxl_package,
    adxl_sensed_acceleration,
    generate,
)
from paper_bridge_simulation.response import simulate_response
from system.algorithm.acceleration import (
    RadarIntervalPreintegration,
    preintegrate_acceleration_to_radar,
    remove_static_bias,
)
from system.algorithm.config import AlgorithmConfig
from system.algorithm.io import build_algorithm_inputs, load_capture_package
from system.algorithm.kalman import run_fixed_beta_kalman
from system.algorithm.phase import recursive_circle_phase, unwrap_nearest_branch
from system.algorithm.types import AccelerationInput, RadarInput

EVENT_WINDOW_S = (0.5, 1.3)  # first train event of the A20 envelope
FAILURE_FRACTION_OF_PEAK = 0.06  # about 100 um for the 1.712 mm A20 peak
_BASE_RADAR_CACHE: dict[tuple, tuple] = {}


@lru_cache(maxsize=1)
def _cached_response():
    return simulate_response()


def _config(capture, radar_rate: float, **overrides) -> AlgorithmConfig:
    meta = capture.radar_metadata
    carrier = float(meta.get("start_frequency_hz", 77.0e9))
    adc_rate = float(meta.get("adc_sample_rate_hz", 0.0))
    slope = float(meta.get("chirp_slope_hz_per_s", 0.0))
    if adc_rate > 0.0 and slope != 0.0:
        centre = (capture.frontend.num_adc_samples - 1) / 2.0
        carrier += slope * (float(meta.get("adc_start_time_s", 0.0)) + centre / adc_rate)
    return AlgorithmConfig(sample_rate_hz=float(radar_rate), carrier_frequency_hz=carrier, **overrides)


def radar_only_displacement(radar, config: AlgorithmConfig, warm: np.ndarray) -> np.ndarray:
    """Causal per-frame inverse-variance mean of beta_i * unwrapped phase_i, no filter."""
    selected = np.asarray(radar.selected_indices, dtype=int)
    corrected = unwrap_nearest_branch(radar.wrapped_phase_rad, radar.available_mask, selected)
    beta = np.asarray(radar.measured_beta, dtype=float)
    weight = 1.0 / np.asarray(radar.initial_r, dtype=float)
    theta = np.zeros(corrected.shape[1], dtype=float)
    last = 0.0
    for k in range(theta.size):
        active = [i for i in selected if np.isfinite(corrected[i, k])]
        if active:
            w = weight[active]
            last = float(np.sum(w * beta[active] * corrected[active, k]) / np.sum(w))
        theta[k] = last
    q = theta * config.wavelength_m() / (4.0 * np.pi)
    return q - np.mean(q[warm])


def adxl_only_displacement(acceleration: AccelerationInput, n_samples: int) -> np.ndarray:
    """Open-loop double integration of the ADXL preintegration increments."""
    pre = acceleration.preintegration
    dt = pre.duration_s
    q = np.zeros(n_samples, dtype=float)
    v = 0.0
    for k in range(dt.size):
        q[k + 1] = q[k] + v * dt[k] + pre.delta_q_m[k]
        v += pre.delta_v_mps[k]
    return q


def _score(q_hat: np.ndarray, truth: np.ndarray, t: np.ndarray, peak_m: float) -> dict:
    err = q_hat - truth
    event = (t >= EVENT_WINDOW_S[0]) & (t <= EVENT_WINDOW_S[1])
    rmse = float(np.sqrt(np.mean(err**2)))
    return {
        "rmse_m": rmse,
        "event_rmse_m": float(np.sqrt(np.mean(err[event] ** 2))),
        "peak_err_m": float(np.max(np.abs(err))),
        "failed": bool(not np.isfinite(rmse) or rmse > FAILURE_FRACTION_OF_PEAK * peak_m),
    }


def _load_or_build_inputs(impairments: Impairments, seed: int, duration_s: float):
    base_key = (
        seed,
        duration_s,
        impairments.snr_offset_db,
        impairments.peak_deflection_m,
        impairments.target_sway_std_m,
        impairments.target_sway_corner_hz,
    )
    is_reusable_regime = (
        impairments.snr_offset_db in (0.0, -10.0)
        and impairments.peak_deflection_m == PEAK_DEFLECTION_M
        and impairments.target_sway_std_m == 0.0
    )
    if base_key in _BASE_RADAR_CACHE:
        base_capture, base_radar, base_targets, radar_rate = _BASE_RADAR_CACHE[base_key]
    else:
        with tempfile.TemporaryDirectory(prefix="sim_trial_") as tmp:
            package = generate(
                Path(tmp) / "pkg",
                duration_s=duration_s,
                seed=seed,
                impairments=replace(impairments, radar_dropout_s=0.0),
            )
            base_capture = load_capture_package(package)
            base_radar, _, base_targets, radar_rate = build_algorithm_inputs(base_capture)
        if is_reusable_regime:
            # Keep only the current seed's reusable regimes in cache.
            stale = [k for k in _BASE_RADAR_CACHE if k[0] != seed]
            for k in stale:
                del _BASE_RADAR_CACHE[k]
            _BASE_RADAR_CACHE[base_key] = (base_capture, base_radar, base_targets, radar_rate)

    if impairments.radar_dropout_s > 0.0:
        drop_start = int(round(impairments.radar_dropout_start_s * radar_rate))
        drop_end = drop_start + int(round(impairments.radar_dropout_s * radar_rate))
        slow_time = np.array(base_targets.slow_time, copy=True)
        slow_time[:, drop_start:drop_end] = np.nan + 1j * np.nan
        available_mask = np.array(base_targets.available_mask, copy=True)
        available_mask[:, drop_start:drop_end] = False
        wrapped, centers, radii, circle_residual, normalized_iq = recursive_circle_phase(slow_time)
        radar = RadarInput(
            base_radar.measured_beta,
            wrapped,
            available_mask,
            base_radar.selected_indices,
            base_radar.initial_r,
            {
                **base_radar.extra,
                "circle_center": centers,
                "circle_radius": radii,
                "circle_residual": circle_residual,
                "normalized_iq": normalized_iq,
            },
        )
    else:
        radar = base_radar

    reference_time_s, _, acceleration_ref, _ = _cached_response()
    amplitude_scale = impairments.peak_deflection_m / PEAK_DEFLECTION_M
    sensed_a = adxl_sensed_acceleration(reference_time_s, amplitude_scale * acceleration_ref, duration_s)
    with tempfile.TemporaryDirectory(prefix="sim_adxl_") as tmp:
        root = Path(tmp)
        _adxl_package(root, sensed_a, seed, impairments)
        adxl_dir = root / "adxl355" / "algorithm_input"
        adxl_accel = np.load(adxl_dir / "acceleration_mps2.npy", allow_pickle=False)
        adxl_time_ns = np.load(adxl_dir / "estimated_sample_monotonic_ns.npy", allow_pickle=False)
    radar_time_ns = np.asarray(radar.extra["radar_time_ns"], dtype=np.int64)
    # Same ADXL path as system.algorithm.io.build_algorithm_inputs.
    structural_accel, _ = remove_static_bias(
        radar_time_ns, adxl_time_ns, adxl_accel[:, 0], AlgorithmConfig().cold_start_duration_s
    )
    preintegration = preintegrate_acceleration_to_radar(radar_time_ns, adxl_time_ns, structural_accel)
    acceleration = AccelerationInput(adxl_time_ns, structural_accel, preintegration)
    return base_capture, radar, acceleration, radar_rate


def run_trial(
    impairments: Impairments,
    seed: int,
    duration_s: float,
    process_noises: tuple[float, ...],
    extra_methods: bool = True,
) -> dict[str, dict]:
    """Return {method_name: metrics}.  ``kf+adxl@q`` is the proposed fusion."""
    capture, radar, acceleration, radar_rate = _load_or_build_inputs(impairments, seed, duration_s)

    radar_time_ns = np.asarray(radar.extra["radar_time_ns"], dtype=np.int64)
    t = (radar_time_ns - radar_time_ns[0]) * 1.0e-9
    config = _config(capture, radar_rate)
    warm = t <= config.cold_start_duration_s
    truth = np.interp(
        radar_time_ns.astype(float),
        np.asarray(capture.truth_time_ns, dtype=float),
        np.asarray(capture.truth_displacement_m, dtype=float),
    )
    truth = truth - truth[warm].mean()

    peak = impairments.peak_deflection_m
    pre = acceleration.preintegration
    no_adxl = AccelerationInput(
        acceleration.native_time_ns,
        acceleration.native_mps2,
        RadarIntervalPreintegration(pre.duration_s, np.zeros_like(pre.delta_v_mps), np.zeros_like(pre.delta_q_m)),
    )

    results: dict[str, dict] = {}
    for q in process_noises:
        cfg = replace(config, process_noise_intensity=q)
        results[f"kf+adxl@{q:g}"] = _score(run_fixed_beta_kalman(radar, acceleration, cfg).q_hat_m, truth, t, peak)
        results[f"kf-only@{q:g}"] = _score(run_fixed_beta_kalman(radar, no_adxl, cfg).q_hat_m, truth, t, peak)
    if extra_methods:
        cfg = replace(config, process_noise_intensity=process_noises[0])
        results["radar-unfiltered"] = _score(radar_only_displacement(radar, config, warm), truth, t, peak)
        results["adxl-double-integration"] = _score(
            adxl_only_displacement(acceleration, radar_time_ns.size),
            truth,
            t,
            peak,
        )
        results[f"kf+adxl-fixedR@{cfg.process_noise_intensity:g}"] = _score(
            run_fixed_beta_kalman(radar, acceleration, replace(cfg, adaptive_r_forgetting=1.0)).q_hat_m, truth, t, peak
        )
        single_radar = replace(radar, selected_indices=radar.selected_indices[:1])
        results[f"kf+adxl-single@{cfg.process_noise_intensity:g}"] = _score(
            run_fixed_beta_kalman(single_radar, acceleration, cfg).q_hat_m, truth, t, peak
        )
    results["_meta"] = {"selected_targets": int(radar.selected_indices.size)}
    return results
