"""Deterministic hardware error models applied before capture-package export.

The capture reader and Phase-1 algorithm deliberately contain no stochastic
sensor model.  These helpers are the single boundary where simulated hardware
errors enter the fixed magnetic-levitation capture package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


STANDARD_GRAVITY_MPS2 = 9.80665


@dataclass(frozen=True)
class Adxl355ErrorModelOutput:
    acceleration_raw: np.ndarray
    acceleration_mps2: np.ndarray
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Iwr1843ErrorModelOutput:
    chirp_cube: np.ndarray
    metadata: dict[str, Any]


def _band_limited_noise(
    sample_count: int,
    sample_rate_hz: float,
    bandwidth_hz: float,
    rms: float,
    rng: np.random.Generator,
) -> np.ndarray:
    white = rng.standard_normal(sample_count)
    spectrum = np.fft.rfft(white)
    frequencies = np.fft.rfftfreq(sample_count, d=1.0 / sample_rate_hz)
    spectrum[frequencies > bandwidth_hz] = 0.0
    noise = np.fft.irfft(spectrum, n=sample_count)
    noise -= float(np.mean(noise))
    measured_rms = float(np.sqrt(np.mean(noise**2)))
    if measured_rms <= 0.0:
        raise RuntimeError("cannot normalize ADXL355 band-limited noise")
    return noise * (rms / measured_rms)


def apply_adxl355_datasheet_typical_calibrated_25c(
    physical_acceleration_mps2: np.ndarray,
    *,
    sample_rate_hz: float,
    seed: int,
) -> Adxl355ErrorModelOutput:
    """Apply the calibrated 25 °C, ±2 g ADXL355 typical-noise profile."""

    physical = np.asarray(physical_acceleration_mps2, dtype=np.float64)
    if physical.ndim != 1 or physical.size < 2:
        raise ValueError("physical acceleration must be a one-dimensional series")
    if not np.all(np.isfinite(physical)):
        raise ValueError("physical acceleration must be finite")
    if sample_rate_hz <= 0.0:
        raise ValueError("sample_rate_hz must be positive")

    profile_name = "datasheet_typical_calibrated_25c"
    range_g = 2
    adc_bits = 20
    sensitivity_lsb_per_g = 256_000.0
    noise_density_ug_per_sqrt_hz = 22.5
    equivalent_noise_bandwidth_hz = 250.0
    noise_density_mps2_per_sqrt_hz = (
        noise_density_ug_per_sqrt_hz * 1.0e-6 * STANDARD_GRAVITY_MPS2
    )
    noise_rms_mps2 = (
        noise_density_mps2_per_sqrt_hz
        * np.sqrt(equivalent_noise_bandwidth_hz)
    )
    rng = np.random.default_rng(int(seed))
    acceleration = np.empty((physical.size, 3), dtype=np.float64)
    for axis in range(3):
        axis_noise = _band_limited_noise(
            physical.size,
            sample_rate_hz,
            equivalent_noise_bandwidth_hz,
            noise_rms_mps2,
            rng,
        )
        acceleration[:, axis] = axis_noise
    acceleration[:, 0] += physical

    scale_mps2_per_lsb = STANDARD_GRAVITY_MPS2 / sensitivity_lsb_per_g
    raw = np.rint(acceleration / scale_mps2_per_lsb)
    raw = np.clip(raw, -(2 ** (adc_bits - 1)), 2 ** (adc_bits - 1) - 1)
    raw = raw.astype(np.int32)
    quantized = raw.astype(np.float64) * scale_mps2_per_lsb
    metadata = {
        "schema_version": 1,
        "profile": profile_name,
        "seed": int(seed),
        "manufacturer": "Analog Devices",
        "device": "ADXL355",
        "datasheet": "ADXL354/ADXL355 Data Sheet",
        "datasheet_revision": "Rev. D",
        "range_g": range_g,
        "adc_bits": adc_bits,
        "sensitivity_lsb_per_g": sensitivity_lsb_per_g,
        "odr_hz": float(sample_rate_hz),
        "noise": {
            "enabled": True,
            "type": "deterministic_fft_band_limited_gaussian",
            "density_ug_per_sqrt_hz": noise_density_ug_per_sqrt_hz,
            "equivalent_bandwidth_hz": equivalent_noise_bandwidth_hz,
            "bandwidth_approximation": (
                "engineering rectangular ENBW approximation at ODR/4; the "
                "datasheet specifies -1.93 dB at ODR/4, not an exact ENBW"
            ),
            "rms_formula": "density_ug_per_sqrt_hz * 1e-6 * g * sqrt(bandwidth_hz)",
            "target_rms_mps2": float(noise_rms_mps2),
            "axis_noise_independent": True,
        },
        "quantization": {
            "enabled": True,
            "rounding": "nearest_lsb",
            "signed_code_min": -(2 ** (adc_bits - 1)),
            "signed_code_max": 2 ** (adc_bits - 1) - 1,
            "mps2_per_lsb": float(scale_mps2_per_lsb),
        },
        "not_injected": {
            "initial_zero_bias": "calibrated before capture",
            "sensitivity_tolerance": "calibrated before capture",
            "cross_axis_sensitivity": "calibrated before capture",
            "nonlinearity": "excluded from the calibrated typical-noise profile",
            "temperature_drift": "25 degC constant-temperature profile",
            "digital_filter_group_delay": (
                "not injected into the synthetic timeline; the capture manifest "
                "declares it uncalibrated and real hardware must measure and "
                "compensate this delay before strict fusion"
            ),
        },
        "datasheet_specifications": {
            "zero_g_offset_mg": {
                "typical_absolute": 25.0,
                "minimum_maximum_absolute": 75.0,
            },
            "sensitivity_lsb_per_g_at_2g": {
                "minimum": 235_520.0,
                "typical": 256_000.0,
                "maximum": 276_480.0,
            },
            "nonlinearity_percent_full_scale": 0.1,
            "cross_axis_sensitivity_percent": 1.0,
            "sensitivity_temperature_percent_per_deg_c": 0.01,
            "offset_temperature_max_mg_per_deg_c": 0.15,
            "digital_filter_group_delay_ms_at_1khz_odr": 1.78,
        },
    }
    return Adxl355ErrorModelOutput(
        acceleration_raw=raw,
        acceleration_mps2=quantized,
        metadata=metadata,
    )


def apply_iwr1843_receiver_and_adc_model(
    clean_chirp_cube: np.ndarray,
    *,
    target_amplitudes: Sequence[float],
    target_snr_db: Sequence[float],
    seed: int,
) -> Iwr1843ErrorModelOutput:
    """Apply one receiver-AWGN layer followed by signed 12-bit I/Q quantization."""

    clean = np.asarray(clean_chirp_cube, dtype=np.complex128)
    if clean.ndim != 4 or not np.all(np.isfinite(clean)):
        raise ValueError("clean chirp cube must be a finite four-dimensional array")
    amplitudes = np.asarray(target_amplitudes, dtype=float)
    snr_db = np.asarray(target_snr_db, dtype=float)
    if amplitudes.shape != snr_db.shape or amplitudes.size == 0:
        raise ValueError("target amplitudes and SNR assumptions must align")
    finite = np.isfinite(snr_db)
    receiver_noise_power = float(
        np.sum(amplitudes[finite] ** 2 / (10.0 ** (snr_db[finite] / 10.0)))
    )
    rng = np.random.default_rng(int(seed))
    noise_std_per_component = np.sqrt(receiver_noise_power / 2.0)
    receiver_noise = noise_std_per_component * (
        rng.standard_normal(clean.shape) + 1j * rng.standard_normal(clean.shape)
    )
    noised = clean + receiver_noise

    adc_bits = 12
    code_min = -(2 ** (adc_bits - 1))
    code_max = 2 ** (adc_bits - 1) - 1
    peak_component = float(
        max(np.max(np.abs(noised.real)), np.max(np.abs(noised.imag)))
    )
    if peak_component <= 0.0:
        volts_per_code = 1.0
    else:
        volts_per_code = peak_component / float(code_max)
    i_code = np.clip(np.rint(noised.real / volts_per_code), code_min, code_max)
    q_code = np.clip(np.rint(noised.imag / volts_per_code), code_min, code_max)
    # Capture-contract complex64 stores the signed ADC codes directly. The
    # inverse scale is metadata only and must not turn codes back into volts.
    quantized = (i_code + 1j * q_code).astype(np.complex64)
    metadata = {
        "schema_version": 1,
        "profile": "datasheet_typical_calibrated_25c",
        "seed": int(seed),
        "manufacturer": "Texas Instruments",
        "device": "IWR1843",
        "datasheet": "IWR1843 single-chip 76-to-81-GHz FMCW radar sensor data sheet",
        "datasheet_revision": "Rev. B (SWRS228B)",
        "receiver_noise": {
            "enabled": True,
            "injection_layers": 1,
            "type": "complex_receiver_awgn",
            "noise_power_formula": "sum(amplitude^2 / 10^(target_snr_db/10))",
            "noise_power": receiver_noise_power,
            "noise_power_semantics": (
                "one common ADC receiver-AWGN power derived from the scenario "
                "link-budget assumptions"
            ),
            "component_std": float(noise_std_per_component),
            "target_snr_db": snr_db.tolist(),
            "target_snr_semantics": (
                "scenario link-budget assumption; not a manufacturer error specification"
            ),
            "noise_figure_db_at_77_to_81_ghz": 15.0,
            "noise_figure_limitation": (
                "NF alone cannot determine ADC SNR without RCS, received power, "
                "bandwidth, gain chain, and ADC full-scale mapping"
            ),
        },
        "quantization": {
            "enabled": True,
            "i_bits": adc_bits,
            "q_bits": adc_bits,
            "signed_code_min": code_min,
            "signed_code_max": code_max,
            "rounding": "nearest_code",
            "full_scale_mapping": "observed_package_peak_to_positive_full_scale",
            "pre_quantization_value_per_code": float(volts_per_code),
            "stored_values": "signed_integer_codes_in_complex64",
        },
        "channel_mismatch": {
            "enabled": False,
            "gain_bound_db": 0.5,
            "phase_bound_deg": 3.0,
            "reason": "default profile assumes channel calibration before capture",
        },
        "dca1000": {
            "noise_injected": False,
            "packet_integrity": "complete_or_fail_closed",
        },
    }
    return Iwr1843ErrorModelOutput(chirp_cube=quantized, metadata=metadata)
