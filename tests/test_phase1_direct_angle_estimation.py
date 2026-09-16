import unittest

import numpy as np

from simulation.phase1.angle_estimation import estimate_local_music_ml


class DirectAngleEstimationTest(unittest.TestCase):
    @staticmethod
    def _snapshots(positions, angles_deg, *, snapshots=256, snr_db=80.0, seed=7):
        positions = np.asarray(positions, dtype=float)
        angles_deg = np.asarray(angles_deg, dtype=float)
        rng = np.random.default_rng(seed)
        t = np.arange(snapshots, dtype=float)
        # Independent complex slow-time envelopes make same-range sources
        # identifiable by their spatial steering vectors.
        freqs = 0.017 + 0.011 * np.arange(angles_deg.size, dtype=float)
        envelopes = np.exp(1j * (freqs[:, None] * t[None, :] + rng.uniform(-np.pi, np.pi, (angles_deg.size, 1))))
        envelopes *= 1.0 + 0.1 * np.exp(1j * 2.0 * np.pi * (0.013 + 0.007 * np.arange(angles_deg.size))[:, None] * t[None, :])
        steering = np.exp(2j * np.pi * positions[:, None] * np.sin(np.deg2rad(angles_deg))[None, :])
        x = steering @ envelopes
        if np.isfinite(snr_db):
            noise_std = np.sqrt(np.mean(np.abs(x) ** 2) / 10.0 ** (snr_db / 10.0) / 2.0)
            x = x + noise_std * (rng.standard_normal(x.shape) + 1j * rng.standard_normal(x.shape))
        return x

    def test_off_grid_single_source_is_continuous_and_beats_fft_grid(self):
        positions = np.arange(8, dtype=float) * 0.5
        true_angle = 17.35
        snapshots = self._snapshots(positions, [true_angle], snapshots=512)
        result = estimate_local_music_ml(
            snapshots,
            positions,
            coarse_angles_deg=[17.0],
            search_half_width_u=0.10,
            music_grid_size=129,
            max_snapshots=512,
        )
        estimate = float(np.asarray(result.angles_deg).reshape(-1)[0])
        self.assertEqual(result.source_slow_time.shape, (1, snapshots.shape[1]))
        # A 64-bin Angle FFT has a much coarser, nonuniform angle grid here;
        # the direct estimator should recover the off-grid source accurately.
        self.assertLess(abs(estimate - true_angle), 0.20)
        self.assertLess(abs(estimate - true_angle), 0.5)
        self.assertTrue(np.isfinite(result.angles_deg).all())
        self.assertTrue(all(np.isfinite(d["residual_power"]) for d in result.diagnostics))

    def test_same_range_two_sources_are_not_collapsed_to_mixture_peak(self):
        positions = np.arange(8, dtype=float) * 0.5
        true_angles = np.array([-21.4, 24.7])
        snapshots = self._snapshots(positions, true_angles, snapshots=512, seed=8)
        result = estimate_local_music_ml(
            snapshots,
            positions,
            coarse_angles_deg=true_angles + np.array([1.0, -1.0]),
            search_half_width_u=0.12,
            music_grid_size=161,
            max_snapshots=512,
        )
        estimates = np.sort(np.asarray(result.angles_deg, dtype=float).reshape(-1))
        self.assertEqual(estimates.size, 2)
        self.assertLess(abs(estimates[0] - true_angles[0]), 0.5)
        self.assertLess(abs(estimates[1] - true_angles[1]), 0.5)
        # Explicitly guard against returning one source at the midpoint.
        self.assertGreater(np.min(np.abs(estimates - np.mean(true_angles))), 10.0)

    def test_nonuniform_geometry_is_used_directly(self):
        positions = np.array([0.0, 0.5, 1.15, 1.95, 2.5, 3.4, 4.05, 5.1])
        true_angle = -28.6
        snapshots = self._snapshots(positions, [true_angle], snapshots=384, seed=9)
        result = estimate_local_music_ml(
            snapshots,
            positions,
            coarse_angles_deg=[-29.0],
            search_half_width_u=0.10,
            music_grid_size=129,
            max_snapshots=384,
        )
        estimate = float(np.asarray(result.angles_deg).reshape(-1)[0])
        self.assertLess(abs(estimate - true_angle), 0.30)

    def test_invalid_or_empty_snapshots_fail_explicitly(self):
        positions = np.arange(8, dtype=float) * 0.5
        with self.assertRaises(ValueError):
            estimate_local_music_ml(
                np.zeros((8, 0), dtype=complex), positions, coarse_angles_deg=[0.0]
            )
        with self.assertRaises(ValueError):
            estimate_local_music_ml(
                np.full((8, 32), np.nan + 1j * np.nan), positions, coarse_angles_deg=[0.0]
            )

    def test_no_truth_or_acceleration_argument_in_public_signature(self):
        import inspect

        parameters = inspect.signature(estimate_local_music_ml).parameters
        self.assertNotIn("truth", parameters)
        self.assertNotIn("acceleration", parameters)
        self.assertNotIn("beta", parameters)


if __name__ == "__main__":
    unittest.main()

class LocalMusicVariantTest(unittest.TestCase):
    def test_local_music_and_local_music_ml_share_coarse_candidates_and_identify_method(self):
        from simulation.phase1 import angle_estimation as module

        positions = np.arange(8, dtype=float) * 0.5
        snapshots = DirectAngleEstimationTest._snapshots(positions, [13.4], snapshots=128, seed=41)
        coarse = [13.0]
        music = module.estimate_local_music(
            snapshots, positions, coarse, search_half_width_u=0.08, music_grid_size=65
        )
        ml = module.estimate_local_music_ml(
            snapshots, positions, coarse, search_half_width_u=0.08, music_grid_size=65
        )
        self.assertEqual(music.angles_deg.shape, (1,))
        self.assertEqual(ml.angles_deg.shape, (1,))
        self.assertEqual(music.source_slow_time.shape, (1, snapshots.shape[1]))
        self.assertEqual(ml.source_slow_time.shape, (1, snapshots.shape[1]))
        self.assertEqual(music.diagnostics[0]["method"], "local_music")
        self.assertEqual(ml.diagnostics[0]["method"], "local_music_ml")
        # Both variants are constrained to the same local spatial-frequency gate.
        self.assertLess(abs(float(music.angles_deg[0]) - coarse[0]), 15.0)
        self.assertLess(abs(float(ml.angles_deg[0]) - coarse[0]), 15.0)

    def test_local_music_ml_has_no_beta_or_motion_feedback_inputs(self):
        import inspect
        from simulation.phase1.angle_estimation import estimate_local_music

        for estimator in (estimate_local_music, estimate_local_music_ml):
            names = inspect.signature(estimator).parameters
            self.assertNotIn("beta", names)
            self.assertNotIn("truth", names)
            self.assertNotIn("acceleration", names)
