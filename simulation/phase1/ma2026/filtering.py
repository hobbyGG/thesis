import numpy as np


def highpass_fft(values, sample_rate_hz, cutoff_hz):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return arr.copy()
    centered = arr - float(np.nanmean(arr))
    freqs = np.fft.rfftfreq(arr.size, d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    spectrum[freqs < float(cutoff_hz)] = 0.0
    return np.fft.irfft(spectrum, n=arr.size)


def acceleration_to_displacement(acceleration_mps2, sample_rate_hz, cutoff_hz):
    accel = np.asarray(acceleration_mps2, dtype=float)
    if accel.size == 0:
        return accel.copy()
    centered = accel - float(np.nanmean(accel))
    freqs = np.fft.rfftfreq(accel.size, d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    displacement_spectrum = np.zeros_like(spectrum, dtype=complex)
    band = freqs >= float(cutoff_hz)
    omega = 2.0 * np.pi * freqs[band]
    displacement_spectrum[band] = -spectrum[band] / np.maximum(omega**2, 1e-18)
    return np.fft.irfft(displacement_spectrum, n=accel.size)
