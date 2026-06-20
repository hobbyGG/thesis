from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .config import Phase1Config


@dataclass(frozen=True)
class TruthSignal:
    t: np.ndarray
    q_m: np.ndarray
    v_mps: np.ndarray
    a_mps2: np.ndarray
    frequencies_hz: Sequence[float]
    amplitudes_m: Sequence[float]
    phases_rad: Sequence[float]


def generate_component_frequencies(
    nominal_frequencies_hz: Sequence[float],
    jitter_hz: float,
    seed: int,
) -> list[float]:
    """Generate reproducible two-decimal frequencies around nominal modes."""

    rng = np.random.default_rng(seed)
    frequencies = []
    for nominal in nominal_frequencies_hz:
        value = rng.uniform(nominal - jitter_hz, nominal + jitter_hz)
        frequencies.append(round(float(value), 2))
    return frequencies


def _quiet_start_envelope(t: np.ndarray, start_s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if start_s <= 0.0:
        return np.ones_like(t), np.zeros_like(t), np.zeros_like(t)

    if t.size < 2:
        return np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)

    sample_period_s = float(t[1] - t[0])
    remaining_s = max(float(t[-1] - start_s), sample_period_s)
    ramp_s = min(0.05, remaining_s / 5.0)
    ramp_s = max(ramp_s, 2.0 * sample_period_s)

    gate = np.zeros_like(t)
    gate_dot = np.zeros_like(t)
    gate_ddot = np.zeros_like(t)

    ramp = (t >= start_s) & (t < start_s + ramp_s)
    after = t >= start_s + ramp_s
    u = (t[ramp] - start_s) / ramp_s

    gate[ramp] = 10.0 * u**3 - 15.0 * u**4 + 6.0 * u**5
    gate_dot[ramp] = (30.0 * u**2 - 60.0 * u**3 + 30.0 * u**4) / ramp_s
    gate_ddot[ramp] = (60.0 * u - 180.0 * u**2 + 120.0 * u**3) / ramp_s**2
    gate[after] = 1.0

    return gate, gate_dot, gate_ddot


