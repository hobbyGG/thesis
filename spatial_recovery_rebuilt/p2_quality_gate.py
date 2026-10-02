"""Scratch-only P2 observable quality gate and truth-free smoke.

The retained thesis estimator is run against a capture package with ``truth/``
and ``paper_response_metadata.json`` removed.  Gate features are evaluated on
frames 0--199 only; the 200--399 half is used only by the post-run evaluator to
measure false accepts.  This deliberately keeps q_true/q_proxy out of the
estimator and out of threshold selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spatial_recovery_rebuilt import rebuild_validation as rv  # noqa: E402


CAL_FRAMES = 200
TEST_START = 200
RADAR_RATE_HZ = 100.0
WARM_S = 0.20

# These limits are registered before the smoke is scored.  They are derived
# from calibration/dev observables and engineering units, never from q_true,
# q_proxy, or frozen-test errors.
THRESHOLDS = {
    "excitation_proxy_std_floor_rad": 0.012,
    "corrected_weighted_residual_rms_max_rad": 0.020,
    "primary_fit_r2_floor": 0.80,
    "iq_snr_floor_db": 20.0,
    "cross_channel_abs_corr_floor": 0.80,
    "beta_abs_cos_floor": 0.50,
    "false_accept_rmse_max_m": 1.0e-5,
}


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _finite_median(value: np.ndarray) -> float:
    x = np.asarray(value, dtype=float)
    x = x[np.isfinite(x)]
    return float(np.median(x)) if x.size else float("nan")


def _structural_phase(result: np.lib.npyio.NpzFile) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return beta-signed structural phase and its common calibration signal."""
    angles = np.asarray(result["target_angle_deg"], dtype=float)
    beta_signed = 1.0 / np.cos(np.deg2rad(angles))
    phase = np.asarray(result["los_corrected_phase_rad"], dtype=float)
    # The retained route records one frozen beta per target.  Remove each
    # target's calibration bias before building the leave-one-out common mode.
    centered = phase - np.nanmedian(phase[:, :CAL_FRAMES], axis=1, keepdims=True)
    structural = beta_signed[:, None] * centered
    common = np.nanmedian(structural[:, :CAL_FRAMES], axis=0)
    return structural, common, beta_signed


def _fit_r2(y: np.ndarray, x: np.ndarray) -> float:
    valid = np.isfinite(y) & np.isfinite(x)
    if int(np.count_nonzero(valid)) < 4:
        return float("nan")
    yy, xx = y[valid], x[valid]
    if np.std(yy) <= 1.0e-12 or np.std(xx) <= 1.0e-12:
        return float("nan")
    design = np.column_stack((np.ones(xx.size), xx))
    coef, *_ = np.linalg.lstsq(design, yy, rcond=None)
    pred = design @ coef
    denom = float(np.sum((yy - np.mean(yy)) ** 2))
    return float(1.0 - np.sum((yy - pred) ** 2) / denom) if denom > 0 else float("nan")


def _corrected_residual(structural: np.ndarray, result: np.lib.npyio.NpzFile) -> float:
    common = np.nanmedian(structural[:, :CAL_FRAMES], axis=0)
    residual = structural[:, :CAL_FRAMES] - common[None, :]
    r = np.asarray(result["r_theta_history"], dtype=float)[:, :CAL_FRAMES]
    weights = 1.0 / np.maximum(r, 1.0e-4)
    finite = np.isfinite(residual) & np.isfinite(weights)
    numerator = np.sum(np.where(finite, weights * residual * residual, 0.0), axis=0)
    denominator = np.sum(np.where(finite, weights, 0.0), axis=0)
    per_frame = np.sqrt(np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0))
    return float(np.sqrt(np.nanmean(per_frame * per_frame))) if np.any(np.isfinite(per_frame)) else float("nan")


