from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .types import FrontendConfig


@dataclass(frozen=True)
class RangeAngleData:
    cube: np.ndarray
    range_axis_m: np.ndarray
    angle_axis_deg: np.ndarray


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


def range_axis_m(config: FrontendConfig) -> np.ndarray:
    return np.arange(config.num_range_bins, dtype=float) * config.range_resolution_m


def virtual_array_positions(config: FrontendConfig) -> np.ndarray:
    if config.virtual_array_positions_wavelengths:
        return np.asarray(config.virtual_array_positions_wavelengths, dtype=float)
    return np.arange(config.num_virtual_rx, dtype=float) * config.antenna_spacing_wavelengths


def angle_axis_deg(config: FrontendConfig) -> np.ndarray:
    spatial = np.fft.fftshift(np.fft.fftfreq(config.num_angle_bins, d=1.0))
    return np.rad2deg(np.arcsin(np.clip(spatial / config.antenna_spacing_wavelengths, -1.0, 1.0)))


def _range_spectrum(adc: np.ndarray, config: FrontendConfig) -> np.ndarray:
    """Return the retained ordinary Hamming-windowed range FFT."""

    samples = np.asarray(adc, dtype=complex)
    if samples.ndim < 1:
        raise ValueError("adc must have a fast-time axis")
    return np.fft.fft(
        samples * np.hamming(samples.shape[-1]),
        n=config.num_range_bins,
        axis=-1,
    )


def range_angle_process(adc_cube: np.ndarray, config: FrontendConfig) -> RangeAngleData:
    adc = np.asarray(adc_cube, dtype=complex)
    range_fft = _range_spectrum(adc, config)
    snapshots = np.transpose(range_fft, (0, 2, 1))
    positions = virtual_array_positions(config)
    window = np.hanning(config.num_virtual_rx) if config.angle_window == "hann" else np.ones(config.num_virtual_rx)
    spatial = np.fft.fftshift(np.fft.fftfreq(config.num_angle_bins, d=1.0))
    steering = np.exp(
        -2j * np.pi * positions[:, None]
        * (spatial / config.antenna_spacing_wavelengths)[None, :]
    )
    cube = np.einsum(
        "frv,va->fra",
        snapshots * window[None, None, :],
        steering,
        optimize=True,
    )
    cube /= float(max(np.sum(np.hamming(adc.shape[-1])), 1.0e-12) * max(np.sum(window), 1.0e-12))
    return RangeAngleData(cube, range_axis_m(config), angle_axis_deg(config))


def extract_dbf_targets_streaming(
    adc_cube: np.ndarray,
    range_bins: Sequence[int],
    angle_bins: Sequence[int],
    config: FrontendConfig,
    *,
    block_size: int = 32,
) -> TargetData:
    """Extract DBF target IQ in bounded FFT blocks."""

    source = np.asarray(adc_cube)
    if source.ndim != 3:
        raise ValueError("adc cube must have [observation, virtual, adc] axes")
    ranges = np.asarray(range_bins, dtype=int)
    angles = np.asarray(angle_bins, dtype=int)
    if ranges.ndim != 1 or angles.ndim != 1 or ranges.size != angles.size:
        raise ValueError("range and angle bins must be one dimensional and paired")
    if np.any(ranges < 0) or np.any(ranges >= config.num_range_bins):
        raise ValueError("range bin is outside the configured FFT grid")
    if np.any(angles < 0) or np.any(angles >= config.num_angle_bins):
        raise ValueError("angle bin is outside the configured DBF grid")

    count = source.shape[0]
    slow_time = np.empty((ranges.size, count), dtype=complex)
    axis = angle_axis_deg(config)
    angle_values = axis[angles].copy()
    step = max(int(block_size), 1)
    for start in range(0, count, step):
        end = min(count, start + step)
        processed = range_angle_process(source[start:end], config)
        slow_time[:, start:end] = processed.cube[:, ranges, angles].T

    available = np.isfinite(slow_time.real) & np.isfinite(slow_time.imag) & (np.abs(slow_time) > 0.0)
    wrapped = np.angle(slow_time)
    wrapped[~available] = np.nan
    beta = 1.0 / np.maximum(np.abs(np.cos(np.deg2rad(angle_values))), 1.0e-6)
    return TargetData(
        slow_time=slow_time,
        wrapped_phase_rad=wrapped,
        available_mask=available,
        angle_deg=angle_values,
        measured_beta=beta,
        range_bins=ranges,
        angle_bins=angles,
        range_m=range_axis_m(config)[ranges],
    )
