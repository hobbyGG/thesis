from dataclasses import dataclass, field, replace

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


def _initial_state_from_cold_start(radar, kappa, target_bias, config, selected_indices=None):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    count = cold_start_sample_count(config, n_samples)
    theta0_estimates = []
    if selected_indices is None:
        indices = range(n_targets)
    else:
        indices = np.asarray(selected_indices, dtype=int)
    for target_idx in indices:
        kappa_i = float(kappa[target_idx])
        if abs(kappa_i) < config.kappa_min_abs:
            continue
        wrapped = radar.wrapped_phase_rad[target_idx, :count]
        valid = np.isfinite(wrapped)
        if not np.any(valid):
            continue
        unwrapped = itoh_unwrap(wrapped[valid])
        aligned_first = prediction_correct_wrapped_phase(wrapped[valid][0], target_bias[target_idx])
        unwrapped = unwrapped + (aligned_first - unwrapped[0])
        theta_samples = (unwrapped - target_bias[target_idx]) / kappa_i
        theta0_estimates.append(float(theta_samples[0]))
    theta0 = float(np.median(theta0_estimates)) if theta0_estimates else 0.0
    theta_dot0 = 0.0
    return np.array([theta0, theta_dot0], dtype=float)


def _phase_accel_input(accel_mps2, config):
    return (4.0 * np.pi / config.wavelength_m()) * float(accel_mps2)


def _safe_inverse(matrix):
    return np.linalg.pinv(matrix)


def estimate_proposed(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="proposed",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
    )


def estimate_proposed_full_pipeline(radar_input, accel, config):
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline",
        radar=radar_input,
        accel=accel,
        config=config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
    )


def calibrated_process_noise_intensity(config):
    value = getattr(config, "calibrated_process_noise_intensity", None)
    if value is None:
        value = getattr(config, "calibrated_q", 5.0e4)
    return float(value)


def estimate_proposed_full_pipeline_calibrated(radar_input, accel, config):
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
        method_name="proposed_full_pipeline_calibrated",
        extra=extra,
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


def estimate_proposed_full_pipeline_kappa_confidence_r(radar_input, accel, config):
    selected = _select_kappa_confidence_r_q_result(radar_input, accel, config)
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
        "ablation_target": "kappa_confidence_adaptive_r",
    }
    return replace(
        result,
        method_name="proposed_full_pipeline_kappa_confidence_r",
        extra=extra,
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


def _select_kappa_confidence_r_q_result(radar_input, accel, config):
    explicit_q = getattr(config, "calibrated_process_noise_intensity", None)
    if explicit_q is not None:
        q_value = float(explicit_q)
        result = _run_kappa_confidence_r_candidate(radar_input, accel, config, q_value)
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
        result = _run_kappa_confidence_r_candidate(radar_input, accel, config, float(q_value))
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
        method_name="proposed_full_pipeline_calibration_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
        kappa_update_mode="centered_regularized_ls",
        adaptive_r_mode="kappa_confidence",
        initial_r_policy="provided_or_config",
    )


def _run_posterior_r_candidate(radar_input, accel, config, process_noise_intensity):
    calibrated_config = replace(config, process_noise_intensity=float(process_noise_intensity))
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline_posterior_r_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
        kappa_update_mode="centered_regularized_ls",
        adaptive_r_mode="posterior_residual",
        initial_r_policy="provided_or_config",
    )


