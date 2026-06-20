from pathlib import Path
from types import SimpleNamespace
import os
import unittest
from unittest.mock import patch

import numpy as np

from simulation.phase1.measured_bridge import (
    MeasuredBridgePreprocessConfig,
    _differentiate_displacement,
    _resolve_project_path,
    load_measured_bridge_record,
    preprocess_measured_signal,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TDMS_PATH = Path(os.environ.get("PHASE1_MEASURED_BRIDGE_TDMS", REPO_ROOT / "datafile" / "20250320test12.tdms"))


def _require_measured_bridge_fixture(testcase):
    if os.environ.get("PHASE1_RUN_MEASURED_BRIDGE_TESTS") != "1":
        testcase.skipTest("set PHASE1_RUN_MEASURED_BRIDGE_TESTS=1 to run local TDMS-backed tests")
    if not TDMS_PATH.exists():
        testcase.skipTest(f"TDMS fixture not found: {TDMS_PATH}")


class TestMeasuredBridgePreprocessing(unittest.TestCase):
    def test_powerline_notch_applies_to_laser_and_acceleration(self):
        fs = 1000.0
        t = np.arange(0.0, 4.0, 1.0 / fs)
        structural = np.sin(2.0 * np.pi * 1.0 * t)
        powerline = 0.5 * np.sin(2.0 * np.pi * 50.0 * t)
        config = MeasuredBridgePreprocessConfig(
            analysis_band_hz=(0.2, 80.0),
            powerline_hz=(50.0, 100.0, 150.0),
            powerline_half_width_hz=1.0,
        )

        laser = preprocess_measured_signal(structural + powerline, fs, config)
        accel = preprocess_measured_signal(2.0 * structural + powerline, fs, config)

        freqs = np.fft.rfftfreq(t.size, 1.0 / fs)
        laser_fft = np.abs(np.fft.rfft(laser))
        accel_fft = np.abs(np.fft.rfft(accel))
        idx_1hz = int(np.argmin(np.abs(freqs - 1.0)))
        idx_50hz = int(np.argmin(np.abs(freqs - 50.0)))

        self.assertLess(laser_fft[idx_50hz], 1.0e-6 * laser_fft[idx_1hz])
        self.assertLess(accel_fft[idx_50hz], 1.0e-6 * accel_fft[idx_1hz])

    def test_frequency_domain_differentiation_recovers_harmonic_acceleration(self):
        fs = 1000.0
        t = np.arange(0.0, 4.0, 1.0 / fs)
        freq_hz = 2.0
        amplitude_m = 0.001
        q_m = amplitude_m * np.sin(2.0 * np.pi * freq_hz * t)

        _, acceleration = _differentiate_displacement(q_m, fs)

        expected = -(2.0 * np.pi * freq_hz) ** 2 * q_m
        self.assertLess(np.sqrt(np.mean((acceleration - expected) ** 2)), 1.0e-10)


class TestMeasuredBridgeRecord(unittest.TestCase):
    def test_relative_tdms_path_resolves_from_project_root(self):
        path = _resolve_project_path("datafile/20250320test12.tdms")

        self.assertEqual(path, REPO_ROOT / "datafile" / "20250320test12.tdms")

    def test_default_laser_truth_preserves_high_frequency_content(self):
        fs = 1000.0
        duration_s = 4.0
        t = np.arange(0.0, duration_s, 1.0 / fs)
        laser_raw = np.sin(2.0 * np.pi * 1.0 * t) + 0.5 * np.sin(2.0 * np.pi * 30.0 * t)

        def fake_read_channel(path, group_name, channel_name):
            del path, group_name, channel_name
            return laser_raw, fs

        config = SimpleNamespace(
            measured_bridge_tdms_path=str(TDMS_PATH),
            measured_bridge_acceleration_source="laser_derived",
            measured_bridge_derived_accel_noise_std_mps2=0.0,
            measured_bridge_event_window_s=(0.0, duration_s),
            measured_bridge_laser_scale_m_per_v=1.0,
            accel_bias_mps2=0.0,
            accel_drift_mps2=0.0,
            seed=2026,
            sample_rate_hz=fs,
            duration_s=duration_s,
            cold_start_duration_s=0.20,
        )

        with patch("simulation.phase1.measured_bridge._read_tdms_channel", side_effect=fake_read_channel):
            record = load_measured_bridge_record(config)

        freqs = np.fft.rfftfreq(record.truth.q_m.size, 1.0 / fs)
        spectrum = np.abs(np.fft.rfft(record.truth.q_m - np.mean(record.truth.q_m)))
        idx_1hz = int(np.argmin(np.abs(freqs - 1.0)))
        idx_30hz = int(np.argmin(np.abs(freqs - 30.0)))

        self.assertGreater(spectrum[idx_30hz], 0.35 * spectrum[idx_1hz])

    def test_laser_derived_acceleration_uses_filtered_copy_not_raw_truth(self):
        fs = 1000.0
        duration_s = 4.0
        t = np.arange(0.0, duration_s, 1.0 / fs)
        laser_raw = np.sin(2.0 * np.pi * 1.0 * t) + 0.02 * np.sin(2.0 * np.pi * 120.0 * t)

        def fake_read_channel(path, group_name, channel_name):
            del path, group_name, channel_name
            return laser_raw, fs

        config = SimpleNamespace(
            measured_bridge_tdms_path=str(TDMS_PATH),
            measured_bridge_acceleration_source="laser_derived",
            measured_bridge_derived_accel_noise_std_mps2=0.0,
            measured_bridge_event_window_s=(0.0, duration_s),
            measured_bridge_laser_scale_m_per_v=1.0,
            accel_bias_mps2=0.0,
            accel_drift_mps2=0.0,
            seed=2026,
            sample_rate_hz=fs,
            duration_s=duration_s,
            cold_start_duration_s=0.20,
        )

        with patch("simulation.phase1.measured_bridge._read_tdms_channel", side_effect=fake_read_channel):
            record = load_measured_bridge_record(config)

        freqs = np.fft.rfftfreq(record.truth.q_m.size, 1.0 / fs)
        q_spectrum = np.abs(np.fft.rfft(record.truth.q_m - np.mean(record.truth.q_m)))
        idx_1hz = int(np.argmin(np.abs(freqs - 1.0)))
        idx_120hz = int(np.argmin(np.abs(freqs - 120.0)))

        self.assertGreater(q_spectrum[idx_120hz], 0.01 * q_spectrum[idx_1hz])
        self.assertLess(np.max(np.abs(record.accelerometer.measured_mps2)), 100.0)

    def test_load_record_returns_truth_and_acceleration_with_same_length(self):
        _require_measured_bridge_fixture(self)
        config = SimpleNamespace(
            measured_bridge_tdms_path=str(TDMS_PATH),
            sample_rate_hz=1000.0,
            duration_s=4.0,
            cold_start_duration_s=0.05,
        )

        record = load_measured_bridge_record(config)

        self.assertEqual(record.truth.t.shape, record.truth.q_m.shape)
        self.assertEqual(record.truth.t.shape, record.accelerometer.measured_mps2.shape)
        self.assertAlmostEqual(record.truth.t[1] - record.truth.t[0], 1.0 / config.sample_rate_hz)
        self.assertEqual(record.laser_channel, "卡3激光位移/3-4")
        self.assertEqual(record.acceleration_channel, "卡1梁振动/1-5")

    def test_laser_derived_acceleration_source_uses_laser_truth_with_seeded_noise(self):
        _require_measured_bridge_fixture(self)
        config = SimpleNamespace(
            measured_bridge_tdms_path=str(TDMS_PATH),
            measured_bridge_acceleration_source="laser_derived",
            measured_bridge_derived_accel_noise_std_mps2=0.0,
            accel_bias_mps2=0.0,
            accel_drift_mps2=0.0,
            seed=2026,
            sample_rate_hz=1000.0,
            duration_s=4.0,
            cold_start_duration_s=0.05,
        )

        record = load_measured_bridge_record(config)

        self.assertEqual(record.acceleration_channel, "laser_derived(卡3激光位移/3-4)")
        self.assertLess(
            np.sqrt(np.mean((record.accelerometer.measured_mps2 - record.truth.a_mps2) ** 2)),
            1.0e-12,
        )


if __name__ == "__main__":
    unittest.main()
