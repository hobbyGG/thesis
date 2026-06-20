import unittest

import numpy as np

from simulation.phase1.config import Phase1Config
from simulation.phase1 import algorithm as phase1_algorithm
from simulation.phase1.methods import (
    cold_start_reference_mean,
    estimate_itoh_ls,
    estimate_multitarget_aoa_fixed_kappa,
    estimate_multitarget_true_kappa_fixed_r,
    estimate_oracle,
    estimate_proposed,
    estimate_proposed_full_pipeline,
    estimate_proposed_full_pipeline_doc_strict,
    estimate_proposed_full_pipeline_kappa_confidence_r,
    estimate_proposed_full_pipeline_posterior_r,
    estimate_selected_aoa_fixed_kappa,
    estimate_single_target_ma_style,
)
from simulation.phase1.accelerometer import simulate_accelerometer
from simulation.phase1.radar import RadarAlgorithmInput, simulate_radar_targets, to_algorithm_radar_input
from simulation.phase1.truth import generate_multifrequency_truth


class Phase1MethodsTest(unittest.TestCase):
    def test_oracle_recovers_truth_from_true_main_phase(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=101)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_oracle(truth, radar, config)
        q_ref = cold_start_reference_mean(truth.q_m, config)

        np.testing.assert_allclose(result.q_hat_m, truth.q_m - q_ref, atol=1e-15)
        self.assertEqual(result.method_name, "oracle")

    def test_itoh_ls_works_in_clean_single_target_small_motion_case(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=102,
            component_amplitudes_mm=(0.01, 0.005, 0.002),
            target_snr_db=(80.0, 80.0, 80.0, 80.0, 80.0),
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_itoh_ls(truth, radar, config, target_index=0)
        q_ref = cold_start_reference_mean(truth.q_m, config)
        start = int(round(config.cold_start_duration_s * config.sample_rate_hz))
        rmse_mm = np.sqrt(np.mean((result.q_hat_m[start:] - (truth.q_m[start:] - q_ref)) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.005)


class Phase1KalmanMethodsTest(unittest.TestCase):
    def test_multitarget_fixed_kappa_recovers_clean_multitarget_case(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=111,
            component_amplitudes_mm=(0.02, 0.01, 0.005),
            target_snr_db=(70.0, 70.0, 70.0, 70.0, 70.0),
            accel_noise_std_mps2=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        accel = simulate_accelerometer(truth, config)

        result = estimate_multitarget_true_kappa_fixed_r(truth, radar, accel, config)
        q_ref = cold_start_reference_mean(truth.q_m, config)
        start = int(round(config.cold_start_duration_s * config.sample_rate_hz))
        rmse_mm = np.sqrt(np.mean((result.q_hat_m[start:] - (truth.q_m[start:] - q_ref)) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.012)

    def test_multitarget_aoa_fixed_kappa_keeps_measured_aoa_values(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=113,
            aoa_error_deg=8.0,
            accel_noise_std_mps2=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_multitarget_aoa_fixed_kappa(radar_input, accel, config)

        self.assertEqual(result.method_name, "multitarget_aoa_fixed_kappa")
        np.testing.assert_allclose(result.kappa_hat, radar.measured_kappa)

    def test_proposed_updates_kappa_from_aoa_initial_values(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1000.0,
            seed=112,
            aoa_error_deg=8.0,
            target_snr_db=(40.0, 40.0, 40.0, 40.0, 40.0),
            accel_noise_std_mps2=0.0,
            kappa_update_start_s=0.1,
            kappa_window_samples=40,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        initial_error = np.median(np.abs(radar.measured_kappa - radar.kappa))
        final_error = np.median(np.abs(result.kappa_hat - radar.kappa))

        self.assertLess(final_error, initial_error)

    def test_methods_proposed_accepts_legacy_truth_radar_config_call(self):
        config = Phase1Config(duration_s=0.5, sample_rate_hz=1000.0, seed=123)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_proposed(truth, radar, config)

        self.assertEqual(result.method_name, "proposed")
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)

    def test_proposed_accepts_only_algorithm_visible_radar_input(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=117)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        self.assertFalse(hasattr(radar_input, "kappa"))
        self.assertFalse(hasattr(radar_input, "true_main_phase_rad"))
        self.assertFalse(hasattr(radar_input, "true_los_phase_rad"))

        result = estimate_proposed(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed")
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)

    def test_proposed_records_kappa_history_that_converges_after_aoa_error(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1000.0,
            seed=115,
            aoa_error_deg=10.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            kappa_update_start_s=0.1,
            kappa_window_samples=50,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        kappa_history = result.extra["kappa_history"]
        initial_error = np.median(np.abs(kappa_history[:, 0] - radar.kappa))
        final_error = np.median(np.abs(kappa_history[:, -1] - radar.kappa))

        self.assertEqual(kappa_history.shape, radar.wrapped_phase_rad.shape)
        self.assertLess(final_error, initial_error)

    def test_proposed_uses_measured_acceleration_instead_of_true_acceleration(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=114,
            target_snr_db=(80.0, 80.0, 80.0, 80.0, 80.0),
            accel_noise_std_mps2=0.0,
            accel_bias_mps2=8.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        measured_result = estimate_proposed(radar_input, accel, config)
        oracle_accel = simulate_accelerometer(truth, Phase1Config(**{**config.__dict__, "accel_bias_mps2": 0.0}))
        oracle_accel_result = estimate_proposed(radar_input, oracle_accel, config)

        difference = np.sqrt(np.mean((measured_result.q_hat_m - oracle_accel_result.q_hat_m) ** 2)) * 1e3
        self.assertGreater(difference, 0.001)

    def test_proposed_adaptive_r_increases_for_degraded_targets_and_recovers(self):
        config = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=1000.0,
            seed=116,
            degraded_target_indices=(0, 1),
            degradation_start_s=1.2,
            degradation_end_s=2.6,
            degradation_snr_drop_db=25.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        before = truth.t < config.degradation_start_s - 0.1
        during = (truth.t >= config.degradation_start_s) & (truth.t <= config.degradation_end_s)
        after = truth.t > config.degradation_end_s + 0.1

        for target_idx in config.degraded_target_indices:
            before_r = np.nanmedian(result.r_history[target_idx, before])
            during_r = np.nanmedian(result.r_history[target_idx, during])
            after_r = np.nanmedian(result.r_history[target_idx, after])
            self.assertGreater(during_r, before_r * 10.0)
            self.assertLess(after_r, during_r * 0.1)

    def test_proposed_full_pipeline_uses_only_selected_targets(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=118)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([1, 3], dtype=int)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([0.9, 0.8], dtype=float),
        )

        result = estimate_proposed_full_pipeline(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(result.corrected_phase_rad), axis=1))

        np.testing.assert_array_equal(used_targets, selected)
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)
        self.assertEqual(result.extra["selected_target_count"], 2)

    def test_target_wise_initial_r_seeds_r_history(self):
        config = Phase1Config(duration_s=0.2, sample_rate_hz=1000.0, seed=119)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        initial_r = np.array([0.2, 0.4, 0.6, 0.8, 1.0], dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=np.array([0, 2, 4], dtype=int),
            initial_r=initial_r,
            selection_scores=np.array([0.9, 0.7, 0.6], dtype=float),
        )

        result = estimate_selected_aoa_fixed_kappa(radar_input, accel, config)

        np.testing.assert_allclose(result.extra["initial_r"], initial_r)
        np.testing.assert_allclose(result.r_history[[0, 2, 4], 0], initial_r[[0, 2, 4]])
        self.assertTrue(np.all(np.isnan(result.r_history[[1, 3], 0])))

    def test_default_initial_r_extra_preserves_initial_variance(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=124,
            degraded_target_indices=(0,),
            degradation_start_s=0.1,
            degradation_end_s=0.8,
            degradation_snr_drop_db=25.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)

        np.testing.assert_allclose(
            result.extra["initial_r"],
            np.full(config.num_targets, config.initial_measurement_variance),
        )

    def test_selected_aoa_fixed_kappa_keeps_selected_measured_kappa(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=120, aoa_error_deg=6.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 2, 3], dtype=int)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([1.0, 0.8, 0.7], dtype=float),
        )

        result = estimate_selected_aoa_fixed_kappa(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(result.corrected_phase_rad), axis=1))

        self.assertEqual(result.method_name, "selected_aoa_fixed_kappa")
        np.testing.assert_allclose(result.kappa_hat, radar.measured_kappa)
        np.testing.assert_array_equal(used_targets, selected)

    def test_proposed_full_pipeline_still_uses_algorithm_visible_input_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=122)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=np.array([0, 1, 2], dtype=int),
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([1.0, 0.8, 0.7], dtype=float),
        )

        self.assertFalse(hasattr(radar_input, "kappa"))
        self.assertFalse(hasattr(radar_input, "true_main_phase_rad"))
        self.assertFalse(hasattr(radar_input, "true_los_phase_rad"))

        result = estimate_proposed_full_pipeline(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline")
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)

    def test_proposed_full_pipeline_calibrated_uses_selected_targets_and_reports_q(self):
        config = Phase1Config(
            duration_s=0.3,
            sample_rate_hz=1000.0,
            seed=125,
            calibrated_process_noise_intensity=5.0e4,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([1, 3], dtype=int)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([0.9, 0.8], dtype=float),
        )

        old_result = estimate_proposed_full_pipeline(radar_input, accel, config)
        calibrated_result = phase1_algorithm.estimate_proposed_full_pipeline_calibrated(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(calibrated_result.corrected_phase_rad), axis=1))

        self.assertEqual(calibrated_result.method_name, "proposed_full_pipeline_calibrated")
        self.assertEqual(calibrated_result.q_hat_m.shape, truth.q_m.shape)
        np.testing.assert_array_equal(used_targets, selected)
        np.testing.assert_array_equal(calibrated_result.extra["selected_indices"], selected)
        self.assertEqual(calibrated_result.extra["process_noise_intensity"], 5.0e4)
        self.assertEqual(calibrated_result.extra["calibrated_q"], 5.0e4)
        self.assertEqual(calibrated_result.extra["adaptive_r_mode"], "kappa_confidence")
        self.assertIn("kappa_variance_history", calibrated_result.extra)
        self.assertIn("kappa_uncertainty_r_history", calibrated_result.extra)
        self.assertEqual(config.process_noise_intensity, 5.0)
        self.assertEqual(old_result.method_name, "proposed_full_pipeline")
        self.assertNotIn("calibrated_q", old_result.extra)

    def test_doc_strict_full_pipeline_uses_documented_kappa_r_and_initial_r_rules(self):
        config = Phase1Config(
            duration_s=0.4,
            sample_rate_hz=1000.0,
            seed=126,
            calibrated_process_noise_intensity=5.0e4,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 2], dtype=int)
        quality_initial_r = np.array([0.2, 25.0, 0.4, 25.0, 25.0], dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=quality_initial_r,
            selection_scores=np.array([0.9, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_doc_strict(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline_doc_strict")
        self.assertEqual(result.extra["kappa_update_mode"], "plain_window_ls")
        self.assertEqual(result.extra["adaptive_r_mode"], "posterior_residual")
        self.assertEqual(result.extra["initial_r_policy"], "uniform_r_max")
        np.testing.assert_allclose(
            result.extra["initial_r"][selected],
            np.full(selected.shape, config.max_measurement_variance),
        )
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)

    def test_posterior_r_full_pipeline_changes_only_adaptive_r_residual_rule(self):
        config = Phase1Config(
            duration_s=0.4,
            sample_rate_hz=1000.0,
            seed=127,
            calibrated_process_noise_intensity=5.0e4,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 2], dtype=int)
        quality_initial_r = np.array([0.2, 25.0, 0.4, 25.0, 25.0], dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=quality_initial_r,
            selection_scores=np.array([0.9, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_posterior_r(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline_posterior_r")
        self.assertEqual(result.extra["kappa_update_mode"], "centered_regularized_ls")
        self.assertEqual(result.extra["adaptive_r_mode"], "posterior_residual")
        self.assertEqual(result.extra["initial_r_policy"], "provided_or_config")
        np.testing.assert_allclose(result.extra["initial_r"], quality_initial_r)
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)

    def test_kappa_confidence_r_full_pipeline_tracks_kappa_uncertainty_in_r(self):
        config = Phase1Config(
            duration_s=0.8,
            sample_rate_hz=1000.0,
            seed=128,
            aoa_error_deg=10.0,
            target_snr_db=(50.0, 50.0, 50.0, 50.0, 50.0),
            accel_noise_std_mps2=0.0,
            calibrated_process_noise_intensity=5.0e4,
            kappa_update_start_s=0.1,
            kappa_window_samples=60,
            kappa_confidence_initial_variance=0.04,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 1, 2], dtype=int)
        initial_r = np.full(config.num_targets, 0.2, dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_kappa=radar.measured_kappa.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=initial_r,
            selection_scores=np.array([0.9, 0.8, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_kappa_confidence_r(radar_input, accel, config)
        kappa_variance = result.extra["kappa_variance_history"]
        kappa_r = result.extra["kappa_uncertainty_r_history"]

        self.assertEqual(result.method_name, "proposed_full_pipeline_kappa_confidence_r")
        self.assertEqual(result.extra["adaptive_r_mode"], "kappa_confidence")
        self.assertEqual(kappa_variance.shape, radar.wrapped_phase_rad.shape)
        self.assertEqual(kappa_r.shape, radar.wrapped_phase_rad.shape)
        self.assertGreater(np.nanmedian(kappa_variance[selected, 0]), np.nanmedian(kappa_variance[selected, -1]))
        self.assertTrue(np.nanmax(kappa_r[selected]) > 0.0)
        np.testing.assert_allclose(
            result.r_history[selected, 0],
            result.extra["base_r_history"][selected, 0] + kappa_r[selected, 0],
        )


class Phase1SingleTargetBaselineTest(unittest.TestCase):
    def test_single_target_ma_style_uses_one_target_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=121, accel_noise_std_mps2=0.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)

        result = estimate_single_target_ma_style(truth, radar, accel, config, target_index=0)

        self.assertEqual(result.method_name, "single_target_ma_style")
        used_targets = np.flatnonzero(np.any(np.isfinite(result.corrected_phase_rad), axis=1))
        np.testing.assert_array_equal(used_targets, np.array([0]))


if __name__ == "__main__":
    unittest.main()