def _iq_snr_and_channel_corr(package: Path, result: np.lib.npyio.NpzFile) -> tuple[float, float]:
    manifest = json.loads((package / "radar/algorithm_input/manifest.json").read_text(encoding="utf-8"))
    radar = manifest["radar"]
    adc = np.load(package / "radar/algorithm_input" / manifest["arrays"]["adc_cube"]["file"], allow_pickle=False)
    spectrum = np.fft.fft(np.asarray(adc[:CAL_FRAMES], dtype=np.complex128), axis=-1)
    resolution = float(radar["range_resolution_m"])
    bins = np.rint(np.asarray(result["target_range_m"], dtype=float) / resolution).astype(int)
    bins = np.clip(bins, 0, spectrum.shape[-1] - 1)
    noise_mask = np.ones(spectrum.shape[-1], dtype=bool)
    for b in bins:
        noise_mask[max(0, int(b) - 3):min(spectrum.shape[-1], int(b) + 4)] = False
    noise = np.median(np.abs(spectrum[..., noise_mask]), axis=-1)
    snr_db = []
    corr = []
    for b in bins:
        signal = np.abs(spectrum[:, :, b])
        floor = max(float(np.median(noise)), 1.0e-15)
        snr_db.append(20.0 * np.log10(max(float(np.median(signal)), 1.0e-15) / floor))
        phase = np.unwrap(np.angle(spectrum[:, :, b]), axis=0)
        phase = phase - np.mean(phase, axis=0, keepdims=True)
        pairwise = []
        for i in range(8):
            for j in range(i):
                if np.std(phase[:, i]) > 1.0e-12 and np.std(phase[:, j]) > 1.0e-12:
                    pairwise.append(abs(float(np.corrcoef(phase[:, i], phase[:, j])[0, 1])))
        corr.append(float(np.median(pairwise)) if pairwise else float("nan"))
    return _finite_median(np.asarray(snr_db)), _finite_median(np.asarray(corr))


def evaluate_gate(package: Path, result_path: Path) -> dict[str, object]:
    result = np.load(result_path, allow_pickle=False)
    structural, common, beta_signed = _structural_phase(result)
    angles = np.asarray(result["target_angle_deg"], dtype=float)
    cos_theta = np.cos(np.deg2rad(angles))
    beta_reported = np.asarray(result["beta_hat"], dtype=float)
    beta_consistent = bool(
        beta_signed.size > 0
        and np.all(np.isfinite(beta_signed))
        and np.all(np.isfinite(beta_reported))
        and np.allclose(beta_reported, beta_signed, rtol=2.0e-3, atol=2.0e-3)
    )
    beta_ok = bool(
        beta_consistent
        and np.all(cos_theta > 0.0)  # positive mounting convention
        and np.all(np.abs(cos_theta) >= THRESHOLDS["beta_abs_cos_floor"])
    )

    acceleration = np.load(
        package / "adxl355/algorithm_input/acceleration_mps2.npy", allow_pickle=False
    )[: CAL_FRAMES * 10, 0]
    # Observable radar excitation proxy: robust median target structural-phase
    # standard deviation on calibration.  This does not use ADXL truth or a
    # requested motion label, and is deliberately frozen before the test half.
    excitation_by_target = np.nanstd(structural[:, :CAL_FRAMES], axis=1)
    excitation_proxy = _finite_median(excitation_by_target)
    # Retain the ADXL statistic for diagnostics only; it is not used to tune
    # or accept this gate because its synthetic white noise dominates 5 um.
    adxl_std = float(np.std(acceleration - np.median(acceleration)))
    fit_r2 = []
    for i in range(structural.shape[0]):
        others = np.delete(structural[:, :CAL_FRAMES], i, axis=0)
        loo = np.nanmedian(others, axis=0) if others.size else common
        fit_r2.append(_fit_r2(structural[i, :CAL_FRAMES], loo))
    primary_r2 = _finite_median(np.asarray(fit_r2))
    residual_rms = _corrected_residual(structural, result)
    snr_db, channel_corr = _iq_snr_and_channel_corr(package, result)

    checks = {
        "signed_beta": beta_ok,
        "excitation": bool(np.isfinite(excitation_proxy) and excitation_proxy >= THRESHOLDS["excitation_proxy_std_floor_rad"]),
        "corrected_residual": bool(np.isfinite(residual_rms) and residual_rms <= THRESHOLDS["corrected_weighted_residual_rms_max_rad"]),
        "primary_fit_r2": bool(np.isfinite(primary_r2) and primary_r2 >= THRESHOLDS["primary_fit_r2_floor"]),
        "iq_snr": bool(np.isfinite(snr_db) and snr_db >= THRESHOLDS["iq_snr_floor_db"]),
        "cross_channel_consistency": bool(np.isfinite(channel_corr) and channel_corr >= THRESHOLDS["cross_channel_abs_corr_floor"]),
    }
    return {
        "accepted": bool(all(checks.values())),
        "checks": checks,
        "features_calibration": {
            "beta_signed": beta_signed.tolist(),
            "beta_reported": beta_reported.tolist(),
            "target_angle_deg": angles.tolist(),
            "excitation_proxy_std_rad": excitation_proxy,
            "excitation_proxy_std_by_target_rad": excitation_by_target.tolist(),
            "adxl_calibration_std_mps2_diagnostic": adxl_std,
            "corrected_weighted_residual_rms_rad": residual_rms,
            "primary_fit_metric": "median_leave_one_target_out_R2",
            "primary_fit_r2": primary_r2,
            "fit_r2_by_target": fit_r2,
            "iq_snr_median_db": snr_db,
            "cross_channel_abs_corr_median": channel_corr,
        },
        "gate_data_scope": {
            "decision_frames": [0, CAL_FRAMES - 1],
            "test_frames_not_used_for_decision": True,
            "truth_used_by_estimator": False,
            "q_proxy_used_by_estimator": False,
            "signed_beta_convention": "beta_signed=1/cos(theta), positive mounting means cos(theta)>0",
        },
    }


