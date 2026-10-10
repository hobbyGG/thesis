#!/usr/bin/env python3
"""Fail-closed preflight for the archived 400-402 pairing experiment.

This intentionally does not run a substitute experiment. It becomes the
entrypoint only after the original archive is restored and its runner contract
is inspected.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / "experiments/same_range_geometry_reference_diagnostic/heldout_20261003"
if not EXPECTED.is_dir():
    raise SystemExit(
        "BLOCKED: missing original archive directory: " + str(EXPECTED) +
        "; restore the exact 400-402 source/protocol/manifest before running."
    )
required = ("protocol.json", "manifest.json")
missing = [name for name in required if not (EXPECTED / name).is_file()]
if missing:
    raise SystemExit("BLOCKED: archive exists but required files are missing: " + ", ".join(missing))
print(json.dumps({"status": "preflight_passed", "archive": str(EXPECTED)}))
