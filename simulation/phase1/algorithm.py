from dataclasses import dataclass, field, replace

import numpy as np

from .phase_utils import itoh_unwrap, prediction_correct_wrapped_phase


@dataclass(frozen=True)
class MethodResult:
    method_name: str
    q_hat_m: np.ndarray
    theta_hat_rad: np.ndarray
    theta_dot_hat_radps: np.ndarray
    los_corrected_phase_rad: np.ndarray
    beta_hat: np.ndarray
    r_theta_history: np.ndarray
    innovation_rad: np.ndarray
    extra: dict = field(default_factory=dict)


def _phase_to_displacement(theta_rad, config):
    return np.asarray(theta_rad, dtype=float) * config.wavelength_m() / (4.0 * np.pi)


def cold_start_sample_count(config, n_samples):
    count = int(round(float(config.cold_start_duration_s) * float(config.sample_rate_hz)))
    return max(1, min(int(n_samples), count))


def cold_start_reference_mean(values, config):
    arr = np.asarray(values, dtype=float)
    count = cold_start_sample_count(config, arr.size)
    return float(np.nanmean(arr[:count]))


def _circular_mean(values):
    arr = np.asarray(values, dtype=float)
    valid = np.isfinite(arr)
    if not np.any(valid):
        return 0.0
    return float(np.angle(np.mean(np.exp(1j * arr[valid]))))


def _estimate_target_biases(radar, config):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    count = cold_start_sample_count(config, n_samples)
    biases = np.zeros(n_targets, dtype=float)
    for target_idx in range(n_targets):
        window = radar.wrapped_phase_rad[target_idx, :count]
        valid = np.isfinite(window)
        if np.count_nonzero(valid) >= 2:
            unwrapped = itoh_unwrap(window[valid])
            anchor = prediction_correct_wrapped_phase(window[valid][0], _circular_mean(window))
            biases[target_idx] = float(np.mean(unwrapped + (anchor - unwrapped[0])))
        else:
            biases[target_idx] = _circular_mean(window)
    return biases


def _state_matrices(config):
    dt = 1.0 / config.sample_rate_hz
    a = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b = np.array([0.5 * dt * dt, dt], dtype=float)
    q0 = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q = float(config.process_noise_intensity) * q0
    return a, b, q


def _initial_state_from_cold_start(radar, beta, target_bias, config, selected_indices=None):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    count = cold_start_sample_count(config, n_samples)
    theta0_estimates = []
    indices = range(n_targets) if selected_indices is None else np.asarray(selected_indices, dtype=int)
    for target_idx in indices:
        beta_i = float(beta[target_idx])
        if abs(beta_i) < config.beta_min_abs:
            continue
        wrapped = radar.wrapped_phase_rad[target_idx, :count]
        valid = np.isfinite(wrapped)
        if not np.any(valid):
            continue
        unwrapped = itoh_unwrap(wrapped[valid])
        aligned_first = prediction_correct_wrapped_phase(wrapped[valid][0], target_bias[target_idx])
        unwrapped = unwrapped + (aligned_first - unwrapped[0])
        theta_samples = beta_i * (unwrapped - target_bias[target_idx])
        theta0_estimates.append(float(theta_samples[0]))
    theta0 = float(np.median(theta0_estimates)) if theta0_estimates else 0.0
    return np.array([theta0, 0.0], dtype=float)


def _phase_accel_input(accel_mps2, config):
    return (4.0 * np.pi / config.wavelength_m()) * float(accel_mps2)


