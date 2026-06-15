import math
import unittest

import numpy as np

from simulation.phase1.phase_utils import (
    count_branch_errors,
    itoh_unwrap,
    prediction_correct_wrapped_phase,
    wrap_to_pi,
)


class PhaseUtilsTest(unittest.TestCase):
    def test_wrap_to_pi_returns_open_left_closed_right_interval(self):
        values = np.array([-3.0 * math.pi, -math.pi, -0.1, 0.0, math.pi, 3.0 * math.pi])
        wrapped = wrap_to_pi(values)

        self.assertTrue(np.all(wrapped > -math.pi))
        self.assertTrue(np.all(wrapped <= math.pi))
        self.assertAlmostEqual(wrapped[1], math.pi)
        self.assertAlmostEqual(wrapped[4], math.pi)

    def test_prediction_correct_wrapped_phase_selects_nearest_branch(self):
        true_phase = 5.8
        wrapped = wrap_to_pi(true_phase)
        corrected = prediction_correct_wrapped_phase(wrapped, prediction=6.0)

        self.assertAlmostEqual(float(corrected), true_phase, places=12)

    def test_itoh_unwrap_recovers_slow_phase_but_not_large_jump(self):
        slow = np.array([0.1, 0.4, 0.7, 1.0])
        np.testing.assert_allclose(itoh_unwrap(wrap_to_pi(slow)), slow)

        large = np.array([0.1, 3.8])
        unwrapped = itoh_unwrap(wrap_to_pi(large))
        self.assertGreater(abs(unwrapped[-1] - large[-1]), math.pi)

    def test_count_branch_errors_counts_two_pi_branch_mismatches(self):
        truth = np.array([0.0, 2.0 * math.pi + 0.1, 4.0 * math.pi + 0.2])
        estimate = np.array([0.0, 0.1, 4.0 * math.pi + 0.2])

        self.assertEqual(count_branch_errors(estimate, truth), 1)


if __name__ == "__main__":
    unittest.main()
