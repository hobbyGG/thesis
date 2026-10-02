"""Read-only, truth-free bootstrap-mode feature analysis.

The script regenerates the same estimator-copy packages used by the scratch
gauge diagnostics, records the first 20 causal rolling windows, and applies
the pre-registered rule in ``gauge_mode_classifier_design.json`` without any
truth input or threshold tuning.  It is a separability diagnostic only; it
does not run a displacement estimator or report accuracy.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402

from experiments.online_geometry_loop_scratch.accuracy_trial import (  # noqa: E402
    PHASE_RAMP_DELTA_SIN,
    TEST_START,
    _apply_phase_ramp,
    _copy_estimator_only,
    _stable_range_slots,
)
from experiments.online_geometry_loop_scratch.gauge_fix_diagnostic import (  # noqa: E402
    _apply_angle_migration,
    _apply_phase_ramp_from_frame,
    _stable_angles,
)
from experiments.online_geometry_loop_scratch.online_geometry_loop import _run_loop  # noqa: E402


SEEDS = (20261001, 20261002, 20261003)
CONDITIONS = ("baseline_no_drift", "post_200_phase_ramp", "pre_window_phase_ramp", "angle_migration")
BOOTSTRAP_FRAMES = 20
GAUGE_RMS_THRESHOLD_RAD = 0.10
PHASE_RMS_THRESHOLD_RAD = 0.10
CORRELATION_THRESHOLD = 0.70


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_default) + "\n", encoding="utf-8")


def _default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _condition_input(estimator_input: Path, condition: str) -> dict[str, object]:
    if condition == "baseline_no_drift":
        return {"enabled": False}
    if condition == "post_200_phase_ramp":
        return _apply_phase_ramp(estimator_input, PHASE_RAMP_DELTA_SIN)
    if condition == "pre_window_phase_ramp":
        return _apply_phase_ramp_from_frame(
            estimator_input,
            start_frame=TEST_START - (BOOTSTRAP_FRAMES - 1),
            delta_sin=PHASE_RAMP_DELTA_SIN,
        )
    if condition == "angle_migration":
        return _apply_angle_migration(
            estimator_input,
            start_frame=TEST_START,
            ramp_frames=40,
            delta_sin=PHASE_RAMP_DELTA_SIN,
        )
    raise ValueError(condition)


def _circular_difference(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    reference = np.asarray(reference, dtype=float)
    if reference.ndim == 2 and reference.shape[1] == 1:
        reference = reference[:, 0]
    return np.angle(np.exp(1j * (values - reference[:, None])))


def _slot_feature_table(
    phase: np.ndarray, angles: np.ndarray, *, centroid: float
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Return first-20 u/r/g traces plus fixed-rule aggregate features."""
    phase = np.asarray(phase, dtype=float)[:, :BOOTSTRAP_FRAMES]
    angles = np.asarray(angles, dtype=float)[:, :BOOTSTRAP_FRAMES]
    u = np.sin(np.deg2rad(angles))
    gauge = -2.0 * np.pi * centroid * (u - u[:, [0]])
    residual = _circular_difference(phase, phase[:, [0]])
    slot_rows: list[dict[str, object]] = []
    all_r: list[float] = []
    all_g: list[float] = []
    corr_values: list[float] = []
    step_values: list[float] = []
    for i in range(u.shape[0]):
        valid = np.isfinite(u[i]) & np.isfinite(gauge[i]) & np.isfinite(residual[i])
        valid[0] = False
        r = residual[i, valid]
        g = gauge[i, valid]
        du = np.diff(u[i])[np.isfinite(np.diff(u[i]))]
        if r.size >= 2 and np.std(r) > 1.0e-12 and np.std(g) > 1.0e-12:
            corr = float(np.corrcoef(r, g)[0, 1])
            corr_values.append(corr)
        else:
            corr = None
        if r.size:
            all_r.extend(r.tolist())
        if g.size:
            all_g.extend(g.tolist())
        if du.size:
            step_values.extend(np.abs(du).tolist())
        slot_rows.append({
            "slot": i,
            "u_first20": u[i].tolist(),
            "phase_residual_first20_rad": residual[i].tolist(),
            "gauge_prediction_first20_rad": gauge[i].tolist(),
            "finite_samples": int(r.size),
            "phase_rms_rad": float(np.sqrt(np.mean(r * r))) if r.size else None,
            "gauge_rms_rad": float(np.sqrt(np.mean(g * g))) if g.size else None,
            "residual_gauge_correlation": corr,
            "median_abs_u_step": float(np.median(np.abs(du))) if du.size else None,
        })
    r_all = np.asarray(all_r, dtype=float)
    g_all = np.asarray(all_g, dtype=float)
    if r_all.size and g_all.size and np.std(r_all) > 1.0e-12 and np.std(g_all) > 1.0e-12:
        correlation = float(np.corrcoef(r_all, g_all)[0, 1])
    else:
        correlation = None
    aggregate = {
        "feature_samples": int(r_all.size),
        "feature_coverage": float(r_all.size / max(u.shape[0] * (BOOTSTRAP_FRAMES - 1), 1)),
        "phase_rms_rad": float(np.sqrt(np.mean(r_all * r_all))) if r_all.size else None,
        "gauge_rms_rad": float(np.sqrt(np.mean(g_all * g_all))) if g_all.size else None,
        "residual_gauge_correlation": correlation,
        "median_abs_u_step": float(np.median(np.asarray(step_values))) if step_values else None,
    }
    return slot_rows, aggregate


