"""Run the rebuilt 40-seed-by-stratum validation without touching smoke output.

The runner is intentionally a scratch-only driver.  It retains compact
per-trial records and removes each ~112 MB capture package after the result is
summarized, so an interrupted run can resume from ``progress.json``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rebuild_validation import (  # noqa: E402
    CALIBRATION_FRAMES,
    DURATION_S,
    RADAR_FRAMES,
    SEED_VALUES,
    STRATA,
    _json,
    _write_scratch_package,
    freeze_guards,
    git_status,
    run_algorithm,
    source_evidence,
    verify_frozen_test,
    verify_package,
)


SEEDS = tuple(range(7200, 7240))
TOTAL_TRIALS = len(SEEDS) * len(STRATA)
TEST_SLICE = slice(CALIBRATION_FRAMES, RADAR_FRAMES)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trial_id(stratum: str, seed: int) -> str:
    return f"{stratum}__seed{seed:04d}"


def _copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        shutil.copy2(source, destination)


def _test_metrics(result_path: Path, summary: dict[str, object], accepted: bool) -> dict[str, object]:
    result = np.load(result_path, allow_pickle=False)
    q_hat = np.asarray(result["q_hat_m"], dtype=float)
    truth = np.asarray(result["truth_displacement_m"], dtype=float)
    if q_hat.shape != truth.shape or q_hat.size != RADAR_FRAMES:
        raise RuntimeError(f"unexpected result shapes q_hat={q_hat.shape} truth={truth.shape}")
    test_q = q_hat[TEST_SLICE]
    test_truth = truth[TEST_SLICE]
    all_finite = bool(np.all(np.isfinite(test_q)) and np.all(np.isfinite(test_truth)))
    # Match algorithm.run's truth centering exactly: its elapsed-time mask
    # includes the sample on the 0.20 s boundary (21 samples at 100 Hz).
    elapsed_s = np.asarray(result["time_s"], dtype=float)
    warm_mask = elapsed_s <= 0.20
    reference = float(np.mean(truth[warm_mask]))
    error = test_q - (test_truth - reference)
    finite_error = error[np.isfinite(error)]
    test_rmse = float(np.sqrt(np.mean(finite_error * finite_error))) if finite_error.size else None
    coverage = float(finite_error.size / test_q.size)
    np.save(result_path.with_name("test_errors.npy"), finite_error, allow_pickle=False)
    accepted_finite = bool(accepted and all_finite)
    return {
        "full_rmse_m": summary.get("truth_rmse_frame_grid_m"),
        "test_rmse_m": test_rmse,
        "test_sample_count": int(test_q.size),
        "finite_test_samples": int(finite_error.size),
        "test_sample_coverage": coverage if accepted else 0.0,
        "accepted_finite_test": accepted_finite,
        "abstention_as_failure_success": accepted_finite,
    }


def _run_trial(output: Path, stratum_name: str, requested_rms_mm: float, seed: int) -> dict[str, object]:
    trial_id = _trial_id(stratum_name, seed)
    trial_dir = output / "trials" / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    trial_record_path = trial_dir / "trial.json"
    if trial_record_path.is_file():
        existing = json.loads(trial_record_path.read_text(encoding="utf-8"))
        if existing.get("status") in {"accepted", "rejected", "error"} and existing.get("complete"):
            return existing

    work_dir = output / "_work" / trial_id
    package = work_dir / "capture"
    algorithm_result = trial_dir / "algorithm_result.npz"
    started = time.monotonic()
    record: dict[str, object] = {
        "schema": "spatial_recovery_rebuilt.trial",
        "protocol": "rebuilt_protocol",
        "claims_parity_with_lost_workspace": False,
        "trial_id": trial_id,
        "stratum": stratum_name,
        "requested_q_true_rms_mm": requested_rms_mm,
        "seed": seed,
        "radar_frames": RADAR_FRAMES,
        "radar_rate_hz": 100.0,
        "calibration_frames": CALIBRATION_FRAMES,
        "frozen_test_frames": RADAR_FRAMES - CALIBRATION_FRAMES,
        "started_at": _now(),
    }
    try:
        realized = _write_scratch_package(
            package,
            stratum_name=stratum_name,
            requested_rms_mm=requested_rms_mm,
            seed=seed,
        )
        record["realized_rms"] = realized
        _json(trial_dir / "rms_log.json", realized)

        contract_error = None
        try:
            contract = verify_package(package)
            _json(trial_dir / "package_contract.json", contract)
        except Exception as exc:  # retain the reason and continue the matrix
            contract = None
            contract_error = f"package_contract:{type(exc).__name__}:{exc}"

        guard_error = None
        frozen_result = None
        guards = None
        if contract_error is None:
            guards = freeze_guards(package)
            _copy_if_present(package / "guards.json", trial_dir / "guards.json")
            if not bool(guards.get("finite_calibration")):
                guard_error = "frozen_calibration_guard:non_finite_capture_array"
            else:
                try:
                    frozen_result = verify_frozen_test(package, guards)
                    _copy_if_present(package / "frozen_test_guard_result.json", trial_dir / "frozen_test_guard_result.json")
                except Exception as exc:
                    guard_error = f"frozen_test_guard:{type(exc).__name__}:{exc}"

        accepted = contract_error is None and guard_error is None
        record["package_contract"] = "passed" if contract_error is None else "rejected"
        record["frozen_guard"] = "passed" if guard_error is None and contract_error is None else "rejected"
        record["accepted"] = accepted
        rejection_reasons = [reason for reason in (contract_error, guard_error) if reason]
        record["rejection_reasons"] = rejection_reasons

        if accepted:
            algorithm = run_algorithm(package, algorithm_result)
            summary = algorithm["summary"]
            _json(trial_dir / "algorithm_summary.json", summary)
            record["algorithm"] = summary
            record["metrics"] = _test_metrics(algorithm_result, summary, accepted=True)
            record["status"] = "accepted"
        else:
            record["status"] = "rejected"
            record["metrics"] = {
                "full_rmse_m": None,
                "test_rmse_m": None,
                "test_sample_count": RADAR_FRAMES - CALIBRATION_FRAMES,
                "finite_test_samples": 0,
                "test_sample_coverage": 0.0,
                "accepted_finite_test": False,
                "abstention_as_failure_success": False,
            }
    except Exception as exc:
        record["status"] = "error"
        record["accepted"] = False
        record["rejection_reasons"] = [f"trial_error:{type(exc).__name__}:{exc}"]
        record["metrics"] = {
            "full_rmse_m": None,
            "test_rmse_m": None,
            "test_sample_count": RADAR_FRAMES - CALIBRATION_FRAMES,
            "finite_test_samples": 0,
            "test_sample_coverage": 0.0,
            "accepted_finite_test": False,
            "abstention_as_failure_success": False,
        }
    finally:
        if algorithm_result.is_file():
            algorithm_result.unlink()
        if work_dir.exists():
            shutil.rmtree(work_dir)

    record["duration_s"] = time.monotonic() - started
    record["completed_at"] = _now()
    record["complete"] = True
    _json(trial_record_path, record)
    return record


def _aggregate(records: list[dict[str, object]], output: Path) -> dict[str, object]:
    accepted = [record for record in records if record.get("accepted") is True]
    successful = [record for record in records if record.get("metrics", {}).get("abstention_as_failure_success") is True]
    finite_errors: list[float] = []
    accepted_rms: list[float] = []
    for record in accepted:
        metrics = record.get("metrics", {})
        value = metrics.get("test_rmse_m")
        if isinstance(value, (int, float)) and np.isfinite(value):
            accepted_rms.append(float(value))
        # Equal frame weighting across accepted trials.
        result_path = output / "trials" / str(record["trial_id"]) / "test_errors.npy"
        if result_path.is_file():
            finite_errors.extend(np.load(result_path, allow_pickle=False).astype(float).tolist())
    pooled_accepted_rmse = (
        float(np.sqrt(np.mean(np.asarray(finite_errors) ** 2))) if finite_errors else None
    )
    reason_counts = Counter(
        reason
        for record in records
        for reason in record.get("rejection_reasons", [])
    )
    by_stratum: dict[str, dict[str, object]] = {}
    for stratum_name, _ in STRATA:
        rows = [record for record in records if record.get("stratum") == stratum_name]
        accepted_rows = [record for record in rows if record.get("accepted") is True]
        rms = [record["metrics"]["test_rmse_m"] for record in accepted_rows if record["metrics"].get("test_rmse_m") is not None]
        by_stratum[stratum_name] = {
            "trials": len(rows),
            "accepted": len(accepted_rows),
            "acceptance_coverage": len(accepted_rows) / len(rows) if rows else 0.0,
            "accepted_only_rmse_m_mean": float(np.mean(rms)) if rms else None,
            "abstention_as_failure_success_rate": sum(bool(row["metrics"].get("abstention_as_failure_success")) for row in rows) / len(rows) if rows else 0.0,
        }
    total = len(records)
    finite_samples = sum(int(record.get("metrics", {}).get("finite_test_samples", 0)) for record in records)
    possible_samples = total * (RADAR_FRAMES - CALIBRATION_FRAMES)
    return {
        "schema": "spatial_recovery_rebuilt.matrix_summary",
        "protocol": "rebuilt_protocol",
        "claims_parity_with_lost_workspace": False,
        "seed_range": [SEEDS[0], SEEDS[-1]],
        "strata": [name for name, _ in STRATA],
        "trial_count": total,
        "expected_trial_count": TOTAL_TRIALS,
        "accepted_trials": len(accepted),
        "rejected_or_error_trials": total - len(accepted),
        "acceptance_coverage": len(accepted) / total if total else 0.0,
        "sample_coverage_with_abstentions_as_zero": finite_samples / possible_samples if possible_samples else 0.0,
        "accepted_only_rmse_m_pooled": pooled_accepted_rmse,
        "accepted_only_rmse_m_mean_of_trials": float(np.mean(accepted_rms)) if accepted_rms else None,
        "abstention_as_failure_successes": len(successful),
        "abstention_as_failure_success_rate": len(successful) / total if total else 0.0,
        "rejection_reason_counts": dict(reason_counts),
        "by_stratum": by_stratum,
        "definition": {
            "acceptance": "package contract and calibration-frozen observable-data guards pass; then retained algorithm completes",
            "sample_coverage": "finite q_hat test samples divided by all possible test samples; rejected trials contribute zero",
            "accepted_only_rmse": "pooled frozen-test RMSE over accepted trials after the algorithm's 0.20 s truth reference centering",
            "abstention_as_failure_success": "accepted trial with finite frozen-test q_hat; every rejection/abstention counts as failure",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run rebuilt 7200-7239 validation matrix")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    if output.resolve() == (SCRATCH / "smoke").resolve():
        parser.error("refusing to overwrite the smoke directory")
    output.mkdir(parents=True, exist_ok=True)
    (output / "trials").mkdir(exist_ok=True)
    (output / "_work").mkdir(exist_ok=True)
    _json(output / "protocol.json", json.loads((SCRATCH / "protocol.json").read_text(encoding="utf-8")))
    manifest = {
        "schema": "spatial_recovery_rebuilt.matrix_run",
        "protocol": "rebuilt_protocol",
        "claims_parity_with_lost_workspace": False,
        "seed_values": list(SEEDS),
        "protocol_seed_values": list(SEED_VALUES),
        "seed_override": "effective seeds 7200-7239 replace protocol example seeds for this rebuilt run",
        "strata": [{"name": name, "requested_q_true_rms_mm": rms} for name, rms in STRATA],
        "trial_count": TOTAL_TRIALS,
        "started_at": _now(),
        "source_evidence": source_evidence(),
        "status": "running",
    }
    _json(output / "run_manifest.json", manifest)

    records: list[dict[str, object]] = []
    completed = 0
    try:
        for stratum_name, requested_rms_mm in STRATA:
            for seed in SEEDS:
                record = _run_trial(output, stratum_name, requested_rms_mm, seed)
                records.append(record)
                completed += 1
                if completed == 1 or completed % 10 == 0 or completed == TOTAL_TRIALS:
                    print(f"completed {completed}/{TOTAL_TRIALS}: {record['trial_id']} status={record['status']}", flush=True)
                _json(output / "progress.json", {
                    "status": "running",
                    "completed_trials": completed,
                    "expected_trials": TOTAL_TRIALS,
                    "last_trial": record["trial_id"],
                    "updated_at": _now(),
                })
    except KeyboardInterrupt:
        _json(output / "progress.json", {
            "status": "interrupted",
            "completed_trials": completed,
            "expected_trials": TOTAL_TRIALS,
            "updated_at": _now(),
        })
        raise

    summary = _aggregate(records, output)
    summary["completed_at"] = _now()
    _json(output / "summary.json", summary)
    manifest["status"] = "completed"
    manifest["completed_at"] = summary["completed_at"]
    manifest["git_status_after"] = git_status()
    _json(output / "run_manifest.json", manifest)
    _json(output / "progress.json", {
        "status": "completed",
        "completed_trials": TOTAL_TRIALS,
        "expected_trials": TOTAL_TRIALS,
        "updated_at": _now(),
    })
    print(json.dumps({
        "status": "completed",
        "output": str(output),
        "trial_count": summary["trial_count"],
        "accepted_trials": summary["accepted_trials"],
        "acceptance_coverage": summary["acceptance_coverage"],
        "accepted_only_rmse_m_pooled": summary["accepted_only_rmse_m_pooled"],
        "abstention_as_failure_success_rate": summary["abstention_as_failure_success_rate"],
    }, indent=2))


if __name__ == "__main__":
    main()