def _acceleration_fft_reference_phase(accel, config, n_samples):
    measured = np.asarray(accel.measured_mps2, dtype=float)
    n_samples = int(n_samples)
    if measured.size < n_samples:
        padded = np.zeros(n_samples, dtype=float)
        padded[: measured.size] = measured
        measured = padded
    elif measured.size > n_samples:
        measured = measured[:n_samples]
    if measured.size == 0:
        return np.zeros(n_samples, dtype=float)

    centered = measured - float(np.nanmean(measured))
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / float(config.sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    displacement_spectrum = np.zeros_like(spectrum, dtype=complex)
    low_hz = max(0.0, float(getattr(config, "beta_accel_reference_low_hz", 0.5)))
    high_hz = min(
        float(getattr(config, "beta_accel_reference_high_hz", 120.0)),
        0.45 * float(config.sample_rate_hz),
    )
    band = (freqs >= low_hz) & (freqs <= high_hz)
    omega = 2.0 * np.pi * freqs[band]
    displacement_spectrum[band] = -spectrum[band] / np.maximum(omega**2, 1.0e-18)
    displacement = np.fft.irfft(displacement_spectrum, n=n_samples)
    displacement -= cold_start_reference_mean(displacement, config)
    return 4.0 * np.pi * displacement / config.wavelength_m()


def _safe_inverse(matrix):
    return np.linalg.pinv(matrix)


def _clip_beta(beta, config):
    arr = np.asarray(beta, dtype=float).copy()
    arr = np.clip(arr, config.beta_min_abs, config.beta_max_abs)
    small = np.abs(arr) < config.beta_min_abs
    arr[small] = config.beta_min_abs
    return arr


def _fit_beta_via_projection(theta_values, los_values, beta_prior, prior_weight, config):
    theta = np.asarray(theta_values, dtype=float)
    los = np.asarray(los_values, dtype=float)
    valid = np.isfinite(theta) & np.isfinite(los)
    if np.count_nonzero(valid) < 3:
        return None

    theta_valid = theta[valid]
    los_valid = los[valid]
    theta_fit = theta_valid - float(np.mean(theta_valid))
    los_fit = los_valid - float(np.mean(los_valid))
    denom = float(np.dot(theta_fit, theta_fit))
    if denom <= 1.0e-12:
        return None

    projection_prior = 1.0 / max(abs(float(beta_prior)), config.beta_min_abs)
    numerator = float(np.dot(theta_fit, los_fit))
    if prior_weight > 0.0:
        projection = (numerator + prior_weight * projection_prior) / (denom + prior_weight)
    else:
        projection = numerator / denom

    projection_abs = abs(float(projection))
    if projection_abs <= 1.0e-12:
        return None

    beta = float(np.clip(1.0 / projection_abs, config.beta_min_abs, config.beta_max_abs))
    residual = los_fit - projection * theta_fit
    dof = max(int(np.count_nonzero(valid)) - 1, 1)
    residual_var = float(np.dot(residual, residual) / dof)
    projection_var = residual_var / max(denom, 1.0e-12)
    beta_var = projection_var / max(projection_abs**4, 1.0e-12)
    beta_var = float(
        np.clip(
            beta_var,
            config.beta_confidence_min_variance,
            config.beta_confidence_max_variance,
        )
    )
    return beta, beta_var


def _beta_update_diagnostics(theta_values, los_values, config):
    theta = np.asarray(theta_values, dtype=float)
    los = np.asarray(los_values, dtype=float)
    valid = np.isfinite(theta) & np.isfinite(los)
    count = int(np.count_nonzero(valid))
    diagnostics = {
        "valid_count": float(count),
        "los_energy": np.nan,
        "theta_energy": np.nan,
        "abs_corr": np.nan,
        "residual_ratio": np.nan,
    }
    if count < int(config.beta_identifiability_min_samples):
        return False, 0.0, diagnostics

    theta_fit = theta[valid] - float(np.mean(theta[valid]))
    los_fit = los[valid] - float(np.mean(los[valid]))
    los_energy = float(np.dot(los_fit, los_fit))
    theta_energy = float(np.dot(theta_fit, theta_fit))
    diagnostics["los_energy"] = los_energy
    diagnostics["theta_energy"] = theta_energy
    if (
        los_energy < float(config.beta_identifiability_min_los_energy)
        or theta_energy < float(config.beta_identifiability_min_theta_energy)
    ):
        return False, 0.0, diagnostics

    cross = float(np.dot(los_fit, theta_fit))
    abs_corr = abs(cross) / np.sqrt(max(los_energy * theta_energy, 1.0e-24))
    diagnostics["abs_corr"] = float(abs_corr)
    if abs_corr < float(config.beta_identifiability_min_abs_corr):
        return False, 0.0, diagnostics

    beta_ls = cross / max(los_energy, 1.0e-12)
    residual = theta_fit - beta_ls * los_fit
    residual_ratio = float(np.dot(residual, residual) / max(theta_energy, 1.0e-12))
    diagnostics["residual_ratio"] = residual_ratio
    if residual_ratio > float(config.beta_identifiability_max_residual_ratio):
        return False, 0.0, diagnostics

    residual_score = max(
        0.0,
        1.0 - residual_ratio / max(float(config.beta_identifiability_max_residual_ratio), 1.0e-12),
    )
    gain = float(config.beta_update_gain) * min(1.0, abs_corr) * residual_score
    return True, gain, diagnostics


def _initial_beta_from_radar(radar):
    return np.asarray(radar.measured_beta, dtype=float).copy()


def estimate_proposed(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="proposed",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_beta=_initial_beta_from_radar(radar_input),
        update_beta=True,
        adaptive_r=True,
    )


def estimate_proposed_full_pipeline(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_beta=_initial_beta_from_radar(radar_input),
        update_beta=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
    )


def calibrated_process_noise_intensity(config):
    value = getattr(config, "calibrated_process_noise_intensity", None)
    if value is None:
        value = getattr(config, "calibrated_q", 5.0e4)
    return float(value)


def estimate_proposed_full_pipeline_beta_confidence(radar_input, accel, config):
    selected = _select_calibrated_q_result(radar_input, accel, config)
    result = selected["result"]
    process_noise_intensity = float(selected["q"])
    extra = {
        **result.extra,
        "process_noise_intensity": process_noise_intensity,
        "calibrated_q": process_noise_intensity,
        "calibrated_q_candidates": selected["candidates"],
        "calibrated_q_metric": "innovation_energy",
        "calibrated_q_metric_values": selected["metric_values"],
        "calibrated_q_selection_index": int(selected["index"]),
    }
    return replace(
        result,
        method_name="proposed_full_pipeline_beta_confidence",
        extra=extra,
    )


def estimate_proposed_full_pipeline_calibrated(radar_input, accel, config):
    result = estimate_proposed_full_pipeline_beta_confidence(radar_input, accel, config)
    return replace(
        result,
        extra={
            **result.extra,
            "legacy_alias": "proposed_full_pipeline_calibrated",
        },
    )


def estimate_proposed_full_pipeline_posterior_r(radar_input, accel, config):
    selected = _select_posterior_r_q_result(radar_input, accel, config)
    result = selected["result"]
    process_noise_intensity = float(selected["q"])
    extra = {
        **result.extra,
        "process_noise_intensity": process_noise_intensity,
        "calibrated_q": process_noise_intensity,
        "calibrated_q_candidates": selected["candidates"],
        "calibrated_q_metric": "innovation_energy",
        "calibrated_q_metric_values": selected["metric_values"],
        "calibrated_q_selection_index": int(selected["index"]),
        "ablation_target": "posterior_residual_adaptive_r",
    }
    return replace(
        result,
        method_name="proposed_full_pipeline_posterior_r",
        extra=extra,
    )


def estimate_proposed_full_pipeline_beta_confidence_r(radar_input, accel, config):
    result = estimate_proposed_full_pipeline_beta_confidence(radar_input, accel, config)
    return replace(
        result,
        extra={
            **result.extra,
            "legacy_alias": "proposed_full_pipeline_beta_confidence_r",
        },
    )


def estimate_proposed_full_pipeline_doc_strict(radar_input, accel, config):
    selected = _select_doc_strict_q_result(radar_input, accel, config)
    result = selected["result"]
    process_noise_intensity = float(selected["q"])
    extra = {
        **result.extra,
        "process_noise_intensity": process_noise_intensity,
        "calibrated_q": process_noise_intensity,
        "calibrated_q_candidates": selected["candidates"],
        "calibrated_q_metric": "innovation_energy",
        "calibrated_q_metric_values": selected["metric_values"],
        "calibrated_q_selection_index": int(selected["index"]),
        "strict_comparison_target": "documented_initial_r_plain_ls_posterior_residual",
    }
    return replace(
        result,
        method_name="proposed_full_pipeline_doc_strict",
        extra=extra,
    )


def _select_calibrated_q_result(radar_input, accel, config):
    explicit_q = getattr(config, "calibrated_process_noise_intensity", None)
    if explicit_q is not None:
        q_value = float(explicit_q)
        result = _run_full_pipeline_candidate(radar_input, accel, config, q_value)
        return {
            "q": q_value,
            "candidates": np.asarray([q_value], dtype=float),
            "metric_values": np.asarray([_innovation_energy(result)], dtype=float),
            "index": 0,
            "result": result,
        }

    candidates = _calibrated_q_candidates(config)
    metric_values = np.full(candidates.shape, np.inf, dtype=float)
    results = []
    for idx, q_value in enumerate(candidates):
        result = _run_full_pipeline_candidate(radar_input, accel, config, float(q_value))
        metric_values[idx] = _innovation_energy(result)
        results.append(result)
    selected_idx = _select_calibrated_q_index(candidates, metric_values, config)
    return {
        "q": float(candidates[selected_idx]),
        "candidates": candidates,
        "metric_values": metric_values,
        "index": int(selected_idx),
        "result": results[selected_idx],
    }


def _select_posterior_r_q_result(radar_input, accel, config):
    explicit_q = getattr(config, "calibrated_process_noise_intensity", None)
    if explicit_q is not None:
        q_value = float(explicit_q)
        result = _run_posterior_r_candidate(radar_input, accel, config, q_value)
        return {
            "q": q_value,
            "candidates": np.asarray([q_value], dtype=float),
            "metric_values": np.asarray([_innovation_energy(result)], dtype=float),
            "index": 0,
            "result": result,
        }

    candidates = _calibrated_q_candidates(config)
    metric_values = np.full(candidates.shape, np.inf, dtype=float)
    results = []
    for idx, q_value in enumerate(candidates):
        result = _run_posterior_r_candidate(radar_input, accel, config, float(q_value))
        metric_values[idx] = _innovation_energy(result)
        results.append(result)
    selected_idx = _select_calibrated_q_index(candidates, metric_values, config)
    return {
        "q": float(candidates[selected_idx]),
        "candidates": candidates,
        "metric_values": metric_values,
        "index": int(selected_idx),
        "result": results[selected_idx],
    }


def _select_doc_strict_q_result(radar_input, accel, config):
    explicit_q = getattr(config, "calibrated_process_noise_intensity", None)
    if explicit_q is not None:
        q_value = float(explicit_q)
        result = _run_doc_strict_candidate(radar_input, accel, config, q_value)
        return {
            "q": q_value,
            "candidates": np.asarray([q_value], dtype=float),
            "metric_values": np.asarray([_innovation_energy(result)], dtype=float),
            "index": 0,
            "result": result,
        }

    candidates = _calibrated_q_candidates(config)
    metric_values = np.full(candidates.shape, np.inf, dtype=float)
    results = []
    for idx, q_value in enumerate(candidates):
        result = _run_doc_strict_candidate(radar_input, accel, config, float(q_value))
        metric_values[idx] = _innovation_energy(result)
        results.append(result)
    selected_idx = _select_calibrated_q_index(candidates, metric_values, config)
    return {
        "q": float(candidates[selected_idx]),
        "candidates": candidates,
        "metric_values": metric_values,
        "index": int(selected_idx),
        "result": results[selected_idx],
    }


def _run_full_pipeline_candidate(radar_input, accel, config, process_noise_intensity):
    calibrated_config = replace(config, process_noise_intensity=float(process_noise_intensity))
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline_beta_confidence_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_beta=_initial_beta_from_radar(radar_input),
        update_beta=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
        beta_update_mode="centered_regularized_ls",
        adaptive_r_mode="beta_confidence",
        initial_r_policy="provided_or_config",
    )


