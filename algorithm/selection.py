import numpy as np


def detect_target_bins(range_angle_cube: np.ndarray, angle_axis_deg: np.ndarray, *, dynamic_range_db: float = 20.0, max_candidates: int = 12):
    representative = np.nanmedian(np.abs(range_angle_cube), axis=0)
    threshold = np.median(representative) + 6.0 * np.median(np.abs(representative - np.median(representative)))
    peaks = []
    for r, a in zip(*np.where(representative >= threshold)):
        r0, r1 = max(0, r - 1), min(representative.shape[0], r + 2)
        a0, a1 = max(0, a - 1), min(representative.shape[1], a + 2)
        if representative[r, a] >= np.max(representative[r0:r1, a0:a1]):
            peaks.append((float(representative[r, a]), int(r), int(a)))
    peaks.sort(reverse=True)
    if not peaks:
        raise RuntimeError("no range-angle target was detected")
    merged = []
    for peak in peaks:
        if any(abs(peak[1] - kept[1]) <= 1 and abs(float(angle_axis_deg[peak[2]]) - float(angle_axis_deg[kept[2]])) < 15.0 for kept in merged):
            continue
        merged.append(peak)
    peaks = merged
    strongest = peaks[0][0]
    floor = strongest * 10.0 ** (-dynamic_range_db / 20.0)
    retained = [peak for peak in peaks if peak[0] >= floor][:max_candidates]
    return (
        np.asarray([item[1] for item in retained], dtype=int),
        np.asarray([item[2] for item in retained], dtype=int),
        {"candidate_count": len(retained), "strongest_magnitude": float(strongest)},
    )


def select_targets(targets):
    quality = np.mean(targets.available_mask, axis=1)
    selected = np.flatnonzero(quality > 0.5)
    scores = np.asarray(quality, dtype=float)
    initial_r = np.full(targets.measured_beta.shape, 9.0, dtype=float)
    return selected, initial_r, scores
