import json
import struct
from pathlib import Path

import numpy as np
import pytest

from mmwavecapture.adxl355_input import (
    RAW_HEADER_BYTES,
    RECORD_DTYPE,
    export_adxl355_input,
)
from mmwavecapture.algorithm_input import export_algorithm_input
from mmwavecapture.fusion_input import FusionInputError, load_fusion_input


PCAP_FIXTURE = Path(__file__).parent / "pcaps" / "test_one_frame.pcap"
GROUP_DELAY_NS = 1_780_000
RADAR_REFERENCE_NS = 11_000_000_000
RADAR_LATENCY_NS = 100_000


def _write_radar_config(path):
    path.write_text(
        "\n".join(
            [
                "channelCfg 15 5 0",
                "adcCfg 2 1",
                "adcbufCfg -1 0 1 1 1",
                "profileCfg 0 77 429 7 57.14 0 0 70 1 256 5209 0 0 30",
                "chirpCfg 0 0 0 0 0 0 0 1",
                "chirpCfg 1 1 0 0 0 0 0 4",
                "frameCfg 0 1 2 1 100 1 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_adxl_source(directory, *, mock=False):
    directory.mkdir(parents=True)
    samples = 9
    header = bytearray(RAW_HEADER_BYTES)
    header[:8] = b"ADXLRW01"
    struct.pack_into("<HHHH", header, 8, 1, 64, 48, 1 if mock else 0)
    struct.pack_into("<I", header, 16, 1_000_000)
    struct.pack_into("<H", header, 20, 2)
    struct.pack_into("<Q", header, 24, 1_800_000_000_000_000_000)
    struct.pack_into("<Q", header, 32, 10_000_000_000)
    struct.pack_into("<q", header, 40, GROUP_DELAY_NS)

    records = np.zeros(samples, dtype=RECORD_DTYPE)
    records["sample_seq"] = np.arange(samples, dtype=np.uint64)
    records["line_seqno"] = np.arange(1, samples + 1, dtype=np.uint64)
    records["drdy_monotonic_ns"] = (
        10_997_000_000 + np.arange(samples, dtype=np.uint64) * 1_000_000
    )
    records["spi_complete_monotonic_ns"] = (
        records["drdy_monotonic_ns"] + 25_000
    )
    records["x_raw"] = np.arange(samples) * 100
    records["z_raw"] = 256_000
    records["status"] = 1
    records["fifo_entries"] = 0 if mock else 3
    raw = directory / "samples.bin"
    raw.write_bytes(bytes(header) + records.tobytes())

    summary = {
        "schema_version": 1,
        "status": "complete",
        "samples": samples,
        "samples_written": samples,
        "first_drdy_monotonic_ns": int(records["drdy_monotonic_ns"][0]),
        "last_drdy_monotonic_ns": int(records["drdy_monotonic_ns"][-1]),
        "line_seq_gaps": 0,
        "fifo_overruns": 0,
        "gpio_backlog_events": 0,
        "fifo_protocol_errors": 0,
        "fifo_xyz_mismatches": 0,
        "fifo_xyz_sets_drained": 0 if mock else samples,
        "max_fifo_entries": 0 if mock else 3,
        "mock": mock,
        "sample_source": "mock" if mock else "FIFO_DATA_oldest",
        "timestamp_pairing": (
            "synthetic" if mock else "one_drdy_edge_to_one_fifo_xyz"
        ),
        "clock": "CLOCK_MONOTONIC",
        "timestamp_semantics": "drdy_edge",
        "start_realtime_ns": 1_800_000_000_000_000_000,
        "start_monotonic_ns": 10_000_000_000,
        "group_delay_ns": GROUP_DELAY_NS,
        "group_delay_calibrated": True,
        "group_delay_source": "adxl-filter-bench-v1",
        "config": {"odr_hz": 1000, "range_g": 2, "spi_hz": 5_000_000},
    }
    summary_path = directory / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return raw, summary_path, summary


def _write_package(tmp_path, *, calibrated=True, hardware_validated=True, mock=False):
    root = tmp_path / "synchronized"
    radar_dir = root / "radar"
    radar_dir.mkdir(parents=True)
    radar_config = radar_dir / "radar.cfg"
    _write_radar_config(radar_config)
    export_algorithm_input(
        PCAP_FIXTURE,
        radar_config,
        radar_dir / "algorithm_input",
    )

    adxl_dir = root / "adxl355"
    raw, summary_path, summary = _write_adxl_source(adxl_dir, mock=mock)
    export_adxl355_input(raw, summary_path, adxl_dir / "algorithm_input")

    sync_dir = root / "sync"
    sync_dir.mkdir()
    fusion_calibration = {
        "schema": "mmwavecapture.fusion-calibration",
        "schema_version": 1,
        "calibration_id": "fixture-v1",
        "validated": True,
        "adxl355": {
            "bias_mps2": [0.0, 0.0, 0.0],
            "scale_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "sensor_to_structure_rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "structural_axis_unit": [1.0, 0.0, 0.0],
            "source": "fixture-six-position",
        },
        "radar": {
            "azimuth_virtual_channel_indices": [0, 1, 2, 3, 4, 5, 6, 7],
            "virtual_array_positions_wavelengths": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
            "channel_correction_real": [1.0] * 8,
            "channel_correction_imag": [0.0] * 8,
            "range_bias_correction_m": 0.0,
            "source": "fixture-corner-reflector",
        },
    }
    (sync_dir / "fusion_calibration.json").write_text(
        json.dumps(fusion_calibration), encoding="utf-8"
    )
    np.save(
        sync_dir / "radar_frame_monotonic_ns.npy",
        np.array([RADAR_REFERENCE_NS], dtype=np.int64),
        allow_pickle=False,
    )
    timeline = {
        "schema_version": 1,
        "status": "complete",
        "sync_mode": "hardware_trigger",
        "timestamp_quality": "kernel_loopback_edge",
        "hardware_validated": hardware_validated,
        "clock": "CLOCK_MONOTONIC",
        "unit": "nanoseconds",
        "frame_count": 1,
        "nominal_frame_period_ns": 100_000_000,
        "radar_algorithm_manifest": "../radar/algorithm_input/manifest.json",
        "radar_packet_integrity_complete": True,
        "array": {
            "file": "radar_frame_monotonic_ns.npy",
            "dtype": "int64",
            "shape": [1],
            "axes": ["radar_frame"],
        },
        "provenance": {
            "source": "kernel_loopback_edge",
            "edge_observation": "physical_loopback_input",
            "is_measured_radar_frame_start": False,
            "semantics": "kernel-observed trigger edge, not radar ADC time",
        },
    }
    (sync_dir / "timeline.json").write_text(
        json.dumps(timeline), encoding="utf-8"
    )

    uncertainty = {
        "status": (
            "characterized"
            if calibrated and hardware_validated
            else (
                "not_characterized"
                if hardware_validated
                else "hardware_not_bench_validated"
            )
        ),
        "trigger_edge_uncertainty_ns": 500,
        "radar_trigger_latency_ns": RADAR_LATENCY_NS if calibrated else None,
        "radar_trigger_latency_calibrated": calibrated,
        "radar_trigger_latency_uncertainty_ns": 1_000 if calibrated else None,
        "radar_trigger_latency_source": "scope-bench-v1" if calibrated else None,
        "adxl_filter_group_delay_ns": GROUP_DELAY_NS,
        "adxl_filter_group_delay_calibrated": True,
        "adxl_filter_group_delay_source": "adxl-filter-bench-v1",
        "adxl_filter_group_delay_uncertainty_ns": 2_000,
    }
    combined = {
        "schema_version": 1,
        "status": "complete",
        "sync_mode": "hardware_trigger",
        "timestamp_quality": "kernel_loopback_edge",
        "hardware_validated": hardware_validated,
        "clock": {
            "alignment_clock": "CLOCK_MONOTONIC",
            "unit": "nanoseconds",
            "wall_clock": "CLOCK_REALTIME",
            "wall_time_used_for_alignment": False,
        },
        "files": {
            "radar": {
                "algorithm_input_manifest": (
                    "radar/algorithm_input/manifest.json"
                )
            },
            "adxl355": {
                "algorithm_input_manifest": (
                    "adxl355/algorithm_input/manifest.json"
                )
            },
            "sync": {
                "timeline_manifest": "sync/timeline.json",
                "radar_frame_monotonic_ns": (
                    "sync/radar_frame_monotonic_ns.npy"
                ),
                "fusion_calibration": "sync/fusion_calibration.json",
            },
        },
        "validation": {
            "status": "complete",
            "radar_finalized": True,
            "adxl355_finalized": True,
            "sync_timeline_exported": True,
            "adxl355": summary,
            "hardware_validated": hardware_validated,
            "radar_trigger_config_validated": True,
        },
        "uncertainty": uncertainty,
        "timestamp_semantics": {
            "adxl355": "DRDY edge on the Pi CLOCK_MONOTONIC timeline",
            "radar": "kernel-observed trigger edge; not radar ADC sample time",
            "pcap": "Ethernet receive time only",
            "pcap_is_frame_start": False,
        },
    }
    combined_path = sync_dir / "manifest.json"
    combined_path.write_text(json.dumps(combined), encoding="utf-8")
    (root / "status.json").write_text(
        json.dumps({"schema_version": 1, "status": "complete"}),
        encoding="utf-8",
    )
    return root


def _edit_json(path, edit):
    payload = json.loads(path.read_text(encoding="utf-8"))
    edit(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_loads_native_rate_timelines_and_certifies_ready_package(tmp_path):
    root = _write_package(tmp_path)

    capture = load_fusion_input(root)

    assert capture.fusion_ready is True
    assert capture.algorithm_ready is True
    assert capture.quality.algorithm_readiness_failures == ()
    assert capture.quality.readiness_failures == ()
    assert capture.radar_reference_monotonic_ns.tolist() == [RADAR_REFERENCE_NS]
    assert capture.radar_adc_sample_monotonic_ns.tolist() == [
        RADAR_REFERENCE_NS + RADAR_LATENCY_NS
    ]
    np.testing.assert_array_equal(
        capture.adxl_drdy_monotonic_ns,
        capture.adxl355.drdy_monotonic_ns,
    )
    np.testing.assert_array_equal(
        capture.adxl_sample_monotonic_ns,
        capture.adxl_drdy_monotonic_ns.astype(np.int64) - GROUP_DELAY_NS,
    )
    assert capture.radar.chirp_cube is not None
    assert capture.calibration.radar_latency_source == "scope-bench-v1"
    assert capture.calibration.adxl_group_delay_calibrated is True
    assert capture.value_calibration.calibration_id == "fixture-v1"
    np.testing.assert_allclose(
        capture.acceleration_structure_mps2,
        capture.adxl355.acceleration_mps2[:, 0],
    )
    assert capture.provenance.clock == "CLOCK_MONOTONIC"
    assert capture.provenance.radar_reference_is_measured_frame_start is False
    assert capture.provenance.pcap_is_frame_start is False


def test_uncalibrated_radar_latency_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path, calibrated=False)

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is True
    assert capture.radar_adc_sample_monotonic_ns is None
    assert "radar_reference_to_adc_latency_not_calibrated" in (
        capture.quality.readiness_failures
    )


def test_missing_value_calibration_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path)
    combined_path = root / "sync" / "manifest.json"
    _edit_json(
        combined_path,
        lambda payload: payload["files"]["sync"].pop("fusion_calibration"),
    )

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is True
    assert capture.acceleration_structure_mps2 is None
    assert "fusion_value_calibration_missing" in capture.quality.readiness_failures


def test_unvalidated_value_calibration_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path)
    _edit_json(
        root / "sync" / "fusion_calibration.json",
        lambda payload: payload.__setitem__("validated", False),
    )

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is True
    assert "fusion_value_calibration_not_validated" in (
        capture.quality.readiness_failures
    )


def test_unvalidated_hardware_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path, hardware_validated=False)

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is True
    assert "hardware_sync_not_validated" in capture.quality.readiness_failures


