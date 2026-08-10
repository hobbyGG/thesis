import unittest
from dataclasses import replace
from types import SimpleNamespace

import numpy as np

from simulation.phase1.config import Phase1Config
from simulation.phase1 import algorithm as phase1_algorithm
from simulation.phase1.methods import (
    cold_start_reference_mean,
    estimate_itoh_ls,
    estimate_multitarget_aoa_fixed_beta,
    estimate_multitarget_true_beta_fixed_r,
    estimate_oracle,
    estimate_proposed,
    estimate_proposed_full_pipeline,
    estimate_proposed_full_pipeline_aoa_fixed_beta,
    estimate_proposed_full_pipeline_doc_strict,
    estimate_proposed_full_pipeline_beta_confidence,
    estimate_proposed_full_pipeline_beta_confidence_r,
    estimate_proposed_full_pipeline_posterior_r,
    estimate_selected_aoa_fixed_beta,
    estimate_single_target_ma_style,
)
from simulation.phase1.accelerometer import AccelerometerObservation, simulate_accelerometer
from simulation.phase1.radar import RadarAlgorithmInput, simulate_radar_targets, to_algorithm_radar_input
from simulation.phase1.scenario_inputs import build_scenario_inputs
from simulation.phase1.scenarios import build_phase1_scenarios
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
    def test_method_result_and_config_expose_beta_names_only_for_core_estimator(self):
        config = Phase1Config()
        legacy_prefix = "kap" + "pa"

        for name in (
            "beta_window_samples",
            "beta_update_start_s",
            "beta_bootstrap_prior_weight",
            "beta_confidence_initial_variance",
            "beta_confidence_min_variance",
            "beta_confidence_max_variance",
            "beta_confidence_forgetting",
            "beta_min_abs",
            "beta_max_abs",
        ):
            self.assertTrue(hasattr(config, name), name)

        for name in (
            f"{legacy_prefix}_window_samples",
            f"{legacy_prefix}_update_start_s",
            f"{legacy_prefix}_bootstrap_prior_weight",
            f"{legacy_prefix}_confidence_initial_variance",
            f"{legacy_prefix}_confidence_min_variance",
            f"{legacy_prefix}_confidence_max_variance",
            f"{legacy_prefix}_confidence_forgetting",
            f"{legacy_prefix}_min_abs",
            f"{legacy_prefix}_max_abs",
        ):
            self.assertFalse(hasattr(config, name), name)

        field_names = set(phase1_algorithm.MethodResult.__dataclass_fields__)
        self.assertIn("los_corrected_phase_rad", field_names)
        self.assertIn("beta_hat", field_names)
        self.assertIn("r_theta_history", field_names)
        self.assertNotIn("corrected_phase_rad", field_names)
        self.assertNotIn(f"{legacy_prefix}_hat", field_names)
        self.assertNotIn("r_history", field_names)

    def test_beta_observation_update_converts_corrected_los_phase_to_structural_phase(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1.0,
            seed=110,
            cold_start_duration_s=1.0,
            process_noise_intensity=0.0,
            initial_state_variance=100.0,
            initial_rate_variance=0.0,
            initial_measurement_variance=1.0e-6,
            min_measurement_variance=1.0e-9,
            max_measurement_variance=25.0,
            beta_update_start_s=10.0,
        )
        radar_input = SimpleNamespace(
            wrapped_phase_rad=np.array([[0.0, 0.5]], dtype=float),
            available_mask=np.array([[False, True]], dtype=bool),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(2, dtype=float),
            measured_mps2=np.zeros(2, dtype=float),
            bias_mps2=np.zeros(2, dtype=float),
            noise_mps2=np.zeros(2, dtype=float),
        )

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="beta_update_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=np.array([2.0], dtype=float),
            update_beta=False,
            adaptive_r=False,
            adaptive_r_mode="posterior_residual",
        )

        self.assertGreater(result.theta_hat_rad[1], 0.9)
        np.testing.assert_allclose(result.los_corrected_phase_rad[0, 1], 0.5)
        np.testing.assert_allclose(result.beta_hat, np.array([2.0], dtype=float))

    def test_multitarget_fixed_beta_recovers_clean_multitarget_case(self):
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

        result = estimate_multitarget_true_beta_fixed_r(truth, radar, accel, config)
        q_ref = cold_start_reference_mean(truth.q_m, config)
        start = int(round(config.cold_start_duration_s * config.sample_rate_hz))
        rmse_mm = np.sqrt(np.mean((result.q_hat_m[start:] - (truth.q_m[start:] - q_ref)) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.012)

    def test_multitarget_aoa_fixed_beta_keeps_measured_aoa_values(self):
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

        result = estimate_multitarget_aoa_fixed_beta(radar_input, accel, config)

        self.assertEqual(result.method_name, "multitarget_aoa_fixed_beta")
        np.testing.assert_allclose(result.beta_hat, radar.measured_beta)

    def test_proposed_updates_beta_from_aoa_initial_values(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1000.0,
            seed=112,
            aoa_error_deg=8.0,
            target_snr_db=(40.0, 40.0, 40.0, 40.0, 40.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=40,
            beta_update_reference_mode="posterior",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        initial_error = np.median(np.abs(radar.measured_beta - radar.beta))
        final_error = np.median(np.abs(result.beta_hat - radar.beta))

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

        self.assertFalse(hasattr(radar_input, "beta"))
        self.assertFalse(hasattr(radar_input, "true_main_phase_rad"))
        self.assertFalse(hasattr(radar_input, "true_los_phase_rad"))

        result = estimate_proposed(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed")
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)

    def test_proposed_records_beta_history_that_converges_after_aoa_error(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1000.0,
            seed=115,
            aoa_error_deg=10.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=50,
            beta_update_reference_mode="posterior",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        beta_history = result.extra["beta_history"]
        initial_error = np.median(np.abs(beta_history[:, 0] - radar.beta))
        final_error = np.median(np.abs(beta_history[:, -1] - radar.beta))

        self.assertEqual(beta_history.shape, radar.wrapped_phase_rad.shape)
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
            before_r = np.nanmedian(result.r_theta_history[target_idx, before])
            during_r = np.nanmedian(result.r_theta_history[target_idx, during])
            after_r = np.nanmedian(result.r_theta_history[target_idx, after])
            self.assertGreater(during_r, before_r * 10.0)
            self.assertLess(after_r, during_r * 0.1)

    def test_proposed_full_pipeline_uses_only_selected_targets(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=118)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([1, 3], dtype=int)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([0.9, 0.8], dtype=float),
        )

        result = estimate_proposed_full_pipeline(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(result.los_corrected_phase_rad), axis=1))

        np.testing.assert_array_equal(used_targets, selected)
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)
        self.assertEqual(result.extra["selected_target_count"], 2)

    def test_target_wise_initial_r_seeds_r_theta_history(self):
        config = Phase1Config(duration_s=0.2, sample_rate_hz=1000.0, seed=119)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        initial_r = np.array([0.2, 0.4, 0.6, 0.8, 1.0], dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=np.array([0, 2, 4], dtype=int),
            initial_r=initial_r,
            selection_scores=np.array([0.9, 0.7, 0.6], dtype=float),
        )

        result = estimate_selected_aoa_fixed_beta(radar_input, accel, config)

        np.testing.assert_allclose(result.extra["initial_r"], initial_r)
        np.testing.assert_allclose(result.r_theta_history[[0, 2, 4], 0], initial_r[[0, 2, 4]])
        self.assertTrue(np.all(np.isnan(result.r_theta_history[[1, 3], 0])))

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

    def test_selected_aoa_fixed_beta_keeps_selected_measured_beta(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=120, aoa_error_deg=6.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 2, 3], dtype=int)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([1.0, 0.8, 0.7], dtype=float),
        )

        result = estimate_selected_aoa_fixed_beta(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(result.los_corrected_phase_rad), axis=1))

        self.assertEqual(result.method_name, "selected_aoa_fixed_beta")
        np.testing.assert_allclose(result.beta_hat, radar.measured_beta)
        np.testing.assert_array_equal(used_targets, selected)

    def test_proposed_full_pipeline_still_uses_algorithm_visible_input_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=122)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=np.array([0, 1, 2], dtype=int),
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([1.0, 0.8, 0.7], dtype=float),
        )

        self.assertFalse(hasattr(radar_input, "beta"))
        self.assertFalse(hasattr(radar_input, "true_main_phase_rad"))
        self.assertFalse(hasattr(radar_input, "true_los_phase_rad"))

        result = estimate_proposed_full_pipeline(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline")
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)

    def test_proposed_full_pipeline_beta_confidence_uses_selected_targets_and_reports_q(self):
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
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([0.9, 0.8], dtype=float),
        )

        old_result = estimate_proposed_full_pipeline(radar_input, accel, config)
        confidence_result = estimate_proposed_full_pipeline_beta_confidence(radar_input, accel, config)
        used_targets = np.flatnonzero(np.any(np.isfinite(confidence_result.los_corrected_phase_rad), axis=1))

        self.assertEqual(confidence_result.method_name, "proposed_full_pipeline_beta_confidence")
        self.assertEqual(confidence_result.q_hat_m.shape, truth.q_m.shape)
        np.testing.assert_array_equal(used_targets, selected)
        np.testing.assert_array_equal(confidence_result.extra["selected_indices"], selected)
        self.assertEqual(confidence_result.extra["process_noise_intensity"], 5.0e4)
        self.assertEqual(confidence_result.extra["calibrated_q"], 5.0e4)
        self.assertEqual(confidence_result.extra["adaptive_r_mode"], "beta_confidence")
        self.assertIn("beta_variance_history", confidence_result.extra)
        self.assertIn("beta_uncertainty_r_theta_history", confidence_result.extra)
        self.assertEqual(config.process_noise_intensity, 5.0)
        self.assertEqual(old_result.method_name, "proposed_full_pipeline")
        self.assertNotIn("calibrated_q", old_result.extra)

    def test_proposed_full_pipeline_aoa_fixed_beta_keeps_main_pipeline_but_disables_beta_update(self):
        config = Phase1Config(
            duration_s=0.5,
            sample_rate_hz=1000.0,
            seed=128,
            aoa_error_deg=8.0,
            calibrated_process_noise_intensity=5.0e4,
            beta_update_start_s=0.05,
            beta_bootstrap_prior_weight=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 2, 4], dtype=int)
        initial_r = np.full(config.num_targets, config.initial_measurement_variance, dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=initial_r,
            selection_scores=np.array([1.0, 0.8, 0.6], dtype=float),
        )

        result = estimate_proposed_full_pipeline_aoa_fixed_beta(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline_aoa_fixed_beta")
        self.assertEqual(result.extra["adaptive_r_mode"], "beta_confidence")
        self.assertEqual(result.extra["beta_update_enabled"], False)
        self.assertEqual(result.extra["process_noise_intensity"], 5.0e4)
        self.assertEqual(result.extra["calibrated_q"], 5.0e4)
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)
        np.testing.assert_allclose(result.beta_hat, radar.measured_beta)
        finite_history = np.isfinite(result.extra["beta_history"])
        self.assertTrue(np.any(finite_history[selected]))
        for target_idx in selected:
            target_history = result.extra["beta_history"][target_idx]
            target_history = target_history[np.isfinite(target_history)]
            self.assertGreater(target_history.size, 0)
            np.testing.assert_allclose(target_history, radar.measured_beta[target_idx])
        self.assertIn("beta_variance_history", result.extra)
        self.assertIn("beta_uncertainty_r_theta_history", result.extra)

    def test_calibrated_name_remains_backward_compatible_alias(self):
        config = Phase1Config(
            duration_s=0.3,
            sample_rate_hz=1000.0,
            seed=129,
            calibrated_process_noise_intensity=5.0e4,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=np.array([0, 1], dtype=int),
            initial_r=np.full(config.num_targets, config.initial_measurement_variance),
            selection_scores=np.array([0.9, 0.8], dtype=float),
        )

        alias_result = phase1_algorithm.estimate_proposed_full_pipeline_calibrated(radar_input, accel, config)

        self.assertEqual(alias_result.method_name, "proposed_full_pipeline_beta_confidence")
        self.assertEqual(alias_result.extra["legacy_alias"], "proposed_full_pipeline_calibrated")

    def test_doc_strict_full_pipeline_uses_documented_beta_r_and_initial_r_rules(self):
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
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=quality_initial_r,
            selection_scores=np.array([0.9, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_doc_strict(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline_doc_strict")
        self.assertEqual(result.extra["beta_update_mode"], "plain_window_ls")
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
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=quality_initial_r,
            selection_scores=np.array([0.9, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_posterior_r(radar_input, accel, config)

        self.assertEqual(result.method_name, "proposed_full_pipeline_posterior_r")
        self.assertEqual(result.extra["beta_update_mode"], "centered_regularized_ls")
        self.assertEqual(result.extra["adaptive_r_mode"], "posterior_residual")
        self.assertEqual(result.extra["initial_r_policy"], "provided_or_config")
        np.testing.assert_allclose(result.extra["initial_r"], quality_initial_r)
        np.testing.assert_array_equal(result.extra["selected_indices"], selected)

    def test_beta_confidence_full_pipeline_tracks_beta_uncertainty_in_r(self):
        config = Phase1Config(
            duration_s=0.8,
            sample_rate_hz=1000.0,
            seed=128,
            aoa_error_deg=10.0,
            target_snr_db=(50.0, 50.0, 50.0, 50.0, 50.0),
            accel_noise_std_mps2=0.0,
            calibrated_process_noise_intensity=5.0e4,
            beta_update_start_s=0.1,
            beta_window_samples=60,
            beta_confidence_initial_variance=0.04,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        selected = np.array([0, 1, 2], dtype=int)
        initial_r = np.full(config.num_targets, 0.2, dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_beta=radar.measured_beta.copy(),
            wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
            available_mask=radar.available_mask.copy(),
            selected_indices=selected,
            initial_r=initial_r,
            selection_scores=np.array([0.9, 0.8, 0.7], dtype=float),
        )

        result = estimate_proposed_full_pipeline_beta_confidence_r(radar_input, accel, config)
        beta_variance = result.extra["beta_variance_history"]
        beta_r = result.extra["beta_uncertainty_r_theta_history"]

        self.assertEqual(result.method_name, "proposed_full_pipeline_beta_confidence")
        self.assertEqual(result.extra["legacy_alias"], "proposed_full_pipeline_beta_confidence_r")
        self.assertEqual(result.extra["adaptive_r_mode"], "beta_confidence")
        self.assertEqual(beta_variance.shape, radar.wrapped_phase_rad.shape)
        self.assertEqual(beta_r.shape, radar.wrapped_phase_rad.shape)
        self.assertGreater(np.nanmedian(beta_variance[selected, 0]), np.nanmedian(beta_variance[selected, -1]))
        self.assertTrue(np.nanmax(beta_r[selected]) > 0.0)
        np.testing.assert_allclose(
            result.r_theta_history[selected, 0],
            result.extra["base_r_theta_history"][selected, 0] + beta_r[selected, 0],
        )

    def test_beta_bootstrap_reports_fft_derived_frontend_beta_diagnostics(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "aoa_error_bootstrap"][0]
        config = replace(
            scenario,
            beta_update_start_s=0.1,
            beta_window_samples=60,
            beta_bootstrap_prior_weight=20.0,
        )
        inputs = build_scenario_inputs(config)

        result = estimate_proposed_full_pipeline_beta_confidence(
            inputs.radar.selected_frontend,
            inputs.accelerometer,
            config,
        )
        fixed = estimate_selected_aoa_fixed_beta(
            inputs.radar.selected_frontend,
            inputs.accelerometer,
            config,
        )
        references = inputs.frontend.target_reference_indices
        selected = np.asarray(result.extra["selected_indices"], dtype=int)
        initial_errors = []
        final_errors = []
        for target_idx in selected:
            reference_idx = int(references[target_idx])
            if reference_idx < 0:
                continue
            true_beta = float(inputs.radar.target_level.beta[reference_idx])
            finite_history = result.extra["beta_history"][target_idx]
            finite_history = finite_history[np.isfinite(finite_history)]
            if finite_history.size == 0:
                continue
            initial_errors.append(abs(float(finite_history[0]) - true_beta) / true_beta)
            final_errors.append(abs(float(result.beta_hat[target_idx]) - true_beta) / true_beta)

        self.assertGreater(len(final_errors), 0)
        self.assertTrue(np.isfinite(float(np.median(initial_errors))))
        self.assertTrue(np.isfinite(float(np.median(final_errors))))
        q_ref = cold_start_reference_mean(inputs.truth.q_m, config)
        truth_relative = inputs.truth.q_m - q_ref
        result_rmse = float(np.sqrt(np.nanmean((result.q_hat_m - truth_relative) ** 2)) * 1e3)
        fixed_rmse = float(np.sqrt(np.nanmean((fixed.q_hat_m - truth_relative) ** 2)) * 1e3)
        self.assertLess(result_rmse, fixed_rmse)

    def test_centered_beta_fit_returns_los_to_structural_beta(self):
        config = Phase1Config()
        los = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=float)
        expected_beta = 1.8
        theta = expected_beta * los

        fitted = phase1_algorithm._fit_beta_via_projection(
            theta_values=theta,
            los_values=los,
            beta_prior=1.0,
            prior_weight=0.0,
            config=config,
        )

        self.assertIsNotNone(fitted)
        self.assertAlmostEqual(fitted[0], expected_beta)

    def test_direct_beta_fit_estimates_los_to_structural_slope(self):
        config = Phase1Config()
        los = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=float)
        theta = 1.8 * los + np.array([0.0, 0.25, -0.05, 0.05, -0.2], dtype=float)
        expected_beta = float(np.dot(los - los.mean(), theta - theta.mean()) / np.dot(los - los.mean(), los - los.mean()))

        fitted = phase1_algorithm._fit_beta_direct(
            theta_values=theta,
            los_values=los,
            beta_prior=1.0,
            prior_weight=0.0,
            config=config,
        )

        self.assertIsNotNone(fitted)
        self.assertAlmostEqual(fitted[0], expected_beta)

    def test_beta_fit_from_self_posterior_preserves_wrong_common_scale(self):
        config = Phase1Config()
        true_beta = 1.25
        wrong_scale = 1.18
        los = np.linspace(-2.0, 2.0, 21)
        theta_true = true_beta * los
        theta_self_posterior = wrong_scale * theta_true

        fitted = phase1_algorithm._fit_beta_direct(
            theta_values=theta_self_posterior,
            los_values=los,
            beta_prior=1.0,
            prior_weight=0.0,
            config=config,
        )

        self.assertIsNotNone(fitted)
        self.assertAlmostEqual(fitted[0], wrong_scale * true_beta)

    def test_common_aoa_bias_fit_recovers_shared_angle_offset(self):
        config = Phase1Config(
            beta_common_aoa_bias_search_deg=15.0,
            beta_common_aoa_bias_step_deg=0.1,
            beta_bootstrap_prior_weight=0.0,
        )
        true_angles = np.array([5.0, 18.0, 32.0], dtype=float)
        measured_angles = true_angles + 10.0
        measured_beta = 1.0 / np.cos(np.deg2rad(measured_angles))
        true_beta = 1.0 / np.cos(np.deg2rad(true_angles))
        theta = np.linspace(-3.0, 3.0, 81)
        los = theta[None, :] / true_beta[:, None]

        fitted = phase1_algorithm._fit_common_aoa_bias_beta(
            theta_values=theta,
            los_values_by_target=los,
            measured_beta=measured_beta,
            selected_indices=np.arange(3, dtype=int),
            prior_bias_deg=0.0,
            config=config,
        )

        self.assertIsNotNone(fitted)
        beta, bias_deg, diagnostics = fitted
        self.assertAlmostEqual(bias_deg, 10.0, places=6)
        np.testing.assert_allclose(beta, true_beta, rtol=1.0e-12, atol=1.0e-12)
        self.assertLess(diagnostics["residual_ratio"], 1.0e-12)

    def test_theta_reference_scaling_matches_acceleration_anchor_slope(self):
        theta = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
        anchor = np.array([3.0, 5.0, 7.0, 9.0], dtype=float)

        scaled = phase1_algorithm._scale_theta_reference_to_anchor(theta, anchor)

        np.testing.assert_allclose(scaled, 2.0 * theta)

    def test_theta_reference_anchor_gate_rejects_unreliable_scale(self):
        config = Phase1Config(
            beta_anchor_min_abs_corr=0.9,
            beta_anchor_min_scale=0.5,
            beta_anchor_max_scale=2.0,
        )
        theta = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
        noisy_anchor = np.array([4.0, 1.0, 3.0, 2.0], dtype=float)

        scaled, accepted, diagnostics = phase1_algorithm._scale_theta_reference_to_anchor_with_gate(
            theta,
            noisy_anchor,
            config,
        )

        self.assertFalse(accepted)
        np.testing.assert_allclose(scaled, theta)
        self.assertLess(diagnostics["anchor_abs_corr"], config.beta_anchor_min_abs_corr)

    def test_theta_reference_anchor_gate_accepts_reliable_scale(self):
        config = Phase1Config(
            beta_anchor_min_abs_corr=0.9,
            beta_anchor_min_scale=0.5,
            beta_anchor_max_scale=2.0,
        )
        theta = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
        anchor = np.array([3.0, 5.0, 7.0, 9.0], dtype=float)

        scaled, accepted, diagnostics = phase1_algorithm._scale_theta_reference_to_anchor_with_gate(
            theta,
            anchor,
            config,
        )

        self.assertTrue(accepted)
        self.assertAlmostEqual(diagnostics["anchor_scale"], 2.0)
        np.testing.assert_allclose(scaled, 2.0 * theta)

    def test_prediction_direct_ls_records_prediction_reference_used_for_unwrap(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=20.0,
            seed=118,
            aoa_error_deg=6.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=8,
            beta_update_reference_mode="prediction_direct_ls",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        prediction_reference = result.extra["beta_prediction_theta_rad"]

        self.assertEqual(result.extra["beta_update_reference_mode"], "prediction_direct_ls")
        self.assertEqual(prediction_reference.shape, result.theta_hat_rad.shape)
        self.assertTrue(np.any(np.isfinite(prediction_reference)))

    def test_loo_update_reference_excludes_current_target_observation(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1.0,
            seed=119,
            cold_start_duration_s=1.0,
            process_noise_intensity=0.0,
            initial_state_variance=1.0e6,
            initial_rate_variance=0.0,
            initial_measurement_variance=1.0e-9,
            min_measurement_variance=1.0e-12,
            max_measurement_variance=25.0,
            beta_update_start_s=10.0,
        )
        wrapped = np.array(
            [
                [0.0, 0.5],
                [0.0, 1.5],
            ],
            dtype=float,
        )
        radar_input = SimpleNamespace(
            wrapped_phase_rad=wrapped,
            available_mask=np.array([[False, True], [False, True]], dtype=bool),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(wrapped.shape[1], dtype=float),
            measured_mps2=np.zeros(wrapped.shape[1], dtype=float),
            bias_mps2=np.zeros(wrapped.shape[1], dtype=float),
            noise_mps2=np.zeros(wrapped.shape[1], dtype=float),
        )

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="loo_reference_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=np.array([1.0, 1.0], dtype=float),
            update_beta=False,
            adaptive_r=False,
            adaptive_r_mode="posterior_residual",
        )

        loo_reference = result.extra["beta_loo_theta_rad"]
        self.assertEqual(loo_reference.shape, wrapped.shape)
        self.assertAlmostEqual(float(loo_reference[0, 1]), 1.5, places=5)
        self.assertAlmostEqual(float(loo_reference[1, 1]), 0.5, places=5)

    def test_loo_update_reference_uses_nonselected_peer_candidates(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1.0,
            seed=121,
            cold_start_duration_s=1.0,
            process_noise_intensity=0.0,
            initial_state_variance=1.0e6,
            initial_rate_variance=0.0,
            initial_measurement_variance=1.0e-9,
            min_measurement_variance=1.0e-12,
            max_measurement_variance=25.0,
            beta_update_start_s=10.0,
            beta_update_reference_mode="loo_update_direct_ls",
        )
        wrapped = np.array(
            [
                [0.0, 0.5],
                [0.0, 1.5],
                [0.0, 3.0],
            ],
            dtype=float,
        )
        radar_input = SimpleNamespace(
            wrapped_phase_rad=wrapped,
            available_mask=np.array([[False, True], [False, True], [False, True]], dtype=bool),
            selected_indices=np.array([0, 1], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(wrapped.shape[1], dtype=float),
            measured_mps2=np.zeros(wrapped.shape[1], dtype=float),
            bias_mps2=np.zeros(wrapped.shape[1], dtype=float),
            noise_mps2=np.zeros(wrapped.shape[1], dtype=float),
        )

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="loo_peer_pool_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=np.ones(3, dtype=float),
            update_beta=False,
            adaptive_r=False,
            adaptive_r_mode="posterior_residual",
            selected_indices=radar_input.selected_indices,
        )

        loo_reference = result.extra["beta_loo_theta_rad"]
        self.assertAlmostEqual(float(loo_reference[0, 1]), 2.25, places=5)
        self.assertAlmostEqual(float(loo_reference[1, 1]), 1.75, places=5)

    def test_loo_update_reference_excludes_candidates_outside_calibration_pool(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1.0,
            seed=122,
            cold_start_duration_s=1.0,
            process_noise_intensity=0.0,
            initial_state_variance=1.0e6,
            initial_rate_variance=0.0,
            initial_measurement_variance=1.0e-9,
            min_measurement_variance=1.0e-12,
            max_measurement_variance=25.0,
            beta_update_start_s=10.0,
            beta_update_reference_mode="loo_update_direct_ls",
        )
        wrapped = np.array(
            [
                [0.0, 0.5],
                [0.0, 1.5],
                [0.0, 3.0],
                [0.0, 100.0],
            ],
            dtype=float,
        )
        radar_input = SimpleNamespace(
            wrapped_phase_rad=wrapped,
            available_mask=np.array([[False, True], [False, True], [False, True], [False, True]], dtype=bool),
            selected_indices=np.array([0, 1], dtype=int),
            calibration_indices=np.array([0, 1, 2], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(wrapped.shape[1], dtype=float),
            measured_mps2=np.zeros(wrapped.shape[1], dtype=float),
            bias_mps2=np.zeros(wrapped.shape[1], dtype=float),
            noise_mps2=np.zeros(wrapped.shape[1], dtype=float),
        )

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="loo_peer_pool_filter_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=np.ones(4, dtype=float),
            update_beta=False,
            adaptive_r=False,
            adaptive_r_mode="posterior_residual",
            selected_indices=radar_input.selected_indices,
        )

        loo_reference = result.extra["beta_loo_theta_rad"]
        self.assertAlmostEqual(float(loo_reference[0, 1]), 2.25, places=5)
        self.assertAlmostEqual(float(loo_reference[1, 1]), 1.75, places=5)

    def test_loo_update_direct_ls_runs_beta_update_from_loo_reference(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=40.0,
            seed=120,
            aoa_error_deg=6.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=8,
            beta_update_reference_mode="loo_update_direct_ls",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)
        loo_reference = result.extra["beta_loo_theta_rad"]
        gate = result.extra["beta_update_gate_history"]

        self.assertEqual(result.extra["beta_update_reference_mode"], "loo_update_direct_ls")
        self.assertEqual(loo_reference.shape, radar.wrapped_phase_rad.shape)
        self.assertTrue(np.any(np.isfinite(loo_reference)))
        self.assertTrue(np.any(np.isfinite(gate)))

    def test_loo_accel_scaled_direct_ls_runs_with_anchored_loo_reference(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=40.0,
            seed=123,
            aoa_error_deg=6.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=8,
            beta_update_reference_mode="loo_accel_scaled_direct_ls",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_proposed(radar_input, accel, config)

        self.assertEqual(result.extra["beta_update_reference_mode"], "loo_accel_scaled_direct_ls")
        self.assertTrue(np.any(np.isfinite(result.extra["beta_loo_theta_rad"])))

    def test_independent_auto_freezes_when_anchor_gate_fails(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=40.0,
            seed=125,
            aoa_error_deg=6.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=8,
            beta_bootstrap_prior_weight=0.0,
            beta_update_reference_mode="independent_auto",
            beta_anchor_min_abs_corr=1.1,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)
        initial_beta = phase1_algorithm._initial_beta_from_radar(radar_input)

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="independent_auto_anchor_reject_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=initial_beta,
            update_beta=True,
            adaptive_r=False,
        )

        self.assertEqual(result.extra["beta_update_reference_mode"], "independent_auto")
        self.assertTrue(np.nanmax(result.extra["beta_update_gate_history"]) == 0.0)
        self.assertTrue(np.nanmax(result.extra["beta_anchor_gate_history"]) == 0.0)
        np.testing.assert_allclose(result.beta_hat, initial_beta)

    def test_independent_auto_updates_when_anchor_gate_passes(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=40.0,
            seed=126,
            aoa_error_deg=6.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=8,
            beta_bootstrap_prior_weight=0.0,
            beta_update_reference_mode="independent_auto",
            beta_anchor_min_abs_corr=0.1,
            beta_anchor_min_scale=0.01,
            beta_anchor_max_scale=100.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)
        initial_beta = phase1_algorithm._initial_beta_from_radar(radar_input)

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="independent_auto_anchor_accept_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=initial_beta,
            update_beta=True,
            adaptive_r=False,
        )

        self.assertEqual(result.extra["beta_update_reference_mode"], "independent_auto")
        self.assertTrue(np.nanmax(result.extra["beta_anchor_gate_history"]) > 0.0)
        self.assertGreater(float(np.nanmax(np.abs(result.beta_hat - initial_beta))), 0.0)

    def test_common_aoa_bias_direct_ls_updates_beta_from_shared_angle_error(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=40.0,
            seed=127,
            aoa_error_deg=10.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.1,
            beta_window_samples=20,
            beta_bootstrap_prior_weight=0.0,
            beta_update_reference_mode="common_aoa_bias_direct_ls",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)
        initial_beta = phase1_algorithm._initial_beta_from_radar(radar_input)

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="common_aoa_bias_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=initial_beta,
            update_beta=True,
            adaptive_r=False,
        )

        initial_error = float(np.median(np.abs(initial_beta - radar.beta) / radar.beta))
        final_error = float(np.median(np.abs(result.beta_hat - radar.beta) / radar.beta))
        self.assertEqual(result.extra["beta_update_reference_mode"], "common_aoa_bias_direct_ls")
        self.assertIn("beta_common_aoa_bias_history_deg", result.extra)
        self.assertLess(final_error, initial_error)

    def test_beta_update_does_not_rewrite_current_sample_phase_correction(self):
        config = Phase1Config(
            duration_s=0.8,
            sample_rate_hz=40.0,
            seed=124,
            aoa_error_deg=8.0,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            accel_noise_std_mps2=0.0,
            beta_update_start_s=0.2,
            beta_window_samples=8,
            beta_bootstrap_prior_weight=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)
        initial_beta = phase1_algorithm._initial_beta_from_radar(radar_input)

        without_update = phase1_algorithm.run_structural_phase_kalman(
            method_name="phase_correction_without_beta_update",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=initial_beta,
            update_beta=False,
            adaptive_r=False,
        )
        with_update = phase1_algorithm.run_structural_phase_kalman(
            method_name="phase_correction_with_beta_update",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=initial_beta,
            update_beta=True,
            adaptive_r=False,
        )

        first_update_idx = int(round(config.beta_update_start_s * config.sample_rate_hz))
        np.testing.assert_allclose(
            with_update.los_corrected_phase_rad[:, first_update_idx],
            without_update.los_corrected_phase_rad[:, first_update_idx],
        )
        self.assertGreater(
            np.nanmax(np.abs(with_update.extra["beta_history"] - without_update.extra["beta_history"])),
            0.0,
        )

    def test_beta_update_gate_freezes_uninformative_windows(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=10.0,
            cold_start_duration_s=0.1,
            process_noise_intensity=0.0,
            initial_state_variance=1.0,
            initial_rate_variance=0.0,
            initial_measurement_variance=1.0e-4,
            min_measurement_variance=1.0e-9,
            beta_update_start_s=0.0,
            beta_window_samples=4,
            beta_bootstrap_prior_weight=0.0,
        )
        wrapped = np.array([[0.0, 0.004, -0.003, 0.005, -0.002, 0.003, -0.004, 0.002, -0.003, 0.004]])
        radar_input = SimpleNamespace(
            wrapped_phase_rad=wrapped,
            available_mask=np.ones_like(wrapped, dtype=bool),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(wrapped.shape[1], dtype=float),
            measured_mps2=np.zeros(wrapped.shape[1], dtype=float),
            bias_mps2=np.zeros(wrapped.shape[1], dtype=float),
            noise_mps2=np.zeros(wrapped.shape[1], dtype=float),
        )

        result = phase1_algorithm.run_structural_phase_kalman(
            method_name="beta_gate_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=np.array([2.0], dtype=float),
            update_beta=True,
            adaptive_r=False,
            adaptive_r_mode="posterior_residual",
        )

        gate = result.extra["beta_update_gate_history"][0]
        finite_gate = gate[np.isfinite(gate)]
        self.assertGreater(finite_gate.size, 0)
        self.assertTrue(np.all(finite_gate == 0.0))
        np.testing.assert_allclose(result.beta_hat, np.array([2.0], dtype=float))

    def test_beta_confidence_variance_decays_after_stable_projection_bootstrap(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "aoa_error_bootstrap"][0]
        config = replace(
            scenario,
            target_snr_db=(45.0, 45.0, 45.0, 45.0, 45.0),
            beta_update_start_s=0.1,
            beta_window_samples=60,
            beta_bootstrap_prior_weight=0.0,
            beta_confidence_initial_variance=0.04,
            beta_update_reference_mode="posterior",
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        result = estimate_proposed_full_pipeline_beta_confidence(to_algorithm_radar_input(radar), accel, config)
        variance = result.extra["beta_variance_history"][0]
        finite = variance[np.isfinite(variance)]

        self.assertGreater(finite.size, 10)
        self.assertLess(float(finite[-1]), float(finite[0]))

    def test_quality_gated_r_suppresses_growth_for_high_quality_target(self):
        result = self._quality_gated_r_probe(selection_score=1.0)

        self.assertIn("base_r_update_gate_history", result.extra)
        self.assertIn("target_quality_history", result.extra)
        base_r = result.extra["base_r_theta_history"][0]
        gate = result.extra["base_r_update_gate_history"][0]
        quality = result.extra["target_quality_history"][0]

        self.assertEqual(result.extra["adaptive_r_mode"], "beta_confidence")
        self.assertAlmostEqual(quality[1], 1.0)
        self.assertAlmostEqual(gate[1], 0.0)
        self.assertLess(np.nanmax(base_r[2:]), 0.02)

    def test_quality_gated_r_allows_growth_for_low_quality_target(self):
        result = self._quality_gated_r_probe(selection_score=0.0)

        self.assertIn("base_r_update_gate_history", result.extra)
        self.assertIn("target_quality_history", result.extra)
        base_r = result.extra["base_r_theta_history"][0]
        gate = result.extra["base_r_update_gate_history"][0]
        quality = result.extra["target_quality_history"][0]

        self.assertAlmostEqual(quality[1], 0.0)
        self.assertAlmostEqual(gate[1], 1.0)
        self.assertGreater(base_r[2], 0.1)

    def _quality_gated_r_probe(self, selection_score):
        config = Phase1Config(
            duration_s=0.4,
            sample_rate_hz=10.0,
            seed=130,
            cold_start_duration_s=0.1,
            process_noise_intensity=0.0,
            initial_state_variance=0.01,
            initial_rate_variance=0.0,
            initial_measurement_variance=0.01,
            min_measurement_variance=1.0e-6,
            max_measurement_variance=25.0,
            adaptive_r_forgetting=0.5,
            beta_confidence_initial_variance=1.0e-6,
            beta_confidence_min_variance=1.0e-6,
            beta_confidence_max_variance=1.0e-6,
            beta_update_start_s=10.0,
        )
        wrapped_phase = np.array([[0.0, 1.0, 1.0, 1.0]], dtype=float)
        radar_input = RadarAlgorithmInput(
            measured_beta=np.array([1.0], dtype=float),
            wrapped_phase_rad=wrapped_phase,
            available_mask=np.ones_like(wrapped_phase, dtype=bool),
            selected_indices=np.array([0], dtype=int),
            initial_r=np.array([0.01], dtype=float),
            selection_scores=np.array([selection_score], dtype=float),
        )
        accel = AccelerometerObservation(
            true_mps2=np.zeros(wrapped_phase.shape[1], dtype=float),
            measured_mps2=np.zeros(wrapped_phase.shape[1], dtype=float),
            bias_mps2=np.zeros(wrapped_phase.shape[1], dtype=float),
            noise_mps2=np.zeros(wrapped_phase.shape[1], dtype=float),
        )
        return phase1_algorithm.run_structural_phase_kalman(
            method_name="quality_gated_r_probe",
            radar=radar_input,
            accel=accel,
            config=config,
            initial_beta=radar_input.measured_beta.copy(),
            update_beta=False,
            adaptive_r=True,
            selected_indices=radar_input.selected_indices,
            initial_r=radar_input.initial_r,
            adaptive_r_mode="beta_confidence",
        )


class Phase1SingleTargetBaselineTest(unittest.TestCase):
    def test_single_target_ma_style_uses_one_target_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=121, accel_noise_std_mps2=0.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)

        result = estimate_single_target_ma_style(truth, radar, accel, config, target_index=0)

        self.assertEqual(result.method_name, "single_target_ma_style")
        used_targets = np.flatnonzero(np.any(np.isfinite(result.los_corrected_phase_rad), axis=1))
        np.testing.assert_array_equal(used_targets, np.array([0]))


if __name__ == "__main__":
    unittest.main()
