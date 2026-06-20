import csv
from pathlib import Path

import numpy as np

from .algorithm import cold_start_reference_mean
from .reporting import write_basic_svg
from .scenario_catalog import scenario_metadata_fields
from .truth import generate_truth_signal


_INTERVALS = (
    ("quiet", 0.0, 0.20),
    ("micro", 0.20, 0.80),
    ("ramp", 0.80, 1.40),
    ("main_response", 1.40, None),
)


def scenario_parameter_rows(scenarios):
    rows = []
    for scenario in scenarios:
        truth = generate_truth_signal(scenario)
        q_ref = cold_start_reference_mean(truth.q_m, scenario)
        q_rel_m = truth.q_m - q_ref
        q_mm = q_rel_m * 1.0e3
        row = {
            "scenario": scenario.scenario_name,
            **scenario_metadata_fields(scenario.scenario_name),
            "duration_s": float(scenario.duration_s),
            "sample_rate_hz": float(scenario.sample_rate_hz),
            "motion_profile": scenario.motion_profile,
            "truth_peak_displacement_mm": _optional_float(scenario.truth_peak_displacement_mm),
            "peak_displacement_mm": _nanmax_abs(q_mm),
            "peak_to_peak_displacement_mm": _peak_to_peak(q_mm),
            "max_frame_step_mm": _max_frame_step(q_mm),
            "nominal_frequencies_hz": _join_numbers(scenario.nominal_frequencies_hz),
            "generated_frequencies_hz": _join_numbers(truth.frequencies_hz),
            "dominant_displacement_frequencies_hz": _join_numbers(
                dominant_frequencies_hz(q_rel_m, scenario.sample_rate_hz)
            ),
            "target_angles_deg": _join_numbers(scenario.target_angles_deg),
            "target_snr_db": _join_numbers(scenario.target_snr_db),
            "target_range_bins": _join_numbers(scenario.target_range_bins),
            "num_targets": int(scenario.num_targets),
            "carrier_frequency_hz": float(scenario.carrier_frequency_hz),
            "adc_sample_rate_hz": float(scenario.adc_sample_rate_hz),
            "adc_samples_per_chirp": int(scenario.adc_samples_per_chirp),
            "chirp_duration_s": float(scenario.chirp_duration_s),
            "chirps_per_frame": int(scenario.chirps_per_frame),
            "aoa_error_deg": float(scenario.aoa_error_deg),
            "degraded_target_indices": _join_numbers(scenario.degraded_target_indices),
            "dropout_target_indices": _join_numbers(scenario.dropout_target_indices),
        }
        for name, start_s, end_s in _INTERVALS:
            mask = _interval_mask(truth.t, start_s, end_s)
            row[f"{name}_peak_mm"] = _nanmax_abs(q_mm[mask])
        rows.append(row)
    return rows


def write_scenario_diagnostics(scenarios, output_dir):
    output = Path(output_dir)
    plots_dir = output / "plots"
    output.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = scenario_parameter_rows(scenarios)
    parameters_csv = output / "scenario_parameters.csv"
    _write_parameter_csv(parameters_csv, rows)

    for scenario in scenarios:
        _write_scenario_plots(plots_dir, scenario)

    summary_md = output / "summary.md"
    _write_summary_md(summary_md, rows, plots_dir)

    return {
        "parameters_csv": parameters_csv,
        "summary_md": summary_md,
        "plots_dir": plots_dir,
    }


def dominant_frequencies_hz(values, sample_rate_hz, count=3, min_hz=0.05):
    values = np.asarray(values, dtype=float)
    if values.size < 3:
        return []
    centered = values - np.nanmean(values)
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    freqs = np.fft.rfftfreq(values.size, d=1.0 / float(sample_rate_hz))
    amp = np.abs(spectrum)
    valid = freqs >= float(min_hz)
    if not np.any(valid):
        return []
    indices = np.flatnonzero(valid)
    indices = indices[np.argsort(amp[indices])[::-1]]
    return [round(float(freqs[idx]), 3) for idx in indices[: int(count)]]


