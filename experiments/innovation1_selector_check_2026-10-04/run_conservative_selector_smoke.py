#!/usr/bin/env python3
"""Conservative truth-free selector smoke; depends on the prior scratch runner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import run_selector_check as base

ROOT = Path(__file__).resolve().parent
MIN_SPAN_DEG = 30.0
MIN_PROJECTION_GAP = 0.05


def conservative_selector(iq):
    """Calibration IQ and constants only; no truth or score is accepted."""
    angles, _ = base.geometry(iq[: base.CAL])
    decision = {
        "selected_route": None,
        "angles_deg": angles,
        "candidate_count": len(angles),
        "selector_failure": None,
    }
    if not angles:
        decision["selector_failure"] = "no_calibration_angle_peak"
        return decision, None, None
    if len(angles) == 1:
        mode = "merge"
    else:
        span = float(abs(angles[0] - angles[1]))
        projection_gap = float(
            abs(np.cos(np.deg2rad(angles[0])) - np.cos(np.deg2rad(angles[1])))
        )
        decision.update(span_deg=span, projection_gap=projection_gap)
        if span < MIN_SPAN_DEG:
            decision["selector_failure"] = "ambiguous_narrow_peak_span"
            return decision, None, None
        if projection_gap < MIN_PROJECTION_GAP:
            decision["selector_failure"] = "ambiguous_projection_gap"
            return decision, None, None
        condition = float(np.linalg.cond(base.steering(angles)))
        decision["steering_condition"] = condition
        if condition > 20:
            decision["selector_failure"] = "ill_conditioned_split"
            return decision, None, None
        mode = "split_ls"
    decision["selected_route"] = mode
    route, qhat = base.route_from_geometry(iq, angles, mode)
    if not route["covered"]:
        decision["selector_failure"] = route["failure"]
    return decision, route, qhat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=213)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for case_name in base.CASES:
        iq, truth = base.generate(case_name, args.seed)
        angles, _ = base.geometry(iq[: base.CAL])
        independent = {}
        for mode in ("merge", "split_ls"):
            route, qhat = base.route_from_geometry(iq, angles, mode)
            independent[mode] = base.score(route, qhat, truth)
        decision, selected_route, selected_qhat = conservative_selector(iq)
        if selected_route is None:
            selected = {
                "mode": None,
                "covered": False,
                "failure": decision["selector_failure"],
                "rmse_mm": None,
                "high_error_gt_0p01mm": None,
            }
        else:
            selected = base.score(selected_route, selected_qhat, truth)
        rows.append({
            "case": case_name,
            "seed": args.seed,
            "selector": decision,
            "selected": selected,
            "independent": independent,
        })
    payload = {
        "protocol_sha256": hashlib.sha256((ROOT / "CONSERVATIVE_PROTOCOL.md").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dependency_sha256": hashlib.sha256((ROOT / "run_selector_check.py").read_bytes()).hexdigest(),
        "scope": "one new seed conservative calibration-feature abstention smoke",
        "seed": args.seed,
        "truth_free_selector": True,
        "truth_access_stage": "post-run score only",
        "frozen_rule": {
            "min_span_deg": MIN_SPAN_DEG,
            "min_projection_gap": MIN_PROJECTION_GAP,
            "failed_selected_route_fallback": False,
        },
        "rows": rows,
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"seed": args.seed, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
