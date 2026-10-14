"""Radar front end of one simulated record, cached on disk.

Synthesising the ADC cube and running the range FFT and DBF dominates the cost
of a trial; the circle fit, the Kalman filter and the baselines after it are
cheap.  ``load_front`` therefore caches the front-end output, keyed on the
scenario, the radar-side impairments, the seed and the source of every module
the result depends on.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields, replace
from functools import lru_cache
from pathlib import Path

import numpy as np

from paper_bridge_simulation.package_builder import RADAR_RATE_HZ, generate
from paper_bridge_simulation.scenario import Impairments, Scenario
from system.algorithm.frontend import TargetData
from system.algorithm.io import effective_carrier_frequency_hz, extract_targets, load_capture_package

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
DEPENDENCIES = (
    "paper_bridge_simulation/package_builder.py",
    "paper_bridge_simulation/response.py",
    "paper_bridge_simulation/scenario.py",
    "system/algorithm/frontend.py",
    "system/algorithm/selection.py",
    "system/algorithm/types.py",
    "system/algorithm/io.py",
    "experiments/front.py",
)


@dataclass(frozen=True)
class Front:
    targets: TargetData
    detection: dict
    radar_time_ns: np.ndarray
    truth_m: np.ndarray
    carrier_frequency_hz: float
    scatterer_range_m: np.ndarray
    scatterer_angle_deg: np.ndarray

    @property
    def radar_rate_hz(self) -> float:
        return float(1.0 / np.median(np.diff(self.radar_time_ns) * 1.0e-9))

    @property
    def time_s(self) -> np.ndarray:
        return (self.radar_time_ns - self.radar_time_ns[0]) * 1.0e-9


def radar_impairments(impairments: Impairments) -> Impairments:
    """The part of the impairments that changes the radar record itself."""
    nominal = Impairments()
    swaying = impairments.target_sway_std_m > 0.0
    return Impairments(
        snr_offset_db=impairments.snr_offset_db,
        iq_offset_ratio=impairments.iq_offset_ratio,
        target_sway_std_m=impairments.target_sway_std_m,
        target_sway_corner_hz=impairments.target_sway_corner_hz if swaying else nominal.target_sway_corner_hz,
        target_sway_targets=impairments.target_sway_targets if swaying else nominal.target_sway_targets,
    )


def compute_front(scenario: Scenario, impairments: Impairments, seed: int, duration_s: float) -> Front:
    """Synthesise one record and run the front end (no cache)."""
    with tempfile.TemporaryDirectory(prefix="front_") as temporary:
        package = generate(
            Path(temporary) / "package", duration_s=duration_s, seed=seed,
            impairments=impairments, scenario=scenario, fast=True,
        )
        capture = load_capture_package(package)
        targets, detection = extract_targets(capture)
        radar_time_ns = np.asarray(capture.radar_time_ns, dtype=np.int64)
        truth_m = np.interp(
            radar_time_ns.astype(float),
            np.asarray(capture.truth_time_ns, dtype=float),
            np.asarray(capture.truth_displacement_m, dtype=float),
        )
        return Front(
            targets, detection, radar_time_ns, truth_m,
            effective_carrier_frequency_hz(capture),
            scenario.target_ranges_m(), np.asarray(scenario.target_angles_deg, dtype=float),
        )


def apply_dropout(front: Front, start_s: float, duration_s: float) -> Front:
    """Lose all targets for a run of frames (same result as NaN ADC frames)."""
    first = round(start_s * RADAR_RATE_HZ)
    last = first + round(duration_s * RADAR_RATE_HZ)
    slow_time = front.targets.slow_time.copy()
    available = front.targets.available_mask.copy()
    wrapped = front.targets.wrapped_phase_rad.copy()
    slow_time[:, first:last] = np.nan + 1j * np.nan
    available[:, first:last] = False
    wrapped[:, first:last] = np.nan
    return replace(
        front,
        targets=replace(front.targets, slow_time=slow_time, available_mask=available, wrapped_phase_rad=wrapped),
    )


@lru_cache(maxsize=1)
def _source_digest() -> str:
    digest = hashlib.sha256()
    for name in DEPENDENCIES:
        digest.update((ROOT / name).read_bytes())
    return digest.hexdigest()


def _cache_path(cache_dir: Path, scenario: Scenario, radar_side: Impairments, seed: int, duration_s: float) -> Path:
    payload = json.dumps(
        {"scenario": asdict(scenario), "impairments": asdict(radar_side), "seed": seed, "duration_s": duration_s},
        sort_keys=True,
    )
    digest = hashlib.sha256((payload + _source_digest()).encode()).hexdigest()[:24]
    return cache_dir / f"front_{digest}.npz"


def _save(path: Path, front: Front) -> None:
    arrays = {f"t_{field.name}": getattr(front.targets, field.name) for field in fields(TargetData)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.stem}.{os.getpid()}.tmp.npz")
    np.savez(
        temporary, **arrays,
        radar_time_ns=front.radar_time_ns, truth_m=front.truth_m,
        scatterer_range_m=front.scatterer_range_m, scatterer_angle_deg=front.scatterer_angle_deg,
        scalars=np.array([front.carrier_frequency_hz, front.detection["candidate_count"],
                          front.detection["strongest_magnitude"]]),
    )
    os.replace(temporary, path)


def _load(path: Path) -> Front:
    with np.load(path, allow_pickle=False) as data:
        carrier, count, strongest = data["scalars"]
        return Front(
            TargetData(**{field.name: data[f"t_{field.name}"] for field in fields(TargetData)}),
            {"candidate_count": int(count), "strongest_magnitude": float(strongest)},
            data["radar_time_ns"], data["truth_m"], float(carrier),
            data["scatterer_range_m"], data["scatterer_angle_deg"],
        )


def load_front(scenario: Scenario, impairments: Impairments, seed: int, duration_s: float,
               cache_dir: Path | None = CACHE_DIR) -> Front:
    """Front end of a record; ``cache_dir=None`` disables the disk cache."""
    radar_side = radar_impairments(impairments)
    if cache_dir is None:
        return compute_front(scenario, radar_side, seed, duration_s)
    path = _cache_path(cache_dir, scenario, radar_side, seed, duration_s)
    if path.is_file():
        return _load(path)
    front = compute_front(scenario, radar_side, seed, duration_s)
    _save(path, front)
    return front