def _truth_free(package: Path) -> None:
    shutil.rmtree(package / "truth", ignore_errors=True)
    metadata = package / "paper_response_metadata.json"
    if metadata.exists():
        metadata.unlink()
    manifest_path = package / "radar/algorithm_input/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("source", None)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _postrun_rmse(package_truth: Path, result_path: Path) -> float:
    result = np.load(result_path, allow_pickle=False)
    q = np.load(package_truth / "displacement_m.npy", allow_pickle=False)
    qt = np.load(package_truth / "time_ns.npy", allow_pickle=False).astype(float)
    rt = np.asarray(result["radar_time_ns"], dtype=float)
    truth = np.interp(rt, qt, q)
    elapsed = (rt - rt[0]) * 1.0e-9
    warm = elapsed <= WARM_S
    reference = float(np.mean(truth[warm]))
    return float(np.sqrt(np.mean((result["q_hat_m"][TEST_START:] - (truth - reference)[TEST_START:]) ** 2)))


def run_smoke(output: Path, seeds: tuple[int, ...] = (20261001, 20261002)) -> dict[str, object]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    # The package builder stages under /tmp and uses rename; keep the temporary
    # work tree on that filesystem so this scratch runner is portable across
    # managed workspace mounts.
    work = Path(tempfile.mkdtemp(prefix="p2-quality-gate-"))
    for stratum_index, (name, rms_mm) in enumerate(rv.STRATA):
        for seed_offset, seed in enumerate(seeds):
            trial_id = f"{name}__seed{seed}"
            trial_dir = work / trial_id
            capture = trial_dir / "capture"
            trial_dir.mkdir(parents=True)
            rv._write_scratch_package(capture, stratum_name=name, requested_rms_mm=rms_mm, seed=seed)
            # Keep an isolated post-run reference, then make estimator input
            # truth-free before invoking the current route.
            truth_copy = trial_dir / "truth_eval"
            shutil.copytree(capture / "truth", truth_copy)
            _truth_free(capture)
            result_path = trial_dir / "algorithm_result.npz"
            completed = subprocess.run(
                [sys.executable, "-m", "algorithm.run", "--input", str(capture), "--output", str(result_path)],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            summary_path = result_path.with_suffix(".json")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            gate = evaluate_gate(capture, result_path)
            rmse_m = _postrun_rmse(truth_copy, result_path)
            row = {
                "trial_id": trial_id,
                "stratum": name,
                "seed": seed,
                "gate_accepted": gate["accepted"],
                "false_accept": bool(gate["accepted"] and rmse_m > THRESHOLDS["false_accept_rmse_max_m"]),
                "abstention_as_failure_success": bool(gate["accepted"] and rmse_m <= THRESHOLDS["false_accept_rmse_max_m"]),
                "frozen_test_rmse_m_postrun": rmse_m,
                "result_contains_truth": bool("truth_rmse_m" in summary or "truth_displacement_m" in np.load(result_path).files),
                "estimator_stdout": completed.stdout.strip(),
                "gate": gate,
            }
            rows.append(row)
            shutil.rmtree(trial_dir, ignore_errors=True)
    # Summaries are intentionally compact and contain no truth arrays.
    accepted = [r for r in rows if r["gate_accepted"]]
    false_accepts = [r for r in rows if r["false_accept"]]
    by_stratum: dict[str, dict[str, object]] = {}
    for name, _ in rv.STRATA:
        group = [r for r in rows if r["stratum"] == name]
        by_stratum[name] = {
            "trials": len(group),
            "accepted": int(sum(bool(r["gate_accepted"]) for r in group)),
            "coverage": float(np.mean([bool(r["gate_accepted"]) for r in group])) if group else 0.0,
            "false_accepts": int(sum(bool(r["false_accept"]) for r in group)),
            "rmse_um_accepted_only": [float(r["frozen_test_rmse_m_postrun"] * 1.0e6) for r in group if r["gate_accepted"]],
        }
    report = {
        "schema": "spatial_recovery_rebuilt.p2_quality_gate_smoke",
        "status": "smoke_complete",
        "claims_parity_with_lost_workspace": False,
        "protocol": {
            "calibration_frames": [0, CAL_FRAMES - 1],
            "frozen_test_frames": [TEST_START, 399],
            "decision_uses_test": False,
            "fence_caveat": "Gate decisions are calibration-only, but retained RA geometry/selection currently uses full 400-frame ADC window; strict calibration-only P2 deployment remains blocked.",
            "thresholds": THRESHOLDS,
            "features": ["signed_beta", "excitation_proxy_std", "corrected_weighted_residual", "median_leave_one_target_out_R2", "IQ_SNR", "cross_channel_abs_corr"],
            "estimator_input": "radar/algorithm_input + adxl355/algorithm_input + sync only; truth and q_proxy removed",
            "false_accept_definition": "gate accepted and post-run frozen-test RMSE > 0.010 mm",
            "abstention_as_failure": True,
        },
        "trials": len(rows),
        "coverage": float(len(accepted) / len(rows)) if rows else 0.0,
        "accepted": len(accepted),
        "abstentions": len(rows) - len(accepted),
        "false_accepts": len(false_accepts),
        "all_trial_success_abstention_as_failure": float(sum(bool(r["abstention_as_failure_success"]) for r in rows) / len(rows)) if rows else 0.0,
        "by_stratum": by_stratum,
        "truth_is_postrun_only": True,
        "trial_rows": rows,
    }
    _json(output / "p2_quality_gate_report.json", report)
    _json(output / "p2_quality_gate_protocol.json", report["protocol"])
    shutil.rmtree(work, ignore_errors=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not args.smoke:
        parser.error("only --smoke is supported")
    report = run_smoke(args.output)
    print(json.dumps({k: report[k] for k in ("status", "trials", "coverage", "accepted", "abstentions", "false_accepts", "all_trial_success_abstention_as_failure")}, indent=2))


if __name__ == "__main__":
    main()
