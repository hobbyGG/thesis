#!/usr/bin/env python3
"""Mechanism experiment: same-range split-vs-merge range-angle IQ processing.

This is a simplified ULA IQ model, not a full FMCW/radar or real-data validation.
The estimator sees only array IQ and declared instrument/model constants; simulation
truth is used only by the generator and evaluator.
"""
from __future__ import annotations
import argparse, json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from scipy.signal import find_peaks

OUT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Case:
    name: str
    angles_deg: Tuple[float, ...]
    amplitudes: Tuple[float, ...]
    static_phase_rad: Tuple[float, ...]
    q_amp_mm: float
    q_second_amp_mm: float
    snr_db: float
    n_sources: int
    expected_route: str
    note: str

# Predeclared development cases. The estimator does not receive these values.
CASES = (
    Case("close_same_phase", (-4.0, 4.0), (1.0, 0.80), (0.15, -0.30),
         0.20, 0.05, 35.0, 2, "merge",
         "Close angles below the declared 12 deg peak-separation threshold; non-destructive mixture."),
    Case("separated_balanced", (-25.0, 25.0), (1.0, 0.90), (0.15, -0.30),
         0.40, 0.10, 35.0, 2, "split",
         "Separated same-range angles with comparable amplitudes."),
    Case("separated_unequal", (-18.0, 18.0), (1.0, 0.35), (0.15, -0.30),
         0.40, 0.10, 35.0, 2, "split",
         "Separated angles but a weak second scatterer; tests leakage/conditioning."),
    Case("close_destructive", (-4.0, 4.0), (1.0, 1.0), (0.0, np.pi),
         0.16, 0.04, 35.0, 2, "negative",
         "Negative case: close equal phasors initially cancel; unresolved mixture is not assumed equivalent."),
    Case("coincident_destructive", (0.0, 0.0), (1.0, 1.0), (0.0, np.pi),
         0.16, 0.04, 35.0, 2, "negative",
         "Limit case: exactly coincident opposite phasors cancel in every array channel; both routes should abstain."),
)

# Declared physical/processing constants.
LAMBDA_MM = 4.0
N_RX = 8
D_OVER_LAMBDA = 0.5
N_SLOW = 256
FS_HZ = 100.0
ANGLE_GRID_DEG = np.arange(-60.0, 60.0001, 0.25)
PEAK_MIN_SEP_DEG = 12.0
PEAK_MIN_RATIO = 0.18
PEAK_MAX = 2
AMP_FLOOR_MULT = 5.0


def steering(theta_deg: float) -> np.ndarray:
    m = np.arange(N_RX, dtype=float) - 0.5 * (N_RX - 1)
    return np.exp(1j * 2.0 * np.pi * D_OVER_LAMBDA * m * np.sin(np.deg2rad(theta_deg)))


def truth_waveform(case: Case, seed: int) -> np.ndarray:
    """Generator-only common structural motion; estimator never sees this."""
    rng = np.random.default_rng(seed)
    t = np.arange(N_SLOW) / FS_HZ
    # Seed phase makes the multi-seed run independent while preserving common motion.
    p = rng.uniform(-np.pi, np.pi)
    q = (case.q_amp_mm * np.sin(2 * np.pi * 3.0 * t + p)
         + case.q_second_amp_mm * np.sin(2 * np.pi * 5.0 * t + 0.43 - 0.2 * p))
    return q


def synthesize(case: Case, seed: int) -> Tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed + 7919)
    q = truth_waveform(case, seed)
    z = np.zeros((N_SLOW, N_RX), complex)
    for theta, amp, psi in zip(case.angles_deg, case.amplitudes, case.static_phase_rad):
        # Common q, target-dependent LOS projection cos(theta).
        temporal = np.exp(1j * (psi + 4.0 * np.pi * q * np.cos(np.deg2rad(theta)) / LAMBDA_MM))
        z += (amp * temporal)[:, None] * steering(theta)[None, :]
    # Noise is scaled from declared per-source amplitudes, rather than the
    # post-interference sum; otherwise a cancellation case would get an
    # artificially zero noise estimate.
    nominal_rms = float(np.sqrt(N_RX * np.sum(np.asarray(case.amplitudes) ** 2) / N_RX))
    noise_std = nominal_rms / (10.0 ** (case.snr_db / 20.0) * np.sqrt(2.0))
    noise = noise_std * (rng.standard_normal(z.shape) + 1j * rng.standard_normal(z.shape))
    return z + noise, q, float(noise_std)


