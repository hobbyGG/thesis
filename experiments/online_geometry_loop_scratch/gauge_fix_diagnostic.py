"""Scratch-only gauge diagnostic for the causal geometry loop.

This file deliberately does not modify ``algorithm/``.  It compares two
truth-free estimator paths on one stationary package per condition:

* ``fixed_reference`` reuses the calibration-only steering and beta reference
  for every test frame (the P1 control);
* ``rolling_bias_transport`` uses the rolling angle/beta rows, but transports
  each slot's phase bias by the known array-centroid steering phase relative
  to the bootstrap sample.

The transport is a diagnostic assumption, not a claimed physical correction:
for positions p (in wavelengths), the frontend coefficient gauge is observed
to follow -gamma(u), where gamma(u) = 2*pi*mean(p)*u and u = sin(angle).
Thus b_t = b_0 - gamma(u_t) + gamma(u_0). Truth is loaded only after both
routes finish.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.acceleration import preintegrate_acceleration_to_radar  # noqa: E402
from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from algorithm.types import AccelerationInput  # noqa: E402
from spatial_recovery_rebuilt.calibration_only.calibration_only_route import (  # noqa: E402
    run_calibration_only,
)
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402

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
from experiments.online_geometry_loop_scratch.online_geometry_loop import _run_loop  # noqa: E402
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)


SEED = 20261001
WINDOW_FRAMES = 20


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


def _apply_phase_ramp_from_frame(estimator_input: Path, *, start_frame: int, delta_sin: float) -> dict[str, object]:
    """Apply the same diagnostic ramp from an explicitly chosen frame."""
    manifest_path = estimator_input / "radar" / "algorithm_input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adc_path = manifest_path.parent / manifest["arrays"]["adc_cube"]["file"]
    adc = np.asarray(np.load(adc_path, allow_pickle=False), dtype=np.complex128)
    if start_frame < 0 or start_frame >= adc.shape[0]:
        raise ValueError("phase-ramp start frame outside ADC array")
    positions = np.asarray(manifest["radar"].get("virtual_array_positions_wavelengths", ()), dtype=float)
    if positions.size != adc.shape[1]:
        positions = np.arange(adc.shape[1], dtype=float) * 0.5
    steering_shift = np.exp(2j * np.pi * positions * float(delta_sin))
    adc[start_frame:] *= steering_shift[None, :, None]
    np.save(adc_path, adc, allow_pickle=False)
    return {
        "enabled": True,
        "frame_range": [int(start_frame), int(adc.shape[0] - 1)],
        "delta_sin": float(delta_sin),
        "operation": "adc_virtual_rx *= exp(+2 pi j * position_wavelength * delta_sin)",
        "truth_q_proxy_or_paper_metadata_modified": False,
    }


def _apply_angle_migration(
    estimator_input: Path, *, start_frame: int, ramp_frames: int, delta_sin: float
) -> dict[str, object]:
    """Apply a smooth common target steering migration without changing range."""
    manifest_path = estimator_input / "radar" / "algorithm_input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adc_path = manifest_path.parent / manifest["arrays"]["adc_cube"]["file"]
    adc = np.asarray(np.load(adc_path, allow_pickle=False), dtype=np.complex128)
    if start_frame < 0 or start_frame >= adc.shape[0] or ramp_frames <= 0:
        raise ValueError("invalid angle-migration interval")
    positions = np.asarray(manifest["radar"].get("virtual_array_positions_wavelengths", ()), dtype=float)
    if positions.size != adc.shape[1]:
        positions = np.arange(adc.shape[1], dtype=float) * 0.5
    frame_delta = np.clip(
        (np.arange(adc.shape[0], dtype=float) - float(start_frame)) / float(ramp_frames),
        0.0,
        1.0,
    ) * float(delta_sin)
    steering = np.exp(2j * np.pi * frame_delta[:, None] * positions[None, :])
    adc[start_frame:] *= steering[start_frame:, :, None]
    np.save(adc_path, adc, allow_pickle=False)
    return {
        "enabled": True,
        "frame_range": [int(start_frame), int(adc.shape[0] - 1)],
        "ramp_frames": int(ramp_frames),
        "delta_sin_final": float(delta_sin),
        "operation": "per-frame adc_virtual_rx *= exp(+2 pi j * position_wavelength * delta_sin(frame))",
        "range_bins_modified": False,
        "truth_q_proxy_or_paper_metadata_modified": False,
    }


def _slice_acceleration(capture, radar_time_ns: np.ndarray) -> AccelerationInput:
    structural = np.asarray(capture.adxl_acceleration_mps2[:, 0], dtype=float)
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns, capture.adxl_time_ns, structural
    )
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    return AccelerationInput(
        np.asarray(capture.adxl_time_ns, dtype=np.int64),
        structural,
        np.r_[interval_average[0], interval_average],
        preintegration,
    )


def _phase_bias_summary(phase: np.ndarray, available: np.ndarray) -> dict[str, object]:
    """Summarize phase drift relative to the bootstrap sample, per slot."""
    phase = np.asarray(phase, dtype=float)
    available = np.asarray(available, dtype=bool)
    if phase.ndim != 2 or available.shape != phase.shape:
        raise ValueError("phase and available must have shape (targets, samples)")
    if phase.shape[1] < 2:
        return {"finite_fraction": 0.0, "mean_rad": None, "rms_rad": None}
    deltas: list[float] = []
    for i in range(phase.shape[0]):
        if not (available[i, 0] and np.isfinite(phase[i, 0])):
            continue
        valid = available[i, 1:] & np.isfinite(phase[i, 1:])
        if np.any(valid):
            # Circular difference avoids arbitrary +/-2*pi wrapping.
            d = np.angle(np.exp(1j * (phase[i, 1:][valid] - phase[i, 0])))
            deltas.extend(np.asarray(d, dtype=float).tolist())
    values = np.asarray(deltas, dtype=float)
    return {
        "finite_fraction": float(values.size / max(phase.shape[0] * (phase.shape[1] - 1), 1)),
        "mean_rad": float(np.mean(values)) if values.size else None,
        "rms_rad": float(np.sqrt(np.mean(values * values))) if values.size else None,
        "sample_count": int(values.size),
    }


def _stable_angles(rows: list[dict[str, object]], slot_ranges: np.ndarray) -> np.ndarray:
    """Reindex rolling AoA values by the same stable range slots as phase."""
    angles = np.full((slot_ranges.size, len(rows)), np.nan, dtype=float)
    for k, row in enumerate(rows):
        for range_bin, angle in zip(row["range_bins"], row["angle_deg"]):
            slot = np.flatnonzero(slot_ranges == int(range_bin))
            if slot.size:
                angles[int(slot[0]), k] = float(angle)
    return angles


def _run_transport(
    capture,
    rows: list[dict[str, object]],
    radar_time_ns: np.ndarray,
    config: AlgorithmConfig,
) -> tuple[np.ndarray, np.ndarray, dict[str, object], dict[str, object]]:
    phase, beta, available, association = _stable_range_slots(rows)
    angles = _stable_angles(rows, np.asarray(association["baseline_range_bins"], dtype=int))
    if not np.isfinite(angles[:, 0]).all():
        raise AssertionError("rolling bootstrap angle is non-finite")
    positions = np.asarray(capture.frontend.virtual_array_positions_wavelengths, dtype=float)
    if positions.size != phase.shape[0] and positions.size == 0:
        positions = np.arange(capture.frontend.num_virtual_rx, dtype=float) * capture.frontend.antenna_spacing_wavelengths
    centroid = float(np.mean(positions))
    reference_dt = float(np.median(np.diff(radar_time_ns)) * 1.0e-9)
    selected = np.arange(phase.shape[0], dtype=int)
    adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=phase[:, 0],
        available_t=available[:, 0],
        selected_indices=selected,
        reference_dt_s=reference_dt,
    )
    raw_adapter = StatefulKalmanAdapter.from_initial_sample(
        config,
        wrapped_phase_t=phase[:, 0],
        available_t=available[:, 0],
        selected_indices=selected,
        reference_dt_s=reference_dt,
    )
    bootstrap_bias = adapter.state.biases.copy()
    u0 = np.sin(np.deg2rad(angles[:, 0]))
    acceleration = _slice_acceleration(capture, radar_time_ns)
    q = np.full(phase.shape[1], np.nan, dtype=float)
    q_raw = np.full(phase.shape[1], np.nan, dtype=float)
    gauge = np.zeros_like(phase, dtype=float)
    for k in range(phase.shape[1]):
        # The gauge is computed from current rolling geometry only.  No future
        # sample is used; k=0 is the bootstrap reference by construction.
        uk = np.sin(np.deg2rad(angles[:, k]))
        # The least-squares source coefficient uses the opposite phase
        # convention to the channel ramp in this frontend, so the raw phase
        # drift is -gamma(delta-u).  Transport the raw bias with that sign.
        gauge[:, k] = -2.0 * np.pi * centroid * (uk - u0)
        adapter.state.biases = bootstrap_bias + gauge[:, k]
        if k == 0:
            duration = reference_dt
            delta_q = delta_v = 0.0
        else:
            duration = float(acceleration.preintegration.duration_s[k - 1])
            delta_q = float(acceleration.preintegration.delta_q_m[k - 1])
            delta_v = float(acceleration.preintegration.delta_v_mps[k - 1])
        step = adapter.step(
            phase[:, k], beta[:, k], available[:, k],
            duration_s=duration, delta_q_m=delta_q, delta_v_mps=delta_v,
        )
        q[k] = float(step["q_hat_m"])
        raw_step = raw_adapter.step(
            phase[:, k], beta[:, k], available[:, k],
            duration_s=duration, delta_q_m=delta_q, delta_v_mps=delta_v,
        )
        q_raw[k] = float(raw_step["q_hat_m"])
    diag = {
        "target_slots": association,
        "array_positions_wavelengths": positions.tolist(),
        "array_centroid_wavelengths": centroid,
        "bootstrap_u": u0.tolist(),
        "gauge_delta_first_to_last_rad": gauge[:, -1].tolist(),
        "phase_bias_raw": _phase_bias_summary(phase, available),
        "phase_bias_after_transport": _phase_bias_summary(phase - gauge, available),
        "transport_assumption": "frontend coefficient gauge is -gamma(u), gamma(u)=2*pi*mean(position_wavelengths)*u; b_t=b_0-gamma(u_t)+gamma(u_0)",
    }
    return q, q_raw, diag, {"phase": phase, "available": available, "beta": beta, "angles": angles}


def _run_condition(generated: Path, estimator_input: Path, *, condition: str, seed: int) -> dict[str, object]:
    capture = load_capture_package(estimator_input)
    if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
        raise AssertionError("truth reached gauge diagnostic estimator")
    config = AlgorithmConfig(sample_rate_hz=RADAR_RATE_HZ)
    radar_time_ns = np.asarray(capture.radar_time_ns[TEST_START:TEST_STOP], dtype=np.int64)

    # A: fixed calibration steering/phase reference (the P1 control).
    p1_result, p1_radar, _ = run_calibration_only(capture, config)
    p1_q = np.asarray(p1_result.q_hat_m, dtype=float)
    p1_phase = np.asarray(p1_radar.wrapped_phase_rad, dtype=float)
    p1_available = np.asarray(p1_radar.available_mask, dtype=bool)

    # B: causal rolling geometry with explicit centroid-gauge bias transport.
    rows = _run_loop(
        capture, window_frames=WINDOW_FRAMES,
        output_frames=TEST_STOP - TEST_START,
        first_output_frame=TEST_START,
    )
    rolling_q, raw_q, transport_diag, raw_diag = _run_transport(capture, rows, radar_time_ns, config)

    # Truth is opened only after both estimator routes have completed.
    centered_truth, reference_m = _truth_reference(generated, radar_time_ns)
    return {
        "schema": "online_geometry_loop_gauge_fix_diagnostic",
        "status": "completed",
        "condition": condition,
        "seed": seed,
        "radar_test_frames": [TEST_START, TEST_STOP - 1],
        "estimator_input": {
            "truth_present": (estimator_input / "truth").exists(),
            "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
            "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
            "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            "truth_or_q_proxy_used_by_estimator": False,
        },
        "protocol": {
            "fixed_reference": "calibration frames 0:199 determine range/angle/phase reference; test frames use fixed steering and beta",
            "rolling_transport": "20-frame causal rolling rows; current beta_t; bias transport from current angle only",
            "gauge_assumption": "source phase gauge follows array centroid gamma(u)=2*pi*mean(p)*sin(angle)",
            "truth_scoring": "post-run only after both routes complete",
            "accuracy_claim": False,
        },
        "truth_reference_post_run": {"reference_m": reference_m, "not_passed_to_estimator": True},
        "fixed_reference": {
            "score": _score(p1_q, centered_truth),
            "phase_bias": _phase_bias_summary(p1_phase, p1_available),
            "coverage": float(np.mean(np.isfinite(p1_q))),
            "target_count": int(p1_radar.selected_indices.size),
        },
        "rolling_bias_transport": {
            "score": _score(rolling_q, centered_truth),
            "coverage": float(np.mean(np.isfinite(rolling_q))),
            **transport_diag,
        },
        "rolling_raw": {
            "score": _score(raw_q, centered_truth),
            "coverage": float(np.mean(np.isfinite(raw_q))),
        },
        "accuracy_claim": False,
    }


def run_trial(output: Path, *, seed: int = SEED, condition: str = "both") -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    conditions = ["baseline_no_drift", "post_200_phase_ramp", "pre_window_phase_ramp"] if condition == "both" else [condition]
    records: list[dict[str, object]] = []
    for name in conditions:
        with tempfile.TemporaryDirectory(prefix=f"gauge-fix-{name}-") as temporary:
            root = Path(temporary)
            generated = root / "generated_with_evaluation_artifacts"
            estimator_input = root / "estimator_input_truth_free"
            _write_scratch_package(generated, stratum_name="stationary", requested_rms_mm=0.0, seed=seed)
            _copy_estimator_only(generated, estimator_input)
            perturbation = {"enabled": False}
            if name == "post_200_phase_ramp":
                perturbation = _apply_phase_ramp(estimator_input, PHASE_RAMP_DELTA_SIN)
            elif name == "pre_window_phase_ramp":
                perturbation = _apply_phase_ramp_from_frame(
                    estimator_input,
                    start_frame=TEST_START - (WINDOW_FRAMES - 1),
                    delta_sin=PHASE_RAMP_DELTA_SIN,
                )
            elif name == "angle_migration":
                perturbation = _apply_angle_migration(
                    estimator_input,
                    start_frame=TEST_START,
                    ramp_frames=40,
                    delta_sin=PHASE_RAMP_DELTA_SIN,
                )
            record = _run_condition(generated, estimator_input, condition=name, seed=seed)
            record["condition_input"] = perturbation
            records.append(record)
            _json(output / f"{name}.json", record)
    summary = {
        "schema": "online_geometry_loop_gauge_fix_diagnostic_summary",
        "status": "completed",
        "seed": seed,
        "conditions": [record["condition"] for record in records],
        "accuracy_claim": False,
        "routes": [
            {
                "condition": record["condition"],
                "fixed_reference": record["fixed_reference"]["score"],
                "rolling_raw": record["rolling_raw"]["score"],
                "rolling_bias_transport": record["rolling_bias_transport"]["score"],
                "fixed_reference_phase_bias": record["fixed_reference"]["phase_bias"],
                "rolling_raw_phase_bias": record["rolling_bias_transport"]["phase_bias_raw"],
                "rolling_transported_phase_bias": record["rolling_bias_transport"]["phase_bias_after_transport"],
            }
            for record in records
        ],
    }
    _json(output / "protocol.json", {
        "schema": "online_geometry_loop_gauge_fix_diagnostic_protocol",
        "truth_free_estimator_copy": True,
        "conditions": conditions,
        "routes": ["fixed_reference", "rolling_raw", "rolling_bias_transport"],
        "transport_assumption": "frontend coefficient gauge is -gamma(u), gamma(u)=2*pi*mean(array_positions_wavelengths)*u, u=sin(angle); b_t=b_0-gamma(u_t)+gamma(u_0)",
        "bootstrap_control": "pre_window_phase_ramp starts at frame 181 so the first 20-frame window is homogeneous",
        "angle_migration": "angle_migration applies a smooth common steering change over 40 frames from frame 200; range bins and truth remain unchanged",
        "no_future_data": True,
        "post_run_truth_scoring": True,
        "accuracy_claim": False,
    })
    _json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scratch-only phase-gauge diagnostic")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--condition",
        choices=("both", "baseline_no_drift", "post_200_phase_ramp", "pre_window_phase_ramp", "angle_migration"),
        default="both",
    )
    args = parser.parse_args()
    summary = run_trial(args.output, seed=args.seed, condition=args.condition)
    print(json.dumps({"status": summary["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
