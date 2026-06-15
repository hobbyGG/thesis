import unittest

import numpy as np

from simulation.phase1.metrics import (
    FeasibilityGate,
    convergence_time_s,
    displacement_metrics,
    evaluate_gate,
    interval_mask,
)


class Phase1MetricsTest(unittest.TestCase):
    def test_displacement_metrics_are_reported_in_mm(self):
        truth = np.array([0.0, 0.001, 0.002])
        estimate = np.array([0.0, 0.0015, 0.001])

        metrics = displacement_metrics(estimate, truth)

        self.assertAlmostEqual(metrics["rmse_mm"], 0.6454972243679028)
        self.assertAlmostEqual(metrics["mae_mm"], 0.5)
        self.assertAlmostEqual(metrics["max_error_mm"], 1.0)

    def test_interval_mask_selects_closed_time_window(self):
        t = np.array([0.0, 0.5, 1.0, 1.5])
        mask = interval_mask(t, 0.5, 1.0)

        np.testing.assert_array_equal(mask, np.array([False, True, True, False]))

    def test_convergence_time_returns_first_sustained_time(self):
        t = np.arange(6, dtype=float)
        estimate = np.array([0.6, 0.4, 0.2, 0.04, 0.03, 0.02])
        truth = np.ones_like(estimate)

        self.assertEqual(convergence_time_s(t, estimate, truth, relative_tol=0.05, sustain_samples=2), 3.0)

    def test_feasibility_gate_passes_when_value_is_below_threshold(self):
        gate = FeasibilityGate(name="nominal_rmse", metric="rmse_mm", max_value=0.03)

        self.assertTrue(evaluate_gate({"rmse_mm": 0.02}, gate)["passed"])
        self.assertFalse(evaluate_gate({"rmse_mm": 0.04}, gate)["passed"])


if __name__ == "__main__":
    unittest.main()
