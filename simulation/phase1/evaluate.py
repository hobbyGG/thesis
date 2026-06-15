import numpy as np

from .accelerometer import simulate_accelerometer
from .metrics import displacement_metrics, phase_rmse_rad
from .methods import (
    estimate_itoh_ls,
    estimate_multitarget_fixed,
    estimate_oracle,
    estimate_proposed,
    estimate_single_target_ma_style,
)
from .phase_utils import count_branch_errors
from .radar import simulate_radar_targets
from .truth import generate_multifrequency_truth


def _best_target_index(radar):
    snr = np.asarray(radar.snr_db, dtype=float)
    return int(np.nanargmax(snr))


def _method_rows(scenario, truth, radar, results):
    rows = []
    for result in results:
        disp = displacement_metrics(result.q_hat_m, truth.q_m)
        phase_rmse = phase_rmse_rad(result.theta_hat_rad, radar.true_main_phase_rad)
        corrected_errors = []
        for target_idx in range(radar.true_los_phase_rad.shape[0]):
            corrected_errors.append(
                count_branch_errors(result.corrected_phase_rad[target_idx], radar.true_los_phase_rad[target_idx])
            )
        row = {
            "scenario": scenario.scenario_name,
            "method": result.method_name,
            "rmse_mm": disp["rmse_mm"],
            "mae_mm": disp["mae_mm"],
            "max_error_mm": disp["max_error_mm"],
            "theta_rmse_rad": phase_rmse,
            "unwrap_errors": int(np.sum(corrected_errors)),
        }
        rows.append(row)
    return rows


def evaluate_scenario(scenario):
    truth = generate_multifrequency_truth(scenario)
    radar = simulate_radar_targets(truth, scenario)
    accel = simulate_accelerometer(truth, scenario)
    best_idx = _best_target_index(radar)
    results = [
        estimate_oracle(truth, radar, scenario),
        estimate_itoh_ls(truth, radar, scenario, target_index=best_idx),
        estimate_single_target_ma_style(truth, radar, scenario, target_index=best_idx),
        estimate_multitarget_fixed(truth, radar, scenario),
        estimate_proposed(truth, radar, scenario),
    ]
    rows = _method_rows(scenario, truth, radar, results)
    artifacts = {"truth": truth, "radar": radar, "accelerometer": accel, "results": results}
    return rows, artifacts


def _row_lookup(rows, scenario, method):
    for row in rows:
        if row["scenario"] == scenario and row["method"] == method:
            return row
    return None


def _build_gate_results(rows):
    gates = []
    nominal = _row_lookup(rows, "nominal_multifrequency", "proposed")
    if nominal:
        gates.append(
            {
                "name": "nominal_proposed_rmse_le_0p03mm",
                "value": nominal["rmse_mm"],
                "threshold": 0.03,
                "passed": bool(nominal["rmse_mm"] <= 0.03),
            }
        )

    strong_prop = _row_lookup(rows, "strong_wrapping", "proposed")
    strong_itoh = _row_lookup(rows, "strong_wrapping", "itoh_ls")
    if strong_prop and strong_itoh:
        gates.append(
            {
                "name": "strong_wrapping_rmse_le_0p08mm",
                "value": strong_prop["rmse_mm"],
                "threshold": 0.08,
                "passed": bool(strong_prop["rmse_mm"] <= 0.08),
            }
        )
        threshold = max(1, 0.1 * strong_itoh["unwrap_errors"])
        gates.append(
            {
                "name": "strong_wrapping_unwrap_errors_le_10pct_itoh",
                "value": strong_prop["unwrap_errors"],
                "threshold": threshold,
                "passed": bool(strong_prop["unwrap_errors"] <= threshold),
            }
        )

    snr_prop = _row_lookup(rows, "target_snr_drop", "proposed")
    snr_fixed = _row_lookup(rows, "target_snr_drop", "multitarget_fixed")
    if snr_prop and snr_fixed:
        gates.append(
            {
                "name": "target_snr_drop_proposed_beats_fixed_r",
                "value": snr_prop["rmse_mm"],
                "threshold": snr_fixed["rmse_mm"],
                "passed": bool(snr_prop["rmse_mm"] < snr_fixed["rmse_mm"]),
            }
        )

    wins = 0
    comparisons = 0
    for scenario_name in sorted({row["scenario"] for row in rows}):
        prop = _row_lookup(rows, scenario_name, "proposed")
        single = _row_lookup(rows, scenario_name, "single_target_ma_style")
        if prop and single:
            comparisons += 1
            if prop["rmse_mm"] < single["rmse_mm"]:
                wins += 1
    if comparisons:
        gates.append(
            {
                "name": "proposed_beats_single_target_in_at_least_4_scenarios",
                "value": wins,
                "threshold": 4,
                "passed": bool(wins >= min(4, comparisons)),
            }
        )
    return gates


def evaluate_all_scenarios(scenarios):
    all_rows = []
    artifacts_by_scenario = {}
    for scenario in scenarios:
        rows, artifacts = evaluate_scenario(scenario)
        all_rows.extend(rows)
        artifacts_by_scenario[scenario.scenario_name] = artifacts
    return {"rows": all_rows, "gates": _build_gate_results(all_rows), "artifacts": artifacts_by_scenario}
