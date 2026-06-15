from dataclasses import dataclass, field

import numpy as np

from .phase_utils import itoh_unwrap, prediction_correct_wrapped_phase


@dataclass(frozen=True)
class MethodResult:
    method_name: str
    q_hat_m: np.ndarray
    theta_hat_rad: np.ndarray
    theta_dot_hat_radps: np.ndarray
    corrected_phase_rad: np.ndarray
    kappa_hat: np.ndarray
    r_history: np.ndarray
    innovation_rad: np.ndarray
    extra: dict = field(default_factory=dict)


def _phase_to_displacement(theta_rad, config):
    return np.asarray(theta_rad, dtype=float) * config.wavelength_m() / (4.0 * np.pi)


def estimate_oracle(truth, radar, config):
    theta = np.asarray(radar.true_main_phase_rad, dtype=float)
    dt = 1.0 / config.sample_rate_hz
    theta_dot = np.gradient(theta, dt)
    empty_targets = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    return MethodResult(
        method_name="oracle",
        q_hat_m=truth.q_m.copy(),
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=radar.true_los_phase_rad.copy(),
        kappa_hat=radar.kappa.copy(),
        r_history=empty_targets.copy(),
        innovation_rad=empty_targets.copy(),
        extra={},
    )


def estimate_itoh_ls(truth, radar, config, target_index=0):
    idx = int(target_index)
    wrapped = radar.wrapped_phase_rad[idx]
    valid = np.isfinite(wrapped)
    corrected = np.full_like(wrapped, np.nan, dtype=float)
    corrected[valid] = itoh_unwrap(wrapped[valid])
    if np.any(valid):
        corrected[valid] -= corrected[valid][0] - radar.true_los_phase_rad[idx, valid][0]
    kappa = float(radar.kappa[idx])
    theta = (corrected - radar.true_los_phase_rad[idx, 0] + kappa * radar.true_main_phase_rad[0]) / max(
        abs(kappa), 1e-12
    )
    dt = 1.0 / config.sample_rate_hz
    theta_dot = np.gradient(np.nan_to_num(theta, nan=0.0), dt)
    corrected_all = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    corrected_all[idx] = corrected
    return MethodResult(
        method_name="itoh_ls",
        q_hat_m=_phase_to_displacement(theta, config),
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=corrected_all,
        kappa_hat=np.full(radar.kappa.shape, np.nan, dtype=float),
        r_history=np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float),
        innovation_rad=np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float),
        extra={"target_index": idx},
    )


def _state_matrices(config):
    dt = 1.0 / config.sample_rate_hz
    a = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b = np.array([0.5 * dt * dt, dt], dtype=float)
    q0 = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q = float(config.process_noise_intensity) * q0
    return a, b, q


def _initial_state(truth, radar, config):
    theta0 = float(radar.true_main_phase_rad[0])
    theta_dot0 = float((4.0 * np.pi / config.wavelength_m()) * truth.v_mps[0])
    return np.array([theta0, theta_dot0], dtype=float)


def _phase_accel_input(accel_mps2, config):
    return (4.0 * np.pi / config.wavelength_m()) * float(accel_mps2)


def _safe_inverse(matrix):
    return np.linalg.pinv(matrix)


def estimate_multitarget_fixed(truth, radar, config):
    return _run_structural_phase_kalman(
        method_name="multitarget_fixed",
        truth=truth,
        radar=radar,
        config=config,
        initial_kappa=radar.kappa.copy(),
        update_kappa=False,
        adaptive_r=False,
    )


def estimate_proposed(truth, radar, config):
    return _run_structural_phase_kalman(
        method_name="proposed",
        truth=truth,
        radar=radar,
        config=config,
        initial_kappa=radar.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
    )


def estimate_single_target_ma_style(truth, radar, config, target_index=0):
    idx = int(target_index)
    single_radar = _single_target_view(radar, idx)
    single_result = _run_structural_phase_kalman(
        method_name="single_target_ma_style",
        truth=truth,
        radar=single_radar,
        config=config,
        initial_kappa=np.array([radar.kappa[idx]], dtype=float),
        update_kappa=False,
        adaptive_r=True,
    )
    corrected = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    innovation = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    r_history = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    corrected[idx] = single_result.corrected_phase_rad[0]
    innovation[idx] = single_result.innovation_rad[0]
    r_history[idx] = single_result.r_history[0]
    return MethodResult(
        method_name="single_target_ma_style",
        q_hat_m=single_result.q_hat_m,
        theta_hat_rad=single_result.theta_hat_rad,
        theta_dot_hat_radps=single_result.theta_dot_hat_radps,
        corrected_phase_rad=corrected,
        kappa_hat=np.full(radar.kappa.shape, np.nan, dtype=float),
        r_history=r_history,
        innovation_rad=innovation,
        extra={"target_index": idx},
    )


def _single_target_view(radar, idx):
    from dataclasses import replace

    target_slice = slice(idx, idx + 1)
    return replace(
        radar,
        kappa=radar.kappa[target_slice],
        measured_kappa=radar.measured_kappa[target_slice],
        target_angles_deg=radar.target_angles_deg[target_slice],
        snr_db=radar.snr_db[target_slice],
        true_los_phase_rad=radar.true_los_phase_rad[target_slice],
        iq=radar.iq[target_slice],
        wrapped_phase_rad=radar.wrapped_phase_rad[target_slice],
        available_mask=radar.available_mask[target_slice],
    )


