"""Combine the pre-registered mode decisions with existing route scores.

This is a scratch-only report generator.  It never opens truth files and does
not rerun or alter an estimator; the route score JSONs were produced by the
truth-free diagnostics and scored post-run by their own harnesses.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


SEEDS = (20261001, 20261002, 20261003)
CONDITIONS = ("baseline_no_drift", "post_200_phase_ramp", "pre_window_phase_ramp", "angle_migration")


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(root: Path, output: Path) -> dict[str, object]:
    classifier = root / "gauge_mode_classifier_analysis"
    records: list[dict[str, object]] = []
    for seed in SEEDS:
        for condition in CONDITIONS:
            feature = json.loads((classifier / f"{seed}_{condition}.json").read_text(encoding="utf-8"))
            route_dir = root / (
                f"gauge_fix_angle_migration_seed{seed}"
                if condition == "angle_migration"
                else f"gauge_fix_diagnostic_seed{seed}"
            )
            route = json.loads((route_dir / f"{condition}.json").read_text(encoding="utf-8"))
            selected_route = (
                "rolling_bias_transport"
                if feature["route_decision"] == "gauge_boundary_candidate"
                else "rolling_raw"
            )
            records.append({
                "seed": seed,
                "condition": condition,
                "classifier_decision": feature["route_decision"],
                "selected_route": selected_route,
                "fixed_reference": route["fixed_reference"]["score"],
                "rolling_raw": route["rolling_raw"]["score"],
                "rolling_bias_transport": route["rolling_bias_transport"]["score"],
                "routed_score": route[selected_route]["score"],
                "routing_uses_truth": False,
            })
    by_condition: dict[str, object] = {}
    for condition in CONDITIONS:
        subset = [r for r in records if r["condition"] == condition]
        route_stats: dict[str, object] = {}
        for route_name in ("fixed_reference", "rolling_raw", "rolling_bias_transport", "routed_score"):
            scores = [r[route_name] for r in subset]
            rmse = np.asarray([s["rmse_mm"] for s in scores], dtype=float)
            coverage = np.asarray([s["coverage"] for s in scores], dtype=float)
            route_stats[route_name] = {
                "rmse_mm_values": rmse.tolist(),
                "rmse_mm_mean": float(np.mean(rmse)),
                "rmse_mm_std": float(np.std(rmse, ddof=1)),
                "coverage_values": coverage.tolist(),
                "coverage_min": float(np.min(coverage)),
                "coverage_mean": float(np.mean(coverage)),
            }
        by_condition[condition] = {
            "routing_decisions": [r["classifier_decision"] for r in subset],
            "selected_routes": [r["selected_route"] for r in subset],
            "scores": route_stats,
        }
    summary = {
        "schema": "online_geometry_loop_gauge_mode_routed_diagnostic",
        "status": "diagnostic_only",
        "seeds": list(SEEDS),
        "conditions": list(CONDITIONS),
        "records": records,
        "by_condition": by_condition,
        "truth_free_estimator_routes": True,
        "routing_uses_truth": False,
        "accuracy_claim": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    _json(output / "summary.json", summary)
    _json(output / "protocol.json", {
        "schema": "online_geometry_loop_gauge_mode_routed_protocol",
        "route_rule": "first-20 truth-free classifier: gauge_boundary_candidate -> rolling_bias_transport; all other decisions -> rolling_raw",
        "inputs": "existing truth-free fixed/raw/transport route records with post-run truth score metadata",
        "routing_uses_truth": False,
        "accuracy_claim": False,
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize mode-routed scratch routes")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.root, args.output)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
