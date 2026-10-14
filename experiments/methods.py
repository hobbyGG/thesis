"""Estimators and baselines evaluated on one simulated record.

All methods share the radar front end, the recursive circle fit and the frozen
AoA beta, so they differ only in how the structural phase is estimated.  The
true displacement is used for scoring and, for the oracle-beta ablation, for
the target geometry; nowhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from experiments.front import Front, apply_dropout
from paper_bridge_simulation.package_builder import RANGE_RESOLUTION_M, AdxlStream
from paper_bridge_simulation.scenario import Scenario
from system.algorithm.acceleration import RadarIntervalPreintegration
from system.algorithm.config import AlgorithmConfig
from system.algorithm.frontend import TargetData
from system.algorithm.io import build_acceleration_input, build_radar_input
from system.algorithm.kalman import run_fixed_beta_kalman
from system.algorithm.phase import unwrap_nearest_branch
from system.algorithm.run import displacement_error_m
from system.algorithm.types import AccelerationInput, RadarInput

METHODS = (
    "fusion", "kf-only", "fixed-R", "single-target", "complementary",
    "radar-only", "adxl-raw", "adxl-hp", "no-circle", "oracle-beta",
)
# The scored event window ends this long after the train has left.
EVENT_TAIL_S = 0.3
# Angular scale (degrees) against one range bin when matching a detected peak
# to the simulated target it came from.
MATCH_ANGLE_SCALE_DEG = 6.0


@dataclass(frozen=True)
class Tuned:
    """Free parameters of the methods, tuned on the development seeds."""

    fusion_q: float = AlgorithmConfig.process_noise_intensity
    kf_only_q: float = 1.0e4
    fixed_r: float = 1.0e-4
    fixed_r_q: float = 3.0
    complementary_corner_hz: float = 8.0
    adxl_hp_corner_hz: float = 0.3


@dataclass(frozen=True)
class RadarSide:
    front: Front
    radar: RadarInput
    targets: TargetData
    config: AlgorithmConfig
    center_over_radius: float


def prepare_radar(front: Front, dropout: tuple[float, float] | None = None) -> RadarSide:
    """Circle fit and target selection (``dropout`` = (start_s, duration_s) of lost frames)."""
    if dropout is not None:
        front = apply_dropout(front, *dropout)
    radar, targets = build_radar_input(front.targets, front.detection, front.radar_time_ns)
    selected = radar.selected_indices
    centre = np.abs(np.asarray(radar.extra["circle_center"])[selected, -1])
    radius = np.asarray(radar.extra["circle_radius"])[selected, -1]
    ratio = float(np.nanmedian(centre / radius)) if selected.size else float("nan")
    config = AlgorithmConfig(
        sample_rate_hz=front.radar_rate_hz, carrier_frequency_hz=front.carrier_frequency_hz
    )
    return RadarSide(front, radar, targets, config, ratio)


def acceleration_input(side: RadarSide, stream: AdxlStream) -> AccelerationInput:
    acceleration, _ = build_acceleration_input(
        side.front.radar_time_ns, stream.estimated_ns, stream.values[:, 0]
    )
    return acceleration


def without_adxl(acceleration: AccelerationInput) -> AccelerationInput:
    pre = acceleration.preintegration
    return AccelerationInput(
        acceleration.native_time_ns,
        acceleration.native_mps2,
        RadarIntervalPreintegration(pre.duration_s, np.zeros_like(pre.delta_v_mps), np.zeros_like(pre.delta_q_m)),
    )


def kalman(radar: RadarInput, acceleration: AccelerationInput, config: AlgorithmConfig, q: float, **overrides) -> np.ndarray:
    return run_fixed_beta_kalman(
        radar, acceleration, replace(config, process_noise_intensity=q, **overrides)
    ).q_hat_m


def radar_phase_series(radar: RadarInput, config: AlgorithmConfig) -> np.ndarray:
    """Per-frame inverse-variance mean of beta_i * unwrapped phase_i, NaN without any target."""
    selected = np.asarray(radar.selected_indices, dtype=int)
    corrected = unwrap_nearest_branch(radar.wrapped_phase_rad, radar.available_mask, selected)
    variance = np.clip(
        np.asarray(radar.initial_r, dtype=float)[selected],
        config.min_measurement_variance, config.max_measurement_variance,
    )
    observation = np.asarray(radar.measured_beta, dtype=float)[selected, None] * corrected[selected]
    valid = np.isfinite(observation)
    weight = np.where(valid, 1.0 / variance[:, None], 0.0)
    total = weight.sum(axis=0)
    theta = np.sum(weight * np.where(valid, observation, 0.0), axis=0) / np.where(total > 0.0, total, 1.0)
    theta[total == 0.0] = np.nan
    return theta


def hold_last(theta: np.ndarray, config: AlgorithmConfig) -> np.ndarray:
    """Causal zero-order hold of the radar phase series, in metres."""
    last = np.maximum.accumulate(np.where(np.isfinite(theta), np.arange(theta.size), 0))
    return np.nan_to_num(theta[last]) * config.wavelength_m() / (4.0 * np.pi)


def phase_observer(
    theta_measured: np.ndarray, acceleration: AccelerationInput, config: AlgorithmConfig,
    corner_hz: float, *, start_at_measurement: bool,
) -> np.ndarray:
    """Fixed-gain second-order complementary filter, in metres.

    The ADXL preintegration drives the prediction; the radar phase enters only
    through its innovation, with critically damped gains
    (sqrt(2) w, w^2) for w = 2 pi corner_hz.  A NaN measurement skips the
    correction.  With a constant zero measurement the same recursion is a
    high-pass filtered double integration of the ADXL signal alone.
    """
    pre = acceleration.preintegration
    scale = 4.0 * np.pi / config.wavelength_m()
    omega = 2.0 * np.pi * corner_hz
    theta = rate = 0.0
    initialised = not start_at_measurement
    out = np.empty(theta_measured.size)
    for k in range(theta_measured.size):
        duration = 1.0 / config.sample_rate_hz
        if k:
            duration = pre.duration_s[k - 1]
            theta += rate * duration + scale * pre.delta_q_m[k - 1]
            rate += scale * pre.delta_v_mps[k - 1]
        z = theta_measured[k]
        if np.isfinite(z):
            if initialised:
                residual = z - theta
                theta += np.sqrt(2.0) * omega * duration * residual
                rate += omega * omega * duration * residual
            else:
                theta, initialised = z, True
        out[k] = theta
    return out / scale


def adxl_double_integration(acceleration: AccelerationInput, frames: int) -> np.ndarray:
    pre = acceleration.preintegration
    q = np.zeros(frames)
    v = 0.0
    for k in range(pre.duration_s.size):
        q[k + 1] = q[k] + v * pre.duration_s[k] + pre.delta_q_m[k]
        v += pre.delta_v_mps[k]
    return q


def no_circle_phase(targets: TargetData) -> np.ndarray:
    """Phase relative to each target's first valid sample, with no centre correction."""
    available = targets.available_mask
    first = np.argmax(available, axis=1)
    reference = targets.slow_time[np.arange(available.shape[0]), first]
    wrapped = np.angle(targets.slow_time * np.conj(reference)[:, None])
    wrapped[~available] = np.nan
    return wrapped


