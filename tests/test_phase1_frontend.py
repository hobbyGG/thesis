import math
import unittest

import numpy as np

from simulation.phase1.config import Phase1Config
from simulation.phase1.frontend import (
    FrontendConfig,
    ScattererTruth,
    angle_deg_to_measured_kappa,
    extract_frontend_target_observation,
    range_angle_process,
    simulate_adc_cube,
    to_algorithm_radar_input,
)
from simulation.phase1.scenario_inputs import build_frontend_views
from simulation.phase1.accelerometer import build_accelerometer_observation
from simulation.phase1.phase_utils import wrap_to_pi
from simulation.phase1.radar import RadarAlgorithmInput, simulate_radar_targets
from simulation.phase1.truth import TruthSignal, generate_multifrequency_truth


def _static_truth(num_frames: int = 4) -> TruthSignal:
    t = np.arange(num_frames, dtype=float) / 1000.0
    zeros = np.zeros(num_frames, dtype=float)
    return TruthSignal(
        t=t,
        q_m=zeros.copy(),
        v_mps=zeros.copy(),
        a_mps2=zeros.copy(),
        frequencies_hz=(),
        amplitudes_m=(),
        phases_rad=(),
    )


class Phase1FrontendTest(unittest.TestCase):
    def test_frontend_adc_defaults_match_iwr_like_profile(self):
        config = Phase1Config()
        frontend_config = FrontendConfig()

        self.assertEqual(frontend_config.num_adc_samples, 256)
        self.assertEqual(frontend_config.adc_sample_rate_hz, 6.0e6)
        self.assertEqual(frontend_config.chirp_duration_s, 60.0e-6)
        self.assertEqual(frontend_config.chirps_per_frame, 4)
        self.assertEqual(frontend_config.num_adc_samples, config.adc_samples_per_chirp)

    def test_adc_cube_shape_axes_and_reproducibility(self):
        config = Phase1Config(
            duration_s=0.008,
            sample_rate_hz=1000.0,
            seed=501,
            num_targets=1,
            target_angles_deg=(0.0,),
            target_snr_db=(80.0,),
            target_amplitudes=(1.0,),
        )
        truth = generate_multifrequency_truth(config)
        frontend_config = FrontendConfig(
            num_virtual_rx=6,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
            range_resolution_m=0.2,
        )

        adc_a = simulate_adc_cube(truth, config, frontend_config)
        adc_b = simulate_adc_cube(truth, config, frontend_config)

        self.assertEqual(adc_a.adc_cube.shape, (truth.t.size, 6, 32))
        self.assertTrue(np.iscomplexobj(adc_a.adc_cube))
        np.testing.assert_allclose(adc_a.frame_times_s, truth.t)
        np.testing.assert_allclose(adc_a.range_axis_m, np.arange(32) * 0.2)
        np.testing.assert_allclose(adc_a.adc_cube, adc_b.adc_cube)

    def test_range_axis_maps_bin_centered_target(self):
        truth = _static_truth()
        config = Phase1Config(seed=502)
        frontend_config = FrontendConfig(
            num_virtual_rx=8,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
            range_resolution_m=0.25,
        )
        target_range_bin = 7
        scatterer = ScattererTruth(
            range_m=target_range_bin * frontend_config.range_resolution_m,
            angle_deg=0.0,
            amplitude=1.0,
            phase_bias_rad=0.0,
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=(scatterer,))
        range_angle = range_angle_process(adc, frontend_config)
        power_by_range = np.sum(np.abs(range_angle.range_angle_cube[0]) ** 2, axis=1)

        self.assertEqual(int(np.argmax(power_by_range)), target_range_bin)
        self.assertAlmostEqual(range_angle.range_axis_m[target_range_bin], scatterer.range_m)

    def test_angle_axis_uses_spatial_frequency(self):
        truth = _static_truth()
        config = Phase1Config(seed=503)
        frontend_config = FrontendConfig(
            num_virtual_rx=8,
            num_adc_samples=16,
            num_range_bins=16,
            num_angle_bins=8,
            antenna_spacing_wavelengths=0.5,
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=())
        range_angle = range_angle_process(adc, frontend_config)
        expected_spatial_frequency = np.fft.fftshift(np.fft.fftfreq(8, d=1.0))
        expected_angle_deg = np.rad2deg(np.arcsin(expected_spatial_frequency / 0.5))

        np.testing.assert_allclose(range_angle.spatial_frequency_axis, expected_spatial_frequency)
        np.testing.assert_allclose(range_angle.angle_axis_deg, expected_angle_deg)
        self.assertFalse(np.allclose(np.diff(range_angle.angle_axis_deg), np.diff(range_angle.angle_axis_deg)[0]))

    def test_angle_fft_maps_bin_centered_target(self):
        truth = _static_truth()
        config = Phase1Config(seed=504)
        frontend_config = FrontendConfig(
            num_virtual_rx=16,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
            antenna_spacing_wavelengths=0.5,
        )
        spatial_axis = np.fft.fftshift(np.fft.fftfreq(frontend_config.num_angle_bins, d=1.0))
        target_angle_bin = 11
        target_angle_deg = math.degrees(
            math.asin(spatial_axis[target_angle_bin] / frontend_config.antenna_spacing_wavelengths)
        )
        target_range_bin = 5
        scatterer = ScattererTruth(
            range_m=target_range_bin * frontend_config.range_resolution_m,
            angle_deg=target_angle_deg,
            amplitude=1.0,
            phase_bias_rad=0.0,
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=(scatterer,))
        range_angle = range_angle_process(adc, frontend_config)
        power_by_angle = np.abs(range_angle.range_angle_cube[0, target_range_bin]) ** 2

        self.assertEqual(int(np.argmax(power_by_angle)), target_angle_bin)

    def test_frontend_phase_matches_radar_oracle_single_target(self):
        config = Phase1Config(
            duration_s=0.08,
            sample_rate_hz=1000.0,
            seed=505,
            num_targets=1,
            target_angles_deg=(0.0,),
            target_snr_db=(320.0,),
            target_amplitudes=(1.0,),
        )
        truth = generate_multifrequency_truth(config)
        frontend_config = FrontendConfig(
            num_virtual_rx=8,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
        )

        radar = simulate_radar_targets(truth, config)
        adc = simulate_adc_cube(truth, config, frontend_config)
        range_angle = range_angle_process(adc, frontend_config)
        scatterer = adc.scatterers[0]
        target = extract_frontend_target_observation(
            range_angle,
            range_bins=(scatterer.range_bin_index,),
            angle_bins=(frontend_config.num_angle_bins // 2,),
        )

        phase_error = wrap_to_pi(target.wrapped_phase_rad[0] - radar.wrapped_phase_rad[0])
        self.assertLess(np.max(np.abs(phase_error)), 1e-8)

    def test_frontend_target_degradation_reduces_iq_quality_inside_window(self):
        clean_config = Phase1Config(
            duration_s=0.6,
            sample_rate_hz=1000.0,
            seed=508,
            num_targets=1,
            target_angles_deg=(0.0,),
            target_snr_db=(30.0,),
            target_amplitudes=(1.0,),
        )
        degraded_config = Phase1Config(
            duration_s=0.6,
            sample_rate_hz=1000.0,
            seed=508,
            num_targets=1,
            target_angles_deg=(0.0,),
            target_snr_db=(30.0,),
            target_amplitudes=(1.0,),
            degraded_target_indices=(0,),
            degradation_start_s=0.2,
            degradation_end_s=0.4,
            degradation_snr_drop_db=35.0,
        )
        truth = generate_multifrequency_truth(clean_config)
        frontend_config = FrontendConfig(num_virtual_rx=8, num_adc_samples=32, num_range_bins=32, num_angle_bins=16)

        clean_adc = simulate_adc_cube(truth, clean_config, frontend_config)
        degraded_adc = simulate_adc_cube(truth, degraded_config, frontend_config)
        clean_ra = range_angle_process(clean_adc, frontend_config)
        degraded_ra = range_angle_process(degraded_adc, frontend_config)
        target_bin = clean_adc.scatterers[0].range_bin_index
        angle_bin = frontend_config.num_angle_bins // 2
        clean_target = extract_frontend_target_observation(clean_ra, (target_bin,), (angle_bin,))
        degraded_target = extract_frontend_target_observation(degraded_ra, (target_bin,), (angle_bin,))

        in_drop = (truth.t >= degraded_config.degradation_start_s) & (truth.t <= degraded_config.degradation_end_s)
        outside = ~in_drop
        residual = degraded_target.slow_time[0] - clean_target.slow_time[0]

        self.assertGreater(np.std(residual[in_drop]), 5.0 * np.std(residual[outside]))

    def test_phase1_snr_is_calibrated_after_range_angle_processing(self):
        truth = _static_truth(num_frames=4000)
        config = Phase1Config(seed=511)
        frontend_config = FrontendConfig(
            num_virtual_rx=8,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
            antenna_spacing_wavelengths=0.5,
        )
        scatterer = ScattererTruth(
            range_m=5 * frontend_config.range_resolution_m,
            angle_deg=0.0,
            amplitude=1.0,
            phase_bias_rad=0.0,
            snr_db=24.0,
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=(scatterer,))
        range_angle = range_angle_process(adc, frontend_config)
        target = extract_frontend_target_observation(
            range_angle,
            range_bins=(5,),
            angle_bins=(frontend_config.num_angle_bins // 2,),
        )

        phase_noise_std = float(np.std(wrap_to_pi(target.wrapped_phase_rad[0])))

        self.assertGreater(phase_noise_std, 0.02)
        self.assertLess(phase_noise_std, 0.08)

    def test_scenario_aoa_error_changes_frontend_measured_kappa(self):
        config = Phase1Config(
            duration_s=0.08,
            sample_rate_hz=1000.0,
            seed=512,
            num_targets=1,
            target_angles_deg=(40.0,),
            target_snr_db=(120.0,),
            target_amplitudes=(1.0,),
            aoa_error_deg=10.0,
        )
        truth = generate_multifrequency_truth(config)
        accelerometer = build_accelerometer_observation(truth, config)

        frontend = build_frontend_views(truth, accelerometer, config)
        measured_angle_deg = frontend.frontend_targets.angle_deg + config.aoa_error_deg
        expected = angle_deg_to_measured_kappa(measured_angle_deg)
        unperturbed = angle_deg_to_measured_kappa(frontend.frontend_targets.angle_deg)

        np.testing.assert_allclose(frontend.frontend_targets.measured_kappa, expected)
        self.assertGreater(
            float(np.max(np.abs(frontend.frontend_targets.measured_kappa - unperturbed))),
            1.0e-3,
        )

    def test_frontend_dropout_removes_target_power_inside_window(self):
        config = Phase1Config(
            duration_s=0.6,
            sample_rate_hz=1000.0,
            seed=509,
            num_targets=1,
            target_angles_deg=(0.0,),
            target_snr_db=(80.0,),
            target_amplitudes=(1.0,),
            dropout_target_indices=(0,),
            dropout_start_s=0.2,
            dropout_end_s=0.4,
        )
        truth = generate_multifrequency_truth(config)
        frontend_config = FrontendConfig(num_virtual_rx=8, num_adc_samples=32, num_range_bins=32, num_angle_bins=16)

        adc = simulate_adc_cube(truth, config, frontend_config)
        range_angle = range_angle_process(adc, frontend_config)
        target_bin = adc.scatterers[0].range_bin_index
        angle_bin = frontend_config.num_angle_bins // 2
        target = extract_frontend_target_observation(
            range_angle,
            (target_bin,),
            (angle_bin,),
            magnitude_threshold=0.2,
        )

        in_dropout = (truth.t >= config.dropout_start_s) & (truth.t <= config.dropout_end_s)
        outside = ~in_dropout

        self.assertLess(np.mean(np.abs(target.slow_time[0, in_dropout])), 0.1)
        self.assertGreater(np.mean(np.abs(target.slow_time[0, outside])), 0.9)
        self.assertLess(np.mean(target.available_mask[0, in_dropout]), 0.1)
        self.assertGreater(np.mean(target.available_mask[0, outside]), 0.9)

    def test_same_range_different_angles_are_separated(self):
        truth = _static_truth(num_frames=3)
        config = Phase1Config(seed=506)
        frontend_config = FrontendConfig(
            num_virtual_rx=16,
            num_adc_samples=32,
            num_range_bins=32,
            num_angle_bins=16,
            antenna_spacing_wavelengths=0.5,
        )
        spatial_axis = np.fft.fftshift(np.fft.fftfreq(frontend_config.num_angle_bins, d=1.0))
        angle_bins = (6, 11)
        angles_deg = tuple(
            math.degrees(math.asin(spatial_axis[idx] / frontend_config.antenna_spacing_wavelengths))
            for idx in angle_bins
        )
        range_bin = 9
        scatterers = tuple(
            ScattererTruth(
                range_m=range_bin * frontend_config.range_resolution_m,
                angle_deg=angle_deg,
                amplitude=1.0,
                phase_bias_rad=0.0,
            )
            for angle_deg in angles_deg
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=scatterers)
        range_angle = range_angle_process(adc, frontend_config)
        power_by_angle = np.abs(range_angle.range_angle_cube[0, range_bin]) ** 2
        strongest = set(np.argsort(power_by_angle)[-2:])

        self.assertEqual(strongest, set(angle_bins))
        for angle_bin in angle_bins:
            self.assertGreater(power_by_angle[angle_bin], np.median(power_by_angle) * 100.0)

    def test_frontend_to_algorithm_input_hides_truth_fields(self):
        truth = _static_truth()
        config = Phase1Config(seed=507)
        frontend_config = FrontendConfig(num_angle_bins=16)
        scatterer = ScattererTruth(
            range_m=3 * frontend_config.range_resolution_m,
            angle_deg=0.0,
            amplitude=1.0,
            phase_bias_rad=0.0,
        )

        adc = simulate_adc_cube(truth, config, frontend_config, scatterers=(scatterer,))
        range_angle = range_angle_process(adc, frontend_config)
        target = extract_frontend_target_observation(
            range_angle,
            range_bins=(3,),
            angle_bins=(frontend_config.num_angle_bins // 2,),
        )
        radar_input = to_algorithm_radar_input(target)

        self.assertIsInstance(radar_input, RadarAlgorithmInput)
        self.assertFalse(hasattr(radar_input, "truth"))
        self.assertFalse(hasattr(radar_input, "kappa"))
        self.assertFalse(hasattr(radar_input, "true_kappa"))
        self.assertFalse(hasattr(radar_input, "true_los_phase_rad"))
        self.assertFalse(hasattr(radar_input, "q_m"))
        self.assertFalse(hasattr(radar_input, "slow_time"))
        np.testing.assert_allclose(radar_input.measured_kappa, target.measured_kappa)
        np.testing.assert_allclose(radar_input.wrapped_phase_rad, target.wrapped_phase_rad)
        np.testing.assert_array_equal(radar_input.available_mask, target.available_mask)


if __name__ == "__main__":
    unittest.main()
