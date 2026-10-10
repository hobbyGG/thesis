#!/usr/bin/env python3
"""Bounded geometry-neighborhood check for the frozen truth-free selector."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import sys

SCRATCH = Path(__file__).resolve().parents[1] / "innovation1_selector_check_2026-10-04"
sys.path.insert(0, str(SCRATCH))
import run_selector_check as base  # noqa: E402

ROOT = Path(__file__).resolve().parent
CELLS = [
    ("span24_gap005", 24.0, 0.05, 3000),
    ("span28_gap005", 28.0, 0.05, 3001),
    ("span30_gap005", 30.0, 0.05, 3002),
    ("span32_gap005", 32.0, 0.05, 3003),
    ("span36_gap005", 36.0, 0.05, 3004),
    ("span30_gap000", 30.0, 0.00, 3005),
    ("span30_gap002", 30.0, 0.02, 3006),
    ("span30_gap008", 30.0, 0.08, 3007),
    ("span30_gap012", 30.0, 0.12, 3008),
]


def pair_angles(span_deg: float, projection_gap: float) -> list[float]:
    half = math.radians(span_deg / 2.0)
    if projection_gap == 0.0:
        center = 0.0
    else:
        ratio = projection_gap / (2.0 * math.sin(half))
        if not 0.0 < ratio < 1.0:
            raise ValueError((span_deg, projection_gap, ratio))
        center = math.asin(ratio)
    c = math.degrees(center)
    return [c - span_deg / 2.0, c + span_deg / 2.0]


def generate(angles, amplitudes, phases, seed):
    rng = np.random.default_rng(seed)
    p = rng.uniform(-np.pi, np.pi)
    t = np.arange(base.N) / base.FS
    q = 0.8 * np.sin(2 * np.pi * 3 * t + p) + 0.2 * np.sin(2 * np.pi * 5 * t + 0.43 - 0.2 * p)
    c = np.cos(np.deg2rad(angles))
    sources = np.array(amplitudes)[None, :] * np.exp(
        1j * (np.array(phases)[None, :] + 4 * np.pi / base.LAMBDA_MM * q[:, None] * c[None, :])
    )
    z = sources @ base.steering(angles).T
    z += base.NOISE_SIGMA * (rng.standard_normal(z.shape) + 1j * rng.standard_normal(z.shape))
    return z, q


def score_rows(iq, truth, decision, selected_route, selected_qhat, angles, requested):
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
    independent = {}
    for mode in ("merge", "split_ls"):
        route, qhat = base.route_from_geometry(iq, angles, mode)
        independent[mode] = base.score(route, qhat, truth)
    return {
        "requested": requested,
        "detected_angles_deg": angles,
        "selector": decision,
        "selected": selected,
        "independent": independent,
    }


def run_cell(cell_id, span, gap, seed):
    requested = {
        "cell_id": cell_id,
        "seed": seed,
        "span_deg": span,
        "projection_gap": gap,
    }
    pair = pair_angles(span, gap)
    pair_semantics = [
        ("balanced_pair", [1.0, 0.8], [0.15, -0.30]),
        ("unequal_pair", [1.0, 0.5], [0.15, -0.30]),
        ("opposed_phase_pair", [1.0, 1.0], [0.0, np.pi]),
    ]
    rows = []
    for semantic, amplitudes, phases in pair_semantics:
        iq, truth = generate(pair, amplitudes, phases, seed)
        decision, selected_route, selected_qhat = base_selector(iq)
        row = score_rows(
            iq, truth, decision, selected_route, selected_qhat, base.geometry(iq[: base.CAL])[0],
            dict(requested, semantic=semantic, generated_angles_deg=pair),
        )
        rows.append(row)
    control_angles = [27.0, 27.0]
    iq, truth = generate(control_angles, [1.0, 1.0], [0.0, np.pi], seed)
    decision, selected_route, selected_qhat = base_selector(iq)
    rows.append(score_rows(
        iq, truth, decision, selected_route, selected_qhat, base.geometry(iq[: base.CAL])[0],
        dict(requested, semantic="coincident_cancel_control", generated_angles_deg=control_angles),
    ))
    if span == 30.0 and gap == 0.0:
        iq, truth = generate(pair, [1.0, 0.8], [0.15, -0.30], seed)
        decision, selected_route, selected_qhat = base_selector(iq)
        rows.append(score_rows(
            iq, truth, decision, selected_route, selected_qhat, base.geometry(iq[: base.CAL])[0],
            dict(requested, semantic="symmetric_control", generated_angles_deg=pair),
        ))
    return rows


def base_selector(iq):
    """Inline frozen conservative selector; only IQ and constants enter."""
    angles, _ = base.geometry(iq[: base.CAL])
    decision = {"selected_route": None, "angles_deg": angles, "candidate_count": len(angles), "selector_failure": None}
    if not angles:
        decision["selector_failure"] = "no_calibration_angle_peak"
        return decision, None, None
    if len(angles) == 1:
        mode = "merge"
    else:
        span = float(abs(angles[0] - angles[1]))
        gap = float(abs(np.cos(np.deg2rad(angles[0])) - np.cos(np.deg2rad(angles[1]))))
        decision.update(span_deg=span, projection_gap=gap)
        if span < 30.0:
            decision["selector_failure"] = "ambiguous_narrow_peak_span"
            return decision, None, None
        if gap < 0.05:
            decision["selector_failure"] = "ambiguous_projection_gap"
            return decision, None, None
        condition = float(np.linalg.cond(base.steering(angles)))
        decision["steering_condition"] = condition
        if condition > 20.0:
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
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for cell_id, span, gap, seed in CELLS:
        rows.extend(run_cell(cell_id, span, gap, seed))
    payload = {
        "schema": "innovation1.geometry_neighborhood_selector",
        "scope": "nine geometry cells, one seed per cell, frozen truth-free selector",
        "truth_free_selector": True,
        "truth_access_stage": "post-run score only",
        "frozen_rule": {"span_lt_deg": 30.0, "projection_gap_lt": 0.05, "condition_lte": 20.0, "fallback": False},
        "cells": [{"cell_id": x[0], "span_deg": x[1], "projection_gap": x[2], "seed": x[3]} for x in CELLS],
        "rows": rows,
        "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dependency_sha256": hashlib.sha256((SCRATCH / "run_selector_check.py").read_bytes()).hexdigest(),
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps({"rows": len(rows), "output": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