def angle_spectrum(z: np.ndarray) -> np.ndarray:
    # Array-only Bartlett covariance spectrum. No case truth is used.
    R = (z.conj().T @ z) / z.shape[0]
    P = np.empty(ANGLE_GRID_DEG.size)
    for i, a in enumerate(ANGLE_GRID_DEG):
        v = steering(float(a))
        P[i] = float(np.real(np.vdot(v, R @ v)) / (N_RX * N_RX))
    return np.maximum(P, 0.0)


def detect_angles(z: np.ndarray) -> Tuple[List[float], np.ndarray]:
    P = angle_spectrum(z)
    distance = max(1, int(round(PEAK_MIN_SEP_DEG / (ANGLE_GRID_DEG[1] - ANGLE_GRID_DEG[0]))))
    peaks, props = find_peaks(P, distance=distance, prominence=max(np.max(P) * 0.01, 1e-12))
    if peaks.size == 0:
        return [], P
    order = peaks[np.argsort(P[peaks])[::-1]]
    selected = []
    for idx in order:
        if P[idx] < P[order[0]] * PEAK_MIN_RATIO:
            continue
        a = float(ANGLE_GRID_DEG[idx])
        if all(abs(a - b) >= PEAK_MIN_SEP_DEG for b in selected):
            selected.append(a)
        if len(selected) >= PEAK_MAX:
            break
    return selected, P


def beamform(z: np.ndarray, angle_deg: float) -> np.ndarray:
    v = steering(angle_deg)
    return z @ np.conj(v) / N_RX


def q_from_channel(y: np.ndarray, angle_deg: float, amp_floor: float) -> Tuple[np.ndarray | None, Dict[str, float]]:
    # Fixed sign/reference convention for every route: phase(y[k] y[0]*) and q-q[0].
    ref = y[0]
    amp = np.abs(y)
    quality = {
        "median_abs": float(np.median(amp)),
        "min_abs": float(np.min(amp)),
        "max_abs": float(np.max(amp)),
        "amp_floor": float(amp_floor),
    }
    if not np.all(np.isfinite(y)) or quality["min_abs"] < amp_floor:
        return None, quality
    phase = np.unwrap(np.angle(y * np.conj(ref)))
    c = np.cos(np.deg2rad(angle_deg))
    if c <= 0.05 or not np.isfinite(c):
        return None, quality
    qhat = phase * LAMBDA_MM / (4.0 * np.pi * c)
    if not np.all(np.isfinite(qhat)):
        return None, quality
    return qhat - qhat[0], quality


def evaluate(z: np.ndarray, noise_std: float, mode: str) -> Dict[str, object]:
    angles, P = detect_angles(z)
    if len(angles) >= 2:
        idx = [int(np.argmin(np.abs(ANGLE_GRID_DEG - a))) for a in angles[:2]]
        result_ratio = float(min(P[idx[0]], P[idx[1]]) / max(P[idx[0]], P[idx[1]]))
    else:
        result_ratio = None
    amp_floor = AMP_FLOOR_MULT * noise_std
    result: Dict[str, object] = {
        "mode": mode,
        "detected_angles_deg": angles,
        "detected_count": len(angles),
        "spectrum_peak_ratio_2nd": result_ratio,
        "coverage": False,
        "failure": None,
    }
    if mode == "split":
        if len(angles) < 2:
            result["failure"] = "fewer_than_two_array-only_angle_peaks"
            return result
        channels = []
        qhats = []
        qualities = []
        for a in angles[:2]:
            y = beamform(z, a)
            qhat, quality = q_from_channel(y, a, amp_floor)
            qualities.append(quality)
            if qhat is None:
                result["failure"] = "beamformed_channel_amplitude_or_geometry_guard"
                result["channel_quality"] = qualities
                return result
            channels.append(y)
            qhats.append(qhat)
        # Declared fusion: initial-magnitude-squared weights, fixed across slow time.
        w = np.array([np.abs(y[0]) ** 2 for y in channels], float)
        if not np.all(np.isfinite(w)) or np.sum(w) <= 0:
            result["failure"] = "invalid_fusion_weights"
            return result
        w /= np.sum(w)
        qhat = np.sum(np.vstack(qhats) * w[:, None], axis=0)
        result.update({"coverage": True, "qhat": qhat.tolist(), "fusion_weights": w.tolist(), "channel_quality": qualities})
    elif mode == "merge":
        if len(angles) < 1:
            result["failure"] = "no_array_only_angle_peak"
            return result
        # Equivalent target uses the strongest array-only angle peak, then one phasor.
        a = angles[0]
        y = beamform(z, a)
        qhat, quality = q_from_channel(y, a, amp_floor)
        result["merged_angle_deg"] = a
        result["channel_quality"] = [quality]
        if qhat is None:
            result["failure"] = "merged_phasor_amplitude_or_geometry_guard"
            return result
        result.update({"coverage": True, "qhat": qhat.tolist()})
    else:
        raise ValueError(mode)
    return result


