import unittest
from dataclasses import dataclass

import numpy as np

from simulation.phase1.algorithm import run_structural_phase_kalman
from simulation.phase1.config import Phase1Config
from simulation.phase1.fusion_adapter import preintegrate_acceleration_to_radar
from simulation.phase1.radar import RadarAlgorithmInput


@dataclass(frozen=True)
class _CapturedAcceleration:
    measured_mps2: np.ndarray
    preintegration: object


class Phase1AsyncAlgorithmTest(unittest.TestCase):
    def test_irregular_radar_intervals_consume_native_adxl_preintegration(self):
        radar_time_ns = np.array([1_000_000_000, 1_100_000_000, 1_250_000_000], dtype=np.int64)
        adxl_time_ns = np.arange(1_000_000_000, 1_250_000_001, 10_000_000, dtype=np.int64)
        acceleration = np.full(adxl_time_ns.shape, 2.0, dtype=float)
        preintegration = preintegrate_acceleration_to_radar(
            radar_time_ns,
            adxl_time_ns,
            acceleration,
            np.ones(adxl_time_ns.shape, dtype=bool),
            max_allowed_gap_ns=10_000_000,
        )
        accel = _CapturedAcceleration(
            measured_mps2=np.full(radar_time_ns.shape, 2.0, dtype=float),
            preintegration=preintegration,
        )
        radar = RadarAlgorithmInput(
            measured_beta=np.array([1.0]),
            wrapped_phase_rad=np.full((1, radar_time_ns.size), np.nan),
            available_mask=np.zeros((1, radar_time_ns.size), dtype=bool),
        )
        config = Phase1Config(
            sample_rate_hz=10.0,
            num_targets=1,
            process_noise_intensity=1.0e-12,
        )

        result = run_structural_phase_kalman(
            method_name="async_test",
            radar=radar,
            accel=accel,
            config=config,
            initial_beta=np.array([1.0]),
            update_beta=False,
            adaptive_r=False,
        )

        np.testing.assert_allclose(result.q_hat_m, [0.0, 0.01, 0.0625], atol=1.0e-12)
        np.testing.assert_allclose(
            result.extra["transition_duration_s"],
            [0.1, 0.15],
            atol=1.0e-15,
        )
        self.assertEqual(result.extra["propagation_timing"], "native_timestamp_preintegration")

    def test_invalid_preintegration_is_rejected_before_filtering(self):
        class _InvalidPreintegration:
            duration_s = np.array([0.1])
            delta_v_mps = np.array([0.0])
            delta_q_m = np.array([0.0])
            interval_valid = np.array([False])

        radar = RadarAlgorithmInput(
            measured_beta=np.array([1.0]),
            wrapped_phase_rad=np.full((1, 2), np.nan),
            available_mask=np.zeros((1, 2), dtype=bool),
        )
        accel = _CapturedAcceleration(
            measured_mps2=np.zeros(2),
            preintegration=_InvalidPreintegration(),
        )

        with self.assertRaisesRegex(ValueError, "invalid radar interval"):
            run_structural_phase_kalman(
                method_name="async_invalid",
                radar=radar,
                accel=accel,
                config=Phase1Config(num_targets=1),
                initial_beta=np.array([1.0]),
                update_beta=False,
                adaptive_r=False,
            )


if __name__ == "__main__":
    unittest.main()
