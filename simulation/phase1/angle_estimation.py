"""Gridless-ish local super-resolution AoA estimators for the synthetic frontend.

The estimator uses the angle FFT only as a coarse candidate generator.  Final
angles are obtained by joint variable-projection least squares on the complex
array snapshots, so they are not quantised to FFT bins.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AngleEstimationResult:
    angles_deg: np.ndarray
    source_slow_time: np.ndarray
    diagnostics: tuple[dict, ...]


def estimate_local_music_ml(
    snapshots: np.ndarray,
    positions_wavelengths: Sequence[float],
    coarse_angles_deg: Sequence[float],
    *,
    search_half_width_u: float = 0.12,
    music_grid_size: int = 129,
    max_snapshots: int = 512,
    iterations: int = 3,
    _method_name: str = "local_music_ml",
) -> AngleEstimationResult:
    """Jointly estimate same-range target angles and complex slow time.

    ``snapshots`` has shape ``(num_virtual_rx, num_snapshots)``.  The returned
    source coefficients are reconstructed with the final, fixed steering
    matrix, avoiding frame-to-frame beamformer phase jumps.  The coordinate
    refinement is deliberately NumPy-only and remains robust for a nonuniform
    array geometry.
    """
    x = np.asarray(snapshots, dtype=complex)
    p = np.asarray(positions_wavelengths, dtype=float).reshape(-1)
    coarse = np.asarray(coarse_angles_deg, dtype=float).reshape(-1)
    if x.ndim != 2 or x.shape[0] != p.size:
        raise ValueError("snapshots must have shape (num_virtual_rx, num_snapshots)")
    if x.shape[1] == 0:
        raise ValueError("snapshots must contain at least one snapshot")
    original_x = x.copy()
    finite_columns = np.all(np.isfinite(x.real) & np.isfinite(x.imag), axis=0)
    if not np.any(finite_columns):
        raise ValueError("snapshots contain no finite columns")
    x = x[:, finite_columns]
    if coarse.size == 0:
        return AngleEstimationResult(np.empty(0), np.empty((0, x.shape[1]), complex), ())
    if p.size < 2 or not np.all(np.isfinite(p)):
        raise ValueError("positions_wavelengths must contain at least two finite values")
    if not np.all(np.isfinite(coarse)):
        raise ValueError("coarse_angles_deg must be finite")
    keep = min(x.shape[1], max(int(max_snapshots), 1))
    xfit = np.ascontiguousarray(x[:, :keep])
    scale = float(np.nanmax(np.abs(xfit)))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("snapshots contain no nonzero finite signal")
    xfit = np.ascontiguousarray(xfit / scale)
    k = min(int(coarse.size), max(p.size - 1, 1))
    coarse = coarse[:k]
    # Keep the strongest candidates when callers provide too many duplicates.
    u = np.sin(np.deg2rad(coarse))
    order = np.argsort(u)
    u = u[order]
    half = max(float(search_half_width_u), 1.0e-4)
    grid_n = max(int(music_grid_size), 17)
    # MUSIC spectrum supplies a physically meaningful continuous initial peak.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        cov = (xfit @ xfit.conj().T) / max(xfit.shape[1], 1)
    if not np.all(np.isfinite(cov)):
        # Extremely large synthetic values can overflow the BLAS path even
        # after scaling; use a finite diagonal covariance as a safe fallback.
        cov = np.eye(p.size, dtype=complex)
    try:
        eigval, eigvec = np.linalg.eigh(cov)
    except np.linalg.LinAlgError:
        eigval, eigvec = np.linalg.eigh(cov + 1.0e-10 * np.eye(p.size))
    noise_dim = max(p.size - k, 1)
    en = eigvec[:, :noise_dim]
    def music_score(uu):
        a = np.exp(2j * np.pi * p * float(uu))
        den = np.linalg.norm(en.conj().T @ a) ** 2
        return 1.0 / max(float(den), 1.0e-14)
    for idx, centre in enumerate(u):
        ug = np.linspace(np.clip(centre - half, -0.999, 0.999),
                         np.clip(centre + half, -0.999, 0.999), grid_n)
        scores = np.asarray([music_score(v) for v in ug])
        # Restrict to the local lobe around the supplied FFT candidate.
        best = int(np.argmax(scores))
        if 0 < best < ug.size - 1:
            y0, y1, y2 = np.log(np.maximum(scores[best - 1:best + 2], 1.0e-30))
            den = y0 - 2.0 * y1 + y2
            frac = 0.5 * (y0 - y2) / den if abs(den) > 1.0e-12 else 0.0
            frac = float(np.clip(frac, -0.5, 0.5))
            u[idx] = ug[best] + frac * (ug[1] - ug[0])
        else:
            u[idx] = ug[best]
    u = np.sort(np.clip(u, -0.999, 0.999))

    def steering(vals):
        return np.exp(2j * np.pi * p[:, None] * np.asarray(vals)[None, :])
    def fit(vals):
        a = steering(vals)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            coef = np.linalg.pinv(a, rcond=1.0e-8) @ xfit
            resid = xfit - a @ coef
        return float(np.vdot(resid, resid).real), coef
    # Joint variable projection: update one source while fitting all sources.
    for _ in range(max(int(iterations), 0)):
        for source in range(k):
            lo = max(-0.999, u[source] - half / 2.0)
            hi = min(0.999, u[source] + half / 2.0)
            ug = np.linspace(lo, hi, max(25, grid_n // 2))
            costs = np.empty(ug.size)
            for j, candidate in enumerate(ug):
                trial = u.copy(); trial[source] = candidate
                costs[j], _ = fit(trial)
            best = int(np.argmin(costs))
            val = float(ug[best])
            if 0 < best < ug.size - 1:
                # Quadratic interpolation on residual cost.
                y0, y1, y2 = costs[best - 1:best + 2]
                den = y0 - 2.0 * y1 + y2
                frac = 0.5 * (y0 - y2) / den if abs(den) > 1.0e-15 else 0.0
                val += float(np.clip(frac, -0.5, 0.5)) * (ug[1] - ug[0])
            u[source] = np.clip(val, -0.999, 0.999)
        u = np.sort(u)
    _, _coef = fit(u)
    # Reconstruct every frame with the fixed final steering matrix.  The
    # max_snapshots limit applies only to covariance/optimization, not output.
    full = np.asarray(original_x, dtype=complex)
    valid = np.all(np.isfinite(full.real) & np.isfinite(full.imag), axis=0)
    coef = np.full((k, full.shape[1]), np.nan + 1j * np.nan, dtype=complex)
    if np.any(valid):
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            coef[:, valid] = np.linalg.pinv(steering(u), rcond=1.0e-8) @ full[:, valid]
    angles = np.rad2deg(np.arcsin(np.clip(u, -1.0, 1.0)))
    residual, _ = fit(u)
    diagnostics = tuple({"method": str(_method_name), "spatial_frequency": float(v),
                         "residual_power": residual / max(float(np.vdot(xfit, xfit).real), 1.0e-15),
                         "num_snapshots": int(keep), "num_sources": int(k)} for v in u)
    # Undo the candidate ordering so each target keeps its original candidate slot.
    inverse = np.argsort(order)
    return AngleEstimationResult(angles[inverse], coef[inverse], tuple(diagnostics[i] for i in inverse))


def estimate_local_music(
    snapshots: np.ndarray,
    positions_wavelengths: Sequence[float],
    coarse_angles_deg: Sequence[float],
    *,
    search_half_width_u: float = 0.12,
    music_grid_size: int = 129,
    max_snapshots: int = 512,
) -> AngleEstimationResult:
    """Local MUSIC-only baseline with the same coarse gate as ML refinement.

    The MUSIC peak is interpolated continuously on the local spatial-frequency
    grid; no residual minimization/refinement is performed.  Source slow-time
    coefficients are still reconstructed jointly with the fixed final steering
    matrix so downstream phase processing has no moving beamformer phase.
    """
    return estimate_local_music_ml(
        snapshots,
        positions_wavelengths,
        coarse_angles_deg,
        search_half_width_u=search_half_width_u,
        music_grid_size=music_grid_size,
        max_snapshots=max_snapshots,
        iterations=0,
        _method_name="local_music",
    )
