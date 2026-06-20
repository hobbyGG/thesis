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
        corrected_errors = []
        corrected_observation_count = 0
        target_reference_indices = _result_target_reference_indices(
            result,
            reference_by_method.get(result.method_name),
        )
        for target_idx in range(result.corrected_phase_rad.shape[0]):
            corrected_observation_count += int(np.count_nonzero(np.isfinite(result.corrected_phase_rad[target_idx])))
            reference_idx = int(target_reference_indices[target_idx])
            if 0 <= reference_idx < radar.true_los_phase_rad.shape[0]:
                corrected_errors.append(
                    count_branch_errors(result.corrected_phase_rad[target_idx], radar.true_los_phase_rad[reference_idx])
                )
        unwrap_errors = int(np.sum(corrected_errors))
        selected_indices_internal = result.extra.get("selected_indices", np.arange(result.corrected_phase_rad.shape[0]))
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
        row["kappa_median_relative_error"] = _kappa_median_relative_error(
            result,
            radar,
            selected_indices_internal,
            target_reference_indices,
        )
        rows.append(row)
    return rows


def _result_target_reference_indices(result, override=None):
    n_targets = int(result.corrected_phase_rad.shape[0])
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


def _kappa_median_relative_error(result, radar, selected_indices, target_reference_indices):
    if result.kappa_hat.shape[0] != target_reference_indices.size:
        return float("nan")
    selected = np.asarray(selected_indices, dtype=int)
    if selected.size == 0:
        selected = np.arange(result.kappa_hat.shape[0], dtype=int)
    errors = []
    for target_idx in selected:
        if target_idx < 0 or target_idx >= result.kappa_hat.shape[0]:
            continue
        reference_idx = int(target_reference_indices[target_idx])
        if reference_idx < 0 or reference_idx >= radar.kappa.size:
            continue
        denom = max(abs(float(radar.kappa[reference_idx])), 1e-12)
        errors.append(abs(float(result.kappa_hat[target_idx]) - float(radar.kappa[reference_idx])) / denom)
    if not errors:
        return float("nan")
    return float(np.median(errors))


_method_rows = method_rows
