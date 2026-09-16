"""Thin reader from the acquisition schema into the Phase-1 ADC frontend.

All hardware-specific adaptation lives in ``mmwavecapture.algorithm_input``.
This module only maps that stable schema into the existing frontend dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

import numpy as np

from .frontend import (
    ADCCubeObservation,
    FrontendConfig,
    extract_frontend_target_observation,
    range_angle_process,
    range_axis_m,
)
from .radar import RadarAlgorithmInput
from .selection import (
    detect_peaks_2d,
    merge_close_angle_peaks,
    select_targets_from_measurements,
)


@dataclass(frozen=True)
class CapturedFrontendInput:
    adc: ADCCubeObservation
    frontend_config: FrontendConfig
    manifest: Mapping[str, Any]
    source_directory: Path


@dataclass(frozen=True)
class CapturedAccelerationInput:
    """Native ADXL series plus radar-interval preintegration for Phase-1."""

    measured_mps2: np.ndarray
    native_time_ns: np.ndarray
    native_mps2: np.ndarray
    valid_mask: np.ndarray
    preintegration: Any


@dataclass(frozen=True)
class CapturedFusionInput:
    adc: ADCCubeObservation
    frontend_config: FrontendConfig
    acceleration: CapturedAccelerationInput
    radar_time_ns: np.ndarray
    fusion_capture: Any
    source_directory: Path
    timing_mode: str = "calibrated_adc_timeline"
    calibration_mode: str = "unknown_unvalidated"
    warnings: tuple[str, ...] = ()
    max_adxl_gap_ns: int = 0
    is_simulation: bool = False
    truth_time_ns: Optional[np.ndarray] = None
    truth_displacement_m: Optional[np.ndarray] = None


@dataclass(frozen=True)
class CapturedAlgorithmInput:
    radar: RadarAlgorithmInput
    acceleration: CapturedAccelerationInput
    range_angle: Any
    frontend_targets: Any
    selection: Any
    effective_radar_rate_hz: float
    source: CapturedFusionInput


def _nominal_adxl_axis(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("nominal_adxl_axis must be x, y, or z")
    normalized = value.strip().lower()
    if normalized not in ("x", "y", "z"):
        raise ValueError("nominal_adxl_axis must be x, y, or z")
    return normalized


def _nominal_adxl_sign(value: int) -> int:
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, (int, np.integer))
        or int(value) not in (-1, 1)
    ):
        raise ValueError("nominal_adxl_sign must be -1 or 1")
    return int(value)


def _resolve_max_adxl_gap_ns(
    adxl_time_ns: np.ndarray,
    configured: Optional[int],
) -> int:
    if configured is not None:
        if (
            isinstance(configured, (bool, np.bool_))
            or not isinstance(configured, (int, np.integer))
            or int(configured) <= 0
        ):
            raise ValueError("max_adxl_gap_ns must be a positive integer or null")
        return int(configured)

    intervals = np.diff(np.asarray(adxl_time_ns, dtype=np.int64))
    if intervals.size == 0 or np.any(intervals <= 0):
        raise RuntimeError(
            "cannot infer the ADXL gap limit from a non-increasing timeline"
        )
    nominal_interval_ns = int(np.median(intervals))
    if nominal_interval_ns <= 0:
        raise RuntimeError("cannot infer a positive ADXL sampling interval")
    # The native collector already rejects GPIO sequence gaps.  A 2.5-period
    # limit tolerates ordinary timestamp jitter without hiding a missing sample.
    return max(1, (5 * nominal_interval_ns + 1) // 2)


def load_captured_frontend_input(
    path: Union[str, Path],
    *,
    mmap_mode: Optional[str] = "r",
) -> CapturedFrontendInput:
    """Load capture-produced arrays without parsing PCAP, LVDS, or radar CFG."""

    try:
        from mmwavecapture.algorithm_input import load_algorithm_input
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "the capture reader requires the local capture_program package; "
            "install it with `pip install -e capture_program`"
        ) from exc

    capture = load_algorithm_input(path, mmap_mode=mmap_mode)
    radar = capture.manifest["radar"]
    frontend_config = FrontendConfig(
        num_tx=len(radar["tx_indices"]),
        num_rx=len(radar["rx_indices"]),
        num_virtual_rx=int(radar["virtual_antennas"]),
        num_adc_samples=int(radar["adc_samples_per_chirp"]),
        adc_sample_rate_hz=float(radar["adc_sample_rate_hz"]),
        chirp_duration_s=float(radar["ramp_end_time_s"]),
        chirps_per_frame=int(radar["physical_chirps_per_frame"]),
        num_range_bins=int(radar["adc_samples_per_chirp"]),
        range_resolution_m=float(radar["range_resolution_m"]),
    )
    adc = ADCCubeObservation(
        adc_cube=np.asarray(capture.adc_cube),
        range_axis_m=range_axis_m(frontend_config),
        frame_times_s=np.asarray(capture.frame_times_s),
        scatterers=(),
    )
    return CapturedFrontendInput(
        adc=adc,
        frontend_config=frontend_config,
        manifest=capture.manifest,
        source_directory=capture.directory,
    )


def load_captured_fusion_input(
    path: Union[str, Path],
    *,
    max_adxl_gap_ns: Optional[int] = None,
    require_fusion_ready: bool = False,
    require_algorithm_ready: bool = True,
    nominal_adxl_axis: str = "x",
    nominal_adxl_sign: int = 1,
    mmap_mode: Optional[str] = "r",
    allow_simulation: bool = False,
) -> CapturedFusionInput:
    """Load a self-contained synchronized capture for asynchronous Phase-1.

    Raw sensor timelines remain untouched. The returned acceleration object
    carries exact interval preintegration for state propagation; its
    ``measured_mps2`` vector is only a radar-grid diagnostic used by legacy
    spectral and fixed-rate compatibility paths.
    """

    try:
        from mmwavecapture.fusion_input import load_fusion_input
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "the fusion reader requires the local capture_program package; "
            "install it with `pip install -e capture_program`"
        ) from exc
    from .fusion_adapter import preintegrate_acceleration_to_radar

    if not isinstance(allow_simulation, (bool, np.bool_)):
        raise ValueError("allow_simulation must be boolean")
    capture = load_fusion_input(
        path,
        mmap_mode=mmap_mode,
        allow_simulation=bool(allow_simulation),
    )
    is_simulation = bool(
        getattr(getattr(capture, "provenance", None), "sync_mode", "")
        == "simulation"
    )
    if is_simulation:
        if not allow_simulation:
            raise RuntimeError("simulation capture requires explicit opt-in")
        if not bool(getattr(capture, "simulation_ready", False)):
            raise RuntimeError("simulation capture is not simulation-ready")
    axis_name = _nominal_adxl_axis(nominal_adxl_axis)
    axis_sign = _nominal_adxl_sign(nominal_adxl_sign)
    if not isinstance(require_fusion_ready, (bool, np.bool_)):
        raise ValueError("require_fusion_ready must be boolean")
    if not isinstance(require_algorithm_ready, (bool, np.bool_)):
        raise ValueError("require_algorithm_ready must be boolean")
    if require_fusion_ready and not capture.fusion_ready:
        blockers = ", ".join(capture.quality.readiness_failures)
        raise RuntimeError(f"capture is not fusion-ready: {blockers}")

    algorithm_ready = bool(
        getattr(capture, "algorithm_ready", capture.fusion_ready)
    )
    algorithm_blockers = tuple(
        getattr(
            capture.quality,
            "algorithm_readiness_failures",
            capture.quality.readiness_failures,
        )
    )
    if require_algorithm_ready and not algorithm_ready and not is_simulation:
        blockers = ", ".join(algorithm_blockers)
        raise RuntimeError(f"capture is not algorithm-ready: {blockers}")

    warnings = []

    radar_time_ns = capture.radar_adc_sample_monotonic_ns
    if radar_time_ns is None:
        if require_fusion_ready:
            raise RuntimeError("capture has no calibrated radar ADC timeline")
        radar_time_ns = capture.radar_reference_monotonic_ns
        sync_mode = capture.provenance.sync_mode
        if sync_mode == "simulation":
            timing_mode = "synthetic_monotonic_schedule"
            warnings.append(
                "simulation timestamps are a synthetic monotonic schedule; "
                "they are not measured GPIO, DRDY, or radar ADC times"
            )
        elif sync_mode == "hardware_trigger":
            timing_mode = "hardware_trigger_reference"
            warnings.append(
                "radar times use the Pi hardware-trigger reference; "
                "radar-to-ADC latency is not calibrated"
            )
        else:
            timing_mode = "software_sensor_start_reference"
            warnings.append(
                "radar times use the software sensorStart reference; "
                "radar-to-ADC latency is not calibrated"
            )
    else:
        if is_simulation:
            timing_mode = "synthetic_coherent_aperture_center"
            warnings.append(
                "radar times are the model-derived center of each synthetic "
                "coherent aperture; they are not measured radar ADC times"
            )
        else:
            timing_mode = "calibrated_adc_timeline"
    radar_time_ns = np.asarray(radar_time_ns, dtype=np.int64)
    if radar_time_ns.size < 2:
        raise RuntimeError("asynchronous fusion requires at least two radar frames")

    adxl_time_ns = np.asarray(capture.adxl_sample_monotonic_ns, dtype=np.int64)
    value_calibration = capture.value_calibration
    if value_calibration is None:
        axis_index = {"x": 0, "y": 1, "z": 2}[axis_name]
        structural_acceleration = axis_sign * np.asarray(
            capture.adxl355.acceleration_mps2[:, axis_index], dtype=float
        )
        calibrated_adc_cube = np.asarray(capture.radar.adc_cube)
        virtual_channel_count = int(calibrated_adc_cube.shape[1])
        virtual_positions = np.arange(virtual_channel_count, dtype=float) * 0.5
        range_bias_correction_m = 0.0
        signed_axis_name = axis_name if axis_sign > 0 else f"neg_{axis_name}"
        calibration_mode = f"nominal_unvalidated_adxl_{signed_axis_name}"
        if is_simulation:
            calibration_mode = "simulation_nominal_unvalidated"
            warnings.append(
                "simulation uses a laser-derived structural acceleration axis "
                "and synthetic nominal radar geometry"
            )
        else:
            warnings.append(
                "no fusion calibration was supplied; ADXL "
                f"{axis_sign:+d}*{axis_name.upper()} and nominal half-wavelength "
                "radar channel geometry are being used"
            )
    else:
        if capture.acceleration_structure_mps2 is None:
            raise RuntimeError(
                "capture calibration did not produce structural-axis acceleration"
            )
        structural_acceleration = np.asarray(
            capture.acceleration_structure_mps2,
            dtype=float,
        )
        radar_calibration = value_calibration.radar
        calibrated_adc_cube = radar_calibration.calibrated_azimuth_cube(
            capture.radar.adc_cube
        )
        virtual_channel_count = int(
            radar_calibration.azimuth_virtual_channel_indices.size
        )
        virtual_positions = np.asarray(
            radar_calibration.virtual_array_positions_wavelengths,
            dtype=float,
        )
        range_bias_correction_m = float(
            radar_calibration.range_bias_correction_m
        )
        # Missing provenance must never silently unlock absolute ADXL scale.
        # Older/custom calibration objects without this flag are therefore
        # treated as supplied-but-unvalidated.
        if bool(getattr(value_calibration, "validated", False)):
            calibration_mode = "validated"
        else:
            calibration_mode = "provided_unvalidated"
            warnings.append(
                "the supplied fusion value/geometry calibration is marked unvalidated"
            )

    calibration = getattr(capture, "calibration", None)
    if calibration is not None and not bool(
        getattr(calibration, "adxl_group_delay_calibrated", False)
    ):
        warnings.append(
            "ADXL digital-filter group delay is not calibrated; its sample "
            "timeline remains nominal/unvalidated"
        )

    valid_mask = np.isfinite(structural_acceleration)
    gap_limit_ns = _resolve_max_adxl_gap_ns(adxl_time_ns, max_adxl_gap_ns)
    preintegration = preintegrate_acceleration_to_radar(
        radar_time_ns,
        adxl_time_ns,
        structural_acceleration,
        valid_mask,
        max_allowed_gap_ns=gap_limit_ns,
    )
    interval_average = preintegration.delta_v_mps / preintegration.duration_s
    measured_on_radar_grid = np.empty(radar_time_ns.shape, dtype=float)
    measured_on_radar_grid[0] = interval_average[0]
    measured_on_radar_grid[1:] = interval_average
    acceleration = CapturedAccelerationInput(
        measured_mps2=measured_on_radar_grid,
        native_time_ns=adxl_time_ns,
        native_mps2=structural_acceleration,
        valid_mask=valid_mask,
        preintegration=preintegration,
    )

    radar_metadata = capture.radar.manifest["radar"]
    frontend_config = FrontendConfig(
        num_tx=len(radar_metadata["tx_indices"]),
        num_rx=len(radar_metadata["rx_indices"]),
        num_virtual_rx=virtual_channel_count,
        virtual_array_positions_wavelengths=tuple(
            float(value) for value in virtual_positions
        ),
        num_adc_samples=int(radar_metadata["adc_samples_per_chirp"]),
        adc_sample_rate_hz=float(radar_metadata["adc_sample_rate_hz"]),
        chirp_duration_s=float(radar_metadata["ramp_end_time_s"]),
        chirps_per_frame=int(radar_metadata["physical_chirps_per_frame"]),
        num_range_bins=int(radar_metadata["adc_samples_per_chirp"]),
        range_resolution_m=float(radar_metadata["range_resolution_m"]),
    )
    calibrated_range_axis_m = (
        range_axis_m(frontend_config)
        + range_bias_correction_m
    )
    frame_times_s = (
        radar_time_ns - radar_time_ns[0]
    ).astype(np.float64) / 1_000_000_000.0
    adc = ADCCubeObservation(
        adc_cube=np.asarray(calibrated_adc_cube),
        range_axis_m=calibrated_range_axis_m,
        frame_times_s=frame_times_s,
        scatterers=(),
    )
    return CapturedFusionInput(
        adc=adc,
        frontend_config=frontend_config,
        acceleration=acceleration,
        radar_time_ns=radar_time_ns,
        fusion_capture=capture,
        source_directory=capture.directory,
        timing_mode=timing_mode,
        calibration_mode=calibration_mode,
        warnings=tuple(warnings),
        max_adxl_gap_ns=gap_limit_ns,
        is_simulation=is_simulation,
        truth_time_ns=getattr(capture, "simulation_truth_time_ns", None),
        truth_displacement_m=getattr(
            capture, "simulation_truth_displacement_m", None
        ),
    )


def detect_captured_target_bins(
    captured: CapturedFusionInput,
    *,
    threshold_scale: float = 6.0,
    range_tolerance_bins: int = 1,
    angle_threshold_deg: float = 15.0,
    dynamic_range_db: float = 20.0,
    max_candidates: int = 12,
    return_diagnostics: bool = False,
) -> tuple[np.ndarray, np.ndarray, Any] | tuple[
    np.ndarray, np.ndarray, Any, Mapping[str, Any]
]:
    """Detect capture-derived range-angle candidates without truth information."""

    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int):
        raise ValueError("max_candidates must be a positive integer")
    if max_candidates <= 0:
        raise ValueError("max_candidates must be a positive integer")
    if not np.isfinite(dynamic_range_db) or dynamic_range_db <= 0.0:
        raise ValueError("dynamic_range_db must be finite and positive")
    range_angle = range_angle_process(captured.adc, captured.frontend_config)
    representative = np.nanmedian(np.abs(range_angle.range_angle_cube), axis=0)
    peaks = detect_peaks_2d(
        representative,
        range_angle.angle_axis_deg,
        threshold_scale=threshold_scale,
    )
    merged = merge_close_angle_peaks(
        peaks,
        range_tolerance_bins=range_tolerance_bins,
        angle_threshold_deg=angle_threshold_deg,
    )
    candidates_before = [candidate for candidate in merged if candidate.value > 0.0]
    if not candidates_before:
        raise RuntimeError("no nonzero range-angle target candidates were detected")
    candidates_with_magnitude = []
    for candidate in candidates_before:
        range_bin = int(round(candidate.range_bin))
        angle_bin = int(round(candidate.angle_bin))
        magnitude = float(representative[range_bin, angle_bin])
        candidates_with_magnitude.append((candidate, magnitude))
    strongest_magnitude = max(value for _candidate, value in candidates_with_magnitude)
    minimum_magnitude = strongest_magnitude * 10.0 ** (
        -float(dynamic_range_db) / 20.0
    )
    candidates_in_dynamic_range = [
        item for item in candidates_with_magnitude if item[1] >= minimum_magnitude
    ]
    candidates_in_dynamic_range.sort(
        key=lambda item: (
            -item[1],
            item[0].range_bin,
            item[0].angle_bin,
        )
    )
    retained = candidates_in_dynamic_range[:max_candidates]
    candidates = [candidate for candidate, _magnitude in retained]
    range_bins = np.asarray(
        [int(round(candidate.range_bin)) for candidate in candidates],
        dtype=int,
    )
    angle_bins = np.asarray(
        [int(round(candidate.angle_bin)) for candidate in candidates],
        dtype=int,
    )
    diagnostics = {
        "mode": "measured_median_peak_dynamic_range",
        "uses_truth": False,
        "threshold_scale": float(threshold_scale),
        "dynamic_range_db": float(dynamic_range_db),
        "max_candidates": int(max_candidates),
        "candidate_count_before_dynamic_range": int(len(candidates_before)),
        "candidate_count_after_dynamic_range": int(
            len(candidates_in_dynamic_range)
        ),
        "candidate_count_after_limit": int(len(candidates)),
        "strongest_median_peak_magnitude": float(strongest_magnitude),
        "minimum_retained_median_peak_magnitude": float(minimum_magnitude),
        "retained_median_peak_magnitudes": [
            float(magnitude) for _candidate, magnitude in retained
        ],
    }
    if return_diagnostics:
        return range_bins, angle_bins, range_angle, diagnostics
    return range_bins, angle_bins, range_angle


def build_captured_algorithm_input(
    captured: CapturedFusionInput,
    *,
    range_bins: Optional[Sequence[int]] = None,
    angle_bins: Optional[Sequence[int]] = None,
    magnitude_threshold: float = 0.0,
    selection_options: Optional[Mapping[str, Any]] = None,
) -> CapturedAlgorithmInput:
    """Build algorithm-visible target phase and asynchronous acceleration inputs."""

    if (range_bins is None) != (angle_bins is None):
        raise ValueError("range_bins and angle_bins must be provided together")
    if range_bins is None:
        (
            range_bin_values,
            angle_bin_values,
            range_angle,
            detection_diagnostics,
        ) = detect_captured_target_bins(captured, return_diagnostics=True)
    else:
        range_bin_values = np.asarray(range_bins, dtype=int)
        angle_bin_values = np.asarray(angle_bins, dtype=int)
        range_angle = range_angle_process(captured.adc, captured.frontend_config)
        detection_diagnostics = {
            "mode": "explicit_bin_override",
            "uses_truth": False,
            "candidate_count_after_limit": int(range_bin_values.size),
        }
    targets = extract_frontend_target_observation(
        range_angle,
        range_bin_values,
        angle_bin_values,
        radar_mount=captured.frontend_config.radar_mount,
        magnitude_threshold=magnitude_threshold,
    )
    intervals_s = np.diff(captured.radar_time_ns).astype(float) * 1.0e-9
    if np.any(~np.isfinite(intervals_s)) or np.any(intervals_s <= 0.0):
        raise RuntimeError("captured radar time intervals are invalid")
    effective_rate_hz = 1.0 / float(np.median(intervals_s))
    options = dict(selection_options or {})
    selected = select_targets_from_measurements(
        iq=targets.slow_time,
        wrapped_phase_rad=targets.wrapped_phase_rad,
        available_mask=targets.available_mask,
        measured_beta=targets.measured_beta,
        measured_acceleration_mps2=captured.acceleration.measured_mps2,
        sample_rate_hz=effective_rate_hz,
        **options,
    )
    if selected.selected_indices.size == 0:
        raise RuntimeError("no measured radar target passed fusion selection")
    radar = RadarAlgorithmInput(
        measured_beta=targets.measured_beta.copy(),
        wrapped_phase_rad=targets.wrapped_phase_rad.copy(),
        available_mask=targets.available_mask.copy(),
        selected_indices=selected.selected_indices.copy(),
        calibration_indices=selected.calibration_indices.copy(),
        initial_r=selected.calibration_initial_r.copy(),
        selection_scores=selected.quality_score.copy(),
        extra={
            "source": (
                "simulation_fusion_capture"
                if captured.is_simulation
                else "measured_fusion_capture"
            ),
            "radar_time_ns": captured.radar_time_ns.copy(),
            "timing_mode": captured.timing_mode,
            "calibration_mode": captured.calibration_mode,
            "capture_warnings": captured.warnings,
            "range_bins": targets.range_bins.copy(),
            "angle_bins": targets.angle_bins.copy(),
            "range_m": targets.range_m.copy(),
            "angle_deg": targets.angle_deg.copy(),
            "effective_radar_rate_hz": effective_rate_hz,
            "target_detection": detection_diagnostics,
        },
    )
    return CapturedAlgorithmInput(
        radar=radar,
        acceleration=captured.acceleration,
        range_angle=range_angle,
        frontend_targets=targets,
        selection=selected,
        effective_radar_rate_hz=effective_rate_hz,
        source=captured,
    )
