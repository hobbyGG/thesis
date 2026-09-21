from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np


@dataclass(frozen=True)
class FrontendConfig:
    num_virtual_rx: int
    num_adc_samples: int
    num_range_bins: int
    num_angle_bins: int = 64
    range_resolution_m: float = 0.15
    antenna_spacing_wavelengths: float = 0.5
    angle_window: str = "hann"
    radar_mount: str = "downward"
    virtual_array_positions_wavelengths: tuple[float, ...] = ()
    angle_estimation_method: str = "local_music_ml"
    angle_search_half_width_u: float = 0.12
    angle_music_grid_size: int = 129
    angle_max_snapshots: int = 512


@dataclass(frozen=True)
class AccelerationInput:
    native_time_ns: np.ndarray
    native_mps2: np.ndarray
    measured_mps2: np.ndarray
    preintegration: Any


@dataclass(frozen=True)
class RadarInput:
    measured_beta: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    selected_indices: np.ndarray
    initial_r: np.ndarray
    selection_scores: np.ndarray
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapturePackage:
    root: Path
    adc_cube: np.ndarray
    frame_times_s: np.ndarray
    radar_time_ns: np.ndarray
    adxl_time_ns: np.ndarray
    adxl_acceleration_mps2: np.ndarray
    frontend: FrontendConfig
    truth_displacement_m: Optional[np.ndarray] = None
    truth_time_ns: Optional[np.ndarray] = None
