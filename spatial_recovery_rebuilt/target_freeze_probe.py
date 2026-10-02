"""Probe whether RA target geometry depends on post-calibration ADC frames.

This scratch-only diagnostic keeps frames 0:200 byte-identical, applies a
deterministic channel steering/amplitude perturbation only to frames 200:400,
and compares the ordinary frame-mode frontend outputs.  It deliberately
removes truth before loading either package and does not run the Kalman result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.io import build_algorithm_inputs, load_capture_package


DEFAULT_PACKAGE = ROOT / "spatial_recovery_rebuilt" / "smoke" / "capture_low_motion_0p005mm_seed20261001"


def _sha256_array(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _strip_truth(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("truth", "paper_response_metadata.json"))


def _frontend_snapshot(package: Path) -> dict[str, object]:
    capture = load_capture_package(package)
    radar, _accel, targets, _rate = build_algorithm_inputs(capture, radar_mode="frame")
    detection = radar.extra["detection"]
    return {
        "candidate_count": int(detection["candidate_count"]),
        "selected_indices": radar.selected_indices.astype(int).tolist(),
        "range_bins": targets.range_bins.astype(int).tolist(),
        "angle_bins": targets.angle_bins.astype(int).tolist(),
        "angle_deg": targets.angle_deg.astype(float).tolist(),
        "measured_beta": targets.measured_beta.astype(float).tolist(),
        "target_count": int(radar.selected_indices.size),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe full-window RA target/beta dependence")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--output", type=Path, default=ROOT / "spatial_recovery_rebuilt" / "target_freeze_probe.json")
    args = parser.parse_args()

    adc_rel = Path("radar") / "algorithm_input" / "adc_cube.npy"
    manifest = json.loads((args.package / adc_rel.parent / "manifest.json").read_text(encoding="utf-8"))
    positions = np.asarray(manifest["radar"]["virtual_array_positions_wavelengths"], dtype=float)
    with tempfile.TemporaryDirectory(prefix="target-freeze-probe-") as temporary:
        baseline = Path(temporary) / "baseline"
        perturbed = Path(temporary) / "perturbed"
        _strip_truth(args.package, baseline)
        _strip_truth(args.package, perturbed)

        adc_path = perturbed / adc_rel
        adc = np.load(adc_path, allow_pickle=False)
        first_half_before = np.asarray(adc[:200]).copy()
        # Change only the frozen-test half.  The per-channel steering term is
        # intentionally large enough to expose a geometry estimator that reads
        # all frames; it is not a proposed physical model or experiment.
        steering = np.exp(2j * np.pi * positions * np.sin(np.deg2rad(40.0)))
        adc[200:] = 20.0 * adc[200:] * steering[None, :, None]
        np.save(adc_path, adc, allow_pickle=False)

        baseline_snapshot = _frontend_snapshot(baseline)
        perturbed_snapshot = _frontend_snapshot(perturbed)
        first_half_after = np.load(adc_path, allow_pickle=False)[:200]
        changed_fields = [
            field for field in ("candidate_count", "selected_indices", "range_bins", "angle_bins", "angle_deg", "measured_beta", "target_count")
            if baseline_snapshot[field] != perturbed_snapshot[field]
        ]
        result = {
            "schema": "spatial_recovery_rebuilt.target_freeze_probe",
            "status": "completed",
            "source_package": str(args.package),
            "truth_present_in_estimator_copies": False,
            "perturbation": {
                "frames_changed": [200, 399],
                "frames_unchanged": [0, 199],
                "channel_steering_angle_deg": 40.0,
                "amplitude_multiplier": 20.0,
                "interpretation": "diagnostic-only post-test perturbation; not a physical model",
            },
            "first_200_exactly_unchanged": bool(np.array_equal(first_half_before, first_half_after)),
            "baseline_adc_sha256": _sha256_array(args.package / adc_rel),
            "perturbed_adc_sha256": _sha256_array(adc_path),
            "baseline_frontend": baseline_snapshot,
            "perturbed_frontend": perturbed_snapshot,
            "changed_frontend_fields": changed_fields,
            "conclusion": (
                "target/angle/beta output changes after a test-half-only perturbation, "
                "so the current RA frontend is not frozen to calibration frames"
                if changed_fields and bool(np.array_equal(first_half_before, first_half_after))
                else "probe did not establish the expected dependence"
            ),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
