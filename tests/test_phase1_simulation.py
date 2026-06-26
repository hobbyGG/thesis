import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from simulation.phase1.accelerometer import simulate_accelerometer
from simulation.phase1.config import Phase1Config
from simulation.phase1.methods import cold_start_reference_mean
from simulation.phase1.phase_utils import wrap_to_pi
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.run_phase1 import run
from simulation.phase1.scenarios import build_all_phase1_scenarios, build_phase1_scenarios
from simulation.phase1.truth import generate_component_frequencies, generate_multifrequency_truth


def _synthetic_phase1_scenarios():
    return [scenario for scenario in build_all_phase1_scenarios() if scenario.motion_profile != "measured_bridge"]


def _scenario_by_name(name):
    return next(scenario for scenario in build_all_phase1_scenarios() if scenario.scenario_name == name)


class Phase1SimulationTest(unittest.TestCase):
    def test_component_frequencies_are_seeded_near_nominal_values(self):
        freqs_a = generate_component_frequencies([2.0, 5.0, 12.0], jitter_hz=1.0, seed=7)
        freqs_b = generate_component_frequencies([2.0, 5.0, 12.0], jitter_hz=1.0, seed=7)

        self.assertEqual(freqs_a, freqs_b)
        self.assertEqual(len(freqs_a), 3)

        for freq, nominal in zip(freqs_a, [2.0, 5.0, 12.0]):
            self.assertGreaterEqual(freq, nominal - 1.0)
            self.assertLessEqual(freq, nominal + 1.0)
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

    def test_truth_generator_supports_quiet_cold_start_window(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=12,
            quiet_start_duration_s=0.08,
        )

        truth = generate_multifrequency_truth(config)
        quiet = truth.t < config.quiet_start_duration_s
        active = truth.t > config.quiet_start_duration_s + 0.1

        self.assertLess(np.max(np.abs(truth.q_m[quiet])), 1e-15)
        self.assertLess(np.max(np.abs(truth.v_mps[quiet])), 1e-12)
        self.assertLess(np.max(np.abs(truth.a_mps2[quiet])), 1e-9)
        self.assertGreater(np.max(np.abs(truth.q_m[active])), 1e-6)

    def test_vehicle_event_truth_is_nonstationary_after_quiet_start(self):
        config = Phase1Config(
            duration_s=3.0,
            sample_rate_hz=1000.0,
            seed=13,
            motion_profile="vehicle_event",
            quiet_start_duration_s=0.10,
            vehicle_event_center_s=1.5,
            vehicle_event_width_s=0.35,
        )

        truth = generate_multifrequency_truth(config)
        quiet = truth.t < config.quiet_start_duration_s
        event = np.abs(truth.t - config.vehicle_event_center_s) < config.vehicle_event_width_s
        tail = truth.t > config.vehicle_event_center_s + 3.0 * config.vehicle_event_width_s

        self.assertLess(np.max(np.abs(truth.q_m[quiet])), 1e-15)
        self.assertGreater(np.max(np.abs(truth.q_m[event])), 5.0 * np.max(np.abs(truth.q_m[tail])))

    def test_default_synthetic_scenario_peak_displacements_match_report_design(self):
        for scenario in _synthetic_phase1_scenarios():
            with self.subTest(scenario=scenario.scenario_name):
                truth = generate_multifrequency_truth(scenario)
                peak_mm = float(np.max(np.abs(truth.q_m)) * 1e3)
                if scenario.scenario_name == "strong_wrapping":
                    self.assertGreaterEqual(peak_mm, 4.0)
                    self.assertLessEqual(peak_mm, 6.0)
                else:
                    self.assertGreaterEqual(peak_mm, 1.0)
                    self.assertLessEqual(peak_mm, 2.0)

    def test_default_synthetic_frequencies_are_below_slow_time_nyquist(self):
        for scenario in _synthetic_phase1_scenarios():
            with self.subTest(scenario=scenario.scenario_name):
                truth = generate_multifrequency_truth(scenario)
                self.assertLess(max(truth.frequencies_hz), 0.45 * scenario.sample_rate_hz)

    def test_default_scenarios_include_literature_modal_response_not_tdms_bridge(self):
        names = [scenario.scenario_name for scenario in build_phase1_scenarios()]

        self.assertEqual(
            names,
            [
                "literature_maglev_modal_response",
                "strong_wrapping",
                "same_range_far_angles",
                "aoa_error_bootstrap",
                "target_snr_drop",
                "vehicle_event_nonstationary",
            ],
        )
        self.assertIn("literature_maglev_modal_response", names)
        self.assertNotIn("nominal_multifrequency", names)
        self.assertNotIn("measured_bridge_point4_transverse", names)

    def test_literature_maglev_modal_response_uses_reported_main_frequencies(self):
        scenario = _scenario_by_name("literature_maglev_modal_response")
        truth = generate_multifrequency_truth(scenario)

        self.assertEqual(scenario.motion_profile, "literature_maglev_modal")
        self.assertEqual(tuple(truth.frequencies_hz[:3]), (7.7737, 11.5742, 26.5642))
        self.assertGreaterEqual(scenario.sample_rate_hz, 200.0)

        peak_mm = float(np.max(np.abs(truth.q_m)) * 1e3)
        self.assertGreaterEqual(peak_mm, 1.0)
        self.assertLessEqual(peak_mm, 2.0)

    def test_literature_maglev_modal_response_has_broadened_modal_bands(self):
        scenario = _scenario_by_name("literature_maglev_modal_response")
        truth = generate_multifrequency_truth(scenario)
        q = truth.q_m - np.mean(truth.q_m)
        freqs = np.fft.rfftfreq(q.size, d=1.0 / scenario.sample_rate_hz)
        spectrum = np.abs(np.fft.rfft(q))

        for modal_hz in (7.7737, 11.5742, 26.5642):
            with self.subTest(modal_hz=modal_hz):
                modal_band = (freqs >= modal_hz - 0.75) & (freqs <= modal_hz + 0.75)
                nearby_floor = (freqs >= modal_hz + 1.25) & (freqs <= modal_hz + 2.75)

                self.assertGreater(float(np.max(spectrum[modal_band])), 0.0)
                self.assertGreater(
                    float(np.mean(spectrum[modal_band])),
                    3.0 * float(np.mean(spectrum[nearby_floor])),
                )
                self.assertGreater(np.count_nonzero(spectrum[modal_band] > 0.15 * np.max(spectrum[modal_band])), 1)

    def test_strong_wrapping_has_quiet_micro_ramp_and_strong_intervals(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "strong_wrapping"][0]
        truth = generate_multifrequency_truth(scenario)

        quiet = truth.t < 0.20
        micro = (truth.t >= 0.20) & (truth.t < 0.80)
        ramp = (truth.t >= 0.80) & (truth.t < 1.40)
        strong = (truth.t >= 1.40) & (truth.t < 3.20)
        decay = truth.t >= 3.20

        quiet_peak_mm = float(np.max(np.abs(truth.q_m[quiet])) * 1e3)
        micro_peak_mm = float(np.max(np.abs(truth.q_m[micro])) * 1e3)
        ramp_peak_mm = float(np.max(np.abs(truth.q_m[ramp])) * 1e3)
        strong_peak_mm = float(np.max(np.abs(truth.q_m[strong])) * 1e3)
        decay_peak_mm = float(np.max(np.abs(truth.q_m[decay])) * 1e3)

        self.assertLess(quiet_peak_mm, 0.02)
        self.assertGreaterEqual(micro_peak_mm, 0.05)
        self.assertLessEqual(micro_peak_mm, 0.25)
        self.assertGreater(ramp_peak_mm, micro_peak_mm)
        self.assertGreaterEqual(strong_peak_mm, 4.0)
        self.assertLessEqual(strong_peak_mm, 6.0)
        self.assertLess(decay_peak_mm, strong_peak_mm)

    def test_default_synthetic_scenarios_start_weak_before_full_response(self):
        for scenario in _synthetic_phase1_scenarios():
            with self.subTest(scenario=scenario.scenario_name):
                truth = generate_multifrequency_truth(scenario)
                q_mm = np.abs(truth.q_m) * 1e3
                peak_mm = float(np.max(q_mm))
                quiet = truth.t < 0.20
                micro = (truth.t >= 0.20) & (truth.t < 0.80)
                strong = truth.t >= 1.40

                quiet_peak_mm = float(np.max(q_mm[quiet]))
                micro_peak_mm = float(np.max(q_mm[micro]))
                strong_peak_mm = float(np.max(q_mm[strong]))

                self.assertLess(quiet_peak_mm, 0.05 * peak_mm)
                self.assertGreater(micro_peak_mm, 0.01 * peak_mm)
                self.assertLess(micro_peak_mm, 0.30 * peak_mm)
                self.assertGreater(strong_peak_mm, 0.80 * peak_mm)

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

    def test_radar_wrapped_phase_matches_independent_los_phase_model(self):
        config = Phase1Config(
            duration_s=0.5,
            sample_rate_hz=1000.0,
            seed=22,
            target_snr_db=(240.0, 240.0, 240.0, 240.0, 240.0),
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)
        theta = 4.0 * math.pi * truth.q_m / config.wavelength_m()

        for target_idx, kappa in enumerate(radar.kappa):
            physical_phase_without_bias = kappa * theta
            bias = wrap_to_pi(radar.wrapped_phase_rad[target_idx, 0] - physical_phase_without_bias[0])
            expected_wrapped = wrap_to_pi(physical_phase_without_bias + bias)
            phase_error = wrap_to_pi(radar.wrapped_phase_rad[target_idx] - expected_wrapped)
            self.assertLess(np.max(np.abs(phase_error)), 1e-8)

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

    def test_accelerometer_sync_error_is_independent_time_shift(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=32,
            accel_noise_std_mps2=0.0,
            accel_bias_mps2=0.0,
            accel_drift_mps2=0.0,
            accel_sync_error_s=0.01,
        )
        truth = generate_multifrequency_truth(config)

        accel = simulate_accelerometer(truth, config)
        expected = np.interp(
            truth.t - config.accel_sync_error_s,
            truth.t,
            truth.a_mps2,
            left=truth.a_mps2[0],
            right=truth.a_mps2[-1],
        )

        np.testing.assert_allclose(accel.measured_mps2, expected)

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

    def test_run_phase1_writes_cold_start_relative_reference_fields(self):
        config = Phase1Config(duration_s=0.2, sample_rate_hz=1000.0, seed=44)

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "phase1.npz"
            run(output, config)
            data = np.load(output)

            q_ref = cold_start_reference_mean(data["q_m"], config)
            self.assertIn("q_ref_m", data)
            self.assertIn("delta_q_m", data)
            self.assertIn("delta_main_phase_rad", data)
            self.assertAlmostEqual(float(data["q_ref_m"]), q_ref)
            np.testing.assert_allclose(data["delta_q_m"], data["q_m"] - q_ref)


class Phase1ConfigExtensionTest(unittest.TestCase):
    def test_default_phase_sample_rate_is_iwr_like_slow_time_not_adc_rate(self):
        config = Phase1Config()

        self.assertEqual(config.sample_rate_hz, 100.0)
        self.assertEqual(config.adc_sample_rate_hz, 6.0e6)
        self.assertEqual(config.chirps_per_frame, 4)
        self.assertEqual(config.adc_samples_per_chirp, 256)

    def test_default_kalman_and_bootstrap_config_values_are_available(self):
        config = Phase1Config()

        self.assertGreater(config.process_noise_intensity, 0.0)
        self.assertGreater(config.initial_state_variance, 0.0)
        self.assertGreater(config.initial_rate_variance, 0.0)
        self.assertGreater(config.initial_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.max_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.cold_start_duration_s, 0.0)
        self.assertGreater(config.kappa_window_samples, 2)
        self.assertGreater(config.kappa_update_start_s, 0.0)
        self.assertGreater(config.kappa_bootstrap_prior_weight, 0.0)
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
