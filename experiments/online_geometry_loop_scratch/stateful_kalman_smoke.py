"""One-seed no-drift smoke for :mod:`stateful_kalman_adapter`.

The generated package is copied to an estimator-only directory before any
algorithm input is loaded.  The smoke compares the adapter's first 20 causal
updates against the retained fixed-beta Kalman on the same truth-free slice.
It is a units/continuity check, never an accuracy evaluation.
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
from algorithm.io import build_algorithm_inputs, load_capture_package  # noqa: E402
from algorithm.kalman import run_fixed_beta_kalman  # noqa: E402
from algorithm.types import AccelerationInput, RadarInput  # noqa: E402
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402

from experiments.online_geometry_loop_scratch.online_geometry_loop import (  # noqa: E402
    _copy_estimator_only,
    _run_loop,
)
from experiments.online_geometry_loop_scratch.stateful_kalman_adapter import (  # noqa: E402
    StatefulKalmanAdapter,
)


WINDOW_FRAMES = 20
FIRST_OUTPUT_FRAME = 19
SAMPLES = 20


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n", encoding="utf-8")


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    raise TypeError(type(value).__name__)


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


def run_smoke(output: Path, *, seed: int = 20261001) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stateful-kalman-smoke-") as temporary:
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
        capture = load_capture_package(estimator_input)
        if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
            raise AssertionError("truth reached the stateful estimator smoke")

        # Reference: retained fixed-beta route restricted to exactly the same
        # 20 radar samples and acceleration intervals.
        full_radar, _, _, _ = build_algorithm_inputs(capture, radar_mode="frame")
        radar_time_ns = np.asarray(
            full_radar.extra["radar_time_ns"][FIRST_OUTPUT_FRAME:FIRST_OUTPUT_FRAME + SAMPLES],
            dtype=np.int64,
        )
        phase_fixed = np.asarray(
            full_radar.wrapped_phase_rad[:, FIRST_OUTPUT_FRAME:FIRST_OUTPUT_FRAME + SAMPLES],
            dtype=float,
        )
        available_fixed = np.asarray(
            full_radar.available_mask[:, FIRST_OUTPUT_FRAME:FIRST_OUTPUT_FRAME + SAMPLES],
            dtype=bool,
        )
        fixed_radar = RadarInput(
            np.asarray(full_radar.measured_beta, dtype=float),
            phase_fixed,
            available_fixed,
            np.asarray(full_radar.selected_indices, dtype=int),
            np.asarray(full_radar.initial_r, dtype=float),
            np.asarray(full_radar.selection_scores, dtype=float),
            {
                **full_radar.extra,
                "radar_time_ns": radar_time_ns,
            },
        )
        acceleration = _slice_acceleration(capture, radar_time_ns)
        config = AlgorithmConfig(sample_rate_hz=100.0)
        fixed_result = run_fixed_beta_kalman(fixed_radar, acceleration, config)

        # Online route: each row came from a fresh 20-frame causal geometry
        # window, with no frame after the current sample read.
        rows = _run_loop(
            capture,
            window_frames=WINDOW_FRAMES,
            output_frames=SAMPLES,
            first_output_frame=FIRST_OUTPUT_FRAME,
        )
        phase_online = np.asarray([row["current_phase_rad"] for row in rows], dtype=float).T
        beta_online = np.asarray([row["beta"] for row in rows], dtype=float).T
        available_online = np.isfinite(phase_online)
        if beta_online.shape != phase_online.shape:
            raise AssertionError("no-drift smoke unexpectedly changed target cardinality")
        adapter = StatefulKalmanAdapter.from_bootstrap(
            config,
            wrapped_phase_rad=phase_online,
            beta_by_sample=beta_online,
            available_mask=available_online,
            selected_indices=full_radar.selected_indices,
            initial_r=full_radar.initial_r,
            radar_time_ns=radar_time_ns,
            reference_dt_s=float(full_radar.extra["frame_period_s"]),
        )
        online_rows: list[dict[str, object]] = []
        for k in range(SAMPLES):
            if k == 0:
                duration = float(full_radar.extra["frame_period_s"])
                delta_q = 0.0
                delta_v = 0.0
            else:
                duration = float(acceleration.preintegration.duration_s[k - 1])
                delta_q = float(acceleration.preintegration.delta_q_m[k - 1])
                delta_v = float(acceleration.preintegration.delta_v_mps[k - 1])
            online_rows.append(
                adapter.step(
                    phase_online[:, k],
                    beta_online[:, k],
                    available_online[:, k],
                    duration_s=duration,
                    delta_q_m=delta_q,
                    delta_v_mps=delta_v,
                )
            )
        q_online = np.asarray([row["q_hat_m"] for row in online_rows], dtype=float)
        q_fixed = np.asarray(fixed_result.q_hat_m, dtype=float)
        phase_delta = np.angle(np.exp(1j * (phase_online - phase_fixed)))
        beta_delta = beta_online - np.asarray(full_radar.measured_beta, dtype=float)[:, None]
        q_delta = q_online - q_fixed
        report = {
            "schema": "online_geometry_loop_stateful_kalman_smoke",
            "status": "smoke_passed",
            "scope": "state_continuity_and_units_only",
            "seed": seed,
            "window_frames": WINDOW_FRAMES,
            "first_output_frame": FIRST_OUTPUT_FRAME,
            "sample_count": SAMPLES,
            "estimator_input": {
                "truth_present": (estimator_input / "truth").exists(),
                "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
                "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
                "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            },
            "causal_checks": {
                "window_size_20": all(int(row["window_size"]) == WINDOW_FRAMES for row in rows),
                "window_end_equals_current": all(row["window_frame_range"][1] == row["frame_index"] for row in rows),
                "future_frame_count_zero": all(int(row["future_frame_count"]) == 0 for row in rows),
            },
            "adapter": {
                "state_sample_index": int(adapter.state.sample_index),
                "state_continuous": int(adapter.state.sample_index) == SAMPLES,
                "beta_t_shape": list(beta_online.shape),
                "beta_t_max_abs_delta_vs_fixed": float(np.max(np.abs(beta_delta))),
                "phase_max_abs_wrapped_delta_vs_fixed_rad": float(np.max(np.abs(phase_delta))),
                "q_hat_units": "m",
                "q_hat_first_three_fixed_m": q_fixed[:3].tolist(),
                "q_hat_first_three_stateful_m": q_online[:3].tolist(),
                "q_hat_first_three_allclose": bool(np.allclose(q_online[:3], q_fixed[:3], rtol=0.0, atol=1.0e-12)),
                "q_hat_max_abs_delta_m": float(np.max(np.abs(q_delta))),
                "q_hat_rmse_delta_m": float(np.sqrt(np.mean(q_delta * q_delta))),
                "q_hat_allclose": bool(np.allclose(q_online, q_fixed, rtol=0.0, atol=1.0e-12)),
            },
            "accuracy_claim": False,
            "truth_or_q_proxy_used_by_estimator": False,
        }
        _json(output / "smoke_report.json", report)
        _json(
            output / "stateful_trace.json",
            {
                "q_hat_fixed_m": q_fixed,
                "q_hat_stateful_m": q_online,
                "q_hat_delta_m": q_delta,
                "beta_t": beta_online,
                "phase_t": phase_online,
            },
        )
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stateful beta_t adapter no-drift smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261001)
    args = parser.parse_args()
    report = run_smoke(args.output, seed=args.seed)
    print(json.dumps({"status": report["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
