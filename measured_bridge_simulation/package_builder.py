from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from .tdms import load_bridge_record

RADAR_RATE_HZ = 100.0
ADXL_RATE_HZ = 1000.0
BASE_TIME_NS = 1_000_000_000
WAVELENGTH_M = 299_792_458.0 / 77.0e9
VIRTUAL_RX = 8
ADC_SAMPLES = 256
RANGE_RESOLUTION_M = 0.15
TARGET_ANGLES_DEG = np.asarray((5.0, 15.0, 25.0, 35.0, 45.0))
TARGET_RANGE_BINS = np.asarray((8, 24, 40, 56, 72))
TARGET_AMPLITUDES = np.asarray((1.0, 0.95, 0.9, 0.85, 0.8))
TARGET_SNR_DB = np.asarray((20.0, 17.0, 14.0, 11.0, 8.0))


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _array(path: Path, values: np.ndarray, axes: list[str]) -> dict:
    np.save(path, values, allow_pickle=False)
    return {"file": path.name, "dtype": values.dtype.name, "shape": list(values.shape), "axes": axes}


def _radar_package(root: Path, q: np.ndarray, seed: int) -> None:
    frames = q.size
    rng = np.random.default_rng(seed)
    adc = np.zeros((frames, VIRTUAL_RX, ADC_SAMPLES), dtype=np.complex64)
    positions = np.arange(VIRTUAL_RX, dtype=float) * 0.5
    sample = np.arange(ADC_SAMPLES, dtype=float)
    theta = 4.0 * np.pi * q / WAVELENGTH_M
    for angle, range_bin, amplitude, snr_db in zip(TARGET_ANGLES_DEG, TARGET_RANGE_BINS, TARGET_AMPLITUDES, TARGET_SNR_DB):
        beta = 1.0 / abs(np.cos(np.deg2rad(angle)))
        bias = rng.uniform(-np.pi, np.pi)
        slow = amplitude * np.exp(1j * (theta / beta + bias))
        noise_std = amplitude / np.sqrt(2.0 * 10.0 ** (snr_db / 10.0))
        slow += noise_std * (rng.standard_normal(frames) + 1j * rng.standard_normal(frames))
        angle_tone = np.exp(2j * np.pi * positions * np.sin(np.deg2rad(angle)))
        range_tone = np.exp(2j * np.pi * range_bin * sample / ADC_SAMPLES)
        adc += (slow[:, None, None] * angle_tone[None, :, None] * range_tone[None, None, :]).astype(np.complex64)
    adc += (0.01 * (rng.standard_normal(adc.shape) + 1j * rng.standard_normal(adc.shape))).astype(np.complex64)
    chirp = np.repeat(adc[:, None, :, :], 16, axis=1)
    directory = root / "radar" / "algorithm_input"
    directory.mkdir(parents=True)
    arrays = {
        "adc_cube": _array(directory / "adc_cube.npy", adc, ["frame", "virtual_antenna", "adc_sample"]),
        "frame_times_s": _array(directory / "frame_times_s.npy", np.arange(frames) / RADAR_RATE_HZ, ["frame"]),
        "chirp_cube": _array(directory / "chirp_cube.npy", chirp, ["frame", "chirp_loop", "virtual_antenna", "adc_sample"]),
    }
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.algorithm-input", "schema_version": 1,
        "source": {"kind": "measured_bridge_simulation", "radar_adc_iq": "synthetic"},
        "packet_integrity": {"complete": True, "mode": "synthetic_payload_integrity", "payload_bytes": int(chirp.size * 4)},
        "radar": {
            "frames": frames, "frame_period_s": 1.0 / RADAR_RATE_HZ, "frame_rate_hz": RADAR_RATE_HZ,
            "minimum_frame_period_s": 1.0 / RADAR_RATE_HZ, "physical_chirps_per_frame": 16,
            "tx_indices": [0, 2], "rx_indices": [0, 1, 2, 3], "virtual_antennas": VIRTUAL_RX,
            "adc_samples_per_chirp": ADC_SAMPLES, "adc_sample_rate_hz": 5.209e6,
            "start_frequency_hz": 77.0e9, "ramp_end_time_s": 57.14e-6,
            "range_resolution_m": RANGE_RESOLUTION_M, "angle_bins": 64,
        },
        "arrays": arrays,
    })


