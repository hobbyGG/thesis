from dataclasses import dataclass

import numpy as np

from ..phase_utils import prediction_correct_wrapped_phase
from .config import Ma2026Config, beta_grid
from .filtering import acceleration_to_displacement


@dataclass(frozen=True)
class Ma2026CalibrationResult:
    selected_target_index: int
    selected_range_bin: int
    selected_beta: float
    beta_values: np.ndarray
    rmse_grid_mm: np.ndarray
    highpass_cutoff_hz: float
    conversion_band_hz: tuple[float, float]


def ma2023_acceleration_aided_unwrap(wrapped_phase_rad, acceleration_mps2, beta, phase1_config):
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    accel = np.asarray(acceleration_mps2, dtype=float)
    n_samples = wrapped.size
    unwrapped = np.full(n_samples, np.nan, dtype=float)
    displacement = np.full(n_samples, np.nan, dtype=float)
    if n_samples == 0:
        return unwrapped, displacement

    finite = np.flatnonzero(np.isfinite(wrapped))
    if finite.size == 0:
        return unwrapped, displacement
    first = int(finite[0])
    phase_ref = float(wrapped[first])
    unwrapped[first] = phase_ref
    displacement[first] = 0.0
    if first + 1 < n_samples and np.isfinite(wrapped[first + 1]):
        unwrapped[first + 1] = float(prediction_correct_wrapped_phase(wrapped[first + 1], phase_ref))
        displacement[first + 1] = _phase_to_displacement(unwrapped[first + 1] - phase_ref, beta, phase1_config)

    dt = 1.0 / float(phase1_config.sample_rate_hz)
    for sample_idx in range(first + 2, n_samples):
        if not np.isfinite(wrapped[sample_idx]):
            continue
        if not np.isfinite(displacement[sample_idx - 1]) or not np.isfinite(displacement[sample_idx - 2]):
            unwrapped[sample_idx] = float(prediction_correct_wrapped_phase(wrapped[sample_idx], phase_ref))
            displacement[sample_idx] = _phase_to_displacement(unwrapped[sample_idx] - phase_ref, beta, phase1_config)
            continue
        accel_idx = min(sample_idx - 1, accel.size - 1)
        accel_value = float(accel[accel_idx]) if accel_idx >= 0 and np.isfinite(accel[accel_idx]) else 0.0
        predicted_u = 2.0 * displacement[sample_idx - 1] - displacement[sample_idx - 2] + dt * dt * accel_value
        predicted_phase = phase_ref + _displacement_to_phase(predicted_u, beta, phase1_config)
        unwrapped[sample_idx] = float(prediction_correct_wrapped_phase(wrapped[sample_idx], predicted_phase))
        displacement[sample_idx] = _phase_to_displacement(unwrapped[sample_idx] - phase_ref, beta, phase1_config)
    return unwrapped, displacement


def calibrate_best_target(rangebin_input, accel, phase1_config, ma_config: Ma2026Config = Ma2026Config()):
    wrapped = np.asarray(rangebin_input.wrapped_phase_rad, dtype=float)
    available = np.asarray(rangebin_input.available_mask, dtype=bool)
    range_bins = np.asarray(rangebin_input.range_bins, dtype=int)
    if wrapped.ndim != 2:
        raise ValueError("wrapped_phase_rad must have shape (num_targets, num_samples)")
    if available.shape != wrapped.shape:
        raise ValueError("available_mask must match wrapped_phase_rad")
    if range_bins.shape != (wrapped.shape[0],):
        raise ValueError("range_bins must have one value per target")
    beta_values = beta_grid(ma_config)
    rmse_grid = np.full((wrapped.shape[0], beta_values.size), np.inf, dtype=float)
    if wrapped.shape[0] == 0:
        return Ma2026CalibrationResult(
            -1,
            -1,
            float("nan"),
            beta_values,
            rmse_grid,
            ma_config.highpass_cutoff_hz,
            _conversion_band(ma_config),
        )

    n_cal = min(wrapped.shape[1], int(ma_config.calibration_max_samples))
    accel_values = np.asarray(accel.measured_mps2, dtype=float)[:n_cal]
    accel_disp = acceleration_to_displacement(
        accel_values,
        phase1_config.sample_rate_hz,
        ma_config.highpass_cutoff_hz,
    )
    for target_idx in range(wrapped.shape[0]):
        target_wrapped = wrapped[target_idx, :n_cal].copy()
        target_wrapped[~available[target_idx, :n_cal]] = np.nan
        rmse_grid[target_idx] = _target_beta_rmse_grid_mm(
            target_wrapped,
            available[target_idx, :n_cal],
            accel_values,
            accel_disp,
            beta_values,
            phase1_config,
            ma_config,
        )

    best_flat = int(np.nanargmin(rmse_grid))
    best_target, best_beta_idx = np.unravel_index(best_flat, rmse_grid.shape)
    return Ma2026CalibrationResult(
        selected_target_index=int(best_target),
        selected_range_bin=int(range_bins[best_target]),
        selected_beta=float(beta_values[best_beta_idx]),
        beta_values=beta_values,
        rmse_grid_mm=rmse_grid,
        highpass_cutoff_hz=float(ma_config.highpass_cutoff_hz),
        conversion_band_hz=_conversion_band(ma_config),
    )


