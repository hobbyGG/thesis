"""Capture-contract simulation for the measured magnetic-levitation beam event.

This module intentionally supports one scenario only.  Its laser displacement
comes from the measured TDMS channel; radar, ADXL355, and all sensor clocks are
derived or synthetic and are labelled as such in the package manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .config import Phase1Config
from .capture_error_models import (
    apply_adxl355_datasheet_typical_calibrated_25c,
    apply_iwr1843_receiver_and_adc_model,
)
from .frontend import FrontendConfig, build_default_scatterers, simulate_adc_cube
from .measured_bridge import load_measured_bridge_record
from .scenarios.measured_bridge_point4_transverse import build as build_scenario
from .truth import TruthSignal


SCHEMA_NAME = "mmwavecapture.simulation-fusion-input"
SCHEMA_VERSION = 1
SCENARIO_NAME = "measured_bridge_point4_transverse"
TDMS_RELATIVE_PATH = "datafile/20250320test12.tdms"
RADAR_CONFIG_RELATIVE_PATH = (
    "capture_program/examples/configs/iwr1843_hardware_trigger.cfg"
)
LASER_CHANNEL = "卡3激光位移/3-4"
EVENT_WINDOW_S = (15.33, 19.33)
RADAR_RATE_HZ = 100
ADXL_RATE_HZ = 1000
ADC_SAMPLES = 256
ADC_SAMPLE_RATE_HZ = 5.209e6
RAMP_END_TIME_S = 57.14e-6
IDLE_TIME_S = 70.0e-6
CHIRP_LOOPS_PER_FRAME = 16
TX_INDICES = (0, 2)
RX_INDICES = (0, 1, 2, 3)
VIRTUAL_ANTENNAS = 8
PHYSICAL_CHIRPS_PER_FRAME = 32
FREQUENCY_SLOPE_HZ_PER_S = 70.0e12
START_FREQUENCY_HZ = 77.0e9
ANTI_ALIAS_BAND_HZ = (0.2, 40.0)
BASE_MONOTONIC_NS = 1_000_000_000
RADAR_MINIMUM_FRAME_PERIOD_S = 9.0e-3
COLD_START_DURATION_S = 0.20
LOOP_START_INTERVAL_S = len(TX_INDICES) * (IDLE_TIME_S + RAMP_END_TIME_S)
COHERENT_APERTURE_CENTER_OFFSET_S = (
    0.5 * (CHIRP_LOOPS_PER_FRAME - 1) * LOOP_START_INTERVAL_S
)
COHERENT_APERTURE_CENTER_OFFSET_NS = int(
    round(COHERENT_APERTURE_CENTER_OFFSET_S * 1_000_000_000)
)


@dataclass(frozen=True)
class MaglevCaptureSimulationResult:
    directory: Path
    manifest_path: Path
    radar_frames: int
    adxl_samples: int


def _array_description(filename: str, array: np.ndarray, axes: tuple[str, ...]) -> dict:
    return {
        "file": filename,
        "dtype": array.dtype.name,
        "shape": list(array.shape),
        "axes": list(axes),
    }


def _write_array(
    directory: Path,
    name: str,
    array: np.ndarray,
    axes: tuple[str, ...],
) -> dict:
    filename = f"{name}.npy"
    np.save(directory / filename, array, allow_pickle=False)
    return _array_description(filename, array, axes)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _project_path(relative_path: str) -> Path:
    return Path(__file__).resolve().parents[2] / relative_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _radar_config_provenance() -> dict[str, Any]:
    """Validate and fingerprint the fixed hardware-trigger radar template."""

    path = _project_path(RADAR_CONFIG_RELATIVE_PATH)
    commands: dict[str, list[list[str]]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("%", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        commands.setdefault(parts[0], []).append(parts[1:])

    def one(name: str) -> list[str]:
        values = commands.get(name, [])
        if len(values) != 1:
            raise RuntimeError(
                f"fixed radar configuration must contain one {name} command"
            )
        return values[0]

    profile = one("profileCfg")
    frame = one("frameCfg")
    channel = one("channelCfg")
    chirps = commands.get("chirpCfg", [])
    if len(profile) < 11 or len(frame) < 6 or len(channel) < 2:
        raise RuntimeError("fixed radar configuration is incomplete")

    chirp_start = int(frame[0])
    chirp_end = int(frame[1])
    tx_sequence = []
    for chirp_index in range(chirp_start, chirp_end + 1):
        matches = [
            values
            for values in chirps
            if int(values[0]) <= chirp_index <= int(values[1])
        ]
        if len(matches) != 1:
            raise RuntimeError("fixed radar chirp sequence is ambiguous")
        tx_mask = int(matches[0][7])
        tx_indices = [index for index in range(32) if tx_mask & (1 << index)]
        if len(tx_indices) != 1:
            raise RuntimeError("fixed radar chirps must each enable exactly one TX")
        tx_sequence.append(tx_indices[0])

    rx_mask = int(channel[0])
    tx_mask = int(channel[1])
    rx_indices = [index for index in range(32) if rx_mask & (1 << index)]
    enabled_tx_indices = [index for index in range(32) if tx_mask & (1 << index)]
    if enabled_tx_indices != sorted(tx_sequence):
        raise RuntimeError("fixed radar channelCfg and chirpCfg TX sets disagree")
    parsed = {
        "tx_indices": tx_sequence,
        "rx_indices": rx_indices,
        "chirp_loops_per_frame": int(frame[2]),
        "minimum_frame_period_s": round(float(frame[4]) * 1.0e-3, 12),
        "trigger_select": int(frame[5]),
        "start_frequency_hz": float(profile[1]) * 1.0e9,
        "idle_time_s": round(float(profile[2]) * 1.0e-6, 12),
        "ramp_end_time_s": round(float(profile[4]) * 1.0e-6, 12),
        "frequency_slope_hz_per_s": float(profile[7]) * 1.0e12,
        "adc_samples_per_chirp": int(profile[9]),
        "adc_sample_rate_hz": float(profile[10]) * 1.0e3,
    }
    expected = {
        "tx_indices": list(TX_INDICES),
        "rx_indices": list(RX_INDICES),
        "chirp_loops_per_frame": CHIRP_LOOPS_PER_FRAME,
        "minimum_frame_period_s": RADAR_MINIMUM_FRAME_PERIOD_S,
        "trigger_select": 2,
        "start_frequency_hz": START_FREQUENCY_HZ,
        "idle_time_s": IDLE_TIME_S,
        "ramp_end_time_s": RAMP_END_TIME_S,
        "frequency_slope_hz_per_s": FREQUENCY_SLOPE_HZ_PER_S,
        "adc_samples_per_chirp": ADC_SAMPLES,
        "adc_sample_rate_hz": ADC_SAMPLE_RATE_HZ,
    }
    for name, value in expected.items():
        actual = parsed[name]
        if isinstance(value, float):
            matches = bool(np.isclose(actual, value, rtol=0.0, atol=1.0e-12))
        else:
            matches = actual == value
        if not matches:
            raise RuntimeError(
                f"fixed radar configuration changed {name}: {actual!r} != {value!r}"
            )
    return {
        "classification": "configured",
        "file": RADAR_CONFIG_RELATIVE_PATH,
        "sha256": _sha256(path),
        **parsed,
    }


def _validate_overwrite_target(path: Path) -> None:
    """Only permit replacement of a package previously written by this module."""

    if not path.is_dir():
        raise FileExistsError(f"overwrite target is not a simulation directory: {path}")
    manifest_path = path / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FileExistsError(
            f"refusing to overwrite an unrecognized directory: {path}"
        ) from exc
    if (
        manifest.get("schema") != SCHEMA_NAME
        or manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("scenario") != SCENARIO_NAME
    ):
        raise FileExistsError(
            f"refusing to overwrite a non-maglev-simulation directory: {path}"
        )


def _scenario_config(duration_s: float, seed: int) -> Phase1Config:
    base = build_scenario(Phase1Config())
    return replace(
        base,
        duration_s=duration_s,
        sample_rate_hz=float(ADXL_RATE_HZ),
        cold_start_duration_s=COLD_START_DURATION_S,
        seed=seed,
        adc_sample_rate_hz=ADC_SAMPLE_RATE_HZ,
        chirp_duration_s=RAMP_END_TIME_S,
        chirps_per_frame=PHYSICAL_CHIRPS_PER_FRAME,
        frontend_num_tx=len(TX_INDICES),
        frontend_num_rx=len(RX_INDICES),
        frontend_num_virtual_rx=VIRTUAL_ANTENNAS,
        measured_bridge_analysis_band_hz=ANTI_ALIAS_BAND_HZ,
        measured_bridge_laser_truth_preprocessing="bandpass_notch",
        measured_bridge_acceleration_source="laser_derived",
        measured_bridge_derived_accel_band_hz=ANTI_ALIAS_BAND_HZ,
        measured_bridge_derived_accel_noise_std_mps2=0.0,
        accel_bias_mps2=0.0,
        accel_drift_mps2=0.0,
    )


def _radar_truth(record, duration_s: float) -> TruthSignal:
    frames = int(round(duration_s * RADAR_RATE_HZ))
    sample_indices = np.arange(frames, dtype=np.int64) * (ADXL_RATE_HZ // RADAR_RATE_HZ)
    if sample_indices[-1] >= record.truth.t.size:
        raise RuntimeError("measured bridge record does not cover the radar schedule")
    return TruthSignal(
        t=np.arange(frames, dtype=float) / float(RADAR_RATE_HZ),
        q_m=np.asarray(record.truth.q_m[sample_indices], dtype=float),
        v_mps=np.asarray(record.truth.v_mps[sample_indices], dtype=float),
        a_mps2=np.asarray(record.truth.a_mps2[sample_indices], dtype=float),
        frequencies_hz=tuple(record.truth.frequencies_hz),
        amplitudes_m=tuple(record.truth.amplitudes_m),
        phases_rad=tuple(record.truth.phases_rad),
    )


def _loop_truth(record, frame_times_s: np.ndarray, loop_index: int) -> TruthSignal:
    loop_times_s = frame_times_s + float(loop_index) * LOOP_START_INTERVAL_S
    source_times_s = np.asarray(record.truth.t, dtype=float)
    if loop_times_s[-1] > source_times_s[-1] + 1.0e-12:
        raise RuntimeError("measured bridge record does not cover the chirp-loop schedule")
    return TruthSignal(
        t=loop_times_s,
        q_m=np.interp(loop_times_s, source_times_s, record.truth.q_m),
        v_mps=np.interp(loop_times_s, source_times_s, record.truth.v_mps),
        a_mps2=np.interp(loop_times_s, source_times_s, record.truth.a_mps2),
        frequencies_hz=tuple(record.truth.frequencies_hz),
        amplitudes_m=tuple(record.truth.amplitudes_m),
        phases_rad=tuple(record.truth.phases_rad),
    )


def _simulate_chirp_cube(
    record,
    radar_truth: TruthSignal,
    radar_config: Phase1Config,
    frontend: FrontendConfig,
) -> tuple[np.ndarray, np.ndarray, Mapping[str, Any]]:
    """Simulate clean loop physics, then inject one pre-export hardware model."""

    scatterers = build_default_scatterers(radar_truth, radar_config, frontend)
    frame_times_s = np.asarray(radar_truth.t, dtype=float)
    chirp_cube = np.empty(
        (
            frame_times_s.size,
            CHIRP_LOOPS_PER_FRAME,
            VIRTUAL_ANTENNAS,
            ADC_SAMPLES,
        ),
        dtype=np.complex64,
    )
    for loop_index in range(CHIRP_LOOPS_PER_FRAME):
        truth = _loop_truth(record, frame_times_s, loop_index)
        observation = simulate_adc_cube(
            truth,
            radar_config,
            frontend,
            scatterers=scatterers,
        )
        chirp_cube[:, loop_index, :, :] = np.asarray(
            observation.adc_cube,
            dtype=np.complex64,
        )
    hardware = apply_iwr1843_receiver_and_adc_model(
        chirp_cube,
        target_amplitudes=radar_config.target_amplitudes,
        target_snr_db=radar_config.target_snr_db,
        seed=int(radar_config.seed) + 701,
    )
    chirp_cube = hardware.chirp_cube
    adc_cube = np.mean(chirp_cube, axis=1).astype(
        np.complex64,
        copy=False,
    )
    return adc_cube, chirp_cube, hardware.metadata


def _radar_manifest(
    directory: Path,
    adc_cube: np.ndarray,
    chirp_cube: np.ndarray,
    radar_config_source: Mapping[str, Any],
    hardware_error_model: Mapping[str, Any],
) -> Path:
    configured_frame_period_s = float(
        radar_config_source["minimum_frame_period_s"]
    )
    frame_times_s = (
        np.arange(adc_cube.shape[0], dtype=np.float64)
        * configured_frame_period_s
    )
    arrays = {
        "adc_cube": _write_array(
            directory,
            "adc_cube",
            adc_cube,
            ("frame", "virtual_antenna", "adc_sample"),
        ),
        "frame_times_s": _write_array(
            directory, "frame_times_s", frame_times_s, ("frame",)
        ),
        "chirp_cube": _write_array(
            directory,
            "chirp_cube",
            chirp_cube,
            ("frame", "chirp_loop", "virtual_antenna", "adc_sample"),
        ),
    }
    range_resolution_m = (
        299_792_458.0
        * ADC_SAMPLE_RATE_HZ
        / (2.0 * FREQUENCY_SLOPE_HZ_PER_S * ADC_SAMPLES)
    )
    frames = int(adc_cube.shape[0])
    # The stable capture contract counts the equivalent two-int16 LVDS payload,
    # not the on-disk NumPy complex64 storage size.
    payload_bytes = int(chirp_cube.size * 4)
    manifest = {
        "schema": "mmwavecapture.algorithm-input",
        "schema_version": 1,
        "source": {
            "kind": "simulation",
            "scenario": SCENARIO_NAME,
            "pcap_file": None,
            "dca_receive_timestamps": None,
        },
        "packet_integrity": {
            "complete": True,
            "mode": "synthetic_payload_integrity",
            "payload_bytes": payload_bytes,
            "warning": "No PCAP, Ethernet reception, or DCA1000 packet stream exists.",
        },
        "timing": {
            "frame_times_s": {
                "clock": "synthetic_monotonic_schedule",
                "semantics": (
                    "configured minimum relative frame schedule; actual synthetic "
                    "trigger references are stored in the root package"
                ),
                "is_measured_frame_start": False,
            }
        },
        "radar": {
            "frames": frames,
            "frame_period_s": configured_frame_period_s,
            "frame_rate_hz": 1.0 / configured_frame_period_s,
            "minimum_frame_period_s": configured_frame_period_s,
            "external_trigger_period_s": 1.0 / RADAR_RATE_HZ,
            "chirp_loops_per_frame": CHIRP_LOOPS_PER_FRAME,
            "tx_chirps_per_loop": len(TX_INDICES),
            "physical_chirps_per_frame": PHYSICAL_CHIRPS_PER_FRAME,
            "tx_indices": list(TX_INDICES),
            "tx_sequence": list(TX_INDICES),
            "rx_indices": list(RX_INDICES),
            "virtual_antennas": VIRTUAL_ANTENNAS,
            "virtual_channels": [
                {"virtual_index": index, "synthetic": True}
                for index in range(VIRTUAL_ANTENNAS)
            ],
            "adc_samples_per_chirp": ADC_SAMPLES,
            "adc_sample_rate_hz": ADC_SAMPLE_RATE_HZ,
            "start_frequency_hz": START_FREQUENCY_HZ,
            "frequency_slope_hz_per_s": FREQUENCY_SLOPE_HZ_PER_S,
            "ramp_end_time_s": RAMP_END_TIME_S,
            "idle_time_s": IDLE_TIME_S,
            "range_resolution_m": range_resolution_m,
            "quadrature_in_lsb": True,
        },
        "processing": {
            "complex_convention": "I+jQ",
            "frame_level_chirp_aggregation": "coherent_mean",
            "chirp_cube_construction": (
                "16 independently noised synthetic loop observations sampled "
                "at their within-frame loop-start times"
            ),
            "loop_start_interval_s": (
                LOOP_START_INTERVAL_S
            ),
            "coherent_aperture_center_offset_s": (
                COHERENT_APERTURE_CENTER_OFFSET_S
            ),
            "tdm_motion_compensation": False,
            "warning": (
                "Loop-to-loop motion is modeled, but the TX0-to-TX2 time skew "
                "inside each virtual array observation is not modeled or compensated."
            ),
            "hardware_error_model": dict(hardware_error_model),
        },
        "arrays": arrays,
    }
    path = directory / "manifest.json"
    _write_json(path, manifest)
    return path


def _adxl_manifest(directory: Path, record, seed: int) -> tuple[Path, Mapping[str, Any]]:
    sample_count = int(record.truth.t.size)
    hardware = apply_adxl355_datasheet_typical_calibrated_25c(
        np.asarray(record.truth.a_mps2, dtype=np.float64),
        sample_rate_hz=float(ADXL_RATE_HZ),
        seed=int(seed) + 503,
    )
    acceleration_raw = hardware.acceleration_raw
    acceleration_mps2 = hardware.acceleration_mps2
    period_ns = 1_000_000_000 // ADXL_RATE_HZ
    sample_time = BASE_MONOTONIC_NS + np.arange(sample_count, dtype=np.int64) * period_ns
    drdy_time = sample_time.astype(np.uint64)
    sample_times_s = np.arange(sample_count, dtype=np.float64) / float(ADXL_RATE_HZ)
    arrays = {
        "acceleration_raw": _write_array(
            directory, "acceleration_raw", acceleration_raw, ("sample", "axis")
        ),
        "acceleration_mps2": _write_array(
            directory, "acceleration_mps2", acceleration_mps2, ("sample", "axis")
        ),
        "drdy_monotonic_ns": _write_array(
            directory, "drdy_monotonic_ns", drdy_time, ("sample",)
        ),
        "estimated_sample_monotonic_ns": _write_array(
            directory,
            "estimated_sample_monotonic_ns",
            sample_time,
            ("sample",),
        ),
        "sample_times_s": _write_array(
            directory, "sample_times_s", sample_times_s, ("sample",)
        ),
    }
    manifest = {
        "schema": "mmwavecapture.adxl355-input",
        "schema_version": 1,
        "source": {
            "kind": "simulation",
            "structural_axis": "physical laser-derived acceleration plus ADXL355 hardware model",
            "other_axes": "ADXL355 hardware-model noise around zero physical acceleration",
            "native_raw_file": None,
        },
        "capture": {
            "complete": True,
            "samples": sample_count,
            "odr_hz_nominal": float(ADXL_RATE_HZ),
            "range_g": 2,
            "group_delay_ns": 0,
            "group_delay_calibrated": False,
            "native_summary": {
                "samples": sample_count,
                "mock": True,
                "simulation": True,
                "group_delay_source": None,
            },
        },
        "timing": {
            "clock": "synthetic_monotonic_schedule",
            "drdy_monotonic_ns_semantics": "synthetic nominal DRDY schedule",
            "estimated_sample_monotonic_ns_semantics": (
                "same synthetic schedule; no measured delay"
            ),
        },
        "conversion": {
            "standard_gravity_mps2": 9.80665,
            "sensitivity_lsb_per_g": hardware.metadata["sensitivity_lsb_per_g"],
            "calibration_applied": True,
        },
        "hardware_error_model": hardware.metadata,
        "arrays": arrays,
    }
    path = directory / "manifest.json"
    _write_json(path, manifest)
    return path, hardware.metadata


def generate_maglev_capture_package(
    output: Path | str,
    *,
    duration_s: float = 4.0,
    seed: int = 2026,
    overwrite: bool = False,
) -> MaglevCaptureSimulationResult:
    """Generate the single supported measured-beam capture simulation."""

    if not np.isfinite(duration_s) or duration_s <= 0.0:
        raise ValueError("duration_s must be finite and positive")
    maximum_duration = round(EVENT_WINDOW_S[1] - EVENT_WINDOW_S[0], 9)
    if duration_s > maximum_duration + 1.0e-12:
        raise ValueError(f"duration_s cannot exceed the {maximum_duration:g} s event window")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise ValueError("seed must be an integer")
    if not isinstance(overwrite, (bool, np.bool_)):
        raise ValueError("overwrite must be boolean")
    requested_frames = duration_s * RADAR_RATE_HZ
    frame_count = int(round(requested_frames))
    if not np.isclose(requested_frames, frame_count, rtol=0.0, atol=1.0e-9):
        raise ValueError("duration_s must be an integer multiple of 0.01 s")
    adxl_count = int(round(duration_s * ADXL_RATE_HZ))
    if frame_count < 2 or adxl_count < 2:
        raise ValueError("duration_s must produce at least two radar and ADXL samples")

    output_path = Path(output)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {output_path}")
    if output_path.exists():
        _validate_overwrite_target(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.parent / f".{output_path.name}.tmp-{uuid.uuid4().hex}"
    temporary.mkdir(exist_ok=False)
    try:
        config = _scenario_config(duration_s, int(seed))
        radar_config_source = _radar_config_provenance()
        tdms_path = _project_path(TDMS_RELATIVE_PATH)
        tdms_sha256 = _sha256(tdms_path)
        record = load_measured_bridge_record(config)
        if record.laser_channel != LASER_CHANNEL:
            raise RuntimeError("fixed magnetic-levitation laser channel changed")
        if record.truth.t.size != adxl_count:
            raise RuntimeError("measured bridge loader returned an unexpected sample count")
        radar_truth = _radar_truth(record, duration_s)
        range_resolution_m = (
            299_792_458.0
            * ADC_SAMPLE_RATE_HZ
            / (2.0 * FREQUENCY_SLOPE_HZ_PER_S * ADC_SAMPLES)
        )
        frontend = FrontendConfig(
            num_tx=len(TX_INDICES),
            num_rx=len(RX_INDICES),
            num_virtual_rx=VIRTUAL_ANTENNAS,
            num_adc_samples=ADC_SAMPLES,
            adc_sample_rate_hz=ADC_SAMPLE_RATE_HZ,
            chirp_duration_s=RAMP_END_TIME_S,
            chirps_per_frame=PHYSICAL_CHIRPS_PER_FRAME,
            num_range_bins=ADC_SAMPLES,
            num_angle_bins=int(config.frontend_num_angle_bins),
            range_resolution_m=range_resolution_m,
            inject_target_slow_time_noise=False,
            inject_adc_receiver_noise=False,
        )
        radar_config = replace(config, sample_rate_hz=float(RADAR_RATE_HZ))
        adc_cube, chirp_cube, radar_error_model = _simulate_chirp_cube(
            record,
            radar_truth,
            radar_config,
            frontend,
        )

        radar_directory = temporary / "radar" / "algorithm_input"
        adxl_directory = temporary / "adxl355" / "algorithm_input"
        radar_directory.mkdir(parents=True)
        adxl_directory.mkdir(parents=True)
        _radar_manifest(
            radar_directory,
            adc_cube,
            chirp_cube,
            radar_config_source,
            radar_error_model,
        )
        _, adxl_error_model = _adxl_manifest(
            adxl_directory,
            record,
            int(seed),
        )

        radar_reference_time_ns = BASE_MONOTONIC_NS + (
            np.arange(frame_count, dtype=np.int64) * (1_000_000_000 // RADAR_RATE_HZ)
        )
        radar_adc_time_ns = (
            radar_reference_time_ns + COHERENT_APERTURE_CENTER_OFFSET_NS
        )
        truth_time_s = (
            radar_adc_time_ns - BASE_MONOTONIC_NS
        ).astype(np.float64) * 1.0e-9
        truth_q = np.interp(
            truth_time_s,
            np.asarray(record.truth.t, dtype=np.float64),
            np.asarray(record.truth.q_m, dtype=np.float64),
        ).astype(np.float64, copy=False)
        radar_time_desc = _write_array(
            temporary,
            "radar_reference_monotonic_ns",
            radar_reference_time_ns,
            ("radar_frame",),
        )
        radar_adc_time_desc = _write_array(
            temporary,
            "radar_adc_sample_monotonic_ns",
            radar_adc_time_ns,
            ("radar_frame",),
        )
        truth_time_desc = _write_array(
            temporary,
            "truth_time_ns",
            radar_adc_time_ns.copy(),
            ("radar_frame",),
        )
        truth_q_desc = _write_array(
            temporary, "truth_displacement_m", truth_q, ("radar_frame",)
        )
        truth_adxl_time_ns = BASE_MONOTONIC_NS + (
            np.arange(adxl_count, dtype=np.int64)
            * (1_000_000_000 // ADXL_RATE_HZ)
        )
        truth_adxl_time_desc = _write_array(
            temporary,
            "truth_adxl_time_ns",
            truth_adxl_time_ns,
            ("adxl_sample",),
        )
        truth_acceleration_desc = _write_array(
            temporary,
            "truth_acceleration_mps2",
            np.asarray(record.truth.a_mps2, dtype=np.float64),
            ("adxl_sample",),
        )
        root_manifest = {
            "schema": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "status": "complete",
            "scenario": SCENARIO_NAME,
            "seed": int(seed),
            "simulation_ready": True,
            "algorithm_ready": False,
            "fusion_ready": False,
            "hardware_validated": False,
            "sync_mode": "simulation",
            "timestamp_quality": "synthetic_coherent_aperture_center",
            "packet_integrity": "synthetic_payload_integrity",
            "algorithm_contract": {
                "cold_start_duration_s": COLD_START_DURATION_S,
                "displacement_reference": "cold_start_mean",
                "truth_evaluation": "cold_start_relative_displacement",
            },
            "source_provenance": {
                "laser_displacement": {
                    "classification": "measured",
                    "file": TDMS_RELATIVE_PATH,
                    "sha256": tdms_sha256,
                    "channel": LASER_CHANNEL,
                    "event_window_s": [EVENT_WINDOW_S[0], EVENT_WINDOW_S[0] + duration_s],
                    "scale_m_per_v": config.measured_bridge_laser_scale_m_per_v,
                    "scale_calibrated": False,
                    "measured_quantity": "raw_voltage_waveform",
                    "displacement_status": (
                        "derived_with_unvalidated_voltage_to_displacement_scale"
                    ),
                    "pre_downsample_filter_hz": list(ANTI_ALIAS_BAND_HZ),
                    "source_sample_rate_hz": record.source_laser_sample_rate_hz,
                },
                "radar_adc_iq": {
                    "classification": "synthetic",
                    "model": "phase1 range-angle ADC frontend",
                    "aoa_deg": list(config.target_angles_deg),
                    "snr_db": list(config.target_snr_db),
                    "target_range_bins": list(config.target_range_bins),
                    "within_frame_tdm_motion_compensation": False,
                    "loop_to_loop_motion_modeled": True,
                    "inter_tx_skew_modeled": False,
                    "hardware_error_model": radar_error_model,
                    "noise_injection_layers": 1,
                },
                "radar_configuration": radar_config_source,
                "adxl_structural_axis": {
                    "classification": "derived",
                    "axis": "x",
                    "noise_classification": "synthetic",
                    "physical_acceleration_noise_std_mps2": 0.0,
                    "physical_acceleration_bias_mps2": 0.0,
                    "physical_acceleration_drift_mps2": 0.0,
                    "hardware_error_model": adxl_error_model,
                    "method": (
                        "0.2-40 Hz band-limited laser displacement, FFT second "
                        "derivative, then package-writer ADXL355 hardware model"
                    ),
                },
                "adxl_other_axes": {
                    "classification": "synthetic",
                    "axes": ["y", "z"],
                },
                "radar_timestamps": {
                    "classification": "synthetic",
                    "quality": "synthetic_coherent_aperture_center",
                    "reference_quality": "synthetic_monotonic_schedule",
                    "effective_observation": "coherent_aperture_center",
                    "coherent_aperture_center_offset_ns": (
                        COHERENT_APERTURE_CENTER_OFFSET_NS
                    ),
                    "measured_gpio": False,
                    "measured_adc_time": False,
                },
                "adxl_drdy_timestamps": {
                    "classification": "synthetic",
                    "quality": "synthetic_monotonic_schedule",
                    "measured_drdy": False,
                },
            },
            "rates_hz": {"radar": RADAR_RATE_HZ, "adxl355": ADXL_RATE_HZ},
            "files": {
                "radar_algorithm_input_manifest": "radar/algorithm_input/manifest.json",
                "adxl355_algorithm_input_manifest": "adxl355/algorithm_input/manifest.json",
            },
            "arrays": {
                "radar_reference_monotonic_ns": radar_time_desc,
                "radar_adc_sample_monotonic_ns": radar_adc_time_desc,
                "truth_time_ns": truth_time_desc,
                "truth_displacement_m": truth_q_desc,
                "truth_adxl_time_ns": truth_adxl_time_desc,
                "truth_acceleration_mps2": truth_acceleration_desc,
            },
        }
        _write_json(temporary / "manifest.json", root_manifest)
        backup = None
        if output_path.exists():
            backup = output_path.parent / f".{output_path.name}.backup-{uuid.uuid4().hex}"
            output_path.replace(backup)
        try:
            temporary.replace(output_path)
        except BaseException:
            if backup is not None and not output_path.exists():
                backup.replace(output_path)
            raise
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return MaglevCaptureSimulationResult(
        directory=output_path,
        manifest_path=output_path / "manifest.json",
        radar_frames=frame_count,
        adxl_samples=adxl_count,
    )
