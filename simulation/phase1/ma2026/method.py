import numpy as np

from ..algorithm import MethodResult
from .alpha import calibrate_alpha_linear_fit
from .calibration import calibrate_best_target
from .convergence import compute_ma2026_convergence_time
from .config import Ma2026Config
from .kalman import select_q_by_energy


def estimate_ma2026_target(
    wrapped_phase_rad,
    acceleration_mps2,
    phase1_config,
    ma_config: Ma2026Config = Ma2026Config(),
    initial_alpha=1.0,
):
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    accel_values = np.asarray(acceleration_mps2, dtype=float)
    n_samples = wrapped.size
    if n_samples == 0:
        return _empty_target_result("ma2026_target", 0)

    n_cal = min(n_samples, int(ma_config.calibration_max_samples))
    cal_wrapped = wrapped[:n_cal]
    cal_accel = accel_values[:n_cal]
    _, _, _, initial_kalman = select_q_by_energy(
        cal_wrapped,
        cal_accel,
        float(initial_alpha),
        phase1_config,
        ma_config,
    )
    alpha_calibration = calibrate_alpha_linear_fit(
        corrected_phase_rad=initial_kalman.corrected_phase_rad,
        acceleration_mps2=cal_accel,
        sample_rate_hz=phase1_config.sample_rate_hz,
        wavelength_m=phase1_config.wavelength_m(),
        band_hz=(ma_config.alpha_band_low_hz, ma_config.alpha_band_high_hz),
        highpass_cutoff_hz=ma_config.alpha_highpass_cutoff_hz,
    )
    selected_alpha = _finite_or_default(alpha_calibration.alpha, float(initial_alpha))
    selected_q, q_candidates, q_energy, kalman = select_q_by_energy(
        wrapped,
        accel_values,
        selected_alpha,
        phase1_config,
        ma_config,
    )
    convergence = compute_ma2026_convergence_time(
        sample_rate_hz=phase1_config.sample_rate_hz,
        wavelength_m=phase1_config.wavelength_m(),
        alpha=selected_alpha,
        q_value=selected_q,
        measurement_noise_r=ma_config.measurement_noise_r,
    )
    theta = 4.0 * np.pi * kalman.displacement_m / phase1_config.wavelength_m()
    dt = 1.0 / float(phase1_config.sample_rate_hz)
    theta_dot = np.gradient(np.nan_to_num(theta, nan=0.0), dt)
    return MethodResult(
        method_name="ma2026_target",
        q_hat_m=kalman.displacement_m,
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=kalman.corrected_phase_rad[None, :],
        kappa_hat=np.asarray([1.0 / selected_alpha], dtype=float),
        r_history=np.full((1, n_samples), kalman.measurement_noise_r, dtype=float),
        innovation_rad=np.full((1, n_samples), np.nan, dtype=float),
        extra={
            "selected_alpha": float(selected_alpha),
            "selected_beta": float(selected_alpha),
            "initial_alpha": float(initial_alpha),
            "alpha_calibration": _alpha_calibration_extra(alpha_calibration),
            "q_grid": q_candidates,
            "q_energy": q_energy,
            "selected_q": float(selected_q),
            "measurement_noise_r": float(ma_config.measurement_noise_r),
            "convergence_steps": int(convergence.convergence_steps),
            "convergence_time_s": float(convergence.convergence_time_s),
            "source": "Ma2026 target-specific acceleration-aided Kalman",
        },
    )


