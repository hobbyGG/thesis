import csv
import json
from pathlib import Path


def _scale(values, lo, hi, size):
    if hi == lo:
        return [size / 2.0 for _ in values]
    return [size * (float(v) - lo) / (hi - lo) for v in values]


def _polyline(points, color):
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.5" />'


def write_basic_svg(path, t, series, title):
    width = 900
    height = 360
    margin = 40
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    all_values = []
    for _, values, _ in series:
        all_values.extend([float(v) for v in values if v == v])
    y_lo = min(all_values) if all_values else -1.0
    y_hi = max(all_values) if all_values else 1.0
    x_scaled = _scale(t, float(t[0]), float(t[-1]), plot_w)
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<text x="{margin}" y="24" font-size="16">{title}</text>',
        f'<rect x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#888" />',
    ]
    for label, values, color in series:
        del label
        y_scaled = _scale(values, y_lo, y_hi, plot_h)
        points = [(margin + x, margin + plot_h - y) for x, y in zip(x_scaled, y_scaled)]
        body.append(_polyline(points, color))
    body.append("</svg>")
    path.write_text("\n".join(body))


def write_validation_report(summary, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics_csv = output / "metrics.csv"
    gates_json = output / "feasibility_gates.json"
    summary_md = output / "summary.md"

    rows = summary["rows"]
    fieldnames = ["scenario", "method", "rmse_mm", "mae_mm", "max_error_mm", "theta_rmse_rad", "unwrap_errors"]
    with metrics_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    with gates_json.open("w") as f:
        json.dump(summary["gates"], f, indent=2)

    with summary_md.open("w") as f:
        f.write("# Phase 1 Simulation Validation Summary\n\n")
        f.write("## Feasibility Gates\n\n")
        for gate in summary["gates"]:
            status = "PASS" if gate["passed"] else "FAIL"
            f.write(f"- {status}: {gate['name']} value={gate['value']} threshold={gate['threshold']}\n")
        f.write("\n## Metrics\n\n")
        f.write("| Scenario | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for row in rows:
            f.write(
                f"| {row['scenario']} | {row['method']} | "
                f"{row['rmse_mm']:.6f} | {row['mae_mm']:.6f} | "
                f"{row['max_error_mm']:.6f} | {row['unwrap_errors']} |\n"
            )

    plots_dir = output / "plots"
    plots_dir.mkdir(exist_ok=True)
    artifacts = summary.get("artifacts", {})
    if artifacts:
        first_name = sorted(artifacts.keys())[0]
        first = artifacts[first_name]
        truth = first["truth"]
        results = first["results"]
        selected = [res for res in results if res.method_name in ("single_target_ma_style", "proposed")]
        series = [("truth", truth.q_m * 1e3, "#111111")]
        colors = {"single_target_ma_style": "#cc5500", "proposed": "#0066cc"}
        for res in selected:
            series.append((res.method_name, res.q_hat_m * 1e3, colors[res.method_name]))
        write_basic_svg(plots_dir / f"{first_name}_displacement.svg", truth.t, series, f"{first_name} displacement")

    return {"metrics_csv": metrics_csv, "gates_json": gates_json, "summary_md": summary_md, "plots_dir": plots_dir}
