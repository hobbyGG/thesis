"""Causal prefix-routed scratch trial.

This diagnostic is intentionally separate from the retrospective route report.
It generates one rolling geometry row at a time, waits for the first twenty
current-phase rows (frames 200--219), then exposes one route from frame 220
onward.  Both route states are advanced causally in parallel during the prefix
so selecting the transport route does not require replaying or rewriting the
prefix.  The estimator copy contains no truth, q_proxy, or paper metadata;
truth is opened only after the trace is complete for post-run scoring.
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

from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402

from experiments.online_geometry_loop_scratch.accuracy_trial import (  # noqa: E402
    PHASE_RAMP_DELTA_SIN,
    RADAR_RATE_HZ,
    TEST_START,
    TEST_STOP,
    _copy_estimator_only,
    _score,
    _slice_acceleration,
    _truth_reference,
    _stable_range_slots,
)
from experiments.online_geometry_loop_scratch.gauge_fix_diagnostic import (  # noqa: E402
    WINDOW_FRAMES,
    _apply_angle_migration,
    _apply_phase_ramp,
    _stable_angles,
)
from experiments.online_geometry_loop_scratch.gauge_mode_classifier_analysis import (  # noqa: E402
    BOOTSTRAP_FRAMES,
    _decision,
    _slot_feature_table,
)
from experiments.online_geometry_loop_scratch.online_geometry_loop import _run_loop  # noqa: E402
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)


SEED = 20261001
CONDITIONS = ("baseline_no_drift", "post_200_phase_ramp", "angle_migration")


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _stream_rows(capture):
    """Generate exactly one causal rolling row per current frame."""
    for frame in range(TEST_START, TEST_STOP):
        # The helper reads only [frame-19, frame].  Calling it one frame at a
        # time makes the prefix decision boundary explicit in this trial.
        yield _run_loop(
            capture,
            window_frames=WINDOW_FRAMES,
            output_frames=1,
            first_output_frame=frame,
        )[0]


def _row_slots(row: dict[str, object], slot_ranges: np.ndarray):
    """Map one current row to persistent range slots without future data."""
    n = int(slot_ranges.size)
    phase = np.full(n, np.nan, dtype=float)
    beta = np.full(n, np.nan, dtype=float)
    angle = np.full(n, np.nan, dtype=float)
    available = np.zeros(n, dtype=bool)
    for j, range_bin in enumerate(np.asarray(row["range_bins"], dtype=int)):
        slots = np.flatnonzero(slot_ranges == range_bin)
        if not slots.size:
            continue
        slot = int(slots[0])
        phase[slot] = float(row["current_phase_rad"][j])
        beta[slot] = float(row["beta"][j])
        angle[slot] = float(row["angle_deg"][j])
        available[slot] = bool(np.isfinite(phase[slot]))
    if not np.isfinite(beta).all() or not np.isfinite(angle).all():
        raise RuntimeError("streamed target slots changed; same-range association is not implemented")
    return phase, beta, angle, available


def _run_stream(generated: Path, estimator_input: Path, *, condition: str, seed: int) -> dict[str, object]:
    capture = load_capture_package(estimator_input)
    if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
        raise AssertionError("truth reached streamed estimator")
    row_stream = iter(_stream_rows(capture))
    # Consume no post-prefix geometry before making the mode decision.  This
    # keeps the temporal fence explicit even though the capture is in memory.
    first_rows = [next(row_stream) for _ in range(BOOTSTRAP_FRAMES)]
    _, _, _, association = _stable_range_slots(first_rows)
    slot_ranges = np.asarray(association["baseline_range_bins"], dtype=int)
    phase20, angles20 = _stable_range_slots(first_rows)[0], _stable_angles(first_rows, slot_ranges)
    positions = np.asarray(capture.frontend.virtual_array_positions_wavelengths, dtype=float)
    if positions.size == 0:
        positions = np.arange(capture.frontend.num_virtual_rx, dtype=float) * capture.frontend.antenna_spacing_wavelengths
    _, features = _slot_feature_table(phase20, angles20, centroid=float(np.mean(positions)))
    route_decision = _decision(features)
    selected_route = "rolling_bias_transport" if route_decision == "gauge_boundary_candidate" else "rolling_raw"

    config = AlgorithmConfig(sample_rate_hz=RADAR_RATE_HZ)
    radar_time_ns = np.asarray(capture.radar_time_ns[TEST_START:TEST_STOP], dtype=np.int64)
    reference_dt = float(np.median(np.diff(radar_time_ns)) * 1.0e-9)
    acceleration = _slice_acceleration(capture, radar_time_ns)
    first_phase, first_beta, first_angle, first_available = _row_slots(first_rows[0], slot_ranges)
    selected_indices = np.arange(slot_ranges.size, dtype=int)
    raw_adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=first_phase,
        available_t=first_available,
        selected_indices=selected_indices,
        reference_dt_s=reference_dt,
    )
    transport_adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=first_phase,
        available_t=first_available,
        selected_indices=selected_indices,
        reference_dt_s=reference_dt,
    )
    bootstrap_bias = transport_adapter.state.biases.copy()
    u0 = np.sin(np.deg2rad(first_angle))
    centroid = float(np.mean(positions))
    rows = list(first_rows)
    q_raw_values: list[float] = []
    q_transport_values: list[float] = []
    gauge_values: list[np.ndarray] = []

    def process_row(k: int, row: dict[str, object]) -> None:
        phase, beta, angle, available = _row_slots(row, slot_ranges)
        uk = np.sin(np.deg2rad(angle))
        gauge = -2.0 * np.pi * centroid * (uk - u0)
        if k == 0:
            duration = reference_dt
            delta_q = delta_v = 0.0
        else:
            duration = float(acceleration.preintegration.duration_s[k - 1])
            delta_q = float(acceleration.preintegration.delta_q_m[k - 1])
            delta_v = float(acceleration.preintegration.delta_v_mps[k - 1])
        raw_step = raw_adapter.step(
            phase, beta, available,
            duration_s=duration, delta_q_m=delta_q, delta_v_mps=delta_v,
        )
        q_raw_values.append(float(raw_step["q_hat_m"]))
        transport_adapter.state.biases = bootstrap_bias + gauge
        transport_step = transport_adapter.step(
            phase, beta, available,
            duration_s=duration, delta_q_m=delta_q, delta_v_mps=delta_v,
        )
        q_transport_values.append(float(transport_step["q_hat_m"]))
        gauge_values.append(gauge)

    # Both candidate states consume the observed prefix, but no selected
    # route is exposed until the decision has been made.
    for k, row in enumerate(first_rows):
        process_row(k, row)
    # Only now read each subsequent rolling window and emit its selected state.
    for k, row in enumerate(row_stream, start=BOOTSTRAP_FRAMES):
        rows.append(row)
        process_row(k, row)

    q_raw = np.asarray(q_raw_values, dtype=float)
    q_transport = np.asarray(q_transport_values, dtype=float)
    gauge_trace = np.asarray(gauge_values, dtype=float)

    # No selected-route output is claimed until the 20 current-phase rows have
    # arrived.  Prefix output is an explicitly labeled raw fallback; thereafter
    # only the route selected by the prefix classifier is exposed.
    q_streamed = q_raw.copy()
    if selected_route == "rolling_bias_transport":
        q_streamed[BOOTSTRAP_FRAMES:] = q_transport[BOOTSTRAP_FRAMES:]

    # Truth is intentionally opened only after estimator processing is complete.
    centered_truth, reference_m = _truth_reference(generated, radar_time_ns)
    prefix_score = _score(q_raw[:BOOTSTRAP_FRAMES], centered_truth[:BOOTSTRAP_FRAMES])
    post_score = _score(q_streamed[BOOTSTRAP_FRAMES:], centered_truth[BOOTSTRAP_FRAMES:])
    stream_score = _score(q_streamed, centered_truth)
    return {
        "schema": "online_geometry_loop_gauge_mode_routed_stream_trial",
        "status": "completed",
        "condition": condition,
        "seed": seed,
        "radar_test_frames": [TEST_START, TEST_STOP - 1],
        "causal_protocol": {
            "window_frames": WINDOW_FRAMES,
            "prefix_current_phase_frames": [TEST_START, TEST_START + BOOTSTRAP_FRAMES - 1],
            "prefix_window_ranges": [[TEST_START - WINDOW_FRAMES + 1, TEST_START], [TEST_START, TEST_START + BOOTSTRAP_FRAMES - 1]],
            "decision_available_after_frame": TEST_START + BOOTSTRAP_FRAMES - 1,
            "selected_route_first_frame": TEST_START + BOOTSTRAP_FRAMES,
            "latency_frames": BOOTSTRAP_FRAMES,
            "latency_seconds": BOOTSTRAP_FRAMES / RADAR_RATE_HZ,
            "future_frame_count_seen_by_prefix": 0,
            "prefix_output_route": "rolling_raw_fallback",
        },
        "estimator_input": {
            "truth_present": (estimator_input / "truth").exists(),
            "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
            "capture_truth_loaded": False,
            "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            "truth_or_q_proxy_used_by_estimator": False,
        },
        "mode_features": features,
        "route_decision": route_decision,
        "selected_route": selected_route,
        "scores_post_run_truth": {
            "reference_m": reference_m,
            "prefix_raw_fallback": prefix_score,
            "selected_route_after_decision": post_score,
            "stitched_stream": stream_score,
        },
        "trace": {
            "frame_index": [int(row["frame_index"]) for row in rows],
            "q_raw_m": q_raw.tolist(),
            "q_transport_m": q_transport.tolist(),
            "q_streamed_m": q_streamed.tolist(),
            "route_per_frame": ["rolling_raw_fallback"] * BOOTSTRAP_FRAMES + [selected_route] * (len(rows) - BOOTSTRAP_FRAMES),
            "gauge_delta_rad": gauge_trace.tolist(),
        },
        "same_range_multi_target": {
            "status": "blocked_interface",
            "reason": "stream slot association currently keys on unique range_bin; same-range angular pair requires a causal (range_bin, angle-track) association before evaluation",
        },
        "accuracy_claim": False,
    }


def run_trial(output: Path, *, seed: int = SEED, conditions: tuple[str, ...] = CONDITIONS) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for condition in conditions:
        with tempfile.TemporaryDirectory(prefix=f"gauge-stream-{seed}-{condition}-") as temporary:
            root = Path(temporary)
            generated = root / "generated_with_evaluation_artifacts"
            estimator_input = root / "estimator_input_truth_free"
            _write_scratch_package(generated, stratum_name="stationary", requested_rms_mm=0.0, seed=seed)
            _copy_estimator_only(generated, estimator_input)
            perturbation = {"enabled": False}
            if condition == "post_200_phase_ramp":
                perturbation = _apply_phase_ramp(estimator_input, PHASE_RAMP_DELTA_SIN)
            elif condition == "angle_migration":
                perturbation = _apply_angle_migration(
                    estimator_input, start_frame=TEST_START, ramp_frames=40, delta_sin=PHASE_RAMP_DELTA_SIN
                )
            record = _run_stream(generated, estimator_input, condition=condition, seed=seed)
            record["condition_input"] = perturbation
            records.append(record)
            _json(output / f"{condition}.json", record)
    summary = {
        "schema": "online_geometry_loop_gauge_mode_routed_stream_trial_summary",
        "status": "completed",
        "seed": seed,
        "conditions": list(conditions),
        "records": records,
        "truth_free_estimator_routes": True,
        "post_run_truth_scoring": True,
        "accuracy_claim": False,
    }
    _json(output / "summary.json", summary)
    _json(output / "protocol.json", {
        "schema": "online_geometry_loop_gauge_mode_routed_stream_trial_protocol",
        "prefix_frames": [TEST_START, TEST_START + BOOTSTRAP_FRAMES - 1],
        "selected_route_first_frame": TEST_START + BOOTSTRAP_FRAMES,
        "route_rule": "prefix truth-free classifier: gauge_boundary_candidate -> rolling_bias_transport; otherwise rolling_raw",
        "prefix_fallback": "rolling_raw; never retroactively replaced",
        "route_states": "raw and transport states advanced causally in parallel; selected trace is emitted only after prefix decision",
        "same_range_multi_target": "not evaluated; current association requires unique range bins",
        "truth_or_q_proxy_used_by_estimator": False,
        "accuracy_claim": False,
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run causal prefix-routed gauge scratch trial")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--condition", choices=("all",) + CONDITIONS, default="all")
    args = parser.parse_args()
    conditions = CONDITIONS if args.condition == "all" else (args.condition,)
    summary = run_trial(args.output, seed=args.seed, conditions=conditions)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