def _run_posterior_r_candidate(radar_input, accel, config, process_noise_intensity):
    calibrated_config = replace(config, process_noise_intensity=float(process_noise_intensity))
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline_posterior_r_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_beta=_initial_beta_from_radar(radar_input),
        update_beta=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
        beta_update_mode="centered_regularized_ls",
        adaptive_r_mode="posterior_residual",
        initial_r_policy="provided_or_config",
    )


def _run_doc_strict_candidate(radar_input, accel, config, process_noise_intensity):
    calibrated_config = replace(config, process_noise_intensity=float(process_noise_intensity))
    n_targets = int(radar_input.wrapped_phase_rad.shape[0])
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline_doc_strict_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_beta=_initial_beta_from_radar(radar_input),
        update_beta=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=np.full(n_targets, float(config.max_measurement_variance), dtype=float),
        beta_update_mode="plain_window_ls",
        adaptive_r_mode="posterior_residual",
        initial_r_policy="uniform_r_max",
    )


def _calibrated_q_candidates(config):
    values = np.asarray(getattr(config, "calibrated_q_candidates", (5.0e4,)), dtype=float)
    values = values[np.isfinite(values) & (values > 0.0)]
    if values.size == 0:
        values = np.asarray([calibrated_process_noise_intensity(config)], dtype=float)
    return values


