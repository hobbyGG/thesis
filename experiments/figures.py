"""Figures from results/*.csv (needs matplotlib).

    python -m experiments.figures
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments import stats
from experiments.front import load_front
from experiments.methods import acceleration_input, estimate_all, prepare_radar
from experiments.sweep import (
    ABLATIONS, DURATION_S, NEUTRAL, REPORT_METHODS, RESULTS, SENSITIVITY_METHODS,
    _values, load_tuned, read_rows,
)
from paper_bridge_simulation.ensemble import draw_case
from paper_bridge_simulation.package_builder import adxl_samples
from system.algorithm.run import displacement_error_m

COLOURS = {
    "fusion": "C0", "kf-only": "C1", "complementary": "C2", "radar-only": "C3", "adxl-hp": "C4",
    "fixed-R": "C5", "single-target": "C6", "adxl-raw": "C7", "no-circle": "C8", "oracle-beta": "C9",
}


def ensemble_figure(rows) -> None:
    methods = REPORT_METHODS + ABLATIONS
    fig, ax = plt.subplots(figsize=(9, 3.8))
    rng = np.random.default_rng(0)
    for position, method in enumerate(methods):
        selected = [r for r in rows if r["method"] == method]
        values = stats.clipped([r["event_rmse_um"] for r in selected])
        failed = np.array([bool(r["failed"]) for r in selected])
        x = position + rng.uniform(-0.18, 0.18, values.size)
        ax.scatter(x[~failed], values[~failed], s=10, color=COLOURS[method], alpha=0.7)
        ax.scatter(x[failed], values[failed], s=22, color=COLOURS[method], marker="x")
        ax.hlines(np.median(values), position - 0.3, position + 0.3, color="k", lw=1.5)
    ax.set_xticks(range(len(methods)), methods, rotation=30, ha="right", fontsize=8)
    ax.set_yscale("log")
    ax.set_ylabel("event RMSE [um]")
    ax.set_title("Randomised ensemble (x = failure, bar = median)")
    ax.grid(alpha=0.3, which="both", axis="y")
    fig.tight_layout()
    fig.savefig(RESULTS / "figures" / "ensemble.png", dpi=140)
    plt.close(fig)


def sensitivity_figure(rows) -> None:
    groups = []
    for row in rows:
        if row["group"] != "nominal" and row["group"] not in groups:
            groups.append(row["group"])
    columns = 4
    fig, axes = plt.subplots(-(-len(groups) // columns), columns, figsize=(3.4 * columns, 2.7 * -(-len(groups) // columns)), squeeze=False)
    for ax, group in zip(axes.ravel(), groups):
        levels = [NEUTRAL[group]] + sorted({r["value"] for r in rows if r["group"] == group})
        for method in SENSITIVITY_METHODS:
            cells = []
            for level in levels:
                match = {"group": "nominal", "value": 0.0} if level == NEUTRAL[group] else {"group": group, "value": level}
                cells.append(np.percentile(stats.clipped(_values(rows, method=method, **match)), [25, 50, 75]))
            cells = np.asarray(cells)
            ax.plot(levels, cells[:, 1], "o-", ms=3, color=COLOURS[method], label=method)
            ax.fill_between(levels, cells[:, 0], cells[:, 2], color=COLOURS[method], alpha=0.12)
        ax.set_yscale("log")
        ax.set_title(group, fontsize=8)
        ax.grid(alpha=0.3, which="both")
        ax.tick_params(labelsize=7)
    for ax in axes.ravel()[len(groups):]:
        ax.axis("off")
    axes[0][0].legend(fontsize=6)
    fig.supylabel("event RMSE [um]", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "figures" / "sensitivity.png", dpi=140)
    plt.close(fig)


def example_figure(rows) -> None:
    """Median-RMSE ensemble scene: truth against the main estimators."""
    fusion = sorted((r for r in rows if r["method"] == "fusion"), key=lambda r: r["event_rmse_um"])
    seed = fusion[len(fusion) // 2]["seed"]
    scenario, impairments = draw_case(seed)
    side = prepare_radar(load_front(scenario, impairments, seed, DURATION_S))
    estimates = estimate_all(side, acceleration_input(side, adxl_samples(scenario, impairments, seed, DURATION_S)), load_tuned())
    time_s, truth = side.front.time_s, side.front.truth_m
    window = (scenario.event_starts_s[0] - 0.1, scenario.event_starts_s[0] + scenario.passage_duration_s + 0.4)
    visible = (time_s >= window[0]) & (time_s <= window[1])
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
    centred_truth = truth - truth[time_s <= 0.2].mean()
    top.plot(time_s[visible], 1e3 * centred_truth[visible], "k", lw=1.5, label="truth")
    for method in ("fusion", "kf-only", "radar-only"):
        error = displacement_error_m(estimates[method], truth, time_s, 0.2)
        top.plot(time_s[visible], 1e3 * (centred_truth + error)[visible], color=COLOURS[method], lw=1, label=method)
        bottom.plot(time_s[visible], 1e6 * error[visible], color=COLOURS[method], lw=1, label=method)
    top.set_ylabel("displacement [mm]")
    top.legend(fontsize=7)
    bottom.set_ylabel("error [um]")
    bottom.set_xlabel("time [s]")
    top.set_title(f"Ensemble scene, seed {seed} (median fusion RMSE)")
    for ax in (top, bottom):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "figures" / "example.png", dpi=140)
    plt.close(fig)


def offset_figure(rows) -> None:
    """Event RMSE of the ensemble scenes against their static IQ-offset ratio."""
    seeds = sorted({r["seed"] for r in rows})
    ratio = np.array([draw_case(seed)[1].iq_offset_ratio for seed in seeds])
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for method, marker in (("fusion", "o"), ("no-circle", "^"), ("radar-only", "s"), ("kf-only", "x")):
        values = stats.clipped(_values(rows, method=method))
        ax.scatter(ratio, values, s=18, marker=marker, color=COLOURS[method], alpha=0.75, label=method)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5], ["0.02", "0.05", "0.1", "0.2", "0.5"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("static IQ-offset ratio |c|/R")
    ax.set_ylabel("event RMSE [um]")
    ax.set_title("Ensemble: error against the uncalibrated IQ offset")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(RESULTS / "figures" / "iq_offset.png", dpi=140)
    plt.close(fig)


def main() -> None:
    (RESULTS / "figures").mkdir(parents=True, exist_ok=True)
    ensemble = read_rows(RESULTS / "ensemble.csv")
    ensemble_figure(ensemble)
    offset_figure(ensemble)
    sensitivity_figure(read_rows(RESULTS / "sensitivity.csv"))
    example_figure(ensemble)
    print("figures written to", RESULTS / "figures")


if __name__ == "__main__":
    main()
