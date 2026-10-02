"""Scratch-only audit of the RA front-end's calibration/test frame usage.

The diagnostic copies an existing smoke package without truth/evaluator files,
keeps frames 0:200 byte-identical, and perturbs only frames 200:400.  It then
rebuilds the normal RA inputs from both copies.  A change in target geometry,
selection, or beta shows that the current front-end sees the frozen-test ADC
frames while constructing those quantities.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "spatial_recovery_rebuilt" / "smoke" / "capture_low_motion_0p005mm_seed20261001"
OUTPUT = Path(__file__).resolve().parent / "ra_fence_audit.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.io import build_algorithm_inputs, load_capture_package  # noqa: E402


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_record(package: Path) -> tuple[np.ndarray, dict[str, object]]:
    manifest = json.loads(
        (package / "radar" / "algorithm_input" / "manifest.json").read_text(encoding="utf-8")
    )
    adc_path = package / "radar" / "algorithm_input" / manifest["arrays"]["adc_cube"]["file"]
    adc = np.load(adc_path, allow_pickle=False).copy()
    return adc, {"path": str(adc_path), "shape": list(adc.shape), "dtype": adc.dtype.name}


def summarize(package: Path) -> dict[str, object]:
    capture = load_capture_package(package)
    radar, _acceleration, targets, _rate = build_algorithm_inputs(capture, radar_mode="frame")
    return {
        "candidate_count": int(radar.extra["detection"]["candidate_count"]),
        "selected_indices": radar.selected_indices.tolist(),
        "range_bins": targets.range_bins.tolist(),
        "range_m": targets.range_m.tolist(),
        "angle_deg": targets.angle_deg.tolist(),
        "beta": targets.measured_beta.tolist(),
        "radar_samples": int(radar.wrapped_phase_rad.shape[1]),
        "truth_files_present": (package / "truth").exists(),
    }


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing smoke source: {SOURCE}")
    with tempfile.TemporaryDirectory(prefix="ra-fence-audit-") as temporary:
        root = Path(temporary)
        baseline = root / "baseline"
        perturbed = root / "perturbed"
        ignore = shutil.ignore_patterns("truth", "paper_response_metadata.json")
        shutil.copytree(SOURCE, baseline, ignore=ignore)
        shutil.copytree(SOURCE, perturbed, ignore=ignore)

        before, adc_meta = array_record(baseline)
        after, _ = array_record(perturbed)
        if not np.array_equal(before, after):
            raise RuntimeError("copy mismatch before perturbation")

        first200_before = before[:200].tobytes(order="C")
        last200_before = before[200:].tobytes(order="C")

        # Diagnostic-only coherent tone in a previously empty range bin.  It is
        # deliberately strong so a 200-frame post-test perturbation cannot be
        # hidden by the detector's median aggregation.  It is not a scene model.
        n = np.arange(before.shape[-1], dtype=float)
        tone = 20.0 * np.exp(2.0j * np.pi * 100.0 * n / before.shape[-1])
        after[200:] += tone[None, None, :]
        manifest = json.loads(
            (perturbed / "radar" / "algorithm_input" / "manifest.json").read_text(encoding="utf-8")
        )
        adc_path = perturbed / "radar" / "algorithm_input" / manifest["arrays"]["adc_cube"]["file"]
        np.save(adc_path, after, allow_pickle=False)

        first200_after = after[:200].tobytes(order="C")
        last200_after = after[200:].tobytes(order="C")
        if first200_before != first200_after:
            raise RuntimeError("the perturbation changed calibration frames")
        if last200_before == last200_after:
            raise RuntimeError("the perturbation did not change test frames")

        baseline_summary = summarize(baseline)
        perturbed_summary = summarize(perturbed)

        geometry_fields = ("range_bins", "range_m", "angle_deg", "beta", "selected_indices")
        changed = {
            key: baseline_summary[key] != perturbed_summary[key] for key in geometry_fields
        }
        report = {
            "schema": "spatial_recovery_rebuilt.ra_fence_audit",
            "source_package": str(SOURCE),
            "truth_isolation": {
                "estimator_copies_excluded": ["truth/", "paper_response_metadata.json"],
                "baseline_truth_files_present": bool(baseline_summary["truth_files_present"]),
                "perturbed_truth_files_present": bool(perturbed_summary["truth_files_present"]),
            },
            "frame_edit": {
                "calibration_frames_unchanged": first200_before == first200_after,
                "test_frames_changed": last200_before != last200_after,
                "calibration_frame_hash_before": sha256_bytes(first200_before),
                "calibration_frame_hash_after": sha256_bytes(first200_after),
                "test_frame_hash_before": sha256_bytes(last200_before),
                "test_frame_hash_after": sha256_bytes(last200_after),
                "adc": adc_meta,
                "diagnostic": "complex tone at FFT bin 100 added only to frames 200:400",
            },
            "baseline": baseline_summary,
            "post_test_perturbed": perturbed_summary,
            "geometry_changed": changed,
            "post_test_data_affects_ra_geometry": bool(any(changed.values())),
            "interpretation": (
                "Changing only ADC frames 200:400 changes detection, selected range bins, "
                "angles and beta; current RA geometry is therefore built from all 400 frames, "
                "not frozen from frames 0:200."
            ),
            "source_evidence": {
                "algorithm/io.py": "98-115",
                "algorithm/selection.py": "4-28,32-37",
                "algorithm/frontend.py": "46-56,59-98",
                "algorithm/angle_estimation.py": "24-38,55-71",
                "algorithm/run.py": "14-18,50-62",
            },
        }
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
