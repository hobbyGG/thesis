from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026RangeBinInput:
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    range_bins: np.ndarray


def rangebin_input_from_range_angle(range_angle, config):
    cube = np.asarray(range_angle.range_angle_cube, dtype=complex)
    if cube.ndim != 3:
        raise ValueError("range_angle_cube must have shape (frames, range_bins, angle_bins)")
    if cube.shape[1] == 0:
        return Ma2026RangeBinInput(
            wrapped_phase_rad=np.empty((0, cube.shape[0]), dtype=float),
            available_mask=np.empty((0, cube.shape[0]), dtype=bool),
            range_bins=np.empty(0, dtype=int),
        )

    range_power = np.nanmedian(np.sum(np.abs(cube) ** 2, axis=2), axis=0)
    candidate_bins = _range_local_maxima(range_power, float(config.rangebin_threshold_ratio), int(config.max_rangebin_targets))
    slow_time = []
    available = []
    for range_bin in candidate_bins:
        series = np.sum(cube[:, int(range_bin), :], axis=1)
        mask = np.isfinite(series.real) & np.isfinite(series.imag) & (np.abs(series) > 0.0)
        wrapped = np.angle(series).astype(float)
        wrapped[~mask] = np.nan
        slow_time.append(wrapped)
        available.append(mask)
    if not slow_time:
        return Ma2026RangeBinInput(
            wrapped_phase_rad=np.empty((0, cube.shape[0]), dtype=float),
            available_mask=np.empty((0, cube.shape[0]), dtype=bool),
            range_bins=np.empty(0, dtype=int),
        )
    return Ma2026RangeBinInput(
        wrapped_phase_rad=np.asarray(slow_time, dtype=float),
        available_mask=np.asarray(available, dtype=bool),
        range_bins=np.asarray(candidate_bins, dtype=int),
    )


def _range_local_maxima(range_power, threshold_ratio, max_targets):
    power = np.asarray(range_power, dtype=float)
    if power.size == 0 or not np.any(np.isfinite(power)):
        return np.empty(0, dtype=int)
    finite_power = np.nan_to_num(power, nan=-np.inf)
    threshold = float(threshold_ratio) * float(np.nanmax(finite_power))
    peaks = []
    for idx, value in enumerate(finite_power):
        left = finite_power[idx - 1] if idx > 0 else -np.inf
        right = finite_power[idx + 1] if idx + 1 < finite_power.size else -np.inf
        if value >= threshold and value >= left and value >= right:
            peaks.append((idx, float(value)))
    peaks.sort(key=lambda item: (-item[1], item[0]))
    selected = [idx for idx, _ in peaks[: max(0, int(max_targets))]]
    selected.sort()
    return np.asarray(selected, dtype=int)
