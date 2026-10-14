import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from paper_bridge_simulation import package_builder
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response
from system.algorithm.config import AlgorithmConfig
from system.algorithm.frontend import extract_dbf_targets_streaming, range_angle_process
from system.algorithm.io import build_algorithm_inputs, load_capture_package
from system.algorithm.kalman import run_fixed_beta_kalman
from system.algorithm.phase import recursive_circle_phase, unwrap_nearest_branch
from system.algorithm.run import run
from system.algorithm.selection import detect_target_bins


class AlgorithmPipelineTest(unittest.TestCase):
    def test_streaming_dbf_extraction_is_block_equivalent(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            capture = load_capture_package(package)
            first = range_angle_process(capture.adc_cube[:1], capture.frontend)
            ranges, angles, _ = detect_target_bins(first.cube, first.angle_axis_deg, max_candidates=5)
            streamed = extract_dbf_targets_streaming(
                capture.adc_cube, ranges, angles, capture.frontend, block_size=32
            )

            blocks = []
            for start in range(0, capture.adc_cube.shape[0], 32):
                end = min(capture.adc_cube.shape[0], start + 32)
                processed = range_angle_process(capture.adc_cube[start:end], capture.frontend)
                blocks.append(processed.cube[:, ranges, angles].T)
            expected = np.concatenate(blocks, axis=1)
            np.testing.assert_allclose(streamed.slow_time, expected)
            self.assertEqual(streamed.wrapped_phase_rad.shape, (5, 500))
            self.assertTrue(np.all(streamed.available_mask))

    def test_paper_bridge_package_matches_algorithm_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            result = Path(temporary) / "result.npz"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            output, summary = run(package, result)
            self.assertTrue(output.is_file())
            payload = json.loads(summary.read_text(encoding="utf-8"))
            metadata = json.loads((package / "paper_response_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_type"], "paper_parameterized_synthetic")
            self.assertEqual(
                json.loads((package / "status.json").read_text(encoding="utf-8"))["source_type"],
                "paper_bridge_simulation",
            )
            self.assertEqual(payload["method"], "base_iq_circle_structural_kalman")
            self.assertNotIn("radar_mode", payload)
            arrays = np.load(output)
            self.assertEqual(arrays["q_hat_m"].shape, (500,))
            self.assertEqual(arrays["selected_target_indices"].size, 5)
            frame_ns = np.load(package / "sync" / "radar_frame_monotonic_ns.npy")
            np.testing.assert_array_equal(np.diff(frame_ns), np.full(499, 2_000_000))

    def test_paper_response_has_consistent_acceleration_and_sampling_margin(self):
        time_s, displacement, acceleration, _ = simulate_response()
        self.assertEqual(time_s.size, round(13.0 * REFERENCE_RATE_HZ))
        self.assertAlmostEqual(float(np.max(np.abs(displacement))), 1.712e-3, places=9)
        dt = 1.0 / REFERENCE_RATE_HZ
        numerical_acceleration = np.gradient(np.gradient(displacement, dt), dt)
        interior = slice(10, -10)
        relative_error = np.linalg.norm(
            numerical_acceleration[interior] - acceleration[interior]
        ) / np.linalg.norm(acceleration[interior])
        self.assertLess(relative_error, 2.0e-3)

    def test_initial_measurement_variance_decreases_with_amplitude(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "capture"
            package_builder.generate(package, duration_s=1.0, seed=2026)
            capture = load_capture_package(package)
            radar, acceleration, targets, radar_rate = build_algorithm_inputs(capture)
            selected = radar.selected_indices
            amplitude = np.abs(targets.slow_time[selected, 0])
            initial_r = radar.initial_r[selected]
            self.assertGreater(np.ptp(initial_r), 0.0)
            self.assertTrue(np.all(np.diff(initial_r[np.argsort(amplitude)]) <= 1.0e-12))
            result = run_fixed_beta_kalman(radar, acceleration, AlgorithmConfig(sample_rate_hz=radar_rate))
            np.testing.assert_allclose(result.beta_hat, radar.measured_beta)

    def test_recursive_circle_phase_is_causal_and_removes_center_offset(self):
        k = np.arange(400)
        true_phase = 1.5 * np.sin(2.0 * np.pi * k / 200.0)
        iq = (0.8 + 0.5j) + np.exp(1j * true_phase)
        wrapped, centers, radii, _, _ = recursive_circle_phase(iq[None, :])
        # Before the first accepted fit the phase is referenced to the origin;
        # that cold-start error remains as a constant offset afterwards.
        converged = np.flatnonzero(np.abs(centers[0]) > 0.0)[0]
        error = wrapped[0, converged:] - true_phase[converged:]
        self.assertLess(np.max(np.abs(error - np.mean(error))), 1.0e-6)
        self.assertLess(abs(centers[0, -1] - (0.8 + 0.5j)), 1.0e-6)
        self.assertLess(abs(radii[0, -1] - 1.0), 1.0e-6)
        prefix, _, _, _, _ = recursive_circle_phase(iq[None, :250])
        np.testing.assert_array_equal(prefix[0], wrapped[0, :250])

    def test_nearest_branch_unwrapping_continues_across_wrap_and_gaps(self):
        true_phase = np.linspace(0.0, 6.0 * np.pi, 120)
        wrapped = np.angle(np.exp(1j * true_phase))[None, :]
        available = np.ones_like(wrapped, dtype=bool)
        available[0, 40:43] = False
        unwrapped = unwrap_nearest_branch(wrapped, available, [0])
        self.assertTrue(np.all(np.isnan(unwrapped[0, 40:43])))
        np.testing.assert_allclose(unwrapped[0, available[0]], true_phase[available[0]], atol=1.0e-12)


if __name__ == "__main__":
    unittest.main()
