"""Monte-Carlo experiments on the simulated guideway scene.

    python -m experiments.sweep smoke    # development seeds, every code path (about a minute)
    python -m experiments.sweep tune     # free parameters on the development seeds
    python -m experiments.sweep test     # held-out seeds; refuses to overwrite without --rerun
    python -m experiments.sweep report   # tables in results/summary.md

Seed sets are disjoint.  Development seeds (1000-1009) are free to inspect and
are the only ones used for tuning and debugging.  The held-out seeds are run
once: 6000-6039 for the randomised ensemble (each seed is one random scene,
structure and set of sensor errors) and 5000-5007 for the one-factor
sensitivity study around the nominal scene.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, fields, replace
from pathlib import Path

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np

from experiments import stats
from experiments.front import load_front, radar_impairments
from experiments.methods import (
    METHODS, Tuned, acceleration_input, event_window, kalman, phase_observer,
    prepare_radar, radar_phase_series, run_methods, score, without_adxl,
)
from paper_bridge_simulation.ensemble import draw_case
from paper_bridge_simulation.package_builder import adxl_samples
from paper_bridge_simulation.response import DYNAMIC_ACCELERATION_PEAK_MPS2, PEAK_DEFLECTION_M
from paper_bridge_simulation.scenario import Impairments, Scenario

RESULTS = Path(__file__).parent / "results"
DURATION_S = 4.0
DEV_SEEDS = tuple(range(1000, 1010))
SENSITIVITY_SEEDS = tuple(range(5000, 5008))
ENSEMBLE_SEEDS = tuple(range(6000, 6040))
Q_GRID = (1.0, 3.0, 1.0e1, 3.0e1, 1.0e2, 3.0e2, 1.0e3, 3.0e3, 1.0e4)
R_GRID = (1.0e-4, 1.0e-3, 1.0e-2, 1.0e-1)
CORNER_GRID = (0.3, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
# Failed runs enter the tuning objective at this event RMSE.
TUNING_CAP_UM = 2000.0
# A dropout starts at a random frame inside the passage of the nominal scene.
DROPOUT_START_RANGE_S = (0.5, 1.26)
FIELDS = (
    "part", "group", "value", "seed", "method", "rmse_um", "event_rmse_um",
    "max_err_um", "failed", "n_selected", "c_over_r", "error",
)


@dataclass(frozen=True)
class Condition:
    group: str
    value: float
    scenario: Scenario
    impairments: Impairments
    dropout_s: float = 0.0


NOMINAL = Scenario()
# Value of each group's parameter that equals the nominal scene.
NEUTRAL = {
    "snr_offset_db": 0.0, "iq_offset_ratio": 0.0, "sway_2_targets_um": 0.0, "sway_5_targets_um": 0.0,
    "peak_deflection_mm": PEAK_DEFLECTION_M * 1.0e3, "adxl_timing_offset_ms": 0.0,
    "adxl_clock_phase_ms": 0.0, "adxl_noise_scale": 1.0, "adxl_bias_walk": 0.0,
    "adxl_tilt_gain": 0.0, "adxl_scale_error": 0.0, "radar_dropout_ms": 0.0,
}


def sensitivity_conditions() -> list[Condition]:
    """One factor at a time around the nominal scene (the nominal case comes first)."""
    base = Impairments()
    small = replace(
        NOMINAL, peak_deflection_m=0.3e-3,
        dynamic_acceleration_peak_mps2=DYNAMIC_ACCELERATION_PEAK_MPS2 * 0.3e-3 / PEAK_DEFLECTION_M,
    )
    sway = {"target_sway_std_m": 30.0e-6}
    conditions = [Condition("nominal", 0.0, NOMINAL, base)]
    conditions += [Condition("snr_offset_db", v, NOMINAL, replace(base, snr_offset_db=v)) for v in (-10.0, -20.0)]
    conditions += [Condition("iq_offset_ratio", v, NOMINAL, replace(base, iq_offset_ratio=v)) for v in (0.03, 0.1, 0.3, 1.0)]
    conditions += [
        Condition("sway_2_targets_um", 30.0, NOMINAL, replace(base, **sway, target_sway_targets=(0, 4))),
        Condition("sway_5_targets_um", 30.0, NOMINAL, replace(base, **sway, target_sway_targets=(0, 1, 2, 3, 4))),
        Condition("peak_deflection_mm", 0.3, small, base),
    ]
    conditions += [Condition("adxl_timing_offset_ms", v, NOMINAL, replace(base, adxl_timestamp_offset_s=v * 1e-3)) for v in (-4.0, -2.0, 2.0, 4.0)]
    conditions += [Condition("adxl_clock_phase_ms", v, NOMINAL, replace(base, adxl_clock_phase_s=v * 1e-3)) for v in (0.5, 1.0, 1.5)]
    conditions += [Condition("adxl_noise_scale", 10.0, NOMINAL, replace(base, adxl_noise_scale=10.0))]
    conditions += [Condition("adxl_bias_walk", v, NOMINAL, replace(base, adxl_bias_walk_mps2_per_sqrt_s=v)) for v in (0.005, 0.02)]
    conditions += [Condition("adxl_tilt_gain", v, NOMINAL, replace(base, adxl_tilt_gain_mps2_per_m=v)) for v in (0.5, 1.5)]
    conditions += [Condition("adxl_scale_error", 0.02, NOMINAL, replace(base, adxl_scale_error=0.02))]
    conditions += [Condition("radar_dropout_ms", v, NOMINAL, base, dropout_s=v * 1e-3) for v in (10.0, 20.0, 30.0, 40.0)]
    return conditions


def _rows(part, group, value, seed, metrics, n_selected, c_over_r, error=""):
    return [
        {
            "part": part, "group": group, "value": value, "seed": seed, "method": name,
            "rmse_um": m["rmse_um"], "event_rmse_um": m["event_rmse_um"], "max_err_um": m["max_err_um"],
            "failed": int(m["failed"]), "n_selected": n_selected, "c_over_r": c_over_r, "error": error,
        }
        for name, m in metrics.items()
    ]


def _error_rows(part, group, value, seed, exc):
    lost = {"rmse_um": np.nan, "event_rmse_um": np.nan, "max_err_um": np.nan, "failed": True}
    return _rows(part, group, value, seed, {name: lost for name in METHODS}, 0, np.nan, repr(exc))


def _trial(part, group, value, seed, strict, compute):
    try:
        side, stream, scenario, tuned = compute()
        metrics = run_methods(side, stream, scenario, tuned)
    except Exception as exc:
        if strict:
            raise
        return _error_rows(part, group, value, seed, exc)
    return _rows(part, group, value, seed, metrics, int(side.radar.selected_indices.size), side.center_over_radius)


def ensemble_rows(seed: int, tuned: Tuned, strict: bool) -> list[dict]:
    def compute():
        scenario, impairments = draw_case(seed)
        side = prepare_radar(load_front(scenario, impairments, seed, DURATION_S))
        return side, adxl_samples(scenario, impairments, seed, DURATION_S), scenario, tuned

    return _trial("ensemble", "ensemble", 0.0, seed, strict, compute)


def sensitivity_rows(seed: int, tuned: Tuned, strict: bool) -> list[dict]:
    rng = np.random.default_rng([seed, 11])
    drop_start_s = float(rng.uniform(*DROPOUT_START_RANGE_S))
    fronts, sides, rows = {}, {}, []
    for condition in sensitivity_conditions():
        def compute(condition=condition):
            key = (condition.scenario, radar_impairments(condition.impairments))
            if key not in fronts:
                fronts[key] = load_front(condition.scenario, condition.impairments, seed, DURATION_S)
            dropout = (drop_start_s, condition.dropout_s) if condition.dropout_s > 0.0 else None
            if (key, dropout) not in sides:
                sides[(key, dropout)] = prepare_radar(fronts[key], dropout)
            stream = adxl_samples(condition.scenario, condition.impairments, seed, DURATION_S)
            return sides[(key, dropout)], stream, condition.scenario, tuned

        rows += _trial("sensitivity", condition.group, condition.value, seed, strict, compute)
    return rows


def run_task(task) -> list[dict]:
    part, seed, tuned, strict = task
    runner = ensemble_rows if part == "ensemble" else sensitivity_rows
    return runner(seed, tuned, strict)


def _map(function, tasks):
    workers = min(8, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function, tasks, chunksize=1))


def load_tuned() -> Tuned:
    path = RESULTS / "tuning.json"
    if not path.is_file():
        return Tuned()
    known = {field.name for field in fields(Tuned)}
    return Tuned(**{k: v for k, v in json.loads(path.read_text())["tuned"].items() if k in known})


def _write(path: Path, rows: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.6g}" if isinstance(value, float) else value) for key, value in row.items()})


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("value", "rmse_um", "event_rmse_um", "max_err_um", "c_over_r"):
            row[key] = float(row[key])
        for key in ("seed", "failed", "n_selected"):
            row[key] = int(row[key])
    return rows


def smoke() -> None:
    tuned = load_tuned()
    tasks = [("ensemble", seed, tuned, True) for seed in DEV_SEEDS[:3]] + [("sensitivity", DEV_SEEDS[0], tuned, True)]
    print(f"{'part':12s} {'group':22s} {'value':>8s} {'seed':>5s}  " + " ".join(f"{m[:9]:>9s}" for m in METHODS))
    for rows in _map(run_task, tasks):
        by_trial: dict[tuple, dict] = {}
        for row in rows:
            by_trial.setdefault((row["part"], row["group"], row["value"], row["seed"]), {})[row["method"]] = row
        for (part, group, value, seed), methods in by_trial.items():
            cells = " ".join(f"{methods[m]['event_rmse_um']:9.1f}" for m in METHODS)
            print(f"{part:12s} {group:22s} {value:8.3g} {seed:5d}  {cells}")


def tune_seed(seed: int) -> dict:
    scenario, impairments = draw_case(seed)
    side = prepare_radar(load_front(scenario, impairments, seed, DURATION_S))
    acceleration = acceleration_input(side, adxl_samples(scenario, impairments, seed, DURATION_S))
    window = event_window(scenario)
    radar, config = side.radar, side.config

    def objective(q_hat) -> float:
        value = score(q_hat, side, window)["event_rmse_um"]
        return float(np.log(min(value if np.isfinite(value) else TUNING_CAP_UM, TUNING_CAP_UM)))

    theta = radar_phase_series(radar, config)
    out = {}
    for q in Q_GRID:
        out[("fusion", q)] = objective(kalman(radar, acceleration, config, q))
        out[("kf-only", q)] = objective(kalman(radar, without_adxl(acceleration), config, q))
        for r in R_GRID:
            out[("fixed-R", (r, q))] = objective(kalman(
                replace(radar, initial_r=np.full_like(radar.initial_r, r)), acceleration, config, q,
                adaptive_r_forgetting=1.0,
            ))
    for corner in CORNER_GRID:
        out[("complementary", corner)] = objective(
            phase_observer(theta, acceleration, config, corner, start_at_measurement=True))
        out[("adxl-hp", corner)] = objective(
            phase_observer(np.zeros(theta.size), acceleration, config, corner, start_at_measurement=False))
    return out


def tune() -> None:
    per_seed = _map(tune_seed, DEV_SEEDS)
    tables: dict[str, dict[str, float]] = {}
    best: dict[str, object] = {}
    for method in ("fusion", "kf-only", "fixed-R", "complementary", "adxl-hp"):
        settings = [key[1] for key in per_seed[0] if key[0] == method]
        scores = {setting: float(np.mean([seed_result[(method, setting)] for seed_result in per_seed])) for setting in settings}
        tables[method] = {str(setting): value for setting, value in scores.items()}
        best[method] = min(scores, key=scores.get)
    tuned = {
        "fusion_q": best["fusion"], "kf_only_q": best["kf-only"],
        "fixed_r": best["fixed-R"][0], "fixed_r_q": best["fixed-R"][1],
        "complementary_corner_hz": best["complementary"], "adxl_hp_corner_hz": best["adxl-hp"],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "tuning.json").write_text(json.dumps({
        "seeds": list(DEV_SEEDS),
        "objective": f"mean over seeds of log(min(event RMSE [um], {TUNING_CAP_UM:g})); lower is better",
        "tuned": tuned, "tables": tables,
    }, indent=2) + "\n")
    print(json.dumps(tuned, indent=2))


def test(rerun: bool) -> None:
    paths = (RESULTS / "ensemble.csv", RESULTS / "sensitivity.csv")
    if not rerun and any(path.exists() for path in paths):
        sys.exit("held-out results exist; re-running re-uses the held-out seeds, pass --rerun to overwrite")
    if not (RESULTS / "tuning.json").is_file():
        sys.exit("run `tune` first")
    tuned = load_tuned()
    tasks = [("sensitivity", seed, tuned, False) for seed in SENSITIVITY_SEEDS]
    tasks += [("ensemble", seed, tuned, False) for seed in ENSEMBLE_SEEDS]
    results = _map(run_task, tasks)
    for part, path in (("ensemble", paths[0]), ("sensitivity", paths[1])):
        part_rows = [row for task_rows in results for row in task_rows if row["part"] == part]
        _write(path, part_rows)
        errors = sum(1 for row in part_rows if row["error"] and row["method"] == METHODS[0])
        print(f"{path.name}: {len(part_rows)} rows, {errors} trials raised an exception")


def _values(rows, **match) -> np.ndarray:
    selected = [r for r in rows if all(r[k] == v for k, v in match.items())]
    return np.array([r["event_rmse_um"] for r in sorted(selected, key=lambda r: r["seed"])])


def _failures(rows, **match) -> tuple[int, int]:
    selected = [r for r in rows if all(r[k] == v for k, v in match.items())]
    return sum(r["failed"] for r in selected), len(selected)


def _fmt_um(values) -> str:
    middle, low, high = stats.median_iqr(values)
    return f"{middle:.1f} [{low:.1f}, {high:.1f}]"


def _fmt_gain(result) -> str:
    return f"{100 * result['gain']:+.0f}% [{100 * result['gain_low']:+.0f}, {100 * result['gain_high']:+.0f}] (p={result['p']:.3g})"


REPORT_METHODS = ("fusion", "kf-only", "fixed-R", "single-target", "complementary", "radar-only", "adxl-hp", "adxl-raw")
ABLATIONS = ("no-circle", "oracle-beta")
SENSITIVITY_METHODS = ("fusion", "kf-only", "fixed-R", "complementary", "radar-only")
STRATUM_METHODS = ("fusion", "kf-only", "fixed-R", "complementary", "radar-only", "no-circle", "oracle-beta")
# Ranges of the static IQ-offset ratio |c|/R in the ensemble report.
STRATA = ((0.0, 0.05), (0.05, 0.15), (0.15, 1.0))


def _method_table(rows, methods) -> list[str]:
    lines = ["| method | event RMSE [um] | whole-record RMSE [um] | failures [Wilson 95%] |", "|---|---|---|---|"]
    for method in methods:
        failed, total = _failures(rows, method=method)
        low, high = stats.wilson_interval(failed, total)
        whole = [r["rmse_um"] for r in rows if r["method"] == method]
        lines.append(
            f"| {method} | {_fmt_um(_values(rows, method=method))} | {_fmt_um(whole)} "
            f"| {failed}/{total} [{100 * low:.0f}%, {100 * high:.0f}%] |"
        )
    return lines


def _gain_table(rows, methods) -> list[str]:
    fusion = _values(rows, method="fusion")
    lines = ["| fusion against | reduction of the geometric-mean event RMSE |", "|---|---|"]
    lines += [f"| {m} | {_fmt_gain(stats.paired_gain(fusion, _values(rows, method=m)))} |" for m in methods]
    return lines


def report() -> None:
    tuning = json.loads((RESULTS / "tuning.json").read_text())
    ensemble = read_rows(RESULTS / "ensemble.csv")
    sensitivity = read_rows(RESULTS / "sensitivity.csv")
    seeds = sorted({row["seed"] for row in ensemble})
    lines = ["# Simulation experiments", ""]
    lines += [
        "Generated by `python -m experiments.sweep report` from `ensemble.csv`, `sensitivity.csv` and `tuning.json`.",
        "",
        f"- Records: {DURATION_S:g} s, 500 Hz radar frames, one train passage.",
        f"- Free parameters tuned on development seeds {DEV_SEEDS[0]}-{DEV_SEEDS[-1]}: `{json.dumps(tuning['tuned'])}`.",
        f"- Ensemble: {len(seeds)} random scenes (seeds {seeds[0]}-{seeds[-1]}), each with its own structure, radar scene and sensor errors.",
        f"- Sensitivity: one factor at a time around the nominal scene, seeds {SENSITIVITY_SEEDS[0]}-{SENSITIVITY_SEEDS[-1]}.",
        "- Error = estimate minus truth, both referenced to their first 0.2 s mean. Event RMSE covers the passage plus 0.3 s.",
        "- Failure: non-finite estimate or maximum error above lambda/8 (about 0.49 mm, a 2*pi branch slip).",
        "- Values are medians with the inter-quartile range in brackets; ratios clip RMSE to [0.01, 10000] um.",
        "- Gains are paired reductions of the geometric-mean event RMSE (positive = fusion better) with a bootstrap 95% CI and a sign-flip p-value.",
        "",
    ]
    offset = {seed: draw_case(seed)[1].iq_offset_ratio for seed in seeds}
    lines += [
        "## 1. Randomised ensemble",
        "",
        "### 1.1 Pooled",
        "",
        "The pooled numbers depend on the assumed distribution of the static IQ-offset ratio |c|/R "
        "(log-uniform 0.02-0.5, not calibrated against a measured capture); the strata in 1.2 do not.",
        "",
    ]
    lines += _method_table(ensemble, REPORT_METHODS + ABLATIONS) + [""]
    lines += _gain_table(ensemble, REPORT_METHODS[1:] + ABLATIONS) + ["", "### 1.2 By static IQ-offset ratio |c|/R", ""]
    for low, high in STRATA:
        members = {seed for seed in seeds if low <= offset[seed] < high}
        if len(members) < 3:
            continue
        rows = [r for r in ensemble if r["seed"] in members]
        lines += [f"**|c|/R in [{low:g}, {high:g}): {len(members)} scenes**", ""]
        lines += _method_table(rows, STRATUM_METHODS) + [""] + _gain_table(rows, STRATUM_METHODS[1:]) + [""]

    failed_cases = sorted({r["seed"] for r in ensemble if r["method"] == "fusion" and r["failed"]})
    lines += ["", f"### 1.3 Scenes where fusion failed ({len(failed_cases)})", ""]
    if failed_cases:
        lines += ["| seed | event RMSE [um] | IQ offset | SNR offset [dB] | sway [um] | timing offset [ms] | bias walk |", "|---|---|---|---|---|---|---|"]
        for seed in failed_cases:
            _, imp = draw_case(seed)
            value = [r for r in ensemble if r["seed"] == seed and r["method"] == "fusion"][0]["event_rmse_um"]
            lines.append(f"| {seed} | {value:.0f} | {imp.iq_offset_ratio:.2f} | {imp.snr_offset_db:.1f} | {1e6 * imp.target_sway_std_m:.0f} | {1e3 * imp.adxl_timestamp_offset_s:+.2f} | {imp.adxl_bias_walk_mps2_per_sqrt_s:.4f} |")
    else:
        lines.append("None.")

    by_seed: dict[int, dict] = {}
    for row in ensemble:
        by_seed.setdefault(row["seed"], {})[row["method"]] = row
    unengaged = [seed for seed in seeds if by_seed[seed]["fusion"]["c_over_r"] == 0.0]
    identical = [seed for seed in seeds if by_seed[seed]["fusion"]["rmse_um"] == by_seed[seed]["no-circle"]["rmse_um"]]
    lines += [
        "", "### 1.4 Engagement of the recursive circle fit", "",
        "The fit accepts a circle only while the cumulative normal matrix has a condition number below 1e4, "
        "so a long static prefix with a short arc can keep it from engaging.",
        "",
        f"- Scenes whose median fitted |c|/R at the end of the record is zero (no accepted circle for most targets): "
        f"{len(unengaged)}/{len(seeds)}{' (seeds ' + ', '.join(map(str, unengaged)) + ')' if unengaged else ''}.",
        f"- Scenes where fusion and no-circle are bit-identical (no accepted circle for any target): "
        f"{len(identical)}/{len(seeds)}{' (seeds ' + ', '.join(map(str, identical)) + ')' if identical else ''}.",
    ]
    lines += ["", "## 2. One-factor sensitivity around the nominal scene", ""]
    groups = []
    for row in sensitivity:
        if row["group"] != "nominal" and row["group"] not in groups:
            groups.append(row["group"])
    nominal_seeds = len(_values(sensitivity, group="nominal", method="fusion"))
    lines += [f"Cells are the median event RMSE in um over {nominal_seeds} seeds with the number of failed runs in parentheses; the last column is the paired reduction of fusion against the Kalman filter without ADXL.", ""]
    for group in groups:
        lines += [f"### {group}", "", "| value | " + " | ".join(SENSITIVITY_METHODS) + " | fusion vs kf-only |", "|---|" + "---|" * (len(SENSITIVITY_METHODS) + 1)]
        levels = sorted({r["value"] for r in sensitivity if r["group"] == group})
        for value in [NEUTRAL[group]] + levels:
            match = {"group": "nominal", "value": 0.0} if value == NEUTRAL[group] else {"group": group, "value": value}
            cells = []
            for method in SENSITIVITY_METHODS:
                failed, _ = _failures(sensitivity, method=method, **match)
                cells.append(f"{stats.median_iqr(_values(sensitivity, method=method, **match))[0]:.1f} ({failed})")
            gain = stats.paired_gain(_values(sensitivity, method="fusion", **match), _values(sensitivity, method="kf-only", **match))
            lines.append(f"| {value:g} | " + " | ".join(cells) + f" | {_fmt_gain(gain)} |")
        lines.append("")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {RESULTS / 'summary.md'}")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "smoke":
        smoke()
    elif command == "tune":
        tune()
    elif command == "test":
        test("--rerun" in sys.argv[2:])
    elif command == "report":
        report()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
