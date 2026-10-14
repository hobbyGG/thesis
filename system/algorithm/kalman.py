from dataclasses import dataclass, field

import numpy as np

from .config import AlgorithmConfig
from .phase import unwrap_nearest_branch
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


def run_fixed_beta_kalman(radar: RadarInput, acceleration: AccelerationInput, config: AlgorithmConfig) -> AlgorithmResult:
    """Shared structural-phase Kalman filter.

    State: [Theta, Theta_dot] with Theta = 4*pi*q/lambda.  The preintegrated
    ADXL increments enter the prediction as a control input.  Each target's
    wrapped phase is continued to the 2*pi branch nearest its own previous
    phase; acceleration is not used to select the branch.  Valid targets are
    merged by inverse-variance weighting into one scalar update per frame, and
    each target's variance is then updated from its posterior residual.
    """

    targets, samples = radar.wrapped_phase_rad.shape
    beta_aoa = np.asarray(radar.measured_beta, dtype=float).copy()
    initial_r = np.clip(
        np.asarray(radar.initial_r, dtype=float).copy(),
        config.min_measurement_variance,
        config.max_measurement_variance,
    )
    selected = np.asarray(radar.selected_indices, dtype=int)
    preintegration = acceleration.preintegration
    reference_dt = float(radar.extra.get("sample_period_s", 1.0 / config.sample_rate_hz))

    corrected = unwrap_nearest_branch(radar.wrapped_phase_rad, radar.available_mask, selected)

    x = np.array([0.0, 0.0], dtype=float)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    r = initial_r.copy()
    theta = np.zeros(samples, dtype=float)
    rate = np.zeros(samples, dtype=float)
    innovation = np.full((targets, samples), np.nan, dtype=float)
    r_history = np.full((targets, samples), np.nan, dtype=float)
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
        active = [i for i in selected if np.isfinite(corrected[i, k])]
        if active:
            observations = []
            variances = []
            for i in active:
                observations.append(beta_aoa[i] * corrected[i, k])
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
                forgetting = config.adaptive_r_forgetting ** (duration / reference_dt)
                r[i] = np.clip(
                    forgetting * r[i] + (1.0 - forgetting) * instant,
                    config.min_measurement_variance,
                    config.max_measurement_variance,
                )
        theta[k], rate[k] = x
        r_history[:, k] = r
    return AlgorithmResult(
        method_name="base_iq_circle_structural_kalman",
        q_hat_m=theta * config.wavelength_m() / (4.0 * np.pi),
        theta_hat_rad=theta,
        theta_dot_hat_radps=rate,
        los_corrected_phase_rad=corrected,
        beta_hat=beta_aoa,
        r_theta_history=r_history,
        innovation_rad=innovation,
        extra={
            "selected_indices": selected,
            "beta_source": "frozen_aoa_geometry",
            "adaptive_r_mode": "posterior_residual",
            "phase_unwrap_mode": "previous_target_phase",
            "circle_source": "recursive_algebraic_fit",
            "initial_r": initial_r,
        },
    )
