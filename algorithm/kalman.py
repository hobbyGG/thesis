from dataclasses import dataclass, field

import numpy as np

from .config import AlgorithmConfig
from .phase import itoh_unwrap, prediction_correct_wrapped_phase
from .types import AccelerationInput, RadarInput


@dataclass(frozen=True)
class AlgorithmResult:
    method_name: str
    q_hat_m: np.ndarray
    theta_hat_rad: np.ndarray
    theta_dot_hat_radps: np.ndarray
    los_corrected_phase_rad: np.ndarray
    beta_hat: np.ndarray
    r_theta_history: np.ndarray
    innovation_rad: np.ndarray
    extra: dict = field(default_factory=dict)


def _cold_start_count(config: AlgorithmConfig, samples: int) -> int:
    return max(1, min(samples, round(config.cold_start_duration_s * config.sample_rate_hz)))


def _target_biases(radar: RadarInput, config: AlgorithmConfig) -> np.ndarray:
    count = _cold_start_count(config, radar.wrapped_phase_rad.shape[1])
    biases = np.zeros(radar.wrapped_phase_rad.shape[0], dtype=float)
    for i, row in enumerate(radar.wrapped_phase_rad[:, :count]):
        valid = np.isfinite(row)
        if np.any(valid):
            biases[i] = float(np.mean(itoh_unwrap(row[valid])))
    return biases


def run_fixed_beta_kalman(radar: RadarInput, acceleration: AccelerationInput, config: AlgorithmConfig) -> AlgorithmResult:
    """Fuse fixed geometry beta observations with native-time acceleration."""

    targets, samples = radar.wrapped_phase_rad.shape
    beta = np.asarray(radar.measured_beta, dtype=float).copy()
    biases = _target_biases(radar, config)
    selected = np.asarray(radar.selected_indices, dtype=int)
    selected_mask = np.zeros(targets, dtype=bool)
    selected_mask[selected] = True
    x = np.array([0.0, 0.0], dtype=float)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    r = np.clip(np.asarray(radar.initial_r, dtype=float), config.min_measurement_variance, config.max_measurement_variance)
    theta = np.zeros(samples, dtype=float)
    rate = np.zeros(samples, dtype=float)
    corrected = np.full((targets, samples), np.nan, dtype=float)
    innovation = np.full((targets, samples), np.nan, dtype=float)
    r_history = np.full((targets, samples), np.nan, dtype=float)
    preintegration = acceleration.preintegration
    for k in range(samples):
        if k:
            duration = preintegration.duration_s[k - 1]
            delta_q = preintegration.delta_q_m[k - 1]
            delta_v = preintegration.delta_v_mps[k - 1]
            a = np.array([[1.0, duration], [0.0, 1.0]])
            q0 = np.array([[duration**3 / 3.0, duration**2 / 2.0], [duration**2 / 2.0, duration]])
            x = a @ x + (4.0 * np.pi / config.wavelength_m()) * np.array([delta_q, delta_v])
            p = a @ p @ a.T + config.process_noise_intensity * q0
        active = [i for i in selected if radar.available_mask[i, k] and np.isfinite(radar.wrapped_phase_rad[i, k])]
        if active:
            observations = []
            variances = []
            for i in active:
                los = prediction_correct_wrapped_phase(radar.wrapped_phase_rad[i, k], x[0] / beta[i] + biases[i])
                corrected[i, k] = los
                observations.append(beta[i] * (los - biases[i]))
                variances.append(r[i])
            observations = np.asarray(observations)
            variances = np.asarray(variances)
            innovation_values = observations - x[0]
            precision = 1.0 / np.maximum(variances, config.min_measurement_variance)
            z = float(np.sum(precision * observations) / np.sum(precision))
            variance = float(1.0 / np.sum(precision))
            gain = p[:, 0] / (p[0, 0] + variance)
            innovation_mean = z - x[0]
            x = x + gain * innovation_mean
            p = (np.eye(2) - np.outer(gain, np.array([1.0, 0.0]))) @ p
            for local, i in enumerate(active):
                innovation[i, k] = innovation_values[local]
                posterior = observations[local] - x[0]
                instant = posterior**2 + p[0, 0]
                r[i] = np.clip(
                    config.adaptive_r_forgetting * r[i] + (1.0 - config.adaptive_r_forgetting) * instant,
                    config.min_measurement_variance,
                    config.max_measurement_variance,
                )
        theta[k], rate[k] = x
        r_history[:, k] = r
    return AlgorithmResult(
        method_name="fixed_geometry_beta_structural_kalman",
        q_hat_m=theta * config.wavelength_m() / (4.0 * np.pi),
        theta_hat_rad=theta,
        theta_dot_hat_radps=rate,
        los_corrected_phase_rad=corrected,
        beta_hat=beta,
        r_theta_history=r_history,
        innovation_rad=innovation,
        extra={"selected_indices": selected, "beta_source": "angle_geometry", "adaptive_r_mode": "posterior_residual"},
    )