def estimate_ma2026_reproduction(rangebin_input, accel, phase1_config, ma_config: Ma2026Config = Ma2026Config()):
    n_targets, n_samples = rangebin_input.wrapped_phase_rad.shape
    corrected = np.full((n_targets, n_samples), np.nan, dtype=float)
    r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovation = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_hat = np.full(n_targets, np.nan, dtype=float)
    offline_calibration = calibrate_best_target(rangebin_input, accel, phase1_config, ma_config)
    selected = int(offline_calibration.selected_target_index)
    selected_beta = float(offline_calibration.selected_beta)
    if not np.isfinite(selected_beta) or selected < 0 or selected >= n_targets:
        selected = -1

    if selected < 0:
        theta = np.full(n_samples, np.nan, dtype=float)
        theta_dot = np.full(n_samples, np.nan, dtype=float)
        q_hat = np.full(n_samples, np.nan, dtype=float)
        selected_indices = np.empty(0, dtype=int)
        q_candidates = np.empty(0, dtype=float)
        q_energy = np.empty(0, dtype=float)
        selected_q = float("nan")
        selected_alpha = float("nan")
        alpha_extra = {}
        convergence_steps = 0
        convergence_time = float("nan")
        selected_range_bin = -1
    else:
        target_wrapped = np.asarray(rangebin_input.wrapped_phase_rad[selected], dtype=float).copy()
        target_available = np.asarray(rangebin_input.available_mask[selected], dtype=bool)
        target_wrapped[~target_available] = np.nan
        selected_q, q_candidates, q_energy, kalman = select_q_by_energy(
            target_wrapped,
            accel.measured_mps2,
            selected_beta,
            phase1_config,
            ma_config,
        )
        convergence = compute_ma2026_convergence_time(
            sample_rate_hz=phase1_config.sample_rate_hz,
            wavelength_m=phase1_config.wavelength_m(),
            alpha=selected_beta,
            q_value=selected_q,
            measurement_noise_r=ma_config.measurement_noise_r,
        )
        corrected[selected] = kalman.corrected_phase_rad
        r_history[selected] = kalman.measurement_noise_r
        q_hat = kalman.displacement_m
        theta = 4.0 * np.pi * q_hat / phase1_config.wavelength_m()
        dt = 1.0 / float(phase1_config.sample_rate_hz)
        theta_dot = np.gradient(np.nan_to_num(theta, nan=0.0), dt)
        selected_alpha = selected_beta
        kappa_hat[selected] = 1.0 / selected_beta
        selected_indices = np.asarray([selected], dtype=int)
        alpha_extra = _offline_alpha_extra(offline_calibration, n_samples)
        convergence_steps = int(convergence.convergence_steps)
        convergence_time = float(convergence.convergence_time_s)
        selected_range_bin = int(rangebin_input.range_bins[selected])

    return MethodResult(
        method_name="ma2026_reproduction",
        q_hat_m=q_hat,
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=corrected,
        kappa_hat=kappa_hat,
        r_history=r_history,
        innovation_rad=innovation,
        extra={
            "selected_indices": selected_indices,
            "selected_target_count": int(selected_indices.size),
            "selected_target_index": int(selected),
            "selected_range_bin": int(selected_range_bin),
            "selected_alpha": float(selected_alpha),
            "selected_beta": float(selected_alpha),
            "alpha_calibration": alpha_extra,
            "calibration_stage": "offline_target_beta_fit",
            "offline_calibration": _offline_calibration_extra(offline_calibration),
            "highpass_cutoff_hz": float(offline_calibration.highpass_cutoff_hz),
            "conversion_band_hz": tuple(float(item) for item in offline_calibration.conversion_band_hz),
            "q_grid": q_candidates,
            "q_energy": q_energy,
            "selected_q": float(selected_q),
            "measurement_noise_r": float(ma_config.measurement_noise_r),
            "convergence_steps": int(convergence_steps),
            "convergence_time_s": float(convergence_time),
            "source": "Ma 2026 staged reproduction with offline direction-factor calibration",
            "adapter_boundary": "range-bin candidate enumeration is a simulation adapter; offline target/beta calibration precedes the target-specific Kalman stage",
        },
    )


def _empty_target_result(method_name, n_samples):
    return MethodResult(
        method_name=method_name,
        q_hat_m=np.full(n_samples, np.nan, dtype=float),
        theta_hat_rad=np.full(n_samples, np.nan, dtype=float),
        theta_dot_hat_radps=np.full(n_samples, np.nan, dtype=float),
        corrected_phase_rad=np.full((1, n_samples), np.nan, dtype=float),
        kappa_hat=np.full(1, np.nan, dtype=float),
        r_history=np.full((1, n_samples), np.nan, dtype=float),
        innovation_rad=np.full((1, n_samples), np.nan, dtype=float),
        extra={
            "selected_alpha": float("nan"),
            "selected_beta": float("nan"),
            "selected_q": float("nan"),
            "source": "Ma2026 target-specific acceleration-aided Kalman",
        },
    )


def _finite_or_default(value, default):
    return float(value) if np.isfinite(value) and abs(float(value)) > 1e-12 else float(default)


def _alpha_calibration_extra(result):
    return {
        "alpha": float(result.alpha),
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r2": float(result.r2),
        "band_hz": tuple(float(item) for item in result.band_hz),
        "sample_count": int(result.sample_count),
    }


def _offline_alpha_extra(result, n_samples):
    return {
        "alpha": float(result.selected_beta),
        "slope": float(result.selected_beta),
        "intercept": 0.0,
        "r2": float("nan"),
        "band_hz": tuple(float(item) for item in result.conversion_band_hz),
        "sample_count": int(n_samples),
        "source": "offline_target_beta_fit",
        "fit_rmse_mm": float(np.nanmin(result.rmse_grid_mm))
        if result.rmse_grid_mm.size and np.any(np.isfinite(result.rmse_grid_mm))
        else float("nan"),
    }


def _offline_calibration_extra(result):
    return {
        "selected_target_index": int(result.selected_target_index),
        "selected_range_bin": int(result.selected_range_bin),
        "selected_beta": float(result.selected_beta),
        "beta_values": result.beta_values,
        "rmse_grid_mm": result.rmse_grid_mm,
        "highpass_cutoff_hz": float(result.highpass_cutoff_hz),
        "conversion_band_hz": tuple(float(item) for item in result.conversion_band_hz),
        "min_rmse_mm": float(np.nanmin(result.rmse_grid_mm))
        if result.rmse_grid_mm.size and np.any(np.isfinite(result.rmse_grid_mm))
        else float("nan"),
    }