def score(result: Dict[str, object], q: np.ndarray) -> Dict[str, object]:
    out = {k: v for k, v in result.items() if k != "qhat"}
    if not result.get("coverage"):
        out.update({"rmse_mm": None, "max_abs_error_mm": None, "corr": None})
        return out
    qhat = np.asarray(result["qhat"], float)
    qref = q - q[0]
    # Same reference and sign for every route; no sign/refit optimization.
    err = qhat - qref
    out.update({
        "rmse_mm": float(np.sqrt(np.mean(err * err))),
        "max_abs_error_mm": float(np.max(np.abs(err))),
        "corr": float(np.corrcoef(qhat, qref)[0, 1]),
    })
    return out


def run_one(case: Case, seed: int) -> Dict[str, object]:
    z, q, noise_std = synthesize(case, seed)
    split = score(evaluate(z, noise_std, "split"), q)
    merge = score(evaluate(z, noise_std, "merge"), q)
    return {"case": case.name, "seed": seed, "expected_route": case.expected_route,
            "noise_std": noise_std, "split": split, "merge": merge}


def summarize(rows: List[Dict[str, object]]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for case in sorted({r["case"] for r in rows}):
        out[case] = {}
        for mode in ("split", "merge"):
            rr = [r[mode] for r in rows if r["case"] == case]
            covered = [r for r in rr if r.get("coverage")]
            rmses = np.array([r["rmse_mm"] for r in covered], float)
            out[case][mode] = {
                "trials": len(rr),
                "coverage_count": len(covered),
                "coverage_fraction": len(covered) / len(rr) if rr else 0.0,
                "rmse_mm_median_covered": float(np.median(rmses)) if len(rmses) else None,
                "rmse_mm_p90_covered": float(np.quantile(rmses, 0.9)) if len(rmses) else None,
                "rmse_mm_max_covered": float(np.max(rmses)) if len(rmses) else None,
                "failure_counts": {str(k): sum(1 for r in rr if r.get("failure") == k)
                                    for k in sorted({r.get("failure") for r in rr if r.get("failure")})},
            }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--out", type=Path, default=OUT / "results.json")
    args = ap.parse_args()
    rows = [run_one(c, s) for s in args.seeds for c in CASES]
    payload = {
        "experiment": "same_range_merge_split_mechanism",
        "model": {"lambda_mm": LAMBDA_MM, "n_rx": N_RX, "d_over_lambda": D_OVER_LAMBDA,
                  "n_slow": N_SLOW, "fs_hz": FS_HZ, "same_range": True,
                  "truth_used_by_estimator": False,
                  "estimator": "array-only Bartlett peaks + conventional beamforming + unwrap + fixed geometric cos(beta)",
                  "phase_sign_reference": "phase(y[k]*conj(y[0])); qhat-qhat[0], no sign/refit optimization",
                  "split_rule": {"grid_deg": [float(ANGLE_GRID_DEG[0]), float(ANGLE_GRID_DEG[-1]), float(ANGLE_GRID_DEG[1]-ANGLE_GRID_DEG[0])],
                                 "min_separation_deg": PEAK_MIN_SEP_DEG, "min_second_peak_ratio": PEAK_MIN_RATIO},
                  "merge_rule": "strongest detected array-only angle peak; one beamformed phasor",
                  "guard": f"minimum beamformed magnitude >= {AMP_FLOOR_MULT}x declared complex-noise sigma"},
        "cases": [asdict(c) for c in CASES],
        "seeds": args.seeds,
        "rows": rows,
        "summary": summarize(rows),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
