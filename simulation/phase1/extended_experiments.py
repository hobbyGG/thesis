import csv
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import numpy as np

from .evaluate import evaluate_scenario
from .method_registry import all_method_specs
from .scenario_catalog import scenario_metadata_fields
from .scenarios import build_all_phase1_scenarios


SCENARIO_METADATA_FIELDS = [
    "scenario_label_zh",
    "validation_purpose_zh",
    "validation_focus_zh",
    "paper_section_zh",
]

PAPER_METHODS = (
    "range_bin_only_mixed_phase",
    "ma2026_reproduction",
    "selected_aoa_fixed_beta",
    "proposed_full_pipeline_beta_confidence",
)

ABLATION_METHODS = (
    "range_bin_only_mixed_phase",
    "ma2026_reproduction",
    "multitarget_aoa_fixed_beta",
    "selected_aoa_fixed_beta",
    "proposed_full_pipeline_beta_confidence",
)

FRONTEND_SENSITIVITY_METHODS = (
    "selected_aoa_fixed_beta",
    "proposed_full_pipeline_beta_confidence",
)

SNR_SENSITIVITY_METHODS = (
    "range_bin_itoh",
    "ma2026_reproduction",
    "selected_aoa_fixed_beta",
    "proposed_full_pipeline_beta_confidence",
)


def run_extended_experiments(
    seeds=(2026, 2027, 2028, 2029, 2030),
    monte_carlo_scenarios=(
        "literature_maglev_modal_response",
        "strong_wrapping",
        "same_range_far_angles",
        "aoa_error_bootstrap",
        "target_snr_drop",
    ),
    ablation_scenarios=(
        "same_range_far_angles",
        "literature_mmwbats_same_range_aliasing",
        "literature_mmshm_adjacent_range_clutter",
        "target_snr_drop",
        "aoa_error_bootstrap",
    ),
    frontend_angle_bins=(32, 48, 64, 96, 128),
    snr_floors_db=(4.0, 6.0, 8.0, 10.0, 12.0),
):
    """Run paper-oriented Phase-1 extended experiments."""

    scenario_by_name = _scenario_lookup()
    seed_values = tuple(int(seed) for seed in seeds)
    if not seed_values:
        raise ValueError("seeds must contain at least one value")
    reference_seed = seed_values[0]

    monte_carlo_rows = []
    method_specs = all_method_specs()
    for scenario_name in monte_carlo_scenarios:
        base = scenario_by_name[scenario_name]
        for seed in seed_values:
            scenario = replace(base, seed=int(seed))
            rows, _ = evaluate_scenario(scenario, method_specs=method_specs)
            for row in _filter_methods(rows, _paper_methods_for_scenario(scenario_name)):
                monte_carlo_rows.append(_prefixed_row(row, seed=int(seed)))

    monte_carlo_summary_rows = _aggregate_monte_carlo(monte_carlo_rows)

    ablation_rows = []
    for scenario_name in ablation_scenarios:
        scenario = replace(scenario_by_name[scenario_name], seed=reference_seed)
        rows, _ = evaluate_scenario(scenario, method_specs=method_specs)
        for row in _filter_methods(rows, _ablation_methods_for_scenario(scenario_name)):
            ablation_rows.append(_prefixed_row(row, seed=reference_seed))

    sensitivity_frontend_rows = []
    frontend_base = scenario_by_name["aoa_error_bootstrap"]
    for angle_bins in frontend_angle_bins:
        scenario = replace(
            frontend_base,
            seed=reference_seed,
            aoa_error_deg=0.0,
            frontend_num_angle_bins=int(angle_bins),
        )
        rows, _ = evaluate_scenario(scenario, method_specs=method_specs)
        for row in _filter_methods(rows, FRONTEND_SENSITIVITY_METHODS):
            enriched = _prefixed_row(row, seed=reference_seed)
            enriched["frontend_num_virtual_rx"] = int(scenario.frontend_num_virtual_rx)
            enriched["frontend_num_angle_bins"] = int(scenario.frontend_num_angle_bins)
            enriched["frontend_angle_window"] = str(scenario.frontend_angle_window)
            enriched["aoa_error_deg"] = float(scenario.aoa_error_deg)
            sensitivity_frontend_rows.append(enriched)

    sensitivity_snr_rows = []
    snr_base = scenario_by_name["target_snr_drop"]
    for snr_floor in snr_floors_db:
        target_snr_db = tuple(float(snr_floor) + offset for offset in (8.0, 6.0, 4.0, 2.0, 0.0))
        scenario = replace(snr_base, seed=reference_seed, target_snr_db=target_snr_db)
        rows, _ = evaluate_scenario(scenario, method_specs=method_specs)
        for row in _filter_methods(rows, SNR_SENSITIVITY_METHODS):
            enriched = _prefixed_row(row, seed=reference_seed)
            enriched["snr_floor_db"] = float(snr_floor)
            enriched["target_snr_db"] = ";".join(f"{item:.1f}" for item in target_snr_db)
            sensitivity_snr_rows.append(enriched)

    return {
        "monte_carlo_rows": monte_carlo_rows,
        "monte_carlo_summary_rows": monte_carlo_summary_rows,
        "ablation_rows": ablation_rows,
        "sensitivity_frontend_rows": sensitivity_frontend_rows,
        "sensitivity_snr_rows": sensitivity_snr_rows,
        "metadata": {
            "seeds": list(seed_values),
            "monte_carlo_scenarios": list(monte_carlo_scenarios),
            "ablation_scenarios": list(ablation_scenarios),
            "frontend_angle_bins": [int(item) for item in frontend_angle_bins],
            "snr_floors_db": [float(item) for item in snr_floors_db],
        },
    }


