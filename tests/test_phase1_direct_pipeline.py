import unittest

import numpy as np

from simulation.phase1.algorithm import estimate_direct_aoa_fixed_beta
from simulation.phase1.accelerometer import simulate_accelerometer
from simulation.phase1.config import Phase1Config
from simulation.phase1.radar import simulate_radar_targets, to_algorithm_radar_input
from simulation.phase1.truth import generate_multifrequency_truth


class DirectAoAPipelineTest(unittest.TestCase):
    def test_direct_entrypoint_freezes_frontend_beta_without_feedback(self):
        config = Phase1Config(
            duration_s=0.8,
            sample_rate_hz=100.0,
            seed=710,
            aoa_error_deg=8.0,
            target_snr_db=(60.0,) * 5,
            accel_noise_std_mps2=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        accel = simulate_accelerometer(truth, config)

        result = estimate_direct_aoa_fixed_beta(radar_input, accel, config)

        self.assertEqual(result.method_name, "direct_aoa_fixed_beta")
        self.assertFalse(result.extra["beta_update_enabled"])
        self.assertEqual(result.extra["beta_source"], "frontend_direct_aoa")
        np.testing.assert_allclose(result.beta_hat, radar.measured_beta)
        history = np.asarray(result.extra["beta_history"], dtype=float)
        self.assertEqual(history.shape, radar.wrapped_phase_rad.shape)
        np.testing.assert_allclose(history, np.repeat(radar.measured_beta[:, None], history.shape[1], axis=1))

    def test_direct_entrypoint_does_not_require_truth_fields(self):
        config = Phase1Config(duration_s=0.25, sample_rate_hz=80.0, seed=711)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        accel = simulate_accelerometer(truth, config)
        radar_input = to_algorithm_radar_input(radar)
        self.assertFalse(hasattr(radar_input, "beta"))
        self.assertFalse(hasattr(radar_input, "true_main_phase_rad"))
        result = estimate_direct_aoa_fixed_beta(radar_input, accel, config)
        self.assertEqual(result.q_hat_m.shape, truth.q_m.shape)


if __name__ == "__main__":
    unittest.main()
