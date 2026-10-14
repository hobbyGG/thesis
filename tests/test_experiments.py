"""The experiment code path equals the retained algorithm, and its statistics are sound."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from experiments import stats
from experiments.front import apply_dropout, compute_front, load_front
from experiments.methods import (
    METHODS, Tuned, acceleration_input, kalman, phase_observer, prepare_radar, run_methods,
)
from paper_bridge_simulation import package_builder
from paper_bridge_simulation.ensemble import draw_case
from paper_bridge_simulation.scenario import Impairments, Scenario
from system.algorithm.acceleration import RadarIntervalPreintegration
from system.algorithm.config import AlgorithmConfig
from system.algorithm.run import displacement_error_m, run
from system.algorithm.types import AccelerationInput


class ExperimentPathTest(unittest.TestCase):
    def test_experiment_path_equals_the_official_run_with_and_without_cache(self):
        scenario, impairments = draw_case(1000)
        with tempfile.TemporaryDirectory(prefix="experiment-path-") as temporary:
            temporary = Path(temporary)
            package = package_builder.generate(
                temporary / "package", duration_s=1.0, seed=1000, impairments=impairments, scenario=scenario)
            official = np.load(run(package, temporary / "result.npz")[0])["q_hat_m"]
            cache = temporary / "cache"
            written = load_front(scenario, impairments, 1000, 1.0, cache)
            read_back = load_front(scenario, impairments, 1000, 1.0, cache)
            uncached = load_front(scenario, impairments, 1000, 1.0, None)
            self.assertEqual(len(list(cache.glob("front_*.npz"))), 1)
            for front in (read_back, uncached):
                np.testing.assert_array_equal(front.targets.slow_time, written.targets.slow_time)
                np.testing.assert_array_equal(front.truth_m, written.truth_m)
                np.testing.assert_array_equal(front.radar_time_ns, written.radar_time_ns)
                self.assertEqual(front.detection, written.detection)
            side = prepare_radar(read_back)
            acceleration = acceleration_input(side, package_builder.adxl_samples(scenario, impairments, 1000, 1.0))
            estimate = kalman(side.radar, acceleration, side.config, AlgorithmConfig().process_noise_intensity)
        np.testing.assert_allclose(estimate, official, rtol=0.0, atol=1.0e-12)

    def test_posthoc_dropout_equals_dropped_adc_frames(self):
        scenario = Scenario()
        official = compute_front(scenario, Impairments(radar_dropout_s=0.02, radar_dropout_start_s=0.3), 7, 1.0)
        posthoc = apply_dropout(compute_front(scenario, Impairments(), 7, 1.0), 0.3, 0.02)
        np.testing.assert_array_equal(official.targets.available_mask, posthoc.targets.available_mask)
        np.testing.assert_array_equal(official.targets.slow_time, posthoc.targets.slow_time)
        self.assertEqual(int(np.count_nonzero(~official.targets.available_mask[0])), 10)
        np.testing.assert_array_equal(
            prepare_radar(official).radar.wrapped_phase_rad, prepare_radar(posthoc).radar.wrapped_phase_rad)

    def test_iq_offset_is_a_constant_term_of_the_stated_size(self):
        scenario = Scenario()
        base = compute_front(scenario, Impairments(), 11, 1.0)
        offset = compute_front(scenario, Impairments(iq_offset_ratio=0.5), 11, 1.0)
        cell = (base.targets.range_bins[0], base.targets.angle_bins[0])
        index = [(r, a) for r, a in zip(offset.targets.range_bins, offset.targets.angle_bins)].index(cell)
        difference = offset.targets.slow_time[index] - base.targets.slow_time[0]
        self.assertAlmostEqual(
            abs(np.mean(difference)) / np.mean(np.abs(base.targets.slow_time[0])), 0.5, delta=0.1)
        self.assertLess(np.std(difference) / abs(np.mean(difference)), 0.05)

    def test_all_methods_score_a_nominal_record(self):
        scenario, impairments = Scenario(), Impairments()
        side = prepare_radar(compute_front(scenario, impairments, 21, 2.0))
        metrics = run_methods(side, package_builder.adxl_samples(scenario, impairments, 21, 2.0), scenario, Tuned())
        self.assertEqual(set(metrics), set(METHODS))
        self.assertFalse(metrics["fusion"]["failed"])
        self.assertLess(metrics["fusion"]["event_rmse_um"], 100.0)
        self.assertGreater(metrics["adxl-raw"]["event_rmse_um"], 10.0 * metrics["fusion"]["event_rmse_um"])

    def test_error_is_referenced_on_both_sides_to_the_cold_start_window(self):
        time_s = np.arange(500) * 2.0e-3
        truth = 1.0e-3 * np.sin(time_s)
        np.testing.assert_allclose(displacement_error_m(truth + 5.0e-3, truth, time_s, 0.2), 0.0, atol=1.0e-15)


class PhaseObserverTest(unittest.TestCase):
    def setUp(self):
        self.frames, self.dt = 1500, 2.0e-3
        t = np.arange(self.frames) * self.dt
        self.omega, self.amplitude = 2.0 * np.pi * 3.0, 1.0e-3
        # Starts at rest, so the observer needs no velocity initialisation.
        self.q = self.amplitude * (1.0 - np.cos(self.omega * t))
        self.v = self.amplitude * self.omega * np.sin(self.omega * t)
        self.config = AlgorithmConfig(sample_rate_hz=500.0)
        self.scale = 4.0 * np.pi / self.config.wavelength_m()

    def acceleration(self, exact: bool) -> AccelerationInput:
        duration = np.full(self.frames - 1, self.dt)
        delta_v = np.diff(self.v) if exact else np.zeros(self.frames - 1)
        delta_q = np.diff(self.q) - self.v[:-1] * self.dt if exact else np.zeros(self.frames - 1)
        return AccelerationInput(
            np.arange(self.frames), np.zeros(self.frames), RadarIntervalPreintegration(duration, delta_v, delta_q))

    def test_consistent_radar_and_adxl_are_tracked_exactly(self):
        estimate = phase_observer(
            self.scale * self.q, self.acceleration(True), self.config, 2.0, start_at_measurement=True)
        self.assertLess(float(np.max(np.abs(estimate - self.q))), 1.0e-3 * self.amplitude)

    def test_without_adxl_the_observer_is_a_tracking_loop_with_the_expected_lag_error(self):
        # Error of a critically damped type-2 loop for a sinusoid of angular
        # frequency w at corner w_c: r^2 / |1 - r^2 + j sqrt(2) r|, r = w / w_c.
        r = 3.0 / 16.0
        expected = r**2 / abs(1.0 - r**2 + 1j * np.sqrt(2.0) * r)
        estimate = phase_observer(
            self.scale * self.q, self.acceleration(False), self.config, 16.0, start_at_measurement=True)
        error = float(np.max(np.abs(estimate - self.q)[500:])) / self.amplitude
        # Euler discretisation at w_c*dt = 0.2 moves the loop a few tens of percent.
        self.assertGreater(error, 0.6 * expected)
        self.assertLess(error, 1.6 * expected)

    def test_a_missing_measurement_skips_the_correction(self):
        theta = self.scale * self.q
        theta[300:400] = np.nan
        estimate = phase_observer(theta, self.acceleration(True), self.config, 2.0, start_at_measurement=True)
        self.assertTrue(np.all(np.isfinite(estimate)))
        self.assertLess(float(np.max(np.abs(estimate - self.q))), 1.0e-3 * self.amplitude)


class StatisticsTest(unittest.TestCase):
    def test_sign_flip_is_exact_for_small_samples_and_monte_carlo_for_large(self):
        self.assertAlmostEqual(stats.sign_flip_p([1, 2, 3, 4, 5]), 2.0 / 32.0)
        self.assertEqual(stats.sign_flip_p([1, -1, 2, -2]), 1.0)
        self.assertLess(stats.sign_flip_p(np.ones(20)), 1.0e-3)

    def test_wilson_interval(self):
        low, high = stats.wilson_interval(0, 10)
        self.assertAlmostEqual(low, 0.0, places=12)
        self.assertAlmostEqual(high, 0.2775, places=3)
        self.assertEqual(stats.wilson_interval(0, 0), (0.0, 1.0))

    def test_paired_gain_and_clipping(self):
        result = stats.paired_gain([10.0] * 8, [20.0] * 8)
        self.assertAlmostEqual(result["gain"], 0.5)
        self.assertAlmostEqual(result["gain_low"], 0.5)
        self.assertAlmostEqual(result["p"], 2.0 / 256.0)
        np.testing.assert_array_equal(stats.clipped([np.nan, 1.0e9, 0.0]), [stats.CAP_UM, stats.CAP_UM, stats.FLOOR_UM])


if __name__ == "__main__":
    unittest.main()
