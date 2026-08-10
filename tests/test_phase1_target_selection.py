import inspect
import unittest

import numpy as np

from simulation.phase1.accelerometer import simulate_accelerometer
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.scenarios import build_phase1_scenarios
from simulation.phase1.selection import (
    DetectedPeak,
    detect_peaks_2d,
    merge_close_angle_peaks,
    select_targets_from_measurements,
)
from simulation.phase1.truth import generate_multifrequency_truth


def _phase_iq(phase_rad, noise_std=0.0, seed=1):
    rng = np.random.default_rng(seed)
    iq = np.exp(1j * phase_rad)
    if noise_std > 0.0:
        iq = iq + noise_std * (
            rng.standard_normal(phase_rad.shape) + 1j * rng.standard_normal(phase_rad.shape)
        )
    return iq


class Phase1TargetSelectionTest(unittest.TestCase):
    def test_peak_detection_uses_2d_local_max_and_relative_threshold(self):
        frame = np.array(
            [
                [1.0, 1.1, 1.0, 1.2, 1.0],
                [1.1, 2.2, 2.1, 1.0, 1.1],
                [1.0, 2.0, 8.0, 1.2, 1.0],
                [1.2, 1.0, 1.3, 1.1, 1.0],
                [1.0, 1.1, 1.0, 1.2, 7.5],
            ],
            dtype=float,
        )
        angle_axis = np.array([-30.0, -15.0, 0.0, 15.0, 30.0])

        peaks = detect_peaks_2d(frame, angle_axis_deg=angle_axis)

        coordinates = {(peak.range_bin, peak.angle_bin) for peak in peaks}
        self.assertEqual(coordinates, {(2, 2), (4, 4)})
        self.assertNotIn((1, 1), coordinates)
        self.assertTrue(all(peak.value >= np.median(frame) + 6.0 * np.median(np.abs(frame - np.median(frame))) for peak in peaks))

    def test_angle_merge_same_range_within_15deg(self):
        peaks = [
            DetectedPeak(range_bin=10, angle_bin=0, angle_deg=20.0, value=9.0),
            DetectedPeak(range_bin=11, angle_bin=1, angle_deg=32.0, value=6.0),
            DetectedPeak(range_bin=10, angle_bin=2, angle_deg=48.0, value=7.0),
            DetectedPeak(range_bin=14, angle_bin=3, angle_deg=23.0, value=8.0),
        ]

        merged = merge_close_angle_peaks(peaks)

        close_cluster = next(item for item in merged if item.peak_count == 2)
        self.assertEqual(len(merged), 3)
        self.assertAlmostEqual(close_cluster.range_bin, 10.4)
        self.assertAlmostEqual(close_cluster.angle_deg, 24.8)
        self.assertEqual({member.angle_deg for member in close_cluster.member_peaks}, {20.0, 32.0})

    def test_sliding_window_appearance_rate_rejects_intermittent_target(self):
        sample_rate_hz = 200.0
        t = np.arange(400, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        phase = 0.7 * np.sin(2.0 * np.pi * 12.0 * t)
        iq = np.vstack([_phase_iq(phase), _phase_iq(phase), _phase_iq(phase)])
        wrapped_phase = np.angle(iq)
        available = np.ones_like(wrapped_phase, dtype=bool)
        available[1, 140:280] = False

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.9, 0.9, 0.9]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
        )

        np.testing.assert_array_equal(selected.selected_indices, np.array([0, 2]))
        self.assertIn("low_presence", selected.diagnostics.rejected_reasons[1])

    def test_band_consistency_uses_measured_acceleration_and_complex_iq(self):
        sample_rate_hz = 500.0
        t = np.arange(1000, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        matching_phase = 0.7 * np.sin(2.0 * np.pi * 12.0 * t)
        mismatched_phase = 0.7 * np.sin(2.0 * np.pi * 37.0 * t)
        iq = np.vstack([_phase_iq(matching_phase), _phase_iq(mismatched_phase)])
        wrapped_phase = np.vstack([matching_phase, matching_phase])
        available = np.ones_like(wrapped_phase, dtype=bool)

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.85, 0.85]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            hard_band_consistency=True,
        )

        np.testing.assert_array_equal(selected.selected_indices, np.array([0]))
        self.assertIn("low_band_consistency", selected.diagnostics.rejected_reasons[1])

    def test_hard_rejected_targets_are_not_selected_just_to_fill_minimum_count(self):
        sample_rate_hz = 500.0
        t = np.arange(1000, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        phase = 0.7 * np.sin(2.0 * np.pi * 12.0 * t)
        iq = np.vstack([
            _phase_iq(phase, noise_std=0.001, seed=11),
            _phase_iq(phase, noise_std=0.001, seed=12),
        ])
        wrapped_phase = np.angle(iq)
        available = np.ones_like(wrapped_phase, dtype=bool)

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.2, 0.3]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
        )

        self.assertEqual(selected.selected_indices.size, 0)
        self.assertIn("low_geometry_projection", selected.diagnostics.rejected_reasons[0])
        self.assertIn("low_geometry_projection", selected.diagnostics.rejected_reasons[1])

    def test_selection_geometry_uses_projection_not_beta_magnitude(self):
        n_targets = 3
        n_samples = 320
        sample_rate_hz = 100.0
        t = np.arange(n_samples, dtype=float) / sample_rate_hz
        iq = np.exp(1j * 2.0 * np.pi * 4.0 * t)[np.newaxis, :].repeat(n_targets, axis=0)
        wrapped = np.angle(iq)
        available = np.ones((n_targets, n_samples), dtype=bool)
        measured_accel = np.sin(2.0 * np.pi * 4.0 * t)
        projection = np.array([0.9, 0.6, 0.2], dtype=float)
        beta = 1.0 / projection

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped,
            available_mask=available,
            measured_beta=beta,
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            min_projection_abs=0.45,
            min_snr_db=0.0,
            min_band_energy_ratio=0.0,
        )

        selected_indices = selected.selected_indices.tolist()
        self.assertIn(0, selected_indices)
        self.assertIn(1, selected_indices)
        self.assertNotIn(2, selected_indices)

    def test_initial_r_uses_snr_even_when_band_consistency_is_low(self):
        sample_rate_hz = 500.0
        t = np.arange(1000, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        mismatched_phase = 0.7 * np.sin(2.0 * np.pi * 37.0 * t)
        iq = _phase_iq(mismatched_phase, noise_std=0.001, seed=3)[np.newaxis, :]
        wrapped_phase = np.angle(iq)
        available = np.ones_like(wrapped_phase, dtype=bool)

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.9]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            min_score=0.0,
        )

        track = selected.diagnostics.tracks[0]
        self.assertLess(track.band_energy_ratio, 0.5)
        self.assertGreater(track.snr_est_db, 40.0)
        self.assertIn(0, selected.selected_indices)
        self.assertLess(selected.initial_r[0], 1.0)
        self.assertGreaterEqual(selected.initial_r[0], 1.0e-4)

    def test_initial_r_is_lower_for_higher_snr_target(self):
        sample_rate_hz = 500.0
        t = np.arange(1000, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        phase = 0.7 * np.sin(2.0 * np.pi * 12.0 * t)
        iq = np.vstack(
            [
                _phase_iq(phase, noise_std=0.05, seed=4),
                _phase_iq(phase, noise_std=0.2, seed=5),
            ]
        )
        wrapped_phase = np.angle(iq)
        available = np.ones_like(wrapped_phase, dtype=bool)

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.9, 0.9]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            min_score=0.0,
            max_targets=2,
        )

        tracks = {track.target_index: track for track in selected.diagnostics.tracks}
        self.assertGreater(tracks[0].snr_est_db, tracks[1].snr_est_db)
        self.assertLess(selected.initial_r[0], selected.initial_r[1])

    def test_initial_r_inflates_for_lower_presence_and_geometry(self):
        sample_rate_hz = 500.0
        t = np.arange(1000, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 12.0 * t)
        phase = 0.7 * np.sin(2.0 * np.pi * 12.0 * t)
        iq = np.vstack(
            [
                _phase_iq(phase, noise_std=0.1, seed=6),
                _phase_iq(phase, noise_std=0.1, seed=6),
                _phase_iq(phase, noise_std=0.1, seed=6),
            ]
        )
        wrapped_phase = np.angle(iq)
        available = np.ones_like(wrapped_phase, dtype=bool)
        available[1, ::4] = False

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped_phase,
            available_mask=available,
            measured_beta=1.0 / np.array([0.9, 0.9, 0.5]),
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            min_score=0.0,
            max_targets=3,
        )

        self.assertLess(selected.initial_r[0], selected.initial_r[1])
        self.assertLess(selected.initial_r[0], selected.initial_r[2])

    def test_selection_rejects_low_projection_low_snr_target_before_kalman(self):
        n_targets = 5
        n_samples = 320
        sample_rate_hz = 100.0
        t = np.arange(n_samples, dtype=float) / sample_rate_hz
        measured_accel = np.sin(2.0 * np.pi * 4.0 * t)
        phase = 0.8 * np.sin(2.0 * np.pi * 4.0 * t)
        iq = np.exp(1j * phase)[np.newaxis, :].repeat(n_targets, axis=0)
        iq[4] += 0.8 * (
            np.sin(2.0 * np.pi * 17.0 * t)
            + 1j * np.cos(2.0 * np.pi * 19.0 * t)
        )
        wrapped = np.angle(iq)
        available = np.ones((n_targets, n_samples), dtype=bool)
        measured_beta = 1.0 / np.array([0.92, 0.85, 0.72, 0.55, 0.18], dtype=float)

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped,
            available_mask=available,
            measured_beta=measured_beta,
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
        )

        self.assertLessEqual(selected.selected_indices.size, 4)
        self.assertNotIn(4, set(selected.selected_indices.tolist()))
        self.assertTrue(
            {
                "low_geometry_projection",
                "low_snr",
                "low_band_consistency",
            }.intersection(selected.diagnostics.rejected_reasons[4])
        )

    def test_calibration_indices_keep_soft_geometry_peer_outside_fusion_set(self):
        n_targets = 5
        n_samples = 320
        sample_rate_hz = 100.0
        t = np.arange(n_samples, dtype=float) / sample_rate_hz
        phase = 0.7 * np.sin(2.0 * np.pi * 4.0 * t)
        iq = np.exp(1j * phase)[np.newaxis, :].repeat(n_targets, axis=0)
        wrapped = np.angle(iq)
        available = np.ones((n_targets, n_samples), dtype=bool)
        measured_accel = np.sin(2.0 * np.pi * 4.0 * t)
        projection = np.array([0.9, 0.8, 0.6, 0.43, 0.18], dtype=float)
        beta = 1.0 / projection

        selected = select_targets_from_measurements(
            iq=iq,
            wrapped_phase_rad=wrapped,
            available_mask=available,
            measured_beta=beta,
            measured_acceleration_mps2=measured_accel,
            sample_rate_hz=sample_rate_hz,
            min_snr_db=0.0,
            min_band_energy_ratio=0.0,
            min_projection_abs=0.45,
            calibration_min_projection_abs=0.35,
        )

        self.assertNotIn(3, selected.selected_indices.tolist())
        self.assertIn(3, selected.calibration_indices.tolist())
        self.assertNotIn(4, selected.calibration_indices.tolist())
        self.assertLess(selected.calibration_initial_r[3], 25.0)
        self.assertEqual(selected.calibration_initial_r[4], 25.0)

    def test_selection_input_has_no_truth_or_kalman_fields(self):
        params = set(inspect.signature(select_targets_from_measurements).parameters)

        self.assertTrue(
            {
                "iq",
                "wrapped_phase_rad",
                "available_mask",
                "measured_beta",
                "measured_acceleration_mps2",
            }.issubset(params)
        )
        forbidden = {
            "truth",
            "q_m",
            "radar",
            "radar_beta",
            "true_los_phase_rad",
            "true_main_phase_rad",
            "corrected_phase_rad",
            "innovation_rad",
            "r_history",
            "kalman",
        }
        self.assertTrue(params.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