def test_mock_adxl_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path, mock=True)

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is False
    assert "adxl_source_is_mock" in capture.quality.readiness_failures


def test_nonoverlapping_native_timelines_are_visible_but_not_ready(tmp_path):
    root = _write_package(tmp_path)
    timeline_path = root / "sync" / "radar_frame_monotonic_ns.npy"
    np.save(
        timeline_path,
        np.array([20_000_000_000], dtype=np.int64),
        allow_pickle=False,
    )

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert capture.algorithm_ready is False
    assert capture.quality.native_timeline_overlap is False
    assert "native_sensor_timelines_do_not_overlap" in (
        capture.quality.readiness_failures
    )


def test_disagreement_with_combined_adxl_summary_fails_closed(tmp_path):
    root = _write_package(tmp_path)
    combined_path = root / "sync" / "manifest.json"
    _edit_json(
        combined_path,
        lambda payload: payload["validation"]["adxl355"].__setitem__(
            "samples", 999
        ),
    )

    with pytest.raises(FusionInputError, match="disagree on the native summary"):
        load_fusion_input(root)


def test_manifest_path_escape_fails_closed(tmp_path):
    root = _write_package(tmp_path)
    combined_path = root / "sync" / "manifest.json"
    _edit_json(
        combined_path,
        lambda payload: payload["files"]["adxl355"].__setitem__(
            "algorithm_input_manifest", "../../outside/manifest.json"
        ),
    )

    with pytest.raises(FusionInputError, match="escapes the synchronized package"):
        load_fusion_input(root)


