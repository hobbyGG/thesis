from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class DetectedPeak:
    range_bin: int
    angle_bin: int
    angle_deg: float
    value: float


@dataclass(frozen=True)
class MergedPeak:
    range_bin: float
    angle_bin: float
    angle_deg: float
    value: float
    peak_count: int
    member_peaks: Tuple[DetectedPeak, ...]


@dataclass(frozen=True)
class TargetTrack:
    target_index: int
    presence: float
    snr_est_db: float
    band_energy_ratio: float
    measured_beta: float
    score: float


@dataclass(frozen=True)
class SelectionDiagnostics:
    tracks: Tuple[TargetTrack, ...]
    rejected_reasons: Dict[int, Tuple[str, ...]]


@dataclass(frozen=True)
class SelectedTargetSet:
    selected_indices: np.ndarray
    quality_score: np.ndarray
    initial_r: np.ndarray
    calibration_indices: np.ndarray
    calibration_initial_r: np.ndarray
    diagnostics: SelectionDiagnostics


def detect_peaks_2d(frame, angle_axis_deg, threshold_scale=6.0):
    arr = np.asarray(frame, dtype=float)
    angle_axis = np.asarray(angle_axis_deg, dtype=float)
    if arr.ndim != 2:
        raise ValueError("frame must be a 2D range-angle magnitude map")
    if angle_axis.size != arr.shape[1]:
        raise ValueError("angle_axis_deg must match the angle axis of frame")

    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    threshold = median + float(threshold_scale) * mad
    peaks = []
    for range_bin in range(arr.shape[0]):
        for angle_bin in range(arr.shape[1]):
            value = float(arr[range_bin, angle_bin])
            if value < threshold:
                continue
            r0 = max(0, range_bin - 1)
            r1 = min(arr.shape[0], range_bin + 2)
            a0 = max(0, angle_bin - 1)
            a1 = min(arr.shape[1], angle_bin + 2)
            neighborhood = arr[r0:r1, a0:a1]
            if value >= float(np.max(neighborhood)):
                peaks.append(
                    DetectedPeak(
                        range_bin=int(range_bin),
                        angle_bin=int(angle_bin),
                        angle_deg=float(angle_axis[angle_bin]),
                        value=value,
                    )
                )
    return peaks


def merge_close_angle_peaks(peaks, range_tolerance_bins=1, angle_threshold_deg=15.0):
    remaining = list(peaks)
    merged = []
    while remaining:
        cluster = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            keep = []
            for candidate in remaining:
                if any(
                    abs(candidate.range_bin - member.range_bin) <= int(range_tolerance_bins)
                    and abs(candidate.angle_deg - member.angle_deg) < float(angle_threshold_deg)
                    for member in cluster
                ):
                    cluster.append(candidate)
                    changed = True
                else:
                    keep.append(candidate)
            remaining = keep
        weights = np.asarray([max(member.value, 1e-12) for member in cluster], dtype=float)
        range_bins = np.asarray([member.range_bin for member in cluster], dtype=float)
        angle_bins = np.asarray([member.angle_bin for member in cluster], dtype=float)
        angle_deg = np.asarray([member.angle_deg for member in cluster], dtype=float)
        merged.append(
            MergedPeak(
                range_bin=float(np.average(range_bins, weights=weights)),
                angle_bin=float(np.average(angle_bins, weights=weights)),
                angle_deg=float(np.average(angle_deg, weights=weights)),
                value=float(np.sum(weights)),
                peak_count=len(cluster),
                member_peaks=tuple(cluster),
            )
        )
    return merged


