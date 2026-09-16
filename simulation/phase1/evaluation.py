import numpy as np

from .algorithm import cold_start_reference_mean
from .metrics import displacement_metrics, phase_rmse_rad
from .phase_utils import count_branch_errors
from .scenario_catalog import scenario_metadata_fields


def method_rows(scenario, truth, radar, results, target_reference_by_method=None):
    rows = []
    reference_by_method = target_reference_by_method or {}
    q_ref = cold_start_reference_mean(truth.q_m, scenario)
    true_relative_phase = 4.0 * np.pi * (truth.q_m - q_ref) / scenario.wavelength_m()
    for result in results:
        disp = displacement_metrics(result.q_hat_m, truth.q_m - q_ref)
        phase_rmse = phase_rmse_rad(result.theta_hat_rad, true_relative_phase)
        los_corrected_phase = result.los_corrected_phase_rad
        corrected_errors = []
        corrected_observation_count = 0
        target_reference_indices = _result_target_reference_indices(
            result,
            reference_by_method.get(result.method_name),
        )
        for target_idx in range(los_corrected_phase.shape[0]):
            corrected_observation_count += int(np.count_nonzero(np.isfinite(los_corrected_phase[target_idx])))
            reference_idx = int(target_reference_indices[target_idx])
            if 0 <= reference_idx < radar.true_los_phase_rad.shape[0]:
                corrected_errors.append(
                    count_branch_errors(los_corrected_phase[target_idx], radar.true_los_phase_rad[reference_idx])
                )
        unwrap_errors = int(np.sum(corrected_errors))
        selected_indices_internal = result.extra.get("selected_indices", np.arange(los_corrected_phase.shape[0]))
        selected_indices_internal = np.asarray(selected_indices_internal, dtype=int)
        selected_indices = _reported_selected_indices(selected_indices_internal, target_reference_indices)
        selected_target_count = int(result.extra.get("selected_target_count", selected_indices.size))
        row = {
            "scenario": scenario.scenario_name,
            **scenario_metadata_fields(scenario.scenario_name),
            "method": result.method_name,
            "rmse_mm": disp["rmse_mm"],
            "mae_mm": disp["mae_mm"],
            "max_error_mm": disp["max_error_mm"],
            "theta_rmse_rad": phase_rmse,
            "unwrap_errors": unwrap_errors,
            "selected_target_count": selected_target_count,
            "selected_indices": selected_indices.tolist(),
            "corrected_observation_count": corrected_observation_count,
            "unwrap_error_rate": float(unwrap_errors / corrected_observation_count)
            if corrected_observation_count
            else 0.0,
        }
        row["beta_median_relative_error"] = _beta_median_relative_error(
            result,
            radar,
            selected_indices_internal,
            target_reference_indices,
        )
        row["beta_initial_median_relative_error"] = _beta_initial_median_relative_error(
            result,
            radar,
            selected_indices_internal,
            target_reference_indices,
        )
        row["beta_improvement_ratio"] = (
            row["beta_median_relative_error"] / row["beta_initial_median_relative_error"]
            if row["beta_initial_median_relative_error"] > 0.0
            else float("nan")
        )
        rows.append(row)
    return rows


def _result_target_reference_indices(result, override=None):
    n_targets = int(result.los_corrected_phase_rad.shape[0])
    references = override
    if references is None:
        return np.arange(n_targets, dtype=int)
    references = np.asarray(references, dtype=int)
    if references.shape != (n_targets,):
        return np.arange(n_targets, dtype=int)
    return references


def _reported_selected_indices(selected_indices, target_reference_indices):
    selected = np.asarray(selected_indices, dtype=int)
    if selected.size == 0:
        return selected
    valid = (selected >= 0) & (selected < target_reference_indices.size)
    reported = selected.copy()
    reported[valid] = target_reference_indices[selected[valid]]
    return reported


def _beta_median_relative_error(result, radar, selected_indices, target_reference_indices):
    if result.beta_hat.shape[0] != target_reference_indices.size:
        return float("nan")
    return _beta_median_relative_error_for_values(
        result.beta_hat,
        radar,
        selected_indices,
        target_reference_indices,
    )


def _beta_initial_median_relative_error(result, radar, selected_indices, target_reference_indices):
    if result.beta_hat.shape[0] != target_reference_indices.size:
        return float("nan")
    initial_beta = _initial_beta_values(result, radar, target_reference_indices)
    return _beta_median_relative_error_for_values(
        initial_beta,
        radar,
        selected_indices,
        target_reference_indices,
    )


def _initial_beta_values(result, radar, target_reference_indices):
    explicit = result.extra.get("beta_initial")
    if explicit is not None:
        explicit = np.asarray(explicit, dtype=float)
        if explicit.shape == (target_reference_indices.size,):
            return explicit.copy()

    history = result.extra.get("beta_history")
    if history is not None:
        history = np.asarray(history, dtype=float)
        if history.ndim == 2 and history.shape[0] == target_reference_indices.size:
            initial = np.full(history.shape[0], np.nan, dtype=float)
            for target_idx in range(history.shape[0]):
                finite = history[target_idx, np.isfinite(history[target_idx])]
                if finite.size:
                    initial[target_idx] = float(finite[0])
            if np.any(np.isfinite(initial)):
                return initial

    initial = np.full(target_reference_indices.size, np.nan, dtype=float)
    for target_idx, reference_idx in enumerate(np.asarray(target_reference_indices, dtype=int)):
        if 0 <= reference_idx < radar.measured_beta.size:
            initial[target_idx] = float(radar.measured_beta[reference_idx])
    return initial


def _beta_median_relative_error_for_values(beta_values, radar, selected_indices, target_reference_indices):
    selected = np.asarray(selected_indices, dtype=int)
    if selected.size == 0:
        selected = np.arange(np.asarray(beta_values).shape[0], dtype=int)
    beta_values = np.asarray(beta_values, dtype=float)
    errors = []
    for target_idx in selected:
        if target_idx < 0 or target_idx >= beta_values.shape[0]:
            continue
        reference_idx = int(target_reference_indices[target_idx])
        if reference_idx < 0 or reference_idx >= radar.beta.size:
            continue
        denom = max(abs(float(radar.beta[reference_idx])), 1e-12)
        beta_value = float(beta_values[target_idx])
        if not np.isfinite(beta_value):
            continue
        errors.append(abs(beta_value - float(radar.beta[reference_idx])) / denom)
    if not errors:
        return float("nan")
    return float(np.median(errors))


_method_rows = method_rows
