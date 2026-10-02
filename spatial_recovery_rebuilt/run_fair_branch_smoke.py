"""Run the pre-registered fair-branch smoke only.

The current checkout contains the retained RA estimator but no RO-all-channel
adapter.  This driver therefore fails closed for RO while still exercising the
shared package, calibration-frozen guards, input hashes, and metric contract.
It never passes the truth directory to an estimator process.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rebuild_validation import (  # noqa: E402
    CALIBRATION_FRAMES,
    RADAR_FRAMES,
    STRATA,
    _json,
    _write_scratch_package,
    freeze_guards,
    git_status,
    verify_frozen_test,
    verify_package,
)

PROTOCOL_PATH = SCRATCH / "fair_branch_protocol.json"
TRUTH_DIR = "truth"
BRANCHES = ("ro_all_channel", "ra")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(_sha256_file(path).encode("ascii"))
    return digest.hexdigest()


def _copy_estimator_package(source: Path, destination: Path) -> None:
    """Copy capture inputs while excluding all truth/evaluator material."""
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(TRUTH_DIR))
    metadata = destination / "paper_response_metadata.json"
    if metadata.exists():
        metadata.unlink()


def _input_hashes(package: Path) -> tuple[str, str]:
    adc = package / "radar" / "algorithm_input" / "adc_cube.npy"
    adxl = package / "adxl355" / "algorithm_input" / "acceleration_mps2.npy"
    return _sha256_file(adc), _sha256_file(adxl)


def _evaluate(q_hat: np.ndarray, package: Path) -> float:
    truth = np.load(package / TRUTH_DIR / "displacement_m.npy", allow_pickle=False)
    truth_time = np.load(package / TRUTH_DIR / "time_ns.npy", allow_pickle=False)
    # The RA estimator is frame-mode, so use its frame time grid and the same
    # physical 0.20 s reference used by the retained experiment.
    timeline = json.loads((package / "sync" / "timeline.json").read_text(encoding="utf-8"))
    radar_time = np.load(package / "sync" / timeline["adc_array"]["file"], allow_pickle=False)
    time_s = (radar_time.astype(float) - float(radar_time[0])) * 1.0e-9
    aligned_truth = np.interp(radar_time.astype(float), truth_time.astype(float), truth)
    reference = float(np.mean(aligned_truth[time_s <= 0.20]))
    error = np.asarray(q_hat, dtype=float) - (aligned_truth - reference)
    test_error = error[CALIBRATION_FRAMES:RADAR_FRAMES]
    if test_error.size != RADAR_FRAMES - CALIBRATION_FRAMES or not np.all(np.isfinite(test_error)):
        raise ValueError("non-finite or incomplete frozen-test estimate")
    return float(np.sqrt(np.mean(test_error * test_error)))


def _base_record(
    *,
    trial_id: str,
    stratum: str,
    seed: int,
    branch_id: str,
    package_hash: str,
    adc_hash: str,
    adxl_hash: str,
    guards_hash: str,
    contract: dict[str, object],
    guards: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": "spatial_recovery_rebuilt.fair_branch_trial",
        "trial_id": trial_id,
        "stratum": stratum,
        "seed": seed,
        "branch_id": branch_id,
        "status": "pending",
        "shared_package_sha256": package_hash,
        "adc_input_sha256": adc_hash,
        "adxl_input_sha256": adxl_hash,
        "guards_sha256": guards_hash,
        "package_contract": contract,
        "guard_result": guards,
        "radar_frames": RADAR_FRAMES,
        "radar_rate_hz": 100.0,
        "calibration_frames": CALIBRATION_FRAMES,
        "frozen_test_frames": RADAR_FRAMES - CALIBRATION_FRAMES,
        "adxl_samples": 4000,
        "adxl_rate_hz": 1000.0,
        "estimator_input_manifest": [
            "radar/algorithm_input/adc_cube.npy",
            "radar/algorithm_input/chirp_cube.npy",
            "radar/algorithm_input/manifest.json",
            "adxl355/algorithm_input/acceleration_mps2.npy",
            "adxl355/algorithm_input/estimated_sample_monotonic_ns.npy",
            "sync/manifest.json",
            "sync/timeline.json",
            "sync/*.npy",
        ],
        "truth_used_by_estimator": False,
        "q_proxy_used_by_estimator": False,
        "actual_route": None,
        "beta_source": None,
        "target_count": None,
        "accepted": False,
        "rmse_m": None,
        "primary_success": False,
        "coverage": False,
        "abstention": True,
    }


def _run_ra(package: Path, output_dir: Path, record: dict[str, object], threshold_m: float) -> None:
    """Run RA on an input-only copy and evaluate against the separate package truth."""
    from algorithm.config import AlgorithmConfig
    from algorithm.io import build_algorithm_inputs, load_capture_package
    from algorithm.kalman import run_fixed_beta_kalman

    with tempfile.TemporaryDirectory(prefix="fair-ra-input-") as temporary:
        estimator_package = Path(temporary) / "capture"
        _copy_estimator_package(package, estimator_package)
        capture = load_capture_package(estimator_package)
        radar, acceleration, targets, radar_rate = build_algorithm_inputs(capture, radar_mode="frame")
        result = run_fixed_beta_kalman(radar, acceleration, AlgorithmConfig(sample_rate_hz=float(radar_rate)))
        q_hat = np.asarray(result.q_hat_m, dtype=float)
        np.savez(output_dir / "ra_result.npz", q_hat_m=q_hat, beta_hat=result.beta_hat,
                 selected_target_indices=radar.selected_indices)

        rmse_m = _evaluate(q_hat, package)
        actual_route = f"{result.method_name}/{radar.extra['radar_mode']}"
        selected_count = int(radar.selected_indices.size)
        detection = radar.extra.get("detection", {})
        record.update({
            "status": "completed",
            "actual_route": actual_route,
            "beta_source": str(result.extra.get("beta_source")),
            "target_count": selected_count,
            "detected_candidate_count": int(detection.get("candidate_count", selected_count)),
            "method": result.method_name,
            "radar_mode": str(radar.extra["radar_mode"]),
            "rmse_m": rmse_m,
            "accepted": True,
            "coverage": True,
            "abstention": False,
            "primary_success": bool(np.isfinite(rmse_m) and rmse_m <= threshold_m),
            "truth_evaluation": "post_run_only_outside_estimator_input_copy",
        })


def _run_ro(record: dict[str, object]) -> None:
    """Fail closed: the current checkout has no RO-all-channel adapter."""
    record.update({
        "status": "blocked_missing_route",
        "blocker": "current checkout exposes no RO-all-channel estimator; no RA fallback was attempted",
        "actual_route": None,
        "beta_source": None,
        "target_count": None,
        "primary_success": False,
        "coverage": False,
        "abstention": True,
    })


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "trial_id", "stratum", "seed", "branch_id", "status", "actual_route",
        "beta_source", "target_count", "detected_candidate_count", "accepted",
        "rmse_m", "primary_success", "coverage", "abstention",
        "shared_package_sha256", "adc_input_sha256", "adxl_input_sha256", "guards_sha256",
        "truth_used_by_estimator", "q_proxy_used_by_estimator",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fair branch 2-seed-per-scenario smoke only")
    parser.add_argument("--output", type=Path, default=SCRATCH / "fair_branch_smoke")
    args = parser.parse_args()
    output = args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing smoke output: {output}")
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    output.mkdir(parents=True)
    (output / "trials").mkdir()
    before = git_status()
    rows: list[dict[str, object]] = []
    scenario_defs = [(item["name"], float(item["requested_q_true_rms_mm"])) for item in protocol["smoke"]["scenarios"]]
    seeds = [int(value) for value in protocol["smoke"]["seed_values"]]
    threshold_m = float(protocol["metrics"]["primary"]["threshold_m"])
    _json(output / "run_manifest.json", {
        "schema": "spatial_recovery_rebuilt.fair_branch_smoke_run",
        "status": "running",
        "started_at": _now(),
        "protocol": str(PROTOCOL_PATH),
        "scenarios": scenario_defs,
        "seeds": seeds,
        "branches": list(BRANCHES),
        "full_matrix_started": False,
        "git_status_before": before,
        "protocol_sha256": _sha256_file(PROTOCOL_PATH),
        "source_sha256": {
            name: _sha256_file(ROOT / name) for name in (
                "paper_bridge_simulation/package_builder.py",
                "paper_bridge_simulation/response.py",
                "algorithm/io.py",
                "algorithm/run.py",
                "algorithm/frontend.py",
                "algorithm/selection.py",
                "algorithm/kalman.py",
            )
        },
    })

    for stratum, requested_rms_mm in scenario_defs:
        for seed in seeds:
            trial_id = f"{stratum}__seed{seed}"
            trial_dir = output / "trials" / trial_id
            trial_dir.mkdir()
            package = trial_dir / "shared_capture"
            realized = _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
            contract = verify_package(package)
            guards = freeze_guards(package)
            try:
                frozen = verify_frozen_test(package, guards)
                frozen_passed = True
            except Exception as exc:
                frozen = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
                frozen_passed = False
            guards_payload = {"guards": guards, "frozen_test": frozen}
            _json(trial_dir / "realized_rms.json", realized)
            _json(trial_dir / "guards.json", guards_payload)
            package_hash = _sha256_tree(package)
            adc_hash, adxl_hash = _input_hashes(package)
            guards_hash = _sha256_file(package / "guards.json")
            for branch_id in BRANCHES:
                branch_dir = trial_dir / branch_id
                branch_dir.mkdir()
                record = _base_record(
                    trial_id=trial_id, stratum=stratum, seed=seed, branch_id=branch_id,
                    package_hash=package_hash, adc_hash=adc_hash, adxl_hash=adxl_hash,
                    guards_hash=guards_hash, contract=contract, guards=guards_payload,
                )
                if not frozen_passed:
                    record["status"] = "guard_rejected"
                    record["blocker"] = "shared frozen-test guard rejected before branch execution"
                elif branch_id == "ro_all_channel":
                    _run_ro(record)
                else:
                    _run_ra(package, branch_dir, record, threshold_m)
                _json(branch_dir / "trial.json", record)
                rows.append(record)
            shutil.rmtree(package)

    # Pairwise and route-mixing audit.
    by_trial: dict[str, dict[str, dict[str, object]]] = {}
    for row in rows:
        by_trial.setdefault(str(row["trial_id"]), {})[str(row["branch_id"])] = row
    pair_checks = []
    for trial_id, pair in sorted(by_trial.items()):
        ro, ra = pair["ro_all_channel"], pair["ra"]
        pair_checks.append({
            "trial_id": trial_id,
            "same_shared_package": ro["shared_package_sha256"] == ra["shared_package_sha256"],
            "same_adc": ro["adc_input_sha256"] == ra["adc_input_sha256"],
            "same_adxl": ro["adxl_input_sha256"] == ra["adxl_input_sha256"],
            "same_guards": ro["guards_sha256"] == ra["guards_sha256"],
            "ro_has_no_ra_output": ro["actual_route"] is None and ro["target_count"] is None,
            "ra_not_labeled_ro": str(ra["actual_route"]).startswith("fixed_geometry_beta_structural_kalman/frame") or ra["status"] != "completed",
        })
    audit = {
        "schema": "spatial_recovery_rebuilt.fair_branch_route_audit",
        "expected_rows": int(protocol["smoke"]["expected_trial_count"]),
        "actual_rows": len(rows),
        "expected_shared_packages": len(scenario_defs) * len(seeds),
        "pair_checks": pair_checks,
        "all_shared_input_checks_pass": all(all(item[key] for key in ("same_shared_package", "same_adc", "same_adxl", "same_guards")) for item in pair_checks),
        "route_mixing_check_pass": all(item["ro_has_no_ra_output"] and item["ra_not_labeled_ro"] for item in pair_checks),
        "truth_q_proxy_input_check_pass": all(not row["truth_used_by_estimator"] and not row["q_proxy_used_by_estimator"] for row in rows),
        "ro_adapter_available": False,
        "full_matrix_started": False,
    }
    _json(output / "fair_branch_route_audit.json", audit)
    _write_csv(output / "fair_branch_smoke_trials.csv", rows)
    ra_rows = [row for row in rows if row["branch_id"] == "ra"]
    report = {
        "schema": "spatial_recovery_rebuilt.fair_branch_smoke_report",
        "protocol": str(PROTOCOL_PATH),
        "status": "smoke_complete_ro_blocked",
        "git_status_before": before,
        "git_status_after": git_status(),
        "claims_parity_with_lost_workspace": False,
        "trial_count": len(rows),
        "primary_success_count": sum(bool(row["primary_success"]) for row in rows),
        "all_trial_success_rate": sum(bool(row["primary_success"]) for row in rows) / len(rows),
        "by_branch": {
            branch_id: {
                "trials": sum(row["branch_id"] == branch_id for row in rows),
                "primary_success": sum(bool(row["primary_success"]) for row in rows if row["branch_id"] == branch_id),
                "coverage": sum(bool(row["coverage"]) for row in rows if row["branch_id"] == branch_id) / len([row for row in rows if row["branch_id"] == branch_id]),
                "abstention": sum(bool(row["abstention"]) for row in rows if row["branch_id"] == branch_id) / len([row for row in rows if row["branch_id"] == branch_id]),
                "accepted_only_rmse_m": [row["rmse_m"] for row in rows if row["branch_id"] == branch_id and row["rmse_m"] is not None],
                "accepted_only_rmse_m_mean": (
                    float(np.mean([row["rmse_m"] for row in rows if row["branch_id"] == branch_id and row["rmse_m"] is not None]))
                    if any(row["branch_id"] == branch_id and row["rmse_m"] is not None for row in rows) else None
                ),
                "metric_status": "estimable" if any(row["branch_id"] == branch_id and row["rmse_m"] is not None for row in rows) else "not_estimable_missing_route",
            } for branch_id in BRANCHES
        },
        "ra_route_values": sorted({row["actual_route"] for row in ra_rows if row["actual_route"] is not None}),
        "audit_file": "fair_branch_route_audit.json",
    }
    _json(output / "fair_branch_smoke_report.json", report)
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    manifest.update({"status": "completed", "completed_at": _now(), "git_status_after": git_status(),
                     "summary": "fair_branch_smoke_report.json"})
    _json(output / "run_manifest.json", manifest)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