def _adxl_package(root: Path, acceleration: np.ndarray, seed: int) -> None:
    rng = np.random.default_rng(seed + 1)
    sample_count = acceleration.size
    values = np.zeros((sample_count, 3), dtype=np.float64)
    values[:, 0] = acceleration + 0.02 * rng.standard_normal(sample_count)
    raw = np.rint(values / 9.80665 * 256000.0).astype(np.int32)
    directory = root / "adxl355" / "algorithm_input"
    directory.mkdir(parents=True)
    times = BASE_TIME_NS + np.arange(sample_count, dtype=np.int64) * round(1.0e9 / ADXL_RATE_HZ)
    arrays = {
        "acceleration_raw": _array(directory / "acceleration_raw.npy", raw, ["sample", "axis"]),
        "acceleration_mps2": _array(directory / "acceleration_mps2.npy", values, ["sample", "axis"]),
        "drdy_monotonic_ns": _array(directory / "drdy_monotonic_ns.npy", times, ["sample"]),
        "estimated_sample_monotonic_ns": _array(directory / "estimated_sample_monotonic_ns.npy", times, ["sample"]),
        "sample_times_s": _array(directory / "sample_times_s.npy", np.arange(sample_count) / ADXL_RATE_HZ, ["sample"]),
    }
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.adxl355-input", "schema_version": 1,
        "source": {"kind": "measured_bridge_simulation", "structural_axis": "laser-derived"},
        "capture": {"complete": True, "samples": sample_count, "odr_hz_nominal": ADXL_RATE_HZ, "range_g": 2,
                    "group_delay_ns": 0, "group_delay_calibrated": False,
                    "native_summary": {"samples": sample_count, "mock": True, "simulation": True}},
        "timing": {"clock": "CLOCK_MONOTONIC", "drdy_monotonic_ns_semantics": "synthetic nominal DRDY schedule",
                   "estimated_sample_monotonic_ns_semantics": "synthetic nominal sample schedule"},
        "arrays": arrays,
    })


def generate(output: str | Path, *, duration_s: float = 4.0, seed: int = 2026) -> Path:
    output = Path(output)
    t, displacement, acceleration = load_bridge_record()
    count = round(duration_s * RADAR_RATE_HZ)
    if count < 2 or count > round(t[-1] * RADAR_RATE_HZ) + 1:
        raise ValueError("duration is outside the measured bridge event")
    step = round(ADXL_RATE_HZ / RADAR_RATE_HZ)
    frame_q = displacement[::step][:count]
    frame_a = acceleration[: round(duration_s * ADXL_RATE_HZ)]
    with tempfile.TemporaryDirectory(prefix="bridge-package-") as temporary:
        staging = Path(temporary) / "package"
        staging.mkdir()
        _radar_package(staging, frame_q, seed)
        _adxl_package(staging, frame_a, seed)
        sync = staging / "sync"
        sync.mkdir()
        radar_time = BASE_TIME_NS + np.arange(count, dtype=np.int64) * round(1.0e9 / RADAR_RATE_HZ)
        np.save(sync / "radar_frame_monotonic_ns.npy", radar_time, allow_pickle=False)
        np.save(sync / "radar_adc_sample_monotonic_ns.npy", radar_time, allow_pickle=False)
        _json(sync / "timeline.json", {"schema_version": 1, "status": "complete",
                                        "sync_mode": "software_timestamp", "timestamp_quality": "sensor_start_bracket_estimate",
                                        "hardware_validated": False, "clock": "CLOCK_MONOTONIC", "unit": "nanoseconds",
                                        "frame_count": count, "nominal_frame_period_ns": round(1.0e9 / RADAR_RATE_HZ),
                                        "radar_algorithm_manifest": "../radar/algorithm_input/manifest.json",
                                        "radar_packet_integrity_complete": True,
                                        "array": {"file": "radar_frame_monotonic_ns.npy", "dtype": "int64", "shape": [count], "axes": ["radar_frame"]},
                                        "adc_array": {"file": "radar_adc_sample_monotonic_ns.npy", "dtype": "int64", "shape": [count]},
                                        "provenance": {"source": "measured_bridge_simulation", "semantics": "synthetic monotonic schedule", "is_measured_radar_frame_start": False}})
        _json(sync / "manifest.json", {"schema_version": 1, "status": "complete",
                                        "sync_mode": "software_timestamp", "timestamp_quality": "sensor_start_bracket_estimate",
                                        "hardware_validated": False,
                                        "clock": {"alignment_clock": "CLOCK_MONOTONIC", "unit": "nanoseconds", "wall_clock": "CLOCK_REALTIME", "wall_time_used_for_alignment": False},
                                        "files": {"radar": {"algorithm_input_manifest": "radar/algorithm_input/manifest.json"},
                                                  "adxl355": {"algorithm_input_manifest": "adxl355/algorithm_input/manifest.json"},
                                                  "sync": {"timeline_manifest": "sync/timeline.json", "radar_frame_monotonic_ns": "sync/radar_frame_monotonic_ns.npy"}},
                                        "validation": {"status": "complete", "radar_finalized": True, "adxl355_finalized": True, "sync_timeline_exported": True, "hardware_validated": False},
                                        "uncertainty": {"status": "not_characterized"},
                                        "timestamp_semantics": {"pcap_is_frame_start": False, "radar": "synthetic monotonic schedule", "adxl355": "synthetic nominal sample schedule"}})
        truth = staging / "truth"
        truth.mkdir()
        np.save(truth / "displacement_m.npy", frame_q, allow_pickle=False)
        np.save(truth / "time_ns.npy", radar_time, allow_pickle=False)
        np.save(truth / "acceleration_mps2.npy", frame_a, allow_pickle=False)
        np.save(truth / "adxl_time_ns.npy", BASE_TIME_NS + np.arange(frame_a.size, dtype=np.int64) * round(1.0e9 / ADXL_RATE_HZ), allow_pickle=False)
        _json(staging / "status.json", {"schema_version": 1, "status": "complete", "source_type": "measured_bridge_simulation"})
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    return output
