"""Scratch-only stateful adapter for per-frame beta observations.

The tracked ``algorithm.kalman.run_fixed_beta_kalman`` API takes one beta
vector for an entire run.  This adapter copies its numerical update equations
behind a tiny step API so a rolling geometry loop can supply ``beta_t`` while
keeping ``x``, ``P``, bias and adaptive measurement variance continuous.  It
is intentionally outside ``algorithm/`` and is not an alternate thesis
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from algorithm.config import AlgorithmConfig
from algorithm.phase import itoh_unwrap, prediction_correct_wrapped_phase


@dataclass
class AdapterState:
    x: np.ndarray
    p: np.ndarray
    biases: np.ndarray
    measurement_variance: np.ndarray
    sample_index: int = 0


def _dynamic_cold_start(
    wrapped_phase_rad: np.ndarray,
    beta_by_sample: np.ndarray,
    available_mask: np.ndarray,
    selected_indices: np.ndarray,
    radar_time_ns: np.ndarray,
    initial_r: np.ndarray,
    config: AlgorithmConfig,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Replicate retained cold-start statistics while accepting beta_t."""
    phase = np.asarray(wrapped_phase_rad, dtype=float)
    beta = np.asarray(beta_by_sample, dtype=float)
    available = np.asarray(available_mask, dtype=bool)
    times = np.asarray(radar_time_ns, dtype=np.int64)
    if phase.ndim != 2 or beta.shape != phase.shape or available.shape != phase.shape:
        raise ValueError("phase, beta_by_sample, and available_mask must share (targets, samples)")
    elapsed_s = (times - times[0]).astype(float) * 1.0e-9
    count = max(1, int(np.searchsorted(elapsed_s, config.cold_start_duration_s, side="left")))
    count = min(count, phase.shape[1])
    biases = np.zeros(phase.shape[0], dtype=float)
    initial = np.clip(
        np.asarray(initial_r, dtype=float).copy(),
        config.min_measurement_variance,
        config.max_measurement_variance,
    )
    structural_phase = np.full((phase.shape[0], count), np.nan, dtype=float)
    for i, row in enumerate(phase[:, :count]):
        valid = available[i, :count] & np.isfinite(row) & np.isfinite(beta[i, :count]) & (beta[i, :count] > 0.0)
        if np.any(valid):
            unwrapped = itoh_unwrap(row[valid])
            biases[i] = float(np.mean(unwrapped))
            structural_phase[i, valid] = beta[i, :count][valid] * (unwrapped - biases[i])
    selected = np.asarray(selected_indices, dtype=int)
    if config.cold_start_r_mode != "residual" or selected.size < 2:
        return biases, initial, count
    common = np.full(count, np.nan, dtype=float)
    for k in range(count):
        values = structural_phase[selected, k]
        values = values[np.isfinite(values)]
        if values.size:
            common[k] = float(np.median(values))
    for i in selected:
        residual = structural_phase[i] - common
        residual = residual[np.isfinite(residual)]
        if residual.size >= 2:
            initial[i] = np.clip(
                float(np.var(residual)),
                config.min_measurement_variance,
                config.max_measurement_variance,
            )
    return biases, initial, count


