import unittest
from dataclasses import replace

import numpy as np

from simulation.phase1.accelerometer import AccelerometerObservation
from simulation.phase1.config import Phase1Config
from simulation.phase1.ma2026 import (
    Ma2026Config,
    Ma2026RangeBinInput,
    beta_grid,
    calibrate_alpha_linear_fit,
    calibrate_best_target,
    estimate_ma2026_target,
    estimate_ma2026_reproduction,
    ma2023_acceleration_aided_unwrap,
    q_grid,
    run_ma2026_los_kalman,
    select_q_by_energy,
)
from simulation.phase1.algorithm import cold_start_reference_mean
from simulation.phase1.ma2026.calibration import _bandpass_fft_rows, _target_beta_rmse_grid_mm
from simulation.phase1.ma2026.filtering import acceleration_to_displacement, highpass_fft
from simulation.phase1.ma2026.kalman import _select_energy_minimizer
from simulation.phase1.metrics import displacement_metrics
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.scenarios import build_phase1_scenarios
from simulation.phase1.truth import generate_multifrequency_truth


class Ma2026ReproductionTest(unittest.TestCase):
    def test_beta_grid_uses_ma2023_range_with_milliscale_resolution(self):
        grid = beta_grid(Ma2026Config())

        self.assertAlmostEqual(float(grid[0]), 0.5)
        self.assertAlmostEqual(float(grid[-1]), 2.0)
        self.assertAlmostEqual(float(grid[1] - grid[0]), 0.001)
        self.assertIn(0.985, set(np.round(grid, 3)))

    def test_q_grid_uses_ma2026_energy_candidate_set(self):
        grid = q_grid(Ma2026Config())

        self.assertEqual(grid.shape, (21,))
        self.assertEqual(float(grid[0]), 1.0)
        self.assertEqual(float(grid[-1]), 1.0e20)
        self.assertTrue(np.allclose(grid, 10.0 ** np.arange(21)))

    def test_q_energy_selection_is_plain_argmin_without_extra_tie_break(self):
        candidates = np.asarray([1.0, 10.0, 100.0, 1000.0], dtype=float)
        energies = np.asarray([3.0, 1.0, 1.0, 2.0], dtype=float)

        selected_idx = _select_energy_minimizer(candidates, energies, Ma2026Config())

        self.assertEqual(selected_idx, 1)

    def test_ma2023_unwrap_uses_two_previous_displacements_and_acceleration(self):
        config = Phase1Config(sample_rate_hz=10.0, carrier_frequency_hz=1.0)
        wavelength = config.wavelength_m()
        beta = 1.0
        accel = np.array([0.0, 2.0, 0.0], dtype=float)
        raw_phase = np.array([0.0, 0.0, -np.pi + 0.1], dtype=float)

        unwrapped, displacement = ma2023_acceleration_aided_unwrap(raw_phase, accel, beta, config)

        dt = 1.0 / config.sample_rate_hz
        predicted_u2 = 2.0 * displacement[1] - displacement[0] + dt * dt * accel[1]
        predicted_phase2 = raw_phase[0] + 4.0 * np.pi * predicted_u2 / (beta * wavelength)
        expected_phase2 = raw_phase[2] + 2.0 * np.pi * np.round((predicted_phase2 - raw_phase[2]) / (2.0 * np.pi))
        self.assertAlmostEqual(float(unwrapped[2]), float(expected_phase2))

    def test_ma2023_calibration_jointly_selects_target_and_beta_by_rmse(self):
        phase1 = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=200.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(Ma2026Config(), beta_grid_step=0.001, calibration_max_samples=400)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.0015 * np.sin(2.0 * np.pi * 3.0 * t)
        accel_values = -(2.0 * np.pi * 3.0) ** 2 * q
        beta_true = 0.985
        los_phase = 4.0 * np.pi * q / (beta_true * phase1.wavelength_m())
        wrapped_good = np.angle(np.exp(1j * los_phase))
        wrapped_bad = np.angle(np.exp(1j * (0.45 * los_phase + 1.2)))
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=np.vstack([wrapped_bad, wrapped_good]),
            available_mask=np.ones((2, t.size), dtype=bool),
            range_bins=np.array([12, 18], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=accel_values,
            measured_mps2=accel_values,
            bias_mps2=np.zeros_like(accel_values),
            noise_mps2=np.zeros_like(accel_values),
        )

        result = calibrate_best_target(radar_input, accel, phase1, ma_config)

        self.assertEqual(result.selected_target_index, 1)
        self.assertEqual(result.selected_range_bin, 18)
        self.assertAlmostEqual(result.selected_beta, beta_true, delta=0.002)
        self.assertEqual(result.highpass_cutoff_hz, 0.5)
        self.assertEqual(result.rmse_grid_mm.shape, (2, beta_grid(ma_config).size))

    def test_ma2023_conversion_factor_calibration_band_limits_high_frequency_mismatch(self):
        phase1 = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(
            Ma2026Config(),
            beta_grid_min=0.8,
            beta_grid_max=1.2,
            beta_grid_step=0.001,
            conversion_band_low_hz=0.5,
            conversion_band_high_hz=10.0,
            calibration_max_samples=200,
        )
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        low_q = 0.001 * np.sin(2.0 * np.pi * 2.0 * t)
        high_q = 0.0004 * np.sin(2.0 * np.pi * 25.0 * t)
        radar_q = low_q + high_q
        accel_q = low_q
        accel_values = -(2.0 * np.pi * 2.0) ** 2 * accel_q
        beta_true = 1.05
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * radar_q / (beta_true * phase1.wavelength_m()))))
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=wrapped[None, :],
            available_mask=np.ones((1, t.size), dtype=bool),
            range_bins=np.array([18], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=accel_values,
            measured_mps2=accel_values,
            bias_mps2=np.zeros_like(accel_values),
            noise_mps2=np.zeros_like(accel_values),
        )

        result = calibrate_best_target(radar_input, accel, phase1, ma_config)

        self.assertAlmostEqual(result.selected_beta, beta_true, delta=0.01)
        self.assertEqual(result.conversion_band_hz, (0.5, 10.0))

    def test_vectorized_beta_rmse_grid_matches_scalar_unwrap_reference(self):
        phase1 = Phase1Config(
            duration_s=0.6,
            sample_rate_hz=80.0,
            carrier_frequency_hz=77.0e9,
            accel_noise_std_mps2=0.0,
        )
        ma_config = Ma2026Config()
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.0008 * np.sin(2.0 * np.pi * 4.0 * t)
        accel_values = -(2.0 * np.pi * 4.0) ** 2 * q
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * q / (1.1 * phase1.wavelength_m()))))
        available = np.ones_like(wrapped, dtype=bool)
        beta_values = np.array([0.8, 1.0, 1.1, 1.3], dtype=float)
        accel_disp = acceleration_to_displacement(
            accel_values,
            phase1.sample_rate_hz,
            ma_config.highpass_cutoff_hz,
        )

        vectorized = _target_beta_rmse_grid_mm(
            wrapped,
            available,
            accel_values,
            accel_disp,
            beta_values,
            phase1,
            ma_config,
        )
        scalar = []
        for beta in beta_values:
            _, radar_disp = ma2023_acceleration_aided_unwrap(wrapped, accel_values, float(beta), phase1)
            radar_band = _bandpass_fft_rows(
                radar_disp[None, :],
                phase1.sample_rate_hz,
                ma_config.conversion_band_low_hz,
                ma_config.conversion_band_high_hz,
            )[0]
            accel_band = _bandpass_fft_rows(
                accel_disp[None, :],
                phase1.sample_rate_hz,
                ma_config.conversion_band_low_hz,
                ma_config.conversion_band_high_hz,
            )[0]
            valid = np.isfinite(radar_band) & np.isfinite(accel_band) & available
            residual = radar_band[valid] - accel_band[valid]
            scalar.append(float(np.sqrt(np.mean(residual**2)) * 1.0e3))

        np.testing.assert_allclose(vectorized, np.asarray(scalar), atol=1e-12)

    def test_ma2026_kalman_uses_paper_discrete_measurement_covariance(self):
        phase1 = Phase1Config(duration_s=0.2, sample_rate_hz=50.0, carrier_frequency_hz=77.0e9)
        ma_config = Ma2026Config()
        n_samples = int(phase1.duration_s * phase1.sample_rate_hz)
        wrapped = np.zeros(n_samples, dtype=float)
        accel = np.zeros(n_samples, dtype=float)

        result = run_ma2026_los_kalman(wrapped, accel, beta=1.0, phase1_config=phase1, ma_config=ma_config, q_value=1.0)

        self.assertEqual(result.measurement_noise_r, ma_config.measurement_noise_r * phase1.sample_rate_hz)
        self.assertEqual(result.process_noise_q, 1.0)
        self.assertEqual(result.corrected_phase_rad.shape, wrapped.shape)

    def test_ma2026_q_selection_uses_energy_argmin_candidate(self):
        phase1 = next(item for item in build_phase1_scenarios() if item.scenario_name == "nominal_multifrequency")
        truth = generate_multifrequency_truth(phase1)
        radar = simulate_radar_targets(truth, phase1)
        accel = AccelerometerObservation(
            true_mps2=truth.a_mps2,
            measured_mps2=truth.a_mps2,
            bias_mps2=np.zeros_like(truth.a_mps2),
            noise_mps2=np.zeros_like(truth.a_mps2),
        )
        beta = 1.0 / float(radar.kappa[0])

        selected_q, _, _, result = select_q_by_energy(
            radar.wrapped_phase_rad[0],
            accel.measured_mps2,
            beta,
            phase1,
            Ma2026Config(),
        )
        q_ref = cold_start_reference_mean(truth.q_m, phase1)
        metrics = displacement_metrics(result.displacement_m, truth.q_m - q_ref)
        peak_mm = float(np.max(np.abs(truth.q_m)) * 1.0e3)

        self.assertIn(float(selected_q), set(float(item) for item in q_grid(Ma2026Config())))
        self.assertLess(metrics["rmse_mm"], 0.12 * peak_mm)

    def test_estimate_ma2026_reproduction_exposes_calibration_and_q_diagnostics(self):
        phase1 = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(Ma2026Config(), beta_grid_step=0.001, calibration_max_samples=100)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.001 * np.sin(2.0 * np.pi * 3.0 * t)
        accel_values = -(2.0 * np.pi * 3.0) ** 2 * q
        beta_true = 1.2
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * q / (beta_true * phase1.wavelength_m()))))
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=wrapped[None, :],
            available_mask=np.ones((1, t.size), dtype=bool),
            range_bins=np.array([9], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=accel_values,
            measured_mps2=accel_values,
            bias_mps2=np.zeros_like(accel_values),
            noise_mps2=np.zeros_like(accel_values),
        )

        result = estimate_ma2026_reproduction(radar_input, accel, phase1, ma_config)

        self.assertEqual(result.method_name, "ma2026_reproduction")
        self.assertEqual(result.extra["selected_range_bin"], 9)
        self.assertAlmostEqual(result.extra["selected_beta"], beta_true, delta=0.003)
        self.assertAlmostEqual(result.extra["selected_alpha"], beta_true, delta=0.003)
        self.assertIn("q_grid", result.extra)
        self.assertIn("q_energy", result.extra)
        self.assertIn("alpha_calibration", result.extra)
        self.assertIn("convergence_time_s", result.extra)
        self.assertNotIn("Ma2023", result.extra["source"])
        self.assertEqual(result.extra["selected_target_count"], 1)
        self.assertEqual(result.corrected_phase_rad.shape, (1, t.size))

    def test_estimate_ma2026_target_is_paper_target_method_not_rangebin_adapter(self):
        phase1 = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(Ma2026Config(), calibration_max_samples=400)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.0011 * np.sin(2.0 * np.pi * 1.0 * t) + 0.0004 * np.sin(2.0 * np.pi * 2.5 * t)
        accel_values = (
            -((2.0 * np.pi * 1.0) ** 2) * 0.0011 * np.sin(2.0 * np.pi * 1.0 * t)
            - ((2.0 * np.pi * 2.5) ** 2) * 0.0004 * np.sin(2.0 * np.pi * 2.5 * t)
        )
        alpha_true = 1.18
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * q / (alpha_true * phase1.wavelength_m()))))

        result = estimate_ma2026_target(
            wrapped,
            accel_values,
            phase1,
            ma_config,
            initial_alpha=1.0,
        )

        convergence_steps = int(result.extra["convergence_steps"])
        metrics = displacement_metrics(result.q_hat_m[convergence_steps:], q[convergence_steps:])
        self.assertEqual(result.method_name, "ma2026_target")
        self.assertAlmostEqual(result.extra["selected_alpha"], alpha_true, delta=0.02)
        self.assertIn(float(result.extra["selected_q"]), set(float(item) for item in q_grid(ma_config)))
        self.assertGreater(result.extra["convergence_time_s"], 0.0)
        self.assertGreater(convergence_steps, 0)
        self.assertLess(metrics["rmse_mm"], 0.03)
        self.assertNotIn("beta_grid", result.extra)
        self.assertEqual(result.extra["source"], "Ma2026 target-specific acceleration-aided Kalman")


