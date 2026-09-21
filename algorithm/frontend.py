from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .angle_estimation import estimate_local_music_ml
from .types import FrontendConfig


def range_axis_m(config: FrontendConfig) -> np.ndarray:
    return np.arange(config.num_range_bins, dtype=float) * config.range_resolution_m


def virtual_array_positions(config: FrontendConfig) -> np.ndarray:
    if config.virtual_array_positions_wavelengths:
        return np.asarray(config.virtual_array_positions_wavelengths, dtype=float)
    return np.arange(config.num_virtual_rx, dtype=float) * config.antenna_spacing_wavelengths


def angle_axis_deg(config: FrontendConfig) -> np.ndarray:
    spatial = np.fft.fftshift(np.fft.fftfreq(config.num_angle_bins, d=1.0))
    return np.rad2deg(np.arcsin(np.clip(spatial / config.antenna_spacing_wavelengths, -1.0, 1.0)))


@dataclass(frozen=True)
class RangeAngleData:
    cube: np.ndarray
    range_axis_m: np.ndarray
    angle_axis_deg: np.ndarray
    snapshots: np.ndarray
    positions_wavelengths: np.ndarray


@dataclass(frozen=True)
class TargetData:
    slow_time: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    angle_deg: np.ndarray
    measured_beta: np.ndarray
    range_bins: np.ndarray
    angle_bins: np.ndarray
    range_m: np.ndarray


def range_angle_process(adc_cube: np.ndarray, config: FrontendConfig) -> RangeAngleData:
    adc = np.asarray(adc_cube, dtype=complex)
    range_fft = np.fft.fft(adc, n=config.num_range_bins, axis=2)
    snapshots = np.transpose(range_fft, (0, 2, 1))
    positions = virtual_array_positions(config)
    window = np.hanning(config.num_virtual_rx) if config.angle_window == "hann" else np.ones(config.num_virtual_rx)
    spatial = np.fft.fftshift(np.fft.fftfreq(config.num_angle_bins, d=1.0))
    steering = np.exp(-2j * np.pi * positions[:, None] * (spatial / config.antenna_spacing_wavelengths)[None, :])
    cube = np.einsum("frv,va->fra", snapshots * window[None, None, :], steering, optimize=True)
    cube /= float(config.num_adc_samples * max(np.sum(window), 1.0e-12))
    return RangeAngleData(cube, range_axis_m(config), angle_axis_deg(config), snapshots, positions)


def extract_targets(
    data: RangeAngleData,
    range_bins: Sequence[int],
    angle_bins: Sequence[int],
    config: FrontendConfig,
) -> TargetData:
    ranges = np.asarray(range_bins, dtype=int)
    angles = np.asarray(angle_bins, dtype=int)
    slow_time = np.empty((ranges.size, data.cube.shape[0]), dtype=complex)
    angle_values = data.angle_axis_deg[angles].copy()
    for range_bin in sorted(set(ranges.tolist())):
        target_indices = np.flatnonzero(ranges == range_bin)
        coarse = data.angle_axis_deg[angles[target_indices]]
        refined = estimate_local_music_ml(
            data.snapshots[:, range_bin, :].T,
            data.positions_wavelengths,
            coarse,
            search_half_width_u=config.angle_search_half_width_u,
            music_grid_size=config.angle_music_grid_size,
            max_snapshots=config.angle_max_snapshots,
        )
        count = min(target_indices.size, refined.angles_deg.size)
        angle_values[target_indices[:count]] = refined.angles_deg[:count]
        slow_time[target_indices[:count]] = refined.source_slow_time[:count]
        for target_index in target_indices[count:]:
            slow_time[target_index] = data.cube[:, range_bin, angles[target_index]]
    available = np.isfinite(slow_time.real) & np.isfinite(slow_time.imag) & (np.abs(slow_time) > 0.0)
    wrapped = np.angle(slow_time)
    wrapped[~available] = np.nan
    beta = 1.0 / np.abs(np.cos(np.deg2rad(angle_values)))
    return TargetData(
        slow_time=slow_time,
        wrapped_phase_rad=wrapped,
        available_mask=available,
        angle_deg=angle_values,
        measured_beta=beta,
        range_bins=ranges,
        angle_bins=angles,
        range_m=data.range_axis_m[ranges],
    )