def _innovation_energy(result):
    innovation = np.asarray(result.innovation_rad, dtype=float)
    valid = np.isfinite(innovation)
    if not np.any(valid):
        return float("inf")
    return float(np.nanmean(innovation[valid] ** 2))


def _select_calibrated_q_index(candidates, metric_values, config):
    finite = np.isfinite(metric_values)
    if not np.any(finite):
        return 0
    min_value = float(np.nanmin(metric_values[finite]))
    tolerance = max(abs(min_value) * 1.0e-12, 1.0e-12)
    tied = np.flatnonzero(np.isfinite(metric_values) & (np.abs(metric_values - min_value) <= tolerance))
    if tied.size <= 1:
        return int(np.nanargmin(metric_values))
    target = max(float(getattr(config, "calibrated_q_tie_break_value", 5.0e4)), np.finfo(float).tiny)
    positive = np.maximum(np.asarray(candidates[tied], dtype=float), np.finfo(float).tiny)
    local = int(np.argmin(np.abs(np.log10(positive) - np.log10(target))))
    return int(tied[local])


def _target_quality_scores(radar, n_targets, selected_indices_arr):
    scores = getattr(radar, "selection_scores", None)
    quality = np.zeros(n_targets, dtype=float)
    if scores is None:
        return quality

    arr = np.asarray(scores, dtype=float).reshape(-1)
    if arr.size == n_targets:
        quality = arr.copy()
    elif arr.size == selected_indices_arr.size:
        quality[selected_indices_arr] = arr
    elif arr.size:
        quality[selected_indices_arr[: min(arr.size, selected_indices_arr.size)]] = arr[
            : min(arr.size, selected_indices_arr.size)
        ]

    quality = np.nan_to_num(quality, nan=0.0, posinf=1.0, neginf=0.0)
    return np.clip(quality, 0.0, 1.0)