def _run_kappa_confidence_r_candidate(radar_input, accel, config, process_noise_intensity):
    calibrated_config = replace(config, process_noise_intensity=float(process_noise_intensity))
    return run_structural_phase_kalman(
        method_name="proposed_full_pipeline_kappa_confidence_r_candidate",
        radar=radar_input,
        accel=accel,
        config=calibrated_config,
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=radar_input.initial_r,
        kappa_update_mode="centered_regularized_ls",
        adaptive_r_mode="kappa_confidence",
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
        initial_kappa=radar_input.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
        selected_indices=radar_input.selected_indices,
        initial_r=np.full(n_targets, float(config.max_measurement_variance), dtype=float),
        kappa_update_mode="plain_window_ls",
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


def run_structural_phase_kalman(
    method_name,
    radar,
    accel,
    config,
    initial_kappa,
    update_kappa,
    adaptive_r,
    selected_indices=None,
    initial_r=None,
    kappa_update_mode="centered_regularized_ls",
    adaptive_r_mode="innovation",
    initial_r_policy="provided_or_config",
):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    a_mat, b_vec, q_mat = _state_matrices(config)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    kappa = np.asarray(initial_kappa, dtype=float).copy()
    kappa = np.clip(kappa, -config.kappa_max_abs, config.kappa_max_abs)
    small = np.abs(kappa) < config.kappa_min_abs
    kappa[small] = np.sign(kappa[small] + 1e-12) * config.kappa_min_abs
    kappa_prior = kappa.copy()

    theta_hat = np.zeros(n_samples, dtype=float)
    theta_dot_hat = np.zeros(n_samples, dtype=float)
    corrected = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovations = np.full((n_targets, n_samples), np.nan, dtype=float)
    if initial_r is None:
        r_values = np.full(n_targets, float(config.initial_measurement_variance), dtype=float)
    else:
        r_values = np.asarray(initial_r, dtype=float).copy()
        if r_values.shape != (n_targets,):
            raise ValueError("initial_r must have one value per target")
        r_values = np.clip(r_values, config.min_measurement_variance, config.max_measurement_variance)
    initial_r_snapshot = r_values.copy()
    r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    base_r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_variance_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_uncertainty_r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    use_kappa_confidence_r = adaptive_r_mode == "kappa_confidence"
    kappa_variance = np.full(
        n_targets,
        float(getattr(config, "kappa_confidence_initial_variance", 0.04)),
        dtype=float,
    )
    kappa_variance = np.clip(
        kappa_variance,
        float(getattr(config, "kappa_confidence_min_variance", 1.0e-6)),
        float(getattr(config, "kappa_confidence_max_variance", 0.25)),
    )
    if selected_indices is None:
        selected_indices_arr = np.arange(n_targets, dtype=int)
    else:
        selected_indices_arr = np.asarray(selected_indices, dtype=int)
    selected_mask = np.zeros(n_targets, dtype=bool)
    selected_mask[selected_indices_arr] = True

    target_bias = _estimate_target_biases(radar, config)
    x = _initial_state_from_cold_start(radar, kappa, target_bias, config, selected_indices_arr)
    warmup_index = int(round(config.kappa_update_start_s * config.sample_rate_hz))
    kappa_prior_weight = max(0.0, float(getattr(config, "kappa_bootstrap_prior_weight", 0.0)))
    measured_accel = np.asarray(accel.measured_mps2, dtype=float)

    for sample_idx in range(n_samples):
        accel_idx = max(sample_idx - 1, 0)
        u = _phase_accel_input(measured_accel[accel_idx], config)
        if sample_idx > 0:
            x_pred = a_mat @ x + b_vec * u
            p_pred = a_mat @ p @ a_mat.T + q_mat
        else:
            x_pred = x
            p_pred = p

        available = np.isfinite(radar.wrapped_phase_rad[:, sample_idx])
        if hasattr(radar, "available_mask"):
            available = available & np.asarray(radar.available_mask[:, sample_idx], dtype=bool)
        available = available & selected_mask
        active_indices = np.flatnonzero(available)
        base_r_used_values = r_values.copy()
        effective_r_values = r_values.copy()
        kappa_uncertainty_r_values = np.zeros(n_targets, dtype=float)
        if active_indices.size:
            h_rows = []
            z_rows = []
            bias_rows = []
            r_rows = []
            for target_idx in active_indices:
                prediction = kappa[target_idx] * x_pred[0] + target_bias[target_idx]
                z_corr = prediction_correct_wrapped_phase(radar.wrapped_phase_rad[target_idx, sample_idx], prediction)
                corrected[target_idx, sample_idx] = z_corr
                if use_kappa_confidence_r:
                    theta_variance = max(0.0, float(p_pred[0, 0]))
                    kappa_uncertainty_r_values[target_idx] = float(
                        (float(x_pred[0]) ** 2 + theta_variance) * kappa_variance[target_idx]
                    )
                    effective_r_values[target_idx] = float(
                        np.clip(
                            r_values[target_idx] + kappa_uncertainty_r_values[target_idx],
                            config.min_measurement_variance,
                            config.max_measurement_variance,
                        )
                    )
                h_rows.append([kappa[target_idx], 0.0])
                z_rows.append(z_corr)
                bias_rows.append(target_bias[target_idx])
                r_rows.append(effective_r_values[target_idx])

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
                prediction_residual = float(innovation[local_idx])
                posterior_residual = float(z[local_idx] - (h[local_idx] @ x + bias_vec_obs[local_idx]))
                innovations[target_idx, sample_idx] = prediction_residual
                if adaptive_r:
                    h_i = h[local_idx : local_idx + 1]
                    post_var = float((h_i @ p @ h_i.T)[0, 0])
                    residual_for_r = (
                        posterior_residual if adaptive_r_mode == "posterior_residual" else prediction_residual
                    )
                    instant_r = float(residual_for_r**2 + post_var)
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
        if use_kappa_confidence_r:
            r_history[selected_mask, sample_idx] = effective_r_values[selected_mask]
            base_r_history[selected_mask, sample_idx] = base_r_used_values[selected_mask]
            kappa_uncertainty_r_history[selected_mask, sample_idx] = kappa_uncertainty_r_values[selected_mask]
        else:
            r_history[selected_mask, sample_idx] = r_values[selected_mask]
            base_r_history[selected_mask, sample_idx] = r_values[selected_mask]

        if update_kappa and sample_idx >= warmup_index:
            start = max(0, sample_idx - int(config.kappa_window_samples) + 1)
            theta_window = theta_hat[start : sample_idx + 1]
            denom = float(np.sum(theta_window**2))
            if denom > 1e-12:
                for target_idx in selected_indices_arr:
                    z_window = corrected[target_idx, start : sample_idx + 1]
                    valid = np.isfinite(z_window)
                    if np.count_nonzero(valid) >= 3:
                        theta_valid = theta_window[valid]
                        z_valid = z_window[valid] - target_bias[target_idx]
                        if kappa_update_mode == "plain_window_ls":
                            denom_valid = float(np.sum(theta_valid**2))
                            if denom_valid <= 1e-12:
                                continue
                            numerator = float(np.sum(theta_valid * z_valid))
                            new_kappa = numerator / denom_valid
                        else:
                            theta_centered = theta_valid - float(np.mean(theta_valid))
                            z_centered = z_valid - float(np.mean(z_valid))
                            denom_valid = float(np.sum(theta_centered**2))
                            if denom_valid <= 1e-12:
                                continue
                            numerator = float(np.sum(theta_centered * z_centered))
                            if kappa_prior_weight > 0.0:
                                new_kappa = (
                                    numerator + kappa_prior_weight * kappa_prior[target_idx]
                                ) / (denom_valid + kappa_prior_weight)
                            else:
                                new_kappa = numerator / denom_valid
                        if abs(new_kappa) >= config.kappa_min_abs:
                            kappa[target_idx] = float(np.clip(new_kappa, -config.kappa_max_abs, config.kappa_max_abs))
                            if use_kappa_confidence_r:
                                residual = z_valid - new_kappa * theta_valid
                                if kappa_update_mode != "plain_window_ls":
                                    residual = z_centered - new_kappa * theta_centered
                                dof = max(int(np.count_nonzero(valid)) - 1, 1)
                                residual_var = float(np.sum(residual**2) / dof)
                                variance_estimate = residual_var / max(float(denom_valid), 1.0e-12)
                                variance_estimate = float(
                                    np.clip(
                                        variance_estimate,
                                        getattr(config, "kappa_confidence_min_variance", 1.0e-6),
                                        getattr(config, "kappa_confidence_max_variance", 0.25),
                                    )
                                )
                                forgetting = float(getattr(config, "kappa_confidence_forgetting", 0.90))
                                kappa_variance[target_idx] = float(
                                    np.clip(
                                        forgetting * kappa_variance[target_idx]
                                        + (1.0 - forgetting) * variance_estimate,
                                        getattr(config, "kappa_confidence_min_variance", 1.0e-6),
                                        getattr(config, "kappa_confidence_max_variance", 0.25),
                                    )
                                )
        kappa_history[:, sample_idx] = kappa
        kappa_variance_history[:, sample_idx] = kappa_variance

    return MethodResult(
        method_name=method_name,
        q_hat_m=_phase_to_displacement(theta_hat, config),
        theta_hat_rad=theta_hat,
        theta_dot_hat_radps=theta_dot_hat,
        corrected_phase_rad=corrected,
        kappa_hat=kappa.copy(),
        r_history=r_history,
        innovation_rad=innovations,
        extra={
            "kappa_history": kappa_history,
            "selected_indices": selected_indices_arr.copy(),
            "selected_target_count": int(selected_indices_arr.size),
            "initial_r": initial_r_snapshot,
            "kappa_update_mode": kappa_update_mode,
            "adaptive_r_mode": adaptive_r_mode,
            "initial_r_policy": initial_r_policy,
            "base_r_history": base_r_history,
            "kappa_variance_history": kappa_variance_history,
            "kappa_uncertainty_r_history": kappa_uncertainty_r_history,
        },
    )


_run_structural_phase_kalman = run_structural_phase_kalman
