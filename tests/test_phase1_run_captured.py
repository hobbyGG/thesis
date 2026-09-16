import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from simulation.phase1.run_captured import _phase1_config, run_captured_algorithm


def test_beta_scale_mode_is_selected_from_capture_calibration_provenance():
    radar_manifest = {
        "radar": {
            "start_frequency_hz": 77.0e9,
            "adc_sample_rate_hz": 5.0e6,
            "ramp_end_time_s": 60.0e-6,
            "physical_chirps_per_frame": 2,
            "adc_samples_per_chirp": 4,
            "tx_indices": [0, 1],
            "rx_indices": [0],
        }
    }
    base = dict(
        radar_time_ns=np.array([0, 10_000_000], dtype=np.int64),
        is_simulation=False,
        fusion_capture=SimpleNamespace(
            radar=SimpleNamespace(manifest=radar_manifest)
        ),
        frontend_config=SimpleNamespace(num_virtual_rx=2, num_angle_bins=8),
    )
    algorithm_input = SimpleNamespace(
        effective_radar_rate_hz=100.0,
        radar=SimpleNamespace(wrapped_phase_rad=np.zeros((3, 2))),
    )

    validated = _phase1_config(
        SimpleNamespace(**base, calibration_mode="validated"),
        algorithm_input,
    )
    unvalidated = _phase1_config(
        SimpleNamespace(
            **base,
            calibration_mode="nominal_unvalidated_adxl_x",
        ),
        algorithm_input,
    )
    missing_provenance = _phase1_config(
        SimpleNamespace(**base),
        algorithm_input,
    )

    assert validated.beta_calibration_scale_mode == "adxl_absolute"
    assert unvalidated.beta_calibration_scale_mode == "aoa_anchored_relative"
    assert (
        missing_provenance.beta_calibration_scale_mode
        == "aoa_anchored_relative"
    )