class Ma2026AlphaCalibrationTest(unittest.TestCase):
    def test_alpha_linear_fit_recovers_known_structural_scaling(self):
        sample_rate_hz = 100.0
        wavelength_m = 3.0e8 / 77.0e9
        t = np.arange(800, dtype=float) / sample_rate_hz
        q_struct = 0.0012 * np.sin(2.0 * np.pi * 1.0 * t) + 0.0007 * np.sin(2.0 * np.pi * 2.25 * t)
        acceleration = (
            -((2.0 * np.pi * 1.0) ** 2) * 0.0012 * np.sin(2.0 * np.pi * 1.0 * t)
            - ((2.0 * np.pi * 2.25) ** 2) * 0.0007 * np.sin(2.0 * np.pi * 2.25 * t)
        )
        alpha_true = 1.37
        radar_phase = 4.0 * np.pi * q_struct / (alpha_true * wavelength_m)

        result = calibrate_alpha_linear_fit(radar_phase, acceleration, sample_rate_hz, wavelength_m)

        self.assertAlmostEqual(result.alpha, alpha_true, delta=0.01)
        self.assertAlmostEqual(result.slope, alpha_true, delta=0.01)
        self.assertGreater(result.r2, 0.99)
        self.assertEqual(result.band_hz, (0.5, 3.0))
        self.assertEqual(result.sample_count, t.size)

    def test_alpha_linear_fit_ignores_out_of_band_radar_phase_mismatch(self):
        sample_rate_hz = 100.0
        wavelength_m = 3.0e8 / 77.0e9
        t = np.arange(800, dtype=float) / sample_rate_hz
        q_struct = 0.0014 * np.sin(2.0 * np.pi * 1.25 * t)
        acceleration = -((2.0 * np.pi * 1.25) ** 2) * q_struct
        alpha_true = 0.82
        in_band_phase = 4.0 * np.pi * q_struct / (alpha_true * wavelength_m)
        out_of_band_mismatch = 2.5 * np.sin(2.0 * np.pi * 12.5 * t + 0.4)
        radar_phase = in_band_phase + out_of_band_mismatch

        result = calibrate_alpha_linear_fit(
            radar_phase,
            acceleration,
            sample_rate_hz,
            wavelength_m,
            band_hz=(0.5, 3.0),
        )

        self.assertAlmostEqual(result.alpha, alpha_true, delta=0.01)
        self.assertGreater(result.r2, 0.99)
        self.assertGreater(np.std(result.corrected_phase_band_rad), 0.1)
        self.assertLess(np.std(result.corrected_phase_band_rad - in_band_phase), 0.02)


if __name__ == "__main__":
    unittest.main()