def _run_structural_phase_kalman(method_name, truth, radar, config, initial_kappa, update_kappa, adaptive_r):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    a_mat, b_vec, q_mat = _state_matrices(config)
    x = _initial_state(truth, radar, config)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    kappa = np.asarray(initial_kappa, dtype=float).copy()
    kappa = np.clip(kappa, -config.kappa_max_abs, config.kappa_max_abs)
    small = np.abs(kappa) < config.kappa_min_abs
    kappa[small] = np.sign(kappa[small] + 1e-12) * config.kappa_min_abs

    theta_hat = np.zeros(n_samples, dtype=float)
    theta_dot_hat = np.zeros(n_samples, dtype=float)
    corrected = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovations = np.full((n_targets, n_samples), np.nan, dtype=float)
    r_values = np.full(n_targets, float(config.initial_measurement_variance), dtype=float)
    r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_history = np.full((n_targets, n_samples), np.nan, dtype=float)

    target_bias = radar.true_los_phase_rad[:, 0] - radar.kappa * radar.true_main_phase_rad[0]
    warmup_index = int(round(config.kappa_update_start_s * config.sample_rate_hz))

    for sample_idx in range(n_samples):
        accel_idx = max(sample_idx - 1, 0)
        u = _phase_accel_input(truth.a_mps2[accel_idx], config)
        if sample_idx > 0:
            x_pred = a_mat @ x + b_vec * u
            p_pred = a_mat @ p @ a_mat.T + q_mat
        else:
            x_pred = x
            p_pred = p

        available = np.isfinite(radar.wrapped_phase_rad[:, sample_idx])
        active_indices = np.flatnonzero(available)
        if active_indices.size:
            h_rows = []
            z_rows = []
            bias_rows = []
            r_rows = []
            for target_idx in active_indices:
                prediction = kappa[target_idx] * x_pred[0] + target_bias[target_idx]
                z_corr = prediction_correct_wrapped_phase(radar.wrapped_phase_rad[target_idx, sample_idx], prediction)
                corrected[target_idx, sample_idx] = z_corr
                h_rows.append([kappa[target_idx], 0.0])
                z_rows.append(z_corr)
                bias_rows.append(target_bias[target_idx])
                r_rows.append(r_values[target_idx])

            h = np.asarray(h_rows, dtype=float)
            z = np.asarray(z_rows, dtype=float)
            bias_vec_obs = np.asarray(bias_rows, dtype=float)
            r_mat = np.diag(np.asarray(r_rows, dtype=float))
            innovation = z - (h @ x_pred + bias_vec_obs)
            s_mat = h @ p_pred @ h.T + r_mat
            k_gain = p_pred @ h.T @ _safe_inverse(s_mat)
            x = x_pred + k_gain @ innovation
            p = (np.eye(2) - k_gain @ h) @ p_pred

            for local_idx, target_idx in enumerate(active_indices):
                innovations[target_idx, sample_idx] = innovation[local_idx]
                if adaptive_r:
                    h_i = h[local_idx : local_idx + 1]
                    post_var = float((h_i @ p @ h_i.T)[0, 0])
                    instant_r = float(innovation[local_idx] ** 2 + post_var)
                    blended = (
                        config.adaptive_r_forgetting * r_values[target_idx]
                        + (1.0 - config.adaptive_r_forgetting) * instant_r
                    )
                    r_values[target_idx] = float(
                        np.clip(blended, config.min_measurement_variance, config.max_measurement_variance)
                    )
        else:
            x = x_pred
            p = p_pred

        theta_hat[sample_idx] = x[0]
        theta_dot_hat[sample_idx] = x[1]
        r_history[:, sample_idx] = r_values

        if update_kappa and sample_idx >= warmup_index:
            start = max(0, sample_idx - int(config.kappa_window_samples) + 1)
            theta_window = theta_hat[start : sample_idx + 1]
            denom = float(np.sum(theta_window**2))
            if denom > 1e-12:
                for target_idx in range(n_targets):
                    z_window = corrected[target_idx, start : sample_idx + 1]
                    valid = np.isfinite(z_window)
                    if np.count_nonzero(valid) >= 3:
                        numerator = float(np.sum(theta_window[valid] * (z_window[valid] - target_bias[target_idx])))
                        new_kappa = numerator / denom
                        if abs(new_kappa) >= config.kappa_min_abs:
                            kappa[target_idx] = float(np.clip(new_kappa, -config.kappa_max_abs, config.kappa_max_abs))
        kappa_history[:, sample_idx] = kappa

    return MethodResult(
        method_name=method_name,
        q_hat_m=_phase_to_displacement(theta_hat, config),
        theta_hat_rad=theta_hat,
        theta_dot_hat_radps=theta_dot_hat,
        corrected_phase_rad=corrected,
        kappa_hat=kappa.copy(),
        r_history=r_history,
        innovation_rad=innovations,
        extra={"kappa_history": kappa_history},
    )
