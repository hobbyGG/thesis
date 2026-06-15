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

    q_m = np.zeros_like(t)
    v_mps = np.zeros_like(t)
    a_mps2 = np.zeros_like(t)
    for amp_m, freq_hz, phase_rad in zip(amplitudes_m, frequencies_hz, phases_rad):
        omega = 2.0 * np.pi * freq_hz
        argument = omega * t + phase_rad
        q_m += amp_m * np.sin(argument)
        v_mps += amp_m * omega * np.cos(argument)
        a_mps2 += -amp_m * omega**2 * np.sin(argument)

    return TruthSignal(
        t=t,
        q_m=q_m,
        v_mps=v_mps,
        a_mps2=a_mps2,
        frequencies_hz=frequencies_hz,
        amplitudes_m=amplitudes_m,
        phases_rad=[float(p) for p in phases_rad],
    )
