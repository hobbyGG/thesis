"""Truth-free RO input isolation smoke; no estimator route is executed."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "spatial_recovery_rebuilt" / "smoke" / "capture_low_motion_0p005mm_seed20261001"
OUTPUT = Path(__file__).resolve().parent / "input_isolation_smoke.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing source package: {SOURCE}")
    with tempfile.TemporaryDirectory(prefix="ro-input-isolation-") as td:
        copy = Path(td) / "capture"
        shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns("truth", "paper_response_metadata.json"))
        forbidden = []
        for path in copy.rglob("*"):
            if path.is_file() and ("truth" in path.parts or "q_proxy" in path.name or "q_true" in path.name):
                forbidden.append(str(path.relative_to(copy)))
        adc = np.load(copy / "radar/algorithm_input/adc_cube.npy", allow_pickle=False, mmap_mode="r")
        chirp = np.load(copy / "radar/algorithm_input/chirp_cube.npy", allow_pickle=False, mmap_mode="r")
        adxl = np.load(copy / "adxl355/algorithm_input/acceleration_mps2.npy", allow_pickle=False, mmap_mode="r")
        source_names = (
            "algorithm/io.py",
            "algorithm/types.py",
            "algorithm/acceleration.py",
            "algorithm/kalman.py",
            "paper_bridge_simulation/package_builder.py",
            "spatial_recovery_rebuilt/rebuild_validation.py",
            "spatial_recovery_rebuilt/ro_allchannel/RO_DESIGN.md",
        )
        result = {
            "schema": "spatial_recovery_rebuilt.ro_input_isolation_smoke",
            "status": "passed" if not forbidden else "failed",
            "estimator_executed": False,
            "source_package": str(SOURCE),
            "truth_present_in_estimator_copy": (copy / "truth").exists(),
            "paper_response_metadata_present_in_estimator_copy": (copy / "paper_response_metadata.json").exists(),
            "forbidden_truth_or_proxy_paths": forbidden,
            "raw_shapes": {"adc_cube": list(adc.shape), "chirp_cube": list(chirp.shape), "adxl": list(adxl.shape)},
            "raw_hashes": {
                "adc_cube": sha256(copy / "radar/algorithm_input/adc_cube.npy"),
                "chirp_cube": sha256(copy / "radar/algorithm_input/chirp_cube.npy"),
                "adxl": sha256(copy / "adxl355/algorithm_input/acceleration_mps2.npy"),
            },
            "source_sha256": {name: sha256(ROOT / name) for name in source_names},
            "conclusion": "raw capture inputs are isolated from truth/q_proxy; RO estimator remains unimplemented",
        }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
