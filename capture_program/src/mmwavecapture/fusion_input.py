"""Fail-closed loader for synchronized radar and ADXL355 fusion captures.

The fusion boundary preserves the two native ``CLOCK_MONOTONIC`` timelines.
It does not resample either sensor and never treats a DCA1000 packet receive
timestamp or a trigger/reference edge as the radar ADC sample time.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple, Union

import numpy as np

from mmwavecapture.adxl355_input import (
    Adxl355Capture,
    Adxl355InputError,
    load_adxl355_input,
)
from mmwavecapture.algorithm_input import (
    AlgorithmCapture,
    AlgorithmInputError,
    load_algorithm_input,
)
from mmwavecapture.synchronized_input import (
    SynchronizedInputError,
    SynchronizedTimeline,
    load_synchronized_timeline,
)
from mmwavecapture.fusion_calibration import (
    FusionCalibrationError,
    FusionValueCalibration,
    load_fusion_calibration,
)


SCHEMA_NAME = "mmwavecapture.fusion-input"
SCHEMA_VERSION = 1
MONOTONIC_CLOCK = "CLOCK_MONOTONIC"
SIMULATION_SCHEMA_NAME = "mmwavecapture.simulation-fusion-input"
SIMULATION_SCHEMA_VERSION = 1
MAGLEV_SIMULATION_SCENARIO = "measured_bridge_point4_transverse"
MAGLEV_SIMULATION_COHERENT_CENTER_OFFSET_NS = 1_907_100
MAGLEV_SIMULATION_COLD_START_DURATION_S = 0.20


class FusionInputError(RuntimeError):
    """Raised when a synchronized package cannot satisfy the fusion contract."""


@dataclass(frozen=True)
class FusionCalibration:
    """Timing and value-calibration facts carried by the source manifests."""

    radar_reference_edge_uncertainty_ns: Optional[int]
    radar_reference_to_adc_latency_ns: Optional[int]
    radar_reference_to_adc_latency_uncertainty_ns: Optional[int]
    radar_latency_calibrated: bool
    radar_latency_source: Optional[str]
    adxl_filter_group_delay_ns: int
    adxl_filter_group_delay_uncertainty_ns: Optional[int]
    adxl_group_delay_calibrated: bool
    adxl_group_delay_source: Optional[str]
    adxl_conversion_calibration_applied: bool


@dataclass(frozen=True)
class FusionQuality:
    """Integrity and readiness result after all cross-package checks."""

    fusion_ready: bool
    readiness_failures: Tuple[str, ...]
    radar_packet_integrity_complete: bool
    adxl_capture_complete: bool
    timeline_complete: bool
    hardware_validated: bool
    native_timeline_overlap: bool
    radar_timeline_fully_covered_by_adxl: bool
    algorithm_ready: bool = False
    algorithm_readiness_failures: Tuple[str, ...] = ()
    simulation_ready: bool = False


@dataclass(frozen=True)
class FusionProvenance:
    """Semantics of the timestamps exposed by :class:`FusionCapture`."""

    clock: str
    sync_mode: str
    radar_timestamp_quality: str
    radar_reference_source: str
    radar_reference_semantics: str
    radar_reference_is_measured_frame_start: bool
    adxl_drdy_semantics: str
    pcap_is_frame_start: bool


@dataclass(frozen=True)
class FusionCapture:
    """Validated, native-rate radar and acceleration data for fusion.

    ``radar_reference_monotonic_ns`` and ``adxl_drdy_monotonic_ns`` are the
    original Pi-clock observations. ``adxl_sample_monotonic_ns`` subtracts the
    ADXL digital-filter group delay recorded by its package. The optional
    ``radar_adc_sample_monotonic_ns`` is present when the synchronization
    manifest certifies a radar reference-to-ADC latency, or when an explicitly
    synthetic package declares a deterministic effective-observation model.
    """

    radar: AlgorithmCapture
    adxl355: Adxl355Capture
    timeline: SynchronizedTimeline
    radar_reference_monotonic_ns: np.ndarray
    adxl_drdy_monotonic_ns: np.ndarray
    adxl_sample_monotonic_ns: np.ndarray
    radar_adc_sample_monotonic_ns: Optional[np.ndarray]
    acceleration_structure_mps2: Optional[np.ndarray]
    calibration: FusionCalibration
    value_calibration: Optional[FusionValueCalibration]
    quality: FusionQuality
    provenance: FusionProvenance
    directory: pathlib.Path
    simulation_truth_time_ns: Optional[np.ndarray] = None
    simulation_truth_displacement_m: Optional[np.ndarray] = None
    simulation_truth_adxl_time_ns: Optional[np.ndarray] = None
    simulation_truth_acceleration_mps2: Optional[np.ndarray] = None

    @property
    def fusion_ready(self) -> bool:
        """Whether this package meets the v1 timing/integrity readiness bar."""

        return self.quality.fusion_ready

    @property
    def algorithm_ready(self) -> bool:
        """Whether the package can drive the asynchronous offline algorithm.

        This operational gate requires complete, hardware-trigger-controlled
        sensor timelines, but it deliberately does not claim calibrated GPIO,
        radar-ADC, ADXL filter, value, or geometry timing.  ``fusion_ready``
        remains the stronger calibrated/metrology gate.
        """

        return self.quality.algorithm_ready

    @property
    def simulation_ready(self) -> bool:
        """Whether an explicitly synthetic package passed its own contract."""

        return self.quality.simulation_ready

    @property
    def combined_manifest(self) -> Mapping[str, Any]:
        """The orchestration manifest cross-validated by this loader."""

        return self.timeline.combined_manifest


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FusionInputError(f"{label} must be an object")
    return value


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise FusionInputError(f"{label} must be boolean")
    return value


def _optional_nonnegative_integer(value: Any, label: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FusionInputError(f"{label} must be a nonnegative integer or null")
    return value


def _contained_manifest(
    base: pathlib.Path,
    relative: Any,
    label: str,
) -> pathlib.Path:
    resolved = _contained_file(base, relative, label)
    if resolved.name != "manifest.json":
        raise FusionInputError(f"{label} is not a manifest: {resolved}")
    return resolved


def _contained_file(
    base: pathlib.Path,
    relative: Any,
    label: str,
) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise FusionInputError(f"{label} has no valid filename")
    relative_path = pathlib.Path(relative)
    if relative_path.is_absolute():
        raise FusionInputError(f"{label} must be package-relative")
    resolved_base = base.resolve()
    resolved = (base / relative_path).resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError as exc:
        raise FusionInputError(f"{label} escapes the synchronized package") from exc
    if not resolved.is_file():
        raise FusionInputError(f"{label} is missing: {resolved}")
    return resolved


def _source_manifests(
    root: pathlib.Path,
    combined: Mapping[str, Any],
) -> Tuple[pathlib.Path, pathlib.Path]:
    files = _mapping(combined.get("files"), "combined manifest files")
    radar_files = _mapping(files.get("radar"), "combined radar files")
    adxl_files = _mapping(files.get("adxl355"), "combined ADXL355 files")
    radar_manifest = _contained_manifest(
        root,
        radar_files.get("algorithm_input_manifest"),
        "radar algorithm-input manifest",
    )
    adxl_manifest = _contained_manifest(
        root,
        adxl_files.get("algorithm_input_manifest"),
        "ADXL355 algorithm-input manifest",
    )
    if radar_manifest == adxl_manifest:
        raise FusionInputError("radar and ADXL355 references resolve to one manifest")
    return radar_manifest, adxl_manifest


def _load_value_calibration(
    root: pathlib.Path,
    combined: Mapping[str, Any],
) -> Optional[FusionValueCalibration]:
    files = _mapping(combined.get("files"), "combined manifest files")
    sync_files = _mapping(files.get("sync"), "combined sync files")
    relative = sync_files.get("fusion_calibration")
    if relative is None:
        return None
    calibration_path = _contained_file(
        root,
        relative,
        "fusion value calibration",
    )
    try:
        return load_fusion_calibration(calibration_path)
    except FusionCalibrationError as exc:
        raise FusionInputError(f"fusion value calibration is invalid: {exc}") from exc


def _validate_finalization_and_summary(
    combined: Mapping[str, Any],
    adxl: Adxl355Capture,
) -> None:
    validation = _mapping(
        combined.get("validation"), "combined manifest validation"
    )
    for field in (
        "radar_finalized",
        "adxl355_finalized",
        "sync_timeline_exported",
    ):
        if validation.get(field) is not True:
            raise FusionInputError(
                f"combined validation does not certify {field}"
            )
    validated_summary = _mapping(
        validation.get("adxl355"), "combined ADXL355 validation summary"
    )
    capture = _mapping(adxl.manifest.get("capture"), "ADXL355 capture metadata")
    native_summary = _mapping(
        capture.get("native_summary"), "ADXL355 native summary"
    )
    if validated_summary != native_summary:
        raise FusionInputError(
            "combined and ADXL355 manifests disagree on the native summary"
        )
    samples = capture.get("samples")
    if (
        isinstance(samples, bool)
        or not isinstance(samples, int)
        or samples != adxl.acceleration_mps2.shape[0]
        or native_summary.get("samples") != samples
    ):
        raise FusionInputError("ADXL355 sample counts disagree across the package")


def _validate_radar_cross_contract(
    radar: AlgorithmCapture,
    timeline: SynchronizedTimeline,
) -> None:
    frames = timeline.radar_frame_monotonic_ns.shape[0]
    if radar.adc_cube.shape[0] != frames:
        raise FusionInputError("radar cube and synchronized timeline frame counts differ")
    radar_metadata = _mapping(radar.manifest.get("radar"), "radar metadata")
    period = radar_metadata.get("frame_period_s")
    if (
        isinstance(period, bool)
        or not isinstance(period, (int, float))
        or not np.isfinite(period)
        or period <= 0.0
    ):
        raise FusionInputError("radar frame period is invalid")
    period_ns = int(round(float(period) * 1_000_000_000.0))
    if period_ns != timeline.manifest.get("nominal_frame_period_ns"):
        raise FusionInputError("radar and synchronized manifests disagree on frame period")
    expected_nominal = np.arange(frames, dtype=np.float64) * float(period)
    if not np.allclose(
        radar.frame_times_s,
        expected_nominal,
        rtol=0.0,
        atol=1e-12,
    ):
        raise FusionInputError("radar nominal frame schedule is inconsistent")


def _validate_adxl_timeline(
    adxl: Adxl355Capture,
) -> Tuple[int, bool, Optional[str], bool]:
    capture = _mapping(adxl.manifest.get("capture"), "ADXL355 capture metadata")
    timing = _mapping(adxl.manifest.get("timing"), "ADXL355 timing metadata")
    if timing.get("clock") != MONOTONIC_CLOCK:
        raise FusionInputError("ADXL355 data is not on CLOCK_MONOTONIC")
    if timing.get("drdy_monotonic_ns_semantics") != (
        "kernel DRDY rising-edge timestamp"
    ):
        raise FusionInputError("ADXL355 DRDY timestamp semantics are unsupported")
    drdy = adxl.drdy_monotonic_ns
    estimated = adxl.estimated_sample_monotonic_ns
    if drdy.dtype != np.dtype(np.uint64) or estimated.dtype != np.dtype(np.int64):
        raise FusionInputError("ADXL355 native timeline dtype is invalid")
    if np.any(drdy > np.iinfo(np.int64).max):
        raise FusionInputError("ADXL355 DRDY timestamp exceeds int64 range")
    group_delay = _optional_nonnegative_integer(
        capture.get("group_delay_ns"), "ADXL355 group_delay_ns"
    )
    if group_delay is None:
        raise FusionInputError("ADXL355 capture has no group delay value")
    expected = drdy.astype(np.int64) - np.int64(group_delay)
    if not np.array_equal(estimated, expected):
        raise FusionInputError(
            "ADXL355 estimated sample timeline disagrees with its group delay"
        )
    if np.any(estimated <= 0) or (
        estimated.size > 1 and np.any(np.diff(estimated) <= 0)
    ):
        raise FusionInputError("ADXL355 sample timeline is not positive/increasing")
    calibrated = _boolean(
        capture.get("group_delay_calibrated"),
        "ADXL355 group_delay_calibrated",
    )
    native_summary = _mapping(
        capture.get("native_summary"), "ADXL355 native summary"
    )
    source_value = native_summary.get("group_delay_source")
    if source_value is not None and (
        not isinstance(source_value, str) or not source_value.strip()
    ):
        raise FusionInputError(
            "ADXL355 group_delay_source must be nonempty or null"
        )
    group_delay_source = (
        source_value.strip() if isinstance(source_value, str) else None
    )
    if calibrated and group_delay_source is None:
        raise FusionInputError(
            "calibrated ADXL355 group delay requires a source"
        )
    if not calibrated and group_delay_source is not None:
        raise FusionInputError(
            "uncalibrated ADXL355 group delay must not claim a source"
        )
    conversion = _mapping(
        adxl.manifest.get("conversion"), "ADXL355 conversion metadata"
    )
    conversion_calibrated = _boolean(
        conversion.get("calibration_applied"),
        "ADXL355 conversion calibration_applied",
    )
    if not np.all(np.isfinite(adxl.acceleration_mps2)):
        raise FusionInputError("ADXL355 acceleration contains non-finite values")
    return group_delay, calibrated, group_delay_source, conversion_calibrated


def _calibration(
    combined: Mapping[str, Any],
    adxl_group_delay_ns: int,
    adxl_group_delay_calibrated: bool,
    adxl_group_delay_source: Optional[str],
    conversion_calibrated: bool,
) -> FusionCalibration:
    uncertainty = _mapping(
        combined.get("uncertainty"), "combined manifest uncertainty"
    )
    edge_uncertainty = _optional_nonnegative_integer(
        uncertainty.get("trigger_edge_uncertainty_ns"),
        "trigger_edge_uncertainty_ns",
    )
    latency = _optional_nonnegative_integer(
        uncertainty.get("radar_trigger_latency_ns"),
        "radar_trigger_latency_ns",
    )
    latency_uncertainty = _optional_nonnegative_integer(
        uncertainty.get("radar_trigger_latency_uncertainty_ns"),
        "radar_trigger_latency_uncertainty_ns",
    )
    calibrated_value = uncertainty.get("radar_trigger_latency_calibrated", False)
    latency_calibrated = _boolean(
        calibrated_value, "radar_trigger_latency_calibrated"
    )
    source_value = uncertainty.get("radar_trigger_latency_source")
    if source_value is not None and (
        not isinstance(source_value, str) or not source_value.strip()
    ):
        raise FusionInputError("radar_trigger_latency_source must be nonempty or null")
    latency_source = source_value.strip() if isinstance(source_value, str) else None
    if latency_calibrated and (
        latency is None or latency_uncertainty is None or latency_source is None
    ):
        raise FusionInputError(
            "calibrated radar latency requires value, uncertainty, and source"
        )

    declared_adxl_delay = _optional_nonnegative_integer(
        uncertainty.get("adxl_filter_group_delay_ns"),
        "adxl_filter_group_delay_ns",
    )
    if (
        declared_adxl_delay is not None
        and declared_adxl_delay != adxl_group_delay_ns
    ):
        raise FusionInputError(
            "combined and ADXL355 manifests disagree on filter group delay"
        )
    declared_adxl_calibrated = uncertainty.get(
        "adxl_filter_group_delay_calibrated"
    )
    if declared_adxl_calibrated is not None:
        if _boolean(
            declared_adxl_calibrated,
            "adxl_filter_group_delay_calibrated",
        ) != adxl_group_delay_calibrated:
            raise FusionInputError(
                "combined and ADXL355 manifests disagree on group-delay calibration"
            )
    adxl_uncertainty = _optional_nonnegative_integer(
        uncertainty.get("adxl_filter_group_delay_uncertainty_ns"),
        "adxl_filter_group_delay_uncertainty_ns",
    )
    declared_adxl_source = uncertainty.get("adxl_filter_group_delay_source")
    if declared_adxl_source is not None and (
        not isinstance(declared_adxl_source, str)
        or not declared_adxl_source.strip()
    ):
        raise FusionInputError(
            "adxl_filter_group_delay_source must be nonempty or null"
        )
    normalized_adxl_source = (
        declared_adxl_source.strip()
        if isinstance(declared_adxl_source, str)
        else None
    )
    if normalized_adxl_source != adxl_group_delay_source:
        raise FusionInputError(
            "combined and ADXL355 manifests disagree on group-delay source"
        )
    return FusionCalibration(
        radar_reference_edge_uncertainty_ns=edge_uncertainty,
        radar_reference_to_adc_latency_ns=latency,
        radar_reference_to_adc_latency_uncertainty_ns=latency_uncertainty,
        radar_latency_calibrated=latency_calibrated,
        radar_latency_source=latency_source,
        adxl_filter_group_delay_ns=adxl_group_delay_ns,
        adxl_filter_group_delay_uncertainty_ns=adxl_uncertainty,
        adxl_group_delay_calibrated=adxl_group_delay_calibrated,
        adxl_group_delay_source=adxl_group_delay_source,
        adxl_conversion_calibration_applied=conversion_calibrated,
    )


def _radar_adc_timeline(
    reference: np.ndarray,
    calibration: FusionCalibration,
) -> Optional[np.ndarray]:
    if not calibration.radar_latency_calibrated:
        return None
    latency = calibration.radar_reference_to_adc_latency_ns
    if latency is None:  # guarded while parsing, retained for type narrowing
        raise FusionInputError("calibrated radar latency has no value")
    if np.any(reference > np.iinfo(np.int64).max - latency):
        raise FusionInputError("calibrated radar ADC timeline overflows int64")
    return reference + np.int64(latency)


def _timeline_coverage(
    radar_times: np.ndarray,
    adxl_times: np.ndarray,
) -> Tuple[bool, bool]:
    radar_first = int(radar_times[0])
    radar_last = int(radar_times[-1])
    adxl_first = int(adxl_times[0])
    adxl_last = int(adxl_times[-1])
    overlap = max(radar_first, adxl_first) <= min(radar_last, adxl_last)
    fully_covered = adxl_first <= radar_first and radar_last <= adxl_last
    return overlap, fully_covered


def _provenance(timeline: SynchronizedTimeline) -> FusionProvenance:
    manifest_provenance = _mapping(
        timeline.manifest.get("provenance"), "timeline provenance"
    )
    combined_semantics = _mapping(
        timeline.combined_manifest.get("timestamp_semantics"),
        "combined timestamp semantics",
    )
    source = manifest_provenance.get("source")
    semantics = manifest_provenance.get("semantics")
    if not isinstance(source, str) or not isinstance(semantics, str):
        raise FusionInputError("radar timeline provenance is incomplete")
    measured = _boolean(
        manifest_provenance.get("is_measured_radar_frame_start"),
        "radar is_measured_frame_start",
    )
    pcap_is_frame_start = _boolean(
        combined_semantics.get("pcap_is_frame_start"),
        "pcap_is_frame_start",
    )
    adxl_semantics = combined_semantics.get("adxl355")
    if not isinstance(adxl_semantics, str) or not adxl_semantics.strip():
        raise FusionInputError("combined manifest has no ADXL355 time semantics")
    if measured or pcap_is_frame_start:
        raise FusionInputError("source manifests overstate radar timestamp semantics")
    return FusionProvenance(
        clock=MONOTONIC_CLOCK,
        sync_mode=str(timeline.manifest["sync_mode"]),
        radar_timestamp_quality=str(timeline.manifest["timestamp_quality"]),
        radar_reference_source=source,
        radar_reference_semantics=semantics,
        radar_reference_is_measured_frame_start=measured,
        adxl_drdy_semantics=adxl_semantics,
        pcap_is_frame_start=pcap_is_frame_start,
    )


def _quality(
    radar: AlgorithmCapture,
    adxl: Adxl355Capture,
    timeline: SynchronizedTimeline,
    calibration: FusionCalibration,
    value_calibration: Optional[FusionValueCalibration],
    overlap: bool,
    fully_covered: bool,
) -> FusionQuality:
    combined = timeline.combined_manifest
    hardware_validated = _boolean(
        combined.get("hardware_validated"), "hardware_validated"
    )
    algorithm_failures = []
    uncertainty = _mapping(
        combined.get("uncertainty"), "combined manifest uncertainty"
    )
    if combined.get("sync_mode") != "hardware_trigger":
        algorithm_failures.append("sync_mode_is_not_hardware_trigger")
    if combined.get("timestamp_quality") not in (
        "kernel_loopback_edge",
        "userspace_set_completed",
    ):
        algorithm_failures.append("radar_reference_is_not_hardware_trigger_timed")
    native_summary = _mapping(
        _mapping(adxl.manifest.get("capture"), "ADXL355 capture metadata").get(
            "native_summary"
        ),
        "ADXL355 native summary",
    )
    if _boolean(native_summary.get("mock"), "ADXL355 mock provenance"):
        algorithm_failures.append("adxl_source_is_mock")
    if radar.chirp_cube is None:
        algorithm_failures.append("lossless_radar_chirp_cube_missing")
    if not overlap:
        algorithm_failures.append("native_sensor_timelines_do_not_overlap")
    if not fully_covered:
        algorithm_failures.append("adxl_timeline_does_not_cover_all_radar_frames")

    algorithm_failures_tuple = tuple(algorithm_failures)
    failures = list(algorithm_failures)
    if not hardware_validated:
        failures.append("hardware_sync_not_validated")
    if uncertainty.get("status") != "characterized":
        failures.append("timing_uncertainty_not_characterized")
    if calibration.radar_reference_edge_uncertainty_ns is None:
        failures.append("radar_reference_edge_uncertainty_missing")
    if not calibration.radar_latency_calibrated:
        failures.append("radar_reference_to_adc_latency_not_calibrated")
    if not calibration.adxl_group_delay_calibrated:
        failures.append("adxl_filter_group_delay_not_calibrated")
    if calibration.adxl_filter_group_delay_uncertainty_ns is None:
        failures.append("adxl_filter_group_delay_uncertainty_missing")
    if value_calibration is None:
        failures.append("fusion_value_calibration_missing")
    elif not value_calibration.validated:
        failures.append("fusion_value_calibration_not_validated")
    failures_tuple = tuple(failures)
    return FusionQuality(
        fusion_ready=not failures_tuple,
        readiness_failures=failures_tuple,
        radar_packet_integrity_complete=True,
        adxl_capture_complete=True,
        timeline_complete=True,
        hardware_validated=hardware_validated,
        native_timeline_overlap=overlap,
        radar_timeline_fully_covered_by_adxl=fully_covered,
        algorithm_ready=not algorithm_failures_tuple,
        algorithm_readiness_failures=algorithm_failures_tuple,
    )


def _simulation_manifest(path: Union[str, pathlib.Path]) -> Optional[pathlib.Path]:
    candidate = pathlib.Path(path)
    if candidate.is_file():
        if candidate.name != "manifest.json":
            return None
        manifest_path = candidate
    else:
        manifest_path = candidate / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if payload.get("schema") != SIMULATION_SCHEMA_NAME:
        return None
    return manifest_path


def _load_simulation_array(
    root: pathlib.Path,
    description: Any,
    *,
    label: str,
    dtype: np.dtype,
    shape: tuple[int, ...],
    mmap_mode: Optional[str],
) -> np.ndarray:
    item = _mapping(description, label)
    filename = item.get("file")
    if not isinstance(filename, str) or not filename:
        raise FusionInputError(f"{label} has no valid file")
    path = (root / filename).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise FusionInputError(f"{label} escapes the simulation package") from exc
    if not path.is_file():
        raise FusionInputError(f"{label} is missing: {path}")
    try:
        result = np.load(path, mmap_mode=mmap_mode, allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise FusionInputError(f"cannot load {label}: {exc}") from exc
    if result.dtype != dtype or result.shape != shape:
        raise FusionInputError(
            f"{label} must have dtype {dtype.name} and shape {shape}"
        )
    return result


def _load_simulation_fusion_input(
    manifest_path: pathlib.Path,
    *,
    mmap_mode: Optional[str],
) -> FusionCapture:
    """Load the narrow, explicitly synthetic magnetic-levitation contract."""

    root = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FusionInputError(f"cannot read simulation manifest: {exc}") from exc
    if (
        manifest.get("schema_version") != SIMULATION_SCHEMA_VERSION
        or manifest.get("status") != "complete"
    ):
        raise FusionInputError("simulation manifest is not complete schema v1")
    if manifest.get("scenario") != MAGLEV_SIMULATION_SCENARIO:
        raise FusionInputError("unsupported simulation scenario")
    if (
        manifest.get("sync_mode") != "simulation"
        or manifest.get("timestamp_quality")
        != "synthetic_coherent_aperture_center"
        or manifest.get("hardware_validated") is not False
        or manifest.get("algorithm_ready") is not False
        or manifest.get("fusion_ready") is not False
        or manifest.get("simulation_ready") is not True
    ):
        raise FusionInputError("simulation readiness/provenance flags are invalid")

    provenance_table = _mapping(
        manifest.get("source_provenance"), "simulation source_provenance"
    )
    algorithm_contract = _mapping(
        manifest.get("algorithm_contract"), "simulation algorithm_contract"
    )
    if algorithm_contract != {
        "cold_start_duration_s": MAGLEV_SIMULATION_COLD_START_DURATION_S,
        "displacement_reference": "cold_start_mean",
        "truth_evaluation": "cold_start_relative_displacement",
    }:
        raise FusionInputError("simulation algorithm contract changed")
    expected_sources = {
        "laser_displacement": "measured",
        "radar_adc_iq": "synthetic",
        "radar_configuration": "configured",
        "adxl_structural_axis": "derived",
        "adxl_other_axes": "synthetic",
        "radar_timestamps": "synthetic",
        "adxl_drdy_timestamps": "synthetic",
    }
    for name, expected in expected_sources.items():
        item = _mapping(provenance_table.get(name), f"source_provenance.{name}")
        if item.get("classification") != expected:
            raise FusionInputError(
                f"source_provenance.{name} must be classified as {expected}"
            )
    structural_axis_source = _mapping(
        provenance_table.get("adxl_structural_axis"),
        "source_provenance.adxl_structural_axis",
    )
    simulation_seed = manifest.get("seed")
    adxl_error_model = _mapping(
        structural_axis_source.get("hardware_error_model"),
        "simulation ADXL hardware_error_model",
    )
    adxl_noise = _mapping(
        adxl_error_model.get("noise"),
        "simulation ADXL noise model",
    )
    adxl_quantization = _mapping(
        adxl_error_model.get("quantization"),
        "simulation ADXL quantization model",
    )
    adxl_not_injected = _mapping(
        adxl_error_model.get("not_injected"),
        "simulation ADXL non-injected errors",
    )
    adxl_specs = _mapping(
        adxl_error_model.get("datasheet_specifications"),
        "simulation ADXL datasheet specifications",
    )
    expected_adxl_rms = 22.5e-6 * 9.80665 * np.sqrt(250.0)
    if (
        isinstance(simulation_seed, bool)
        or not isinstance(simulation_seed, int)
        or structural_axis_source.get("noise_classification") != "synthetic"
        or structural_axis_source.get("physical_acceleration_noise_std_mps2")
        != 0.0
        or structural_axis_source.get("physical_acceleration_bias_mps2") != 0.0
        or structural_axis_source.get("physical_acceleration_drift_mps2") != 0.0
        or adxl_error_model.get("schema_version") != 1
        or adxl_error_model.get("profile")
        != "datasheet_typical_calibrated_25c"
        or adxl_error_model.get("seed") != simulation_seed + 503
        or adxl_error_model.get("manufacturer") != "Analog Devices"
        or adxl_error_model.get("device") != "ADXL355"
        or adxl_error_model.get("datasheet_revision") != "Rev. D"
        or adxl_error_model.get("range_g") != 2
        or adxl_error_model.get("adc_bits") != 20
        or adxl_error_model.get("sensitivity_lsb_per_g") != 256_000.0
        or adxl_error_model.get("odr_hz") != 1000.0
        or adxl_noise.get("enabled") is not True
        or adxl_noise.get("density_ug_per_sqrt_hz") != 22.5
        or adxl_noise.get("equivalent_bandwidth_hz") != 250.0
        or "not an exact ENBW"
        not in str(adxl_noise.get("bandwidth_approximation", ""))
        or not np.isclose(
            adxl_noise.get("target_rms_mps2", np.nan),
            expected_adxl_rms,
            rtol=0.0,
            atol=1.0e-15,
        )
        or adxl_quantization.get("enabled") is not True
        or adxl_quantization.get("signed_code_min") != -(2**19)
        or adxl_quantization.get("signed_code_max") != 2**19 - 1
        or set(adxl_not_injected) != {
            "initial_zero_bias",
            "sensitivity_tolerance",
            "cross_axis_sensitivity",
            "nonlinearity",
            "temperature_drift",
            "digital_filter_group_delay",
        }
        or adxl_specs.get("zero_g_offset_mg")
        != {"typical_absolute": 25.0, "minimum_maximum_absolute": 75.0}
        or adxl_specs.get("sensitivity_lsb_per_g_at_2g")
        != {"minimum": 235_520.0, "typical": 256_000.0, "maximum": 276_480.0}
        or adxl_specs.get("nonlinearity_percent_full_scale") != 0.1
        or adxl_specs.get("cross_axis_sensitivity_percent") != 1.0
        or adxl_specs.get("sensitivity_temperature_percent_per_deg_c") != 0.01
        or adxl_specs.get("offset_temperature_max_mg_per_deg_c") != 0.15
        or adxl_specs.get("digital_filter_group_delay_ms_at_1khz_odr") != 1.78
    ):
        raise FusionInputError("simulation ADXL structural-axis provenance is invalid")
    radar_source = _mapping(
        provenance_table.get("radar_adc_iq"),
        "source_provenance.radar_adc_iq",
    )
    radar_error_model = _mapping(
        radar_source.get("hardware_error_model"),
        "simulation radar hardware_error_model",
    )
    receiver_noise = _mapping(
        radar_error_model.get("receiver_noise"),
        "simulation radar receiver_noise",
    )
    radar_quantization = _mapping(
        radar_error_model.get("quantization"),
        "simulation radar quantization",
    )
    channel_mismatch = _mapping(
        radar_error_model.get("channel_mismatch"),
        "simulation radar channel_mismatch",
    )
    dca_model = _mapping(
        radar_error_model.get("dca1000"),
        "simulation DCA1000 model",
    )
    if (
        radar_source.get("noise_injection_layers") != 1
        or radar_error_model.get("schema_version") != 1
        or radar_error_model.get("profile")
        != "datasheet_typical_calibrated_25c"
        or radar_error_model.get("seed") != simulation_seed + 701
        or radar_error_model.get("manufacturer") != "Texas Instruments"
        or radar_error_model.get("device") != "IWR1843"
        or radar_error_model.get("datasheet_revision") != "Rev. B (SWRS228B)"
        or receiver_noise.get("enabled") is not True
        or receiver_noise.get("injection_layers") != 1
        or receiver_noise.get("noise_figure_db_at_77_to_81_ghz") != 15.0
        or receiver_noise.get("target_snr_semantics")
        != "scenario link-budget assumption; not a manufacturer error specification"
        or "link-budget assumptions"
        not in str(receiver_noise.get("noise_power_semantics", ""))
        or "cannot determine ADC SNR"
        not in str(receiver_noise.get("noise_figure_limitation", ""))
        or radar_quantization.get("enabled") is not True
        or radar_quantization.get("i_bits") != 12
        or radar_quantization.get("q_bits") != 12
        or radar_quantization.get("signed_code_min") != -(2**11)
        or radar_quantization.get("signed_code_max") != 2**11 - 1
        or radar_quantization.get("stored_values")
        != "signed_integer_codes_in_complex64"
        or channel_mismatch.get("enabled") is not False
        or channel_mismatch.get("gain_bound_db") != 0.5
        or channel_mismatch.get("phase_bound_deg") != 3.0
        or dca_model.get("noise_injected") is not False
        or dca_model.get("packet_integrity") != "complete_or_fail_closed"
    ):
        raise FusionInputError("simulation radar hardware-error provenance is invalid")
    laser_source = _mapping(
        provenance_table.get("laser_displacement"),
        "source_provenance.laser_displacement",
    )
    event_window = laser_source.get("event_window_s")
    tdms_sha256 = laser_source.get("sha256")
    if (
        laser_source.get("file") != "datafile/20250320test12.tdms"
        or laser_source.get("channel") != "卡3激光位移/3-4"
        or laser_source.get("pre_downsample_filter_hz") != [0.2, 40.0]
        or laser_source.get("scale_calibrated") is not False
        or laser_source.get("measured_quantity") != "raw_voltage_waveform"
        or laser_source.get("displacement_status")
        != "derived_with_unvalidated_voltage_to_displacement_scale"
        or not isinstance(tdms_sha256, str)
        or len(tdms_sha256) != 64
        or any(character not in "0123456789abcdef" for character in tdms_sha256)
        or not isinstance(event_window, list)
        or len(event_window) != 2
        or event_window[0] != 15.33
        or not isinstance(event_window[1], (int, float))
        or event_window[1] <= event_window[0]
        or event_window[1] > 19.33
    ):
        raise FusionInputError("fixed measured laser source/window/filter is invalid")
    radar_source = _mapping(
        provenance_table.get("radar_configuration"),
        "source_provenance.radar_configuration",
    )
    radar_sha256 = radar_source.get("sha256")
    expected_radar_source = {
        "tx_indices": [0, 2],
        "rx_indices": [0, 1, 2, 3],
        "chirp_loops_per_frame": 16,
        "minimum_frame_period_s": 9.0e-3,
        "trigger_select": 2,
        "start_frequency_hz": 77.0e9,
        "idle_time_s": 70.0e-6,
        "ramp_end_time_s": 57.14e-6,
        "frequency_slope_hz_per_s": 70.0e12,
        "adc_samples_per_chirp": 256,
        "adc_sample_rate_hz": 5.209e6,
    }
    if (
        radar_source.get("file")
        != "capture_program/examples/configs/iwr1843_hardware_trigger.cfg"
        or not isinstance(radar_sha256, str)
        or len(radar_sha256) != 64
        or any(character not in "0123456789abcdef" for character in radar_sha256)
        or any(
            radar_source.get(name) != value
            for name, value in expected_radar_source.items()
        )
    ):
        raise FusionInputError("fixed radar configuration provenance is invalid")
    radar_timestamp_source = _mapping(
        provenance_table.get("radar_timestamps"),
        "source_provenance.radar_timestamps",
    )
    if (
        radar_timestamp_source.get("quality")
        != "synthetic_coherent_aperture_center"
        or radar_timestamp_source.get("reference_quality")
        != "synthetic_monotonic_schedule"
        or radar_timestamp_source.get("effective_observation")
        != "coherent_aperture_center"
        or radar_timestamp_source.get("coherent_aperture_center_offset_ns")
        != MAGLEV_SIMULATION_COHERENT_CENTER_OFFSET_NS
        or radar_timestamp_source.get("measured_gpio") is not False
        or radar_timestamp_source.get("measured_adc_time") is not False
    ):
        raise FusionInputError("simulation radar timestamp provenance is invalid")
    rates = _mapping(manifest.get("rates_hz"), "simulation rates_hz")
    if (
        rates.get("radar") != 100
        or rates.get("adxl355") != 1000
        or manifest.get("packet_integrity") != "synthetic_payload_integrity"
    ):
        raise FusionInputError("simulation rate or payload-integrity contract changed")

    files = _mapping(manifest.get("files"), "simulation files")
    radar_manifest = _contained_manifest(
        root, files.get("radar_algorithm_input_manifest"), "radar manifest"
    )
    adxl_manifest = _contained_manifest(
        root, files.get("adxl355_algorithm_input_manifest"), "ADXL355 manifest"
    )
    try:
        radar = load_algorithm_input(radar_manifest, mmap_mode=mmap_mode)
        adxl = load_adxl355_input(adxl_manifest, mmap_mode=mmap_mode)
    except (AlgorithmInputError, Adxl355InputError, OSError, ValueError) as exc:
        raise FusionInputError(f"simulation source package validation failed: {exc}") from exc

    radar_metadata = _mapping(radar.manifest.get("radar"), "radar metadata")
    required_radar = {
        "frame_period_s": 9.0e-3,
        "frame_rate_hz": 1.0 / 9.0e-3,
        "chirp_loops_per_frame": 16,
        "physical_chirps_per_frame": 32,
        "tx_indices": [0, 2],
        "rx_indices": [0, 1, 2, 3],
        "virtual_antennas": 8,
        "adc_samples_per_chirp": 256,
        "adc_sample_rate_hz": 5.209e6,
        "ramp_end_time_s": 57.14e-6,
        "idle_time_s": 70.0e-6,
        "minimum_frame_period_s": 9.0e-3,
        "external_trigger_period_s": 10.0e-3,
        "quadrature_in_lsb": True,
    }
    if any(radar_metadata.get(name) != value for name, value in required_radar.items()):
        raise FusionInputError("simulation radar configuration is not the fixed 100 Hz contract")
    expected_nominal_frame_times = (
        np.arange(radar.adc_cube.shape[0], dtype=np.float64) * 9.0e-3
    )
    if not np.allclose(
        radar.frame_times_s,
        expected_nominal_frame_times,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise FusionInputError("simulation nominal radar schedule is invalid")
    processing = _mapping(radar.manifest.get("processing"), "radar processing")
    loop_start_interval_s = processing.get("loop_start_interval_s")
    coherent_center_offset_s = processing.get(
        "coherent_aperture_center_offset_s"
    )
    if (
        processing.get("tdm_motion_compensation") is not False
        or processing.get("chirp_cube_construction")
        != (
            "16 independently noised synthetic loop observations sampled "
            "at their within-frame loop-start times"
        )
        or isinstance(loop_start_interval_s, bool)
        or not isinstance(loop_start_interval_s, (int, float))
        or not np.isclose(
            loop_start_interval_s,
            254.28e-6,
            rtol=0.0,
            atol=1.0e-12,
        )
        or isinstance(coherent_center_offset_s, bool)
        or not isinstance(coherent_center_offset_s, (int, float))
        or not np.isclose(
            coherent_center_offset_s,
            MAGLEV_SIMULATION_COHERENT_CENTER_OFFSET_NS * 1.0e-9,
            rtol=0.0,
            atol=1.0e-12,
        )
    ):
        raise FusionInputError("simulation chirp-loop provenance is invalid")
    if radar.chirp_cube is None:
        raise FusionInputError("simulation radar chirp cube is missing")
    chirp_i = radar.chirp_cube.real
    chirp_q = radar.chirp_cube.imag
    if (
        np.any(chirp_i < -(2**11))
        or np.any(chirp_i > 2**11 - 1)
        or np.any(chirp_q < -(2**11))
        or np.any(chirp_q > 2**11 - 1)
        or not np.array_equal(chirp_i, np.rint(chirp_i))
        or not np.array_equal(chirp_q, np.rint(chirp_q))
    ):
        raise FusionInputError(
            "simulation chirp cube is not signed 12-bit I/Q code data"
        )
    coherent_mean = np.mean(
        radar.chirp_cube,
        axis=1,
    ).astype(np.complex64, copy=False)
    if not np.array_equal(coherent_mean, radar.adc_cube):
        raise FusionInputError(
            "simulation adc_cube is not the coherent mean of chirp_cube"
        )
    frames = int(radar_metadata.get("frames", 0))
    samples = int(adxl.manifest.get("capture", {}).get("samples", 0))
    if adxl.manifest.get("capture", {}).get("odr_hz_nominal") != 1000.0:
        raise FusionInputError("simulation ADXL rate is not 1 kHz")
    adxl_timing = _mapping(adxl.manifest.get("timing"), "ADXL timing")
    if (
        adxl_timing.get("clock") != "synthetic_monotonic_schedule"
        or adxl_timing.get("drdy_monotonic_ns_semantics")
        != "synthetic nominal DRDY schedule"
    ):
        raise FusionInputError("simulation ADXL timing provenance is invalid")
    arrays = _mapping(manifest.get("arrays"), "simulation arrays")
    radar_time = _load_simulation_array(
        root,
        arrays.get("radar_reference_monotonic_ns"),
        label="radar_reference_monotonic_ns",
        dtype=np.dtype(np.int64),
        shape=(frames,),
        mmap_mode=mmap_mode,
    )
    radar_adc_time = _load_simulation_array(
        root,
        arrays.get("radar_adc_sample_monotonic_ns"),
        label="radar_adc_sample_monotonic_ns",
        dtype=np.dtype(np.int64),
        shape=(frames,),
        mmap_mode=mmap_mode,
    )
    truth_time = _load_simulation_array(
        root,
        arrays.get("truth_time_ns"),
        label="truth_time_ns",
        dtype=np.dtype(np.int64),
        shape=(frames,),
        mmap_mode=mmap_mode,
    )
    truth_q = _load_simulation_array(
        root,
        arrays.get("truth_displacement_m"),
        label="truth_displacement_m",
        dtype=np.dtype(np.float64),
        shape=(frames,),
        mmap_mode=mmap_mode,
    )
    truth_adxl_time = _load_simulation_array(
        root,
        arrays.get("truth_adxl_time_ns"),
        label="truth_adxl_time_ns",
        dtype=np.dtype(np.int64),
        shape=(samples,),
        mmap_mode=mmap_mode,
    )
    truth_acceleration = _load_simulation_array(
        root,
        arrays.get("truth_acceleration_mps2"),
        label="truth_acceleration_mps2",
        dtype=np.dtype(np.float64),
        shape=(samples,),
        mmap_mode=mmap_mode,
    )
    if (
        frames < 2
        or samples < 2
        or np.any(radar_time <= 0)
        or np.any(np.diff(radar_time) <= 0)
        or not np.array_equal(
            radar_adc_time,
            radar_time + MAGLEV_SIMULATION_COHERENT_CENTER_OFFSET_NS,
        )
        or not np.array_equal(truth_time, radar_adc_time)
        or np.any(~np.isfinite(truth_q))
        or np.any(~np.isfinite(truth_acceleration))
        or np.any(np.diff(radar_time) != 10_000_000)
    ):
        raise FusionInputError("simulation timelines or truth arrays are invalid")
    if not np.array_equal(adxl.drdy_monotonic_ns, adxl.estimated_sample_monotonic_ns):
        raise FusionInputError("synthetic ADXL schedule must declare zero group delay")
    adxl_time = np.asarray(adxl.estimated_sample_monotonic_ns, dtype=np.int64)
    if (
        np.any(np.diff(adxl_time) != 1_000_000)
        or not np.array_equal(truth_adxl_time, adxl_time)
    ):
        raise FusionInputError("synthetic ADXL schedule is not exactly 1 kHz")
    overlap, fully_covered = _timeline_coverage(radar_adc_time, adxl_time)
    if not overlap or not fully_covered:
        raise FusionInputError("synthetic ADXL schedule does not cover radar frames")

    calibration = FusionCalibration(
        radar_reference_edge_uncertainty_ns=None,
        radar_reference_to_adc_latency_ns=(
            MAGLEV_SIMULATION_COHERENT_CENTER_OFFSET_NS
        ),
        radar_reference_to_adc_latency_uncertainty_ns=None,
        radar_latency_calibrated=False,
        radar_latency_source="synthetic coherent-aperture center model",
        adxl_filter_group_delay_ns=0,
        adxl_filter_group_delay_uncertainty_ns=None,
        adxl_group_delay_calibrated=False,
        adxl_group_delay_source=None,
        adxl_conversion_calibration_applied=False,
    )
    timeline = SynchronizedTimeline(
        radar_frame_monotonic_ns=radar_time,
        manifest=manifest,
        combined_manifest=manifest,
        directory=root,
    )
    quality = FusionQuality(
        fusion_ready=False,
        readiness_failures=(
            "simulation_source",
            "hardware_sync_not_validated",
            "timing_calibration_not_measured",
        ),
        radar_packet_integrity_complete=False,
        adxl_capture_complete=True,
        timeline_complete=True,
        hardware_validated=False,
        native_timeline_overlap=True,
        radar_timeline_fully_covered_by_adxl=True,
        algorithm_ready=False,
        algorithm_readiness_failures=("simulation_requires_explicit_opt_in",),
        simulation_ready=True,
    )
    provenance = FusionProvenance(
        clock="synthetic_monotonic_schedule",
        sync_mode="simulation",
        radar_timestamp_quality="synthetic_coherent_aperture_center",
        radar_reference_source="synthetic_external_trigger_schedule",
        radar_reference_semantics="synthetic nominal external-trigger schedule",
        radar_reference_is_measured_frame_start=False,
        adxl_drdy_semantics="synthetic nominal ADXL sample/DRDY schedule",
        pcap_is_frame_start=False,
    )
    return FusionCapture(
        radar=radar,
        adxl355=adxl,
        timeline=timeline,
        radar_reference_monotonic_ns=radar_time,
        adxl_drdy_monotonic_ns=adxl.drdy_monotonic_ns,
        adxl_sample_monotonic_ns=adxl_time,
        radar_adc_sample_monotonic_ns=radar_adc_time,
        acceleration_structure_mps2=None,
        calibration=calibration,
        value_calibration=None,
        quality=quality,
        provenance=provenance,
        directory=root,
        simulation_truth_time_ns=truth_time,
        simulation_truth_displacement_m=truth_q,
        simulation_truth_adxl_time_ns=truth_adxl_time,
        simulation_truth_acceleration_mps2=truth_acceleration,
    )


def load_fusion_input(
    path: Union[str, pathlib.Path],
    *,
    mmap_mode: Optional[str] = "r",
    allow_simulation: bool = False,
) -> FusionCapture:
    """Load one complete synchronized capture without resampling either sensor.

    Structural, integrity, clock, path-containment, and cross-manifest failures
    raise :class:`FusionInputError`. A structurally valid package can be
    ``algorithm_ready`` under hardware SYNC control while ``fusion_ready``
    remains false until timing/value calibration is supplied. The respective
    blockers are exposed through both readiness-failure tuples.
    """

    if not isinstance(allow_simulation, (bool, np.bool_)):
        raise ValueError("allow_simulation must be boolean")

    simulation_manifest = _simulation_manifest(path)
    if simulation_manifest is not None:
        if not allow_simulation:
            raise FusionInputError(
                "simulation package rejected; pass allow_simulation=True explicitly"
            )
        return _load_simulation_fusion_input(
            simulation_manifest,
            mmap_mode=mmap_mode,
        )

    try:
        timeline = load_synchronized_timeline(path, mmap_mode=mmap_mode)
        root = timeline.directory.parent
        radar_manifest, adxl_manifest = _source_manifests(
            root, timeline.combined_manifest
        )
        radar = load_algorithm_input(radar_manifest, mmap_mode=mmap_mode)
        adxl = load_adxl355_input(adxl_manifest, mmap_mode=mmap_mode)
    except (AlgorithmInputError, Adxl355InputError, SynchronizedInputError) as exc:
        raise FusionInputError(f"source package validation failed: {exc}") from exc
    except (OSError, ValueError) as exc:
        raise FusionInputError(f"cannot load synchronized source package: {exc}") from exc

    _validate_finalization_and_summary(timeline.combined_manifest, adxl)
    _validate_radar_cross_contract(radar, timeline)
    group_delay, group_calibrated, group_delay_source, conversion_calibrated = (
        _validate_adxl_timeline(adxl)
    )
    calibration = _calibration(
        timeline.combined_manifest,
        group_delay,
        group_calibrated,
        group_delay_source,
        conversion_calibrated,
    )
    value_calibration = _load_value_calibration(
        root,
        timeline.combined_manifest,
    )
    acceleration_structure_mps2 = None
    if value_calibration is not None:
        if (
            int(np.max(value_calibration.radar.azimuth_virtual_channel_indices))
            >= radar.adc_cube.shape[1]
        ):
            raise FusionInputError(
                "fusion calibration references an uncaptured radar channel"
            )
        acceleration_structure_mps2 = (
            value_calibration.adxl355.project_structural_axis(
                adxl.acceleration_mps2
            )
        )
    radar_adc_times = _radar_adc_timeline(
        timeline.radar_frame_monotonic_ns, calibration
    )
    coverage_times = (
        radar_adc_times
        if radar_adc_times is not None
        else timeline.radar_frame_monotonic_ns
    )
    overlap, fully_covered = _timeline_coverage(
        coverage_times, adxl.estimated_sample_monotonic_ns
    )
    provenance = _provenance(timeline)
    quality = _quality(
        radar,
        adxl,
        timeline,
        calibration,
        value_calibration,
        overlap,
        fully_covered,
    )
    return FusionCapture(
        radar=radar,
        adxl355=adxl,
        timeline=timeline,
        radar_reference_monotonic_ns=timeline.radar_frame_monotonic_ns,
        adxl_drdy_monotonic_ns=adxl.drdy_monotonic_ns,
        adxl_sample_monotonic_ns=adxl.estimated_sample_monotonic_ns,
        radar_adc_sample_monotonic_ns=radar_adc_times,
        acceleration_structure_mps2=acceleration_structure_mps2,
        calibration=calibration,
        value_calibration=value_calibration,
        quality=quality,
        provenance=provenance,
        directory=root,
    )
