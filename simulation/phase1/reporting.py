import csv
from html import escape
import json
from pathlib import Path

import numpy as np

from .algorithm import cold_start_reference_mean
from .beta_bootstrap_diagnostics import (
    DIAGNOSTIC_FIELDNAMES,
    beta_bootstrap_figure_title,
    beta_bootstrap_rows_from_result,
)


def _scale(values, lo, hi, size):
    if hi == lo:
        return [size / 2.0 for _ in values]
    return [size * (float(v) - lo) / (hi - lo) for v in values]


def _polyline(points, color):
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.5" />'


def write_basic_svg(path, t, series, title, x_label="", y_label=""):
    width = 960
    height = 430
    left = 84
    right = 26
    top = 46
    bottom = 66
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_values = []
    for _, values, _ in series:
        all_values.extend([float(v) for v in values if v == v])
    y_lo = min(all_values) if all_values else -1.0
    y_hi = max(all_values) if all_values else 1.0
    if y_hi == y_lo:
        pad = max(1.0, abs(y_hi) * 0.05)
        y_lo -= pad
        y_hi += pad
    else:
        pad = 0.05 * (y_hi - y_lo)
        y_lo -= pad
        y_hi += pad
    x = np.asarray(t, dtype=float)
    x_lo = float(x[0]) if x.size else 0.0
    x_hi = float(x[-1]) if x.size else 1.0
    if x_hi == x_lo:
        x_hi = x_lo + 1.0
    x_scaled = _scale(x, x_lo, x_hi, plot_w)
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />',
        f'<text x="{left}" y="24" font-size="16" font-family="Arial, sans-serif">{escape(title)}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#777" />',
    ]
    body.extend(_axis_elements(left, top, plot_w, plot_h, x_lo, x_hi, y_lo, y_hi, x_label, y_label))
    for label, values, color in series:
        y_scaled = _scale(values, y_lo, y_hi, plot_h)
        points = [(left + x_val, top + plot_h - y_val) for x_val, y_val in zip(x_scaled, y_scaled)]
        body.append(_polyline(points, color))
    body.extend(_legend_elements(left, top, plot_w, series))
    body.append("</svg>")
    path.write_text("\n".join(body))


def _axis_elements(left, top, plot_w, plot_h, x_lo, x_hi, y_lo, y_hi, x_label, y_label):
    elements = []
    tick_style = 'font-size="11" font-family="Arial, sans-serif" fill="#333"'
    axis_style = 'stroke="#333" stroke-width="1"'
    grid_style = 'stroke="#e6e6e6" stroke-width="1"'
    elements.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" {axis_style} />')
    elements.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" {axis_style} />')
    for tick in np.linspace(x_lo, x_hi, 6):
        x_pos = left + plot_w * (float(tick) - x_lo) / (x_hi - x_lo)
        elements.append(f'<line x1="{x_pos:.2f}" y1="{top}" x2="{x_pos:.2f}" y2="{top + plot_h}" {grid_style} />')
        elements.append(f'<line x1="{x_pos:.2f}" y1="{top + plot_h}" x2="{x_pos:.2f}" y2="{top + plot_h + 5}" {axis_style} />')
        elements.append(
            f'<text x="{x_pos:.2f}" y="{top + plot_h + 22}" text-anchor="middle" {tick_style}>{_format_tick(tick)}</text>'
        )
    for tick in np.linspace(y_lo, y_hi, 6):
        y_pos = top + plot_h - plot_h * (float(tick) - y_lo) / (y_hi - y_lo)
        elements.append(f'<line x1="{left}" y1="{y_pos:.2f}" x2="{left + plot_w}" y2="{y_pos:.2f}" {grid_style} />')
        elements.append(f'<line x1="{left - 5}" y1="{y_pos:.2f}" x2="{left}" y2="{y_pos:.2f}" {axis_style} />')
        elements.append(
            f'<text x="{left - 9}" y="{y_pos + 4:.2f}" text-anchor="end" {tick_style}>{_format_tick(tick)}</text>'
        )
    if x_label:
        elements.append(
            f'<text x="{left + plot_w / 2:.2f}" y="{top + plot_h + 48}" text-anchor="middle" '
            f'font-size="13" font-family="Arial, sans-serif">{escape(x_label)}</text>'
        )
    if y_label:
        elements.append(
            f'<text transform="translate(22 {top + plot_h / 2:.2f}) rotate(-90)" text-anchor="middle" '
            f'font-size="13" font-family="Arial, sans-serif">{escape(y_label)}</text>'
        )
    return elements