def write_extended_experiment_report(summary, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "monte_carlo_csv": output / "monte_carlo_metrics.csv",
        "monte_carlo_summary_csv": output / "monte_carlo_summary.csv",
        "ablation_csv": output / "ablation_summary.csv",
        "sensitivity_frontend_csv": output / "sensitivity_frontend.csv",
        "sensitivity_snr_csv": output / "sensitivity_snr.csv",
        "summary_md": output / "extended_summary.md",
    }

    metric_fields = [
        "seed",
        "scenario",
        *SCENARIO_METADATA_FIELDS,
        "method",
        "rmse_mm",
        "mae_mm",
        "max_error_mm",
        "unwrap_error_rate",
        "selected_target_count",
        "selected_indices",
        "beta_median_relative_error",
    ]
    _write_csv(paths["monte_carlo_csv"], summary["monte_carlo_rows"], metric_fields)
    _write_csv(
        paths["monte_carlo_summary_csv"],
        summary["monte_carlo_summary_rows"],
        [
            "scenario",
            *SCENARIO_METADATA_FIELDS,
            "method",
            "n",
            "rmse_mean_mm",
            "rmse_std_mm",
            "rmse_min_mm",
            "rmse_max_mm",
            "unwrap_error_rate_mean",
            "selected_target_count_mean",
        ],
    )
    _write_csv(paths["ablation_csv"], summary["ablation_rows"], metric_fields)
    _write_csv(
        paths["sensitivity_frontend_csv"],
        summary["sensitivity_frontend_rows"],
        ["frontend_num_virtual_rx", "frontend_num_angle_bins", "frontend_angle_window", "aoa_error_deg"] + metric_fields,
    )
    _write_csv(
        paths["sensitivity_snr_csv"],
        summary["sensitivity_snr_rows"],
        ["snr_floor_db", "target_snr_db"] + metric_fields,
    )
    _write_extended_summary_markdown(paths["summary_md"], summary)

    return paths


def _scenario_lookup():
    return {scenario.scenario_name: scenario for scenario in build_all_phase1_scenarios()}


def _filter_methods(rows, methods):
    method_set = set(methods)
    return [row for row in rows if row["method"] in method_set]


def _paper_methods_for_scenario(scenario_name):
    if scenario_name == "same_range_far_angles":
        return PAPER_METHODS
    return tuple(
        method
        for method in PAPER_METHODS
        if method != "range_bin_only_mixed_phase"
    )


def _ablation_methods_for_scenario(scenario_name):
    if scenario_name == "same_range_far_angles":
        return ABLATION_METHODS
    return tuple(
        method
        for method in ABLATION_METHODS
        if method != "range_bin_only_mixed_phase"
    )