def test_ambiguous_radar_latency_calibration_fails_closed(tmp_path):
    root = _write_package(tmp_path)
    combined_path = root / "sync" / "manifest.json"
    _edit_json(
        combined_path,
        lambda payload: payload["uncertainty"].__setitem__(
            "radar_trigger_latency_calibrated", "yes"
        ),
    )

    with pytest.raises(
        FusionInputError,
        match="incomplete latency calibration|must be boolean",
    ):
        load_fusion_input(root)


def test_missing_edge_uncertainty_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path)
    _edit_json(
        root / "sync" / "manifest.json",
        lambda payload: payload["uncertainty"].__setitem__(
            "trigger_edge_uncertainty_ns", None
        ),
    )

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert "radar_reference_edge_uncertainty_missing" in (
        capture.quality.readiness_failures
    )


def test_not_characterized_status_never_reports_fusion_ready(tmp_path):
    root = _write_package(tmp_path)
    _edit_json(
        root / "sync" / "manifest.json",
        lambda payload: payload["uncertainty"].__setitem__(
            "status", "not_characterized"
        ),
    )

    capture = load_fusion_input(root)

    assert capture.fusion_ready is False
    assert "timing_uncertainty_not_characterized" in (
        capture.quality.readiness_failures
    )


def test_userspace_set_completion_is_algorithm_ready_without_calibration(tmp_path):
    root = _write_package(
        tmp_path,
        calibrated=False,
        hardware_validated=False,
    )

    def userspace_timeline(payload):
        payload["timestamp_quality"] = "userspace_set_completed"
        payload["provenance"].update(
            {
                "source": "userspace_set_completed",
                "edge_observation": "userspace_gpio_set_completion",
                "semantics": (
                    "GPIO set completion used as the hardware SYNC reference"
                ),
            }
        )

    _edit_json(root / "sync" / "timeline.json", userspace_timeline)
    _edit_json(
        root / "sync" / "manifest.json",
        lambda payload: payload.__setitem__(
            "timestamp_quality", "userspace_set_completed"
        ),
    )

    capture = load_fusion_input(root)

    assert capture.algorithm_ready is True
    assert capture.quality.algorithm_readiness_failures == ()
    assert capture.fusion_ready is False
    assert "hardware_sync_not_validated" in capture.quality.readiness_failures
