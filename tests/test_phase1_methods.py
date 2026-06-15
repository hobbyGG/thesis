import unittest

import numpy as np

from simulation.phase1.config import Phase1Config
from simulation.phase1.methods import (
    estimate_itoh_ls,
    estimate_multitarget_fixed,
    estimate_oracle,
    estimate_proposed,
    estimate_single_target_ma_style,
)
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.truth import generate_multifrequency_truth


class Phase1MethodsTest(unittest.TestCase):
    def test_oracle_recovers_truth_from_true_main_phase(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=101)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_oracle(truth, radar, config)

        np.testing.assert_allclose(result.q_hat_m, truth.q_m, atol=1e-15)
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
        rmse_mm = np.sqrt(np.mean((result.q_hat_m - truth.q_m) ** 2)) * 1e3

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

        result = estimate_multitarget_fixed(truth, radar, config)
        rmse_mm = np.sqrt(np.mean((result.q_hat_m - truth.q_m) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.01)

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

        result = estimate_proposed(truth, radar, config)
        initial_error = np.median(np.abs(radar.measured_kappa - radar.kappa))
        final_error = np.median(np.abs(result.kappa_hat - radar.kappa))

        self.assertLess(final_error, initial_error)


class Phase1SingleTargetBaselineTest(unittest.TestCase):
    def test_single_target_ma_style_uses_one_target_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=121, accel_noise_std_mps2=0.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_single_target_ma_style(truth, radar, config, target_index=0)

        self.assertEqual(result.method_name, "single_target_ma_style")
        used_targets = np.flatnonzero(np.any(np.isfinite(result.corrected_phase_rad), axis=1))
        np.testing.assert_array_equal(used_targets, np.array([0]))


if __name__ == "__main__":
    unittest.main()
