import math
import unittest

import numpy as np

from simulation.phase1.accelerometer import simulate_accelerometer
from simulation.phase1.config import Phase1Config
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.truth import generate_component_frequencies, generate_multifrequency_truth


class Phase1SimulationTest(unittest.TestCase):
    def test_component_frequencies_are_seeded_near_nominal_values(self):
        freqs_a = generate_component_frequencies([20.0, 40.0, 60.0], jitter_hz=10.0, seed=7)
        freqs_b = generate_component_frequencies([20.0, 40.0, 60.0], jitter_hz=10.0, seed=7)

        self.assertEqual(freqs_a, freqs_b)
        self.assertEqual(len(freqs_a), 3)

        for freq, nominal in zip(freqs_a, [20.0, 40.0, 60.0]):
            self.assertGreaterEqual(freq, nominal - 10.0)
            self.assertLessEqual(freq, nominal + 10.0)
            self.assertAlmostEqual(freq, round(freq, 2))

    def test_multifrequency_truth_has_consistent_analytic_derivatives(self):
        config = Phase1Config(duration_s=2.0, sample_rate_hz=1000.0, seed=11)
        truth = generate_multifrequency_truth(config)

        self.assertEqual(truth.t.shape, truth.q_m.shape)
        self.assertEqual(truth.t.shape, truth.v_mps.shape)
        self.assertEqual(truth.t.shape, truth.a_mps2.shape)
        self.assertEqual(len(truth.frequencies_hz), 3)

        reconstructed_acc = np.zeros_like(truth.t)
        for amp_m, freq_hz, phase_rad in zip(
            truth.amplitudes_m, truth.frequencies_hz, truth.phases_rad
        ):
            omega = 2.0 * math.pi * freq_hz
            reconstructed_acc += -amp_m * omega**2 * np.sin(omega * truth.t + phase_rad)

        np.testing.assert_allclose(truth.a_mps2, reconstructed_acc, rtol=0.0, atol=1e-12)

    def test_radar_targets_return_wrapped_phase_and_are_reproducible(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=21)
        truth = generate_multifrequency_truth(config)

        radar_a = simulate_radar_targets(truth, config)
        radar_b = simulate_radar_targets(truth, config)

        self.assertEqual(radar_a.wrapped_phase_rad.shape, (config.num_targets, truth.t.size))
        self.assertEqual(radar_a.true_los_phase_rad.shape, (config.num_targets, truth.t.size))
        self.assertEqual(radar_a.iq.shape, (config.num_targets, truth.t.size))
        self.assertTrue(np.all(radar_a.wrapped_phase_rad > -math.pi))
        self.assertTrue(np.all(radar_a.wrapped_phase_rad <= math.pi))
        np.testing.assert_allclose(radar_a.wrapped_phase_rad, radar_b.wrapped_phase_rad)

    def test_accelerometer_noise_is_seeded_and_bias_is_applied(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=31,
            accel_noise_std_mps2=0.02,
            accel_bias_mps2=0.05,
            accel_drift_mps2=0.01,
        )
        truth = generate_multifrequency_truth(config)

        accel_a = simulate_accelerometer(truth, config)
        accel_b = simulate_accelerometer(truth, config)

        self.assertEqual(accel_a.measured_mps2.shape, truth.a_mps2.shape)
        np.testing.assert_allclose(accel_a.measured_mps2, accel_b.measured_mps2)
        self.assertGreater(abs(np.mean(accel_a.measured_mps2 - truth.a_mps2)), 0.01)

    def test_radar_target_degradation_reduces_iq_quality_inside_window(self):
        config = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=1000.0,
            seed=41,
            degraded_target_indices=(0,),
            degradation_start_s=1.0,
            degradation_end_s=2.0,
            degradation_snr_drop_db=30.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        in_window = (truth.t >= 1.0) & (truth.t <= 2.0)
        out_window = truth.t < 0.8
        clean = np.exp(1j * radar.true_los_phase_rad[0])
        err_in = np.mean(np.abs(radar.iq[0, in_window] - clean[in_window]) ** 2)
        err_out = np.mean(np.abs(radar.iq[0, out_window] - clean[out_window]) ** 2)

        self.assertGreater(err_in, err_out * 5.0)

    def test_radar_target_dropout_marks_phase_as_nan_inside_window(self):
        config = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=1000.0,
            seed=42,
            dropout_target_indices=(1,),
            dropout_start_s=1.0,
            dropout_end_s=2.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        in_window = (truth.t >= 1.0) & (truth.t <= 2.0)
        out_window = truth.t < 0.8

        self.assertTrue(np.all(np.isnan(radar.wrapped_phase_rad[1, in_window])))
        self.assertFalse(np.any(np.isnan(radar.wrapped_phase_rad[1, out_window])))

    def test_aoa_error_changes_measured_kappa_but_not_true_kappa(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=43, aoa_error_deg=8.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        expected_measured = np.cos(np.deg2rad(radar.target_angles_deg + 8.0))
        np.testing.assert_allclose(radar.measured_kappa, expected_measured)
        self.assertGreater(np.max(np.abs(radar.measured_kappa - radar.kappa)), 1e-3)


class Phase1ConfigExtensionTest(unittest.TestCase):
    def test_default_kalman_and_bootstrap_config_values_are_available(self):
        config = Phase1Config()

        self.assertGreater(config.process_noise_intensity, 0.0)
        self.assertGreater(config.initial_state_variance, 0.0)
        self.assertGreater(config.initial_rate_variance, 0.0)
        self.assertGreater(config.initial_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.max_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.kappa_window_samples, 2)
        self.assertGreater(config.kappa_update_start_s, 0.0)
        self.assertGreater(config.adaptive_r_forgetting, 0.0)
        self.assertLess(config.adaptive_r_forgetting, 1.0)

    def test_default_scenario_controls_are_available(self):
        config = Phase1Config()

        self.assertEqual(config.scenario_name, "nominal_multifrequency")
        self.assertEqual(config.aoa_error_deg, 0.0)
        self.assertEqual(config.degraded_target_indices, ())
        self.assertEqual(config.dropout_target_indices, ())
        self.assertFalse(config.enable_mixed_scatterer_target)


if __name__ == "__main__":
    unittest.main()