def _legend_elements(left, top, plot_w, series):
    elements = ['<g class="legend">']
    x0 = left + plot_w - 190
    y0 = top + 16
    for idx, (label, _, color) in enumerate(series):
        y = y0 + idx * 18
        elements.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + 22}" y2="{y}" stroke="{color}" stroke-width="2" />')
        elements.append(
            f'<text x="{x0 + 28}" y="{y + 4}" font-size="11" font-family="Arial, sans-serif">{escape(str(label))}</text>'
        )
    elements.append("</g>")
    return elements


def _format_tick(value):
    value = float(value)
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.3f}"


def _find_result(results, method_name):
    for result in results:
        if result.method_name == method_name:
            return result
    return None


def _preferred_full_pipeline_result(results):
    return (
        _find_result(results, "direct_aoa_fixed_beta")
        or _find_result(results, "proposed_full_pipeline_aoa_fixed_beta")
        or _find_result(results, "proposed_full_pipeline_beta_confidence")
        or _find_result(results, "proposed_full_pipeline_calibrated")
    )


def _target_colors():
    return ["#0066cc", "#cc5500", "#228833", "#aa3377", "#777777", "#ee7733", "#33bbee"]


def _write_beta_bootstrap_plot(plots_dir, artifacts):
    scenario = artifacts.get("aoa_error_bootstrap")
    if not scenario:
        return
    result = _preferred_full_pipeline_result(scenario["results"])
    if result is None:
        return
    beta_history = result.extra.get("beta_history")
    if beta_history is None:
        return
    radar = scenario["radar"]
    truth = scenario["truth"]
    references = np.asarray(scenario.get("target_reference_indices", []), dtype=int)
    diagnostic_rows = beta_bootstrap_rows_from_result(
        result,
        radar,
        target_reference_indices=references,
        scenario="aoa_error_bootstrap",
    )
    selected_indices = np.asarray(result.extra.get("selected_indices", np.arange(beta_history.shape[0])), dtype=int)
    series = []
    colors = _target_colors()
    for target_idx in selected_indices:
        if target_idx < 0 or target_idx >= beta_history.shape[0]:
            continue
        reference_idx = int(references[target_idx]) if target_idx < references.size else target_idx
        if reference_idx < 0 or reference_idx >= radar.beta.size:
            continue
        series.append((f"beta_hat_{target_idx}", beta_history[target_idx], colors[target_idx % len(colors)]))
        series.append(
            (
                f"beta_true_{target_idx}",
                np.full_like(truth.t, radar.beta[reference_idx], dtype=float),
                "#111111",
            )
        )
    write_basic_svg(
        plots_dir / "aoa_error_bootstrap_beta_bootstrap.svg",
        truth.t,
        series,
        f"aoa_error_bootstrap {result.method_name} {beta_bootstrap_figure_title(diagnostic_rows)}",
        x_label="Time (s)",
        y_label="LOS-to-structure conversion factor beta",
    )


def _write_adaptive_r_plot(plots_dir, artifacts):
    scenario = artifacts.get("target_snr_drop")
    if not scenario:
        return
    result = _preferred_full_pipeline_result(scenario["results"])
    if result is None:
        return
    truth = scenario["truth"]
    series = []
    colors = _target_colors()
    for target_idx in range(result.r_theta_history.shape[0]):
        series.append((f"r_{target_idx}", result.r_theta_history[target_idx], colors[target_idx % len(colors)]))
    write_basic_svg(
        plots_dir / "target_snr_drop_adaptive_r.svg",
        truth.t,
        series,
        f"target_snr_drop {result.method_name} adaptive R",
        x_label="Time (s)",
        y_label="Measurement variance R (rad^2)",
    )


