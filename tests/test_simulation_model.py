"""Calibration of the simulator's knobs and the randomised scenario ensemble.

Each test states the physical meaning of a parameter and checks that the
generated data realises it, so a sweep over that parameter measures what its
label says.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from experiments.front import compute_front
from paper_bridge_simulation import package_builder
from paper_bridge_simulation.ensemble import (
    MAX_TARGET_RANGE_M, MIN_ANGLE_SEPARATION_DEG, MIN_RANGE_SEPARATION_BINS, draw_case,
)
from paper_bridge_simulation.response import simulate_response
from paper_bridge_simulation.scenario import Impairments, Scenario


def phase_noise_rad(front) -> float:
    """Median over targets of the white phase-noise std (second-difference estimator)."""
    spread = []
    for series in front.targets.slow_time:
        second_difference = np.diff(np.unwrap(np.angle(series)), n=2)
        spread.append(np.std(second_difference) / np.sqrt(6.0))
    return float(np.median(spread))


class SimulatorCalibrationTest(unittest.TestCase):
    def test_scenario_defaults_are_the_nominal_response_and_scene(self):
        nominal = simulate_response(1.0)
        parameterised = simulate_response(1.0, **Scenario().response_kwargs())
        for expected, actual in zip(nominal, parameterised):
            np.testing.assert_array_equal(expected, actual)
        np.testing.assert_array_equal(Scenario().target_ranges_m(), package_builder.TARGET_RANGES_M)

    def test_ambient_forcing_has_the_requested_rms_and_is_seeded(self):
        base = simulate_response(1.0)
        ambient = simulate_response(1.0, ambient_acceleration_rms_mps2=2.0e-3, ambient_seed=7)
        again = simulate_response(1.0, ambient_acceleration_rms_mps2=2.0e-3, ambient_seed=7)
        other = simulate_response(1.0, ambient_acceleration_rms_mps2=2.0e-3, ambient_seed=8)
        added = ambient[2] - base[2]
        self.assertAlmostEqual(float(np.std(added)), 2.0e-3, delta=1.0e-4)
        np.testing.assert_array_equal(ambient[2], again[2])
        self.assertFalse(np.array_equal(ambient[2], other[2]))
        # Displacement and acceleration come from the same forcing.
        self.assertGreater(float(np.std(ambient[1] - base[1])), 0.0)

    def test_snr_offset_scales_the_target_phase_noise(self):
        # The per-target SNR is that of the scattering coefficient, so the
        # phase noise of a motionless scene follows 10**(-SNR/20); thermal and
        # quantisation noise are negligible against it in the DBF output.
        still = Scenario(peak_deflection_m=1.0e-9, dynamic_acceleration_peak_mps2=1.0e-9)
        nominal = phase_noise_rad(compute_front(still, Impairments(), 2026, 1.0))
        weaker = phase_noise_rad(compute_front(still, Impairments(snr_offset_db=-10.0), 2026, 1.0))
        self.assertAlmostEqual(weaker / nominal, 10.0 ** 0.5, delta=0.35)

    def test_bias_walk_variance_grows_linearly_with_time(self):
        scene, intensity = Scenario(), 0.01
        endpoints = []
        for seed in range(300):
            walk = package_builder.adxl_samples(
                scene, Impairments(adxl_bias_walk_mps2_per_sqrt_s=intensity), seed, 4.0).values[:, 0]
            plain = package_builder.adxl_samples(scene, Impairments(), seed, 4.0).values[:, 0]
            endpoints.append((walk - plain)[[499, 999]])
        variance = np.var(np.asarray(endpoints), axis=0)
        np.testing.assert_allclose(variance, intensity**2 * np.array([1.0, 2.0]), rtol=0.25)

    def test_timestamp_jitter_and_offset_act_on_the_published_times_only(self):
        scene = Scenario()
        plain = package_builder.adxl_samples(scene, Impairments(), 3, 4.0)
        jittered = package_builder.adxl_samples(
            scene, Impairments(adxl_timestamp_jitter_std_s=100.0e-6, adxl_timestamp_offset_s=1.0e-3), 3, 4.0)
        np.testing.assert_array_equal(plain.drdy_ns, jittered.drdy_ns)
        np.testing.assert_array_equal(plain.values, jittered.values)
        deviation = (jittered.estimated_ns - plain.estimated_ns) * 1.0e-9 - 1.0e-3
        self.assertAlmostEqual(float(np.std(deviation)), 100.0e-6, delta=10.0e-6)

    def test_clock_phase_and_odr_error_move_sampling_instants_and_timestamps_together(self):
        scene = Scenario()
        plain = package_builder.adxl_samples(scene, Impairments(), 3, 4.0)
        shifted = package_builder.adxl_samples(
            scene, Impairments(adxl_clock_phase_s=1.0e-3, adxl_odr_error=0.002), 3, 4.0)
        self.assertEqual(shifted.drdy_ns[0] - plain.drdy_ns[0], 1_000_000)
        period = np.mean(np.diff(shifted.drdy_ns))
        self.assertAlmostEqual(period / np.mean(np.diff(plain.drdy_ns)), 1.002, places=5)
        np.testing.assert_array_equal(
            shifted.drdy_ns - shifted.estimated_ns, np.full(shifted.drdy_ns.shape, package_builder.ADXL_GROUP_DELAY_NS))

    def test_scale_error_and_tilt_follow_their_definitions(self):
        scene = Scenario()
        quiet = {"adxl_noise_scale": 0.0, "adxl_scale_error": 0.0}
        plain = package_builder.adxl_samples(scene, Impairments(**quiet), 5, 4.0)
        scaled = package_builder.adxl_samples(scene, Impairments(adxl_noise_scale=0.0, adxl_scale_error=0.02), 5, 4.0)
        tilted = package_builder.adxl_samples(scene, Impairments(**quiet, adxl_tilt_gain_mps2_per_m=2.0), 5, 4.0)
        reference_time, displacement, acceleration = package_builder.structural_response(scene, 4.0)
        content_s = (plain.drdy_ns - package_builder.BASE_TIME_NS) * 1.0e-9 - package_builder.ADXL_GROUP_DELAY_S
        sensed = np.interp(content_s, reference_time, acceleration)
        np.testing.assert_allclose(scaled.values[:, 0] - plain.values[:, 0], 0.02 * sensed, atol=1.0e-12)
        np.testing.assert_allclose(
            tilted.values[:, 0] - plain.values[:, 0], 2.0 * np.interp(content_s, reference_time, displacement), atol=1.0e-12)

    def test_sway_is_stationary_low_pass_motion_of_the_chosen_targets_only(self):
        sway = package_builder.sway_series(1, 200_000, 5, 30.0e-6, 0.5, (0, 4))
        np.testing.assert_array_equal(sway[:, 1:4], 0.0)
        self.assertEqual(float(sway[0].max()), 0.0)
        np.testing.assert_allclose(np.std(sway[:, [0, 4]], axis=0), 30.0e-6, rtol=0.1)
        # Low-pass: lag-1 correlation is rho = exp(-2*pi*f/fs).
        rho = np.exp(-2.0 * np.pi * 0.5 / package_builder.RADAR_RATE_HZ)
        self.assertAlmostEqual(float(np.corrcoef(sway[:-1, 0], sway[1:, 0])[0, 1]), rho, delta=2.0e-3)


class EnsembleTest(unittest.TestCase):
    def test_a_seed_fixes_the_case(self):
        first, second, other = draw_case(1000), draw_case(1000), draw_case(1001)
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_cases_stay_inside_the_simulator_and_the_record(self):
        for seed in range(1000, 1200):
            scenario, impairments = draw_case(seed)
            ranges = scenario.target_ranges_m()
            angles = np.asarray(scenario.target_angles_deg)
            self.assertLessEqual(ranges.max(), MAX_TARGET_RANGE_M)
            self.assertLess(np.abs(angles).max(), 28.0 + 1.0e-9)
            range_gap = np.abs(ranges[:, None] - ranges[None, :]) / package_builder.RANGE_RESOLUTION_M
            angle_gap = np.abs(angles[:, None] - angles[None, :])
            unresolved = (range_gap < MIN_RANGE_SEPARATION_BINS) & (angle_gap < MIN_ANGLE_SEPARATION_DEG)
            self.assertFalse(np.any(np.triu(unresolved, k=1)), msg=f"seed {seed}")
            start, = scenario.event_starts_s
            self.assertLess(start + scenario.passage_duration_s + 0.3, 4.0)
            self.assertGreater(scenario.passage_duration_s, 0.5)
            self.assertTrue(0.0 <= impairments.adxl_clock_phase_s <= 2.0e-3)
            self.assertLessEqual(abs(impairments.adxl_timestamp_offset_s), 2.0e-3)
            self.assertGreaterEqual(impairments.iq_offset_ratio, 0.02)
            self.assertLessEqual(impairments.iq_offset_ratio, 0.5)
            self.assertGreaterEqual(impairments.snr_offset_db, -10.0)

    def test_a_drawn_case_generates_a_package(self):
        scenario, impairments = draw_case(1003)
        with tempfile.TemporaryDirectory(prefix="ensemble-test-") as temporary:
            package = package_builder.generate(
                Path(temporary) / "p", duration_s=0.5, seed=1003, impairments=impairments, scenario=scenario, fast=True)
            manifest = json.loads((package / "radar" / "algorithm_input" / "manifest.json").read_text())
            self.assertNotIn("chirp_cube", manifest["arrays"])
            self.assertEqual(manifest["source"]["scenario"]["height_m"], scenario.height_m)
            self.assertEqual(manifest["source"]["impairments"]["iq_offset_ratio"], impairments.iq_offset_ratio)
            self.assertEqual(
                [round(r, 9) for r in manifest["source"]["target_ranges_m"]],
                [round(float(r), 9) for r in scenario.target_ranges_m()],
            )


if __name__ == "__main__":
    unittest.main()
