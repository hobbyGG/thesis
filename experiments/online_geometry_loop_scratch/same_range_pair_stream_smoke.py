"""Causal same-range angular-pair association smoke.

This uses the locked ``final_v2`` same-range IQ generator only as a data source:
the estimator receives IQ and fixed instrument constants, never q or target
metadata.  Every test frame gets a past-only 20-frame angle estimate.  Pair
slots are keyed by ``(range_bin, angle_track)`` so two returns sharing one range
cell can feed the stateful beta adapter without shifting one target into the
other's slot.  This is an interface smoke, not displacement evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.same_range_merge_mechanism.final_v2.run_experiment import (  # noqa: E402
    geometry,
    generate,
    steering,
)
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)
from algorithm.config import AlgorithmConfig  # noqa: E402


SEED = 100
CASE = "separated_benign"
# The final_v2 generator is a one-cell IQ model.  Zero is the observed local
# cell index, not a target-provided range label.
RANGE_BIN = 0
WINDOW_FRAMES = 20
CALIBRATION_END = 128
TEST_STOP = 256
RADAR_RATE_HZ = 100.0


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n", encoding="utf-8")


def _track_angles(previous: np.ndarray | None, detected: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """Assign 0/1 angle tracks by nearest previous angle, without truth IDs."""
    values = np.asarray(detected, dtype=float)
    if values.size > 2:
        values = values[:2]
    if previous is None:
        values = np.sort(values)
        return values, np.arange(values.size, dtype=int)
    tracks: list[int] = []
    used: set[int] = set()
    for value in values:
        candidates = [i for i in range(previous.size) if i not in used]
        if not candidates:
            break
        track = min(candidates, key=lambda i: abs(float(previous[i]) - float(value)))
        tracks.append(track)
        used.add(track)
    return values[: len(tracks)], np.asarray(tracks, dtype=int)


def _project_sample(sample: np.ndarray, angles: np.ndarray) -> np.ndarray:
    if angles.size == 0:
        return np.empty(0, dtype=complex)
    # Same least-squares source projection as final_v2, but only current IQ is
    # passed.  No generator angles, amplitudes, phase offsets or q are used.
    return np.asarray(sample, dtype=complex) @ np.linalg.pinv(steering(angles)).T


def _make_observations(z: np.ndarray) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    previous: np.ndarray | None = None
    for frame in range(CALIBRATION_END, TEST_STOP):
        start = frame - WINDOW_FRAMES + 1
        detected, _ = geometry(z[start : frame + 1])
        angles, tracks = _track_angles(previous, detected)
        previous = angles.copy() if angles.size else previous
        # The frame's own current sample is projected with geometry from the
        # window ending at that frame.  The input is one same-range cell.
        source = _project_sample(z[frame], angles)
        slot_angles = np.full(2, np.nan, dtype=float)
        slot_phase = np.full(2, np.nan, dtype=float)
        slot_beta = np.full(2, np.nan, dtype=float)
        available = np.zeros(2, dtype=bool)
        for local, track in enumerate(tracks):
            slot_angles[int(track)] = float(angles[local])
            slot_phase[int(track)] = float(np.angle(source[local]))
            slot_beta[int(track)] = float(1.0 / abs(np.cos(np.deg2rad(angles[local]))))
            available[int(track)] = True
        # Keep the merge route on the persistent track-0 angle; it represents
        # one conventional same-range phasor while split keeps both tracks.
        merge_angle = slot_angles[0] if np.isfinite(slot_angles[0]) else (angles[0] if angles.size else np.nan)
        merge_source = _project_sample(z[frame], np.asarray([merge_angle])) if np.isfinite(merge_angle) else np.empty(0, dtype=complex)
        observations.append({
            "frame_index": frame,
            "window_frame_range": [start, frame],
            "detected_angle_count": int(angles.size),
            "raw_angles_deg": angles.tolist(),
            "track_indices": tracks.tolist(),
            "slot_keys": [[RANGE_BIN, int(track)] for track in tracks],
            "angle_deg": slot_angles.tolist(),
            "beta": slot_beta.tolist(),
            "phase_rad": slot_phase.tolist(),
            "available": available.tolist(),
            "merge_angle_deg": float(merge_angle) if np.isfinite(merge_angle) else None,
            "merge_beta": float(1.0 / abs(np.cos(np.deg2rad(merge_angle)))) if np.isfinite(merge_angle) else None,
            "merge_phase_rad": float(np.angle(merge_source[0])) if merge_source.size else None,
            "merge_available": bool(np.isfinite(merge_source[0])) if merge_source.size else False,
            "range_bin": RANGE_BIN,
        })
    return observations


def _run_stateful(observations: list[dict[str, object]], mode: str) -> dict[str, object]:
    n_slots = 2 if mode == "split_ls" else 1
    first = observations[0]
    if mode == "merge":
        phase = np.asarray([first["merge_phase_rad"]], dtype=float)
        beta = np.asarray([first["merge_beta"]], dtype=float)
        available = np.asarray([first["merge_available"]], dtype=bool)
    else:
        phase = np.asarray(first["phase_rad"], dtype=float)[:n_slots]
        beta = np.asarray(first["beta"], dtype=float)[:n_slots]
        available = np.asarray(first["available"], dtype=bool)[:n_slots]
    # Missing split slots keep a finite beta from the first observed geometry;
    # availability remains false and cannot contaminate another slot.
    if not np.isfinite(beta).all():
        beta[~np.isfinite(beta)] = 1.0
    adapter = StatefulKalmanAdapter.from_initial_sample(
        AlgorithmConfig(sample_rate_hz=RADAR_RATE_HZ),
        wrapped_phase_t=np.nan_to_num(phase, nan=0.0),
        available_t=available,
        selected_indices=np.arange(n_slots, dtype=int),
        reference_dt_s=1.0 / RADAR_RATE_HZ,
    )
    q_trace: list[float] = []
    beta_trace: list[list[float]] = []
    for index, row in enumerate(observations):
        if mode == "merge":
            phase = np.asarray([row["merge_phase_rad"]], dtype=float)
            beta = np.asarray([row["merge_beta"]], dtype=float)
            available = np.asarray([row["merge_available"]], dtype=bool)
        else:
            phase = np.asarray(row["phase_rad"], dtype=float)[:n_slots]
            beta = np.asarray(row["beta"], dtype=float)[:n_slots]
            available = np.asarray(row["available"], dtype=bool)[:n_slots]
        if not np.isfinite(beta).all():
            beta[~np.isfinite(beta)] = 1.0
        step = adapter.step(
            np.nan_to_num(phase, nan=0.0), beta, available,
            duration_s=1.0 / RADAR_RATE_HZ,
        )
        q_trace.append(float(step["q_hat_m"]))
        beta_trace.append(beta.tolist())
    return {
        "mode": mode,
        "slot_count": n_slots,
        "sample_count": len(observations),
        "state_sample_index": int(adapter.state.sample_index),
        "state_continuous": int(adapter.state.sample_index) == len(observations),
        "finite_q_count": int(np.sum(np.isfinite(q_trace))),
        "q_trace_m": q_trace,
        "beta_trace": beta_trace,
        "beta_history_shape": [len(adapter.beta_history), n_slots],
    }


def _post_run_score(q_trace_m: list[float], truth_mm: np.ndarray, bootstrap_frames: int) -> dict[str, object]:
    """Score only after the declared prefix; truth enters here and nowhere earlier."""
    estimate_mm = np.asarray(q_trace_m, dtype=float) * 1.0e3
    truth = np.asarray(truth_mm, dtype=float)
    estimate = estimate_mm[bootstrap_frames:]
    target = truth[bootstrap_frames:]
    finite = np.isfinite(estimate) & np.isfinite(target)
    error = estimate[finite] - target[finite]
    rmse = float(np.sqrt(np.mean(error * error))) if error.size else None
    return {
        "sample_count": int(target.size),
        "finite_samples": int(np.sum(finite)),
        "coverage": float(np.mean(finite)) if finite.size else 0.0,
        "rmse_mm": rmse,
        "max_abs_error_mm": float(np.max(np.abs(error))) if error.size else None,
    }


def run_smoke(output: Path, *, seed: int = SEED) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    # `truth` is intentionally discarded at the generator boundary.  It is
    # not passed to geometry, association, projection, or the beta adapter.
    z, _ = generate(CASE, seed)
    observations = _make_observations(np.asarray(z, dtype=complex))
    keys = [tuple(row["slot_keys"][0]) for row in observations if row["slot_keys"]]
    stable_two_slot_rows = sum(int(row["detected_angle_count"]) == 2 for row in observations)
    if stable_two_slot_rows != len(observations):
        raise AssertionError("same-range pair was not detected in every causal window")
    if not all(len(row["slot_keys"]) == 2 and row["slot_keys"] == [[RANGE_BIN, 0], [RANGE_BIN, 1]] for row in observations):
        raise AssertionError("same-range angle-track slots are not stable")
    states = {mode: _run_stateful(observations, mode) for mode in ("split_ls", "merge")}
    for mode, state in states.items():
        if not state["state_continuous"] or state["finite_q_count"] != len(observations):
            raise AssertionError(f"stateful {mode} route did not consume all beta samples")
    # Re-open the deterministic generator's truth only after all estimator
    # routes have consumed the IQ stream.  Verify that this is the same IQ
    # realization without passing q into any route.
    z_check, truth_mm = generate(CASE, seed)
    if not np.array_equal(np.asarray(z_check), np.asarray(z)):
        raise AssertionError("deterministic IQ regeneration mismatch")
    centered_truth_mm = np.asarray(truth_mm, dtype=float)[CALIBRATION_END:TEST_STOP]
    bootstrap_frames = 20
    scores = {
        mode: _post_run_score(state["q_trace_m"], centered_truth_mm, bootstrap_frames)
        for mode, state in states.items()
    }
    report = {
        "schema": "online_geometry_loop_same_range_pair_stream_smoke",
        "status": "smoke_passed",
        "scope": "same-range angular association and stateful beta interface only",
        "seed": seed,
        "generator_case": CASE,
        "source_protocol": "experiments/same_range_merge_mechanism/final_v2/PROTOCOL.md",
        "superseded_v1_used": False,
        "same_range": True,
        "range_bin": RANGE_BIN,
        "window_frames": WINDOW_FRAMES,
        "calibration_end_frame": CALIBRATION_END - 1,
        "test_frame_range": [CALIBRATION_END, TEST_STOP - 1],
        "estimator_inputs": ["current/past IQ window", "fixed array positions", "current sample"],
        "forbidden_estimator_inputs": ["q", "truth target angles", "target amplitudes", "static phases", "q_proxy"],
        "association": {
            "key": "(range_bin, angle_track)",
            "track_assignment": "nearest previous refined angle; initial tracks sorted by angle",
            "observations": len(observations),
            "stable_two_slot_rows": stable_two_slot_rows,
            "unique_slot_keys": [[RANGE_BIN, 0], [RANGE_BIN, 1]],
            "slot_keys_stable": True,
            "raw_angle_span_deg": [
                float(np.nanmin(np.asarray([row["angle_deg"] for row in observations], dtype=float)[:, 0])),
                float(np.nanmax(np.asarray([row["angle_deg"] for row in observations], dtype=float)[:, 1])),
            ],
        },
        "stateful_routes": states,
        "scores_post_run_truth": {
            "truth_loaded_after_estimator": True,
            "trial_count": 1,
            "bootstrap_frames_excluded": bootstrap_frames,
            "test_frame_range": [CALIBRATION_END + bootstrap_frames, TEST_STOP - 1],
            "split_ls": scores["split_ls"],
            "merge": scores["merge"],
            "paired_split_minus_merge_rmse_mm": (
                scores["split_ls"]["rmse_mm"] - scores["merge"]["rmse_mm"]
                if scores["split_ls"]["rmse_mm"] is not None and scores["merge"]["rmse_mm"] is not None
                else None
            ),
        },
        "truth_or_q_proxy_used_by_estimator": False,
        "accuracy_claim": False,
    }
    _json(output / "smoke_report.json", report)
    _json(output / "association_trace.json", observations)
    _json(output / "stateful_route_trace.json", states)
    _json(output / "protocol.json", {
        "schema": "online_geometry_loop_same_range_pair_stream_smoke_protocol",
        "data_source": "final_v2 separated_benign same-range IQ generator, seed-specific",
        "same_range": True,
        "causal_window": "IQ[frame-19:frame+1]",
        "association_key": "(range_bin, angle_track)",
        "split_route": "two same-range angle tracks with per-track beta_t",
        "merge_route": "one selected angle track with one beta_t",
        "stateful_adapter": "raw/split and merge routes each consume beta_t with persistent state",
        "truth_or_q_proxy_used_by_estimator": False,
        "accuracy_claim": False,
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run causal same-range pair association smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    report = run_smoke(args.output, seed=args.seed)
    print(json.dumps({"status": report["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