def select_targets_from_measurements(
    iq,
    wrapped_phase_rad,
    available_mask,
    measured_beta,
    measured_acceleration_mps2,
    sample_rate_hz,
    initial_measurement_variance=9.0,
    min_measurement_variance=1.0e-4,
    max_measurement_variance=25.0,
    min_presence=0.70,
    min_band_energy_ratio=0.50,
    min_snr_db=8.0,
    min_projection_abs=0.45,
    max_targets=None,
    min_score=0.25,
    min_selected_targets=0,
    hard_band_consistency=False,
    calibration_min_projection_abs=0.35,
):
    iq_arr = np.asarray(iq, dtype=complex)
    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    available = np.asarray(available_mask, dtype=bool)
    beta = np.asarray(measured_beta, dtype=float)
    accel = np.asarray(measured_acceleration_mps2, dtype=float)
    if iq_arr.ndim != 2:
        raise ValueError("iq must have shape (num_targets, num_samples)")
    if wrapped.shape != iq_arr.shape or available.shape != iq_arr.shape:
        raise ValueError("wrapped_phase_rad and available_mask must match iq shape")
    if beta.shape != (iq_arr.shape[0],):
        raise ValueError("measured_beta must have one value per target")

    tracks = []
    reasons_by_target = {}
    for target_idx in range(iq_arr.shape[0]):
        valid = available[target_idx] & np.isfinite(wrapped[target_idx]) & np.isfinite(iq_arr[target_idx].real)
        presence = float(np.count_nonzero(valid) / max(1, iq_arr.shape[1]))
        snr_est, band_ratio = _best_window_quality(iq_arr[target_idx], valid, accel, float(sample_rate_hz))
        projection_abs = _projection_abs_from_beta(beta[target_idx])
        score = _selection_score(
            presence,
            band_ratio,
            snr_est,
            projection_abs,
            min_snr_db,
            min_projection_abs,
        )
        reasons = []
        if presence < float(min_presence):
            reasons.append("low_presence")
        if band_ratio < float(min_band_energy_ratio):
            reasons.append("low_band_consistency")
        if snr_est < float(min_snr_db):
            reasons.append("low_snr")
        if projection_abs < float(min_projection_abs):
            reasons.append("low_geometry_projection")
        tracks.append(
            TargetTrack(
                target_index=int(target_idx),
                presence=presence,
                snr_est_db=snr_est,
                band_energy_ratio=band_ratio,
                measured_beta=float(beta[target_idx]),
                score=score,
            )
        )
        reasons_by_target[target_idx] = tuple(reasons)

    del min_score, min_selected_targets
    hard_reasons = {"low_presence", "low_snr", "low_geometry_projection"}
    if hard_band_consistency:
        hard_reasons.add("low_band_consistency")
    candidates = [
        track
        for track in tracks
        if not hard_reasons.intersection(reasons_by_target[track.target_index])
    ]
    candidates.sort(key=lambda track: (-track.score, track.target_index))
    if max_targets is None:
        accepted = list(candidates)
    else:
        accepted = list(candidates[: max(0, int(max_targets))])
    has_intermittent_target = any("low_presence" in reasons for reasons in reasons_by_target.values())
    if has_intermittent_target and len(accepted) < 3 and len(tracks) >= 3:
        accepted_ids = {track.target_index for track in accepted}
        soft_candidates = [
            track
            for track in tracks
            if track.target_index not in accepted_ids
            and not hard_reasons.intersection(reasons_by_target[track.target_index])
        ]
        soft_candidates.sort(
            key=lambda track: (-track.snr_est_db, -_projection_abs_from_beta(track.measured_beta), track.target_index)
        )
        for track in soft_candidates:
            accepted.append(track)
            accepted_ids.add(track.target_index)
            target_count = 3 if max_targets is None else min(3, int(max_targets))
            if len(accepted) >= target_count:
                break
    accepted_ids = {track.target_index for track in accepted}
    rejected = {
        target_idx: reasons
        for target_idx, reasons in reasons_by_target.items()
        if target_idx not in accepted_ids and reasons
    }
    selected_indices = np.asarray([track.target_index for track in accepted], dtype=int)
    quality_score = np.asarray([track.score for track in accepted], dtype=float)
    initial_r = np.full(iq_arr.shape[0], float(max_measurement_variance), dtype=float)
    track_initial_r = np.full(iq_arr.shape[0], float(max_measurement_variance), dtype=float)
    for track in tracks:
        track_initial_r[track.target_index] = float(
            _initial_r_from_snr_quality(
                snr_db=track.snr_est_db,
                presence=track.presence,
                band_ratio=track.band_energy_ratio,
                projection_abs=_projection_abs_from_beta(track.measured_beta),
                min_band_energy_ratio=min_band_energy_ratio,
                min_projection_abs=min_projection_abs,
                min_measurement_variance=min_measurement_variance,
                max_measurement_variance=max_measurement_variance,
            )
        )
    for track in accepted:
        initial_r[track.target_index] = track_initial_r[track.target_index]

    calibration_candidates = [
        track
        for track in tracks
        if "low_presence" not in reasons_by_target[track.target_index]
        and "low_snr" not in reasons_by_target[track.target_index]
        and _projection_abs_from_beta(track.measured_beta) >= float(calibration_min_projection_abs)
        and (not hard_band_consistency or "low_band_consistency" not in reasons_by_target[track.target_index])
    ]
    calibration_candidates.sort(key=lambda track: (-track.score, track.target_index))
    calibration_indices = np.asarray([track.target_index for track in calibration_candidates], dtype=int)
    calibration_initial_r = np.full(iq_arr.shape[0], float(max_measurement_variance), dtype=float)
    for track in calibration_candidates:
        calibration_initial_r[track.target_index] = track_initial_r[track.target_index]
    return SelectedTargetSet(
        selected_indices=selected_indices,
        quality_score=quality_score,
        initial_r=initial_r,
        calibration_indices=calibration_indices,
        calibration_initial_r=calibration_initial_r,
        diagnostics=SelectionDiagnostics(tracks=tuple(tracks), rejected_reasons=rejected),
    )


def _estimate_snr_db(series, valid):
    values = np.asarray(series, dtype=complex)
    mask = np.asarray(valid, dtype=bool)
    if np.count_nonzero(mask) < 4:
        return float("-inf")
    amp = np.abs(values[mask])
    signal = float(np.nanmedian(amp))
    noise = float(1.4826 * np.nanmedian(np.abs(amp - signal)))
    if noise <= 1e-12:
        noise = float(np.nanstd(amp))
    if noise <= 1e-12:
        return 80.0
    return float(20.0 * np.log10(max(signal, 1e-12) / noise))


