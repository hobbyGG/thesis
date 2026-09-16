import unittest

import numpy as np

from simulation.phase1.fusion_adapter import (
    FusionAdapterError,
    FusionCoverageError,
    preintegrate_acceleration_to_radar,
)


class Phase1FusionAdapterTest(unittest.TestCase):
    def test_constant_acceleration_integrates_across_irregular_native_rates(self):
        radar_time_ns = np.array([0, 1_000_000_000, 2_500_000_000], dtype=np.int64)
        adxl_time_ns = np.array(
            [
                0,
                200_000_000,
                550_000_000,
                1_000_000_000,
                1_300_000_000,
                1_700_000_000,
                2_000_000_000,
                2_500_000_000,
            ],
            dtype=np.int64,
        )
        acceleration = np.full(adxl_time_ns.shape, 2.0)

        result = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            acceleration,
            np.ones(adxl_time_ns.shape, dtype=bool),
            max_allowed_gap_ns=500_000_000,
        )

        np.testing.assert_allclose(result.duration_s, [1.0, 1.5], atol=0.0, rtol=0.0)
        np.testing.assert_allclose(result.delta_v_mps, [2.0, 3.0], atol=1.0e-15, rtol=0.0)
        np.testing.assert_allclose(result.delta_q_m, [1.0, 2.25], atol=1.0e-15, rtol=0.0)
        np.testing.assert_array_equal(result.interval_valid, [True, True])
        self.assertEqual(result.source_indices, ((0, 1, 2, 3), (3, 4, 5, 6, 7)))
        np.testing.assert_array_equal(result.max_observed_gap_ns, [450_000_000, 500_000_000])

    def test_linear_acceleration_is_integrated_exactly_without_losing_epoch_precision(self):
        epoch_ns = 8_000_000_000_000_000
        radar_time_ns = np.array([epoch_ns, epoch_ns + 2_000_000_000], dtype=np.int64)
        offsets_ns = np.array(
            [-250_000_000, 0, 350_000_000, 900_000_000, 1_400_000_000, 2_000_000_000],
            dtype=np.int64,
        )
        adxl_time_ns = epoch_ns + offsets_ns
        acceleration = offsets_ns.astype(float) * 1.0e-9

        result = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            acceleration,
            np.ones(adxl_time_ns.shape, dtype=bool),
            max_allowed_gap_ns=600_000_000,
        )

        self.assertEqual(result.radar_start_time_ns[0], epoch_ns)
        self.assertEqual(result.radar_end_time_ns[0], epoch_ns + 2_000_000_000)
        self.assertAlmostEqual(result.delta_v_mps[0], 2.0, places=14)
        self.assertAlmostEqual(result.delta_q_m[0], 4.0 / 3.0, places=14)

    def test_masked_sample_creates_observed_gap_and_invalid_numeric_outputs(self):
        radar_time_ns = np.array([0, 4_000_000], dtype=np.int64)
        adxl_time_ns = np.arange(5, dtype=np.int64) * 1_000_000
        acceleration = np.ones(5)
        valid_mask = np.array([True, True, False, True, True])

        result = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            acceleration,
            valid_mask,
            max_allowed_gap_ns=1_500_000,
            fail_on_invalid_interval=False,
        )

        np.testing.assert_array_equal(result.coverage_complete, [True])
        np.testing.assert_allclose(result.coverage_fraction, [1.0])
        np.testing.assert_array_equal(result.max_observed_gap_ns, [2_000_000])
        np.testing.assert_array_equal(result.gap_within_limit, [False])
        np.testing.assert_array_equal(result.interval_valid, [False])
        self.assertEqual(result.source_indices, ((0, 1, 3, 4),))
        self.assertTrue(np.isnan(result.delta_v_mps[0]))
        self.assertTrue(np.isnan(result.delta_q_m[0]))
        with self.assertRaisesRegex(FusionCoverageError, r"interval\(s\): 0"):
            result.require_all_valid()

    def test_default_mode_fails_closed_when_adxl_does_not_cover_radar_interval(self):
        radar_time_ns = np.array([0, 10_000_000], dtype=np.int64)
        adxl_time_ns = np.array([5_000_000, 10_000_000], dtype=np.int64)

        with self.assertRaises(FusionCoverageError) as caught:
            preintegrate_acceleration_to_radar(
                radar_time_ns,
                adxl_time_ns,
                np.ones(2),
                np.ones(2, dtype=bool),
                max_allowed_gap_ns=10_000_000,
            )

        self.assertEqual(caught.exception.invalid_interval_indices, (0,))

        diagnostic = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            np.ones(2),
            np.ones(2, dtype=bool),
            max_allowed_gap_ns=10_000_000,
            fail_on_invalid_interval=False,
        )
        np.testing.assert_allclose(diagnostic.coverage_fraction, [0.5])
        np.testing.assert_array_equal(diagnostic.coverage_complete, [False])
        self.assertEqual(diagnostic.source_indices, ((),))
        self.assertTrue(np.isnan(diagnostic.delta_v_mps[0]))

    def test_inputs_are_not_modified_and_results_retain_native_timestamps(self):
        radar_time_ns = np.array([100, 200, 350], dtype=np.int64)
        adxl_time_ns = np.array([50, 100, 150, 200, 275, 350, 400], dtype=np.int64)
        acceleration = np.array([0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0])
        valid_mask = np.ones(7, dtype=bool)
        inputs = (radar_time_ns, adxl_time_ns, acceleration, valid_mask)
        originals = tuple(value.copy() for value in inputs)

        result = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            acceleration,
            valid_mask,
            max_allowed_gap_ns=75,
        )

        for value, original in zip(inputs, originals):
            np.testing.assert_array_equal(value, original)
        np.testing.assert_array_equal(result.radar_start_time_ns, [100, 200])
        np.testing.assert_array_equal(result.radar_end_time_ns, [200, 350])
        self.assertFalse(result.radar_start_time_ns.flags.writeable)
        self.assertFalse(result.delta_v_mps.flags.writeable)

    def test_rejects_non_integer_or_non_monotonic_time_and_bad_valid_samples(self):
        valid_adxl_time = np.array([0, 10, 20], dtype=np.int64)
        valid_acceleration = np.ones(3)
        valid_mask = np.ones(3, dtype=bool)

        invalid_cases = (
            (
                np.array([0.0, 10.0]),
                valid_adxl_time,
                valid_acceleration,
                valid_mask,
                "integer nanoseconds",
            ),
            (
                np.array([0, 10], dtype=np.int64),
                np.array([0, 10, 10], dtype=np.int64),
                valid_acceleration,
                valid_mask,
                "strictly increasing",
            ),
            (
                np.array([0, 10], dtype=np.int64),
                valid_adxl_time,
                np.array([1.0, np.nan, 1.0]),
                valid_mask,
                "must be finite",
            ),
        )
        for radar, adxl, acceleration, mask, expected in invalid_cases:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(FusionAdapterError, expected):
                    preintegrate_acceleration_to_radar(
                        radar,
                        adxl,
                        acceleration,
                        mask,
                        max_allowed_gap_ns=10,
                    )


if __name__ == "__main__":
    unittest.main()
