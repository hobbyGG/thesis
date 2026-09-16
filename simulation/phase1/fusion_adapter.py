"""Time-preserving acceleration preintegration for asynchronous radar fusion.

The adapter deliberately keeps the radar and accelerometer clocks on their
native sample grids.  It only derives acceleration increments over each radar
interval; it does not manufacture paired samples with nearest-neighbour
matching.
"""

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np


class FusionAdapterError(ValueError):
    """Raised when fusion inputs violate the adapter data contract."""


class FusionCoverageError(RuntimeError):
    """Raised when a radar interval cannot be integrated safely."""

    def __init__(self, invalid_interval_indices: Iterable[int]):
        self.invalid_interval_indices = tuple(int(index) for index in invalid_interval_indices)
        joined = ", ".join(str(index) for index in self.invalid_interval_indices)
        super().__init__(f"ADXL coverage failed for radar interval(s): {joined}")


def _readonly(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class RadarIntervalPreintegration:
    """Acceleration increments and quality for consecutive radar timestamps.

    ``source_indices[i]`` contains the original ADXL indices used to bracket
    and integrate radar interval ``i``.  Bracketing samples may lie just
    outside the radar interval.  An empty tuple means the interval could not
    be bracketed; a non-empty tuple may still be rejected by the gap limit.

    For a valid interval with duration ``dt``, a constant-acceleration state
    model consumes the outputs as::

        v_next = v + delta_v_mps[i]
        q_next = q + v * dt + delta_q_m[i]

    ``delta_q_m`` is the acceleration-only term
    ``integral[(t_end - t) * a(t)] dt`` over the radar interval.  Piecewise-linear interpolation is
    used only between valid, timestamped ADXL samples that bracket the whole
    radar interval.
    """

    radar_start_time_ns: np.ndarray
    radar_end_time_ns: np.ndarray
    duration_s: np.ndarray
    source_indices: Tuple[Tuple[int, ...], ...]
    source_sample_count: np.ndarray
    coverage_fraction: np.ndarray
    coverage_complete: np.ndarray
    max_observed_gap_ns: np.ndarray
    gap_within_limit: np.ndarray
    interval_valid: np.ndarray
    delta_v_mps: np.ndarray
    delta_q_m: np.ndarray
    max_allowed_gap_ns: int

    def require_all_valid(self) -> "RadarIntervalPreintegration":
        """Return this result, or raise before a caller can use bad intervals."""

        invalid = np.flatnonzero(~self.interval_valid)
        if invalid.size:
            raise FusionCoverageError(invalid)
        return self


def _int64_timestamps(name: str, values: Iterable[int], minimum_size: int) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1:
        raise FusionAdapterError(f"{name} must be one-dimensional")
    if raw.dtype.kind not in "iu" or raw.dtype.kind == "b":
        raise FusionAdapterError(f"{name} must contain integer nanoseconds")
    timestamps = np.array(raw, dtype=np.int64, copy=True)
    if timestamps.size < minimum_size:
        raise FusionAdapterError(f"{name} must contain at least {minimum_size} timestamp(s)")
    if np.any(timestamps[1:] <= timestamps[:-1]):
        raise FusionAdapterError(f"{name} must be strictly increasing")
    return timestamps


def _validate_inputs(
    radar_time_ns: Iterable[int],
    adxl_time_ns: Iterable[int],
    acceleration_mps2: Iterable[float],
    valid_mask: Iterable[bool],
    max_allowed_gap_ns: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    radar = _int64_timestamps("radar_time_ns", radar_time_ns, minimum_size=2)
    adxl = _int64_timestamps("adxl_time_ns", adxl_time_ns, minimum_size=1)

    acceleration = np.array(acceleration_mps2, dtype=float, copy=True)
    if acceleration.ndim != 1 or acceleration.shape != adxl.shape:
        raise FusionAdapterError("acceleration_mps2 must be one-dimensional and match adxl_time_ns")

    mask = np.asarray(valid_mask)
    if mask.ndim != 1 or mask.shape != adxl.shape or mask.dtype.kind != "b":
        raise FusionAdapterError("valid_mask must be a boolean vector matching adxl_time_ns")
    mask = np.array(mask, dtype=bool, copy=True)
    if np.any(~np.isfinite(acceleration[mask])):
        raise FusionAdapterError("valid acceleration samples must be finite")

    if isinstance(max_allowed_gap_ns, (bool, np.bool_)) or not isinstance(
        max_allowed_gap_ns, (int, np.integer)
    ):
        raise FusionAdapterError("max_allowed_gap_ns must be a positive integer")
    gap_limit = int(max_allowed_gap_ns)
    if gap_limit <= 0:
        raise FusionAdapterError("max_allowed_gap_ns must be a positive integer")

    return radar, adxl, acceleration, mask, gap_limit


def _interpolate_at(
    timestamp_ns: int,
    valid_time_ns: np.ndarray,
    valid_acceleration_mps2: np.ndarray,
) -> float:
    right = int(np.searchsorted(valid_time_ns, timestamp_ns, side="left"))
    if right < valid_time_ns.size and int(valid_time_ns[right]) == timestamp_ns:
        return float(valid_acceleration_mps2[right])

    left = right - 1
    if left < 0 or right >= valid_time_ns.size:
        raise FusionAdapterError("internal interpolation attempted without timestamp bracketing")
    span_ns = int(valid_time_ns[right]) - int(valid_time_ns[left])
    offset_ns = timestamp_ns - int(valid_time_ns[left])
    fraction = float(offset_ns) / float(span_ns)
    return float(
        valid_acceleration_mps2[left]
        + fraction * (valid_acceleration_mps2[right] - valid_acceleration_mps2[left])
    )


def _piecewise_linear_preintegration(
    node_time_ns: np.ndarray,
    node_acceleration_mps2: np.ndarray,
) -> Tuple[float, float]:
    delta_v_mps = 0.0
    delta_q_m = 0.0
    for index in range(node_time_ns.size - 1):
        step_s = float(int(node_time_ns[index + 1]) - int(node_time_ns[index])) * 1.0e-9
        acceleration_start = float(node_acceleration_mps2[index])
        acceleration_end = float(node_acceleration_mps2[index + 1])

        # Exact integration for linearly varying acceleration over this step.
        delta_q_m += (
            delta_v_mps * step_s
            + 0.5 * acceleration_start * step_s**2
            + (acceleration_end - acceleration_start) * step_s**2 / 6.0
        )
        delta_v_mps += 0.5 * (acceleration_start + acceleration_end) * step_s
    return delta_v_mps, delta_q_m


def preintegrate_acceleration_to_radar(
    radar_time_ns: Iterable[int],
    adxl_time_ns: Iterable[int],
    acceleration_mps2: Iterable[float],
    valid_mask: Iterable[bool],
    *,
    max_allowed_gap_ns: int,
    fail_on_invalid_interval: bool = True,
) -> RadarIntervalPreintegration:
    """Preintegrate native-rate ADXL data over consecutive radar intervals.

    Inputs are copied and never modified.  Both timestamp arrays must contain
    integer nanoseconds and be strictly increasing.  A radar interval is valid
    only when valid ADXL samples bracket both boundaries and every contributing
    ADXL gap is no greater than ``max_allowed_gap_ns``.

    Invalid intervals never receive a numeric increment: their ``delta_v_mps``
    and ``delta_q_m`` entries remain NaN.  By default the function additionally
    raises :class:`FusionCoverageError` if any interval is invalid.  Set
    ``fail_on_invalid_interval=False`` only when inspecting quality diagnostics.
    """

    radar, adxl, acceleration, mask, gap_limit = _validate_inputs(
        radar_time_ns,
        adxl_time_ns,
        acceleration_mps2,
        valid_mask,
        max_allowed_gap_ns,
    )
    if not isinstance(fail_on_invalid_interval, (bool, np.bool_)):
        raise FusionAdapterError("fail_on_invalid_interval must be boolean")

    valid_indices = np.flatnonzero(mask)
    valid_time_ns = adxl[valid_indices]
    valid_acceleration_mps2 = acceleration[valid_indices]

    starts = radar[:-1].copy()
    ends = radar[1:].copy()
    interval_count = starts.size
    duration_s = (ends - starts).astype(float) * 1.0e-9
    source_indices = []
    source_sample_count = np.zeros(interval_count, dtype=np.int64)
    coverage_fraction = np.zeros(interval_count, dtype=float)
    coverage_complete = np.zeros(interval_count, dtype=bool)
    max_observed_gap_ns = np.full(interval_count, -1, dtype=np.int64)
    gap_within_limit = np.zeros(interval_count, dtype=bool)
    interval_valid = np.zeros(interval_count, dtype=bool)
    delta_v_mps = np.full(interval_count, np.nan, dtype=float)
    delta_q_m = np.full(interval_count, np.nan, dtype=float)

    for interval_index, (start_raw, end_raw) in enumerate(zip(starts, ends)):
        start_ns = int(start_raw)
        end_ns = int(end_raw)

        if valid_time_ns.size:
            overlap_start_ns = max(start_ns, int(valid_time_ns[0]))
            overlap_end_ns = min(end_ns, int(valid_time_ns[-1]))
            covered_ns = max(0, overlap_end_ns - overlap_start_ns)
            coverage_fraction[interval_index] = float(covered_ns) / float(end_ns - start_ns)

        left_position = int(np.searchsorted(valid_time_ns, start_ns, side="right")) - 1
        right_position = int(np.searchsorted(valid_time_ns, end_ns, side="left"))
        fully_bracketed = left_position >= 0 and right_position < valid_time_ns.size
        coverage_complete[interval_index] = fully_bracketed
        if not fully_bracketed:
            source_indices.append(())
            continue

        selected_positions = np.arange(left_position, right_position + 1, dtype=np.int64)
        selected_source_indices = tuple(int(index) for index in valid_indices[selected_positions])
        source_indices.append(selected_source_indices)
        source_sample_count[interval_index] = len(selected_source_indices)

        contributing_times = valid_time_ns[selected_positions]
        observed_gaps = np.diff(contributing_times)
        if observed_gaps.size == 0:
            # A positive-duration interval cannot be bracketed by one timestamp,
            # but keep the quality path explicit if the contract changes later.
            continue
        observed_gap_ns = int(np.max(observed_gaps))
        max_observed_gap_ns[interval_index] = observed_gap_ns
        gap_within_limit[interval_index] = observed_gap_ns <= gap_limit
        if not gap_within_limit[interval_index]:
            continue

        internal = (contributing_times > start_ns) & (contributing_times < end_ns)
        internal_times = contributing_times[internal]
        internal_acceleration = valid_acceleration_mps2[selected_positions][internal]
        node_time_ns = np.concatenate(
            (
                np.array([start_ns], dtype=np.int64),
                internal_times,
                np.array([end_ns], dtype=np.int64),
            )
        )
        node_acceleration_mps2 = np.concatenate(
            (
                np.array(
                    [_interpolate_at(start_ns, valid_time_ns, valid_acceleration_mps2)],
                    dtype=float,
                ),
                internal_acceleration,
                np.array(
                    [_interpolate_at(end_ns, valid_time_ns, valid_acceleration_mps2)],
                    dtype=float,
                ),
            )
        )
        delta_v_mps[interval_index], delta_q_m[interval_index] = _piecewise_linear_preintegration(
            node_time_ns,
            node_acceleration_mps2,
        )
        interval_valid[interval_index] = True

    result = RadarIntervalPreintegration(
        radar_start_time_ns=_readonly(starts),
        radar_end_time_ns=_readonly(ends),
        duration_s=_readonly(duration_s),
        source_indices=tuple(source_indices),
        source_sample_count=_readonly(source_sample_count),
        coverage_fraction=_readonly(coverage_fraction),
        coverage_complete=_readonly(coverage_complete),
        max_observed_gap_ns=_readonly(max_observed_gap_ns),
        gap_within_limit=_readonly(gap_within_limit),
        interval_valid=_readonly(interval_valid),
        delta_v_mps=_readonly(delta_v_mps),
        delta_q_m=_readonly(delta_q_m),
        max_allowed_gap_ns=gap_limit,
    )
    if bool(fail_on_invalid_interval):
        result.require_all_valid()
    return result


__all__ = (
    "FusionAdapterError",
    "FusionCoverageError",
    "RadarIntervalPreintegration",
    "preintegrate_acceleration_to_radar",
)
