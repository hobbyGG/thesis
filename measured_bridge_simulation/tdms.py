from __future__ import annotations

from pathlib import Path

import numpy as np
from nptdms import TdmsFile


def _channel(path: Path, group: str, channel: str):
    with TdmsFile.open(path) as tdms:
        wanted = channel.split("/")[-1]
        for item in tdms[group].channels():
            if item.name.split("/")[-1] == wanted:
                values = np.asarray(item[:], dtype=float)
                rate = 1.0 / float(item.properties["wf_increment"])
                return values, rate
    raise KeyError(f"channel {group}/{channel} not found")


def load_bridge_record(
    path: str | Path = "datafile/20250320test12.tdms",
    *,
    event_window_s: tuple[float, float] = (15.33, 19.33),
    target_rate_hz: float = 1000.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return relative time, measured laser displacement and derived acceleration."""

    values, source_rate = _channel(Path(path), "卡3激光位移", "3-4")
    start, end = (round(event_window_s[0] * source_rate), round(event_window_s[1] * source_rate))
    values = values[start:end]
    source_t = np.arange(values.size) / source_rate
    sample_count = round((event_window_s[1] - event_window_s[0]) * target_rate_hz)
    t = np.arange(sample_count) / target_rate_hz
    voltage = np.interp(t, source_t, values)
    voltage -= np.mean(voltage[: max(1, round(0.2 * target_rate_hz))])
    displacement = voltage * 1.0e-3
    frequency = np.fft.rfftfreq(sample_count, 1.0 / target_rate_hz)
    spectrum = np.fft.rfft(displacement)
    keep = (frequency >= 0.2) & (frequency <= 40.0)
    spectrum[~keep] = 0.0
    displacement = np.fft.irfft(spectrum, n=sample_count)
    acceleration = np.fft.irfft(-(2.0 * np.pi * frequency) ** 2 * np.fft.rfft(displacement), n=sample_count)
    return t, displacement, acceleration
