"""Causal geometry-beta matching used by the conditional correction branch.

The AoA geometry value remains the default.  The ADXL branch only supplies a
per-target beta when a causal matched displacement fit is both observable and
in disagreement with the geometry estimate.  Every operation below is
prefix-causal: the filters are one-sided and the least-squares terms are
prefix sums.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import AlgorithmConfig
from .types import AccelerationInput, RadarInput


@dataclass(frozen=True)
class BetaCorrection:
    matched_beta: np.ndarray
    ready: np.ndarray
    excitation_m: np.ndarray
    discrepancy: np.ndarray
    snr_db: np.ndarray
    trigger: np.ndarray
    used_beta: np.ndarray


def _lfilter(b: np.ndarray, a: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Small causal IIR filter for rows of a target-by-time array."""

    x = np.asarray(values, dtype=float)
    was_vector = x.ndim == 1
    if was_vector:
        x = x[None, :]
    if x.ndim != 2:
        raise ValueError("filter input must be one or two dimensional")
    b = np.asarray(b, dtype=float) / float(a[0])
    a = np.asarray(a, dtype=float) / float(a[0])
    y = np.zeros_like(x)
    for k in range(x.shape[1]):
        y[:, k] = b[0] * x[:, k]
        for j in range(1, min(k + 1, b.size)):
            y[:, k] += b[j] * x[:, k - j]
        for j in range(1, min(k + 1, a.size)):
            y[:, k] -= a[j] * y[:, k - j]
    return y[0] if was_vector else y


def _causal_fill(values: np.ndarray) -> np.ndarray:
    """Hold the last valid value; never fill a gap from a future sample."""

    x = np.asarray(values, dtype=float)
    output = np.zeros_like(x)
    last = 0.0
    seen = False
    for k, value in enumerate(x):
        if np.isfinite(value):
            last = float(value)
            seen = True
        output[k] = last if seen else 0.0
    return output


def _rolling_rms(values: np.ndarray, window: int) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    window = max(int(window), 1)
    squared = x * x
    cumulative = np.r_[0.0, np.cumsum(squared)]
    end = np.arange(1, x.size + 1)
    start = np.maximum(end - window, 0)
    return np.sqrt((cumulative[end] - cumulative[start]) / (end - start))