def test_run_captured_algorithm_publishes_portable_result(tmp_path):
    capture_root = tmp_path / "capture_00001"
    captured = SimpleNamespace(
        source_directory=capture_root,
        radar_time_ns=np.array(
            [1_000_000_000, 1_100_000_000, 1_200_000_000],
            dtype=np.int64,
        ),
        frontend_config=SimpleNamespace(
            num_virtual_rx=2,
            num_angle_bins=8,
        ),
        timing_mode="hardware_trigger_reference",
        calibration_mode="nominal_unvalidated_adxl_x",
        warnings=("nominal calibration",),
        max_adxl_gap_ns=2_500_000,
        fusion_capture=SimpleNamespace(
            algorithm_ready=True,
            fusion_ready=False,
            provenance=SimpleNamespace(
                radar_timestamp_quality="userspace_set_completed"
            ),
            radar_reference_monotonic_ns=np.array(
                [1_000_000_000, 1_100_000_000, 1_200_000_000],
                dtype=np.int64,
            ),
            radar_adc_sample_monotonic_ns=None,
            adxl_drdy_monotonic_ns=np.array(
                [990, 1_000, 1_010], dtype=np.uint64
            ),
            radar=SimpleNamespace(
                manifest={
                    "radar": {
                        "start_frequency_hz": 77.0e9,
                        "adc_sample_rate_hz": 5.0e6,
                        "ramp_end_time_s": 60.0e-6,
                        "physical_chirps_per_frame": 2,
                        "adc_samples_per_chirp": 4,
                        "tx_indices": [0, 1],
                        "rx_indices": [0],
                    }
                }
            ),
        ),
    )
    preintegration = SimpleNamespace(
        delta_v_mps=np.array([0.1, 0.2]),
        delta_q_m=np.array([0.01, 0.02]),
        duration_s=np.array([0.1, 0.1]),
    )
    algorithm_input = SimpleNamespace(
        effective_radar_rate_hz=10.0,
        radar=SimpleNamespace(
            wrapped_phase_rad=np.zeros((1, 3)),
            available_mask=np.ones((1, 3), dtype=bool),
            measured_beta=np.array([1.1]),
            selected_indices=np.array([0], dtype=np.int64),
            calibration_indices=np.array([0], dtype=np.int64),
            initial_r=np.array([0.5]),
            selection_scores=np.array([0.9]),
        ),
        acceleration=SimpleNamespace(
            native_time_ns=np.array([990, 1_000, 1_010], dtype=np.int64),
            native_mps2=np.array([1.0, 2.0, 3.0]),
            preintegration=preintegration,
        ),
        frontend_targets=SimpleNamespace(
            range_bins=np.array([4]),
            angle_bins=np.array([3]),
            range_m=np.array([0.4]),
            angle_deg=np.array([10.0]),
            slow_time=np.ones((1, 3), dtype=np.complex128),
        ),
    )
    result = SimpleNamespace(
        method_name="fixture_method",
        q_hat_m=np.array([0.0, 0.1, 0.2]),
        theta_hat_rad=np.array([0.0, 1.0, 2.0]),
        theta_dot_hat_radps=np.array([0.0, 0.5, 0.5]),
        beta_hat=np.array([1.1]),
        los_corrected_phase_rad=np.array([[0.0, 1.0, 2.0]]),
        r_theta_history=np.array([[0.5, 0.4, 0.3]]),
        innovation_rad=np.array([[0.0, 0.1, 0.2]]),
        extra={"beta_history": np.array([[1.0, 1.05, 1.1]])},
    )
    output = tmp_path / "result.npz"

    with patch(
        "simulation.phase1.run_captured.load_captured_fusion_input",
        return_value=captured,
    ):
        with patch(
            "simulation.phase1.run_captured.build_captured_algorithm_input",
            return_value=algorithm_input,
        ):
            with patch.dict(
                "simulation.phase1.run_captured.METHODS",
                {"fixed_beta": lambda _radar, _accel, _config: result},
                clear=True,
            ):
                result_path, summary_path = run_captured_algorithm(
                    Path("/input/capture"),
                    output_path=output,
                )

    assert result_path == output
    assert summary_path == output.with_suffix(".json")
    with np.load(output, allow_pickle=False) as arrays:
        np.testing.assert_allclose(arrays["q_hat_m"], [0.0, 0.1, 0.2])
        np.testing.assert_array_equal(
            arrays["radar_time_ns"],
            captured.radar_time_ns,
        )
        np.testing.assert_allclose(
            arrays["diagnostic_beta_history"],
            [[1.0, 1.05, 1.1]],
        )
        np.testing.assert_allclose(
            arrays["radar_target_slow_time_iq"],
            np.ones((1, 3)),
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["algorithm_ready"] is True
    assert summary["calibrated_fusion_ready"] is False
    assert summary["timing_mode"] == "hardware_trigger_reference"
    assert summary["warnings"] == ["nominal calibration"]
    assert summary["nominal_adxl_sign"] == 1
    assert summary["result_samples"] == 3
    assert "radar_wrapped_phase_rad" in summary["result_arrays"]


def test_run_captured_algorithm_executes_real_adaptive_estimator(tmp_path):
    frame_count = 24
    interval_s = 0.1
    frame_index = np.arange(frame_count)
    radar_time_ns = (
        2_000_000_000 + frame_index * int(interval_s * 1_000_000_000)
    ).astype(np.int64)
    phase = 0.4 * np.sin(2.0 * np.pi * frame_index / 10.0)
    acceleration = 0.2 * np.sin(2.0 * np.pi * frame_index / 10.0)
    interval_acceleration = acceleration[:-1]
    preintegration = SimpleNamespace(
        delta_v_mps=interval_acceleration * interval_s,
        delta_q_m=0.5 * interval_acceleration * interval_s**2,
        duration_s=np.full(frame_count - 1, interval_s),
        interval_valid=np.ones(frame_count - 1, dtype=bool),
        radar_start_time_ns=radar_time_ns[:-1],
        radar_end_time_ns=radar_time_ns[1:],
    )
    capture_root = tmp_path / "capture_00002" / "synchronized"
    captured = SimpleNamespace(
        source_directory=capture_root,
        radar_time_ns=radar_time_ns,
        frontend_config=SimpleNamespace(num_virtual_rx=2, num_angle_bins=8),
        timing_mode="hardware_trigger_reference",
        calibration_mode="nominal_unvalidated_adxl_x",
        warnings=("nominal calibration",),
        max_adxl_gap_ns=2_500_000,
        fusion_capture=SimpleNamespace(
            algorithm_ready=True,
            fusion_ready=False,
            provenance=SimpleNamespace(
                radar_timestamp_quality="userspace_set_completed"
            ),
            radar_reference_monotonic_ns=radar_time_ns,
            radar_adc_sample_monotonic_ns=None,
            adxl_drdy_monotonic_ns=radar_time_ns.astype(np.uint64),
            radar=SimpleNamespace(
                manifest={
                    "radar": {
                        "start_frequency_hz": 77.0e9,
                        "adc_sample_rate_hz": 5.0e6,
                        "ramp_end_time_s": 60.0e-6,
                        "physical_chirps_per_frame": 2,
                        "adc_samples_per_chirp": 4,
                        "tx_indices": [0, 1],
                        "rx_indices": [0],
                    }
                }
            ),
        ),
    )
    radar = SimpleNamespace(
        wrapped_phase_rad=phase[None, :],
        available_mask=np.ones((1, frame_count), dtype=bool),
        measured_beta=np.array([1.1]),
        selected_indices=np.array([0], dtype=np.int64),
        calibration_indices=np.array([0], dtype=np.int64),
        initial_r=np.array([0.5]),
        selection_scores=np.array([0.9]),
        extra={
            "radar_time_ns": radar_time_ns,
            "angle_deg": np.array([10.0]),
        },
    )
    algorithm_input = SimpleNamespace(
        effective_radar_rate_hz=1.0 / interval_s,
        radar=radar,
        acceleration=SimpleNamespace(
            measured_mps2=acceleration,
            native_time_ns=radar_time_ns,
            native_mps2=acceleration,
            preintegration=preintegration,
        ),
        frontend_targets=SimpleNamespace(
            range_bins=np.array([4]),
            angle_bins=np.array([3]),
            range_m=np.array([0.4]),
            angle_deg=np.array([10.0]),
            slow_time=np.exp(1j * phase)[None, :],
        ),
    )

    with patch(
        "simulation.phase1.run_captured.load_captured_fusion_input",
        return_value=captured,
    ):
        with patch(
            "simulation.phase1.run_captured.build_captured_algorithm_input",
            return_value=algorithm_input,
        ):
            result_path, summary_path = run_captured_algorithm(
                Path("/input/capture"),
                method="adaptive_beta",
            )

    assert result_path == capture_root / "algorithm" / "phase1_result.npz"
    with np.load(result_path, allow_pickle=False) as arrays:
        assert arrays["q_hat_m"].shape == (frame_count,)
        assert np.all(np.isfinite(arrays["q_hat_m"]))
        assert arrays["diagnostic_beta_history"].shape == (1, frame_count)
        np.testing.assert_allclose(arrays["diagnostic_beta_initial"], [1.1])
        np.testing.assert_allclose(
            arrays["diagnostic_beta_calibration_beta_frozen"], [1.1]
        )
        assert not bool(arrays["diagnostic_beta_calibration_accepted"])
        np.testing.assert_array_equal(
            arrays["diagnostic_beta_calibration_accepted_mask"],
            [False],
        )
        assert arrays["interval_delta_v_mps"].shape == (frame_count - 1,)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["method"] == "proposed_full_pipeline_beta_confidence"
    assert summary["result_samples"] == frame_count
    assert summary["beta_calibration_strategy"] == "independent_prepass_frozen"
    assert summary["beta_calibration_used_stage"] == "aoa_initial_fallback"
    assert summary["beta_calibration_accepted"] is False
    assert summary["beta_calibration_any_accepted"] is False
    assert summary["beta_calibration_accepted_count"] == 0
    assert summary["beta_calibration_all_selected_accepted"] is False
    assert summary["beta_calibration_accepted_mask"] == [False]
    assert summary["beta_calibration_reason"]
    assert (
        summary["beta_calibration_adxl_reason"]
        == "insufficient_disjoint_window_samples"
    )
    assert summary["beta_calibration_adxl_reason_by_target"] == [
        "insufficient_disjoint_window_samples"
    ]
    assert (
        summary["beta_calibration_adxl_scale_mode_requested"]
        == "aoa_anchored_relative"
    )
    assert summary["beta_calibration_adxl_scale_mode"] == "none"
