"""Figures from results/test.csv (median and inter-quartile band over seeds)."""

from __future__ import annotations

import json
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments.sweep import DEFAULT_PROCESS_NOISE, RESULTS, _read

tuned = json.loads((RESULTS / "tuning.json").read_text())
qf, qk = tuned["fusion_process_noise"], tuned["kf_only_process_noise"]
STYLES = [
    (f"kf+adxl@{qf:g}", f"fusion (q={qf:g})", "C0", "-"),
    (f"kf-only@{qk:g}", f"Kalman, no ADXL (q={qk:g})", "C1", "-"),
    (f"kf+adxl-fixedR@{qf:g}", "fusion, fixed R", "C4", "--"),
    (f"kf+adxl-single@{qf:g}", "single-target fusion", "C5", "-."),
    ("radar-unfiltered", "radar only, no filter", "C2", "-"),
    ("adxl-double-integration", "ADXL only", "C3", ":"),
]
rows = _read(RESULTS / "test.csv")
by = defaultdict(list)
for r in rows:
    by[(r["group"], r["regime"], r["method"], r["value"])].append(r["rmse_um"])

groups = []
for r in rows:
    if r["group"] not in groups:
        groups.append(r["group"])
for group in groups:
    regimes = sorted({r["regime"] for r in rows if r["group"] == group})
    fig, axes = plt.subplots(1, len(regimes), figsize=(5 * len(regimes), 3.6), squeeze=False)
    for ax, regime in zip(axes[0], regimes):
        values = sorted({r["value"] for r in rows if r["group"] == group and r["regime"] == regime})
        for method, label, colour, style in STYLES:
            if not any((group, regime, method, v) in by for v in values):
                continue
            stats = np.array([np.nanpercentile(by[(group, regime, method, v)], [25, 50, 75]) for v in values])
            ax.plot(values, stats[:, 1], style, color=colour, marker="o", ms=3, label=label)
            ax.fill_between(values, stats[:, 0], stats[:, 2], color=colour, alpha=0.12)
        ax.set_yscale("log")
        ax.set_xlabel(group)
        ax.set_ylabel("RMSE [um]")
        ax.set_title(regime if regime != "-" else group)
        ax.grid(alpha=0.3, which="both")
    axes[0][0].legend(fontsize=7)
    fig.tight_layout()
    (RESULTS / "figures").mkdir(exist_ok=True)
    fig.savefig(RESULTS / "figures" / f"{group}.png", dpi=140)
    plt.close(fig)
print("figures written to", RESULTS / "figures")
