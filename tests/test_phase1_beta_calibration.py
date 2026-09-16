import unittest
from types import SimpleNamespace

import numpy as np

from simulation.phase1.accelerometer import AccelerometerObservation
from simulation.phase1.algorithm import (
    _validate_beta_preintegration_timeline,
    estimate_proposed_full_pipeline_beta_confidence,
)
from simulation.phase1.beta_calibration import (
    BetaCalibrationConfig,
    CommonAoABiasConfig,
    calibrate_common_aoa_bias,
    calibrate_static_beta,
    calibrate_targetwise_beta,
)
from simulation.phase1.config import Phase1Config
from simulation.phase1.radar import RadarAlgorithmInput


class Phase1BetaCalibrationTest(unittest.TestCase):
    @staticmethod
    def _coherent_record(seed=14):
        sample_rate_hz = 200.0
        duration_s = 24.0
        time_s = np.arange(int(sample_rate_hz * duration_s)) / sample_rate_hz
        frequencies_hz = np.array([2.0, 3.7, 6.3, 9.1, 13.4])
        amplitudes_mps2 = np.array([0.18, 0.12, 0.08, 0.05, 0.035])
        phases_rad = np.array([0.3, -0.7, 1.2, 0.1, -1.4])
        delay_s = 0.0175
        wavelength_m = 299_792_458.0 / 77.0e9
        true_beta = np.array([1.18, 1.73])

        acceleration = np.zeros_like(time_s)
        displacement = np.zeros_like(time_s)
        for frequency_hz, amplitude, phase_rad in zip(
            frequencies_hz, amplitudes_mps2, phases_rad
        ):
            omega = 2.0 * np.pi * frequency_hz
            acceleration += amplitude * np.cos(omega * time_s + phase_rad)
            # This construction exactly follows the calibrator delay convention:
            # -w^2 Phi = kappa*p*exp(-jw*tau)*A.
            displacement += -(amplitude / omega**2) * np.cos(
                omega * (time_s - delay_s) + phase_rad
            )

        kappa = 4.0 * np.pi / wavelength_m
        los_phase = kappa * displacement[None, :] / true_beta[:, None]
        rng = np.random.default_rng(seed)
        acceleration += rng.normal(0.0, 0.0015, size=time_s.size)
        los_phase += rng.normal(0.0, 0.003, size=los_phase.shape)
        return time_s, los_phase, acceleration, wavelength_m, true_beta, delay_s

    @staticmethod
    def _targetwise_record(seed=14, acceleration_scale=1.0):
        sample_rate_hz = 200.0
        time_s = np.arange(int(sample_rate_hz * 24.0)) / sample_rate_hz
        frequencies_hz = np.array([2.0, 3.7, 6.3, 9.1, 13.4])
        amplitudes_mps2 = np.array([0.18, 0.12, 0.08, 0.05, 0.035])
        phases_rad = np.array([0.3, -0.7, 1.2, 0.1, -1.4])
        delay_s = 0.0175
        acceleration = np.zeros_like(time_s)
        displacement = np.zeros_like(time_s)
        for frequency_hz, amplitude, phase_rad in zip(
            frequencies_hz, amplitudes_mps2, phases_rad
        ):
            omega = 2.0 * np.pi * frequency_hz
            acceleration += amplitude * np.cos(
                omega * time_s + phase_rad
            )
            displacement += -(amplitude / omega**2) * np.cos(
                omega * (time_s - delay_s) + phase_rad
            )

        wavelength_m = 299_792_458.0 / 77.0e9
        true_angles_deg = np.array([20.0, 35.0, 50.0, 65.0, 75.0])
        true_beta = 1.0 / np.cos(np.deg2rad(true_angles_deg))
        kappa = 4.0 * np.pi / wavelength_m
        rng = np.random.default_rng(seed)
        measured_acceleration = (
            acceleration_scale * acceleration
            + rng.normal(0.0, 0.0015, size=time_s.size)
        )
        los_phase = (
            kappa * displacement[None, :] / true_beta[:, None]
            + rng.normal(0.0, 0.003, size=(true_beta.size, time_s.size))
        )
        return (
            time_s,
            los_phase,
            measured_acceleration,
            wavelength_m,
            true_angles_deg,
            true_beta,
            delay_s,
        )

    def test_recovers_known_beta_and_common_delay_without_truth_input(self):
        time_s, los_phase, acceleration, wavelength_m, true_beta, true_delay_s = (
            self._coherent_record()
        )
        initial_beta = true_beta * np.array([0.82, 1.16])
        config = BetaCalibrationConfig(
            delay_bounds_s=(-0.04, 0.04),
            delay_step_s=5.0e-4,
            min_holdout_improvement=0.01,
        )

        result = calibrate_static_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=config,
        )

        self.assertTrue(result.accepted, result.reason)
        np.testing.assert_allclose(result.beta, true_beta, rtol=0.035, atol=0.0)
        self.assertAlmostEqual(result.delay_s, true_delay_s, delta=0.002)
        self.assertTrue(np.all(result.coherence > 0.8))
        self.assertTrue(np.all(result.holdout_improvement > 0.01))
        self.assertTrue(np.all(np.isfinite(result.variance)))

    def test_no_excitation_rejects_and_returns_initial_beta(self):
        time_s = np.arange(1000) / 100.0
        initial_beta = np.array([1.2, 1.8])

        result = calibrate_static_beta(
            time_s,
            np.zeros((2, time_s.size)),
            np.zeros(time_s.size),
            wavelength_m=0.004,
            initial_beta=initial_beta,
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "insufficient_acceleration_excitation")
        np.testing.assert_array_equal(result.beta, initial_beta)
        self.assertTrue(np.all(result.confidence == 0.0))

    def test_fit_prior_does_not_replace_original_aoa_acceptance_baseline(self):
        time_s, los_phase, acceleration, wavelength_m, true_beta, _ = (
            self._coherent_record()
        )
        initial_beta = true_beta * 0.8

        result = calibrate_static_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            fit_prior_beta=true_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.1,
            ),
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "beta_candidate_change_too_large")
        np.testing.assert_array_equal(result.beta, initial_beta)

    def test_fit_prior_does_not_replace_original_aoa_holdout_baseline(self):
        time_s, los_phase, acceleration, wavelength_m, true_beta, _ = (
            self._coherent_record()
        )
        initial_beta = true_beta * np.array([0.82, 1.16])

        result = calibrate_static_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            fit_prior_beta=true_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
            ),
        )

        self.assertTrue(result.accepted, result.reason)
        self.assertTrue(np.all(result.holdout_improvement > 0.01))
        np.testing.assert_allclose(result.beta, true_beta, rtol=0.035)

    def test_native_preintegration_requires_explicit_radar_interval_anchors(self):
        radar = SimpleNamespace(
            extra={"radar_time_ns": np.array([10, 20, 30], dtype=np.int64)}
        )
        accel = SimpleNamespace(
            native_time_ns=np.array([10, 20, 30], dtype=np.int64),
            preintegration=SimpleNamespace(),
        )

        with self.assertRaisesRegex(
            ValueError, "preintegration_radar_timeline_missing"
        ):
            _validate_beta_preintegration_timeline(radar, accel)

    def test_incoherent_phase_is_rejected_and_never_applied(self):
        time_s, _, acceleration, wavelength_m, _, _ = self._coherent_record()
        rng = np.random.default_rng(91)
        incoherent_phase = rng.normal(0.0, 0.5, size=(2, time_s.size))
        initial_projection = np.array([0.8, 0.6])
        expected_initial_beta = 1.0 / initial_projection

        result = calibrate_static_beta(
            time_s,
            incoherent_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_projection=initial_projection,
        )

        self.assertFalse(result.accepted)
        self.assertIn(
            result.reason,
            {
                "insufficient_phase_acceleration_coherence",
                "cross_validation_delay_inconsistent",
                "cross_validation_beta_inconsistent",
                "delay_candidate_on_search_boundary",
            },
        )
        np.testing.assert_array_equal(result.beta, expected_initial_beta)

    def test_public_api_has_no_truth_argument(self):
        import inspect

        parameters = inspect.signature(calibrate_static_beta).parameters
        self.assertNotIn("truth", parameters)
        self.assertNotIn("kalman", parameters)
        self.assertNotIn("posterior", parameters)

    def test_targetwise_calibration_corrects_different_aoa_errors(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            true_angles_deg,
            true_beta,
            true_delay_s,
        ) = self._targetwise_record()
        measured_angles_deg = true_angles_deg + np.array(
            [5.0, -5.0, 6.0, -6.0, 4.0]
        )
        initial_beta = 1.0 / np.cos(np.deg2rad(measured_angles_deg))

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
                scale_mode="adxl_absolute",
            ),
        )

        self.assertTrue(result.accepted, result.reason)
        self.assertTrue(result.all_accepted, result.reason_by_target)
        np.testing.assert_array_equal(
            result.accepted_mask,
            np.ones(true_beta.size, dtype=bool),
        )
        np.testing.assert_allclose(result.beta, true_beta, rtol=0.01)
        self.assertAlmostEqual(result.delay_s, true_delay_s, delta=0.002)
        self.assertEqual(result.scale_mode, "adxl_absolute")

    def test_targetwise_calibration_rejects_only_an_incoherent_target(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            _true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=29)
        initial_beta = true_beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])
        bad_target = 2
        rng = np.random.default_rng(291)
        los_phase[bad_target] = rng.normal(0.0, 0.25, size=time_s.size)

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
            ),
        )

        expected_mask = np.ones(true_beta.size, dtype=bool)
        expected_mask[bad_target] = False
        np.testing.assert_array_equal(result.accepted_mask, expected_mask)
        self.assertIn(
            result.reason_by_target[bad_target],
            {
                "cross_validation_beta_inconsistent",
                "insufficient_phase_acceleration_coherence",
            },
        )
        self.assertEqual(result.beta[bad_target], initial_beta[bad_target])
        np.testing.assert_allclose(
            result.beta[expected_mask],
            true_beta[expected_mask],
            rtol=0.015,
        )

    def test_invalid_target_cannot_mask_shared_delay_failure(self):
        for mode in ("adxl_absolute", "aoa_anchored_relative"):
            for second_fold_shift_s, bounds, expected_reason in (
                (0.0, (-0.01, 0.01), "delay_candidate_on_search_boundary"),
                (0.015, (-0.06, 0.06), "cross_validation_delay_inconsistent"),
            ):
                with self.subTest(mode=mode, reason=expected_reason):
                    time_s, phase, acceleration, wavelength_m, _, beta, _ = (
                        self._targetwise_record()
                    )
                    if second_fold_shift_s:
                        second_half = time_s >= 12.0
                        for target_phase in phase:
                            target_phase[second_half] = np.interp(
                                time_s[second_half] - second_fold_shift_s,
                                time_s,
                                target_phase,
                            )
                    # A reversed target fails positivity before static delay gates.
                    phase[-1] *= -1.0
                    initial_beta = beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])
                    config = BetaCalibrationConfig(
                        delay_bounds_s=bounds,
                        delay_step_s=5.0e-4,
                        min_holdout_improvement=0.01,
                        max_relative_beta_change=0.5,
                        scale_mode=mode,
                    )
                    raw = calibrate_static_beta(
                        time_s, phase, acceleration,
                        wavelength_m=wavelength_m,
                        initial_beta=initial_beta, config=config,
                    )
                    self.assertEqual(raw.reason, "non_positive_projection_candidate")
                    if second_fold_shift_s:
                        self.assertGreater(
                            abs(np.diff(raw.fold_delay_s)[0]),
                            config.max_fold_delay_difference_s,
                        )
                        self.assertTrue(np.all(raw.fold_delay_s > bounds[0]))
                        self.assertTrue(np.all(raw.fold_delay_s < bounds[1]))
                    else:
                        np.testing.assert_allclose(raw.fold_delay_s, bounds[1])

                    result = calibrate_targetwise_beta(
                        time_s, phase, acceleration,
                        wavelength_m=wavelength_m,
                        initial_beta=initial_beta, config=config,
                    )
                    self.assertFalse(result.accepted)
                    self.assertFalse(np.any(result.accepted_mask))
                    self.assertEqual(result.reason, expected_reason)
                    self.assertEqual(result.reason_by_target, (expected_reason,) * 5)
                    np.testing.assert_array_equal(result.beta, initial_beta)

    def test_relative_mode_does_not_turn_common_adxl_gain_into_beta_error(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=39, acceleration_scale=1.08)
        initial_beta = true_beta.copy()
        changed_target = 2
        initial_beta[changed_target] = 1.0 / np.cos(
            np.deg2rad(true_angles_deg[changed_target] + 7.0)
        )

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.005,
                max_relative_beta_change=0.5,
                scale_mode="aoa_anchored_relative",
            ),
        )

        expected_mask = np.zeros(true_beta.size, dtype=bool)
        expected_mask[changed_target] = True
        self.assertEqual(result.scale_mode, "aoa_anchored_relative")
        np.testing.assert_array_equal(result.accepted_mask, expected_mask)
        np.testing.assert_array_equal(
            result.beta[~expected_mask],
            initial_beta[~expected_mask],
        )
        self.assertAlmostEqual(
            result.beta[changed_target],
            true_beta[changed_target],
            delta=0.01,
        )
        self.assertTrue(np.all(np.abs(result.fold_common_scale - 1.0) > 0.05))

    def test_one_ambiguous_phase_target_falls_back_without_rejecting_others(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            _true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=49)
        initial_beta = true_beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])
        bad_target = 3
        los_phase[bad_target, time_s.size // 2 :] += 3.0

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
                max_unwrapped_phase_step_rad=0.8 * np.pi,
                scale_mode="adxl_absolute",
            ),
        )

        expected_mask = np.ones(true_beta.size, dtype=bool)
        expected_mask[bad_target] = False
        np.testing.assert_array_equal(result.accepted_mask, expected_mask)
        self.assertEqual(
            result.reason_by_target[bad_target],
            "nonfinite_or_ambiguous_unwrapped_phase",
        )
        self.assertEqual(result.beta[bad_target], initial_beta[bad_target])
        np.testing.assert_allclose(
            result.beta[expected_mask],
            true_beta[expected_mask],
            rtol=0.015,
        )

    def test_relative_mode_requires_adxl_correlated_reference_targets(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            _true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=59)
        initial_beta = true_beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_target_coherence=0.9999999,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
                scale_mode="aoa_anchored_relative",
            ),
        )

        self.assertFalse(result.accepted)
        self.assertEqual(
            result.reason,
            "insufficient_adxl_correlated_reference_targets",
        )
        self.assertFalse(np.any(result.relative_adxl_eligible_mask))
        np.testing.assert_array_equal(result.beta, initial_beta)

    def test_relative_reference_selection_is_training_fold_local(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            _true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=63)
        inconsistent_target = true_beta.size - 1
        second_half = time_s >= 0.5 * time_s[-1]
        rng = np.random.default_rng(631)
        los_phase[inconsistent_target, second_half] = rng.normal(
            0.0,
            0.25,
            size=np.count_nonzero(second_half),
        )
        initial_beta = true_beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
                scale_mode="aoa_anchored_relative",
            ),
        )

        self.assertTrue(
            result.relative_fold_reference_mask[0, inconsistent_target]
        )
        self.assertFalse(
            result.relative_fold_reference_mask[1, inconsistent_target]
        )
        self.assertFalse(
            result.relative_adxl_eligible_mask[inconsistent_target]
        )

    def test_relative_mode_rejects_when_target_count_is_too_small(self):
        time_s, los_phase, acceleration, wavelength_m, true_beta, _ = (
            self._coherent_record(seed=69)
        )
        initial_beta = true_beta * np.array([1.10, 0.90])

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                scale_mode="aoa_anchored_relative",
            ),
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "insufficient_relative_scale_targets")
        np.testing.assert_array_equal(result.beta, initial_beta)

    def test_relative_mode_requires_rank1_shared_motion(self):
        (
            time_s,
            los_phase,
            acceleration,
            wavelength_m,
            _true_angles_deg,
            true_beta,
            _true_delay_s,
        ) = self._targetwise_record(seed=79)
        initial_beta = true_beta * np.array([1.10, 0.90, 1.12, 0.88, 1.15])

        result = calibrate_targetwise_beta(
            time_s,
            los_phase,
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial_beta,
            config=BetaCalibrationConfig(
                delay_bounds_s=(-0.04, 0.04),
                delay_step_s=5.0e-4,
                min_holdout_improvement=0.01,
                max_relative_beta_change=0.5,
                min_relative_rank1_fraction=1.0,
                scale_mode="aoa_anchored_relative",
            ),
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "relative_phase_rank1_gate_failed")
        self.assertTrue(np.all(result.relative_fold_rank1_fraction < 1.0))
        np.testing.assert_array_equal(result.beta, initial_beta)

    def test_targetwise_public_api_has_no_truth_or_filter_feedback_argument(self):
        import inspect

        parameters = inspect.signature(calibrate_targetwise_beta).parameters
        self.assertNotIn("truth", parameters)
        self.assertNotIn("kalman", parameters)
        self.assertNotIn("posterior", parameters)

    def test_common_aoa_bias_changes_only_one_shared_delta(self):
        time_s = np.arange(1600) / 100.0
        true_angles = np.array([12.0, 35.0, 61.0])
        shared_angle_error = 6.0
        measured_angles = true_angles + shared_angle_error
        theta = 2.0 * np.sin(2.0 * np.pi * 1.7 * time_s) + 0.7 * np.sin(
            2.0 * np.pi * 4.1 * time_s + 0.4
        )
        bias = np.array([0.3, -1.0, 1.4])
        phase = np.cos(np.deg2rad(true_angles))[:, None] * theta + bias[:, None]
        wrapped = np.angle(np.exp(1j * phase))

        result = calibrate_common_aoa_bias(
            wrapped,
            measured_angles,
            config=CommonAoABiasConfig(delta_bounds_deg=(-12.0, 12.0)),
        )

        self.assertTrue(result.accepted, result.reason)
        self.assertAlmostEqual(result.delta_deg, shared_angle_error, delta=0.15)
        np.testing.assert_allclose(
            result.beta,
            1.0 / np.abs(np.cos(np.deg2rad(true_angles))),
            rtol=0.01,
        )

    def test_common_aoa_bias_rejects_unidentifiable_angle_cluster(self):
        wrapped = np.zeros((2, 400))
        angles = np.array([20.0, 22.0])

        result = calibrate_common_aoa_bias(wrapped, angles)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "insufficient_angle_span")
        np.testing.assert_array_equal(
            result.beta,
            1.0 / np.abs(np.cos(np.deg2rad(angles))),
        )

    def test_common_aoa_bias_rejects_statistically_insignificant_change(self):
        time_s = np.arange(1600) / 100.0
        angles = np.array([12.0, 35.0, 61.0])
        theta = 2.0 * np.sin(2.0 * np.pi * 1.7 * time_s)
        phase = np.cos(np.deg2rad(angles))[:, None] * theta
        wrapped = np.angle(np.exp(1j * phase))

        result = calibrate_common_aoa_bias(wrapped, angles)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "aoa_bias_not_significant")
        np.testing.assert_array_equal(
            result.beta,
            1.0 / np.abs(np.cos(np.deg2rad(angles))),
        )

    def test_common_aoa_bias_rejects_ambiguous_wrapped_phase_step(self):
        wrapped = np.zeros((2, 400), dtype=float)
        wrapped[:, 200:] = 0.9 * np.pi
        angles = np.array([10.0, 40.0])

        result = calibrate_common_aoa_bias(wrapped, angles)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "ambiguous_wrapped_phase_step")

    def test_full_pipeline_precalibrates_then_freezes_beta_from_frame_zero(self):
        sample_rate_hz = 100.0
        sample_count = 1600
        time_s = np.arange(sample_count) / sample_rate_hz
        true_angles = np.array([12.0, 35.0, 61.0])
        measured_angles = true_angles + 4.0
        theta = 2.0 * np.sin(2.0 * np.pi * 1.7 * time_s) + 0.7 * np.sin(
            2.0 * np.pi * 4.1 * time_s + 0.4
        )
        target_bias = np.array([0.3, -1.0, 1.4])
        phase = (
            np.cos(np.deg2rad(true_angles))[:, None] * theta
            + target_bias[:, None]
        )
        wrapped = np.angle(np.exp(1j * phase))
        wavelength_m = 299_792_458.0 / 77.0e9
        displacement = theta * wavelength_m / (4.0 * np.pi)
        acceleration = np.gradient(
            np.gradient(displacement, 1.0 / sample_rate_hz),
            1.0 / sample_rate_hz,
        )
        radar = RadarAlgorithmInput(
            measured_beta=1.0
            / np.abs(np.cos(np.deg2rad(measured_angles))),
            wrapped_phase_rad=wrapped,
            available_mask=np.ones_like(wrapped, dtype=bool),
            selected_indices=np.arange(true_angles.size),
            initial_r=np.full(true_angles.size, 0.05),
            selection_scores=np.ones(true_angles.size),
            extra={"angle_deg": measured_angles},
        )
        accel = AccelerometerObservation(
            true_mps2=acceleration,
            measured_mps2=acceleration,
            bias_mps2=np.zeros(sample_count),
            noise_mps2=np.zeros(sample_count),
        )
        config = Phase1Config(
            duration_s=sample_count / sample_rate_hz,
            sample_rate_hz=sample_rate_hz,
            num_targets=true_angles.size,
            calibrated_process_noise_intensity=50.0,
            beta_calibration_use_adxl=False,
            cold_start_duration_s=0.2,
        )

        result = estimate_proposed_full_pipeline_beta_confidence(
            radar, accel, config
        )
        expected_beta = 1.0 / np.abs(np.cos(np.deg2rad(true_angles)))

        self.assertTrue(result.extra["beta_calibration_accepted"])
        self.assertTrue(result.extra["beta_calibration_common_aoa_accepted"])
        self.assertEqual(
            result.extra["beta_calibration_adxl_reason_by_target"],
            ("disabled", "disabled", "disabled"),
        )
        self.assertAlmostEqual(
            result.extra["beta_calibration_common_aoa_bias_deg"], 4.0, delta=0.15
        )
        self.assertFalse(result.extra["beta_update_enabled"])
        self.assertEqual(result.extra["adaptive_r_mode"], "posterior_residual")
        np.testing.assert_allclose(result.beta_hat, expected_beta, rtol=0.01)
        expected_initial_r = np.clip(
            radar.initial_r * (result.beta_hat / radar.measured_beta) ** 2,
            config.min_measurement_variance,
            config.max_measurement_variance,
        )
        np.testing.assert_allclose(result.extra["initial_r"], expected_initial_r)
        np.testing.assert_allclose(
            result.extra["beta_history"],
            np.repeat(result.beta_hat[:, None], sample_count, axis=1),
        )

    def test_default_requires_adxl_validation_before_applying_common_aoa(self):
        sample_rate_hz = 100.0
        sample_count = 400
        time_s = np.arange(sample_count) / sample_rate_hz
        true_angles = np.array([12.0, 35.0, 61.0])
        measured_angles = true_angles + 4.0
        theta = 2.0 * np.sin(2.0 * np.pi * 1.7 * time_s)
        phase = np.cos(np.deg2rad(true_angles))[:, None] * theta
        wrapped = np.angle(np.exp(1j * phase))
        initial_beta = 1.0 / np.abs(np.cos(np.deg2rad(measured_angles)))
        radar = RadarAlgorithmInput(
            measured_beta=initial_beta,
            wrapped_phase_rad=wrapped,
            available_mask=np.ones_like(wrapped, dtype=bool),
            selected_indices=np.arange(true_angles.size),
            initial_r=np.full(true_angles.size, 0.05),
            selection_scores=np.ones(true_angles.size),
            extra={"angle_deg": measured_angles},
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(sample_count),
            measured_mps2=np.zeros(sample_count),
            bias_mps2=np.zeros(sample_count),
            noise_mps2=np.zeros(sample_count),
        )
        config = Phase1Config(
            duration_s=sample_count / sample_rate_hz,
            sample_rate_hz=sample_rate_hz,
            num_targets=true_angles.size,
            calibrated_process_noise_intensity=50.0,
            cold_start_duration_s=0.2,
        )

        result = estimate_proposed_full_pipeline_beta_confidence(
            radar, accel, config
        )

        self.assertTrue(result.extra["beta_calibration_common_aoa_accepted"])
        self.assertFalse(result.extra["beta_calibration_adxl_accepted"])
        self.assertFalse(result.extra["beta_calibration_accepted"])
        self.assertEqual(
            result.extra["beta_calibration_used_stage"],
            "aoa_initial_fallback",
        )
        self.assertIn(
            "common_aoa_candidate_unverified",
            result.extra["beta_calibration_reason"],
        )
        np.testing.assert_array_equal(result.beta_hat, initial_beta)

    def test_full_pipeline_uses_native_adxl_timestamps_at_a_different_rate(self):
        radar_rate_hz = 100.0
        adxl_rate_hz = 1000.0
        duration_s = 24.0
        radar_time_s = np.arange(int(radar_rate_hz * duration_s)) / radar_rate_hz
        adxl_time_s = np.arange(int(adxl_rate_hz * duration_s)) / adxl_rate_hz
        frequencies_hz = np.array([2.0, 3.7, 6.3, 9.1, 13.4])
        amplitudes_mps2 = np.array([0.18, 0.12, 0.08, 0.05, 0.035])
        phases_rad = np.array([0.3, -0.7, 1.2, 0.1, -1.4])
        delay_s = 0.0175
        acceleration = np.zeros_like(adxl_time_s)
        displacement = np.zeros_like(radar_time_s)
        for frequency_hz, amplitude, phase_rad in zip(
            frequencies_hz, amplitudes_mps2, phases_rad
        ):
            omega = 2.0 * np.pi * frequency_hz
            acceleration += amplitude * np.cos(
                omega * adxl_time_s + phase_rad
            )
            displacement += -(amplitude / omega**2) * np.cos(
                omega * (radar_time_s - delay_s) + phase_rad
            )

        wavelength_m = 299_792_458.0 / 77.0e9
        kappa = 4.0 * np.pi / wavelength_m
        true_beta = np.array([1.18, 1.73])
        true_angles = np.rad2deg(np.arccos(1.0 / true_beta))
        measured_angles = true_angles + 4.0
        los_phase = (
            kappa * displacement[None, :] / true_beta[:, None]
            + np.array([0.4, -1.2])[:, None]
        )
        wrapped = np.angle(np.exp(1j * los_phase))
        timestamp_origin_ns = 5_000_000_000
        radar_time_ns = timestamp_origin_ns + np.rint(
            radar_time_s * 1.0e9
        ).astype(np.int64)
        adxl_time_ns = timestamp_origin_ns + np.rint(
            adxl_time_s * 1.0e9
        ).astype(np.int64)
        radar = RadarAlgorithmInput(
            measured_beta=1.0
            / np.abs(np.cos(np.deg2rad(measured_angles))),
            wrapped_phase_rad=wrapped,
            available_mask=np.ones_like(wrapped, dtype=bool),
            selected_indices=np.arange(true_beta.size),
            initial_r=np.full(true_beta.size, 0.05),
            selection_scores=np.ones(true_beta.size),
            extra={
                "radar_time_ns": radar_time_ns,
                "angle_deg": measured_angles,
            },
        )
        accel = SimpleNamespace(
            measured_mps2=np.interp(radar_time_s, adxl_time_s, acceleration),
            native_time_ns=adxl_time_ns,
            native_mps2=acceleration,
            valid_mask=np.ones(adxl_time_s.size, dtype=bool),
            preintegration=None,
        )
        config = Phase1Config(
            duration_s=duration_s,
            sample_rate_hz=radar_rate_hz,
            num_targets=true_beta.size,
            calibrated_process_noise_intensity=50.0,
            cold_start_duration_s=0.2,
            beta_calibration_scale_mode="adxl_absolute",
        )

        result = estimate_proposed_full_pipeline_beta_confidence(
            radar, accel, config
        )

        self.assertTrue(result.extra["beta_calibration_common_aoa_accepted"])
        self.assertAlmostEqual(
            result.extra["beta_calibration_common_aoa_bias_deg"],
            4.0,
            delta=0.15,
        )
        self.assertTrue(result.extra["beta_calibration_adxl_accepted"])
        self.assertAlmostEqual(
            result.extra["beta_calibration_adxl_delay_s"], delay_s, delta=0.002
        )
        np.testing.assert_allclose(result.beta_hat, true_beta, rtol=0.01)
        np.testing.assert_allclose(
            result.extra["beta_history"],
            np.repeat(result.beta_hat[:, None], radar_time_s.size, axis=1),
        )


if __name__ == "__main__":
    unittest.main()
