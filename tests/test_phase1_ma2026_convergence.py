import math
import unittest

import numpy as np

from simulation.phase1.ma2026.convergence import compute_ma2026_convergence_time


class Ma2026ConvergenceTests(unittest.TestCase):
    def test_ma2026_convergence_outputs_shapes_and_positive_time(self):
        result = compute_ma2026_convergence_time(
            sample_rate_hz=100.0,
            wavelength_m=0.0039,
            alpha=1.0,
            q_value=1.0,
            max_steps=600,
        )

        self.assertEqual(result.steady_state_gain.shape, (2,))
        self.assertEqual(result.measurement_coefficients.shape, (600, 2))
        self.assertEqual(result.acceleration_coefficients.shape, (600, 2))
        self.assertGreater(result.convergence_steps, 0)
        self.assertGreater(result.convergence_time_s, 0.0)
        self.assertEqual(result.threshold, 1e-3)
        self.assertTrue(math.isclose(result.convergence_time_s, result.convergence_steps / 100.0))
        self.assertTrue(np.all(np.isfinite(result.measurement_coefficients)))
        self.assertTrue(np.all(np.isfinite(result.acceleration_coefficients)))

    def test_ma2026_convergence_steps_are_stable_when_max_steps_increases(self):
        short = compute_ma2026_convergence_time(
            sample_rate_hz=100.0,
            wavelength_m=0.0039,
            alpha=1.0,
            q_value=1.0,
            max_steps=2000,
        )
        long = compute_ma2026_convergence_time(
            sample_rate_hz=100.0,
            wavelength_m=0.0039,
            alpha=1.0,
            q_value=1.0,
            max_steps=4000,
        )

        self.assertLess(short.convergence_steps, 2000)
        self.assertEqual(long.convergence_steps, short.convergence_steps)
        self.assertTrue(math.isclose(long.convergence_time_s, short.convergence_time_s))
        np.testing.assert_allclose(long.steady_state_gain, short.steady_state_gain)
        np.testing.assert_allclose(long.measurement_coefficients[:2000], short.measurement_coefficients)
        np.testing.assert_allclose(long.acceleration_coefficients[:2000], short.acceleration_coefficients)

    def test_ma2026_acceleration_coefficients_shrink_with_larger_alpha(self):
        alpha_one = compute_ma2026_convergence_time(
            sample_rate_hz=100.0,
            wavelength_m=0.0039,
            alpha=1.0,
            q_value=1.0,
            max_steps=600,
        )
        alpha_two = compute_ma2026_convergence_time(
            sample_rate_hz=100.0,
            wavelength_m=0.0039,
            alpha=2.0,
            q_value=1.0,
            max_steps=600,
        )

        norm_one = np.linalg.norm(alpha_one.acceleration_coefficients[0])
        norm_two = np.linalg.norm(alpha_two.acceleration_coefficients[0])
        self.assertLess(norm_two, norm_one)
        self.assertTrue(math.isclose(norm_two, norm_one / 2.0))
