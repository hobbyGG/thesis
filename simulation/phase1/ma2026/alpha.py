from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026AlphaCalibrationResult:
    alpha: float
    slope: float
    intercept: float
    r2: float
    band_hz: tuple[float, float]
    phase_acc_rad: np.ndarray
    phase_acc_band_rad: np.ndarray
    corrected_phase_band_rad: np.ndarray
    sample_count: int


def acceleration_to_phase(acceleration_mps2, sample_rate_hz, wavelength_m, highpass_cutoff_hz=0.5):
    displacement = _acceleration_to_displacement_fft(
        acceleration_mps2,
        sample_rate_hz,
        highpass_cutoff_hz,
    )
    return 4.0 * np.pi * displacement / float(wavelength_m)


def bandpass_rows(values, sample_rate_hz, band_hz):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr.copy()
    low_hz, high_hz = _validate_band(sample_rate_hz, band_hz)
    rows, was_1d = _as_rows(arr)
    freqs = np.fft.rfftfreq(rows.shape[1], d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(rows, nan=0.0), axis=1)
    keep = (freqs >= low_hz) & (freqs <= high_hz)
    spectrum[:, ~keep] = 0.0
    filtered = np.fft.irfft(spectrum, n=rows.shape[1], axis=1)
    return filtered[0] if was_1d else filtered.reshape(arr.shape)


def calibrate_alpha_linear_fit(
    corrected_phase_rad,
    acceleration_mps2,
    sample_rate_hz,
    wavelength_m,
    band_hz=(0.5, 3.0),
    highpass_cutoff_hz=0.5,
):
    corrected = np.asarray(corrected_phase_rad, dtype=float)
    phase_acc = acceleration_to_phase(
        acceleration_mps2,
        sample_rate_hz,
        wavelength_m,
        highpass_cutoff_hz,
    )
    if corrected.shape != phase_acc.shape:
        raise ValueError("corrected_phase_rad and acceleration_mps2 must have matching shapes")

    phase_acc_band = bandpass_rows(phase_acc, sample_rate_hz, band_hz)
    corrected_band = bandpass_rows(corrected, sample_rate_hz, band_hz)

    valid = np.isfinite(corrected) & np.isfinite(acceleration_mps2) & np.isfinite(corrected_band) & np.isfinite(phase_acc_band)
    x = corrected_band[valid].astype(float, copy=False)
    y = phase_acc_band[valid].astype(float, copy=False)
    slope, intercept, r2 = _linear_fit(x, y)

    low_hz, high_hz = _validate_band(sample_rate_hz, band_hz)
    return Ma2026AlphaCalibrationResult(
        alpha=float(slope),
        slope=float(slope),
        intercept=float(intercept),
        r2=float(r2),
        band_hz=(low_hz, high_hz),
        phase_acc_rad=phase_acc,
        phase_acc_band_rad=phase_acc_band,
        corrected_phase_band_rad=corrected_band,
        sample_count=int(x.size),
    )


def _acceleration_to_displacement_fft(acceleration_mps2, sample_rate_hz, highpass_cutoff_hz):
    arr = np.asarray(acceleration_mps2, dtype=float)
    if arr.size == 0:
        return arr.copy()
    if float(sample_rate_hz) <= 0.0:
        raise ValueError("sample_rate_hz must be positive")
    rows, was_1d = _as_rows(arr)
    centered = rows - np.nanmean(rows, axis=1, keepdims=True)
    freqs = np.fft.rfftfreq(rows.shape[1], d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0), axis=1)
    displacement_spectrum = np.zeros_like(spectrum, dtype=complex)
    band = freqs >= float(highpass_cutoff_hz)
    omega = 2.0 * np.pi * freqs[band]
    displacement_spectrum[:, band] = -spectrum[:, band] / np.maximum(omega**2, 1.0e-18)
    displacement = np.fft.irfft(displacement_spectrum, n=rows.shape[1], axis=1)
    return displacement[0] if was_1d else displacement.reshape(arr.shape)


def _linear_fit(x, y):
    if x.size < 2:
        return float("nan"), float("nan"), float("nan")
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    dx = x - x_mean
    dy = y - y_mean
    denom = float(np.sum(dx**2))
    if denom <= 0.0:
        return float("nan"), float("nan"), float("nan")
    slope = float(np.sum(dx * dy) / denom)
    intercept = y_mean - slope * x_mean
    residual = y - (slope * x + intercept)
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum(dy**2))
    r2 = 1.0 if ss_tot <= 0.0 and ss_res <= 0.0 else 1.0 - ss_res / ss_tot
    return slope, intercept, r2


def _as_rows(arr):
    if arr.ndim == 1:
        return arr[None, :], True
    if arr.ndim == 2:
        return arr, False
    raise ValueError("values must be 1D or 2D")


def _validate_band(sample_rate_hz, band_hz):
    if float(sample_rate_hz) <= 0.0:
        raise ValueError("sample_rate_hz must be positive")
    if len(band_hz) != 2:
        raise ValueError("band_hz must contain low and high frequencies")
    low_hz = float(band_hz[0])
    high_hz = float(band_hz[1])
    if low_hz < 0.0 or high_hz < low_hz:
        raise ValueError("band_hz must satisfy 0 <= low <= high")
    return low_hz, high_hz