def oracle_beta(front: Front) -> np.ndarray:
    """beta = 1/|cos| of the simulated target each detected peak is closest to."""
    targets = front.targets
    cost = (
        ((targets.range_m[:, None] - front.scatterer_range_m[None, :]) / RANGE_RESOLUTION_M) ** 2
        + ((targets.angle_deg[:, None] - front.scatterer_angle_deg[None, :]) / MATCH_ANGLE_SCALE_DEG) ** 2
    )
    angle = front.scatterer_angle_deg[np.argmin(cost, axis=1)]
    return 1.0 / np.maximum(np.abs(np.cos(np.deg2rad(angle))), 1.0e-6)


def estimate_all(side: RadarSide, acceleration: AccelerationInput, tuned: Tuned) -> dict[str, np.ndarray]:
    """Displacement estimate (m) of every method."""
    radar, config = side.radar, side.config
    theta = radar_phase_series(radar, config)
    frames = theta.size
    return {
        "fusion": kalman(radar, acceleration, config, tuned.fusion_q),
        "kf-only": kalman(radar, without_adxl(acceleration), config, tuned.kf_only_q),
        "fixed-R": kalman(
            replace(radar, initial_r=np.full_like(radar.initial_r, tuned.fixed_r)),
            acceleration, config, tuned.fixed_r_q, adaptive_r_forgetting=1.0,
        ),
        "single-target": kalman(
            replace(radar, selected_indices=radar.selected_indices[:1]), acceleration, config, tuned.fusion_q
        ),
        "complementary": phase_observer(
            theta, acceleration, config, tuned.complementary_corner_hz, start_at_measurement=True
        ),
        "radar-only": hold_last(theta, config),
        "adxl-raw": adxl_double_integration(acceleration, frames),
        "adxl-hp": phase_observer(
            np.zeros(frames), acceleration, config, tuned.adxl_hp_corner_hz, start_at_measurement=False
        ),
        "no-circle": kalman(
            replace(radar, wrapped_phase_rad=no_circle_phase(side.front.targets)),
            acceleration, config, tuned.fusion_q,
        ),
        "oracle-beta": kalman(
            replace(radar, measured_beta=oracle_beta(side.front)), acceleration, config, tuned.fusion_q
        ),
    }


def event_window(scenario: Scenario) -> tuple[float, float]:
    start = scenario.event_starts_s[0]
    return start, start + scenario.passage_duration_s + EVENT_TAIL_S


def score(q_hat: np.ndarray, side: RadarSide, window: tuple[float, float]) -> dict:
    front = side.front
    error = displacement_error_m(q_hat, front.truth_m, front.time_s, side.config.cold_start_duration_s)
    if not np.all(np.isfinite(error)):
        return {"rmse_um": np.nan, "event_rmse_um": np.nan, "max_err_um": np.nan, "failed": True}
    event = (front.time_s >= window[0]) & (front.time_s <= window[1])
    maximum = float(np.max(np.abs(error)))
    return {
        "rmse_um": float(np.sqrt(np.mean(error**2))) * 1.0e6,
        "event_rmse_um": float(np.sqrt(np.mean(error[event] ** 2))) * 1.0e6,
        "max_err_um": maximum * 1.0e6,
        # A branch slip shifts the estimate by a fraction of half a wavelength.
        "failed": bool(maximum > side.config.wavelength_m() / 8.0),
    }


def run_methods(side: RadarSide, stream: AdxlStream, scenario: Scenario, tuned: Tuned) -> dict[str, dict]:
    """Score every method on one record."""
    estimates = estimate_all(side, acceleration_input(side, stream), tuned)
    window = event_window(scenario)
    return {name: score(estimates[name], side, window) for name in METHODS}
