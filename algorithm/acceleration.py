from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class RadarIntervalPreintegration:
    duration_s: np.ndarray
    delta_v_mps: np.ndarray
    delta_q_m: np.ndarray
    interval_valid: np.ndarray


def preintegrate_acceleration_to_radar(
    radar_time_ns: Iterable[int],
    adxl_time_ns: Iterable[int],
    acceleration_mps2: Iterable[float],
) -> RadarIntervalPreintegration:
    """Integrate native ADXL samples over each consecutive radar interval."""

    radar = np.asarray(radar_time_ns, dtype=np.int64)
    adxl = np.asarray(adxl_time_ns, dtype=np.int64)
    accel = np.asarray(acceleration_mps2, dtype=float)
    starts, ends = radar[:-1], radar[1:]
    duration = (ends - starts).astype(float) * 1.0e-9
    delta_v = np.empty(starts.size, dtype=float)
    delta_q = np.empty(starts.size, dtype=float)
    valid = np.ones(starts.size, dtype=bool)
    for i, (start, end) in enumerate(zip(starts, ends)):
        indices = np.flatnonzero((adxl >= start) & (adxl <= end))
        nodes_t = np.r_[start, adxl[indices], end]
        nodes_a = np.interp(nodes_t, adxl, accel)
        dv = 0.0
        dq = 0.0
        for j in range(nodes_t.size - 1):
            dt = float(nodes_t[j + 1] - nodes_t[j]) * 1.0e-9
            a0, a1 = float(nodes_a[j]), float(nodes_a[j + 1])
            dq += dv * dt + 0.5 * a0 * dt * dt + (a1 - a0) * dt * dt / 6.0
            dv += 0.5 * (a0 + a1) * dt
        delta_v[i], delta_q[i] = dv, dq
    return RadarIntervalPreintegration(duration, delta_v, delta_q, valid)
