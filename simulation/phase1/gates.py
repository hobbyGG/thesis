import numpy as np


def row_lookup(rows, scenario, method):
    for row in rows:
        if row["scenario"] == scenario and row["method"] == method:
            return row
    return None


def full_pipeline_row(rows, scenario):
    return (
        row_lookup(rows, scenario, "proposed_full_pipeline_beta_confidence")
        or row_lookup(rows, scenario, "proposed_full_pipeline_calibrated")
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
    strong_itoh = row_lookup(rows, "strong_wrapping", "range_bin_itoh")
    strong_full = full_pipeline_row(rows, "strong_wrapping")
    if strong_full and strong_itoh:
        gates.append(
            {
                "name": "strong_wrapping_full_pipeline_beats_range_bin_itoh",
                "value": strong_full["rmse_mm"],
                "threshold": strong_itoh["rmse_mm"],
                "passed": bool(strong_full["rmse_mm"] < strong_itoh["rmse_mm"]),
            }
        )
        ratio = float(strong_itoh["rmse_mm"] / max(strong_full["rmse_mm"], 1e-12))
        gates.append(
            {
                "name": "strong_wrapping_range_bin_itoh_rmse_ge_2x_full_pipeline",
                "value": ratio,
                "threshold": 2.0,
                "passed": bool(ratio >= 2.0),
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

    same_range = full_pipeline_row(rows, "same_range_far_angles")
    same_range_range_only = row_lookup(rows, "same_range_far_angles", "range_bin_only_mixed_phase")
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
    snr_full = full_pipeline_row(rows, "target_snr_drop")
    snr_selected_fixed = row_lookup(rows, "target_snr_drop", "selected_aoa_fixed_beta")
    if snr_full and snr_selected_fixed:
        gates.append(
            {
                "name": "target_snr_drop_full_pipeline_beats_selected_fixed_r",
                "value": snr_full["rmse_mm"],
                "threshold": snr_selected_fixed["rmse_mm"],
                "passed": bool(snr_full["rmse_mm"] < snr_selected_fixed["rmse_mm"]),
            }
        )
    aoa = full_pipeline_row(rows, "aoa_error_bootstrap")
    if aoa:
        gates.append(
            {
                "name": "aoa_bootstrap_beta_median_relative_error_le_0p10",
                "value": aoa.get("beta_median_relative_error", 0.0),
                "threshold": 0.10,
                "passed": bool(aoa.get("beta_median_relative_error", 0.0) <= 0.10),
            }
        )
    return gates