def _write_phase_correction_plot(plots_dir, artifacts):
    scenario = artifacts.get("strong_wrapping")
    if not scenario:
        return
    result = _preferred_full_pipeline_result(scenario["results"])
    if result is None:
        return
    radar = scenario["radar"]
    radar_input = scenario.get("radar_input")
    truth = scenario["truth"]
    references = np.asarray(scenario.get("target_reference_indices", []), dtype=int)
    selected_indices = np.asarray(result.extra.get("selected_indices", [0]), dtype=int)
    target_idx = int(selected_indices[0]) if selected_indices.size else 0
    if target_idx < 0 or target_idx >= result.los_corrected_phase_rad.shape[0]:
        return
    corrected = result.los_corrected_phase_rad[target_idx]
    reference_idx = int(references[target_idx]) if target_idx < references.size else target_idx
    if reference_idx < 0 or reference_idx >= radar.true_los_phase_rad.shape[0]:
        return
    true_phase = radar.true_los_phase_rad[reference_idx]
    valid = np.isfinite(corrected) & np.isfinite(true_phase)
    if np.any(valid):
        offset = 2.0 * np.pi * np.round(np.median((corrected[valid] - true_phase[valid]) / (2.0 * np.pi)))
        true_phase = true_phase + offset
    wrapped = (
        radar_input.wrapped_phase_rad[target_idx]
        if radar_input is not None and target_idx < radar_input.wrapped_phase_rad.shape[0]
        else radar.wrapped_phase_rad[reference_idx]
    )
    series = [
        ("wrapped", wrapped, "#777777"),
        ("corrected", corrected, "#0066cc"),
        ("true_los_aligned", true_phase, "#111111"),
    ]
    write_basic_svg(
        plots_dir / "strong_wrapping_phase_correction.svg",
        truth.t,
        series,
        f"strong_wrapping {result.method_name} phase correction target {target_idx}",
        x_label="Time (s)",
        y_label="LoS phase (rad)",
    )


def _write_diagnostic_plots(plots_dir, artifacts):
    _write_beta_bootstrap_plot(plots_dir, artifacts)
    _write_adaptive_r_plot(plots_dir, artifacts)
    _write_phase_correction_plot(plots_dir, artifacts)


def _beta_bootstrap_diagnostic_rows(artifacts):
    rows = []
    for scenario_name in sorted(artifacts):
        scenario = artifacts[scenario_name]
        result = _preferred_full_pipeline_result(scenario.get("results", []))
        radar = scenario.get("radar")
        if result is None or radar is None:
            continue
        references = np.asarray(scenario.get("target_reference_indices", []), dtype=int)
        rows.extend(
            beta_bootstrap_rows_from_result(
                result,
                radar,
                target_reference_indices=references,
                scenario=scenario_name,
            )
        )
    return rows


def _write_beta_bootstrap_diagnostics_csv(path, artifacts):
    rows = _beta_bootstrap_diagnostic_rows(artifacts)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DIAGNOSTIC_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in DIAGNOSTIC_FIELDNAMES})


FRONTEND_AOA_DIAGNOSTIC_FIELDNAMES = [
    "scenario",
    "target_idx",
    "reference_idx",
    "range_bin",
    "angle_bin",
    "true_angle_deg",
    "measured_angle_deg",
    "angle_error_deg",
    "true_beta",
    "measured_beta",
    "beta_initial_relative_error",
]


def _write_frontend_aoa_diagnostics_csv(path, artifacts):
    rows = []
    for scenario_name in sorted(artifacts):
        for row in artifacts[scenario_name].get("frontend_aoa_diagnostics", []):
            enriched = {"scenario": scenario_name}
            enriched.update(row)
            rows.append(enriched)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FRONTEND_AOA_DIAGNOSTIC_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FRONTEND_AOA_DIAGNOSTIC_FIELDNAMES})


