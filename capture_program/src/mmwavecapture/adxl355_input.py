"""Validated, algorithm-facing ADXL355 capture export.

The native collector writes an append-only binary stream whose timing source is
the kernel timestamp of each DRDY rising edge.  This module is the only place
that interprets that binary ABI.  It validates sequence and timing continuity
before publishing NumPy arrays atomically.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import shutil
import struct
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

import numpy as np


SCHEMA_NAME = "mmwavecapture.adxl355-input"
SCHEMA_VERSION = 1
MANIFEST_FILENAME = "manifest.json"
RAW_MAGIC = b"ADXLRW01"
RAW_VERSION = 1
RAW_HEADER_BYTES = 64
RAW_RECORD_BYTES = 48
RAW_FLAG_MOCK = 0x0001
RAW_KNOWN_FLAGS = RAW_FLAG_MOCK
SUPPORTED_ODR_HZ = frozenset((125, 250, 500, 1000, 2000, 4000))
STANDARD_GRAVITY_MPS2 = 9.80665
SENSITIVITY_LSB_PER_G = {2: 256_000.0, 4: 128_000.0, 8: 64_000.0}

RECORD_DTYPE = np.dtype(
    [
        ("sample_seq", "<u8"),
        ("line_seqno", "<u8"),
        ("drdy_monotonic_ns", "<u8"),
        ("spi_complete_monotonic_ns", "<u8"),
        ("x_raw", "<i4"),
        ("y_raw", "<i4"),
        ("z_raw", "<i4"),
        ("temp_raw", "<i2"),
        ("status", "u1"),
        ("fifo_entries", "u1"),
    ],
    align=False,
)
if RECORD_DTYPE.itemsize != RAW_RECORD_BYTES:  # pragma: no cover - import invariant
    raise RuntimeError("ADXL355 record dtype does not match the native ABI")


class Adxl355InputError(RuntimeError):
    """Raised when a native ADXL355 capture is incomplete or inconsistent."""


@dataclass(frozen=True)
class Adxl355RawHeader:
    flags: int
    odr_millihz: int
    range_g: int
    start_realtime_ns: int
    start_monotonic_ns: int
    group_delay_ns: int


@dataclass(frozen=True)
class Adxl355Capture:
    acceleration_raw: np.ndarray
    acceleration_mps2: np.ndarray
    drdy_monotonic_ns: np.ndarray
    estimated_sample_monotonic_ns: np.ndarray
    sample_times_s: np.ndarray
    manifest: Mapping[str, Any]
    directory: pathlib.Path


def _parse_header(data: bytes) -> Adxl355RawHeader:
    if len(data) != RAW_HEADER_BYTES:
        raise Adxl355InputError("ADXL355 raw header is truncated")
    if data[:8] != RAW_MAGIC:
        raise Adxl355InputError(f"invalid ADXL355 raw magic {data[:8]!r}")
    version, header_bytes, record_bytes, flags = struct.unpack_from("<HHHH", data, 8)
    if version != RAW_VERSION:
        raise Adxl355InputError(
            f"unsupported ADXL355 raw version {version}; expected {RAW_VERSION}"
        )
    if header_bytes != RAW_HEADER_BYTES or record_bytes != RAW_RECORD_BYTES:
        raise Adxl355InputError(
            "ADXL355 raw header/record size disagrees with schema version 1"
        )
    odr_millihz = struct.unpack_from("<I", data, 16)[0]
    range_g = struct.unpack_from("<H", data, 20)[0]
    start_realtime_ns = struct.unpack_from("<Q", data, 24)[0]
    start_monotonic_ns = struct.unpack_from("<Q", data, 32)[0]
    group_delay_ns = struct.unpack_from("<q", data, 40)[0]
    if flags & ~RAW_KNOWN_FLAGS:
        raise Adxl355InputError(f"ADXL355 raw header has unknown flags 0x{flags:04x}")
    if (
        odr_millihz % 1000 != 0
        or odr_millihz // 1000 not in SUPPORTED_ODR_HZ
    ):
        raise Adxl355InputError("ADXL355 raw header has an unsupported ODR")
    if range_g not in SENSITIVITY_LSB_PER_G:
        raise Adxl355InputError(f"unsupported ADXL355 range ±{range_g}g")
    if start_realtime_ns <= 0 or start_monotonic_ns <= 0:
        raise Adxl355InputError("ADXL355 raw start clocks must be positive")
    if group_delay_ns < 0:
        raise Adxl355InputError("ADXL355 group delay cannot be negative")
    return Adxl355RawHeader(
        flags=flags,
        odr_millihz=odr_millihz,
        range_g=range_g,
        start_realtime_ns=start_realtime_ns,
        start_monotonic_ns=start_monotonic_ns,
        group_delay_ns=group_delay_ns,
    )


def read_adxl355_raw(
    raw_file: Union[str, pathlib.Path],
) -> tuple[Adxl355RawHeader, np.ndarray]:
    """Open and structurally validate a native capture without copying records."""

    path = pathlib.Path(raw_file)
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size < RAW_HEADER_BYTES:
        raise Adxl355InputError(f"ADXL355 raw file is too small: {path}")
    payload_bytes = size - RAW_HEADER_BYTES
    if payload_bytes % RAW_RECORD_BYTES:
        raise Adxl355InputError(
            f"ADXL355 raw payload has {payload_bytes} bytes, not a multiple of "
            f"{RAW_RECORD_BYTES}"
        )
    with open(path, "rb") as stream:
        header = _parse_header(stream.read(RAW_HEADER_BYTES))
    count = payload_bytes // RAW_RECORD_BYTES
    if count <= 0:
        raise Adxl355InputError("ADXL355 raw capture contains no samples")
    records = np.memmap(
        path,
        dtype=RECORD_DTYPE,
        mode="r",
        offset=RAW_HEADER_BYTES,
        shape=(count,),
    )
    return header, records


def _load_summary(
    path: pathlib.Path,
    header: Adxl355RawHeader,
    records: np.ndarray,
) -> Mapping[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("schema_version") != 1:
        raise Adxl355InputError("unsupported or missing ADXL355 summary schema")
    if summary.get("status") != "complete":
        raise Adxl355InputError("ADXL355 native collector did not finish completely")
    expected_samples = int(records.shape[0])

    def summary_int(field: str) -> int:
        value = summary.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise Adxl355InputError(
                f"ADXL355 summary field {field!r} is not an integer"
            )
        return value

    if (
        summary_int("samples") != expected_samples
        or summary_int("samples_written") != expected_samples
    ):
        raise Adxl355InputError(
            "ADXL355 summary sample count disagrees with the raw file"
        )
    for field, label in (
        ("line_seq_gaps", "DRDY line sequence gaps"),
        ("fifo_overruns", "FIFO overrun"),
        ("gpio_backlog_events", "GPIO event backlog"),
        ("fifo_protocol_errors", "FIFO protocol errors"),
        ("fifo_xyz_mismatches", "FIFO/current-data mismatch"),
    ):
        if summary_int(field) != 0:
            raise Adxl355InputError(f"ADXL355 summary reports {label}")
    is_mock = summary.get("mock")
    if not isinstance(is_mock, bool):
        raise Adxl355InputError("ADXL355 summary has no mock/real provenance")
    header_is_mock = bool(header.flags & RAW_FLAG_MOCK)
    if is_mock != header_is_mock:
        raise Adxl355InputError(
            "ADXL355 summary mock provenance disagrees with the raw header"
        )
    drained = summary_int("fifo_xyz_sets_drained")
    if is_mock:
        source_ok = summary.get("sample_source") == "mock"
        pairing_ok = summary.get("timestamp_pairing") == "synthetic"
        drain_ok = drained == 0
    else:
        source_ok = summary.get("sample_source") == "FIFO_DATA_oldest"
        pairing_ok = (
            summary.get("timestamp_pairing") == "one_drdy_edge_to_one_fifo_xyz"
        )
        drain_ok = drained == expected_samples
    if not source_ok or not pairing_ok or not drain_ok:
        raise Adxl355InputError(
            "ADXL355 summary has inconsistent FIFO sample/timestamp provenance"
        )
    observed_max_fifo_entries = int(np.max(records["fifo_entries"]))
    if summary_int("max_fifo_entries") != observed_max_fifo_entries:
        raise Adxl355InputError(
            "ADXL355 summary max_fifo_entries disagrees with the raw records"
        )
    if summary.get("clock") != "CLOCK_MONOTONIC":
        raise Adxl355InputError("ADXL355 summary uses an unsupported event clock")
    if summary.get("timestamp_semantics") != "drdy_edge":
        raise Adxl355InputError("ADXL355 summary timestamp is not a DRDY edge")
    if (
        summary_int("first_drdy_monotonic_ns")
        != int(records["drdy_monotonic_ns"][0])
        or summary_int("last_drdy_monotonic_ns")
        != int(records["drdy_monotonic_ns"][-1])
    ):
        raise Adxl355InputError(
            "ADXL355 summary first/last DRDY timestamp disagrees with raw data"
        )
    if summary_int("start_realtime_ns") != header.start_realtime_ns:
        raise Adxl355InputError(
            "ADXL355 summary start_realtime_ns disagrees with the raw header"
        )
    if summary_int("start_monotonic_ns") != header.start_monotonic_ns:
        raise Adxl355InputError(
            "ADXL355 summary start_monotonic_ns disagrees with the raw header"
        )
    if summary_int("group_delay_ns") != header.group_delay_ns:
        raise Adxl355InputError(
            "ADXL355 summary group_delay_ns disagrees with the raw header"
        )
    calibrated = summary.get("group_delay_calibrated")
    if not isinstance(calibrated, bool) or calibrated != (header.group_delay_ns > 0):
        raise Adxl355InputError(
            "ADXL355 summary group-delay calibration provenance is inconsistent"
        )

    config = summary.get("config")
    if not isinstance(config, Mapping):
        raise Adxl355InputError("ADXL355 summary config is not an object")

    def config_int(field: str) -> int:
        value = config.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise Adxl355InputError(
                f"ADXL355 summary config field {field!r} is not an integer"
            )
        return value

    if config_int("odr_hz") * 1000 != header.odr_millihz:
        raise Adxl355InputError(
            "ADXL355 summary config ODR disagrees with the raw header"
        )
    if config_int("range_g") != header.range_g:
        raise Adxl355InputError(
            "ADXL355 summary config range disagrees with the raw header"
        )
    spi_hz = config_int("spi_hz")
    if not 1 <= spi_hz <= 10_000_000:
        raise Adxl355InputError("ADXL355 summary config SPI clock is out of range")
    return summary


def _validate_records(records: np.ndarray, *, is_mock: bool) -> None:
    count = records.shape[0]
    expected = np.arange(count, dtype=np.uint64)
    if not np.array_equal(records["sample_seq"], expected):
        raise Adxl355InputError("ADXL355 sample sequence is not contiguous from zero")
    if int(records["line_seqno"][0]) != 1:
        raise Adxl355InputError("ADXL355 first DRDY line sequence is not 1")
    if count > 1:
        if np.any(np.diff(records["line_seqno"]) != 1):
            raise Adxl355InputError("ADXL355 DRDY line sequence contains a gap")
        if np.any(
            np.diff(records["drdy_monotonic_ns"].astype(np.int64)) <= 0
        ):
            raise Adxl355InputError("ADXL355 DRDY timestamps are not strictly increasing")
    if np.any(
        records["spi_complete_monotonic_ns"] < records["drdy_monotonic_ns"]
    ):
        raise Adxl355InputError("ADXL355 SPI completion precedes its DRDY edge")
    if np.any(records["status"] & np.uint8(0x04)):
        raise Adxl355InputError("ADXL355 STATUS reports FIFO overrun")
    expected_fifo_entries = 0 if is_mock else 3
    if np.any(records["fifo_entries"] != np.uint8(expected_fifo_entries)):
        raise Adxl355InputError(
            "ADXL355 per-record FIFO depth disagrees with capture provenance"
        )
    for axis in ("x_raw", "y_raw", "z_raw"):
        values = records[axis]
        if np.any(values < -524_288) or np.any(values > 524_287):
            raise Adxl355InputError(
                f"ADXL355 {axis} contains a value outside signed 20-bit range"
            )


def _array_description(filename: str, array: np.ndarray, axes: tuple[str, ...]) -> dict:
    return {
        "file": filename,
        "dtype": array.dtype.name,
        "shape": list(array.shape),
        "axes": list(axes),
    }


def export_adxl355_input(
    raw_file: Union[str, pathlib.Path],
    summary_file: Union[str, pathlib.Path],
    output_directory: Union[str, pathlib.Path],
) -> pathlib.Path:
    """Validate a complete native stream and atomically publish NumPy arrays."""

    raw_path = pathlib.Path(raw_file)
    summary_path = pathlib.Path(summary_file)
    output_path = pathlib.Path(output_directory)
    if output_path.exists():
        raise FileExistsError(f"ADXL355 algorithm input already exists: {output_path}")

    header, records = read_adxl355_raw(raw_path)
    summary = _load_summary(summary_path, header, records)
    _validate_records(records, is_mock=bool(summary["mock"]))

    acceleration_raw = np.column_stack(
        (records["x_raw"], records["y_raw"], records["z_raw"])
    ).astype(np.int32, copy=False)
    scale = STANDARD_GRAVITY_MPS2 / SENSITIVITY_LSB_PER_G[header.range_g]
    acceleration_mps2 = acceleration_raw.astype(np.float64) * scale
    drdy_monotonic_ns = np.asarray(records["drdy_monotonic_ns"], dtype=np.uint64)
    estimated_sample_monotonic_ns = (
        drdy_monotonic_ns.astype(np.int64) - np.int64(header.group_delay_ns)
    )
    sample_times_s = (
        drdy_monotonic_ns - drdy_monotonic_ns[0]
    ).astype(np.float64) / 1_000_000_000.0
    sample_seq = np.asarray(records["sample_seq"], dtype=np.uint64)
    line_seqno = np.asarray(records["line_seqno"], dtype=np.uint64)
    spi_complete_ns = np.asarray(
        records["spi_complete_monotonic_ns"], dtype=np.uint64
    )
    temperature_raw = np.asarray(records["temp_raw"], dtype=np.int16)
    status = np.asarray(records["status"], dtype=np.uint8)
    fifo_entries = np.asarray(records["fifo_entries"], dtype=np.uint8)

    arrays_to_write = {
        "acceleration_raw": (acceleration_raw, ("sample", "axis")),
        "acceleration_mps2": (acceleration_mps2, ("sample", "axis")),
        "drdy_monotonic_ns": (drdy_monotonic_ns, ("sample",)),
        "estimated_sample_monotonic_ns": (
            estimated_sample_monotonic_ns,
            ("sample",),
        ),
        "sample_times_s": (sample_times_s, ("sample",)),
        "sample_seq": (sample_seq, ("sample",)),
        "line_seqno": (line_seqno, ("sample",)),
        "spi_complete_monotonic_ns": (spi_complete_ns, ("sample",)),
        "temperature_raw": (temperature_raw, ("sample",)),
        "status": (status, ("sample",)),
        "fifo_entries": (fifo_entries, ("sample",)),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.parent / f".{output_path.name}.tmp-{uuid.uuid4().hex}"
    temporary.mkdir(exist_ok=False)
    try:
        arrays = {}
        for name, (array, axes) in arrays_to_write.items():
            filename = f"{name}.npy"
            np.save(temporary / filename, array, allow_pickle=False)
            arrays[name] = _array_description(filename, array, axes)

        manifest = {
            "schema": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.datetime.now().astimezone().isoformat(),
            "source": {
                "raw_file": f"../{raw_path.name}",
                "raw_size_bytes": raw_path.stat().st_size,
                "summary_file": f"../{summary_path.name}",
                "summary_size_bytes": summary_path.stat().st_size,
            },
            "capture": {
                "complete": True,
                "samples": int(records.shape[0]),
                "odr_hz_nominal": header.odr_millihz / 1000.0,
                "range_g": header.range_g,
                "start_realtime_ns": header.start_realtime_ns,
                "start_monotonic_ns": header.start_monotonic_ns,
                "group_delay_ns": header.group_delay_ns,
                "group_delay_calibrated": header.group_delay_ns > 0,
                "native_summary": dict(summary),
            },
            "timing": {
                "clock": "CLOCK_MONOTONIC",
                "drdy_monotonic_ns_semantics": "kernel DRDY rising-edge timestamp",
                "estimated_sample_monotonic_ns_semantics": (
                    "DRDY edge minus configured digital-filter group delay"
                ),
                "warning": (
                    "A zero group delay means uncalibrated, not zero physical "
                    "sensor latency."
                ),
            },
            "conversion": {
                "standard_gravity_mps2": STANDARD_GRAVITY_MPS2,
                "sensitivity_lsb_per_g": SENSITIVITY_LSB_PER_G[header.range_g],
                "calibration_applied": False,
            },
            "arrays": arrays,
        }
        (temporary / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output_path)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return output_path / MANIFEST_FILENAME


def load_adxl355_input(
    path: Union[str, pathlib.Path],
    *,
    mmap_mode: Optional[str] = "r",
) -> Adxl355Capture:
    """Load the stable ADXL355 arrays without interpreting the native stream."""

    directory = pathlib.Path(path)
    if directory.is_file() and directory.name == MANIFEST_FILENAME:
        directory = directory.parent
    manifest_path = directory / MANIFEST_FILENAME
    if not manifest_path.is_file():
        candidate = directory / "algorithm_input" / MANIFEST_FILENAME
        if candidate.is_file():
            directory = candidate.parent
            manifest_path = candidate
        else:
            raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA_NAME:
        raise Adxl355InputError(f"unsupported ADXL355 schema {manifest.get('schema')!r}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise Adxl355InputError(
            f"unsupported ADXL355 schema version {manifest.get('schema_version')}"
        )
    if manifest.get("capture", {}).get("complete") is not True:
        raise Adxl355InputError("ADXL355 algorithm input is not marked complete")

    arrays = manifest.get("arrays")
    if not isinstance(arrays, dict):
        raise Adxl355InputError("ADXL355 manifest has no arrays table")

    def load(name: str) -> np.ndarray:
        description = arrays.get(name)
        if not isinstance(description, dict):
            raise Adxl355InputError(f"ADXL355 array `{name}` is missing")
        filename = description.get("file")
        if not isinstance(filename, str):
            raise Adxl355InputError(f"ADXL355 array `{name}` has no file")
        base = directory.resolve()
        array_path = (directory / filename).resolve()
        try:
            array_path.relative_to(base)
        except ValueError as exc:
            raise Adxl355InputError(f"ADXL355 array `{name}` escapes package") from exc
        array = np.load(array_path, mmap_mode=mmap_mode, allow_pickle=False)
        if list(array.shape) != description.get("shape"):
            raise Adxl355InputError(f"ADXL355 array `{name}` shape mismatch")
        if array.dtype.name != description.get("dtype"):
            raise Adxl355InputError(f"ADXL355 array `{name}` dtype mismatch")
        return array

    acceleration_raw = load("acceleration_raw")
    acceleration_mps2 = load("acceleration_mps2")
    drdy_monotonic_ns = load("drdy_monotonic_ns")
    estimated_sample_monotonic_ns = load("estimated_sample_monotonic_ns")
    sample_times_s = load("sample_times_s")
    samples = int(manifest["capture"]["samples"])
    if acceleration_raw.shape != (samples, 3):
        raise Adxl355InputError("ADXL355 acceleration_raw has invalid shape")
    if acceleration_mps2.shape != (samples, 3):
        raise Adxl355InputError("ADXL355 acceleration_mps2 has invalid shape")
    for name, array in (
        ("drdy_monotonic_ns", drdy_monotonic_ns),
        ("estimated_sample_monotonic_ns", estimated_sample_monotonic_ns),
        ("sample_times_s", sample_times_s),
    ):
        if array.shape != (samples,):
            raise Adxl355InputError(f"ADXL355 `{name}` has invalid shape")
    if samples > 1 and np.any(
        np.diff(drdy_monotonic_ns.astype(np.int64)) <= 0
    ):
        raise Adxl355InputError("ADXL355 DRDY times are not strictly increasing")
    return Adxl355Capture(
        acceleration_raw=acceleration_raw,
        acceleration_mps2=acceleration_mps2,
        drdy_monotonic_ns=drdy_monotonic_ns,
        estimated_sample_monotonic_ns=estimated_sample_monotonic_ns,
        sample_times_s=sample_times_s,
        manifest=manifest,
        directory=directory,
    )
