"""Observable physics checks for the paper-parameterized capture package.

These tests deliberately consume the same files as ``algorithm.run``.  They
do not inspect private simulation state: a generated package is the boundary
between the physical model and the retained algorithm.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from paper_bridge_simulation import package_builder


class PhysicalSimulationTest(unittest.TestCase):
    """Check the radar/ADXL arrays and the physical relationships they encode."""

    @classmethod
    def setUpClass(cls):
        cls._temporary = tempfile.TemporaryDirectory(prefix="physical-sim-tests-")
        cls.root = Path(cls._temporary.name) / "capture"
        # Half a second contains enough modal motion to test phase while
        # keeping this test independent of the four-second reference run.
        package_builder.generate(cls.root, duration_s=0.5, seed=2026)
        cls.radar_dir = cls.root / "radar" / "algorithm_input"
        cls.adxl_dir = cls.root / "adxl355" / "algorithm_input"
        cls.radar_manifest = json.loads((cls.radar_dir / "manifest.json").read_text())
        cls.adxl_manifest = json.loads((cls.adxl_dir / "manifest.json").read_text())
        cls.radar_meta = cls.radar_manifest["radar"]
        cls.chirp = np.load(cls.radar_dir / cls.radar_manifest["arrays"]["chirp_cube"]["file"])
        cls.adc = np.load(cls.radar_dir / cls.radar_manifest["arrays"]["adc_cube"]["file"])
        cls.frame_times_s = np.load(
            cls.radar_dir / cls.radar_manifest["arrays"]["frame_times_s"]["file"]
        )
        cls.truth_q = np.load(cls.root / "truth" / "displacement_m.npy")
        cls.truth_t_ns = np.load(cls.root / "truth" / "time_ns.npy")
        cls.truth_t_s = (cls.truth_t_ns - cls.truth_t_ns[0]) * 1.0e-9

    @classmethod
    def tearDownClass(cls):
        cls._temporary.cleanup()

    @classmethod
    def _fft(cls):
        window = np.hanning(cls.chirp.shape[-1])
        # ADC IQ is complex, so use a complex FFT (rfft only accepts real
        # input).  The configured beat tones occupy bins 0..N-1.
        return np.fft.fft(cls.chirp * window[None, None, None, :], axis=-1)

    @classmethod
    def _target_bins(cls):
        bins = cls.radar_meta.get("target_range_bins")
        if bins is None:
            bins = package_builder.TARGET_RANGE_BINS.tolist()
        return np.asarray(bins, dtype=int)

    def test_capture_package_contract_and_timing_arrays(self):
        self.assertEqual(self.radar_manifest["schema"], "mmwavecapture.algorithm-input")
        self.assertEqual(self.radar_manifest["schema_version"], 1)
        self.assertTrue(self.radar_manifest["packet_integrity"]["complete"])
        self.assertEqual(self.chirp.dtype, np.dtype("complex64"))
        self.assertEqual(self.adc.dtype, np.dtype("complex64"))
        self.assertEqual(self.chirp.ndim, 4)
        self.assertEqual(self.adc.shape, (self.chirp.shape[0], self.chirp.shape[2], self.chirp.shape[3]))
        np.testing.assert_allclose(self.adc, np.mean(self.chirp, axis=1), rtol=0.0, atol=2.0e-6)

        sync = json.loads((self.root / "sync" / "timeline.json").read_text())
        timeline = np.load(self.root / "sync" / sync["array"]["file"])
        self.assertEqual(timeline.dtype, np.dtype("int64"))
        self.assertEqual(timeline.size, self.chirp.shape[0])
        self.assertTrue(np.all(np.diff(timeline) > 0))
        self.assertEqual(self.adxl_manifest["schema"], "mmwavecapture.adxl355-input")
        self.assertTrue(self.adxl_manifest["capture"]["complete"])
        adxl_times = np.load(self.adxl_dir / self.adxl_manifest["arrays"]["estimated_sample_monotonic_ns"]["file"])
        self.assertTrue(np.all(np.diff(adxl_times) > 0))

    def test_fmcw_range_peaks_are_at_scene_ranges(self):
        """The fast-time beat tones map to c*Fs/(2*S*N) range bins."""
        spectrum_power = np.mean(np.abs(self._fft()) ** 2, axis=(0, 1, 2))
        peak_order = np.argsort(spectrum_power)[::-1]
        expected = self._target_bins()
        self.assertGreater(expected.size, 0)
        # A Hann-windowed bin can split over two adjacent bins.  Every moving
        # scene return must still be represented in the strongest range bins.
        for target_bin in expected:
            distance = np.min(np.abs(peak_order[:40] - target_bin))
            self.assertLessEqual(distance, 2, msg=f"missing range peak near bin {target_bin}")

        resolution = float(self.radar_meta["range_resolution_m"])
        slope = float(self.radar_meta["chirp_slope_hz_per_s"])
        sample_rate = float(self.radar_meta["adc_sample_rate_hz"])
        samples = int(self.radar_meta["adc_samples_per_chirp"])
        expected_resolution = package_builder.C_LIGHT_MPS * sample_rate / (2.0 * slope * samples)
        self.assertAlmostEqual(resolution, expected_resolution, places=12)

    def test_propagation_phase_increment_tracks_radial_q(self):
        """A fixed-world reference phase follows 4*pi*cos(theta)*q/lambda."""
        target_number = 2  # isolated from the neighboring first two bins
        target_bin = int(self._target_bins()[target_number])
        angle_deg = float(np.asarray(self.radar_manifest["source"]["target_angles_deg"])[target_number])
        wavelength = float(self.radar_meta.get("wavelength_m", package_builder.WAVELENGTH_M))
        q = np.interp(self.frame_times_s, self.truth_t_s, self.truth_q)
        coefficient = self._fft()[:, :, 0, target_bin]
        measured = np.mean(coefficient, axis=1)
        expected_slope = 4.0 * np.pi * np.cos(np.deg2rad(angle_deg)) / wavelength
        # Remove the arbitrary target phase and compare on the unit circle,
        # which remains valid when the accumulated phase crosses +/-pi.
        residual = np.angle(np.exp(1j * (np.unwrap(np.angle(measured)) - expected_slope * q)))
        self.assertGreater(float(np.abs(np.mean(np.exp(1j * residual)))), 0.45)

    def test_fixed_world_scatterer_phase_follows_radar_motion_slope(self):
        """A world-fixed return changes range when the radar follows q(t)."""
        scene = self.radar_manifest["source"].get("scene", {})
        scatterers = scene.get("static_scatterers", scene.get("fixed_world_scatterers", []))
        self.assertTrue(scatterers, "manifest must describe at least one fixed-world scatterer")
        scatterer = scatterers[0]
        target_range = float(scatterer.get("range_m", scatterer.get("range")))
        angle_deg = float(scatterer.get("angle_deg", scatterer.get("angle", 0.0)))
        target_bin = int(np.rint(target_range / float(self.radar_meta["range_resolution_m"])))
        target_bin = min(max(target_bin, 0), self.chirp.shape[-1] - 1)
        q = np.interp(self.frame_times_s, self.truth_t_s, self.truth_q)
        measured = np.mean(self._fft()[:, :, 0, target_bin], axis=1)
        expected_slope = 4.0 * np.pi * np.cos(np.deg2rad(angle_deg)) / float(
            self.radar_meta.get("wavelength_m", package_builder.WAVELENGTH_M)
        )
        residual = np.angle(np.exp(1j * (np.unwrap(np.angle(measured)) - expected_slope * q)))
        self.assertGreater(float(np.abs(np.mean(np.exp(1j * residual)))), 0.20)

    def test_tdm_schedule_matches_two_tx_profile(self):
        loops = int(self.radar_meta["chirp_loops_per_frame"])
        tx_per_loop = int(self.radar_meta["tx_chirps_per_loop"])
        self.assertEqual(tx_per_loop, 2)
        self.assertEqual(self.chirp.shape[1], loops)
        self.assertEqual(int(self.radar_meta["physical_chirps_per_frame"]), loops * tx_per_loop)
        cycle = float(self.radar_meta["chirp_cycle_time_s"])
        loop_interval = float(self.radar_meta["loop_start_interval_s"])
        self.assertAlmostEqual(loop_interval, tx_per_loop * cycle, places=15)
        tx_offsets = np.asarray(self.radar_meta.get("tx_chirp_offsets_s", (0.0, cycle)), dtype=float)
        self.assertEqual(tx_offsets.shape, (2,))
        self.assertAlmostEqual(float(tx_offsets[1] - tx_offsets[0]), cycle, places=15)
        self.assertEqual(list(self.radar_meta["tx_indices"]), [0, 2])

    def test_adc_levels_are_integer_quantized_and_saturation_counts_match(self):
        quant = self.radar_meta.get("adc_quantization", self.radar_meta)
        bits = int(quant["bits"])
        full_scale = float(quant["full_scale_v"])
        lsb = float(quant["lsb_v"])
        self.assertEqual(bits, int(self.radar_meta.get("adc_bits", bits)))
        self.assertAlmostEqual(lsb, 2.0 * full_scale / (2**bits), places=15)
        # The saved frame cube is a coherent mean of 16 quantized loop
        # snapshots, so its levels are fractional LSBs.  Quantization is
        # checked on the lossless chirp cube instead.
        i = np.real(self.chirp).astype(float)
        q = np.imag(self.chirp).astype(float)
        np.testing.assert_allclose(i / lsb, np.rint(i / lsb), atol=2.0e-4)
        np.testing.assert_allclose(q / lsb, np.rint(q / lsb), atol=2.0e-4)
        self.assertLessEqual(float(np.max(i)), full_scale - lsb + 2.0e-6)
        self.assertGreaterEqual(float(np.min(i)), -full_scale - 2.0e-6)
        self.assertLessEqual(float(np.max(q)), full_scale - lsb + 2.0e-6)
        self.assertGreaterEqual(float(np.min(q)), -full_scale - 2.0e-6)
        i_sat = int(np.count_nonzero((i <= -full_scale + lsb / 4.0) | (i >= full_scale - lsb - lsb / 4.0)))
        q_sat = int(np.count_nonzero((q <= -full_scale + lsb / 4.0) | (q >= full_scale - lsb - lsb / 4.0)))
        self.assertEqual(int(quant["saturated_i_count"]), i_sat)
        self.assertEqual(int(quant["saturated_q_count"]), q_sat)

    def test_seed_repeats_adc_and_noise_exactly(self):
        with tempfile.TemporaryDirectory(prefix="physical-sim-repeat-") as temporary:
            repeat = Path(temporary) / "capture"
            package_builder.generate(repeat, duration_s=0.5, seed=2026)
            np.testing.assert_array_equal(self.adc, np.load(repeat / "radar" / "algorithm_input" / "adc_cube.npy"))
            np.testing.assert_array_equal(self.chirp, np.load(repeat / "radar" / "algorithm_input" / "chirp_cube.npy"))
            changed = Path(temporary) / "changed"
            package_builder.generate(changed, duration_s=0.5, seed=2027)
            self.assertFalse(np.array_equal(self.adc, np.load(changed / "radar" / "algorithm_input" / "adc_cube.npy")))


if __name__ == "__main__":
    unittest.main()