def _vehicle_event_envelope(
    t: np.ndarray,
    center_s: float,
    width_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if width_s <= 0.0:
        raise ValueError("vehicle_event_width_s must be positive")

    normalized = (t - center_s) / width_s
    envelope = np.exp(-0.5 * normalized**2)
    envelope_dot = envelope * (-(t - center_s) / width_s**2)
    envelope_ddot = envelope * (((t - center_s) ** 2 / width_s**4) - (1.0 / width_s**2))
    return envelope, envelope_dot, envelope_ddot


def _smooth_transition(
    t: np.ndarray,
    start_s: float,
    end_s: float,
    left_level: float,
    right_level: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    value = np.full_like(t, float(left_level), dtype=float)
    dot = np.zeros_like(t, dtype=float)
    ddot = np.zeros_like(t, dtype=float)
    if end_s <= start_s:
        value[t >= start_s] = float(right_level)
        return value, dot, ddot

    after = t >= end_s
    ramp = (t >= start_s) & (t < end_s)
    value[after] = float(right_level)
    u = (t[ramp] - start_s) / (end_s - start_s)
    level_delta = float(right_level) - float(left_level)
    smooth = 10.0 * u**3 - 15.0 * u**4 + 6.0 * u**5
    smooth_dot = (30.0 * u**2 - 60.0 * u**3 + 30.0 * u**4) / (end_s - start_s)
    smooth_ddot = (60.0 * u - 180.0 * u**2 + 120.0 * u**3) / (end_s - start_s) ** 2
    value[ramp] = float(left_level) + level_delta * smooth
    dot[ramp] = level_delta * smooth_dot
    ddot[ramp] = level_delta * smooth_ddot
    return value, dot, ddot


def _cold_start_ramp_strong_wrapping_envelope(t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Envelope for a cold-start, bootstrap, rapid-growth wrapping experiment."""

    if t.size < 2:
        return np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)

    micro_level = 0.035
    decay_level = 0.18

    value = np.zeros_like(t, dtype=float)
    dot = np.zeros_like(t, dtype=float)
    ddot = np.zeros_like(t, dtype=float)

    segments = (
        (0.20, 0.30, 0.0, micro_level),
        (0.80, 1.40, micro_level, 1.0),
        (3.20, 4.20, 1.0, decay_level),
    )
    for start_s, end_s, left_level, right_level in segments:
        ramp_value, ramp_dot, ramp_ddot = _smooth_transition(t, start_s, end_s, left_level, right_level)
        active = t >= start_s
        value[active] = ramp_value[active]
        dot[active] = ramp_dot[active]
        ddot[active] = ramp_ddot[active]

    plateau = (t >= 0.30) & (t < 0.80)
    value[plateau] = micro_level
    dot[plateau] = 0.0
    ddot[plateau] = 0.0

    strong = (t >= 1.40) & (t < 3.20)
    value[strong] = 1.0
    dot[strong] = 0.0
    ddot[strong] = 0.0

    return value, dot, ddot


def _cold_start_ramp_envelope(t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Envelope for regular bridge responses that grow from weak to full motion."""

    if t.size < 2:
        return np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)

    micro_level = 0.08
    value = np.zeros_like(t, dtype=float)
    dot = np.zeros_like(t, dtype=float)
    ddot = np.zeros_like(t, dtype=float)

    segments = (
        (0.20, 0.30, 0.0, micro_level),
        (0.80, 1.40, micro_level, 1.0),
    )
    for start_s, end_s, left_level, right_level in segments:
        ramp_value, ramp_dot, ramp_ddot = _smooth_transition(t, start_s, end_s, left_level, right_level)
        active = t >= start_s
        value[active] = ramp_value[active]
        dot[active] = ramp_dot[active]
        ddot[active] = ramp_ddot[active]

    micro = (t >= 0.30) & (t < 0.80)
    value[micro] = micro_level
    dot[micro] = 0.0
    ddot[micro] = 0.0

    full = t >= 1.40
    value[full] = 1.0
    dot[full] = 0.0
    ddot[full] = 0.0

    return value, dot, ddot


def _cold_start_vehicle_event_envelope(
    t: np.ndarray,
    center_s: float,
    width_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vehicle-event envelope with a weak pre-event vibration floor."""

    micro_value, micro_dot, micro_ddot = _smooth_transition(t, 0.20, 0.30, 0.0, 0.06)
    gaussian, gaussian_dot, gaussian_ddot = _vehicle_event_envelope(t, center_s, width_s)
    value = micro_value + (1.0 - micro_value) * gaussian
    dot = micro_dot * (1.0 - gaussian) + (1.0 - micro_value) * gaussian_dot
    ddot = micro_ddot * (1.0 - gaussian) - 2.0 * micro_dot * gaussian_dot + (
        1.0 - micro_value
    ) * gaussian_ddot
    return value, dot, ddot


def _combine_envelopes(
    first: tuple[np.ndarray, np.ndarray, np.ndarray],
    second: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    value_a, dot_a, ddot_a = first
    value_b, dot_b, ddot_b = second
    value = value_a * value_b
    dot = dot_a * value_b + value_a * dot_b
    ddot = ddot_a * value_b + 2.0 * dot_a * dot_b + value_a * ddot_b
    return value, dot, ddot


def generate_multifrequency_truth(config: Phase1Config) -> TruthSignal:
    """Generate q, velocity, and acceleration from analytic harmonic components."""

    if config.sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    if config.duration_s <= 0:
        raise ValueError("duration_s must be positive")

    frequencies_hz = generate_component_frequencies(
        config.nominal_frequencies_hz,
        config.frequency_jitter_hz,
        config.seed,
    )
    if len(config.component_amplitudes_mm) != len(frequencies_hz):
        raise ValueError("component_amplitudes_mm must match nominal_frequencies_hz")

    n_samples = int(round(config.duration_s * config.sample_rate_hz))
    t = np.arange(n_samples, dtype=float) / config.sample_rate_hz
    amplitudes_m = [float(mm) * 1e-3 for mm in config.component_amplitudes_mm]

    phase_rng = np.random.default_rng(config.seed + 1)
    phases_rad = phase_rng.uniform(0.0, 2.0 * np.pi, size=len(frequencies_hz))

    envelope = _quiet_start_envelope(t, config.quiet_start_duration_s)
    if config.motion_profile == "multifrequency":
        pass
    elif config.motion_profile == "cold_start_ramp":
        envelope = _combine_envelopes(envelope, _cold_start_ramp_envelope(t))
    elif config.motion_profile == "vehicle_event":
        vehicle_envelope = _vehicle_event_envelope(
            t,
            config.vehicle_event_center_s,
            config.vehicle_event_width_s,
        )
        envelope = _combine_envelopes(envelope, vehicle_envelope)
    elif config.motion_profile == "cold_start_vehicle_event":
        vehicle_envelope = _cold_start_vehicle_event_envelope(
            t,
            config.vehicle_event_center_s,
            config.vehicle_event_width_s,
        )
        envelope = _combine_envelopes(envelope, vehicle_envelope)
    elif config.motion_profile in ("cold_start_ramp_strong_wrapping", "segmented_strong_wrapping"):
        envelope = _combine_envelopes(envelope, _cold_start_ramp_strong_wrapping_envelope(t))
    else:
        raise ValueError(f"unsupported motion_profile: {config.motion_profile}")

    envelope_value, envelope_dot, envelope_ddot = envelope
    q_m = np.zeros_like(t)
    v_mps = np.zeros_like(t)
    a_mps2 = np.zeros_like(t)
    for amp_m, freq_hz, phase_rad in zip(amplitudes_m, frequencies_hz, phases_rad):
        omega = 2.0 * np.pi * freq_hz
        argument = omega * t + phase_rad
        sin_argument = np.sin(argument)
        cos_argument = np.cos(argument)
        q_m += amp_m * envelope_value * sin_argument
        v_mps += amp_m * (envelope_dot * sin_argument + envelope_value * omega * cos_argument)
        a_mps2 += amp_m * (
            envelope_ddot * sin_argument
            + 2.0 * envelope_dot * omega * cos_argument
            - envelope_value * omega**2 * sin_argument
        )

    q_m, v_mps, a_mps2, amplitudes_m = _scale_to_peak_displacement(
        q_m,
        v_mps,
        a_mps2,
        amplitudes_m,
        config.truth_peak_displacement_mm,
    )

    return TruthSignal(
        t=t,
        q_m=q_m,
        v_mps=v_mps,
        a_mps2=a_mps2,
        frequencies_hz=frequencies_hz,
        amplitudes_m=amplitudes_m,
        phases_rad=[float(p) for p in phases_rad],
    )


def _scale_to_peak_displacement(q_m, v_mps, a_mps2, amplitudes_m, peak_displacement_mm):
    if peak_displacement_mm is None:
        return q_m, v_mps, a_mps2, amplitudes_m
    target_peak_m = float(peak_displacement_mm) * 1.0e-3
    if target_peak_m <= 0.0:
        raise ValueError("truth_peak_displacement_mm must be positive when provided")
    current_peak_m = float(np.max(np.abs(q_m))) if q_m.size else 0.0
    if current_peak_m <= 1.0e-18:
        return q_m, v_mps, a_mps2, amplitudes_m
    scale = target_peak_m / current_peak_m
    return (
        q_m * scale,
        v_mps * scale,
        a_mps2 * scale,
        [float(amp_m) * scale for amp_m in amplitudes_m],
    )


def generate_truth_signal(config: Phase1Config) -> TruthSignal:
    if config.motion_profile == "measured_bridge":
        from .measured_bridge import load_measured_bridge_record

        return load_measured_bridge_record(config).truth
    return generate_multifrequency_truth(config)
