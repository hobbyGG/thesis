import unittest

import numpy as np

from simulation.phase1.frontend import (
    ADCCubeObservation,
    FrontendConfig,
    range_angle_process,
)


class Phase1CalibratedFrontendTest(unittest.TestCase):
    def test_nonuniform_calibrated_array_uses_geometry_aware_beamforming(self):
        positions = np.array([0.0, 0.5, 1.5])
        target_angle_deg = 30.0
        num_adc_samples = 16
        range_bin = 3
        fast_time = np.exp(
            2j
            * np.pi
            * range_bin
            * np.arange(num_adc_samples)
            / num_adc_samples
        )
        array_tone = np.exp(
            2j * np.pi * positions * np.sin(np.deg2rad(target_angle_deg))
        )
        cube = array_tone[None, :, None] * fast_time[None, None, :]
        calibrated_range_axis = np.arange(num_adc_samples) * 0.1 - 0.02
        adc = ADCCubeObservation(
            adc_cube=cube,
            range_axis_m=calibrated_range_axis,
            frame_times_s=np.array([0.0]),
            scatterers=(),
        )
        config = FrontendConfig(
            num_virtual_rx=3,
            virtual_array_positions_wavelengths=tuple(positions),
            num_adc_samples=num_adc_samples,
            num_range_bins=num_adc_samples,
            num_angle_bins=64,
            antenna_spacing_wavelengths=0.5,
            angle_window="rect",
        )

        observation = range_angle_process(adc, config)

        peak = np.unravel_index(
            int(np.argmax(np.abs(observation.range_angle_cube[0]))),
            observation.range_angle_cube[0].shape,
        )
        self.assertEqual(peak[0], range_bin)
        self.assertAlmostEqual(observation.angle_axis_deg[peak[1]], target_angle_deg)
        np.testing.assert_allclose(
            observation.range_axis_m,
            calibrated_range_axis,
        )

    def test_rejects_range_axis_that_cannot_describe_fft_bins(self):
        adc = ADCCubeObservation(
            adc_cube=np.zeros((1, 2, 4), dtype=complex),
            range_axis_m=np.zeros(3),
            frame_times_s=np.array([0.0]),
            scatterers=(),
        )

        with self.assertRaisesRegex(ValueError, "range_axis_m"):
            range_angle_process(
                adc,
                FrontendConfig(
                    num_virtual_rx=2,
                    num_adc_samples=4,
                    num_range_bins=4,
                ),
            )


if __name__ == "__main__":
    unittest.main()
