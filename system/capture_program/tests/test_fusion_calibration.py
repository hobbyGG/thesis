import json

import numpy as np
import pytest

from mmwavecapture.fusion_calibration import (
    FusionCalibrationError,
    load_fusion_calibration,
)


def _payload():
    return {
        "schema": "mmwavecapture.fusion-calibration",
        "schema_version": 1,
        "calibration_id": "bench-v1",
        "validated": True,
        "adxl355": {
            "bias_mps2": [1.0, 0.0, 0.0],
            "scale_matrix": [[2.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "sensor_to_structure_rotation": [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
            "structural_axis_unit": [0.0, 1.0, 0.0],
            "source": "six-position-and-installation-survey",
        },
        "radar": {
            "azimuth_virtual_channel_indices": [0, 1],
            "virtual_array_positions_wavelengths": [0.0, 0.5],
            "channel_correction_real": [1.0, 0.0],
            "channel_correction_imag": [0.0, -1.0],
            "range_bias_correction_m": -0.02,
            "source": "corner-reflector-v1",
        },
    }


def _write(tmp_path, payload):
    path = tmp_path / "fusion_calibration.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_applies_adxl_structure_axis_and_radar_channel_calibration(tmp_path):
    calibration = load_fusion_calibration(_write(tmp_path, _payload()))

    acceleration = np.array([[2.0, 3.0, 4.0]])
    np.testing.assert_allclose(
        calibration.adxl355.apply_xyz(acceleration),
        [[3.0, -2.0, 4.0]],
    )
    np.testing.assert_allclose(
        calibration.adxl355.project_structural_axis(acceleration),
        [-2.0],
    )

    cube = np.ones((1, 3, 2), dtype=np.complex64)
    calibrated = calibration.radar.calibrated_azimuth_cube(cube)
    np.testing.assert_allclose(calibrated[0, :, 0], [1.0, -1.0j])
    np.testing.assert_array_equal(cube, np.ones((1, 3, 2), dtype=np.complex64))


@pytest.mark.parametrize(
    "edit,match",
    [
        (
            lambda payload: payload["adxl355"].__setitem__(
                "sensor_to_structure_rotation",
                [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1.0]],
            ),
            "orthonormal",
        ),
        (
            lambda payload: payload["adxl355"].__setitem__(
                "structural_axis_unit", [1.0, 1.0, 0.0]
            ),
            "norm 1",
        ),
        (
            lambda payload: payload["radar"].__setitem__(
                "azimuth_virtual_channel_indices", [0, 0]
            ),
            "unique and nonnegative",
        ),
    ],
)
def test_rejects_ambiguous_or_nonphysical_calibration(tmp_path, edit, match):
    payload = _payload()
    edit(payload)

    with pytest.raises(FusionCalibrationError, match=match):
        load_fusion_calibration(_write(tmp_path, payload))
