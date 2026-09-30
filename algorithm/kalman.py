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


def _cold_start_count(radar: RadarInput, config: AlgorithmConfig, samples: int) -> int:
    if "radar_time_ns" in radar.extra:
        times = np.asarray(radar.extra["radar_time_ns"], dtype=np.int64)
        elapsed_s = (times - times[0]).astype(float) * 1.0e-9
        return max(1, int(np.searchsorted(elapsed_s, config.cold_start_duration_s, side="left")))
    return max(1, min(samples, round(config.cold_start_duration_s * config.sample_rate_hz)))


def _cold_start_statistics(radar: RadarInput, config: AlgorithmConfig) -> tuple[np.ndarray, np.ndarray]:
    count = _cold_start_count(radar, config, radar.wrapped_phase_rad.shape[1])
    biases = np.zeros(radar.wrapped_phase_rad.shape[0], dtype=float)
    initial_r = np.clip(
        np.asarray(radar.initial_r, dtype=float).copy(),
        config.min_measurement_variance,
        config.max_measurement_variance,
    )
    if config.cold_start_r_mode != "residual":
        for i, row in enumerate(radar.wrapped_phase_rad[:, :count]):
            valid = np.isfinite(row)
            if np.any(valid):
                biases[i] = float(np.mean(itoh_unwrap(row[valid])))
        return biases, initial_r

    beta = np.asarray(radar.measured_beta, dtype=float)
    structural_phase = np.full((radar.wrapped_phase_rad.shape[0], count), np.nan, dtype=float)
    for i, row in enumerate(radar.wrapped_phase_rad[:, :count]):
        valid = np.isfinite(row)
        if np.any(valid):
            unwrapped = itoh_unwrap(row[valid])
            biases[i] = float(np.mean(unwrapped))
            structural_phase[i, valid] = beta[i] * (unwrapped - biases[i])

    selected = np.asarray(radar.selected_indices, dtype=int)
    if selected.size < 2:
        return biases, initial_r

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
            initial_r[i] = np.clip(
                float(np.var(residual)),
                config.min_measurement_variance,
                config.max_measurement_variance,
            )
    return biases, initial_r


def run_fixed_beta_kalman(radar: RadarInput, acceleration: AccelerationInput, config: AlgorithmConfig) -> AlgorithmResult:
    """Fuse fixed geometry beta observations with native-time acceleration."""

    targets, samples = radar.wrapped_phase_rad.shape
    beta = np.asarray(radar.measured_beta, dtype=float).copy()
    biases, initial_r = _cold_start_statistics(radar, config)
    selected = np.asarray(radar.selected_indices, dtype=int)
    x = np.array([0.0, 0.0], dtype=float)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    r = initial_r.copy()
    theta = np.zeros(samples, dtype=float)
    rate = np.zeros(samples, dtype=float)
    corrected = np.full((targets, samples), np.nan, dtype=float)
    innovation = np.full((targets, samples), np.nan, dtype=float)
    r_history = np.full((targets, samples), np.nan, dtype=float)
    preintegration = acceleration.preintegration
    reference_dt = float(radar.extra.get("frame_period_s", 1.0 / config.sample_rate_hz))
    for k in range(samples):
        duration = reference_dt
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
                # Keep the same physical adaptation time across frame and
                # burst-like loop observations: rho(dt) = rho_frame**(dt/T).
                forgetting = config.adaptive_r_forgetting ** (duration / reference_dt)
                r[i] = np.clip(
                    forgetting * r[i] + (1.0 - forgetting) * instant,
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
        extra={
            "selected_indices": selected,
            "beta_source": "angle_geometry",
            "adaptive_r_mode": "cold_start_residual_then_posterior",
            "cold_start_r_mode": config.cold_start_r_mode,
            "initial_r": initial_r,
        },
    )