def _phase_to_displacement(phase_delta_rad, beta, phase1_config):
    return float(beta) * phase1_config.wavelength_m() * np.asarray(phase_delta_rad, dtype=float) / (4.0 * np.pi)


def _displacement_to_phase(displacement_m, beta, phase1_config):
    return 4.0 * np.pi * np.asarray(displacement_m, dtype=float) / (float(beta) * phase1_config.wavelength_m())


def _target_beta_rmse_grid_mm(
    target_wrapped,
    target_available,
    accel_values,
    accel_disp,
    beta_values,
    phase1_config,
    ma_config: Ma2026Config,
):
    wrapped = np.asarray(target_wrapped, dtype=float)
    available = np.asarray(target_available, dtype=bool)
    accel = np.asarray(accel_values, dtype=float)
    accel_reference = np.asarray(accel_disp, dtype=float)
    beta = np.asarray(beta_values, dtype=float)
    rmse = np.full(beta.shape, np.inf, dtype=float)
    if wrapped.size == 0 or beta.size == 0:
        return rmse

    valid_wrapped = np.isfinite(wrapped) & available
    finite = np.flatnonzero(valid_wrapped)
    if finite.size == 0:
        return rmse

    n_beta = beta.size
    n_samples = wrapped.size
    unwrapped = np.full((n_beta, n_samples), np.nan, dtype=float)
    displacement = np.full((n_beta, n_samples), np.nan, dtype=float)
    first = int(finite[0])
    phase_ref = float(wrapped[first])
    unwrapped[:, first] = phase_ref
    displacement[:, first] = 0.0
    if first + 1 < n_samples and valid_wrapped[first + 1]:
        corrected = float(prediction_correct_wrapped_phase(wrapped[first + 1], phase_ref))
        unwrapped[:, first + 1] = corrected
        displacement[:, first + 1] = beta * phase1_config.wavelength_m() * (corrected - phase_ref) / (4.0 * np.pi)

    dt = 1.0 / float(phase1_config.sample_rate_hz)
    wavelength = phase1_config.wavelength_m()
    for sample_idx in range(first + 2, n_samples):
        if not valid_wrapped[sample_idx]:
            continue
        if not np.all(np.isfinite(displacement[:, sample_idx - 1])) or not np.all(
            np.isfinite(displacement[:, sample_idx - 2])
        ):
            corrected = float(prediction_correct_wrapped_phase(wrapped[sample_idx], phase_ref))
            unwrapped[:, sample_idx] = corrected
            displacement[:, sample_idx] = beta * wavelength * (corrected - phase_ref) / (4.0 * np.pi)
            continue
        accel_idx = min(sample_idx - 1, accel.size - 1)
        accel_value = float(accel[accel_idx]) if accel_idx >= 0 and np.isfinite(accel[accel_idx]) else 0.0
        predicted_u = 2.0 * displacement[:, sample_idx - 1] - displacement[:, sample_idx - 2] + dt * dt * accel_value
        predicted_phase = phase_ref + 4.0 * np.pi * predicted_u / (beta * wavelength)
        unwrapped[:, sample_idx] = wrapped[sample_idx] + 2.0 * np.pi * np.round(
            (predicted_phase - wrapped[sample_idx]) / (2.0 * np.pi)
        )
        displacement[:, sample_idx] = beta * wavelength * (unwrapped[:, sample_idx] - phase_ref) / (4.0 * np.pi)

    band_low, band_high = _conversion_band(ma_config)
    radar_band = _bandpass_fft_rows(displacement, phase1_config.sample_rate_hz, band_low, band_high)
    accel_band = _bandpass_fft_rows(accel_reference[None, :], phase1_config.sample_rate_hz, band_low, band_high)[0]
    finite_residual = np.isfinite(radar_band) & np.isfinite(accel_band)[None, :] & available[None, :]
    counts = np.count_nonzero(finite_residual, axis=1)
    residual = np.where(finite_residual, radar_band - accel_band[None, :], 0.0)
    enough = counts >= 3
    if np.any(enough):
        rmse[enough] = np.sqrt(np.sum(residual[enough] ** 2, axis=1) / counts[enough]) * 1.0e3
    return rmse


def _conversion_band(ma_config: Ma2026Config):
    low = float(ma_config.conversion_band_low_hz)
    high = float(ma_config.conversion_band_high_hz)
    if low < 0.0:
        raise ValueError("conversion_band_low_hz must be non-negative")
    if high <= low:
        raise ValueError("conversion_band_high_hz must be greater than conversion_band_low_hz")
    return low, high


def _bandpass_fft_rows(values, sample_rate_hz, low_hz, high_hz):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr.copy()
    mean = np.nanmean(arr, axis=1, keepdims=True)
    centered = arr - mean
    freqs = np.fft.rfftfreq(arr.shape[1], d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0), axis=1)
    keep = (freqs >= float(low_hz)) & (freqs <= float(high_hz))
    spectrum[:, ~keep] = 0.0
    return np.fft.irfft(spectrum, n=arr.shape[1], axis=1)


def _highpass_fft_rows(values, sample_rate_hz, cutoff_hz):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr.copy()
    mean = np.nanmean(arr, axis=1, keepdims=True)
    centered = arr - mean
    freqs = np.fft.rfftfreq(arr.shape[1], d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0), axis=1)
    spectrum[:, freqs < float(cutoff_hz)] = 0.0
    return np.fft.irfft(spectrum, n=arr.shape[1], axis=1)