def _prefixed_row(row, seed):
    metadata = scenario_metadata_fields(row["scenario"])
    for field in SCENARIO_METADATA_FIELDS:
        if field in row:
            metadata[field] = row[field]
    result = {
        "seed": int(seed),
        "scenario": row["scenario"],
        **metadata,
        "method": row["method"],
        "rmse_mm": float(row["rmse_mm"]),
        "mae_mm": float(row["mae_mm"]),
        "max_error_mm": float(row["max_error_mm"]),
        "unwrap_error_rate": float(row.get("unwrap_error_rate", 0.0)),
        "selected_target_count": int(row.get("selected_target_count", 0)),
        "selected_indices": row.get("selected_indices", []),
        "beta_median_relative_error": row.get("beta_median_relative_error", float("nan")),
    }
    return result


def _aggregate_monte_carlo(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["scenario"], row["method"])].append(row)

    summary_rows = []
    for (scenario_name, method_name), group_rows in sorted(groups.items()):
        first = group_rows[0]
        rmse = np.asarray([float(row["rmse_mm"]) for row in group_rows], dtype=float)
        unwrap = np.asarray([float(row["unwrap_error_rate"]) for row in group_rows], dtype=float)
        selected = np.asarray([float(row["selected_target_count"]) for row in group_rows], dtype=float)
        summary_rows.append(
            {
                "scenario": scenario_name,
                **{field: first.get(field, scenario_metadata_fields(scenario_name)[field]) for field in SCENARIO_METADATA_FIELDS},
                "method": method_name,
                "n": int(rmse.size),
                "rmse_mean_mm": float(np.mean(rmse)),
                "rmse_std_mm": float(np.std(rmse, ddof=1)) if rmse.size > 1 else 0.0,
                "rmse_min_mm": float(np.min(rmse)),
                "rmse_max_mm": float(np.max(rmse)),
                "unwrap_error_rate_mean": float(np.mean(unwrap)),
                "selected_target_count_mean": float(np.mean(selected)),
            }
        )
    return summary_rows


def _write_csv(path, rows, fieldnames):
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fieldnames})


def _csv_value(value):
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    if isinstance(value, float) and value != value:
        return ""
    return value


def _write_extended_summary_markdown(path, summary):
    with Path(path).open("w") as f:
        f.write("# Phase 1 Extended Experiment Summary\n\n")
        metadata = summary.get("metadata", {})
        f.write("## Metadata\n\n")
        f.write(f"- Seeds: {metadata.get('seeds', [])}\n")
        f.write(f"- Monte Carlo scenarios: {metadata.get('monte_carlo_scenarios', [])}\n")
        f.write(f"- Frontend angle FFT bins: {metadata.get('frontend_angle_bins', [])}\n")
        f.write(f"- SNR floor levels: {metadata.get('snr_floors_db', [])}\n\n")

        f.write("## Monte Carlo Summary\n\n")
        _write_markdown_table(
            f,
            summary["monte_carlo_summary_rows"],
            ["scenario_label_zh", "validation_purpose_zh", "method", "n", "rmse_mean_mm", "rmse_std_mm"],
            max_rows=30,
        )

        f.write("\n## Ablation Summary\n\n")
        _write_markdown_table(
            f,
            summary["ablation_rows"],
            ["scenario_label_zh", "validation_purpose_zh", "method", "rmse_mm", "unwrap_error_rate", "selected_target_count"],
            max_rows=40,
        )

        f.write("\n## Frontend Angle FFT Sensitivity\n\n")
        _write_markdown_table(
            f,
            summary["sensitivity_frontend_rows"],
            [
                "scenario_label_zh",
                "frontend_num_virtual_rx",
                "frontend_num_angle_bins",
                "method",
                "rmse_mm",
                "beta_median_relative_error",
            ],
            max_rows=40,
        )

        f.write("\n## SNR Sensitivity\n\n")
        _write_markdown_table(
            f,
            summary["sensitivity_snr_rows"],
            ["scenario_label_zh", "snr_floor_db", "method", "rmse_mm", "selected_target_count"],
            max_rows=40,
        )


def _write_markdown_table(f, rows, fields, max_rows=None):
    f.write("| " + " | ".join(fields) + " |\n")
    f.write("|" + "|".join("---" for _ in fields) + "|\n")
    for row in rows[:max_rows]:
        values = [_markdown_value(row.get(field, "")) for field in fields]
        f.write("| " + " | ".join(values) + " |\n")
    if max_rows is not None and len(rows) > max_rows:
        f.write(f"\nShowing first {max_rows} of {len(rows)} rows. See CSV files for full tables.\n")


def _markdown_value(value):
    if isinstance(value, float):
        if value != value:
            return ""
        return f"{value:.6f}"
    return str(value)
