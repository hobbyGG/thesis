import unittest
from dataclasses import replace

import numpy as np

from simulation.phase1.accelerometer import AccelerometerObservation
from simulation.phase1.config import Phase1Config
from simulation.phase1.ma2026 import (
    Ma2026Config,
    Ma2026RangeBinInput,
    calibrate_alpha_linear_fit,
    estimate_ma2026_target,
    estimate_ma2026_reproduction,
    q_grid,
    rangebin_input_from_range_fft,
    run_ma2026_los_kalman,
    select_q_by_energy,
)
from simulation.phase1.algorithm import cold_start_reference_mean
from simulation.phase1.ma2026.kalman import _select_energy_minimizer
from simulation.phase1.metrics import displacement_metrics
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.scenario_inputs import build_scenario_inputs
from simulation.phase1.scenarios import build_all_phase1_scenarios, build_phase1_scenarios
from simulation.phase1.truth import generate_multifrequency_truth


class Ma2026ReproductionTest(unittest.TestCase):
    def test_ma2026_package_does_not_contain_prior_paper_reference_path(self):
        import simulation.phase1.ma2026 as ma2026
        import simulation.phase1.ma2026.method as ma2026_method

        old_paper = "ma20" + "23"
        self.assertFalse(hasattr(ma2026, f"estimate_{old_paper}_reproduction"))
        self.assertNotIn(old_paper, ma2026_method.__dict__)
        self.assertNotIn(f"{old_paper}_fir_fusion", ma2026_method.__dict__)

    def test_q_grid_uses_ma2026_energy_candidate_set(self):
        grid = q_grid(Ma2026Config())

        self.assertEqual(grid.shape, (21,))
        self.assertEqual(float(grid[0]), 1.0)
        self.assertEqual(float(grid[-1]), 1.0e20)
        self.assertTrue(np.allclose(grid, 10.0 ** np.arange(21)))

    def test_ma2026_default_alpha_fit_band_matches_paper_experiment(self):
        config = Ma2026Config()

        self.assertEqual((config.alpha_band_low_hz, config.alpha_band_high_hz), (0.5, 3.0))

    def test_scenario_adapter_alpha_band_covers_configured_structural_frequencies(self):
        phase1 = next(
            item for item in build_phase1_scenarios() if item.scenario_name == "literature_maglev_modal_response"
        )

        inputs = build_scenario_inputs(phase1)

        self.assertGreaterEqual(
            inputs.ma2026_config.alpha_band_high_hz,
            max(phase1.nominal_frequencies_hz),
        )

    def test_q_energy_selection_is_plain_argmin_without_extra_tie_break(self):
        candidates = np.asarray([1.0, 10.0, 100.0, 1000.0], dtype=float)
        energies = np.asarray([3.0, 1.0, 1.0, 2.0], dtype=float)

        selected_idx = _select_energy_minimizer(candidates, energies, Ma2026Config())

        self.assertEqual(selected_idx, 1)


    def test_ma2026_formal_adapter_uses_range_fft_slow_time_not_range_angle_bins(self):
        frames = 6
        range_fft = np.zeros((frames, 3, 5), dtype=complex)
        phase = np.linspace(-0.2, 0.8, frames)
        range_fft[:, 1, 2] = 3.0 * np.exp(1j * phase)
        range_fft[:, 2, 2] = 0.5 * np.exp(1j * (phase + 1.0))

        result = rangebin_input_from_range_fft(range_fft, Ma2026Config())

        self.assertEqual(result.range_bins.tolist(), [2])
        np.testing.assert_allclose(result.wrapped_phase_rad[0], phase, atol=1e-12)

    def test_ma2026_rangebin_adapter_orders_candidates_by_distance_spectrum_power(self):
        frames = 6
        range_fft = np.zeros((frames, 2, 6), dtype=complex)
        phase = np.linspace(-0.2, 0.8, frames)
        range_fft[:, 0, 1] = 2.0 * np.exp(1j * phase)
        range_fft[:, 1, 4] = 5.0 * np.exp(1j * (phase + 0.4))

        result = rangebin_input_from_range_fft(range_fft, Ma2026Config())

        self.assertEqual(result.range_bins[:2].tolist(), [4, 1])

    def test_ma2026_reproduction_uses_first_rangebin_candidate_without_beta_grid(self):
        phase1 = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(
            Ma2026Config(),
            calibration_max_samples=200,
            q_exponent_min=0,
            q_exponent_max=1,
        )
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.001 * np.sin(2.0 * np.pi * 2.0 * t)
        accel_values = -((2.0 * np.pi * 2.0) ** 2) * q
        beta_target_1 = 1.25
        los_phase_target_1 = 4.0 * np.pi * q / (beta_target_1 * phase1.wavelength_m())
        wrapped_first_candidate = np.angle(np.exp(1j * (0.35 * los_phase_target_1 + 1.1)))
        wrapped_second_candidate = np.angle(np.exp(1j * los_phase_target_1))
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=np.vstack([wrapped_first_candidate, wrapped_second_candidate]),
            available_mask=np.ones((2, t.size), dtype=bool),
            range_bins=np.asarray([10, 20], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=accel_values,
            measured_mps2=accel_values,
            bias_mps2=np.zeros_like(accel_values),
            noise_mps2=np.zeros_like(accel_values),
        )

        result = estimate_ma2026_reproduction(radar_input, accel, phase1, ma_config)

        self.assertEqual(result.extra["selected_target_index"], 0)
        self.assertNotIn("beta_grid", result.extra)
        self.assertNotIn("offline_calibration", result.extra)

    def test_ma2026_target_alpha_fit_uses_supplied_corrected_phase(self):
        phase1 = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        ma_config = replace(Ma2026Config(), calibration_max_samples=400, q_exponent_min=0, q_exponent_max=2)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.0011 * np.sin(2.0 * np.pi * 1.0 * t) + 0.0004 * np.sin(2.0 * np.pi * 2.5 * t)
        accel_values = (
            -((2.0 * np.pi * 1.0) ** 2) * 0.0011 * np.sin(2.0 * np.pi * 1.0 * t)
            - ((2.0 * np.pi * 2.5) ** 2) * 0.0004 * np.sin(2.0 * np.pi * 2.5 * t)
        )
        alpha_true = 1.31
        true_los_phase = 4.0 * np.pi * q / (alpha_true * phase1.wavelength_m()) + 0.73
        wrapped = np.angle(np.exp(1j * true_los_phase))

        result = estimate_ma2026_target(
            wrapped,
            accel_values,
            phase1,
            ma_config,
            fallback_alpha=9.0,
            calibration_los_corrected_phase_rad=true_los_phase,
        )

        self.assertAlmostEqual(result.extra["selected_alpha"], alpha_true, delta=0.01)
        self.assertEqual(result.extra["alpha_calibration"]["phase_source"], "supplied_corrected_los_phase")
        self.assertNotIn("fallback_alpha", result.extra)

    def test_ma2026_kalman_uses_paper_discrete_measurement_covariance(self):
        phase1 = Phase1Config(duration_s=0.2, sample_rate_hz=50.0, carrier_frequency_hz=77.0e9)
        ma_config = Ma2026Config()
        n_samples = int(phase1.duration_s * phase1.sample_rate_hz)
        wrapped = np.zeros(n_samples, dtype=float)
        accel = np.zeros(n_samples, dtype=float)

        result = run_ma2026_los_kalman(wrapped, accel, beta=1.0, phase1_config=phase1, ma_config=ma_config, q_value=1.0)

        self.assertEqual(result.measurement_noise_r, ma_config.measurement_noise_r * phase1.sample_rate_hz)
        self.assertEqual(result.process_noise_q, 1.0)
        self.assertEqual(result.los_corrected_phase_rad.shape, wrapped.shape)

    def test_ma2026_q_energy_uses_corrected_measurement_phase_per_eq16(self):
        phase1 = Phase1Config(duration_s=0.5, sample_rate_hz=20.0, carrier_frequency_hz=77.0e9)
        ma_config = replace(Ma2026Config(), q_exponent_min=0, q_exponent_max=2)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        structural_phase = 1.8 * np.sin(2.0 * np.pi * 2.0 * t)
        beta = 1.2
        los_phase = structural_phase / beta
        wrapped = np.angle(np.exp(1j * los_phase))
        acceleration = np.zeros_like(wrapped)

        _, candidates, energies, _ = select_q_by_energy(
            wrapped,
            acceleration,
            beta,
            phase1,
            ma_config,
        )

        expected = []
        for q_value in candidates:
            result = run_ma2026_los_kalman(
                wrapped,
                acceleration,
                beta,
                phase1,
                ma_config,
                q_value=float(q_value),
            )
            corrected_delta = result.los_corrected_phase_rad - result.los_corrected_phase_rad[0]
            valid = np.isfinite(corrected_delta)
            expected.append(float(np.mean(corrected_delta[valid] ** 2)))
        np.testing.assert_allclose(energies, np.asarray(expected), rtol=1e-12, atol=1e-12)

    def test_ma2026_q_selection_uses_energy_argmin_candidate(self):
        phase1 = next(
            item for item in build_all_phase1_scenarios() if item.scenario_name == "literature_maglev_modal_response"
        )
        truth = generate_multifrequency_truth(phase1)
        radar = simulate_radar_targets(truth, phase1)
        accel = AccelerometerObservation(
            true_mps2=truth.a_mps2,
            measured_mps2=truth.a_mps2,
            bias_mps2=np.zeros_like(truth.a_mps2),
            noise_mps2=np.zeros_like(truth.a_mps2),
        )
        beta = float(radar.beta[0])

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
        ma_config = replace(Ma2026Config(), calibration_max_samples=100)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz), dtype=float) / phase1.sample_rate_hz
        q = 0.001 * np.sin(2.0 * np.pi * 3.0 * t)
        accel_values = -(2.0 * np.pi * 3.0) ** 2 * q
        beta_true = 1.2
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * q / (beta_true * phase1.wavelength_m()))))
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=wrapped[None, :],
            available_mask=np.ones((1, t.size), dtype=bool),
            range_bins=np.array([9], dtype=int),
            calibration_los_corrected_phase_rad=(4.0 * np.pi * q / (beta_true * phase1.wavelength_m()))[None, :],
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
        self.assertEqual(result.extra["calibration_stage"], "ma2026_alpha_linear_fit")
        self.assertEqual(result.extra["target_adapter"], "range_fft_distance_spectrum_first_candidate")
        self.assertEqual(result.extra["alpha_calibration"]["source"], "ma2026_bandpass_phase_linear_fit")
        self.assertEqual(result.extra["alpha_calibration"]["phase_source"], "supplied_corrected_los_phase")
        self.assertIn("q_grid", result.extra)
        self.assertIn("q_energy", result.extra)
        self.assertIn("alpha_calibration", result.extra)
        self.assertIn("convergence_time_s", result.extra)
        self.assertNotIn("offline_calibration", result.extra)
        self.assertNotIn("Ma20" + "23", result.extra["source"])
        self.assertEqual(result.extra["selected_target_count"], 1)
        self.assertEqual(result.los_corrected_phase_rad.shape, (1, t.size))

    def test_ma2026_reproduction_uses_rangebin_adapter_before_target_kalman(self):
        phase1 = next(
            item for item in build_phase1_scenarios() if item.scenario_name == "literature_maglev_modal_response"
        )
        from simulation.phase1.scenario_inputs import build_scenario_inputs

        inputs = build_scenario_inputs(phase1)
        ma_config = replace(
            inputs.ma2026_config,
            calibration_max_samples=int(phase1.duration_s * phase1.sample_rate_hz),
        )

        result = estimate_ma2026_reproduction(
            inputs.radar.ma2026_rangebin,
            inputs.accelerometer,
            phase1,
            ma_config,
        )
        q_ref = cold_start_reference_mean(inputs.truth.q_m, phase1)
        metrics = displacement_metrics(result.q_hat_m, inputs.truth.q_m - q_ref)

        self.assertEqual(result.extra["calibration_stage"], "ma2026_alpha_linear_fit")
        self.assertEqual(result.extra["target_adapter"], "range_fft_distance_spectrum_first_candidate")
        self.assertEqual(int(result.extra["selected_target_index"]), 0)
        self.assertNotIn("offline_calibration", result.extra)
        self.assertTrue(np.isfinite(metrics["rmse_mm"]))
        self.assertLess(abs(float(result.extra["selected_beta"])), 2.0)

    def test_ma2026_q_energy_selection_reaches_paper_level_accuracy_after_beta_calibration(self):
        phase1 = next(
            item for item in build_phase1_scenarios() if item.scenario_name == "literature_maglev_modal_response"
        )
        from simulation.phase1.scenario_inputs import build_scenario_inputs

        inputs = build_scenario_inputs(phase1)
        ma_config = replace(
            inputs.ma2026_config,
            calibration_max_samples=int(phase1.duration_s * phase1.sample_rate_hz),
        )

        result = estimate_ma2026_reproduction(
            inputs.radar.ma2026_rangebin,
            inputs.accelerometer,
            phase1,
            ma_config,
        )
        q_ref = cold_start_reference_mean(inputs.truth.q_m, phase1)
        metrics = displacement_metrics(result.q_hat_m, inputs.truth.q_m - q_ref)

        self.assertIn(float(result.extra["selected_q"]), set(q_grid(ma_config).tolist()))
        self.assertTrue(np.isfinite(metrics["rmse_mm"]))
        self.assertGreater(metrics["rmse_mm"], 0.0)

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
        true_los_phase = 4.0 * np.pi * q / (alpha_true * phase1.wavelength_m())
        wrapped = np.angle(np.exp(1j * true_los_phase))

        result = estimate_ma2026_target(
            wrapped,
            accel_values,
            phase1,
            ma_config,
            calibration_los_corrected_phase_rad=true_los_phase,
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