def _matched_displacement(
    radar_los_m: np.ndarray,
    acceleration_mps2: np.ndarray,
    sample_rate_hz: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Match q and q'' through the same causal band-limited transfer path."""

    k = 2.0 * float(sample_rate_hz)
    wh = 2.0 * np.pi * 3.0
    wl = 2.0 * np.pi * 100.0
    hp_b = np.array([k, -k]) / (k + wh)
    hp_a = np.array([1.0, (wh - k) / (wh + k)])
    int_b = np.ones(2) / (k + wh)
    lp_b = np.array([wl, wl]) / (k + wl)
    lp_a = np.array([1.0, (wl - k) / (wl + k)])

    radar = np.asarray(radar_los_m, dtype=float)
    accel = np.asarray(acceleration_mps2, dtype=float)
    filtered_radar = radar.copy()
    filtered_accel = accel.copy()
    for _ in range(3):
        filtered_radar = _lfilter(hp_b, hp_a, filtered_radar)
    for _ in range(2):
        filtered_accel = _lfilter(int_b, hp_a, filtered_accel)
    filtered_accel = _lfilter(hp_b, hp_a, filtered_accel)
    for _ in range(2):
        filtered_radar = _lfilter(lp_b, lp_a, filtered_radar)
        filtered_accel = _lfilter(lp_b, lp_a, filtered_accel)
    return filtered_radar, filtered_accel


def conditional_beta_correction(
    radar: RadarInput,
    acceleration: AccelerationInput,
    los_phase_rad: np.ndarray,
    config: AlgorithmConfig,
) -> BetaCorrection:
    """Estimate a causal ADXL beta and gate it against AoA geometry.

    The matched fit is deliberately conservative.  ``ready`` means a target
    has accumulated enough excited samples for a positive least-squares slope;
    it does not itself authorize a correction.  The global trigger additionally
    requires sufficient measured range-FFT SNR, current ADXL excitation, and at
    least the configured number of targets whose beta differs from AoA by the
    configured relative amount.
    """

    targets, samples = los_phase_rad.shape
    aoa_beta = np.asarray(radar.measured_beta, dtype=float)
    radar_time_ns = np.asarray(radar.extra["radar_time_ns"], dtype=np.int64)
    native_time_ns = np.asarray(acceleration.native_time_ns, dtype=np.int64)
    if radar_time_ns.size != samples:
        raise ValueError("radar time axis does not match phase samples")
    if native_time_ns.size < 2:
        matched = np.broadcast_to(aoa_beta[:, None], (targets, samples)).copy()
        false = np.zeros_like(matched, dtype=bool)
        return BetaCorrection(matched, false, np.zeros(samples), np.zeros_like(matched),
                              np.full(targets, np.nan), np.zeros(samples, dtype=bool), matched)

    # Both clocks are monotonic-clock timestamps.  A full native ADXL period
    # is retained as a causal interpolation margin; the calibrated digital
    # group delay is applied in the same direction.
    t0 = int(native_time_ns[0])
    radar_t = (radar_time_ns - t0).astype(float) * 1.0e-9
    native_t = (native_time_ns - t0).astype(float) * 1.0e-9
    adxl_period = float(np.max(np.diff(native_t)))
    group_delay = float(radar.extra.get("adxl_group_delay_s", 0.0))
    delayed_t = radar_t - adxl_period
    acceleration_stream = np.asarray(acceleration.native_mps2, dtype=float)
    if acceleration_stream.ndim == 2:
        acceleration_stream = acceleration_stream[:, 0]
    acceleration_stream = _causal_fill(acceleration_stream)
    aligned_acceleration = np.interp(delayed_t, native_t, acceleration_stream)

    # The delayed radar samples are queried only from the causal held phase.
    aligned_los = np.empty((targets, samples), dtype=float)
    query_t = radar_t - adxl_period - group_delay
    for i in range(targets):
        aligned_los[i] = np.interp(query_t, radar_t, _causal_fill(los_phase_rad[i]))
    filtered_radar, filtered_acceleration = _matched_displacement(
        aligned_los * config.wavelength_m() / (4.0 * np.pi),
        aligned_acceleration,
        config.sample_rate_hz,
    )

    excitation = np.abs(filtered_acceleration)
    usable = excitation >= float(config.beta_adxl_excitation_min_m)
    count = np.cumsum(usable, dtype=int)
    sxx = np.cumsum(filtered_radar * filtered_radar * usable, axis=1)
    sxy = np.cumsum(filtered_radar * filtered_acceleration[None, :] * usable, axis=1)
    matched = np.divide(
        sxy,
        sxx,
        out=np.zeros_like(sxy),
        where=sxx > float(config.beta_match_min_sxx),
    )
    ready = (
        (count[None, :] >= int(np.ceil(config.beta_adxl_excitation_duration_s * config.sample_rate_hz)))
        & (sxx > float(config.beta_match_min_sxx))
        & np.isfinite(matched)
        & (matched > 0.0)
    )
    # The slope is a dimensionless correction to the LOS phase displacement.
    # Clip only numerical outliers; the gate below still requires a meaningful
    # disagreement with AoA.
    matched = np.clip(matched, config.beta_min, config.beta_max)
    discrepancy = np.abs(matched / np.maximum(aoa_beta[:, None], 1.0e-12) - 1.0)

    snr = np.asarray(radar.extra.get("range_fft_snr_db", np.full(targets, np.nan)), dtype=float)
    if snr.size != targets:
        snr = np.full(targets, np.nan)
    selected = np.asarray(radar.selected_indices, dtype=int)
    selected = selected[(selected >= 0) & (selected < targets)]
    if selected.size and np.all(np.isfinite(snr[selected])):
        snr_score = float(np.min(snr[selected]))
    else:
        snr_score = np.nan
    snr_ok = np.isfinite(snr_score) and snr_score >= float(config.beta_snr_min_db)
    recent_excitation = _rolling_rms(
        filtered_acceleration,
        int(np.ceil(config.beta_adxl_excitation_duration_s * config.sample_rate_hz)),
    )
    discrepant = ready & (discrepancy >= float(config.beta_discrepancy_min_relative))
    if selected.size:
        discrepant_count = np.sum(discrepant[selected], axis=0)
    else:
        discrepant_count = np.zeros(samples, dtype=int)
    trigger = (
        snr_ok
        & (recent_excitation >= float(config.beta_adxl_excitation_min_m))
        & (discrepant_count >= int(config.beta_min_discrepant_targets))
    )
    used_beta = np.broadcast_to(aoa_beta[:, None], (targets, samples)).copy()
    # Once the scene-level gate is open, use the matched slope for every
    # target with a valid fit.  The discrepancy count is the confidence test;
    # applying a mixed AoA/ADXL correction target by target would leave the
    # common structural update internally inconsistent.
    selected_mask = np.zeros(targets, dtype=bool)
    selected_mask[selected] = True
    use_match = trigger[None, :] & ready & selected_mask[:, None]
    used_beta[use_match] = matched[use_match]
    return BetaCorrection(
        matched_beta=matched,
        ready=ready,
        excitation_m=recent_excitation,
        discrepancy=discrepancy,
        snr_db=snr,
        trigger=trigger,
        used_beta=used_beta,
    )