def _decision(features: dict[str, object]) -> str:
    g = features["gauge_rms_rad"]
    r = features["phase_rms_rad"]
    c = features["residual_gauge_correlation"]
    if g is None or r is None:
        return "ambiguous"
    if g >= GAUGE_RMS_THRESHOLD_RAD and r >= PHASE_RMS_THRESHOLD_RAD and c is not None and c >= CORRELATION_THRESHOLD:
        return "gauge_boundary_candidate"
    if g >= GAUGE_RMS_THRESHOLD_RAD and r < PHASE_RMS_THRESHOLD_RAD:
        return "tracked_or_settled_geometry_change"
    if g < GAUGE_RMS_THRESHOLD_RAD and r < PHASE_RMS_THRESHOLD_RAD:
        return "stable_or_no_geometry_change"
    return "ambiguous"


def run(output: Path, *, seeds: tuple[int, ...] = SEEDS, conditions: tuple[str, ...] = CONDITIONS) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for seed in seeds:
        for condition in conditions:
            with tempfile.TemporaryDirectory(prefix=f"mode-classifier-{seed}-{condition}-") as temporary:
                root = Path(temporary)
                generated = root / "generated_with_evaluation_artifacts"
                estimator_input = root / "estimator_input_truth_free"
                _write_scratch_package(generated, stratum_name="stationary", requested_rms_mm=0.0, seed=seed)
                _copy_estimator_only(generated, estimator_input)
                perturbation = _condition_input(estimator_input, condition)
                capture = load_capture_package(estimator_input)
                if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
                    raise AssertionError("truth reached classifier estimator")
                rows = _run_loop(
                    capture,
                    window_frames=BOOTSTRAP_FRAMES,
                    output_frames=BOOTSTRAP_FRAMES,
                    first_output_frame=TEST_START,
                )
                phase, _, _, association = _stable_range_slots(rows)
                angles = _stable_angles(rows, np.asarray(association["baseline_range_bins"], dtype=int))
                positions = np.asarray(capture.frontend.virtual_array_positions_wavelengths, dtype=float)
                if positions.size == 0:
                    positions = np.arange(capture.frontend.num_virtual_rx, dtype=float) * capture.frontend.antenna_spacing_wavelengths
                slots, features = _slot_feature_table(phase, angles, centroid=float(np.mean(positions)))
                record = {
                    "schema": "online_geometry_loop_gauge_mode_classifier_features",
                    "status": "diagnostic_only",
                    "seed": seed,
                    "condition": condition,
                    "bootstrap_frame_range": [TEST_START, TEST_START + BOOTSTRAP_FRAMES - 1],
                    "estimator_input": {
                        "truth_present": (estimator_input / "truth").exists(),
                        "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
                        "capture_truth_loaded": False,
                        "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
                    },
                    "condition_input": perturbation,
                    "target_slots": association,
                    "array_centroid_wavelengths": float(np.mean(positions)),
                    "features": features,
                    "slot_features": slots,
                    "pre_registered_rule": {
                        "gauge_rms_threshold_rad": GAUGE_RMS_THRESHOLD_RAD,
                        "phase_rms_threshold_rad": PHASE_RMS_THRESHOLD_RAD,
                        "correlation_threshold": CORRELATION_THRESHOLD,
                    },
                    "route_decision": _decision(features),
                    "accuracy_claim": False,
                }
                records.append(record)
                _json(output / f"{seed}_{condition}.json", record)
    decisions = [r["route_decision"] for r in records]
    summary = {
        "schema": "online_geometry_loop_gauge_mode_classifier_summary",
        "status": "diagnostic_only",
        "seeds": list(seeds),
        "conditions": list(conditions),
        "records": len(records),
        "decision_counts": {name: decisions.count(name) for name in sorted(set(decisions))},
        "truth_free_estimator_copy": True,
        "thresholds_untuned": True,
        "accuracy_claim": False,
        "failure_boundary": "A ramp already settled before bootstrap and a genuinely smooth migration can both produce low phase residual; classifier must abstain without slope/context features.",
    }
    _json(output / "summary.json", summary)
    _json(output / "protocol.json", {
        "schema": "online_geometry_loop_gauge_mode_classifier_protocol",
        "bootstrap_frames": [TEST_START, TEST_START + BOOTSTRAP_FRAMES - 1],
        "truth_free_features": ["u_t", "phase_residual_t", "gauge_prediction_t", "AoA step MAD", "residual-gauge correlation"],
        "pre_registered_thresholds": {
            "gauge_rms_rad": GAUGE_RMS_THRESHOLD_RAD,
            "phase_rms_rad": PHASE_RMS_THRESHOLD_RAD,
            "correlation": CORRELATION_THRESHOLD,
        },
        "truth_or_q_proxy_used": False,
        "accuracy_claim": False,
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Record truth-free bootstrap mode features")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.output)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
