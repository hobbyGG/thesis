import json
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from mmwavecapture.fusion_input import FusionInputError, load_fusion_input
from simulation.phase1.capture_reader import (
    detect_captured_target_bins,
    load_captured_fusion_input,
)
from simulation.phase1.maglev_capture_simulator import (
    COHERENT_APERTURE_CENTER_OFFSET_NS,
    SCENARIO_NAME,
    generate_maglev_capture_package,
)
from simulation.phase1.run_captured import run_captured_algorithm


def test_fixed_maglev_package_contract_and_determinism(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_maglev_capture_package(first, duration_s=0.1, seed=19)
    generate_maglev_capture_package(second, duration_s=0.1, seed=19)
    generate_maglev_capture_package(
        second, duration_s=0.1, seed=19, overwrite=True
    )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario"] == SCENARIO_NAME
    assert manifest["sync_mode"] == "simulation"
    assert manifest["timestamp_quality"] == (
        "synthetic_coherent_aperture_center"
    )
    assert manifest["simulation_ready"] is True
    assert manifest["algorithm_ready"] is False
    assert manifest["fusion_ready"] is False
    assert manifest["hardware_validated"] is False
    assert manifest["packet_integrity"] == "synthetic_payload_integrity"
    assert manifest["rates_hz"] == {"radar": 100, "adxl355": 1000}
    assert manifest["algorithm_contract"] == {
        "cold_start_duration_s": 0.2,
        "displacement_reference": "cold_start_mean",
        "truth_evaluation": "cold_start_relative_displacement",
    }
    provenance = manifest["source_provenance"]
    assert provenance["laser_displacement"]["classification"] == "measured"
    assert provenance["laser_displacement"]["channel"] == "卡3激光位移/3-4"
    assert provenance["laser_displacement"]["pre_downsample_filter_hz"] == [
        0.2,
        40.0,
    ]
    assert provenance["laser_displacement"]["scale_calibrated"] is False
    assert provenance["laser_displacement"]["measured_quantity"] == (
        "raw_voltage_waveform"
    )
    assert len(provenance["laser_displacement"]["sha256"]) == 64
    assert provenance["radar_configuration"]["classification"] == "configured"
    assert provenance["radar_configuration"]["file"].endswith(
        "iwr1843_hardware_trigger.cfg"
    )
    assert provenance["radar_adc_iq"]["classification"] == "synthetic"
    radar_error = provenance["radar_adc_iq"]["hardware_error_model"]
    assert provenance["radar_adc_iq"]["noise_injection_layers"] == 1
    assert radar_error["schema_version"] == 1
    assert radar_error["profile"] == "datasheet_typical_calibrated_25c"
    assert radar_error["datasheet_revision"] == "Rev. B (SWRS228B)"
    assert radar_error["receiver_noise"]["injection_layers"] == 1
    assert radar_error["receiver_noise"]["noise_figure_db_at_77_to_81_ghz"] == 15.0
    assert "not a manufacturer error specification" in radar_error[
        "receiver_noise"
    ]["target_snr_semantics"]
    assert radar_error["quantization"]["i_bits"] == 12
    assert radar_error["quantization"]["q_bits"] == 12
    assert radar_error["quantization"]["stored_values"] == (
        "signed_integer_codes_in_complex64"
    )
    assert "link-budget assumptions" in radar_error["receiver_noise"][
        "noise_power_semantics"
    ]
    assert "cannot determine ADC SNR" in radar_error["receiver_noise"][
        "noise_figure_limitation"
    ]
    assert radar_error["channel_mismatch"]["enabled"] is False
    assert radar_error["channel_mismatch"]["gain_bound_db"] == 0.5
    assert radar_error["channel_mismatch"]["phase_bound_deg"] == 3.0
    assert radar_error["dca1000"]["noise_injected"] is False
    assert provenance["adxl_structural_axis"]["classification"] == "derived"
    assert provenance["adxl_structural_axis"]["noise_classification"] == (
        "synthetic"
    )
    assert provenance["adxl_other_axes"]["classification"] == "synthetic"
    adxl_error = provenance["adxl_structural_axis"]["hardware_error_model"]
    assert adxl_error["schema_version"] == 1
    assert adxl_error["profile"] == "datasheet_typical_calibrated_25c"
    assert adxl_error["datasheet_revision"] == "Rev. D"
    assert adxl_error["range_g"] == 2
    assert adxl_error["adc_bits"] == 20
    assert adxl_error["sensitivity_lsb_per_g"] == 256_000.0
    assert adxl_error["noise"]["density_ug_per_sqrt_hz"] == 22.5
    assert adxl_error["noise"]["equivalent_bandwidth_hz"] == 250.0
    assert adxl_error["noise"]["target_rms_mps2"] == pytest.approx(
        22.5e-6 * 9.80665 * np.sqrt(250.0)
    )
    assert set(adxl_error["not_injected"]) == {
        "initial_zero_bias",
        "sensitivity_tolerance",
        "cross_axis_sensitivity",
        "nonlinearity",
        "temperature_drift",
        "digital_filter_group_delay",
    }
    assert "not injected" in adxl_error["not_injected"][
        "digital_filter_group_delay"
    ]
    assert "real hardware" in adxl_error["not_injected"][
        "digital_filter_group_delay"
    ]
    assert "not an exact ENBW" in adxl_error["noise"][
        "bandwidth_approximation"
    ]
    assert adxl_error["datasheet_specifications"] == {
        "zero_g_offset_mg": {
            "typical_absolute": 25.0,
            "minimum_maximum_absolute": 75.0,
        },
        "sensitivity_lsb_per_g_at_2g": {
            "minimum": 235_520.0,
            "typical": 256_000.0,
            "maximum": 276_480.0,
        },
        "nonlinearity_percent_full_scale": 0.1,
        "cross_axis_sensitivity_percent": 1.0,
        "sensitivity_temperature_percent_per_deg_c": 0.01,
        "offset_temperature_max_mg_per_deg_c": 0.15,
        "digital_filter_group_delay_ms_at_1khz_odr": 1.78,
    }
    assert provenance["adxl_structural_axis"][
        "physical_acceleration_noise_std_mps2"
    ] == 0.0
    assert "noise_std_mps2" not in provenance["adxl_structural_axis"]
    assert "0.02" not in json.dumps(manifest, sort_keys=True)
    assert provenance["radar_timestamps"]["measured_gpio"] is False
    assert provenance["adxl_drdy_timestamps"]["measured_drdy"] is False

    radar_manifest = json.loads(
        (first / "radar" / "algorithm_input" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    radar = radar_manifest["radar"]
    assert radar["frame_period_s"] == pytest.approx(9.0e-3)
    assert radar["frame_rate_hz"] == pytest.approx(1.0 / 9.0e-3)
    assert radar["chirp_loops_per_frame"] == 16
    assert radar["physical_chirps_per_frame"] == 32
    assert radar["tx_indices"] == [0, 2]
    assert radar["virtual_antennas"] == 8
    assert radar["adc_samples_per_chirp"] == 256
    assert radar["adc_sample_rate_hz"] == 5.209e6
    assert radar["ramp_end_time_s"] == 57.14e-6
    assert radar["idle_time_s"] == 70.0e-6
    assert radar["minimum_frame_period_s"] == pytest.approx(9.0e-3)
    assert radar["external_trigger_period_s"] == pytest.approx(10.0e-3)
    assert radar_manifest["processing"]["tdm_motion_compensation"] is False
    assert radar_manifest["processing"]["loop_start_interval_s"] == pytest.approx(
        254.28e-6
    )
    assert radar_manifest["processing"][
        "coherent_aperture_center_offset_s"
    ] == pytest.approx(1.9071e-3)

    adc = np.load(first / "radar" / "algorithm_input" / "adc_cube.npy")
    chirps = np.load(first / "radar" / "algorithm_input" / "chirp_cube.npy")
    nominal_frame_times = np.load(
        first / "radar" / "algorithm_input" / "frame_times_s.npy"
    )
    adxl = np.load(
        first / "adxl355" / "algorithm_input" / "acceleration_mps2.npy"
    )
    truth_acceleration = np.load(first / "truth_acceleration_mps2.npy")
    radar_time = np.load(first / "radar_reference_monotonic_ns.npy")
    radar_adc_time = np.load(first / "radar_adc_sample_monotonic_ns.npy")
    truth_time = np.load(first / "truth_time_ns.npy")
    drdy_time = np.load(
        first / "adxl355" / "algorithm_input" / "drdy_monotonic_ns.npy"
    )
    assert adc.shape == (10, 8, 256)
    assert adc.dtype == np.complex64
    assert chirps.shape == (10, 16, 8, 256)
    assert chirps.dtype == np.complex64
    np.testing.assert_array_equal(chirps.real, np.rint(chirps.real))
    np.testing.assert_array_equal(chirps.imag, np.rint(chirps.imag))
    assert float(np.min(chirps.real)) >= -2048.0
    assert float(np.max(chirps.real)) <= 2047.0
    assert float(np.min(chirps.imag)) >= -2048.0
    np.testing.assert_allclose(
        adc,
        np.mean(chirps, axis=1).astype(np.complex64, copy=False),
        rtol=0.0,
        atol=0.0,
    )
    assert np.any(chirps[:, 1:, :, :] != chirps[:, :-1, :, :])
    assert adxl.shape == (100, 3)
    assert truth_acceleration.shape == (100,)
    assert np.all(np.diff(radar_time) == 10_000_000)
    assert COHERENT_APERTURE_CENTER_OFFSET_NS == 1_907_100
    np.testing.assert_array_equal(
        radar_adc_time - radar_time,
        np.full(radar_time.shape, COHERENT_APERTURE_CENTER_OFFSET_NS),
    )
    np.testing.assert_array_equal(truth_time, radar_adc_time)
    np.testing.assert_allclose(np.diff(nominal_frame_times), 9.0e-3)
    assert np.all(np.diff(drdy_time.astype(np.int64)) == 1_000_000)
    np.testing.assert_array_equal(
        adc,
        np.load(second / "radar" / "algorithm_input" / "adc_cube.npy"),
    )
    np.testing.assert_array_equal(
        adxl,
        np.load(
            second / "adxl355" / "algorithm_input" / "acceleration_mps2.npy"
        ),
    )


def test_simulation_requires_opt_in_and_runs_through_phase1(tmp_path):
    package = tmp_path / "maglev"
    generate_maglev_capture_package(package, duration_s=4.0, seed=23)

    with pytest.raises(FusionInputError, match="allow_simulation=True"):
        load_fusion_input(package)
    with pytest.raises(FusionInputError, match="allow_simulation=True"):
        run_captured_algorithm(package)

    captured = load_captured_fusion_input(package, allow_simulation=True)
    assert captured.is_simulation is True
    assert captured.timing_mode == "synthetic_coherent_aperture_center"
    assert captured.fusion_capture.provenance.clock == (
        "synthetic_monotonic_schedule"
    )
    assert captured.fusion_capture.simulation_ready is True
    assert captured.fusion_capture.algorithm_ready is False
    assert captured.fusion_capture.fusion_ready is False
    assert captured.adc.adc_cube.shape == (400, 8, 256)
    assert captured.fusion_capture.radar.chirp_cube.shape == (400, 16, 8, 256)
    assert captured.acceleration.native_mps2.shape == (4000,)

    # Sensor RNG belongs exclusively to package generation. Loading, target
    # detection, and estimation must remain deterministic consumers.
    with patch(
        "numpy.random.default_rng",
        side_effect=AssertionError("algorithm layer attempted RNG injection"),
    ):
        result_path, summary_path = run_captured_algorithm(
            package,
            allow_simulation=True,
        )
    with np.load(result_path, allow_pickle=False) as arrays:
        assert arrays["q_hat_m"].shape == (400,)
        assert arrays["truth_displacement_m"].shape == (400,)
        assert arrays["truth_displacement_relative_m"].shape == (400,)
        assert arrays["truth_displacement_reference_m"].shape == ()
        assert arrays["truth_acceleration_mps2"].shape == (4000,)
        assert arrays["truth_adxl_time_ns"].shape == (4000,)
        np.testing.assert_array_equal(
            arrays["truth_time_ns"], arrays["radar_time_ns"]
        )
        np.testing.assert_allclose(
            arrays["truth_displacement_relative_m"],
            arrays["truth_displacement_m"]
            - arrays["truth_displacement_reference_m"],
        )
        np.testing.assert_allclose(
            np.mean(arrays["truth_displacement_relative_m"][:20]),
            0.0,
            atol=1.0e-15,
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["is_simulation"] is True
    assert summary["simulation_ready"] is True
    assert summary["simulation_opt_in"] is True
    assert summary["algorithm_ready"] is False
    assert summary["calibrated_fusion_ready"] is False
    assert summary["timing_mode"] == "synthetic_coherent_aperture_center"
    assert summary["source_timestamp_quality"] == (
        "synthetic_coherent_aperture_center"
    )
    assert summary["cold_start_duration_s"] == 0.2
    assert summary["truth_displacement_reference"] == "cold_start_mean"
    assert summary["method_key"] == "fixed_beta"
    assert summary["adaptive_r_mode"] == "posterior_residual"
    assert summary["target_detection"]["uses_truth"] is False
    assert summary["target_detection"]["dynamic_range_db"] == 20.0
    assert summary["target_detection"]["max_candidates"] == 12
    assert np.isfinite(summary["truth_displacement_rmse_m"])
    assert np.isfinite(summary["truth_acceleration_rmse_mps2"])


def test_targetwise_beta_improves_the_fixed_maglev_capture(tmp_path):
    package = tmp_path / "targetwise_beta"
    generate_maglev_capture_package(package, duration_s=4.0, seed=2026)
    fixed_path, fixed_summary_path = run_captured_algorithm(
        package,
        output_path=package / "algorithm" / "fixed_beta.npz",
        allow_simulation=True,
    )
    adaptive_path, adaptive_summary_path = run_captured_algorithm(
        package,
        output_path=package / "algorithm" / "targetwise_beta.npz",
        method="adaptive_beta",
        allow_simulation=True,
    )

    fixed_summary = json.loads(fixed_summary_path.read_text(encoding="utf-8"))
    adaptive_summary = json.loads(
        adaptive_summary_path.read_text(encoding="utf-8")
    )
    assert adaptive_summary["beta_calibration_accepted"] is False
    assert adaptive_summary["beta_calibration_any_accepted"] is True
    assert adaptive_summary["beta_calibration_adxl_accepted"] is False
    assert adaptive_summary["beta_calibration_adxl_any_accepted"] is True
    assert adaptive_summary["beta_calibration_accepted_count"] == 4
    assert adaptive_summary["beta_calibration_all_selected_accepted"] is False
    assert adaptive_summary["beta_calibration_adxl_scale_mode"] == (
        "aoa_anchored_relative"
    )
    assert adaptive_summary["beta_calibration_adxl_reason_by_target"][-2:] == [
        "not_selected",
        "not_selected",
    ]
    assert adaptive_summary["beta_calibration_adxl_eligible_mask"] == [
        True,
        True,
        True,
        True,
        True,
        False,
        False,
    ]
    assert min(
        adaptive_summary["beta_calibration_relative_fold_rank1_fraction"]
    ) >= 0.90
    assert adaptive_summary["truth_displacement_rmse_m"] < 0.01e-3
    assert adaptive_summary["truth_displacement_rmse_m"] < fixed_summary[
        "truth_displacement_rmse_m"
    ]

    expected_beta = 1.0 / np.cos(np.deg2rad([5.0, 15.0, 25.0, 35.0, 45.0]))
    with np.load(fixed_path, allow_pickle=False) as fixed_arrays, np.load(
        adaptive_path,
        allow_pickle=False,
    ) as adaptive_arrays:
        accepted_mask = adaptive_arrays[
            "diagnostic_beta_calibration_accepted_mask"
        ]
        np.testing.assert_array_equal(
            accepted_mask,
            [False, True, True, True, True, False, False],
        )
        np.testing.assert_allclose(
            adaptive_arrays["beta_hat"][:5],
            expected_beta,
            rtol=0.002,
        )
        assert np.linalg.norm(
            adaptive_arrays["beta_hat"][:5] - expected_beta
        ) < np.linalg.norm(fixed_arrays["beta_hat"][:5] - expected_beta)


def test_measured_peak_gate_does_not_require_truth(tmp_path):
    package = tmp_path / "no_truth_detection"
    generate_maglev_capture_package(package, duration_s=0.2, seed=41)
    captured = load_captured_fusion_input(package, allow_simulation=True)
    sensor_only = SimpleNamespace(
        adc=captured.adc,
        frontend_config=captured.frontend_config,
    )
    range_bins, angle_bins, _maps, diagnostics = detect_captured_target_bins(
        sensor_only,
        return_diagnostics=True,
    )
    assert range_bins.size == angle_bins.size
    assert range_bins.size <= 12
    assert diagnostics["uses_truth"] is False
    assert diagnostics["candidate_count_before_dynamic_range"] > range_bins.size
    assert diagnostics["candidate_count_after_limit"] == range_bins.size


@pytest.mark.parametrize("seed", [1, 7, 23, 2026, 2030])
def test_datasheet_profile_fixed_default_rmse_below_001_mm(tmp_path, seed):
    package = tmp_path / f"seed_{seed}"
    generate_maglev_capture_package(package, duration_s=4.0, seed=seed)
    result_path, summary_path = run_captured_algorithm(
        package,
        allow_simulation=True,
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["method_key"] == "fixed_beta"
    assert summary["selected_targets"] == 5
    assert summary["truth_displacement_rmse_m"] < 0.01e-3
    with np.load(result_path, allow_pickle=False) as arrays:
        beta_r = arrays["diagnostic_beta_uncertainty_r_theta_history"]
        assert np.nanmax(np.nan_to_num(beta_r, nan=0.0)) == 0.0


def test_duration_is_bounded_by_measured_event_window(tmp_path):
    with pytest.raises(ValueError, match="cannot exceed"):
        generate_maglev_capture_package(tmp_path / "too_long", duration_s=4.01)
    with pytest.raises(ValueError, match="multiple of 0.01"):
        generate_maglev_capture_package(tmp_path / "partial_frame", duration_s=0.105)

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    with pytest.raises(FileExistsError, match="unrecognized"):
        generate_maglev_capture_package(
            unrelated, duration_s=0.1, overwrite=True
        )


def test_simulation_provenance_tampering_is_rejected(tmp_path):
    package = tmp_path / "tampered"
    generate_maglev_capture_package(package, duration_s=0.1, seed=31)
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_provenance"]["laser_displacement"][
        "scale_calibrated"
    ] = True
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(FusionInputError, match="fixed measured laser"):
        load_fusion_input(package, allow_simulation=True)