def run_structural_phase_kalman(
    method_name,
    radar,
    accel,
    config,
    initial_beta,
    update_beta,
    adaptive_r,
    selected_indices=None,
    initial_r=None,
    beta_update_mode="centered_regularized_ls",
    adaptive_r_mode="beta_confidence",
    initial_r_policy="provided_or_config",
):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    a_mat, b_vec, q_mat = _state_matrices(config)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    beta = _clip_beta(initial_beta, config)
    beta_prior = beta.copy()

    theta_hat = np.zeros(n_samples, dtype=float)
    theta_dot_hat = np.zeros(n_samples, dtype=float)
    beta_reference_theta = np.zeros(n_samples, dtype=float)
    los_corrected_phase = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovations = np.full((n_targets, n_samples), np.nan, dtype=float)
    if initial_r is None:
        r_theta_values = np.full(n_targets, float(config.initial_measurement_variance), dtype=float)
    else:
        r_theta_values = np.asarray(initial_r, dtype=float).copy()
        if r_theta_values.shape != (n_targets,):
            raise ValueError("initial_r must have one value per target")
        r_theta_values = np.clip(r_theta_values, config.min_measurement_variance, config.max_measurement_variance)
    initial_r_snapshot = r_theta_values.copy()
    r_theta_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    base_r_theta_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_variance_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_uncertainty_r_theta_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_gate_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_gain_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_abs_corr_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_residual_ratio_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_los_energy_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    beta_update_theta_energy_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    use_beta_confidence_r = adaptive_r_mode == "beta_confidence"
    use_quality_gated_r = adaptive_r_mode == "beta_confidence"
    beta_variance = np.full(
        n_targets,
        float(config.beta_confidence_initial_variance),
        dtype=float,
    )
    beta_variance = np.clip(
        beta_variance,
        float(config.beta_confidence_min_variance),
        float(config.beta_confidence_max_variance),
    )
    if selected_indices is None:
        selected_indices_arr = np.arange(n_targets, dtype=int)
    else:
        selected_indices_arr = np.asarray(selected_indices, dtype=int)
    selected_mask = np.zeros(n_targets, dtype=bool)
    selected_mask[selected_indices_arr] = True
    target_quality = _target_quality_scores(radar, n_targets, selected_indices_arr)
    target_quality_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    base_r_update_gate_history = np.full((n_targets, n_samples), np.nan, dtype=float)

    target_bias = _estimate_target_biases(radar, config)
    x = _initial_state_from_cold_start(radar, beta, target_bias, config, selected_indices_arr)
    x_beta_reference = x.copy()
    beta_fft_reference_theta = _acceleration_fft_reference_phase(accel, config, n_samples)
    warmup_index = int(round(config.beta_update_start_s * config.sample_rate_hz))
    beta_prior_weight = max(0.0, float(config.beta_bootstrap_prior_weight))
    measured_accel = np.asarray(accel.measured_mps2, dtype=float)

    for sample_idx in range(n_samples):
        accel_idx = max(sample_idx - 1, 0)
        u = _phase_accel_input(measured_accel[accel_idx], config)
        if sample_idx > 0:
            x_pred = a_mat @ x + b_vec * u
            p_pred = a_mat @ p @ a_mat.T + q_mat
            x_beta_reference = a_mat @ x_beta_reference + b_vec * u
        else:
            x_pred = x
            p_pred = p

        beta_reference_theta[sample_idx] = x_beta_reference[0]

        available = np.isfinite(radar.wrapped_phase_rad[:, sample_idx])
        if hasattr(radar, "available_mask"):
            available = available & np.asarray(radar.available_mask[:, sample_idx], dtype=bool)
        available = available & selected_mask
        active_indices = np.flatnonzero(available)
        base_r_used_values = r_theta_values.copy()
        effective_r_values = r_theta_values.copy()
        beta_uncertainty_r_values = np.zeros(n_targets, dtype=float)
        if active_indices.size:
            h_rows = []
            y_rows = []
            r_rows = []
            for target_idx in active_indices:
                los_prediction = x_pred[0] / beta[target_idx] + target_bias[target_idx]
                los_corrected = prediction_correct_wrapped_phase(
                    radar.wrapped_phase_rad[target_idx, sample_idx],
                    los_prediction,
                )
                los_corrected_phase[target_idx, sample_idx] = los_corrected
                los_without_bias = los_corrected - target_bias[target_idx]
                y_obs = beta[target_idx] * los_without_bias
                if use_beta_confidence_r:
                    beta_uncertainty_r_values[target_idx] = float(los_without_bias**2 * beta_variance[target_idx])
                    effective_r_values[target_idx] = float(
                        np.clip(
                            r_theta_values[target_idx] + beta_uncertainty_r_values[target_idx],
                            config.min_measurement_variance,
                            config.max_measurement_variance,
                        )
                    )
                h_rows.append([1.0, 0.0])
                y_rows.append(y_obs)
                r_rows.append(effective_r_values[target_idx])

            h = np.asarray(h_rows, dtype=float)
            y = np.asarray(y_rows, dtype=float)
            r_mat = np.diag(np.asarray(r_rows, dtype=float))
            innovation = y - (h @ x_pred)
            s_mat = h @ p_pred @ h.T + r_mat
            k_gain = p_pred @ h.T @ _safe_inverse(s_mat)
            x = x_pred + k_gain @ innovation
            p = (np.eye(2) - k_gain @ h) @ p_pred

            for local_idx, target_idx in enumerate(active_indices):
                prediction_residual = float(innovation[local_idx])
                posterior_residual = float(y[local_idx] - (h[local_idx] @ x))
                innovations[target_idx, sample_idx] = prediction_residual
                if adaptive_r:
                    h_i = h[local_idx : local_idx + 1]
                    post_var = float((h_i @ p @ h_i.T)[0, 0])
                    residual_for_r = (
                        posterior_residual
                        if adaptive_r_mode in ("posterior_residual", "beta_confidence")
                        else prediction_residual
                    )
                    variance_for_r = post_var
                    instant_r = float(residual_for_r**2 + variance_for_r)
                    if use_quality_gated_r:
                        delta_r = instant_r - float(r_theta_values[target_idx])
                        quality = float(target_quality[target_idx])
                        gate = (1.0 - quality) if delta_r > 0.0 else 1.0
                        blended = (
                            float(r_theta_values[target_idx])
                            + (1.0 - config.adaptive_r_forgetting) * gate * delta_r
                        )
                    else:
                        gate = 1.0
                        blended = (
                            config.adaptive_r_forgetting * r_theta_values[target_idx]
                            + (1.0 - config.adaptive_r_forgetting) * instant_r
                        )
                    r_theta_values[target_idx] = float(
                        np.clip(blended, config.min_measurement_variance, config.max_measurement_variance)
                    )
                    base_r_update_gate_history[target_idx, sample_idx] = gate
        else:
            x = x_pred
            p = p_pred

        theta_hat[sample_idx] = x[0]
        theta_dot_hat[sample_idx] = x[1]
        target_quality_history[selected_mask, sample_idx] = target_quality[selected_mask]
        if use_beta_confidence_r:
            r_theta_history[selected_mask, sample_idx] = effective_r_values[selected_mask]
            base_r_theta_history[selected_mask, sample_idx] = base_r_used_values[selected_mask]
            beta_uncertainty_r_theta_history[selected_mask, sample_idx] = beta_uncertainty_r_values[selected_mask]
        else:
            r_theta_history[selected_mask, sample_idx] = r_theta_values[selected_mask]
            base_r_theta_history[selected_mask, sample_idx] = r_theta_values[selected_mask]

        if update_beta and sample_idx >= warmup_index:
            start = max(0, sample_idx - int(config.beta_window_samples) + 1)
            reference_mode = getattr(config, "beta_update_reference_mode", "accel_fft_reference")
            if reference_mode == "accel_prediction":
                theta_window = beta_reference_theta[start : sample_idx + 1]
            elif reference_mode == "accel_fft_reference":
                theta_window = beta_fft_reference_theta[start : sample_idx + 1]
            else:
                theta_window = theta_hat[start : sample_idx + 1]
            for target_idx in selected_indices_arr:
                los_window = los_corrected_phase[target_idx, start : sample_idx + 1]
                valid = np.isfinite(los_window) & np.isfinite(theta_window)
                if np.count_nonzero(valid) < 3:
                    beta_update_gate_history[target_idx, sample_idx] = 0.0
                    beta_update_gain_history[target_idx, sample_idx] = 0.0
                    continue
                los_without_bias = los_window[valid] - target_bias[target_idx]
                theta_valid = theta_window[valid]
                can_update, update_gain, diagnostics = _beta_update_diagnostics(
                    theta_values=theta_valid,
                    los_values=los_without_bias,
                    config=config,
                )
                beta_update_gate_history[target_idx, sample_idx] = 1.0 if can_update else 0.0
                beta_update_gain_history[target_idx, sample_idx] = update_gain
                beta_update_abs_corr_history[target_idx, sample_idx] = diagnostics["abs_corr"]
                beta_update_residual_ratio_history[target_idx, sample_idx] = diagnostics["residual_ratio"]
                beta_update_los_energy_history[target_idx, sample_idx] = diagnostics["los_energy"]
                beta_update_theta_energy_history[target_idx, sample_idx] = diagnostics["theta_energy"]
                if not can_update or update_gain <= 0.0:
                    continue
                if beta_update_mode == "plain_window_ls":
                    denom_valid = float(np.dot(los_without_bias, los_without_bias))
                    if denom_valid <= 1.0e-12:
                        continue
                    new_beta = float(np.dot(los_without_bias, theta_valid) / denom_valid)
                    beta_var_estimate = None
                else:
                    fitted = _fit_beta_via_projection(
                        theta_values=theta_valid,
                        los_values=los_without_bias,
                        beta_prior=beta_prior[target_idx],
                        prior_weight=beta_prior_weight,
                        config=config,
                    )
                    if fitted is None:
                        continue
                    new_beta, beta_var_estimate = fitted
                if abs(new_beta) >= config.beta_min_abs:
                    delta = float(update_gain) * (float(new_beta) - float(beta[target_idx]))
                    max_delta = float(config.beta_update_max_relative_step) * max(
                        abs(float(beta[target_idx])),
                        config.beta_min_abs,
                    )
                    delta = float(np.clip(delta, -max_delta, max_delta))
                    beta[target_idx] = float(
                        np.clip(beta[target_idx] + delta, config.beta_min_abs, config.beta_max_abs)
                    )
                    if use_beta_confidence_r and beta_var_estimate is not None:
                        forgetting = float(config.beta_confidence_forgetting)
                        beta_variance[target_idx] = float(
                            np.clip(
                                forgetting * beta_variance[target_idx]
                                + (1.0 - forgetting) * beta_var_estimate,
                                config.beta_confidence_min_variance,
                                config.beta_confidence_max_variance,
                            )
                        )
        beta_history[:, sample_idx] = beta
        beta_variance_history[:, sample_idx] = beta_variance

    return MethodResult(
        method_name=method_name,
        q_hat_m=_phase_to_displacement(theta_hat, config),
        theta_hat_rad=theta_hat,
        theta_dot_hat_radps=theta_dot_hat,
        los_corrected_phase_rad=los_corrected_phase,
        beta_hat=beta.copy(),
        r_theta_history=r_theta_history,
        innovation_rad=innovations,
        extra={
            "beta_history": beta_history,
            "selected_indices": selected_indices_arr.copy(),
            "selected_target_count": int(selected_indices_arr.size),
            "initial_r": initial_r_snapshot,
            "beta_update_mode": beta_update_mode,
            "adaptive_r_mode": adaptive_r_mode,
            "initial_r_policy": initial_r_policy,
            "base_r_theta_history": base_r_theta_history,
            "beta_variance_history": beta_variance_history,
            "beta_uncertainty_r_theta_history": beta_uncertainty_r_theta_history,
            "beta_update_gate_history": beta_update_gate_history,
            "beta_update_gain_history": beta_update_gain_history,
            "beta_update_abs_corr_history": beta_update_abs_corr_history,
            "beta_update_residual_ratio_history": beta_update_residual_ratio_history,
            "beta_update_los_energy_history": beta_update_los_energy_history,
            "beta_update_theta_energy_history": beta_update_theta_energy_history,
            "beta_reference_theta_rad": beta_reference_theta,
            "beta_fft_reference_theta_rad": beta_fft_reference_theta,
            "target_quality_history": target_quality_history,
            "base_r_update_gate_history": base_r_update_gate_history,
        },
    )


_run_structural_phase_kalman = run_structural_phase_kalman
