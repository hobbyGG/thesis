import numpy as np

from ..algorithm import MethodResult
from .alpha import calibrate_alpha_linear_fit
from .convergence import compute_ma2026_convergence_time
from .config import Ma2026Config
from .kalman import select_q_by_energy


def estimate_ma2026_target(
    wrapped_phase_rad,
    acceleration_mps2,
    phase1_config,
    ma_config: Ma2026Config = Ma2026Config(),
    fallback_alpha=1.0,
    calibration_los_corrected_phase_rad=None,
):
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    accel_values = np.asarray(acceleration_mps2, dtype=float)
    n_samples = wrapped.size
    if n_samples == 0:
        return _empty_target_result("ma2026_target", 0)

    n_cal = min(n_samples, int(ma_config.calibration_max_samples))
    cal_wrapped = wrapped[:n_cal]
    cal_accel = accel_values[:n_cal]
    calibration_phase, calibration_phase_source = _calibration_los_phase(
        cal_wrapped,
        calibration_los_corrected_phase_rad,
        n_cal,
    )

    alpha_calibration = calibrate_alpha_linear_fit(
        los_corrected_phase_rad=calibration_phase,
        acceleration_mps2=cal_accel,
        sample_rate_hz=phase1_config.sample_rate_hz,
        wavelength_m=phase1_config.wavelength_m(),
        band_hz=(ma_config.alpha_band_low_hz, ma_config.alpha_band_high_hz),
        highpass_cutoff_hz=ma_config.alpha_highpass_cutoff_hz,
    )
    selected_alpha = _finite_or_default(alpha_calibration.alpha, float(fallback_alpha))
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
        los_corrected_phase_rad=kalman.los_corrected_phase_rad[None, :],
        beta_hat=np.asarray([selected_alpha], dtype=float),
        r_theta_history=np.full((1, n_samples), kalman.measurement_noise_r, dtype=float),
        innovation_rad=np.full((1, n_samples), np.nan, dtype=float),
        extra={
            "selected_alpha": float(selected_alpha),
            "selected_beta": float(selected_alpha),
            "alpha_calibration": _alpha_calibration_extra(alpha_calibration, calibration_phase_source),
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
    los_corrected = np.full((n_targets, n_samples), np.nan, dtype=float)
    r_theta_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovation = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_hat = np.full(n_targets, np.nan, dtype=float)
    selected = 0 if n_targets > 0 else -1

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
        calibration_phase = None
        calibration_all = getattr(rangebin_input, "calibration_los_corrected_phase_rad", None)
        if calibration_all is not None:
            calibration_phase = np.asarray(calibration_all[selected], dtype=float).copy()
            calibration_phase[~target_available] = np.nan
        target_result = estimate_ma2026_target(
            target_wrapped,
            accel.measured_mps2,
            phase1_config,
            ma_config,
            calibration_los_corrected_phase_rad=calibration_phase,
        )
        los_corrected[selected] = target_result.los_corrected_phase_rad[0]
        r_theta_history[selected] = target_result.r_theta_history[0]
        q_hat = target_result.q_hat_m
        theta = target_result.theta_hat_rad
        theta_dot = target_result.theta_dot_hat_radps
        selected_alpha = float(target_result.extra["selected_alpha"])
        beta_hat[selected] = selected_alpha
        selected_indices = np.asarray([selected], dtype=int)
        alpha_extra = target_result.extra["alpha_calibration"]
        q_candidates = target_result.extra["q_grid"]
        q_energy = target_result.extra["q_energy"]
        selected_q = float(target_result.extra["selected_q"])
        convergence_steps = int(target_result.extra["convergence_steps"])
        convergence_time = float(target_result.extra["convergence_time_s"])
        selected_range_bin = int(rangebin_input.range_bins[selected])

    return MethodResult(
        method_name="ma2026_reproduction",
        q_hat_m=q_hat,
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        los_corrected_phase_rad=los_corrected,
        beta_hat=beta_hat,
        r_theta_history=r_theta_history,
        innovation_rad=innovation,
        extra={
            "selected_indices": selected_indices,
            "selected_target_count": int(selected_indices.size),
            "selected_target_index": int(selected),
            "selected_range_bin": int(selected_range_bin),
            "selected_alpha": float(selected_alpha),
            "selected_beta": float(selected_alpha),
            "alpha_calibration": alpha_extra,
            "target_adapter": "range_fft_distance_spectrum_first_candidate",
            "calibration_stage": "ma2026_alpha_linear_fit",
            "highpass_cutoff_hz": float(ma_config.alpha_highpass_cutoff_hz),
            "q_grid": q_candidates,
            "q_energy": q_energy,
            "selected_q": float(selected_q),
            "measurement_noise_r": float(ma_config.measurement_noise_r),
            "convergence_steps": int(convergence_steps),
            "convergence_time_s": float(convergence_time),
            "source": "Ma 2026 target-specific reproduction with Range FFT distance-spectrum adapter and alpha linear fit",
            "adapter_boundary": "Range FFT range-bin candidate enumeration is a simulation adapter; no Range-Angle, angle-bin, or beta-grid target selection is used before the Ma 2026 target-specific Kalman stages",
        },
    )


def _empty_target_result(method_name, n_samples):
    return MethodResult(
        method_name=method_name,
        q_hat_m=np.full(n_samples, np.nan, dtype=float),
        theta_hat_rad=np.full(n_samples, np.nan, dtype=float),
        theta_dot_hat_radps=np.full(n_samples, np.nan, dtype=float),
        los_corrected_phase_rad=np.full((1, n_samples), np.nan, dtype=float),
        beta_hat=np.full(1, np.nan, dtype=float),
        r_theta_history=np.full((1, n_samples), np.nan, dtype=float),
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


def _alpha_calibration_extra(result, phase_source):
    return {
        "alpha": float(result.alpha),
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r2": float(result.r2),
        "band_hz": tuple(float(item) for item in result.band_hz),
        "sample_count": int(result.sample_count),
        "source": "ma2026_bandpass_phase_linear_fit",
        "phase_source": str(phase_source),
    }


def _calibration_los_phase(cal_wrapped, calibration_los_corrected_phase_rad, n_cal):
    if calibration_los_corrected_phase_rad is not None:
        phase = np.asarray(calibration_los_corrected_phase_rad, dtype=float)[:n_cal].copy()
        if phase.shape != np.asarray(cal_wrapped, dtype=float).shape:
            raise ValueError("calibration_los_corrected_phase_rad and wrapped calibration phase must have matching shapes")
        return phase, "supplied_corrected_los_phase"
    return _unwrap_available_phase(cal_wrapped), "unwrap_wrapped_los_phase"


def _unwrap_available_phase(wrapped_phase_rad):
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    result = np.full(wrapped.shape, np.nan, dtype=float)
    valid = np.isfinite(wrapped)
    if np.count_nonzero(valid):
        result[valid] = np.unwrap(wrapped[valid])
    return result
