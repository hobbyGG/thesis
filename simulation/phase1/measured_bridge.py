from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from nptdms import TdmsFile

from .accelerometer import AccelerometerObservation
from .truth import TruthSignal


@dataclass(frozen=True)
class MeasuredBridgePreprocessConfig:
    analysis_band_hz: tuple[float, float] = (0.2, 10.0)
    powerline_hz: Sequence[float] = (50.0, 100.0, 150.0)
    powerline_half_width_hz: float = 1.0


@dataclass(frozen=True)
class MeasuredBridgeRecord:
    truth: TruthSignal
    accelerometer: AccelerometerObservation
    laser_channel: str
    acceleration_channel: str
    event_window_s: tuple[float, float]
    sample_rate_hz: float
    preprocessing: MeasuredBridgePreprocessConfig
    source_laser_sample_rate_hz: float = 0.0


def preprocess_measured_signal(signal, sample_rate_hz, config: MeasuredBridgePreprocessConfig):
    values = np.asarray(signal, dtype=float)
    if values.ndim != 1:
        values = np.ravel(values)
    if values.size == 0:
        return values.copy()
    if sample_rate_hz <= 0.0:
        raise ValueError("sample_rate_hz must be positive")

    values = values - np.nanmean(values)
    freqs = np.fft.rfftfreq(values.size, 1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(values)

    low_hz, high_hz = config.analysis_band_hz
    keep = (freqs >= float(low_hz)) & (freqs <= float(high_hz))
    for center_hz in config.powerline_hz:
        keep &= np.abs(freqs - float(center_hz)) > float(config.powerline_half_width_hz)
    spectrum[~keep] = 0.0
    return np.fft.irfft(spectrum, n=values.size)


def _preprocess_laser_truth(signal, sample_rate_hz: float, config, preprocess_config: MeasuredBridgePreprocessConfig):
    mode = str(_config_value(config, "measured_bridge_laser_truth_preprocessing", "none")).lower()
    values = np.asarray(signal, dtype=float)
    if mode in ("none", "raw", "minimal"):
        return values.copy()
    if mode in ("bandpass_notch", "filtered", "legacy"):
        return preprocess_measured_signal(values, sample_rate_hz, preprocess_config)
    raise ValueError(f"unsupported measured_bridge_laser_truth_preprocessing: {mode}")


def _preprocess_derived_accel_displacement(q_m, sample_rate_hz: float, config):
    mode = str(_config_value(config, "measured_bridge_derived_accel_preprocessing", "bandpass_notch")).lower()
    values = np.asarray(q_m, dtype=float)
    if mode in ("none", "raw", "minimal"):
        return values.copy()
    if mode in ("bandpass_notch", "filtered"):
        preprocess_config = MeasuredBridgePreprocessConfig(
            analysis_band_hz=tuple(_config_value(config, "measured_bridge_derived_accel_band_hz", (0.2, 30.0))),
            powerline_hz=tuple(_config_value(config, "measured_bridge_powerline_hz", (50.0, 100.0, 150.0))),
            powerline_half_width_hz=float(
                _config_value(config, "measured_bridge_powerline_half_width_hz", 1.0)
            ),
        )
        return preprocess_measured_signal(values, sample_rate_hz, preprocess_config)
    raise ValueError(f"unsupported measured_bridge_derived_accel_preprocessing: {mode}")


def _config_value(config, name: str, default):
    return getattr(config, name, default)


def _resolve_project_path(path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[2] / candidate


def _normalize_channel_name(name: str) -> str:
    return str(name).split("/")[-1]


def _read_tdms_channel(path: Path, group_name: str, channel_name: str) -> tuple[np.ndarray, float]:
    wanted = _normalize_channel_name(channel_name)
    with TdmsFile.open(path) as tdms:
        group = tdms[group_name]
        for channel in group.channels():
            if _normalize_channel_name(channel.name) == wanted:
                dt = float(channel.properties.get("wf_increment", 0.000333325))
                if dt <= 0.0:
                    raise ValueError(f"invalid sample interval for {group_name}/{channel_name}: {dt}")
                return np.asarray(channel[:], dtype=float), 1.0 / dt
    raise KeyError(f"channel {group_name}/{channel_name} not found in {path}")


def _slice_event(values: np.ndarray, sample_rate_hz: float, window_s: tuple[float, float]) -> np.ndarray:
    start_s, end_s = window_s
    if end_s <= start_s:
        raise ValueError("measured_bridge_event_window_s must be increasing")
    start = max(0, int(round(float(start_s) * float(sample_rate_hz))))
    end = min(values.size, int(round(float(end_s) * float(sample_rate_hz))))
    if end <= start:
        raise ValueError("measured bridge event window does not overlap the TDMS channel")
    return values[start:end]


def _resample(values, source_rate_hz: float, target_rate_hz: float, duration_s: float):
    if source_rate_hz <= 0.0 or target_rate_hz <= 0.0:
        raise ValueError("sample rates must be positive")
    if duration_s <= 0.0:
        raise ValueError("duration_s must be positive")

    source_t = np.arange(len(values), dtype=float) / float(source_rate_hz)
    n_samples = int(round(float(duration_s) * float(target_rate_hz)))
    target_t = np.arange(n_samples, dtype=float) / float(target_rate_hz)
    if values.size == 0:
        return target_t, np.zeros_like(target_t)
    return target_t, np.interp(target_t, source_t, values)


def _apply_time_shift(values, sample_rate_hz: float, shift_s: float):
    if shift_s == 0.0 or len(values) == 0:
        return values
    t = np.arange(len(values), dtype=float) / float(sample_rate_hz)
    return np.interp(t - float(shift_s), t, values, left=values[0], right=values[-1])


def _differentiate_displacement(q_m, sample_rate_hz: float):
    values = np.asarray(q_m, dtype=float)
    if values.size <= 1:
        return np.zeros_like(values), np.zeros_like(values)
    if sample_rate_hz <= 0.0:
        raise ValueError("sample_rate_hz must be positive")

    freqs = np.fft.rfftfreq(values.size, 1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(values - np.mean(values))
    omega = 2.0 * np.pi * freqs
    velocity = np.fft.irfft(1j * omega * spectrum, n=values.size)
    acceleration = np.fft.irfft(-(omega**2) * spectrum, n=values.size)
    return velocity, acceleration


def _derived_acceleration_observation(a_true, t, config):
    noise_std = float(
        _config_value(
            config,
            "measured_bridge_derived_accel_noise_std_mps2",
            _config_value(config, "accel_noise_std_mps2", 0.02),
        )
    )
    rng = np.random.default_rng(int(_config_value(config, "seed", 2026)) + 41)
    noise = rng.normal(0.0, noise_std, size=a_true.shape)
    drift = (
        float(_config_value(config, "accel_drift_mps2", 0.0)) * (t / t[-1])
        if t.size > 1
        else np.zeros_like(t)
    )
    bias = np.full_like(t, float(_config_value(config, "accel_bias_mps2", 0.0))) + drift
    return np.asarray(a_true, dtype=float) + bias + noise, bias, noise


def load_measured_bridge_record(config) -> MeasuredBridgeRecord:
    tdms_path = _resolve_project_path(_config_value(config, "measured_bridge_tdms_path", "datafile/20250320test12.tdms"))
    laser_group = _config_value(config, "measured_bridge_laser_group", "卡3激光位移")
    laser_channel = _config_value(config, "measured_bridge_laser_channel", "3-4")
    accel_group = _config_value(config, "measured_bridge_acceleration_group", "卡1梁振动")
    accel_channel = _config_value(config, "measured_bridge_acceleration_channel", "1-5")
    accel_source = _config_value(config, "measured_bridge_acceleration_source", "tdms")

    laser_raw, laser_fs = _read_tdms_channel(tdms_path, laser_group, laser_channel)
    if accel_source == "tdms":
        accel_raw, accel_fs = _read_tdms_channel(tdms_path, accel_group, accel_channel)
    elif accel_source == "laser_derived":
        accel_raw = None
        accel_fs = laser_fs
    else:
        raise ValueError(f"unsupported measured_bridge_acceleration_source: {accel_source}")

    event_window_s = tuple(_config_value(config, "measured_bridge_event_window_s", (15.33, 19.33)))
    laser_slice = _slice_event(laser_raw, laser_fs, event_window_s)
    accel_slice = _slice_event(accel_raw, accel_fs, event_window_s) if accel_raw is not None else None

    preprocess_config = MeasuredBridgePreprocessConfig(
        analysis_band_hz=tuple(_config_value(config, "measured_bridge_analysis_band_hz", (0.2, 10.0))),
        powerline_hz=tuple(_config_value(config, "measured_bridge_powerline_hz", (50.0, 100.0, 150.0))),
        powerline_half_width_hz=float(
            _config_value(config, "measured_bridge_powerline_half_width_hz", 1.0)
        ),
    )
    laser_truth = _preprocess_laser_truth(laser_slice, laser_fs, config, preprocess_config)
    if accel_slice is not None:
        accel_filtered = preprocess_measured_signal(accel_slice, accel_fs, preprocess_config)
        accel_filtered = _apply_time_shift(
            accel_filtered,
            accel_fs,
            float(_config_value(config, "measured_bridge_time_shift_s", -0.01)),
        )
    else:
        accel_filtered = None

    target_rate_hz = float(_config_value(config, "sample_rate_hz", 1000.0))
    target_duration_s = min(
        float(_config_value(config, "duration_s", event_window_s[1] - event_window_s[0])),
        float(event_window_s[1] - event_window_s[0]),
    )
    t, q_v = _resample(laser_truth, laser_fs, target_rate_hz, target_duration_s)

    q_m = q_v * float(_config_value(config, "measured_bridge_laser_scale_m_per_v", 1.0e-3))
    cold_start_s = float(_config_value(config, "cold_start_duration_s", 0.05))
    baseline_samples = max(1, min(q_m.size, int(round(cold_start_s * target_rate_hz))))
    q_m = q_m - np.mean(q_m[:baseline_samples])

    v_mps, a_from_raw_laser = _differentiate_displacement(q_m, target_rate_hz)
    if accel_source == "tdms":
        _, a_v = _resample(accel_filtered, accel_fs, target_rate_hz, target_duration_s)
        a_meas = (
            float(_config_value(config, "measured_bridge_accel_sign", -1.0))
            * float(_config_value(config, "measured_bridge_accel_scale_mps2_per_v", 1.0))
            * a_v
        )
        bias = np.zeros_like(a_meas)
        a_reference = a_from_raw_laser
        noise = a_meas - a_reference
        acceleration_channel = f"{accel_group}/{accel_channel}"
    else:
        accel_q_m = _preprocess_derived_accel_displacement(q_m, target_rate_hz, config)
        _, a_reference = _differentiate_displacement(accel_q_m, target_rate_hz)
        a_meas, bias, noise = _derived_acceleration_observation(a_reference, t, config)
        acceleration_channel = f"laser_derived({laser_group}/{laser_channel})"

    truth = TruthSignal(
        t=t,
        q_m=q_m,
        v_mps=v_mps,
        a_mps2=a_reference,
        frequencies_hz=tuple(preprocess_config.analysis_band_hz),
        amplitudes_m=(float(np.max(np.abs(q_m))) if q_m.size else 0.0,),
        phases_rad=(0.0,),
    )
    accelerometer = AccelerometerObservation(
        true_mps2=a_reference,
        measured_mps2=a_meas,
        bias_mps2=bias,
        noise_mps2=noise,
    )

    return MeasuredBridgeRecord(
        truth=truth,
        accelerometer=accelerometer,
        laser_channel=f"{laser_group}/{laser_channel}",
        acceleration_channel=acceleration_channel,
        event_window_s=(float(event_window_s[0]), float(event_window_s[0]) + target_duration_s),
        sample_rate_hz=target_rate_hz,
        preprocessing=preprocess_config,
        source_laser_sample_rate_hz=float(laser_fs),
    )
