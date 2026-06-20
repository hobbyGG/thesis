from dataclasses import replace

import numpy as np

from .algorithm import (
    MethodResult,
    _circular_mean,
    _phase_to_displacement,
    cold_start_reference_mean,
    cold_start_sample_count,
    run_structural_phase_kalman,
)
from .phase_utils import itoh_unwrap, prediction_correct_wrapped_phase


def _relative_truth_phase(truth, config):
    q_ref = cold_start_reference_mean(truth.q_m, config)
    return 4.0 * np.pi * (truth.q_m - q_ref) / config.wavelength_m()


def estimate_oracle(truth, radar, config):
    theta = _relative_truth_phase(truth, config)
    dt = 1.0 / config.sample_rate_hz
    theta_dot = np.gradient(theta, dt)
    empty_targets = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    return MethodResult(
        method_name="oracle",
        q_hat_m=truth.q_m.copy() - cold_start_reference_mean(truth.q_m, config),
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
        target_bias = cold_start_reference_mean(corrected, config)
        corrected[valid] -= corrected[valid][0] - prediction_correct_wrapped_phase(wrapped[valid][0], target_bias)
    target_phase_ref = cold_start_reference_mean(corrected, config)
    kappa = float(radar.kappa[idx])
    theta = (corrected - target_phase_ref) / max(abs(kappa), 1e-12)
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


def estimate_multitarget_true_kappa_fixed_r(truth, radar, accel, config):
    return run_structural_phase_kalman(
        method_name="multitarget_true_kappa_fixed_r",
        radar=radar,
        accel=accel,
        config=config,
        initial_kappa=radar.kappa.copy(),
        update_kappa=False,
        adaptive_r=False,
    )


def estimate_multitarget_aoa_fixed_kappa(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="multitarget_aoa_fixed_kappa",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=False,
        adaptive_r=False,
    )


def estimate_selected_aoa_fixed_kappa(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="selected_aoa_fixed_kappa",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=False,
        adaptive_r=False,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
    )


def estimate_range_bin_only_mixed_phase(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="range_bin_only_mixed_phase",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=False,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
    )


def estimate_ma_style_iterative_beta_range_bin(radar_input, accel, config):
    beta_hat, beta_history, beta_bias, beta_residual = _fit_iterative_beta_from_mixed_phase(
        radar_input,
        accel,
        config,
    )
    result = run_structural_phase_kalman(
        method_name="ma_style_iterative_beta_range_bin",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=np.array([beta_hat], dtype=float),
        update_kappa=False,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
    )
    result.extra.update(
        {
            "beta_hat": float(beta_hat),
            "beta_history": np.asarray(beta_history, dtype=float),
            "beta_bias_rad": float(beta_bias),
            "beta_fit_residual_rad": float(beta_residual),
        }
    )
    return result


def _fit_iterative_beta_from_mixed_phase(radar_input, accel, config, max_iterations=8):
    wrapped = np.asarray(radar_input.wrapped_phase_rad[0], dtype=float)
    available = np.isfinite(wrapped)
    if hasattr(radar_input, "available_mask"):
        available &= np.asarray(radar_input.available_mask[0], dtype=bool)

    theta_ref = _acceleration_reference_phase(accel, config, wrapped.size)
    valid = available & np.isfinite(theta_ref)
    beta = float(np.asarray(radar_input.measured_kappa, dtype=float)[0])
    beta = float(np.clip(abs(beta), config.kappa_min_abs, config.kappa_max_abs))
    bias = _circular_mean(wrapped[: cold_start_sample_count(config, wrapped.size)])
    history = [beta]
    residual = float("nan")
    if np.count_nonzero(valid) < 4 or float(np.nanstd(theta_ref[valid])) <= 1e-12:
        return beta, history + [beta], bias, residual

    for _ in range(int(max_iterations)):
        prediction = beta * theta_ref + bias
        corrected = np.full_like(wrapped, np.nan, dtype=float)
        corrected[valid] = wrapped[valid] + 2.0 * np.pi * np.round(
            (prediction[valid] - wrapped[valid]) / (2.0 * np.pi)
        )
        x = theta_ref[valid]
        y = corrected[valid]
        design = np.column_stack([x, np.ones_like(x)])
        fitted, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        new_beta = float(np.clip(abs(fitted[0]), config.kappa_min_abs, config.kappa_max_abs))
        new_bias = float(fitted[1])
        residual = float(np.sqrt(np.mean((y - (new_beta * x + new_bias)) ** 2)))
        history.append(new_beta)
        beta_delta = abs(new_beta - beta)
        bias_delta = abs(new_bias - bias)
        beta = new_beta
        bias = new_bias
        if len(history) >= 3 and beta_delta < 1e-5 and bias_delta < 1e-4:
            break
    if len(history) < 2:
        history.append(beta)
    return beta, history, bias, residual


def _acceleration_reference_phase(accel, config, n_samples):
    measured = np.asarray(accel.measured_mps2, dtype=float)
    n_samples = int(n_samples)
    if measured.size < n_samples:
        padded = np.zeros(n_samples, dtype=float)
        padded[: measured.size] = measured
        measured = padded
    elif measured.size > n_samples:
        measured = measured[:n_samples]
    measured = measured - float(np.nanmean(measured))
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / float(config.sample_rate_hz))
    spectrum = np.fft.rfft(measured)
    displacement_spectrum = np.zeros_like(spectrum, dtype=complex)
    high = min(120.0, 0.45 * float(config.sample_rate_hz))
    band = (freqs >= 5.0) & (freqs <= high)
    omega = 2.0 * np.pi * freqs[band]
    displacement_spectrum[band] = -spectrum[band] / np.maximum(omega**2, 1e-12)
    displacement = np.fft.irfft(displacement_spectrum, n=n_samples)
    displacement -= cold_start_reference_mean(displacement, config)
    return 4.0 * np.pi * displacement / config.wavelength_m()


def estimate_multitarget_fixed(truth, radar, config, accel=None):
    if accel is None:
        from .accelerometer import simulate_accelerometer

        accel = simulate_accelerometer(truth, config)
    return estimate_multitarget_true_kappa_fixed_r(truth, radar, accel, config)


def estimate_single_target_ma_style(truth, radar, accel, config, target_index=0):
    idx = int(target_index)
    single_radar = _single_target_view(radar, idx)
    single_result = run_structural_phase_kalman(
        method_name="single_target_ma_style",
        radar=single_radar,
        accel=accel,
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
