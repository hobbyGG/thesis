from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026ConvergenceResult:
    steady_state_gain: np.ndarray
    measurement_coefficients: np.ndarray
    acceleration_coefficients: np.ndarray
    convergence_steps: int
    convergence_time_s: float
    threshold: float


def compute_ma2026_convergence_time(
    sample_rate_hz,
    wavelength_m,
    alpha,
    q_value,
    measurement_noise_r=1.0,
    max_steps=2000,
    threshold_ratio=1e-3,
):
    dt = 1.0 / float(sample_rate_hz)
    a_mat = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b_vec = np.array([0.5 * dt * dt, dt], dtype=float)
    q0 = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q_mat = float(q_value) * q0
    h_mat = np.array([[1.0, 0.0]], dtype=float)
    r_value = float(measurement_noise_r) / dt

    steady_state_gain = _steady_state_kalman_gain(a_mat, q_mat, h_mat, r_value)
    correction_mat = np.eye(2) - steady_state_gain[:, None] @ h_mat
    closed_loop = correction_mat @ a_mat
    phase_accel_scale = 4.0 * np.pi / (float(alpha) * float(wavelength_m))

    n_steps = int(max_steps)
    measurement_coefficients = np.zeros((n_steps, 2), dtype=float)
    acceleration_coefficients = np.zeros((n_steps, 2), dtype=float)
    measurement_coeff = steady_state_gain.copy()
    acceleration_coeff = correction_mat @ b_vec * phase_accel_scale

    for idx in range(n_steps):
        measurement_coefficients[idx] = measurement_coeff
        acceleration_coefficients[idx] = acceleration_coeff
        measurement_coeff = closed_loop @ measurement_coeff
        acceleration_coeff = closed_loop @ acceleration_coeff

    convergence_steps = _first_converged_step(
        measurement_coefficients,
        acceleration_coefficients,
        float(threshold_ratio),
    )
    return Ma2026ConvergenceResult(
        steady_state_gain=steady_state_gain,
        measurement_coefficients=measurement_coefficients,
        acceleration_coefficients=acceleration_coefficients,
        convergence_steps=convergence_steps,
        convergence_time_s=float(convergence_steps) * dt,
        threshold=float(threshold_ratio),
    )


def _steady_state_kalman_gain(a_mat, q_mat, h_mat, r_value, max_iterations=100000, tolerance=1e-12):
    p_mat = np.zeros((2, 2), dtype=float)
    gain = np.zeros(2, dtype=float)
    identity = np.eye(2)
    for _ in range(max_iterations):
        p_pred = a_mat @ p_mat @ a_mat.T + q_mat
        s_value = float((h_mat @ p_pred @ h_mat.T)[0, 0] + r_value)
        next_gain = (p_pred @ h_mat.T / s_value).reshape(2)
        next_p = (identity - next_gain[:, None] @ h_mat) @ p_pred
        if np.linalg.norm(next_gain - gain) <= tolerance:
            return next_gain
        p_mat = next_p
        gain = next_gain
    return gain


def _first_converged_step(measurement_coefficients, acceleration_coefficients, threshold_ratio):
    measurement_initial = max(float(np.linalg.norm(measurement_coefficients[0])), np.finfo(float).tiny)
    acceleration_initial = max(float(np.linalg.norm(acceleration_coefficients[0])), np.finfo(float).tiny)
    for idx in range(1, measurement_coefficients.shape[0]):
        measurement_ratio = float(np.linalg.norm(measurement_coefficients[idx])) / measurement_initial
        acceleration_ratio = float(np.linalg.norm(acceleration_coefficients[idx])) / acceleration_initial
        if measurement_ratio <= threshold_ratio and acceleration_ratio <= threshold_ratio:
            return idx
    return int(measurement_coefficients.shape[0])
