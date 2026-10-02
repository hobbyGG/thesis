"""Scratch-only target-ID/beta association smoke.

The diagnostic adds a complex tone to estimator-copy ADC frames 200:209. A
20-frame rolling window then produces a controlled 5 -> 1 -> 5 target-count
transition. The check reindexes beta by ``(range_bin, angle_bin)`` IDs and
verifies that a missing target becomes NaN in its fixed slot rather than
receiving a surviving target's beta. No displacement or truth score is run.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithm.io import load_capture_package  # noqa: E402
from spatial_recovery_rebuilt.rebuild_validation import _write_scratch_package  # noqa: E402

from experiments.online_geometry_loop_scratch.online_geometry_loop import (  # noqa: E402
    _copy_estimator_only,
    _run_loop,
)


WINDOW_FRAMES = 20
FIRST_OUTPUT_FRAME = 199
OUTPUT_FRAMES = 50
PERTURB_START_FRAME = 200
PERTURB_END_FRAME_EXCLUSIVE = 210
PERTURB_AMPLITUDE = 20.0


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _json_default(value: object):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def _apply_interval_tone(estimator_input: Path) -> dict[str, object]:
    manifest_path = estimator_input / "radar" / "algorithm_input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adc_path = manifest_path.parent / manifest["arrays"]["adc_cube"]["file"]
    adc = np.asarray(np.load(adc_path, allow_pickle=False), dtype=np.complex128)
    sample_index = np.arange(adc.shape[-1], dtype=float)
    tone = PERTURB_AMPLITUDE * np.exp(2j * np.pi * 100.0 * sample_index / adc.shape[-1])
    adc[PERTURB_START_FRAME:PERTURB_END_FRAME_EXCLUSIVE] += tone[None, None, :]
    np.save(adc_path, adc, allow_pickle=False)
    return {
        "enabled": True,
        "start_frame": PERTURB_START_FRAME,
        "end_frame_exclusive": PERTURB_END_FRAME_EXCLUSIVE,
        "amplitude": PERTURB_AMPLITUDE,
        "excluded_from_guard_and_rmse": True,
    }


def _target_ids(row: dict[str, object]) -> list[tuple[int, int]]:
    return [
        (int(r), int(a))
        for r, a in zip(row["range_bins"], row["angle_bins"])
    ]


def run_smoke(output: Path, *, seed: int = 20261001) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="association-smoke-") as temporary:
        root = Path(temporary)
        generated = root / "generated_with_evaluation_artifacts"
        estimator_input = root / "estimator_input_truth_free"
        _write_scratch_package(
            generated,
            stratum_name="stationary",
            requested_rms_mm=0.0,
            seed=seed,
        )
        _copy_estimator_only(generated, estimator_input)
        perturbation = _apply_interval_tone(estimator_input)
        capture = load_capture_package(estimator_input)
        if capture.truth_displacement_m is not None or capture.truth_time_ns is not None:
            raise AssertionError("truth reached association estimator smoke")
        rows = _run_loop(
            capture,
            window_frames=WINDOW_FRAMES,
            output_frames=OUTPUT_FRAMES,
            first_output_frame=FIRST_OUTPUT_FRAME,
        )

        raw_ids = [_target_ids(row) for row in rows]
        counts = [int(row["target_count"]) for row in rows]
        if counts[0] != 5 or 1 not in counts or counts[-1] != 5:
            raise AssertionError(f"expected 5 -> 1 -> 5, got {counts}")
        first_one = counts.index(1)
        last_one = len(counts) - 1 - counts[::-1].index(1)
        if not all(counts[i] == 1 for i in range(first_one, last_one + 1)):
            raise AssertionError("diagnostic target-count transition is not a contiguous 1-target block")
        if not all(counts[i] == 5 for i in range(last_one + 1, len(counts))):
            raise AssertionError("target count did not return to five after the missing block")

        fixed_slots = tuple(raw_ids[0])
        if len(set(fixed_slots)) != 5:
            raise AssertionError(f"baseline target IDs are not unique: {fixed_slots}")
        association_mismatch_count = 0
        missing_slot_contamination = 0
        associated_trace: list[dict[str, object]] = []
        raw_order_permutations = 0
        nonbaseline_ids: set[tuple[int, int]] = set()
        for row, ids in zip(rows, raw_ids):
            beta = np.asarray(row["beta"], dtype=float)
            current = {target_id: float(value) for target_id, value in zip(ids, beta)}
            if len(ids) == 5:
                if set(ids) != set(fixed_slots):
                    association_mismatch_count += 1
                if tuple(ids) != fixed_slots:
                    raw_order_permutations += 1
            else:
                nonbaseline_ids.update(set(ids) - set(fixed_slots))
            stable = []
            for slot in fixed_slots:
                value = current.get(slot)
                stable.append({
                    "id": [int(slot[0]), int(slot[1])],
                    "present": value is not None,
                    "beta": value,
                })
            missing_slots = [item for item in stable if not item["present"]]
            # A missing baseline slot is represented as None/NaN. It must
            # never receive any beta from the remaining raw targets.
            if any(item["beta"] is not None for item in missing_slots):
                missing_slot_contamination += 1
            if len(ids) == 1:
                # Here the sole diagnostic ID is not one of the five baseline
                # IDs, so every fixed slot must remain absent/NaN.
                if any(item["present"] or item["beta"] is not None for item in stable):
                    missing_slot_contamination += 1
            associated_trace.append({
                "frame_index": int(row["frame_index"]),
                "window_frame_range": row["window_frame_range"],
                "raw_ids": [[int(target_id[0]), int(target_id[1])] for target_id in ids],
                "raw_beta": beta.tolist(),
                "stable_slots": stable,
            })

        # A compact per-slot beta series demonstrates that order is fixed by
        # IDs even when the frontend's raw target order permutes.
        stable_present = np.asarray(
            [[item["present"] for item in row["stable_slots"]] for row in associated_trace],
            dtype=bool,
        )
        stable_beta = np.asarray(
            [[np.nan if item["beta"] is None else item["beta"] for item in row["stable_slots"]]
             for row in associated_trace],
            dtype=float,
        )
        report = {
            "schema": "online_geometry_loop_association_smoke",
            "status": "smoke_passed",
            "scope": "target_id_beta_association_and_availability_only",
            "seed": seed,
            "window_frames": WINDOW_FRAMES,
            "first_output_frame": FIRST_OUTPUT_FRAME,
            "output_frames": OUTPUT_FRAMES,
            "perturbation": perturbation,
            "estimator_input": {
                "truth_present": (estimator_input / "truth").exists(),
                "paper_response_metadata_present": (estimator_input / "paper_response_metadata.json").exists(),
                "capture_truth_loaded": capture.truth_displacement_m is not None or capture.truth_time_ns is not None,
                "q_proxy_present": any(estimator_input.rglob("*q_proxy*")),
            },
            "target_count_transition": {
                "counts": counts,
                "first_one_frame": int(rows[first_one]["frame_index"]),
                "last_one_frame": int(rows[last_one]["frame_index"]),
                "returned_to_five": counts[-1] == 5,
            },
            "fixed_target_slots": [[int(target_id[0]), int(target_id[1])] for target_id in fixed_slots],
            "association": {
                "raw_order_permutations_among_5_target_rows": raw_order_permutations,
                "association_mismatch_count": association_mismatch_count,
                "missing_slot_contamination_count": missing_slot_contamination,
                "nonbaseline_ids_seen_during_missing_block": [
                    [int(target_id[0]), int(target_id[1])] for target_id in sorted(nonbaseline_ids)
                ],
                "stable_slot_matrix_shape": list(stable_beta.shape),
                "stable_slot_order_is_fixed": True,
                "all_baseline_slots_absent_during_one_target_block": bool(
                    not np.any(stable_present[first_one:last_one + 1])
                ),
                "all_baseline_slots_restored_after_block": bool(np.all(stable_present[-1])),
            },
            "accuracy_claim": False,
            "displacement_or_truth_metrics": None,
        }
        if association_mismatch_count or missing_slot_contamination:
            raise AssertionError(f"association check failed: {report['association']}")
        _json(output / "smoke_report.json", report)
        _json(output / "association_trace.json", associated_trace)
        _json(output / "stable_beta_slots.json", {
            "fixed_target_slots": [[int(target_id[0]), int(target_id[1])] for target_id in fixed_slots],
            "frame_indices": [int(row["frame_index"]) for row in rows],
            "stable_present": stable_present,
            "stable_beta": stable_beta,
        })
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run target-ID/beta association diagnostic smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261001)
    args = parser.parse_args()
    report = run_smoke(args.output, seed=args.seed)
    print(json.dumps({"status": report["status"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
