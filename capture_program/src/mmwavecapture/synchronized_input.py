"""Reader for the synchronized radar reference timeline."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple, Union

import numpy as np

from mmwavecapture.algorithm_input import (
    SCHEMA_NAME as RADAR_ALGORITHM_SCHEMA_NAME,
    SCHEMA_VERSION as RADAR_ALGORITHM_SCHEMA_VERSION,
)

TIMELINE_MANIFEST_FILENAME = "timeline.json"
COMBINED_MANIFEST_FILENAME = "manifest.json"
CAPTURE_STATUS_FILENAME = "status.json"
SYNC_MODES = ("software_timestamp", "hardware_trigger")
HARDWARE_TIMESTAMP_QUALITIES = (
    "kernel_loopback_edge",
    "userspace_set_completed",
)


class SynchronizedInputError(RuntimeError):
    """Raised when a synchronized timeline is incomplete or inconsistent."""


@dataclass(frozen=True)
class SynchronizedTimeline:
    radar_frame_monotonic_ns: np.ndarray
    manifest: Mapping[str, Any]
    combined_manifest: Mapping[str, Any]
    directory: pathlib.Path


def _resolve_directory(path: Union[str, pathlib.Path]) -> pathlib.Path:
    candidate = pathlib.Path(path)
    if candidate.is_file() and candidate.name == TIMELINE_MANIFEST_FILENAME:
        return candidate.parent
    if (candidate / TIMELINE_MANIFEST_FILENAME).is_file():
        return candidate
    if (candidate / "sync" / TIMELINE_MANIFEST_FILENAME).is_file():
        return candidate / "sync"
    matches = list(candidate.glob(f"*/sync/{TIMELINE_MANIFEST_FILENAME}"))
    if len(matches) == 1:
        return matches[0].parent
    if len(matches) > 1:
        raise SynchronizedInputError(
            "multiple synchronized timelines found; select one capture directory"
        )
    raise FileNotFoundError(candidate / TIMELINE_MANIFEST_FILENAME)


def _read_json_object(path: pathlib.Path, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SynchronizedInputError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise SynchronizedInputError(f"{label} must be a JSON object")
    return payload


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SynchronizedInputError(f"{label} must be a positive integer")
    return value


def _resolve_contained_path(
    base: pathlib.Path,
    relative: Any,
    label: str,
) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise SynchronizedInputError(f"{label} has no valid filename")
    resolved_base = base.resolve()
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError as exc:
        raise SynchronizedInputError(f"{label} escapes its package") from exc
    if not resolved.is_file():
        raise SynchronizedInputError(f"{label} is missing: {resolved}")
    return resolved


def _validate_complete_combined_manifest(
    directory: pathlib.Path,
) -> Mapping[str, Any]:
    combined = _read_json_object(
        directory / COMBINED_MANIFEST_FILENAME,
        "combined synchronization manifest",
    )
    if combined.get("schema_version") != 1 or combined.get("status") != "complete":
        raise SynchronizedInputError(
            "combined synchronization manifest is not complete schema v1"
        )
    sync_mode = combined.get("sync_mode")
    if sync_mode not in SYNC_MODES:
        raise SynchronizedInputError("combined manifest has an unsupported sync_mode")
    quality = combined.get("timestamp_quality")
    if sync_mode == "software_timestamp":
        if quality != "sensor_start_bracket_estimate":
            raise SynchronizedInputError(
                "software combined manifest has inconsistent timestamp_quality"
            )
    elif quality not in HARDWARE_TIMESTAMP_QUALITIES:
        raise SynchronizedInputError(
            "hardware combined manifest has inconsistent timestamp_quality"
        )
    hardware_validated = combined.get("hardware_validated")
    if not isinstance(hardware_validated, bool):
        raise SynchronizedInputError(
            "combined manifest hardware_validated must be boolean"
        )

    clock = combined.get("clock")
    if (
        not isinstance(clock, Mapping)
        or clock.get("alignment_clock") != "CLOCK_MONOTONIC"
        or clock.get("unit") != "nanoseconds"
        or clock.get("wall_time_used_for_alignment") is not False
    ):
        raise SynchronizedInputError("combined manifest has an invalid clock contract")
    validation = combined.get("validation")
    if (
        not isinstance(validation, Mapping)
        or validation.get("status") != "complete"
        or validation.get("sync_timeline_exported") is not True
        or validation.get("hardware_validated") is not hardware_validated
    ):
        raise SynchronizedInputError(
            "combined manifest does not validate the synchronized timeline"
        )
    uncertainty = combined.get("uncertainty")
    if not isinstance(uncertainty, Mapping):
        raise SynchronizedInputError(
            "combined manifest uncertainty disagrees with hardware validation"
        )
    uncertainty_status = uncertainty.get("status")
    if sync_mode == "hardware_trigger" and not hardware_validated:
        valid_uncertainty_status = uncertainty_status == "hardware_not_bench_validated"
    elif sync_mode == "hardware_trigger":
        valid_uncertainty_status = uncertainty_status in (
            "not_characterized",
            "characterized",
        )
    else:
        valid_uncertainty_status = uncertainty_status == "not_characterized"
    if not valid_uncertainty_status:
        raise SynchronizedInputError(
            "combined manifest uncertainty disagrees with hardware validation"
        )
    if uncertainty_status == "characterized" and (
        uncertainty.get("radar_trigger_latency_calibrated") is not True
        or uncertainty.get("adxl_filter_group_delay_calibrated") is not True
    ):
        raise SynchronizedInputError(
            "characterized synchronization has incomplete latency calibration"
        )
    timestamp_semantics = combined.get("timestamp_semantics")
    if (
        not isinstance(timestamp_semantics, Mapping)
        or timestamp_semantics.get("pcap_is_frame_start") is not False
    ):
        raise SynchronizedInputError(
            "combined manifest must state that PCAP receive time is not frame start"
        )
    files = combined.get("files")
    sync_files = files.get("sync") if isinstance(files, Mapping) else None
    radar_files = files.get("radar") if isinstance(files, Mapping) else None
    if not isinstance(sync_files, Mapping) or not isinstance(radar_files, Mapping):
        raise SynchronizedInputError("combined manifest has no synchronized files map")
    expected_sync_files = {
        "timeline_manifest": f"sync/{TIMELINE_MANIFEST_FILENAME}",
        "radar_frame_monotonic_ns": "sync/radar_frame_monotonic_ns.npy",
    }
    for field, expected in expected_sync_files.items():
        if sync_files.get(field) != expected:
            raise SynchronizedInputError(
                f"combined manifest sync file {field} is missing or inconsistent"
            )
    radar_algorithm_relative = radar_files.get("algorithm_input_manifest")
    if not isinstance(radar_algorithm_relative, str):
        raise SynchronizedInputError(
            "combined manifest has no decoded radar algorithm manifest"
        )
    return combined


def _validate_capture_status_if_present(directory: pathlib.Path) -> None:
    candidates = (
        directory.parent / CAPTURE_STATUS_FILENAME,
        directory.parent.parent / CAPTURE_STATUS_FILENAME,
    )
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not candidate.is_file():
            continue
        seen.add(resolved)
        status = _read_json_object(candidate, "capture status")
        if status.get("schema_version") != 1 or status.get("status") != "complete":
            raise SynchronizedInputError(
                f"capture root status is not complete: {candidate}"
            )


def _validate_radar_algorithm_manifest(
    directory: pathlib.Path,
    timeline: Mapping[str, Any],
    combined: Mapping[str, Any],
    frames: int,
    frame_period_ns: int,
) -> None:
    reference = timeline.get("radar_algorithm_manifest")
    hardware_root = directory.parent
    if not isinstance(reference, str) or not reference:
        raise SynchronizedInputError(
            "timeline has no decoded radar algorithm manifest reference"
        )
    radar_path = (directory / reference).resolve()
    try:
        radar_path.relative_to(hardware_root.resolve())
    except ValueError as exc:
        raise SynchronizedInputError(
            "radar algorithm manifest escapes the synchronized package"
        ) from exc
    if not radar_path.is_file():
        raise SynchronizedInputError(
            f"decoded radar algorithm manifest is missing: {radar_path}"
        )

    files = combined["files"]
    combined_reference = files["radar"]["algorithm_input_manifest"]
    combined_radar_path = (hardware_root / combined_reference).resolve()
    if combined_radar_path != radar_path:
        raise SynchronizedInputError(
            "timeline and combined manifest disagree on radar algorithm input"
        )
    radar_manifest = _read_json_object(
        radar_path, "decoded radar algorithm manifest"
    )
    if (
        radar_manifest.get("schema") != RADAR_ALGORITHM_SCHEMA_NAME
        or radar_manifest.get("schema_version") != RADAR_ALGORITHM_SCHEMA_VERSION
    ):
        raise SynchronizedInputError(
            "decoded radar algorithm manifest has an unsupported schema"
        )
    packet_integrity = radar_manifest.get("packet_integrity")
    if (
        not isinstance(packet_integrity, Mapping)
        or packet_integrity.get("complete") is not True
        or timeline.get("radar_packet_integrity_complete") is not True
    ):
        raise SynchronizedInputError(
            "decoded radar packet integrity is not certified complete"
        )
    radar = radar_manifest.get("radar")
    if not isinstance(radar, Mapping):
        raise SynchronizedInputError("decoded radar manifest has no radar metadata")
    radar_frames_value = radar.get("frames")
    radar_period_value = radar.get("frame_period_s")
    if (
        isinstance(radar_frames_value, bool)
        or not isinstance(radar_frames_value, int)
        or isinstance(radar_period_value, bool)
        or not isinstance(radar_period_value, (int, float))
    ):
        raise SynchronizedInputError("decoded radar frame metadata is invalid")
    try:
        radar_frames = radar_frames_value
        radar_period_ns = int(
            round(float(radar_period_value) * 1_000_000_000.0)
        )
    except (ValueError, OverflowError) as exc:
        raise SynchronizedInputError(
            "decoded radar frame metadata is invalid"
        ) from exc
    arrays = radar_manifest.get("arrays")
    adc_cube = arrays.get("adc_cube") if isinstance(arrays, Mapping) else None
    adc_shape = adc_cube.get("shape") if isinstance(adc_cube, Mapping) else None
    if (
        radar_frames != frames
        or radar_period_ns != frame_period_ns
        or not isinstance(adc_shape, list)
        or not adc_shape
        or isinstance(adc_shape[0], bool)
        or not isinstance(adc_shape[0], int)
        or adc_shape[0] != frames
    ):
        raise SynchronizedInputError(
            "timeline disagrees with decoded radar frame metadata"
        )


def _validate_timeline_metadata(
    manifest: Mapping[str, Any],
    combined: Mapping[str, Any],
) -> Tuple[int, int, Mapping[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("status") != "complete":
        raise SynchronizedInputError("synchronized timeline is not complete schema v1")
    if manifest.get("clock") != "CLOCK_MONOTONIC":
        raise SynchronizedInputError("synchronized timeline has an unsupported clock")
    if manifest.get("unit") != "nanoseconds":
        raise SynchronizedInputError("synchronized timeline unit must be nanoseconds")
    sync_mode = manifest.get("sync_mode")
    if sync_mode not in SYNC_MODES or sync_mode != combined.get("sync_mode"):
        raise SynchronizedInputError(
            "timeline sync_mode is unsupported or disagrees with combined manifest"
        )
    quality = manifest.get("timestamp_quality")
    if quality != combined.get("timestamp_quality"):
        raise SynchronizedInputError(
            "timeline timestamp_quality disagrees with combined manifest"
        )
    hardware_validated = manifest.get("hardware_validated")
    if (
        not isinstance(hardware_validated, bool)
        or hardware_validated != combined.get("hardware_validated")
    ):
        raise SynchronizedInputError(
            "timeline hardware_validated disagrees with combined manifest"
        )

    frames = _positive_integer(manifest.get("frame_count"), "frame_count")
    frame_period_ns = _positive_integer(
        manifest.get("nominal_frame_period_ns"), "nominal_frame_period_ns"
    )
    description = manifest.get("array")
    if not isinstance(description, Mapping):
        raise SynchronizedInputError("synchronized timeline has no array metadata")
    expected_description = {
        "file": "radar_frame_monotonic_ns.npy",
        "dtype": "int64",
        "shape": [frames],
        "axes": ["radar_frame"],
    }
    for field, expected in expected_description.items():
        if description.get(field) != expected:
            raise SynchronizedInputError(
                f"synchronized timeline array {field} metadata is inconsistent"
            )

    provenance = manifest.get("provenance")
    if (
        not isinstance(provenance, Mapping)
        or provenance.get("is_measured_radar_frame_start") is not False
        or not isinstance(provenance.get("semantics"), str)
    ):
        raise SynchronizedInputError("synchronized timeline provenance is invalid")
    if sync_mode == "software_timestamp":
        if (
            quality != "sensor_start_bracket_estimate"
            or provenance.get("source")
            != "sensor_start_bracket_midpoint_plus_nominal_period"
        ):
            raise SynchronizedInputError(
                "software timeline provenance disagrees with timestamp quality"
            )
        before = provenance.get("sensor_start_before_monotonic_ns")
        after = provenance.get("sensor_start_after_monotonic_ns")
        if (
            isinstance(before, bool)
            or not isinstance(before, int)
            or isinstance(after, bool)
            or not isinstance(after, int)
            or before <= 0
            or after < before
        ):
            raise SynchronizedInputError(
                "software timeline has an invalid sensorStart bracket"
            )
    else:
        expected_observation = (
            "physical_loopback_input"
            if quality == "kernel_loopback_edge"
            else "userspace_gpio_set_completion"
        )
        if (
            quality not in HARDWARE_TIMESTAMP_QUALITIES
            or provenance.get("source") != quality
            or provenance.get("edge_observation") != expected_observation
        ):
            raise SynchronizedInputError(
                "hardware timeline provenance disagrees with timestamp quality"
            )
    return frames, frame_period_ns, description


def load_synchronized_timeline(
    path: Union[str, pathlib.Path],
    *,
    mmap_mode: Optional[str] = "r",
) -> SynchronizedTimeline:
    """Load and validate the common Pi ``CLOCK_MONOTONIC`` radar timeline."""

    directory = _resolve_directory(path)
    combined = _validate_complete_combined_manifest(directory)
    _validate_capture_status_if_present(directory)
    manifest = _read_json_object(
        directory / TIMELINE_MANIFEST_FILENAME,
        "synchronized timeline manifest",
    )
    expected_frames, frame_period_ns, description = _validate_timeline_metadata(
        manifest, combined
    )
    _validate_radar_algorithm_manifest(
        directory,
        manifest,
        combined,
        expected_frames,
        frame_period_ns,
    )
    array_path = _resolve_contained_path(
        directory,
        description["file"],
        "synchronized timeline array",
    )
    try:
        frame_times = np.load(array_path, mmap_mode=mmap_mode, allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise SynchronizedInputError(
            f"cannot load synchronized timeline array {array_path}: {exc}"
        ) from exc
    if frame_times.dtype != np.dtype(np.int64) or frame_times.shape != (
        expected_frames,
    ):
        raise SynchronizedInputError("synchronized radar timeline shape/dtype mismatch")
    if np.any(frame_times <= 0) or (
        frame_times.size > 1 and np.any(np.diff(frame_times) <= 0)
    ):
        raise SynchronizedInputError(
            "synchronized radar timestamps are not positive and increasing"
        )
    if frame_times.size > 1:
        intervals = np.diff(frame_times)
        if manifest["sync_mode"] == "software_timestamp":
            if np.any(intervals != frame_period_ns):
                raise SynchronizedInputError(
                    "software timeline intervals disagree with nominal frame period"
                )
        elif np.any(intervals < frame_period_ns):
            raise SynchronizedInputError(
                "hardware timeline contains a trigger interval below the radar period"
            )
    return SynchronizedTimeline(
        radar_frame_monotonic_ns=frame_times,
        manifest=manifest,
        combined_manifest=combined,
        directory=directory,
    )
