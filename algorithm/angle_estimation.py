from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AngleEstimationResult:
    angles_deg: np.ndarray
    source_slow_time: np.ndarray


def estimate_local_music_ml(
    snapshots: np.ndarray,
    positions_wavelengths: Sequence[float],
    coarse_angles_deg: Sequence[float],
    *,
    search_half_width_u: float = 0.12,
    music_grid_size: int = 129,
    max_snapshots: int = 512,
) -> AngleEstimationResult:
    """Refine FFT angle candidates with local MUSIC and least squares."""

    original = np.asarray(snapshots, dtype=complex)
    x = original.copy()
    positions = np.asarray(positions_wavelengths, dtype=float)
    coarse = np.asarray(coarse_angles_deg, dtype=float).reshape(-1)
    x = x[:, np.all(np.isfinite(x.real) & np.isfinite(x.imag), axis=0)]
    if x.shape[1] > max_snapshots:
        x = x[:, :max_snapshots]
    if coarse.size == 0:
        return AngleEstimationResult(np.empty(0), np.empty((0, x.shape[1]), complex))
    count = min(coarse.size, max(positions.size - 1, 1))
    u = np.sort(np.sin(np.deg2rad(coarse[:count])))
    scale = max(float(np.nanmax(np.abs(x))), 1.0e-15)
    x = x / scale
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        covariance = np.einsum("ik,jk->ij", x, x.conj()) / max(x.shape[1], 1)
    _, eigenvectors = np.linalg.eigh(covariance)
    noise = eigenvectors[:, : max(positions.size - count, 1)]
    half = max(float(search_half_width_u), 1.0e-4)
    grid_size = max(int(music_grid_size), 17)

    def steering(values):
        return np.exp(2j * np.pi * positions[:, None] * np.asarray(values)[None, :])

    def music_score(value):
        vector = np.exp(2j * np.pi * positions * value)
        return 1.0 / max(float(np.linalg.norm(noise.conj().T @ vector) ** 2), 1.0e-14)

    for i, center in enumerate(u):
        grid = np.linspace(max(-0.999, center - half), min(0.999, center + half), grid_size)
        u[i] = grid[int(np.argmax([music_score(value) for value in grid]))]

    def fit(values):
        matrix = steering(values)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            coefficient = np.einsum("ij,jk->ik", np.linalg.pinv(matrix, rcond=1.0e-8), x)
            residual = x - np.einsum("ij,jk->ik", matrix, coefficient)
        return float(np.vdot(residual, residual).real), coefficient

    for _ in range(3):
        for source in range(count):
            grid = np.linspace(max(-0.999, u[source] - half / 2), min(0.999, u[source] + half / 2), 25)
            costs = np.asarray([fit(np.where(np.arange(count) == source, value, u))[0] for value in grid])
            u[source] = grid[int(np.argmin(costs))]
        u.sort()

    matrix = steering(u)
    coefficient = np.linalg.pinv(matrix, rcond=1.0e-8) @ original
    return AngleEstimationResult(np.rad2deg(np.arcsin(np.clip(u, -1.0, 1.0))), coefficient)
