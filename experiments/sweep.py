"""Monte Carlo sweeps of the simulated guideway experiment.

    python -m experiments.sweep tune      # process noise on training seeds
    python -m experiments.sweep test      # all conditions on held-out seeds
    python -m experiments.sweep report    # tables from the CSV

Process noise is tuned on seeds disjoint from the test seeds.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np

from experiments.methods import run_trial
from paper_bridge_simulation.package_builder import Impairments

RESULTS = Path(__file__).parent / "results"
DURATION_S = 4.0
TRAIN_SEEDS = list(range(1000, 1010))
TEST_SEEDS = list(range(2000, 2030))
TUNING_GRID = (1.0, 3.0, 1.0e1, 3.0e1, 1.0e2, 3.0e2, 1.0e3, 3.0e3, 1.0e4, 5.0e4)
TUNING_CONDITIONS = {"snr0": {}, "snr-10": {"snr_offset_db": -10.0}, "snr-20": {"snr_offset_db": -20.0}}
LOW_SNR = {"snr_offset_db": -10.0}
REGIMES = {"nominal": {}, "snr-10dB": LOW_SNR}

# (group, parameter name, values, Impairments field, scale to field units)
ADXL_AND_SCENE_SWEEPS = [
    ("adxl_bias", "static axis offset incl. gravity [m/s^2]", [0.0, 0.2, 2.0, 9.80665], "adxl_bias_x_mps2", 1.0),
    ("adxl_noise", "noise scale [x]", [1.0, 3.0, 10.0, 30.0], "adxl_noise_scale", 1.0),
    ("adxl_time_offset", "residual timestamp offset [ms]", [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0], "adxl_timestamp_offset_s", 1.0e-3),
    ("adxl_jitter", "timestamp jitter std [ms]", [0.0, 0.5, 1.0, 3.0], "adxl_timestamp_jitter_std_s", 1.0e-3),
    ("adxl_bias_walk", "bias walk [m/s^2/sqrt(s)]", [0.0, 0.005, 0.02, 0.05, 0.1], "adxl_bias_walk_mps2_per_sqrt_s", 1.0),
    ("radar_dropout", "radar dropout [ms]", [0.0, 6.0, 12.0, 20.0, 30.0], "radar_dropout_s", 1.0e-3),
    ("target_sway", "target sway std [um]", [0.0, 5.0, 10.0, 20.0, 50.0], "target_sway_std_m", 1.0e-6),
    ("peak_deflection", "peak deflection [mm]", [0.1, 0.3, 1.0, 1.712], "peak_deflection_m", 1.0e-3),
]


def test_conditions() -> list[tuple[str, str, float, dict]]:
    """(group, regime, parameter value, Impairments kwargs)."""
    conditions = [("snr", "-", offset, {"snr_offset_db": offset}) for offset in (0.0, -10.0, -15.0, -20.0, -25.0, -30.0)]
    for group, _, values, field, scale in ADXL_AND_SCENE_SWEEPS:
        for regime, base in REGIMES.items():
            for value in values:
                conditions.append((group, regime, value, {**base, field: value * scale}))
    return conditions


def _work(task):
    group, regime, value, kwargs, seed, noises, extra = task
    try:
        metrics = run_trial(Impairments(**kwargs), seed, DURATION_S, noises, extra_methods=extra)
        meta = metrics.pop("_meta")
        return [(group, regime, value, seed, name, m, meta["selected_targets"]) for name, m in metrics.items()]
    except Exception as exc:  # a failed generation or detection counts as a failed trial
        return [(group, regime, value, seed, "ERROR", {"rmse_m": float("nan"), "event_rmse_m": float("nan"), "peak_err_m": float("nan"), "failed": True, "error": repr(exc)}, 0)]


def _work_seed(seed_task):
    seed, conditions, noises, extra = seed_task
    out = []
    trial_cache: dict[Impairments, dict] = {}
    for cond_idx, (group, regime, value, kwargs) in enumerate(conditions):
        imp = Impairments(**kwargs)
        if imp not in trial_cache:
            try:
                metrics = run_trial(imp, seed, DURATION_S, noises, extra_methods=extra)
                meta = metrics.pop("_meta")
                trial_cache[imp] = (metrics, meta["selected_targets"])
            except Exception as exc:
                trial_cache[imp] = (
                    {"ERROR": {"rmse_m": float("nan"), "event_rmse_m": float("nan"), "peak_err_m": float("nan"), "failed": True, "error": repr(exc)}},
                    0,
                )
        metrics, selected = trial_cache[imp]
        rows = [(group, regime, value, seed, name, m, selected) for name, m in metrics.items()]
        out.append((cond_idx, seed, rows))
    return out


def _run_conditions_by_seed(conditions: list[tuple[str, str, float, dict]], seeds: list[int], noises: tuple[float, ...], extra: bool, path: Path) -> None:
    RESULTS.mkdir(exist_ok=True)
    seed_tasks = [(seed, conditions, noises, extra) for seed in seeds]
    collected = []
    workers = min(len(seed_tasks), max(1, (os.cpu_count() or 2) - 2))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done, seed_out in enumerate(pool.map(_work_seed, seed_tasks, chunksize=1), 1):
            collected.extend(seed_out)
            print(f"seeds {done}/{len(seed_tasks)}", end="\r", flush=True)
    print()
    collected.sort(key=lambda item: (item[0], item[1]))
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["group", "regime", "value", "seed", "method", "rmse_um", "event_rmse_um", "peak_err_um", "failed", "selected_targets"])
        for _, _, rows in collected:
            for group, regime, value, seed, name, m, selected in rows:
                writer.writerow([group, regime, value, seed, name, m["rmse_m"] * 1e6, m["event_rmse_m"] * 1e6, m["peak_err_m"] * 1e6, int(m["failed"]), selected])


def tune() -> None:
    conditions = [(name, "-", 0.0, kwargs) for name, kwargs in TUNING_CONDITIONS.items()]
    _run_conditions_by_seed(conditions, TRAIN_SEEDS, TUNING_GRID, False, RESULTS / "tuning.csv")
    choose()


def choose() -> None:
    """Pick the process noise of each method separately on the training seeds."""
    rows = _read(RESULTS / "tuning.csv")
    best, tables = {}, {}
    for method in ("kf+adxl", "kf-only"):
        score = {
            q: float(np.mean([
                np.mean(np.log([r["rmse_um"] for r in rows if r["method"] == f"{method}@{q:g}" and r["group"] == cond]))
                for cond in TUNING_CONDITIONS
            ]))
            for q in TUNING_GRID
        }
        best[method] = min(score, key=score.get)
        tables[method] = {f"{q:g}": round(float(np.exp(v)), 3) for q, v in score.items()}
    (RESULTS / "tuning.json").write_text(json.dumps({
        "fusion_process_noise": best["kf+adxl"],
        "kf_only_process_noise": best["kf-only"],
        "geometric_mean_rmse_um_by_q": tables,
        "train_seeds": TRAIN_SEEDS,
    }, indent=2) + "\n")
    print("tuned process noise:", best, tables)


def test() -> None:
    tuned = json.loads((RESULTS / "tuning.json").read_text())
    noises = tuple(dict.fromkeys((tuned["fusion_process_noise"], tuned["kf_only_process_noise"])))
    _run_conditions_by_seed(test_conditions(), TEST_SEEDS, noises, True, RESULTS / "test.csv")


def _read(path: Path) -> list[dict]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["value"] = float(row["value"])
        for key in ("rmse_um", "event_rmse_um", "peak_err_um"):
            row[key] = float(row[key])
        row["failed"] = int(row["failed"])
    return rows


def report() -> None:
    tuning = json.loads((RESULTS / "tuning.json").read_text())
    qf, qk = tuning["fusion_process_noise"], tuning["kf_only_process_noise"]
    rows = _read(RESULTS / "test.csv")
    methods = [
        (f"kf+adxl@{qf:g}", f"fusion (q={qf:g})"),
        (f"kf-only@{qk:g}", f"KF no ADXL (q={qk:g})"),
        (f"kf+adxl-fixedR@{qf:g}", "fusion, fixed R"),
        (f"kf+adxl-single@{qf:g}", "single-target fusion"),
        ("radar-unfiltered", "radar only, no filter"),
        ("adxl-double-integration", "ADXL only"),
    ]
    present = {r["method"] for r in rows}
    methods = [m for m in methods if m[0] in present]
    labels = {g: (name, scale) for g, name, _, _, scale in ADXL_AND_SCENE_SWEEPS}
    labels["snr"] = ("radar SNR offset [dB]", 1.0)

    def cell(selection):
        values = np.array([r["rmse_um"] for r in selection])
        failed = sum(r["failed"] for r in selection)
        if not values.size:
            return "-"
        text = f"{np.nanmean(values):.1f}±{np.nanstd(values):.1f}"
        return text + (f" ({failed}/{len(values)} fail)" if failed else "")

    lines = [
        "# Simulation experiment results",
        "",
        f"Duration {DURATION_S:g} s per trial (one train event at 0.5-1.3 s), {len(TEST_SEEDS)} held-out seeds "
        f"({TEST_SEEDS[0]}-{TEST_SEEDS[-1]}) per condition. Process noise tuned on seeds "
        f"{TRAIN_SEEDS[0]}-{TRAIN_SEEDS[-1]}, separately per method: fusion q = {qf:g}, KF without ADXL q = {qk:g}.",
        "ADXL timestamps are exported as DRDY time minus the calibrated 3.26 ms group delay; the static axis offset "
        "(gravity projection and turn-on bias) is removed over the first 0.2 s, as in system.algorithm.io.",
        "Cells are RMSE over the whole trial in um, mean±std over seeds; a trial fails when RMSE exceeds 6 % of the peak deflection. "
        "'ADXL gain' is the reduction of the mean RMSE of fusion relative to the Kalman filter without ADXL.",
        "",
    ]
    groups = []
    for r in rows:
        if (r["group"], r["regime"]) not in groups:
            groups.append((r["group"], r["regime"]))
    for group, regime in groups:
        name = labels[group][0]
        title = f"{group} ({regime})" if regime != "-" else group
        lines += [f"## {title}", "", "| " + name + " | " + " | ".join(m[1] for m in methods) + " | ADXL gain | fusion beats KF-only (each at own q) |", "|" + "---|" * (len(methods) + 3)]
        values = sorted({r["value"] for r in rows if r["group"] == group and r["regime"] == regime})
        for value in values:
            sel = [r for r in rows if r["group"] == group and r["regime"] == regime and r["value"] == value]
            cells = [cell([r for r in sel if r["method"] == m[0]]) for m in methods]
            fusion = {r["seed"]: r["rmse_um"] for r in sel if r["method"] == methods[0][0]}
            kf = {r["seed"]: r["rmse_um"] for r in sel if r["method"] == methods[1][0]}
            wins = sum(fusion[s] < kf[s] for s in fusion if s in kf)
            gain = 1.0 - np.mean(list(fusion.values())) / np.mean(list(kf.values()))
            lines.append(f"| {value:g} | " + " | ".join(cells) + f" | {100.0 * gain:.0f} % | {wins}/{len(fusion)} |")
        lines.append("")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    {"tune": tune, "choose": choose, "test": test, "report": report}[sys.argv[1]]()