class StatefulKalmanAdapter:
    """Small stateful counterpart to the retained fixed-beta update loop."""

    def __init__(
        self,
        config: AlgorithmConfig,
        *,
        biases: np.ndarray,
        initial_r: np.ndarray,
        selected_indices: Iterable[int],
        reference_dt_s: float,
    ) -> None:
        self.config = config
        self.reference_dt_s = float(reference_dt_s)
        self.selected_indices = np.asarray(selected_indices, dtype=int).copy()
        self.state = AdapterState(
            x=np.array([0.0, 0.0], dtype=float),
            p=np.diag([config.initial_state_variance, config.initial_rate_variance]),
            biases=np.asarray(biases, dtype=float).copy(),
            measurement_variance=np.clip(
                np.asarray(initial_r, dtype=float).copy(),
                config.min_measurement_variance,
                config.max_measurement_variance,
            ),
        )
        self.beta_history: list[np.ndarray] = []

    @classmethod
    def from_bootstrap(
        cls,
        config: AlgorithmConfig,
        *,
        wrapped_phase_rad: np.ndarray,
        beta_by_sample: np.ndarray,
        available_mask: np.ndarray,
        selected_indices: Iterable[int],
        initial_r: np.ndarray,
        radar_time_ns: np.ndarray,
        reference_dt_s: float,
    ) -> "StatefulKalmanAdapter":
        biases, initial, _ = _dynamic_cold_start(
            wrapped_phase_rad,
            beta_by_sample,
            available_mask,
            np.asarray(selected_indices, dtype=int),
            radar_time_ns,
            initial_r,
            config,
        )
        return cls(
            config,
            biases=biases,
            initial_r=initial,
            selected_indices=selected_indices,
            reference_dt_s=reference_dt_s,
        )

    @classmethod
    def from_initial_sample(
        cls,
        config: AlgorithmConfig,
        *,
        wrapped_phase_t: np.ndarray,
        available_t: np.ndarray,
        selected_indices: Iterable[int],
        reference_dt_s: float,
    ) -> "StatefulKalmanAdapter":
        """Causally initialize from one sample, without future warm-up data."""
        phase = np.asarray(wrapped_phase_t, dtype=float)
        available = np.asarray(available_t, dtype=bool)
        if phase.ndim != 1 or available.shape != phase.shape:
            raise ValueError("wrapped_phase_t and available_t must be matching 1-D arrays")
        biases = np.where(available & np.isfinite(phase), phase, 0.0)
        initial_r = np.full(phase.shape, config.initial_measurement_variance, dtype=float)
        return cls(
            config,
            biases=biases,
            initial_r=initial_r,
            selected_indices=selected_indices,
            reference_dt_s=reference_dt_s,
        )

    def step(
        self,
        wrapped_phase_t: np.ndarray,
        beta_t: np.ndarray,
        available_t: np.ndarray | None = None,
        *,
        duration_s: float | None = None,
        delta_q_m: float = 0.0,
        delta_v_mps: float = 0.0,
        selected_indices: Iterable[int] | None = None,
    ) -> dict[str, object]:
        """Consume one phase/beta sample and return the updated state.

        ``delta_q_m`` and ``delta_v_mps`` are the native-time acceleration
        preintegration over the interval immediately before this sample.  The
        first sample has no preceding interval, matching the retained loop.
        Target indices must remain stable; callers changing target cardinality
        must perform association before calling this method.
        """
        phase = np.asarray(wrapped_phase_t, dtype=float)
        beta = np.asarray(beta_t, dtype=float)
        if phase.ndim != 1 or beta.shape != phase.shape:
            raise ValueError("wrapped_phase_t and beta_t must be 1-D arrays with equal shape")
        if available_t is None:
            available = np.isfinite(phase)
        else:
            available = np.asarray(available_t, dtype=bool)
            if available.shape != phase.shape:
                raise ValueError("available_t shape must match wrapped_phase_t")
        if np.any(~np.isfinite(beta)) or np.any(beta <= 0.0):
            raise ValueError("beta_t must be finite and strictly positive")
        k = self.state.sample_index
        duration = self.reference_dt_s if duration_s is None else float(duration_s)
        if duration <= 0.0:
            raise ValueError("duration_s must be positive")
        x = self.state.x
        p = self.state.p
        if k:
            a = np.array([[1.0, duration], [0.0, 1.0]])
            q0 = np.array([[duration**3 / 3.0, duration**2 / 2.0], [duration**2 / 2.0, duration]])
            x = a @ x + (4.0 * np.pi / self.config.wavelength_m()) * np.array([delta_q_m, delta_v_mps])
            p = a @ p @ a.T + self.config.process_noise_intensity * q0

        selected = self.selected_indices if selected_indices is None else np.asarray(selected_indices, dtype=int)
        active = [
            int(i) for i in selected
            if 0 <= int(i) < phase.size and available[int(i)] and np.isfinite(phase[int(i)])
        ]
        corrected = np.full(phase.shape, np.nan, dtype=float)
        innovation = np.full(phase.shape, np.nan, dtype=float)
        if active:
            observations = []
            variances = []
            for i in active:
                los = prediction_correct_wrapped_phase(
                    phase[i], x[0] / beta[i] + self.state.biases[i]
                )
                corrected[i] = los
                observations.append(beta[i] * (los - self.state.biases[i]))
                variances.append(self.state.measurement_variance[i])
            observations = np.asarray(observations, dtype=float)
            variances = np.asarray(variances, dtype=float)
            innovation_values = observations - x[0]
            precision = 1.0 / np.maximum(variances, self.config.min_measurement_variance)
            z = float(np.sum(precision * observations) / np.sum(precision))
            variance = float(1.0 / np.sum(precision))
            gain = p[:, 0] / (p[0, 0] + variance)
            x = x + gain * (z - x[0])
            p = (np.eye(2) - np.outer(gain, np.array([1.0, 0.0]))) @ p
            for local, i in enumerate(active):
                innovation[i] = innovation_values[local]
                posterior = observations[local] - x[0]
                instant = posterior**2 + p[0, 0]
                forgetting = self.config.adaptive_r_forgetting ** (duration / self.reference_dt_s)
                self.state.measurement_variance[i] = np.clip(
                    forgetting * self.state.measurement_variance[i]
                    + (1.0 - forgetting) * instant,
                    self.config.min_measurement_variance,
                    self.config.max_measurement_variance,
                )
        self.state.x = x
        self.state.p = p
        self.state.sample_index += 1
        self.beta_history.append(beta.copy())
        return {
            "sample_index": k,
            "q_hat_m": float(x[0] * self.config.wavelength_m() / (4.0 * np.pi)),
            "theta_hat_rad": float(x[0]),
            "theta_dot_hat_radps": float(x[1]),
            "corrected_phase_rad": corrected,
            "innovation_rad": innovation,
            "measurement_variance": self.state.measurement_variance.copy(),
            "active_indices": np.asarray(active, dtype=int),
        }