def write_validation_report(summary, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics_csv = output / "metrics.csv"
    beta_diagnostics_csv = output / "beta_bootstrap_diagnostics.csv"
    frontend_aoa_diagnostics_csv = output / "frontend_aoa_diagnostics.csv"
    gates_json = output / "feasibility_gates.json"
    summary_md = output / "summary.md"

    rows = summary["rows"]
    fieldnames = [
        "scenario",
        "scenario_label_zh",
        "validation_purpose_zh",
        "validation_focus_zh",
        "paper_section_zh",
        "method",
        "rmse_mm",
        "mae_mm",
        "max_error_mm",
        "theta_rmse_rad",
        "unwrap_errors",
        "selected_target_count",
        "selected_indices",
        "corrected_observation_count",
        "unwrap_error_rate",
        "beta_median_relative_error",
        "beta_initial_median_relative_error",
        "beta_improvement_ratio",
    ]
    with metrics_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    with gates_json.open("w") as f:
        json.dump(summary["gates"], f, indent=2)

    artifacts = summary.get("artifacts", {})
    _write_beta_bootstrap_diagnostics_csv(beta_diagnostics_csv, artifacts)
    _write_frontend_aoa_diagnostics_csv(frontend_aoa_diagnostics_csv, artifacts)

    with summary_md.open("w") as f:
        f.write("# Phase 1 Simulation Validation Summary\n\n")
        f.write("## Feasibility Gates\n\n")
        for gate in summary["gates"]:
            status = "PASS" if gate["passed"] else "FAIL"
            f.write(f"- {status}: {gate['name']} value={gate['value']} threshold={gate['threshold']}\n")
        f.write("\n## Metrics\n\n")
        f.write(
            "| Scenario | 中文场景 | 验证目的 | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors | "
            "Selected | Selected Indices | Corrected Obs | Unwrap Error Rate | Beta Rel Err | Beta Initial Rel Err | "
            "Beta Improvement Ratio |\n"
        )
        f.write("|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|\n")
        for row in rows:
            beta_error = row.get("beta_median_relative_error", float("nan"))
            beta_text = "" if beta_error != beta_error else f"{beta_error:.6f}"
            beta_initial_error = row.get("beta_initial_median_relative_error", float("nan"))
            beta_initial_text = "" if beta_initial_error != beta_initial_error else f"{beta_initial_error:.6f}"
            beta_improvement = row.get("beta_improvement_ratio", float("nan"))
            beta_improvement_text = "" if beta_improvement != beta_improvement else f"{beta_improvement:.6f}"
            f.write(
                f"| {row['scenario']} | {row.get('scenario_label_zh', '')} | "
                f"{row.get('validation_purpose_zh', '')} | {row['method']} | "
                f"{row['rmse_mm']:.6f} | {row['mae_mm']:.6f} | "
                f"{row['max_error_mm']:.6f} | {row['unwrap_errors']} | "
                f"{row.get('selected_target_count', '')} | {row.get('selected_indices', '')} | "
                f"{row.get('corrected_observation_count', '')} | "
                f"{row.get('unwrap_error_rate', 0.0):.6f} | {beta_text} | "
                f"{beta_initial_text} | {beta_improvement_text} |\n"
            )

    plots_dir = output / "plots"
    plots_dir.mkdir(exist_ok=True)
    for stale_svg in plots_dir.glob("*.svg"):
        stale_svg.unlink()
    if artifacts:
        first_name = sorted(artifacts.keys())[0]
        first = artifacts[first_name]
        truth = first["truth"]
        scenario = first["scenario"]
        results = first["results"]
        selected = [
            res
            for res in results
            if res.method_name
            in (
                "range_bin_itoh",
                "range_bin_only_mixed_phase",
                "selected_aoa_fixed_beta",
                "direct_aoa_fixed_beta",
                "proposed_full_pipeline_aoa_fixed_beta",
                "proposed_full_pipeline_beta_confidence",
            )
            or res.method_name == "ma2026_reproduction"
        ]
        q_ref = cold_start_reference_mean(truth.q_m, scenario)
        series = [("truth", (truth.q_m - q_ref) * 1e3, "#111111")]
        colors = {
            "range_bin_itoh": "#cc5500",
            "range_bin_only_mixed_phase": "#777777",
            "ma2026_reproduction": "#ddaa33",
            "selected_aoa_fixed_beta": "#aa3377",
            "direct_aoa_fixed_beta": "#117733",
            "proposed_full_pipeline_aoa_fixed_beta": "#4477aa",
            "proposed_full_pipeline_beta_confidence": "#009988",
        }
        for res in selected:
            series.append((res.method_name, res.q_hat_m * 1e3, colors[res.method_name]))
        write_basic_svg(
            plots_dir / f"{first_name}_displacement.svg",
            truth.t,
            series,
            f"{first_name} displacement",
            x_label="Time (s)",
            y_label="Relative displacement (mm)",
        )
        _write_diagnostic_plots(plots_dir, artifacts)

    return {
        "metrics_csv": metrics_csv,
        "beta_diagnostics_csv": beta_diagnostics_csv,
        "frontend_aoa_diagnostics_csv": frontend_aoa_diagnostics_csv,
        "gates_json": gates_json,
        "summary_md": summary_md,
        "plots_dir": plots_dir,
    }
