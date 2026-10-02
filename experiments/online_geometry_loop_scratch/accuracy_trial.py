"""One-seed accuracy trial for frozen P1 vs causal rolling/stateful routes.

This is a scratch-only evaluation harness. Both estimators consume a copy with
only radar/ADXL/sync algorithm inputs. Truth is loaded from the separate
generated package only after both routes finish, for post-run scoring.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.acceleration import preintegrate_acceleration_to_radar  # noqa: E402
from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from spatial_recovery_rebuilt.calibration_only.calibration_only_route import (  # noqa: E402
    run_calibration_only,
)
from spatial_recovery_rebuilt.rebuild_validation import (  # noqa: E402
    _write_scratch_package,
    freeze_guards,
    verify_frozen_test,
)
from algorithm.types import AccelerationInput  # noqa: E402

from experiments.online_geometry_loop_scratch.online_geometry_loop import (  # noqa: E402
    _copy_estimator_only,
    _run_loop,
)
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)


RADAR_RATE_HZ = 100.0
TEST_START = 200
TEST_STOP = 400
WINDOW_FRAMES = 20
SEED = 20261001
PHASE_RAMP_DELTA_SIN = 0.04


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _apply_phase_ramp(estimator_input: Path, delta_sin: float) -> dict[str, object]:
    """Shift virtual-array phase after frame 200, preserving target count."""
    manifest_path = estimator_input / "radar" / "algorithm_input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adc_path = manifest_path.parent / manifest["arrays"]["adc_cube"]["file"]
    adc = np.asarray(np.load(adc_path, allow_pickle=False), dtype=np.complex128)
    radar_meta = manifest["radar"]
    positions = np.asarray(radar_meta.get("virtual_array_positions_wavelengths", ()), dtype=float)
    if positions.size != adc.shape[1]:
        positions = np.arange(adc.shape[1], dtype=float) * 0.5
    steering_shift = np.exp(2j * np.pi * positions * float(delta_sin))
    adc[TEST_START:TEST_STOP] *= steering_shift[None, :, None]
    np.save(adc_path, adc, allow_pickle=False)
    return {
        "enabled": True,
        "frame_range": [TEST_START, TEST_STOP - 1],
        "delta_sin": float(delta_sin),
        "operation": "adc_virtual_rx *= exp(+2 pi j * position_wavelength * delta_sin)",
        "truth_q_proxy_or_paper_metadata_modified": False,
    }


def _slice_acceleration(capture, radar_time_ns: np.ndarray) -> AccelerationInput:
    structural = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns, capture.adxl_time_ns, structural
    )
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured = np.r_[interval_average[0], interval_average]
    return AccelerationInput(
        np.asarray(capture.adxl_time_ns, dtype=np.int64),
        structural,
        measured,
        preintegration,
    )


def _truth_reference(generated: Path, radar_time_ns: np.ndarray) -> tuple[np.ndarray, float]:
    truth = np.load(generated / "truth" / "displacement_m.npy", allow_pickle=False)
    truth_time = np.load(generated / "truth" / "time_ns.npy", allow_pickle=False)
    frame_time = np.load(generated / "sync" / "radar_adc_sample_monotonic_ns.npy", allow_pickle=False)
    frame_truth = np.interp(frame_time.astype(float), truth_time.astype(float), truth)
    elapsed = (frame_time.astype(float) - float(frame_time[0])) * 1.0e-9
    reference = float(np.mean(frame_truth[elapsed <= 0.20]))
    truth_test = np.interp(radar_time_ns.astype(float), truth_time.astype(float), truth)
    return truth_test - reference, reference


def _score(estimate: np.ndarray, truth_centered: np.ndarray, *, abstain: bool = False,
           reason: str | None = None) -> dict[str, object]:
    estimate = np.asarray(estimate, dtype=float)
    truth_centered = np.asarray(truth_centered, dtype=float)
    finite = np.isfinite(estimate) & np.isfinite(truth_centered)
    errors = estimate[finite] - truth_centered[finite]
    rmse_m = float(np.sqrt(np.mean(errors * errors))) if errors.size else None
    return {
        "sample_count": int(truth_centered.size),
        "finite_samples": int(np.sum(finite)),
        "coverage": float(np.mean(finite)) if finite.size else 0.0,
        "rmse_m": rmse_m,
        "rmse_mm": rmse_m * 1.0e3 if rmse_m is not None else None,
        "abstain": bool(abstain),
        "abstain_reason": reason,
    }


def _stable_range_slots(rows: list[dict[str, object]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    """Reindex each rolling row by unique range-bin IDs."""
    first_ranges = np.asarray(rows[0]["range_bins"], dtype=int)
    if np.unique(first_ranges).size != first_ranges.size:
        raise ValueError("rolling smoke requires unique baseline range bins for slot association")
    slot_ranges = first_ranges.copy()
    phase = np.full((slot_ranges.size, len(rows)), np.nan, dtype=float)
    beta = np.full((slot_ranges.size, len(rows)), np.nan, dtype=float)
    available = np.zeros((slot_ranges.size, len(rows)), dtype=bool)
    mismatch = 0
    for k, row in enumerate(rows):
        ranges = np.asarray(row["range_bins"], dtype=int)
        angles = np.asarray(row["angle_deg"], dtype=float)
        row_beta = np.asarray(row["beta"], dtype=float)
        row_phase = np.asarray(row["current_phase_rad"], dtype=float)
        if np.unique(ranges).size != ranges.size:
            mismatch += 1
            continue
        for j, range_bin in enumerate(ranges):
            slot = np.flatnonzero(slot_ranges == range_bin)
            if slot.size:
                s = int(slot[0])
                beta[s, k] = row_beta[j]
                phase[s, k] = row_phase[j]
                available[s, k] = np.isfinite(row_phase[j])
        # ``angles`` is read above to make the AoA path explicit in the record;
        # beta is allowed to change while the range-bin identity persists.
        _ = angles
    association = {
        "slot_key": "range_bin (unique in this synthetic condition)",
        "baseline_range_bins": slot_ranges.tolist(),
        "range_slot_mismatch_rows": mismatch,
        "target_count_first": int(len(rows[0]["range_bins"])),
        "target_count_last": int(len(rows[-1]["range_bins"])),
    }
    return phase, beta, available, association


def _run_route_pair(generated: Path, estimator_input: Path, *, condition: str,
                    seed: int) -> dict[str, object]:
    capture = load_capture_package(estimator_input)
    if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
        raise AssertionError("truth reached estimator CapturePackage")
    guards = freeze_guards(estimator_input)
    frozen_test = verify_frozen_test(estimator_input, guards)
    config = AlgorithmConfig(sample_rate_hz=RADAR_RATE_HZ)
    radar_time_ns = np.asarray(capture.radar_time_ns[TEST_START:TEST_STOP], dtype=np.int64)

    # P1: existing calibration-frozen geometry route, test-only retained Kalman.
    p1_result = None
    p1_started = time.monotonic()
    if frozen_test["passed"]:
        p1_result, p1_radar, _ = run_calibration_only(capture, config)
        p1_elapsed = time.monotonic() - p1_started
        p1_q = np.asarray(p1_result.q_hat_m, dtype=float)
    else:
        p1_elapsed = time.monotonic() - p1_started
        p1_radar = None
        p1_q = np.full(TEST_STOP - TEST_START, np.nan, dtype=float)

    # Causal rolling route: each geometry uses [t-19, t], then stateful step
    # consumes beta_t and the current phase. Initialization uses only t=200.
    rolling_started = time.monotonic()
    rows = _run_loop(
        capture,
        window_frames=WINDOW_FRAMES,
        output_frames=TEST_STOP - TEST_START,
        first_output_frame=TEST_START,
    )
    phase, beta, available, association = _stable_range_slots(rows)
    rolling_elapsed = time.monotonic() - rolling_started
    n_targets = phase.shape[0]
    reference_dt = float(np.median(np.diff(radar_time_ns)) * 1.0e-9)
    selected = np.arange(n_targets, dtype=int)
    adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=phase[:, 0],
        available_t=available[:, 0],
        selected_indices=selected,
        reference_dt_s=reference_dt,
    )
    acceleration = _slice_acceleration(capture, radar_time_ns)
    rolling_q = np.full(TEST_STOP - TEST_START, np.nan, dtype=float)
    for k in range(TEST_STOP - TEST_START):
        if k == 0:
            duration = reference_dt
            delta_q = delta_v = 0.0
        else:
            duration = float(acceleration.preintegration.duration_s[k - 1])
            delta_q = float(acceleration.preintegration.delta_q_m[k - 1])
            delta_v = float(acceleration.preintegration.delta_v_mps[k - 1])
        step = adapter.step(
            phase[:, k],
            beta[:, k],
            available[:, k],
            duration_s=duration,
            delta_q_m=delta_q,
            delta_v_mps=delta_v,
        )
        rolling_q[k] = float(step["q_hat_m"])

    # Truth is opened only after both estimator routes have completed.
    centered_truth, reference_m = _truth_reference(generated, radar_time_ns)
    p1_score = _score(
        p1_q,
        centered_truth,
        abstain=not bool(frozen_test["passed"]),
        reason=None if frozen_test["passed"] else "frozen_test_guard_failed",
    )
    rolling_finite = bool(np.isfinite(rolling_q).all())
    rolling_score = _score(
        rolling_q,
        centered_truth,
        abstain=not rolling_finite,
        reason=None if rolling_finite else "nonfinite_stateful_output",
    )
    beta_first = beta[:, 0]
    beta_last = beta[:, -1]
    angle_first = np.asarray(rows[0]["angle_deg"], dtype=float)
    angle_last = np.asarray(rows[-1]["angle_deg"], dtype=float)
    return {
        "schema": "online_geometry_loop_accuracy_trial",
        "status": "completed",
        "condition": condition,
        "seed": seed,
        "radar_test_frames": [TEST_START, TEST_STOP - 1],
        "estimator_input": {
            "truth_present": (estimator_input / "truth").exists(),
            "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
            "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
            "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            "truth_used_by_estimator": False,
            "q_proxy_used_by_estimator": False,
        },
        "guard": {
            "calibration_source_only": guards["source"] == "calibration_capture_arrays_only",
            "frozen_test": frozen_test,
        },
        "truth_reference_post_run": {
            "reference_m": reference_m,
            "sample_count": int(centered_truth.size),
            "not_passed_to_estimator": True,
        },
        "p1_frozen": {
            "route": "calibration frames 0:199; retained run_calibration_only on test 200:399",
            "elapsed_s": p1_elapsed,
            "score": p1_score,
            "beta_source": "calibration-frozen angle geometry",
            "target_count": int(p1_radar.selected_indices.size) if p1_radar is not None else None,
        },
        "causal_rolling_stateful": {
            "route": "20-frame causal rolling geometry; stateful beta_t adapter on frames 200:399",
            "elapsed_s": rolling_elapsed,
            "score": rolling_score,
            "state_sample_index": int(adapter.state.sample_index),
            "state_continuous": int(adapter.state.sample_index) == TEST_STOP - TEST_START,
            "target_slots": association,
            "beta_first": beta_first.tolist(),
            "beta_last": beta_last.tolist(),
            "beta_max_abs_change": float(np.max(np.abs(beta_last - beta_first))),
            "angle_first_deg": angle_first.tolist(),
            "angle_last_deg": angle_last.tolist(),
            "angle_max_abs_change_deg": float(np.max(np.abs(angle_last - angle_first))),
            "rolling_target_count_min": int(min(len(row["range_bins"]) for row in rows)),
            "rolling_target_count_max": int(max(len(row["range_bins"]) for row in rows)),
        },
        "accuracy_claim": False,
    }


def run_trial(output: Path, *, seed: int = SEED, condition: str = "both") -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    conditions = ["baseline_no_drift", "post_200_phase_ramp"] if condition == "both" else [condition]
    records: list[dict[str, object]] = []
    for name in conditions:
        with tempfile.TemporaryDirectory(prefix=f"accuracy-trial-{name}-") as temporary:
            root = Path(temporary)
            generated = root / "generated_with_evaluation_artifacts"
            estimator_input = root / "estimator_input_truth_free"
            _write_scratch_package(
                generated,
                stratum_name="stationary",
                requested_rms_mm=0.0,
                seed=seed,
            )
            _copy_estimator_only(generated, estimator_input)
            perturbation = {"enabled": False}
            if name == "post_200_phase_ramp":
                perturbation = _apply_phase_ramp(estimator_input, PHASE_RAMP_DELTA_SIN)
            record = _run_route_pair(generated, estimator_input, condition=name, seed=seed)
            record["condition_input"] = perturbation
            records.append(record)
            _json(output / f"{name}.json", record)
    summary = {
        "schema": "online_geometry_loop_accuracy_trial_summary",
        "status": "completed",
        "seed": seed,
        "conditions": [record["condition"] for record in records],
        "truth_q_proxy_or_paper_metadata_to_estimator": False,
        "accuracy_claim": False,
        "routes": [
            {
                "condition": record["condition"],
                "p1_frozen": record["p1_frozen"]["score"],
                "causal_rolling_stateful": record["causal_rolling_stateful"]["score"],
            }
            for record in records
        ],
    }
    _json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one-seed frozen-vs-causal scratch accuracy trial")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--condition",
        choices=("both", "baseline_no_drift", "post_200_phase_ramp"),
        default="both",
    )
    args = parser.parse_args()
    summary = run_trial(args.output, seed=args.seed, condition=args.condition)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
