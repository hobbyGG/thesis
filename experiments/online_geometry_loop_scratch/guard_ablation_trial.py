"""Pre-registered one-seed guard ablation for rolling beta/AoA updates.

Only fixed engineering thresholds are used:

* reject a geometry update when any matched AoA jump exceeds 0.20 degrees;
* reject when any matched beta relative change exceeds 0.5 percent.

Thresholds compare adjacent raw rolling windows. On rejection, the previous
accepted beta/slot state is used. An explicit
abstain is counted only when no selected slot has a finite current phase, so a
guard fallback remains distinguishable from an estimator abstention. Truth is
opened only after both rolling routes finish.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.config import AlgorithmConfig
from algorithm.io import load_capture_package
from algorithm.acceleration import preintegrate_acceleration_to_radar
from algorithm.types import AccelerationInput
from spatial_recovery_rebuilt.calibration_only.calibration_only_route import run_calibration_only
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package, freeze_guards, verify_frozen_test

from experiments.online_geometry_loop_scratch.accuracy_trial import (  # noqa: E402
    PHASE_RAMP_DELTA_SIN,
    RADAR_RATE_HZ,
    TEST_START,
    TEST_STOP,
    _apply_phase_ramp,
    _copy_estimator_only,
    _score,
    _stable_range_slots,
    _truth_reference,
)
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)
from experiments.online_geometry_loop_scratch.online_geometry_loop import _run_loop  # noqa: E402


SEED = 20261001
WINDOW_FRAMES = 20
AOA_JUMP_THRESHOLD_DEG = 0.20
BETA_REL_CHANGE_THRESHOLD = 0.005


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n", encoding="utf-8")


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _slice_acceleration(capture, radar_time_ns: np.ndarray) -> AccelerationInput:
    structural = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(radar_time_ns, capture.adxl_time_ns, structural)
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    return AccelerationInput(capture.adxl_time_ns, structural, np.r_[interval_average[0], interval_average], preintegration)


def _stable_angles(rows: list[dict[str, object]], slot_ranges: np.ndarray) -> np.ndarray:
    angles = np.full((slot_ranges.size, len(rows)), np.nan, dtype=float)
    for k, row in enumerate(rows):
        for range_bin, angle in zip(row["range_bins"], row["angle_deg"]):
            slot = np.flatnonzero(slot_ranges == int(range_bin))
            if slot.size:
                angles[int(slot[0]), k] = float(angle)
    return angles


def _run_condition(generated: Path, estimator_input: Path, *, condition: str, seed: int) -> dict[str, object]:
    capture = load_capture_package(estimator_input)
    if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
        raise AssertionError("truth reached guard estimator")
    guards = freeze_guards(estimator_input)
    frozen_test = verify_frozen_test(estimator_input, guards)
    config = AlgorithmConfig(sample_rate_hz=RADAR_RATE_HZ)
    radar_time_ns = np.asarray(capture.radar_time_ns[TEST_START:TEST_STOP], dtype=np.int64)

    # Frozen P1 reference.
    if frozen_test["passed"]:
        p1_result, p1_radar, _ = run_calibration_only(capture, config)
        p1_q = np.asarray(p1_result.q_hat_m, dtype=float)
    else:
        p1_radar = None
        p1_q = np.full(TEST_STOP - TEST_START, np.nan, dtype=float)

    rows = _run_loop(capture, window_frames=WINDOW_FRAMES, output_frames=TEST_STOP - TEST_START, first_output_frame=TEST_START)
    phase, beta_raw, available, association = _stable_range_slots(rows)
    slot_ranges = np.asarray(association["baseline_range_bins"], dtype=int)
    angle_raw = _stable_angles(rows, slot_ranges)
    reference_dt = float(np.median(np.diff(radar_time_ns)) * 1.0e-9)
    acceleration = _slice_acceleration(capture, radar_time_ns)
    selected = np.arange(slot_ranges.size, dtype=int)

    # Guard state is updated only from observable geometry; no truth enters.
    accepted_beta = beta_raw[:, 0].copy()
    accepted_angle = angle_raw[:, 0].copy()
    # Guard thresholds are evaluated against the immediately preceding raw
    # window. A rejected update still falls back to the last accepted state,
    # but does not make the next adjacent-window comparison cumulative.
    previous_raw_beta = beta_raw[:, 0].copy()
    previous_raw_angle = angle_raw[:, 0].copy()
    accepted_count = 1
    guard_reject_count = 0
    fallback_count = 0
    abstain_count = 0
    guard_flags: list[dict[str, object]] = [{"frame_index": TEST_START, "accepted": True, "reason": "bootstrap"}]

    raw_adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=phase[:, 0],
        available_t=available[:, 0],
        selected_indices=selected,
        reference_dt_s=reference_dt,
    )
    guarded_adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=phase[:, 0],
        available_t=available[:, 0],
        selected_indices=selected,
        reference_dt_s=reference_dt,
    )
    raw_q = np.full(TEST_STOP - TEST_START, np.nan, dtype=float)
    guarded_q = np.full(TEST_STOP - TEST_START, np.nan, dtype=float)
    raw_q[0] = float(raw_adapter.step(phase[:, 0], beta_raw[:, 0], available[:, 0])["q_hat_m"])
    guarded_q[0] = float(guarded_adapter.step(phase[:, 0], accepted_beta, available[:, 0])["q_hat_m"])
    for k in range(1, TEST_STOP - TEST_START):
        duration = float(acceleration.preintegration.duration_s[k - 1])
        delta_q = float(acceleration.preintegration.delta_q_m[k - 1])
        delta_v = float(acceleration.preintegration.delta_v_mps[k - 1])
        raw_step = raw_adapter.step(
            phase[:, k], beta_raw[:, k], available[:, k], duration_s=duration, delta_q_m=delta_q, delta_v_mps=delta_v
        )
        raw_q[k] = float(raw_step["q_hat_m"])
        current_angle = angle_raw[:, k]
        current_beta = beta_raw[:, k]
        matched = np.isfinite(current_angle) & np.isfinite(previous_raw_angle) & np.isfinite(current_beta) & np.isfinite(previous_raw_beta)
        aoa_jump = float(np.max(np.abs(current_angle[matched] - previous_raw_angle[matched]))) if np.any(matched) else float("inf")
        beta_rel = float(np.max(np.abs(current_beta[matched] / previous_raw_beta[matched] - 1.0))) if np.any(matched) else float("inf")
        reasons = []
        if aoa_jump > AOA_JUMP_THRESHOLD_DEG:
            reasons.append("aoa_jump")
        if beta_rel > BETA_REL_CHANGE_THRESHOLD:
            reasons.append("beta_relative_change")
        accepted = not reasons
        if accepted:
            accepted_angle = current_angle.copy()
            accepted_beta = current_beta.copy()
            accepted_count += 1
        else:
            guard_reject_count += 1
            fallback_count += 1
        has_measurement = bool(np.any(available[:, k] & np.isfinite(phase[:, k])))
        if not has_measurement:
            abstain_count += 1
        guarded_step = guarded_adapter.step(
            phase[:, k],
            accepted_beta,
            available[:, k] if has_measurement else np.zeros_like(available[:, k]),
            duration_s=duration,
            delta_q_m=delta_q,
            delta_v_mps=delta_v,
        )
        guarded_q[k] = np.nan if not has_measurement else float(guarded_step["q_hat_m"])
        guard_flags.append({
            "frame_index": TEST_START + k,
            "accepted": accepted,
            "reasons": reasons,
            "aoa_jump_deg": aoa_jump,
            "beta_relative_change": beta_rel,
            "fallback_previous_geometry": not accepted,
            "measurement_available": has_measurement,
        })
        previous_raw_beta = current_beta.copy()
        previous_raw_angle = current_angle.copy()

    centered_truth, reference_m = _truth_reference(generated, radar_time_ns)
    return {
        "schema": "online_geometry_loop_guard_ablation_trial",
        "status": "completed",
        "condition": condition,
        "seed": seed,
        "guard_thresholds": {
            "aoa_jump_deg": AOA_JUMP_THRESHOLD_DEG,
            "beta_relative_change": BETA_REL_CHANGE_THRESHOLD,
            "source": "fixed engineering thresholds, pre-registered before scoring",
        },
        "estimator_input": {
            "truth_present": (estimator_input / "truth").exists(),
            "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
            "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
            "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            "truth_or_q_proxy_used_by_estimator": False,
        },
        "frozen_guard": frozen_test,
        "truth_reference_post_run": {"reference_m": reference_m, "not_passed_to_estimator": True},
        "p1_frozen": {
            "target_count": int(p1_radar.selected_indices.size) if p1_radar is not None else None,
            "score": _score(p1_q, centered_truth, abstain=not bool(frozen_test["passed"]), reason=None if frozen_test["passed"] else "frozen_test_guard_failed"),
        },
        "rolling_raw": {
            "score": _score(raw_q, centered_truth),
            "target_slots": association,
        },
        "rolling_guarded": {
            "score": _score(guarded_q, centered_truth, abstain=abstain_count > 0, reason="no_measurement" if abstain_count else None),
            "target_slots": association,
            "accepted_geometry_updates": accepted_count,
            "guard_reject_count": guard_reject_count,
            "fallback_count": fallback_count,
            "abstain_count": abstain_count,
            "guard_flags": guard_flags,
        },
        "accuracy_claim": False,
    }


def run_trial(output: Path, *, seed: int = SEED, condition: str = "both") -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    conditions = ["baseline_no_drift", "post_200_phase_ramp"] if condition == "both" else [condition]
    records = []
    for name in conditions:
        with tempfile.TemporaryDirectory(prefix=f"guard-ablation-{name}-") as temporary:
            root = Path(temporary)
            generated = root / "generated_with_evaluation_artifacts"
            estimator_input = root / "estimator_input_truth_free"
            _write_scratch_package(generated, stratum_name="stationary", requested_rms_mm=0.0, seed=seed)
            _copy_estimator_only(generated, estimator_input)
            perturbation = {"enabled": False}
            if name == "post_200_phase_ramp":
                perturbation = _apply_phase_ramp(estimator_input, PHASE_RAMP_DELTA_SIN)
            record = _run_condition(generated, estimator_input, condition=name, seed=seed)
            record["condition_input"] = perturbation
            records.append(record)
            _json(output / f"{name}.json", record)
    summary = {
        "schema": "online_geometry_loop_guard_ablation_summary",
        "status": "completed",
        "seed": seed,
        "guard_thresholds": {"aoa_jump_deg": AOA_JUMP_THRESHOLD_DEG, "beta_relative_change": BETA_REL_CHANGE_THRESHOLD},
        "conditions": [
            {
                "condition": record["condition"],
                "p1_frozen": record["p1_frozen"]["score"],
                "rolling_raw": record["rolling_raw"]["score"],
                "rolling_guarded": record["rolling_guarded"]["score"],
                "guard_reject_count": record["rolling_guarded"]["guard_reject_count"],
                "fallback_count": record["rolling_guarded"]["fallback_count"],
                "abstain_count": record["rolling_guarded"]["abstain_count"],
            }
            for record in records
        ],
        "truth_q_proxy_or_paper_metadata_to_estimator": False,
        "accuracy_claim": False,
    }
    _json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixed-threshold AoA/beta guard ablation")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--condition", choices=("both", "baseline_no_drift", "post_200_phase_ramp"), default="both")
    args = parser.parse_args()
    summary = run_trial(args.output, seed=args.seed, condition=args.condition)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
