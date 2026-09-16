import json
import struct

import numpy as np
import pytest

from mmwavecapture.adxl355_input import (
    Adxl355InputError,
    RAW_HEADER_BYTES,
    RECORD_DTYPE,
    export_adxl355_input,
    load_adxl355_input,
)


def write_capture(
    tmp_path,
    *,
    line_seq=(1, 2, 3),
    fifo_overruns=0,
    mock=True,
    header_flags=None,
    fifo_entries=None,
    x_raw=None,
    summary_overrides=None,
    config_overrides=None,
):
    raw_path = tmp_path / "adxl355.raw"
    summary_path = tmp_path / "summary.json"
    header = bytearray(RAW_HEADER_BYTES)
    header[:8] = b"ADXLRW01"
    if header_flags is None:
        header_flags = 1 if mock else 0
    struct.pack_into("<HHHH", header, 8, 1, 64, 48, header_flags)
    struct.pack_into("<I", header, 16, 1_000_000)
    struct.pack_into("<H", header, 20, 2)
    struct.pack_into("<Q", header, 24, 1_800_000_000_000_000_000)
    struct.pack_into("<Q", header, 32, 10_000_000_000)
    struct.pack_into("<q", header, 40, 1_780_000)

    records = np.zeros(len(line_seq), dtype=RECORD_DTYPE)
    records["sample_seq"] = np.arange(len(line_seq), dtype=np.uint64)
    records["line_seqno"] = line_seq
    records["drdy_monotonic_ns"] = [11_000_000_000, 11_001_000_000, 11_002_000_000]
    records["spi_complete_monotonic_ns"] = records["drdy_monotonic_ns"] + 25_000
    records["x_raw"] = [256_000, 0, -256_000]
    records["y_raw"] = [0, 128_000, 0]
    records["z_raw"] = [-128_000, 0, 128_000]
    records["temp_raw"] = [100, 101, 102]
    if x_raw is not None:
        records["x_raw"][0] = x_raw
    if fifo_entries is None:
        fifo_entries = 0 if mock else 3
    records["fifo_entries"] = fifo_entries

    raw_path.write_bytes(bytes(header) + records.tobytes())
    config = {
        "spi_device": "/dev/spidev0.0",
        "gpiochip": "/dev/gpiochip0",
        "drdy_line": 25,
        "odr_hz": 1000,
        "range_g": 2,
        "spi_hz": 5_000_000,
        "max_samples": 0,
    }
    config.update(config_overrides or {})
    summary = {
        "schema_version": 1,
        "status": "complete",
        "samples": len(records),
        "samples_written": len(records),
        "first_drdy_monotonic_ns": int(records["drdy_monotonic_ns"][0]),
        "last_drdy_monotonic_ns": int(records["drdy_monotonic_ns"][-1]),
        "line_seq_gaps": 0,
        "fifo_overruns": fifo_overruns,
        "gpio_backlog_events": 0,
        "fifo_protocol_errors": 0,
        "fifo_xyz_mismatches": 0,
        "fifo_xyz_sets_drained": 0 if mock else len(records),
        "max_fifo_entries": fifo_entries,
        "mock": mock,
        "sample_source": "mock" if mock else "FIFO_DATA_oldest",
        "timestamp_pairing": (
            "synthetic" if mock else "one_drdy_edge_to_one_fifo_xyz"
        ),
        "clock": "CLOCK_MONOTONIC",
        "timestamp_semantics": "drdy_edge",
        "start_realtime_ns": 1_800_000_000_000_000_000,
        "start_monotonic_ns": 10_000_000_000,
        "group_delay_ns": 1_780_000,
        "group_delay_calibrated": True,
        "config": config,
    }
    summary.update(summary_overrides or {})
    summary_path.write_text(
        json.dumps(summary),
        encoding="utf-8",
    )
    return raw_path, summary_path


def test_export_and_load_preserve_raw_time_and_calibrated_units(tmp_path):
    raw_path, summary_path = write_capture(tmp_path)
    output = tmp_path / "algorithm_input"

    manifest_path = export_adxl355_input(raw_path, summary_path, output)
    capture = load_adxl355_input(output)

    assert manifest_path == output / "manifest.json"
    assert capture.acceleration_raw.shape == (3, 3)
    assert capture.sample_times_s.tolist() == [0.0, 0.001, 0.002]
    np.testing.assert_allclose(
        capture.acceleration_mps2[0],
        [9.80665, 0.0, -4.903325],
    )
    assert capture.estimated_sample_monotonic_ns[0] == 10_998_220_000
    assert capture.manifest["capture"]["group_delay_calibrated"] is True
    assert capture.manifest["conversion"]["calibration_applied"] is False


def test_line_sequence_gap_fails_closed(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, line_seq=(1, 3, 4))

    with pytest.raises(Adxl355InputError, match="line sequence contains a gap"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_native_fifo_overrun_summary_fails_closed(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, fifo_overruns=1)

    with pytest.raises(Adxl355InputError, match="FIFO overrun"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_first_line_sequence_must_be_one(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, line_seq=(2, 3, 4))

    with pytest.raises(Adxl355InputError, match="first DRDY line sequence is not 1"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_header_and_summary_mock_provenance_must_match(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, header_flags=0, mock=True)

    with pytest.raises(Adxl355InputError, match="mock provenance disagrees"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_mock_records_must_have_empty_fifo_depth(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, fifo_entries=3)

    with pytest.raises(Adxl355InputError, match="per-record FIFO depth"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_axis_values_must_fit_signed_20_bits(tmp_path):
    raw_path, summary_path = write_capture(tmp_path, x_raw=524_288)

    with pytest.raises(Adxl355InputError, match="outside signed 20-bit range"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_summary_max_fifo_entries_must_match_records(tmp_path):
    raw_path, summary_path = write_capture(
        tmp_path, summary_overrides={"max_fifo_entries": 3}
    )

    with pytest.raises(Adxl355InputError, match="max_fifo_entries disagrees"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_summary_config_must_match_raw_header(tmp_path):
    raw_path, summary_path = write_capture(
        tmp_path, config_overrides={"odr_hz": 500}
    )

    with pytest.raises(Adxl355InputError, match="config ODR disagrees"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")


def test_aborted_summary_is_never_exportable(tmp_path):
    raw_path, summary_path = write_capture(
        tmp_path,
        summary_overrides={
            "status": "aborted",
            "native_prior_status": "complete",
        },
    )

    with pytest.raises(Adxl355InputError, match="did not finish completely"):
        export_adxl355_input(raw_path, summary_path, tmp_path / "algorithm_input")