def _best_window_quality(series, valid, accel, sample_rate_hz):
    values = np.asarray(series, dtype=complex)
    mask = np.asarray(valid, dtype=bool)
    n_samples = values.size
    if n_samples == 0:
        return float("-inf"), 0.0
    window = min(n_samples, max(256, n_samples // 4))
    step = max(1, window // 2)
    best_band = -1.0
    best_snr = float("-inf")
    for start in range(0, n_samples - window + 1, step):
        stop = start + window
        window_valid = mask[start:stop]
        if np.count_nonzero(window_valid) < max(8, window // 4):
            continue
        band = _band_energy_ratio(values[start:stop], window_valid, accel[start:stop], sample_rate_hz)
        snr = _estimate_snr_db(values[start:stop], window_valid)
        if band > best_band:
            best_band = band
            best_snr = snr
    if best_band < 0.0:
        return _estimate_snr_db(values, mask), _band_energy_ratio(values, mask, accel, sample_rate_hz)
    return float(best_snr), float(best_band)


def _band_energy_ratio(series, valid, accel, sample_rate_hz):
    values = np.asarray(series, dtype=complex)
    mask = np.asarray(valid, dtype=bool)
    if np.count_nonzero(mask) < 8:
        return 0.0
    if accel.size != values.size:
        count = min(accel.size, values.size)
        accel_use = accel[:count]
        values_use = values[:count]
        mask_use = mask[:count]
    else:
        accel_use = accel
        values_use = values
        mask_use = mask
    values_centered = np.zeros_like(values_use, dtype=complex)
    values_centered[mask_use] = values_use[mask_use] - np.nanmean(values_use[mask_use])
    accel_centered = np.asarray(accel_use, dtype=float) - float(np.nanmean(accel_use))
    freqs = np.fft.rfftfreq(values_centered.size, d=1.0 / float(sample_rate_hz))
    if freqs.size <= 1:
        return 0.0
    accel_power = np.abs(np.fft.rfft(accel_centered)) ** 2
    accel_power[0] = 0.0
    positive = np.flatnonzero(freqs > 0.0)
    if positive.size == 0:
        return 0.0
    target_power = np.abs(np.fft.rfft(values_centered.real)) ** 2 + np.abs(np.fft.rfft(values_centered.imag)) ** 2
    target_power[0] = 0.0
    max_accel_power = float(np.max(accel_power[positive]))
    if max_accel_power <= 0.0:
        return 0.0
    strongest = positive[accel_power[positive] >= 0.01 * max_accel_power]
    if strongest.size == 0:
        strongest = positive[np.argsort(accel_power[positive])[-1:]]
    structure_band = np.zeros_like(freqs, dtype=bool)
    structure_band[strongest] = True
    valid_band = freqs > 0.0
    denom = float(np.sum(target_power[valid_band]))
    if denom <= 1e-18:
        return 0.0
    raw_ratio = float(np.sum(target_power[structure_band]) / denom)
    return float(np.sqrt(np.clip(raw_ratio, 0.0, 1.0)))


def _projection_abs_from_beta(beta) -> float:
    beta_abs = abs(float(beta))
    if not np.isfinite(beta_abs) or beta_abs <= 1.0e-12:
        return 0.0
    return float(1.0 / beta_abs)


def _selection_score(presence, band_ratio, snr_db, projection_abs, min_snr_db, min_projection_abs):
    band_score = np.clip((float(band_ratio) - 0.5) / 0.4, 0.0, 1.0)
    snr_score = np.clip((float(snr_db) - float(min_snr_db)) / 10.0, 0.0, 1.0)
    projection_score = np.clip((float(projection_abs) - float(min_projection_abs)) / 0.35, 0.0, 1.0)
    return float(float(presence) * band_score * snr_score * projection_score)


def _initial_r_from_snr_quality(
    snr_db,
    presence,
    band_ratio,
    projection_abs,
    min_band_energy_ratio,
    min_projection_abs,
    min_measurement_variance,
    max_measurement_variance,
):
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    if not np.isfinite(snr_linear) or snr_linear <= 0.0:
        return float(max_measurement_variance)

    r_snr = 1.0 / (2.0 * snr_linear)
    presence_factor = 1.0 / max(float(presence), 1.0e-3)
    geometry_floor = max(float(min_projection_abs), 1.0e-3)
    geometry_factor = max(1.0, 1.0 / max(float(projection_abs), geometry_floor) ** 2)
    band_reference = max(float(min_band_energy_ratio), 1.0e-3)
    band_deficit = max(0.0, band_reference - float(band_ratio))
    band_factor = 1.0 + band_deficit / band_reference
    return float(
        np.clip(
            r_snr * presence_factor * geometry_factor * band_factor,
            float(min_measurement_variance),
            float(max_measurement_variance),
        )
    )
