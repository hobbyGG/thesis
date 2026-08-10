import math

import numpy as np


DIAGNOSTIC_FIELDNAMES = [
    "scenario",
    "method",
    "beta_update_reference_mode",
    "target_idx",
    "reference_idx",
    "beta_true",
    "beta_initial",
    "beta_final",
    "initial_relative_error",
    "final_relative_error",
    "last20_median_relative_error",
    "gate_on_ratio",
    "abs_corr_median",
    "residual_ratio_median",
    "common_aoa_bias_final_deg",
]


def beta_bootstrap_diagnostic_rows(
    beta_history,
    beta_true,
    beta_initial=None,
    selected_indices=None,
    target_reference_indices=None,
    gate_history=None,
    abs_corr_history=None,
    residual_ratio_history=None,
    beta_update_reference_mode="",
    common_aoa_bias_history_deg=None,
    scenario="",
    method="",
):
    history = _as_2d_float(beta_history)
    n_targets = history.shape[0]
    true_beta = np.asarray(beta_true, dtype=float)
    initial_beta = _initial_beta_values(history, beta_initial)
    references = _reference_indices(n_targets, target_reference_indices)
    selected = _selected_indices(n_targets, selected_indices)
    gates = _optional_2d_float(gate_history, n_targets)
    abs_corr = _optional_2d_float(abs_corr_history, n_targets)
    residual_ratio = _optional_2d_float(residual_ratio_history, n_targets)
    common_aoa_bias_final_deg = _last_finite(common_aoa_bias_history_deg)

    rows = []
    for target_idx in selected:
        if target_idx < 0 or target_idx >= n_targets:
            continue
        reference_idx = int(references[target_idx])
        beta_true_value = _indexed_value(true_beta, reference_idx)
        beta_initial_value = _indexed_value(initial_beta, target_idx)
        beta_final_value = _last_finite(history[target_idx])
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "beta_update_reference_mode": beta_update_reference_mode,
                "target_idx": int(target_idx),
                "reference_idx": reference_idx,
                "beta_true": beta_true_value,
                "beta_initial": beta_initial_value,
                "beta_final": beta_final_value,
                "initial_relative_error": _relative_error(beta_initial_value, beta_true_value),
                "final_relative_error": _relative_error(beta_final_value, beta_true_value),
                "last20_median_relative_error": _last_fraction_median_relative_error(
                    history[target_idx],
                    beta_true_value,
                    fraction=0.2,
                ),
                "gate_on_ratio": _gate_on_ratio(_row_or_empty(gates, target_idx)),
                "abs_corr_median": _finite_median(_row_or_empty(abs_corr, target_idx)),
                "residual_ratio_median": _finite_median(_row_or_empty(residual_ratio, target_idx)),
                "common_aoa_bias_final_deg": common_aoa_bias_final_deg,
            }
        )
    return rows


def beta_bootstrap_rows_from_result(result, radar, target_reference_indices=None, scenario=""):
    beta_history = result.extra.get("beta_history")
    if beta_history is None:
        return []
    selected_indices = result.extra.get("selected_indices")
    return beta_bootstrap_diagnostic_rows(
        beta_history=beta_history,
        beta_true=radar.beta,
        selected_indices=selected_indices,
        target_reference_indices=target_reference_indices,
        gate_history=result.extra.get("beta_update_gate_history"),
        abs_corr_history=result.extra.get("beta_update_abs_corr_history"),
        residual_ratio_history=result.extra.get("beta_update_residual_ratio_history"),
        beta_update_reference_mode=result.extra.get("beta_update_reference_mode", ""),
        common_aoa_bias_history_deg=result.extra.get("beta_common_aoa_bias_history_deg"),
        scenario=scenario,
        method=result.method_name,
    )


def beta_diagnostics_gate_passes(rows, threshold=0.05):
    if not rows:
        return False
    for row in rows:
        final_error = float(row.get("final_relative_error", math.nan))
        last20_error = float(row.get("last20_median_relative_error", math.nan))
        gate_on_ratio = float(row.get("gate_on_ratio", math.nan))
        if not (
            math.isfinite(final_error)
            and math.isfinite(last20_error)
            and math.isfinite(gate_on_ratio)
            and final_error <= threshold
            and last20_error <= threshold
            and gate_on_ratio > 0.0
        ):
            return False
    return True


def beta_bootstrap_figure_title(rows, threshold=0.05):
    if beta_diagnostics_gate_passes(rows, threshold=threshold):
        return "beta convergence diagnostics"
    return "beta error reduction under AoA initialization bias"


def _as_2d_float(values):
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2:
        raise ValueError("beta_history must be one- or two-dimensional")
    return arr


def _optional_2d_float(values, n_targets):
    if values is None:
        return np.empty((n_targets, 0), dtype=float)
    arr = _as_2d_float(values)
    if arr.shape[0] != n_targets:
        return np.empty((n_targets, 0), dtype=float)
    return arr


def _initial_beta_values(history, beta_initial):
    if beta_initial is not None:
        initial = np.asarray(beta_initial, dtype=float)
        if initial.shape == (history.shape[0],):
            return initial
    return np.asarray([_first_finite(row) for row in history], dtype=float)


def _reference_indices(n_targets, target_reference_indices):
    if target_reference_indices is None:
        return np.arange(n_targets, dtype=int)
    references = np.asarray(target_reference_indices, dtype=int)
    if references.shape != (n_targets,):
        return np.arange(n_targets, dtype=int)
    return references


def _selected_indices(n_targets, selected_indices):
    if selected_indices is None:
        return np.arange(n_targets, dtype=int)
    selected = np.asarray(selected_indices, dtype=int)
    if selected.size == 0:
        return np.arange(n_targets, dtype=int)
    return selected


def _indexed_value(values, idx):
    if 0 <= idx < values.size:
        return float(values[idx])
    return float("nan")


def _first_finite(values):
    arr = np.asarray(values, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return float("nan")
    return float(valid[0])


def _last_finite(values):
    arr = np.asarray(values, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return float("nan")
    return float(valid[-1])


def _relative_error(value, truth):
    if not (math.isfinite(value) and math.isfinite(truth)):
        return float("nan")
    denom = max(abs(float(truth)), 1.0e-12)
    return float(abs(float(value) - float(truth)) / denom)


def _last_fraction_median_relative_error(values, truth, fraction):
    arr = np.asarray(values, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0 or not math.isfinite(float(truth)):
        return float("nan")
    count = max(1, int(math.ceil(float(valid.size) * float(fraction))))
    errors = np.asarray([_relative_error(value, truth) for value in valid[-count:]], dtype=float)
    return _finite_median(errors)


def _gate_on_ratio(values):
    arr = np.asarray(values, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return float("nan")
    return float(np.count_nonzero(valid > 0.0) / valid.size)


def _finite_median(values):
    arr = np.asarray(values, dtype=float)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return float("nan")
    return float(np.median(valid))


def _row_or_empty(values, target_idx):
    if values.size == 0 or target_idx < 0 or target_idx >= values.shape[0]:
        return np.asarray([], dtype=float)
    return values[target_idx]