def _write_scenario_plots(plots_dir, scenario):
    truth = generate_truth_signal(scenario)
    q_ref = cold_start_reference_mean(truth.q_m, scenario)
    q_mm = (truth.q_m - q_ref) * 1.0e3
    accel = truth.a_mps2

    write_basic_svg(
        plots_dir / f"{scenario.scenario_name}_time_displacement.svg",
        truth.t,
        [("relative displacement", q_mm, "#0066cc")],
        f"{scenario.scenario_name} time-domain displacement",
        x_label="Time (s)",
        y_label="Relative displacement (mm)",
    )
    write_basic_svg(
        plots_dir / f"{scenario.scenario_name}_time_acceleration.svg",
        truth.t,
        [("acceleration", accel, "#228833")],
        f"{scenario.scenario_name} time-domain acceleration",
        x_label="Time (s)",
        y_label="Acceleration (m/s^2)",
    )

    f_q, a_q = _single_sided_spectrum(q_mm, scenario.sample_rate_hz)
    f_a, a_a = _single_sided_spectrum(accel, scenario.sample_rate_hz)
    max_hz = _frequency_plot_max_hz(scenario)
    q_mask = f_q <= max_hz
    a_mask = f_a <= max_hz
    write_basic_svg(
        plots_dir / f"{scenario.scenario_name}_frequency_displacement.svg",
        f_q[q_mask],
        [("displacement amplitude", a_q[q_mask], "#0066cc")],
        f"{scenario.scenario_name} displacement spectrum",
        x_label="Frequency (Hz)",
        y_label="Amplitude (mm)",
    )
    write_basic_svg(
        plots_dir / f"{scenario.scenario_name}_frequency_acceleration.svg",
        f_a[a_mask],
        [("acceleration amplitude", a_a[a_mask], "#228833")],
        f"{scenario.scenario_name} acceleration spectrum",
        x_label="Frequency (Hz)",
        y_label="Amplitude (m/s^2)",
    )


def _frequency_plot_max_hz(scenario):
    limit_hz = 120.0 if scenario.motion_profile == "measured_bridge" else 30.0
    return min(0.5 * float(scenario.sample_rate_hz), limit_hz)


def _single_sided_spectrum(values, sample_rate_hz):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.asarray([0.0]), np.asarray([0.0])
    centered = arr - np.nanmean(arr)
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    freqs = np.fft.rfftfreq(arr.size, d=1.0 / float(sample_rate_hz))
    amp = 2.0 * np.abs(spectrum) / max(1, arr.size)
    if amp.size:
        amp[0] *= 0.5
    return freqs, amp


def _write_parameter_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_summary_md(path, rows, plots_dir):
    lines = [
        "# Phase 1 Scenario Diagnostics",
        "",
        "## Parameter Summary",
        "",
        "| Scenario | 中文场景 | 验证目的 | Profile | Duration s | fs Hz | Peak mm | Quiet mm | Micro mm | Ramp mm | Main mm | Dominant Hz |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['scenario_label_zh']} | {row['validation_purpose_zh']} | "
            f"{row['motion_profile']} | {row['duration_s']:.2f} | "
            f"{row['sample_rate_hz']:.1f} | {row['peak_displacement_mm']:.3f} | "
            f"{row['quiet_peak_mm']:.3f} | {row['micro_peak_mm']:.3f} | "
            f"{row['ramp_peak_mm']:.3f} | {row['main_response_peak_mm']:.3f} | "
            f"{row['dominant_displacement_frequencies_hz']} |"
        )
    lines.extend(["", "## Plots", ""])
    for row in rows:
        scenario = row["scenario"]
        lines.extend(
            [
                f"### {scenario}",
                "",
                f"- [time displacement](plots/{scenario}_time_displacement.svg)",
                f"- [time acceleration](plots/{scenario}_time_acceleration.svg)",
                f"- [frequency displacement](plots/{scenario}_frequency_displacement.svg)",
                f"- [frequency acceleration](plots/{scenario}_frequency_acceleration.svg)",
                "",
            ]
        )
    del plots_dir
    path.write_text("\n".join(lines))


def _interval_mask(t, start_s, end_s):
    arr = np.asarray(t, dtype=float)
    mask = arr >= float(start_s)
    if end_s is not None:
        mask &= arr < float(end_s)
    return mask


def _nanmax_abs(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or not np.any(np.isfinite(arr)):
        return float("nan")
    return float(np.nanmax(np.abs(arr)))


def _peak_to_peak(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or not np.any(np.isfinite(arr)):
        return float("nan")
    return float(np.nanmax(arr) - np.nanmin(arr))


def _max_frame_step(values):
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return 0.0
    return float(np.nanmax(np.abs(np.diff(arr))))


def _join_numbers(values):
    return ";".join(f"{float(value):g}" for value in values)


def _optional_float(value):
    if value is None:
        return ""
    return float(value)
