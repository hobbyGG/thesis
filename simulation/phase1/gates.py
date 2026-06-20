import numpy as np


def row_lookup(rows, scenario, method):
    for row in rows:
        if row["scenario"] == scenario and row["method"] == method:
            return row
    return None


def full_pipeline_row(rows, scenario):
    return row_lookup(rows, scenario, "proposed_full_pipeline_calibrated") or row_lookup(
        rows,
        scenario,
        "proposed_full_pipeline",
    )


def same_range_far_angle_pair_count(frontend_targets, min_angle_separation_deg=15.0):
    if frontend_targets is None:
        return 0
    range_bins = np.asarray(frontend_targets.range_bins, dtype=int)
    angles = np.asarray(frontend_targets.angle_deg, dtype=float)
    count = 0
    for left in range(range_bins.size):
        for right in range(left + 1, range_bins.size):
            if range_bins[left] == range_bins[right] and abs(angles[left] - angles[right]) > min_angle_separation_deg:
                count += 1
    return int(count)


def build_gate_results(rows, artifacts_by_scenario=None):
    gates = []
    artifacts_by_scenario = artifacts_by_scenario or {}
    nominal = row_lookup(rows, "nominal_multifrequency", "proposed")
    if nominal:
        gates.append(
            {
                "name": "nominal_proposed_rmse_le_0p10mm",
                "value": nominal["rmse_mm"],
                "threshold": 0.10,
                "passed": bool(nominal["rmse_mm"] <= 0.10),
            }
        )

    strong_prop = row_lookup(rows, "strong_wrapping", "proposed")
    strong_itoh = row_lookup(rows, "strong_wrapping", "itoh_ls")
    if strong_prop and strong_itoh:
        gates.append(
            {
                "name": "strong_wrapping_proposed_rmse_le_0p50mm",
                "value": strong_prop["rmse_mm"],
                "threshold": 0.50,
                "passed": bool(strong_prop["rmse_mm"] <= 0.50),
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
    strong_full = full_pipeline_row(rows, "strong_wrapping")
    if strong_full and strong_itoh:
        gates.append(
            {
                "name": "strong_wrapping_itoh_unwrap_errors_gt_0",
                "value": strong_itoh["unwrap_errors"],
                "threshold": 0,
                "passed": bool(strong_itoh["unwrap_errors"] > 0),
            }
        )
        gates.append(
            {
                "name": "strong_wrapping_full_pipeline_unwrap_error_rate_lt_itoh",
                "value": strong_full["unwrap_error_rate"],
                "threshold": strong_itoh["unwrap_error_rate"],
                "passed": bool(strong_full["unwrap_error_rate"] <= strong_itoh["unwrap_error_rate"]),
            }
        )
        gates.append(
            {
                "name": "strong_wrapping_full_pipeline_rmse_le_reasonable_threshold",
                "value": strong_full["rmse_mm"],
                "threshold": 0.50,
                "passed": bool(strong_full["rmse_mm"] <= 0.50),
            }
        )

    snr_prop = row_lookup(rows, "target_snr_drop", "proposed")
    snr_fixed = row_lookup(rows, "target_snr_drop", "multitarget_true_kappa_fixed_r")
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
        prop = row_lookup(rows, scenario_name, "proposed")
        single = row_lookup(rows, scenario_name, "single_target_ma_style")
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
    full_nominal = full_pipeline_row(rows, "nominal_multifrequency")
    if full_nominal:
        gates.append(
            {
                "name": "nominal_full_pipeline_rmse_le_0p10mm",
                "value": full_nominal["rmse_mm"],
                "threshold": 0.10,
                "passed": bool(full_nominal["rmse_mm"] <= 0.10),
            }
        )
    ma_like_full = full_pipeline_row(rows, "ma2023_balanced_good_targets")
    ma_like_single = row_lookup(rows, "ma2023_balanced_good_targets", "single_target_ma_style")
    if ma_like_full and ma_like_single:
        gates.append(
            {
                "name": "ma2023_balanced_good_targets_full_pipeline_beats_best_target",
                "value": ma_like_full["rmse_mm"],
                "threshold": ma_like_single["rmse_mm"],
                "passed": bool(ma_like_full["rmse_mm"] < ma_like_single["rmse_mm"]),
            }
        )
    same_range = full_pipeline_row(rows, "same_range_far_angles")
    same_range_range_only = row_lookup(rows, "same_range_far_angles", "range_bin_only_mixed_phase")
    same_range_ma_style = row_lookup(rows, "same_range_far_angles", "ma_style_iterative_beta_range_bin")
    same_range_ma2026 = row_lookup(rows, "same_range_far_angles", "ma2026_reproduction")
    same_range_artifacts = artifacts_by_scenario.get("same_range_far_angles", {})
    same_range_pair_count = same_range_far_angle_pair_count(same_range_artifacts.get("selected_frontend_targets"))
    if same_range:
        gates.append(
            {
                "name": "same_range_far_angles_full_pipeline_selects_two_same_range_targets",
                "value": same_range_pair_count,
                "threshold": 1,
                "passed": bool(same_range_pair_count >= 1),
            }
        )
        gates.append(
            {
                "name": "same_range_far_angles_full_pipeline_rmse_le_0p10mm",
                "value": same_range["rmse_mm"],
                "threshold": 0.10,
                "passed": bool(same_range["rmse_mm"] <= 0.10),
            }
        )
    if same_range and same_range_range_only:
        ratio = float(same_range_range_only["rmse_mm"] / max(same_range["rmse_mm"], 1e-12))
        gates.append(
            {
                "name": "same_range_far_angles_full_pipeline_beats_range_bin_only_mixed_phase",
                "value": same_range["rmse_mm"],
                "threshold": same_range_range_only["rmse_mm"],
                "passed": bool(same_range["rmse_mm"] < same_range_range_only["rmse_mm"]),
            }
        )
        gates.append(
            {
                "name": "same_range_far_angles_range_bin_only_rmse_ge_1p25x_full_pipeline",
                "value": ratio,
                "threshold": 1.25,
                "passed": bool(ratio >= 1.25),
            }
        )
    if same_range and same_range_ma_style:
        gates.append(
            {
                "name": "same_range_far_angles_full_pipeline_beats_ma_style_iterative_beta_range_bin",
                "value": same_range["rmse_mm"],
                "threshold": same_range_ma_style["rmse_mm"],
                "passed": bool(same_range["rmse_mm"] < same_range_ma_style["rmse_mm"]),
            }
        )
    if same_range and same_range_ma2026:
        gates.append(
            {
                "name": "same_range_far_angles_full_pipeline_beats_ma2026_reproduction",
                "value": same_range["rmse_mm"],
                "threshold": same_range_ma2026["rmse_mm"],
                "passed": bool(same_range["rmse_mm"] < same_range_ma2026["rmse_mm"]),
            }
        )
    vehicle = full_pipeline_row(rows, "vehicle_event_nonstationary")
    if vehicle:
        gates.append(
            {
                "name": "vehicle_event_full_pipeline_selected_count_ge_1",
                "value": vehicle["selected_target_count"],
                "threshold": 1,
                "passed": bool(vehicle["selected_target_count"] >= 1),
            }
        )
        gates.append(
            {
                "name": "vehicle_event_full_pipeline_excludes_target4",
                "value": 0 if 4 not in vehicle["selected_indices"] else 1,
                "threshold": 0,
                "passed": bool(4 not in vehicle["selected_indices"]),
            }
        )
        gates.append(
            {
                "name": "vehicle_event_full_pipeline_unwrap_error_rate_eq_0",
                "value": vehicle["unwrap_error_rate"],
                "threshold": 0.0,
                "passed": bool(vehicle["unwrap_error_rate"] == 0.0),
            }
        )
        gates.append(
            {
                "name": "vehicle_event_full_pipeline_rmse_le_0p05mm",
                "value": vehicle["rmse_mm"],
                "threshold": 0.05,
                "passed": bool(vehicle["rmse_mm"] <= 0.05),
            }
        )
    snr_full = full_pipeline_row(rows, "target_snr_drop")
    snr_selected_fixed = row_lookup(rows, "target_snr_drop", "selected_aoa_fixed_kappa")
    if snr_full and snr_selected_fixed:
        gates.append(
            {
                "name": "target_snr_drop_full_pipeline_beats_selected_fixed_r",
                "value": snr_full["rmse_mm"],
                "threshold": snr_selected_fixed["rmse_mm"],
                "passed": bool(snr_full["rmse_mm"] < snr_selected_fixed["rmse_mm"]),
            }
        )
    low_snr = full_pipeline_row(rows, "low_snr_multitarget")
    if low_snr:
        gates.append(
            {
                "name": "low_snr_full_pipeline_selects_at_least_2_targets",
                "value": low_snr["selected_target_count"],
                "threshold": 2,
                "passed": bool(low_snr["selected_target_count"] >= 2),
            }
        )
    aoa = full_pipeline_row(rows, "aoa_error_bootstrap")
    if aoa:
        gates.append(
            {
                "name": "aoa_bootstrap_kappa_median_relative_error_le_0p05",
                "value": aoa.get("kappa_median_relative_error", 0.0),
                "threshold": 0.05,
                "passed": bool(aoa.get("kappa_median_relative_error", 0.0) <= 0.05),
            }
        )
    return gates
