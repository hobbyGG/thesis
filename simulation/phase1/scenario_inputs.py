"""Scenario-level data assembly for Phase 1 validation.

This module converts one ``Phase1Config`` into the named views consumed by
registered methods. It is the orchestration boundary between simulation data
generation, frontend target selection, and estimator execution.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .accelerometer import AccelerometerObservation, build_accelerometer_observation
from .config import Phase1Config
from .frontend import (
    ADCCubeObservation,
    FrontendConfig,
    FrontendTargetObservation,
    RangeAngleObservation,
    angle_deg_to_measured_kappa,
    extract_frontend_target_observation,
    range_angle_process,
    simulate_adc_cube,
)
from .ma2026 import Ma2026Config, Ma2026RangeBinInput, rangebin_input_from_range_angle
from .radar import RadarAlgorithmInput, RadarObservation, simulate_radar_targets, to_algorithm_radar_input
from .selection import (
    DetectedPeak,
    MergedPeak,
    SelectedTargetSet,
    SelectionDiagnostics,
    detect_peaks_2d,
    merge_close_angle_peaks,
    select_targets_from_measurements,
)
from .truth import TruthSignal, generate_truth_signal


@dataclass(frozen=True)
class FrontendViews:
    frontend_config: FrontendConfig
    adc_cube: ADCCubeObservation
    range_angle_maps: RangeAngleObservation
    frontend_targets: FrontendTargetObservation
    detected_peaks: tuple[DetectedPeak, ...]
    merged_peaks: tuple[MergedPeak, ...]
    selected_targets: SelectedTargetSet
    selected_frontend_targets: Optional[FrontendTargetObservation]
    target_reference_indices: np.ndarray

    @property
    def target_tracks(self):
        return self.selected_targets.diagnostics.tracks

    @property
    def selection_diagnostics(self) -> SelectionDiagnostics:
        return self.selected_targets.diagnostics

    def artifacts(self):
        return {
            "frontend_config": self.frontend_config,
            "adc_cube": self.adc_cube,
            "range_angle_maps": self.range_angle_maps,
            "frontend_targets": self.frontend_targets,
            "detected_peaks": list(self.detected_peaks),
            "merged_peaks": list(self.merged_peaks),
            "target_tracks": self.target_tracks,
            "selected_targets": self.selected_targets,
            "selected_frontend_targets": self.selected_frontend_targets,
            "selection_diagnostics": self.selection_diagnostics,
            "target_reference_indices": self.target_reference_indices,
        }


@dataclass(frozen=True)
class RadarViews:
    target_level: RadarObservation
    target_algorithm: RadarAlgorithmInput
    selected_frontend: RadarAlgorithmInput
    range_bin_only: RadarAlgorithmInput
    ma2026_rangebin: Ma2026RangeBinInput
    best_target_index: int


@dataclass(frozen=True)
class ScenarioInputs:
    scenario: Phase1Config
    truth: TruthSignal
    accelerometer: AccelerometerObservation
    radar: RadarViews
    frontend: FrontendViews
    ma2026_config: Ma2026Config

    def artifacts(self):
        artifacts = {
            "scenario": self.scenario,
            "truth": self.truth,
            "radar": self.radar.target_level,
            "accelerometer": self.accelerometer,
            "radar_input": self.radar.selected_frontend,
            "range_bin_only_input": self.radar.range_bin_only,
            "ma2026_rangebin_input": self.radar.ma2026_rangebin,
        }
        artifacts.update(self.frontend.artifacts())
        return artifacts


def build_scenario_inputs(scenario: Phase1Config, ma2026_config: Optional[Ma2026Config] = None) -> ScenarioInputs:
    truth = generate_truth_signal(scenario)
    target_radar = simulate_radar_targets(truth, scenario)
    target_algorithm = to_algorithm_radar_input(target_radar)
    accelerometer = build_accelerometer_observation(truth, scenario)
    frontend = build_frontend_views(truth, accelerometer, scenario)
    ma_config = ma2026_config or Ma2026Config()
    ma2026_rangebin = rangebin_input_from_range_angle(frontend.range_angle_maps, ma_config)
    radar = RadarViews(
        target_level=target_radar,
        target_algorithm=target_algorithm,
        selected_frontend=selected_frontend_algorithm_input(frontend.frontend_targets, frontend.selected_targets),
        range_bin_only=range_bin_only_mixed_input(frontend, scenario),
        ma2026_rangebin=ma2026_rangebin,
        best_target_index=best_target_index(target_radar),
    )
    return ScenarioInputs(
        scenario=scenario,
        truth=truth,
        accelerometer=accelerometer,
        radar=radar,
        frontend=frontend,
        ma2026_config=ma_config,
    )


def build_frontend_views(
    truth: TruthSignal,
    accelerometer: AccelerometerObservation,
    scenario: Phase1Config,
) -> FrontendViews:
    frontend_config = FrontendConfig(
        num_adc_samples=int(scenario.adc_samples_per_chirp),
        adc_sample_rate_hz=float(scenario.adc_sample_rate_hz),
        chirp_duration_s=float(scenario.chirp_duration_s),
        chirps_per_frame=int(scenario.chirps_per_frame),
    )
    adc = simulate_adc_cube(truth, scenario, frontend_config)
    range_angle = range_angle_process(adc, frontend_config)
    frame_idx = min(
        range_angle.range_angle_cube.shape[0] - 1,
        max(0, int(round(scenario.cold_start_duration_s * scenario.sample_rate_hz))),
    )
    peaks = tuple(detect_peaks_2d(np.abs(range_angle.range_angle_cube[frame_idx]), range_angle.angle_axis_deg))
    merged = tuple(merge_close_angle_peaks(peaks))
    range_bins, angle_bins = frontend_candidate_bins(merged, range_angle)
    frontend_targets = extract_frontend_target_observation(
        range_angle,
        range_bins=range_bins,
        angle_bins=angle_bins,
        magnitude_threshold=frontend_available_threshold(range_angle.range_angle_cube)
        if scenario.dropout_target_indices
        else 0.0,
    )
    selected = select_targets_from_measurements(
        iq=frontend_targets.slow_time,
        wrapped_phase_rad=frontend_targets.wrapped_phase_rad,
        available_mask=frontend_targets.available_mask,
        measured_kappa=frontend_targets.measured_kappa,
        measured_acceleration_mps2=accelerometer.measured_mps2,
        sample_rate_hz=scenario.sample_rate_hz,
        initial_measurement_variance=scenario.initial_measurement_variance,
        min_measurement_variance=scenario.min_measurement_variance,
        max_measurement_variance=scenario.max_measurement_variance,
    )
    selected_frontend = (
        slice_frontend_targets(frontend_targets, selected.selected_indices)
        if selected.selected_indices.size
        else None
    )
    target_reference_indices = evaluation_reference_indices(
        adc.scatterers,
        frontend_targets.range_bins,
        frontend_targets.angle_bins,
        range_angle,
    )
    return FrontendViews(
        frontend_config=frontend_config,
        adc_cube=adc,
        range_angle_maps=range_angle,
        frontend_targets=frontend_targets,
        detected_peaks=peaks,
        merged_peaks=merged,
        selected_targets=selected,
        selected_frontend_targets=selected_frontend,
        target_reference_indices=target_reference_indices,
    )


def selected_frontend_algorithm_input(
    frontend_targets: FrontendTargetObservation,
    selected: SelectedTargetSet,
) -> RadarAlgorithmInput:
    return RadarAlgorithmInput(
        measured_kappa=frontend_targets.measured_kappa.copy(),
        wrapped_phase_rad=frontend_targets.wrapped_phase_rad.copy(),
        available_mask=frontend_targets.available_mask.copy(),
        selected_indices=selected.selected_indices.copy(),
        initial_r=selected.initial_r.copy(),
        selection_scores=selected.quality_score.copy(),
    )


def best_target_index(radar: RadarObservation) -> int:
    snr = np.asarray(radar.snr_db, dtype=float)
    return int(np.nanargmax(snr))


def frontend_candidate_bins(merged_peaks, range_angle):
    candidates = []
    used_bins = set()
    range_peak_values = {}
    for merged_peak in merged_peaks:
        range_bin = int(np.clip(round(merged_peak.range_bin), 0, range_angle.range_angle_cube.shape[1] - 1))
        range_peak_values[range_bin] = max(float(merged_peak.value), range_peak_values.get(range_bin, 0.0))
    for merged_peak in sorted(merged_peaks, key=lambda peak: -peak.value):
        range_bin = int(np.clip(round(merged_peak.range_bin), 0, range_angle.range_angle_cube.shape[1] - 1))
        angle_bin = int(np.clip(round(merged_peak.angle_bin), 0, range_angle.range_angle_cube.shape[2] - 1))
        if float(merged_peak.value) < 0.6 * range_peak_values.get(range_bin, float(merged_peak.value)):
            continue
        bin_key = (range_bin, angle_bin)
        if bin_key in used_bins:
            continue
        used_bins.add(bin_key)
        candidates.append((range_bin, angle_bin))

    candidates.sort(key=lambda item: (item[0], item[1]))
    if not candidates:
        return np.asarray([], dtype=int), np.asarray([], dtype=int)
    range_bins, angle_bins = zip(*candidates)
    return (
        np.asarray(range_bins, dtype=int),
        np.asarray(angle_bins, dtype=int),
    )


def frontend_available_threshold(range_angle_cube):
    magnitude = np.abs(np.asarray(range_angle_cube, dtype=complex))
    if magnitude.size == 0:
        return 0.0
    median = float(np.median(magnitude))
    mad = float(np.median(np.abs(magnitude - median)))
    return median + 6.0 * mad


def evaluation_reference_indices(scatterers, range_bins, angle_bins, range_angle):
    references = []
    for range_bin, angle_bin in zip(range_bins, angle_bins):
        _, reference_idx = nearest_scatterer_reference(
            scatterers,
            int(range_bin),
            float(range_angle.angle_axis_deg[int(angle_bin)]),
        )
        references.append(reference_idx)
    return np.asarray(references, dtype=int)


def nearest_scatterer_reference(scatterers, range_bin, angle_deg):
    best = None
    best_distance = float("inf")
    for scatterer_idx, scatterer in enumerate(scatterers):
        range_distance = abs(int(scatterer.range_bin_index) - int(range_bin))
        angle_distance = abs(float(scatterer.angle_deg) - float(angle_deg))
        if range_distance > 1 or angle_distance >= 15.0:
            continue
        distance = range_distance + angle_distance / 15.0
        if distance < best_distance:
            best = (scatterer_idx, int(scatterer.target_index))
            best_distance = distance
    if best is None:
        return None, -1
    return best


def slice_frontend_targets(frontend_targets, indices):
    indices = np.asarray(indices, dtype=int)
    references = None
    if frontend_targets.target_reference_indices is not None:
        references = frontend_targets.target_reference_indices[indices]
    return type(frontend_targets)(
        measured_kappa=frontend_targets.measured_kappa[indices].copy(),
        slow_time=frontend_targets.slow_time[indices].copy(),
        wrapped_phase_rad=frontend_targets.wrapped_phase_rad[indices].copy(),
        available_mask=frontend_targets.available_mask[indices].copy(),
        range_bins=frontend_targets.range_bins[indices].copy(),
        angle_bins=frontend_targets.angle_bins[indices].copy(),
        range_m=frontend_targets.range_m[indices].copy(),
        angle_deg=frontend_targets.angle_deg[indices].copy(),
        target_reference_indices=None if references is None else references.copy(),
    )


def range_bin_only_mixed_input(frontend: FrontendViews, scenario: Phase1Config) -> RadarAlgorithmInput:
    range_angle = frontend.range_angle_maps
    frontend_targets = frontend.frontend_targets
    range_bin = range_bin_only_reference_bin(frontend_targets, range_angle)
    cube = np.asarray(range_angle.range_angle_cube, dtype=complex)
    if range_bin < 0 or range_bin >= cube.shape[1]:
        slow_time = np.full(cube.shape[0], np.nan + 1j * np.nan, dtype=complex)
        measured_kappa = np.array([1.0], dtype=float)
    else:
        slow_time = np.sum(cube[:, range_bin, :], axis=1)
        power_by_angle = np.nanmedian(np.abs(cube[:, range_bin, :]) ** 2, axis=0)
        angle_bin = int(np.nanargmax(power_by_angle)) if power_by_angle.size else 0
        measured_kappa = np.array(
            [angle_deg_to_measured_kappa(range_angle.angle_axis_deg[angle_bin])],
            dtype=float,
        )
    available = np.isfinite(slow_time.real) & np.isfinite(slow_time.imag) & (np.abs(slow_time) > 0.0)
    wrapped = np.angle(slow_time).astype(float)[None, :]
    wrapped[:, ~available] = np.nan
    return RadarAlgorithmInput(
        measured_kappa=measured_kappa,
        wrapped_phase_rad=wrapped,
        available_mask=available[None, :],
        selected_indices=np.array([0], dtype=int),
        initial_r=np.array([scenario.initial_measurement_variance], dtype=float),
        selection_scores=np.array([1.0], dtype=float),
    )


def range_bin_only_reference_bin(frontend_targets, range_angle):
    if frontend_targets is not None and frontend_targets.range_bins.size:
        range_bins = np.asarray(frontend_targets.range_bins, dtype=int)
        angles = np.asarray(frontend_targets.angle_deg, dtype=float)
        best_range = int(range_bins[0])
        best_score = -1.0
        for range_bin in sorted(set(range_bins.tolist())):
            idx = np.flatnonzero(range_bins == range_bin)
            if idx.size == 0:
                continue
            angle_span = float(np.nanmax(angles[idx]) - np.nanmin(angles[idx])) if idx.size >= 2 else 0.0
            score = float(idx.size) + angle_span / 15.0
            if score > best_score:
                best_score = score
                best_range = int(range_bin)
        return best_range
    magnitude = np.nanmedian(np.abs(range_angle.range_angle_cube), axis=(0, 2))
    return int(np.nanargmax(magnitude)) if magnitude.size else -1


def frontend_views_to_artifacts(frontend: FrontendViews):
    return frontend.artifacts()
