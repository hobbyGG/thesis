import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from simulation.phase1.algorithm import run_structural_phase_kalman
from simulation.phase1.capture_reader import (
    build_captured_algorithm_input,
    load_captured_fusion_input,
)
from simulation.phase1.config import Phase1Config


class _RadarCalibration:
    azimuth_virtual_channel_indices = np.array([1], dtype=np.int64)
    virtual_array_positions_wavelengths = np.array([0.0])
    range_bias_correction_m = -0.02

    @staticmethod
    def calibrated_azimuth_cube(cube):
        return np.asarray(cube)[:, 1:2, :] * (0.0 - 1.0j)


class Phase1CaptureFusionReaderTest(unittest.TestCase):
    def test_builds_calibrated_frontend_and_async_acceleration(self):
        radar_time_ns = np.array(
            [1_000_000_000, 1_100_000_000, 1_250_000_000],
            dtype=np.int64,
        )
        adxl_time_ns = np.arange(
            990_000_000,
            1_260_000_001,
            10_000_000,
            dtype=np.int64,
        )
        adc_cube = np.ones((3, 2, 4), dtype=np.complex64)
        adc_cube[:, 1, :] = 2.0 + 0.0j
        capture = SimpleNamespace(
            fusion_ready=True,
            quality=SimpleNamespace(readiness_failures=()),
            value_calibration=SimpleNamespace(radar=_RadarCalibration()),
            acceleration_structure_mps2=np.full(adxl_time_ns.shape, 2.0),
            radar_adc_sample_monotonic_ns=radar_time_ns,
            radar_reference_monotonic_ns=radar_time_ns - 100_000,
            adxl_sample_monotonic_ns=adxl_time_ns,
            radar=SimpleNamespace(
                adc_cube=adc_cube,
                manifest={
                    "radar": {
                        "tx_indices": [0, 1, 2],
                        "rx_indices": [0, 1, 2, 3],
                        "adc_samples_per_chirp": 4,
                        "adc_sample_rate_hz": 5.0e6,
                        "ramp_end_time_s": 60.0e-6,
                        "physical_chirps_per_frame": 6,
                        "range_resolution_m": 0.1,
                    }
                },
            ),
            directory=Path("/capture"),
        )

        with patch(
            "mmwavecapture.fusion_input.load_fusion_input",
            return_value=capture,
        ):
            loaded = load_captured_fusion_input(
                "/capture",
                max_adxl_gap_ns=10_000_000,
            )

        np.testing.assert_allclose(loaded.adc.adc_cube, -2.0j)
        np.testing.assert_allclose(loaded.adc.frame_times_s, [0.0, 0.1, 0.25])
        np.testing.assert_allclose(
            loaded.adc.range_axis_m,
            [-0.02, 0.08, 0.18, 0.28],
        )
        np.testing.assert_allclose(
            loaded.acceleration.preintegration.delta_v_mps,
            [0.2, 0.3],
        )
        np.testing.assert_allclose(loaded.acceleration.measured_mps2, 2.0)
        self.assertEqual(loaded.frontend_config.num_virtual_rx, 1)
        self.assertEqual(loaded.calibration_mode, "provided_unvalidated")
        self.assertTrue(
            any("marked unvalidated" in warning for warning in loaded.warnings)
        )

        algorithm_input = build_captured_algorithm_input(
            loaded,
            range_bins=[0],
            angle_bins=[loaded.frontend_config.num_angle_bins // 2],
            selection_options={
                "min_presence": 0.0,
                "min_band_energy_ratio": 0.0,
                "min_snr_db": -np.inf,
                "min_projection_abs": 0.0,
            },
        )
        self.assertEqual(algorithm_input.radar.wrapped_phase_rad.shape, (1, 3))
        self.assertEqual(algorithm_input.radar.selected_indices.tolist(), [0])
        self.assertAlmostEqual(algorithm_input.effective_radar_rate_hz, 8.0)
        np.testing.assert_array_equal(
            algorithm_input.radar.extra["radar_time_ns"],
            radar_time_ns,
        )

        result = run_structural_phase_kalman(
            method_name="captured_async_fixture",
            radar=algorithm_input.radar,
            accel=algorithm_input.acceleration,
            config=Phase1Config(
                sample_rate_hz=algorithm_input.effective_radar_rate_hz,
                num_targets=1,
            ),
            initial_beta=algorithm_input.radar.measured_beta,
            update_beta=False,
            adaptive_r=False,
            selected_indices=algorithm_input.radar.selected_indices,
            initial_r=algorithm_input.radar.initial_r,
        )
        self.assertEqual(result.q_hat_m.shape, (3,))
        self.assertEqual(
            result.extra["propagation_timing"],
            "native_timestamp_preintegration",
        )

    def test_readiness_blockers_fail_before_algorithm_adaptation(self):
        capture = SimpleNamespace(
            fusion_ready=False,
            quality=SimpleNamespace(
                readiness_failures=("radar_reference_to_adc_latency_not_calibrated",)
            ),
        )
        with patch(
            "mmwavecapture.fusion_input.load_fusion_input",
            return_value=capture,
        ):
            with self.assertRaisesRegex(RuntimeError, "latency_not_calibrated"):
                load_captured_fusion_input(
                    "/capture",
                    max_adxl_gap_ns=10_000_000,
                )

    def test_algorithm_ready_capture_uses_nominal_fallbacks(self):
        radar_time_ns = np.array(
            [1_000_000_000, 1_100_000_000, 1_200_000_000],
            dtype=np.int64,
        )
        adxl_time_ns = np.arange(
            990_000_000,
            1_210_000_001,
            10_000_000,
            dtype=np.int64,
        )
        acceleration_xyz = np.column_stack(
            (
                np.full(adxl_time_ns.shape, 2.0),
                np.full(adxl_time_ns.shape, 3.0),
                np.full(adxl_time_ns.shape, 4.0),
            )
        )
        capture = SimpleNamespace(
            fusion_ready=False,
            algorithm_ready=True,
            quality=SimpleNamespace(
                readiness_failures=("hardware_sync_not_validated",),
                algorithm_readiness_failures=(),
            ),
            value_calibration=None,
            acceleration_structure_mps2=None,
            radar_adc_sample_monotonic_ns=None,
            radar_reference_monotonic_ns=radar_time_ns,
            provenance=SimpleNamespace(sync_mode="hardware_trigger"),
            adxl_sample_monotonic_ns=adxl_time_ns,
            adxl355=SimpleNamespace(acceleration_mps2=acceleration_xyz),
            calibration=SimpleNamespace(adxl_group_delay_calibrated=False),
            radar=SimpleNamespace(
                adc_cube=np.ones((3, 2, 4), dtype=np.complex64),
                manifest={
                    "radar": {
                        "tx_indices": [0, 1],
                        "rx_indices": [0],
                        "adc_samples_per_chirp": 4,
                        "adc_sample_rate_hz": 5.0e6,
                        "ramp_end_time_s": 60.0e-6,
                        "physical_chirps_per_frame": 2,
                        "range_resolution_m": 0.1,
                    }
                },
            ),
            directory=Path("/capture"),
        )

        with patch(
            "mmwavecapture.fusion_input.load_fusion_input",
            return_value=capture,
        ):
            loaded = load_captured_fusion_input(
                "/capture",
                nominal_adxl_axis="x",
                nominal_adxl_sign=-1,
            )

        self.assertEqual(loaded.timing_mode, "hardware_trigger_reference")
        self.assertEqual(
            loaded.calibration_mode,
            "nominal_unvalidated_adxl_neg_x",
        )
        self.assertEqual(loaded.max_adxl_gap_ns, 25_000_000)
        np.testing.assert_allclose(loaded.acceleration.native_mps2, -2.0)
        np.testing.assert_allclose(
            loaded.frontend_config.virtual_array_positions_wavelengths,
            [0.0, 0.5],
        )
        self.assertGreaterEqual(len(loaded.warnings), 3)


if __name__ == "__main__":
    unittest.main()
