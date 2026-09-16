"""Versioned value/geometry calibration for radar-accelerometer fusion."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Mapping, Union

import numpy as np


SCHEMA_NAME = "mmwavecapture.fusion-calibration"
SCHEMA_VERSION = 1


class FusionCalibrationError(ValueError):
    """Raised when a fusion calibration file is incomplete or ambiguous."""


def _readonly(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FusionCalibrationError(f"{label} must be an object")
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FusionCalibrationError(f"{label} must be a nonempty string")
    return value.strip()


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise FusionCalibrationError(f"{label} must be boolean")
    return value


def _vector(value: Any, length: int, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (length,) or np.any(~np.isfinite(array)):
        raise FusionCalibrationError(
            f"{label} must contain {length} finite numbers"
        )
    return np.array(array, dtype=float, copy=True)


def _matrix3(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (3, 3) or np.any(~np.isfinite(array)):
        raise FusionCalibrationError(f"{label} must be a finite 3x3 matrix")
    return np.array(array, dtype=float, copy=True)


@dataclass(frozen=True)
class AdxlValueCalibration:
    bias_mps2: np.ndarray
    scale_matrix: np.ndarray
    sensor_to_structure_rotation: np.ndarray
    structural_axis_unit: np.ndarray
    source: str

    def apply_xyz(self, nominal_acceleration_mps2: np.ndarray) -> np.ndarray:
        """Apply bias, scale/cross-axis, and sensor-to-structure transforms."""

        values = np.asarray(nominal_acceleration_mps2, dtype=float)
        if values.ndim != 2 or values.shape[1] != 3:
            raise FusionCalibrationError(
                "nominal ADXL acceleration must have shape (sample, 3)"
            )
        if np.any(~np.isfinite(values)):
            raise FusionCalibrationError("nominal ADXL acceleration is not finite")
        corrected_sensor = (values - self.bias_mps2) @ self.scale_matrix.T
        return corrected_sensor @ self.sensor_to_structure_rotation.T

    def project_structural_axis(
        self,
        nominal_acceleration_mps2: np.ndarray,
    ) -> np.ndarray:
        structure_xyz = self.apply_xyz(nominal_acceleration_mps2)
        return structure_xyz @ self.structural_axis_unit


@dataclass(frozen=True)
class RadarFrontendCalibration:
    azimuth_virtual_channel_indices: np.ndarray
    virtual_array_positions_wavelengths: np.ndarray
    channel_complex_correction: np.ndarray
    range_bias_correction_m: float
    source: str

    def calibrated_azimuth_cube(self, adc_cube: np.ndarray) -> np.ndarray:
        """Select calibrated azimuth channels without mutating raw radar IQ."""

        cube = np.asarray(adc_cube)
        if cube.ndim != 3:
            raise FusionCalibrationError(
                "radar ADC cube must have shape (frame, virtual_antenna, sample)"
            )
        if int(np.max(self.azimuth_virtual_channel_indices)) >= cube.shape[1]:
            raise FusionCalibrationError(
                "azimuth channel calibration exceeds captured virtual antennas"
            )
        selected = cube[:, self.azimuth_virtual_channel_indices, :]
        return selected * self.channel_complex_correction[None, :, None]


@dataclass(frozen=True)
class FusionValueCalibration:
    calibration_id: str
    validated: bool
    adxl355: AdxlValueCalibration
    radar: RadarFrontendCalibration
    manifest: Mapping[str, Any]
    source_path: pathlib.Path


def _parse_adxl(payload: Mapping[str, Any]) -> AdxlValueCalibration:
    bias = _vector(payload.get("bias_mps2"), 3, "ADXL355 bias_mps2")
    scale = _matrix3(payload.get("scale_matrix"), "ADXL355 scale_matrix")
    if abs(float(np.linalg.det(scale))) <= 1.0e-12:
        raise FusionCalibrationError("ADXL355 scale_matrix must be invertible")
    rotation = _matrix3(
        payload.get("sensor_to_structure_rotation"),
        "ADXL355 sensor_to_structure_rotation",
    )
    if not np.allclose(rotation @ rotation.T, np.eye(3), rtol=0.0, atol=1.0e-6):
        raise FusionCalibrationError(
            "ADXL355 sensor_to_structure_rotation must be orthonormal"
        )
    if not np.isclose(np.linalg.det(rotation), 1.0, rtol=0.0, atol=1.0e-6):
        raise FusionCalibrationError(
            "ADXL355 sensor_to_structure_rotation must be right-handed"
        )
    axis = _vector(
        payload.get("structural_axis_unit"),
        3,
        "ADXL355 structural_axis_unit",
    )
    if not np.isclose(np.linalg.norm(axis), 1.0, rtol=0.0, atol=1.0e-6):
        raise FusionCalibrationError("ADXL355 structural_axis_unit must have norm 1")
    return AdxlValueCalibration(
        bias_mps2=_readonly(bias),
        scale_matrix=_readonly(scale),
        sensor_to_structure_rotation=_readonly(rotation),
        structural_axis_unit=_readonly(axis),
        source=_nonempty_string(payload.get("source"), "ADXL355 source"),
    )


def _parse_radar(payload: Mapping[str, Any]) -> RadarFrontendCalibration:
    raw_indices = np.asarray(payload.get("azimuth_virtual_channel_indices"))
    if (
        raw_indices.ndim != 1
        or raw_indices.size == 0
        or raw_indices.dtype.kind not in "iu"
        or raw_indices.dtype.kind == "b"
    ):
        raise FusionCalibrationError(
            "radar azimuth_virtual_channel_indices must be a nonempty integer vector"
        )
    indices = np.array(raw_indices, dtype=np.int64, copy=True)
    if np.any(indices < 0) or np.unique(indices).size != indices.size:
        raise FusionCalibrationError(
            "radar azimuth_virtual_channel_indices must be unique and nonnegative"
        )
    positions = _vector(
        payload.get("virtual_array_positions_wavelengths"),
        indices.size,
        "radar virtual_array_positions_wavelengths",
    )
    correction_real = _vector(
        payload.get("channel_correction_real"),
        indices.size,
        "radar channel_correction_real",
    )
    correction_imag = _vector(
        payload.get("channel_correction_imag"),
        indices.size,
        "radar channel_correction_imag",
    )
    correction = correction_real + 1j * correction_imag
    if np.any(np.abs(correction) <= 0.0):
        raise FusionCalibrationError("radar channel correction cannot contain zero")
    range_bias = payload.get("range_bias_correction_m")
    if (
        isinstance(range_bias, bool)
        or not isinstance(range_bias, (int, float))
        or not np.isfinite(range_bias)
    ):
        raise FusionCalibrationError(
            "radar range_bias_correction_m must be finite"
        )
    return RadarFrontendCalibration(
        azimuth_virtual_channel_indices=_readonly(indices),
        virtual_array_positions_wavelengths=_readonly(positions),
        channel_complex_correction=_readonly(
            np.array(correction, dtype=np.complex128, copy=True)
        ),
        range_bias_correction_m=float(range_bias),
        source=_nonempty_string(payload.get("source"), "radar source"),
    )


def load_fusion_calibration(
    path: Union[str, pathlib.Path],
) -> FusionValueCalibration:
    calibration_path = pathlib.Path(path)
    try:
        payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FusionCalibrationError(
            f"cannot read fusion calibration {calibration_path}: {exc}"
        ) from exc
    manifest = _mapping(payload, "fusion calibration")
    if manifest.get("schema") != SCHEMA_NAME:
        raise FusionCalibrationError(
            f"unsupported fusion calibration schema {manifest.get('schema')!r}"
        )
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise FusionCalibrationError(
            "unsupported fusion calibration schema version "
            f"{manifest.get('schema_version')!r}"
        )
    calibration_id = _nonempty_string(
        manifest.get("calibration_id"),
        "calibration_id",
    )
    validated = _boolean(manifest.get("validated"), "validated")
    adxl = _parse_adxl(_mapping(manifest.get("adxl355"), "ADXL355 calibration"))
    radar = _parse_radar(_mapping(manifest.get("radar"), "radar calibration"))
    return FusionValueCalibration(
        calibration_id=calibration_id,
        validated=validated,
        adxl355=adxl,
        radar=radar,
        manifest=manifest,
        source_path=calibration_path,
    )


__all__ = (
    "AdxlValueCalibration",
    "FusionCalibrationError",
    "FusionValueCalibration",
    "RadarFrontendCalibration",
    "load_fusion_calibration",
)
