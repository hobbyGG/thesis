from dataclasses import dataclass

import numpy as np

from ..phase_utils import prediction_correct_wrapped_phase, wrap_to_pi
from .config import Ma2026Config, q_grid


@dataclass(frozen=True)
class Ma2026KalmanResult:
    phase_delta_rad: np.ndarray
    phase_rate_radps: np.ndarray
    corrected_phase_rad: np.ndarray
    displacement_m: np.ndarray
    process_noise_q: float
    measurement_noise_r: float


def run_ma2026_los_kalman(
    wrapped_phase_rad,
    acceleration_mps2,
    beta,
    phase1_config,
    ma_config: Ma2026Config = Ma2026Config(),
    q_value=1.0,
):
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    accel = np.asarray(acceleration_mps2, dtype=float)
    n_samples = wrapped.size
    phase_delta = np.zeros(n_samples, dtype=float)
    phase_rate = np.zeros(n_samples, dtype=float)
    corrected_delta = np.full(n_samples, np.nan, dtype=float)
    if n_samples == 0:
        return Ma2026KalmanResult(
            phase_delta,
            phase_rate,
            corrected_delta,
            phase_delta.copy(),
            float(q_value),
            float(ma_config.measurement_noise_r),
        )

    finite = np.flatnonzero(np.isfinite(wrapped))
    phase_ref = float(wrapped[int(finite[0])]) if finite.size else 0.0
    wrapped_delta = wrap_to_pi(wrapped - phase_ref)
    dt = 1.0 / float(phase1_config.sample_rate_hz)
    a_mat = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b_vec = np.array([0.5 * dt * dt, dt], dtype=float)
    q0 = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q_mat = float(q_value) * q0
    h = np.array([[1.0, 0.0]], dtype=float)
    r = float(ma_config.measurement_noise_r) / dt
    x = np.zeros(2, dtype=float)
    p = np.zeros((2, 2), dtype=float)

    for sample_idx in range(n_samples):
        accel_idx = max(sample_idx - 1, 0)
        accel_value = float(accel[accel_idx]) if accel_idx < accel.size and np.isfinite(accel[accel_idx]) else 0.0
        phase_accel = 4.0 * np.pi * accel_value / (float(beta) * phase1_config.wavelength_m())
        if sample_idx > 0:
            x_pred = a_mat @ x + b_vec * phase_accel
            p_pred = a_mat @ p @ a_mat.T + q_mat
        else:
            x_pred = x
            p_pred = p
        if np.isfinite(wrapped_delta[sample_idx]):
            z_corr = float(prediction_correct_wrapped_phase(wrapped_delta[sample_idx], x_pred[0]))
            corrected_delta[sample_idx] = z_corr
            innovation = z_corr - float((h @ x_pred)[0])
            s_value = float((h @ p_pred @ h.T)[0, 0] + r)
            k_gain = (p_pred @ h.T / s_value).reshape(2)
            x = x_pred + k_gain * innovation
            p = (np.eye(2) - k_gain[:, None] @ h) @ p_pred
        else:
            x = x_pred
            p = p_pred
        phase_delta[sample_idx] = x[0]
        phase_rate[sample_idx] = x[1]

    displacement = float(beta) * phase1_config.wavelength_m() * phase_delta / (4.0 * np.pi)
    corrected_abs = corrected_delta + phase_ref
    return Ma2026KalmanResult(
        phase_delta_rad=phase_delta,
        phase_rate_radps=phase_rate,
        corrected_phase_rad=corrected_abs,
        displacement_m=displacement,
        process_noise_q=float(q_value),
        measurement_noise_r=r,
    )


def select_q_by_energy(wrapped_phase_rad, acceleration_mps2, beta, phase1_config, ma_config: Ma2026Config = Ma2026Config()):
    candidates = q_grid(ma_config)
    energies = np.full(candidates.shape, np.inf, dtype=float)
    results = []
    for idx, q_value in enumerate(candidates):
        result = run_ma2026_los_kalman(
            wrapped_phase_rad,
            acceleration_mps2,
            beta,
            phase1_config,
            ma_config,
            q_value=float(q_value),
        )
        corrected = result.corrected_phase_rad
        valid = np.isfinite(corrected)
        if np.count_nonzero(valid):
            energies[idx] = float(np.mean(corrected[valid] ** 2))
        results.append(result)
    selected_idx = _select_energy_minimizer(candidates, energies, ma_config)
    return float(candidates[selected_idx]), candidates, energies, results[selected_idx]


def _select_energy_minimizer(candidates, energies, ma_config: Ma2026Config):
    del candidates, ma_config
    finite = np.isfinite(energies)
    if not np.any(finite):
        return 0
    return int(np.nanargmin(energies))
