"""Strict P3 follow-up: two seeds x three strata, compact outputs only.

This scratch-only runner reuses calibration-frozen geometry but predeclares a
20-frame test warm-up: frames 200:219 initialize phase bias/R, and scoring is
only frames 220:399. The estimator copy excludes truth and metadata. Every
trial's raw package is deleted after its compact JSON is written.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "spatial_recovery_rebuilt" / "p3_fusion_docs"
SCRATCH = ROOT / "spatial_recovery_rebuilt" / "calibration_only"
# The package builder atomically replaces its staging directory. Keep staging
# and compact output on the same filesystem (some managed mounts differ from
# /tmp), while deleting each raw package after the trial.
TMPROOT = DOCS / "strict_followup" / "_tmp"
TMPROOT.mkdir(parents=True, exist_ok=True)
os.environ["TMPDIR"] = str(TMPROOT)
tempfile.tempdir = str(TMPROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRATCH) not in sys.path:
    sys.path.insert(0, str(SCRATCH))
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

from algorithm.config import AlgorithmConfig  # noqa: E402
from algorithm.io import load_capture_package  # noqa: E402
from algorithm.kalman import run_fixed_beta_kalman  # noqa: E402
from algorithm.types import RadarInput  # noqa: E402
from calibration_only_wrapper import _copy_estimator_package, build_calibration_only_inputs  # noqa: E402
from rebuild_validation import _write_scratch_package, freeze_guards, verify_frozen_test  # noqa: E402
from p3_fusion_ablation import (  # noqa: E402
    _calibration_strength,
    _run_common_with_diag,
    _verify_capture_no_truth,
)

CAL = 200
TEST = 200
WARMUP = 20
SCORE_START = CAL + WARMUP
SEEDS = (20261001, 20261002)
STRATA = (
    ("stationary", 0.0),
    ("low_motion_0p005mm", 0.005),
    ("low_motion_0p050mm", 0.05),
)


def _json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _scalar_radar(radar, idx: int, initial_r: float) -> RadarInput:
    return RadarInput(
        measured_beta=np.asarray(radar.measured_beta[idx:idx + 1], dtype=float),
        wrapped_phase_rad=np.asarray(radar.wrapped_phase_rad[idx:idx + 1], dtype=float),
        available_mask=np.asarray(radar.available_mask[idx:idx + 1], dtype=bool),
        selected_indices=np.asarray([0], dtype=int),
        initial_r=np.asarray([initial_r], dtype=float),
        selection_scores=np.asarray(radar.selection_scores[idx:idx + 1], dtype=float),
        extra=dict(radar.extra),
    )


def _score_tail(est: np.ndarray, truth: np.ndarray, truth_t: np.ndarray,
                full_radar_time_ns: np.ndarray) -> dict[str, float | int]:
    """Score test frames 220:399 after the predeclared 20-frame warm-up."""
    frame_time = np.asarray(full_radar_time_ns, dtype=float)
    truth_full = np.interp(frame_time, np.asarray(truth_t, dtype=float), np.asarray(truth, dtype=float))
    elapsed = frame_time - frame_time[0]
    reference = float(np.mean(truth_full[elapsed <= 0.20e9]))
    est = np.asarray(est, dtype=float)
    tail = est[WARMUP:]
    truth_tail = truth_full[SCORE_START:SCORE_START + tail.size] - reference
    error = tail - truth_tail
    finite = np.isfinite(error)
    if not np.any(finite):
        return {
            "score_frames": 0,
            "rmse_m": float("nan"), "mae_m": float("nan"), "bias_m": float("nan"),
            "std_m": float("nan"), "max_abs_m": float("nan"),
            "truth_rms_m": float(np.sqrt(np.mean(truth_tail * truth_tail))),
            "warm_reference_m": reference,
        }
    error = error[finite]
    return {
        "score_frames": int(error.size),
        "rmse_m": float(np.sqrt(np.mean(error * error))),
        "mae_m": float(np.mean(np.abs(error))),
        "bias_m": float(np.mean(error)),
        "std_m": float(np.std(error)),
        "max_abs_m": float(np.max(np.abs(error))),
        "truth_rms_m": float(np.sqrt(np.mean(truth_tail * truth_tail))),
        "warm_reference_m": reference,
    }


def _corr_matrix(innov: np.ndarray, start: int = WARMUP) -> tuple[list[list[float | None]], dict[str, float | int]]:
    """Pearson correlations across target innovations over scored test frames."""
    values = np.asarray(innov, dtype=float)[:, start:]
    count = values.shape[0]
    matrix: list[list[float | None]] = [[None for _ in range(count)] for _ in range(count)]
    pairs: list[float] = []
    for i in range(count):
        for j in range(count):
            x, y = values[i], values[j]
            finite = np.isfinite(x) & np.isfinite(y)
            if np.count_nonzero(finite) < 3:
                continue
            xf, yf = x[finite], y[finite]
            sx, sy = float(np.std(xf)), float(np.std(yf))
            if sx <= 0.0 or sy <= 0.0:
                continue
            c = float(np.corrcoef(xf, yf)[0, 1])
            matrix[i][j] = c
            if i < j:
                pairs.append(c)
    if pairs:
        summary = {
            "pair_count": int(len(pairs)),
            "median": float(np.median(pairs)),
            "mean": float(np.mean(pairs)),
            "min": float(np.min(pairs)),
            "max": float(np.max(pairs)),
            "absolute_median": float(np.median(np.abs(pairs))),
            "absolute_max": float(np.max(np.abs(pairs))),
        }
    else:
        summary = {
            "pair_count": 0, "median": float("nan"), "mean": float("nan"),
            "min": float("nan"), "max": float("nan"),
            "absolute_median": float("nan"), "absolute_max": float("nan"),
        }
    return matrix, summary


def _hash_source(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_trial(work: Path, output: Path, stratum: str, requested_rms_mm: float, seed: int) -> dict:
    package = work / "shared_capture"
    realized = _write_scratch_package(package, stratum_name=stratum, requested_rms_mm=requested_rms_mm, seed=seed)
    contract = _verify_capture_no_truth(package)
    guards = freeze_guards(package)
    frozen = verify_frozen_test(package, guards)
    with tempfile.TemporaryDirectory(prefix="p3-strict-estimator-") as td:
        estimator_package = Path(td) / "capture"
        _copy_estimator_package(package, estimator_package)
        capture = load_capture_package(estimator_package)
        radar, acceleration, geometry, radar_rate = build_calibration_only_inputs(capture)
        config = AlgorithmConfig(sample_rate_hz=float(radar_rate))
        common_diag = _run_common_with_diag(radar, acceleration, config)
        retained = run_fixed_beta_kalman(radar, acceleration, config)
        retained_delta = float(np.max(np.abs(common_diag["q_hat_m"] - retained.q_hat_m)))
        strength = _calibration_strength(geometry)
        order = np.argsort(-strength, kind="stable")
        single_idx = int(order[0])
        independent_config = AlgorithmConfig(sample_rate_hz=float(radar_rate), cold_start_r_mode="fixed")
        independent_results = []
        for idx in range(radar.wrapped_phase_rad.shape[0]):
            one = run_fixed_beta_kalman(
                _scalar_radar(radar, idx, float(common_diag["initial_r"][idx])),
                acceleration,
                independent_config,
            )
            independent_results.append(one)
        single_result = independent_results[single_idx]
        # Truth is first opened only after every estimator output is complete.
        truth = np.load(package / "truth" / "displacement_m.npy", allow_pickle=False)
        truth_t = np.load(package / "truth" / "time_ns.npy", allow_pickle=False)
        full_radar_time = np.load(package / "sync" / "radar_adc_sample_monotonic_ns.npy", allow_pickle=False)
        score = {
            "single_target": _score_tail(single_result.q_hat_m, truth, truth_t, full_radar_time),
            "common_state_fusion": _score_tail(common_diag["q_hat_m"], truth, truth_t, full_radar_time),
            "independent_per_target": [
                _score_tail(one.q_hat_m, truth, truth_t, full_radar_time) for one in independent_results
            ],
        }
        common_corr_matrix, common_corr_summary = _corr_matrix(common_diag["innovation"], WARMUP)
        independent_innov = np.concatenate([
            np.asarray(one.innovation_rad, dtype=float) for one in independent_results
        ], axis=0)
        independent_corr_matrix, independent_corr_summary = _corr_matrix(independent_innov, WARMUP)
    result = {
        "schema": "p3_common_latent_structural_state_fusion_strict_followup_trial",
        "status": "completed",
        "trial": {"stratum": stratum, "requested_q_true_rms_mm": requested_rms_mm, "seed": seed, "realized": realized},
        "protocol": {
            "radar_frames": 400,
            "calibration_frames": [0, 199],
            "test_frames": [200, 399],
            "score_frames": [220, 399],
            "test_warmup_frames": [200, 219],
            "score_rule": "discard first 20 test frames used by retained cold-start bias/R initialization; score remaining 180 frames",
            "geometry_and_selection_source": "calibration frames 0:200 only",
            "bias_and_initial_R_source": "test warm-up frames 200:220 in retained API",
            "strict_calibration_only_initialization": False,
            "estimator_truth_present": False,
            "truth_role": "post_run_scoring_only",
            "single_target_rule": "largest median calibration complex-return magnitude",
            "independent_rule": "one retained filter per target with common route initial R_i; fixed cold-start mode and retained posterior R adaptation",
            "common_rule": "one shared [Theta, Theta_dot] precision-weighted state with adaptive target R_i",
            "target_error_correlations_measured": "innovation correlations only; not truth-error covariance",
            "common_N_eff_definition": "1 / sum_i(weight_i ** 2)",
            "common_N_eff_interpretation": "weight diversity only; not covariance-adjusted information or independent-target count",
        },
        "contract": contract,
        "guards": guards,
        "frozen_test": frozen,
        "estimator_input_audit": {
            "truth_present": False,
            "paper_response_metadata_present": False,
            "truth_used_by_estimator": False,
            "q_proxy_used_by_estimator": False,
        },
        "target_selection": {
            "single_target_index": single_idx,
            "calibration_strength_order": order.tolist(),
            "calibration_strength": strength.tolist(),
        },
        "diagnostics": {
            "common_weight_diversity": {
                "definition": "1 / sum_i(weight_i ** 2)",
                "interpretation": "weight diversity only; not covariance-adjusted information",
                "median": float(np.nanmedian(common_diag["effective_n"])),
                "p05": float(np.nanpercentile(common_diag["effective_n"], 5.0)),
                "p95": float(np.nanpercentile(common_diag["effective_n"], 95.0)),
                "min": float(np.nanmin(common_diag["effective_n"])),
                "max": float(np.nanmax(common_diag["effective_n"])),
            },
            "common_posterior_theta_variance": {
                "median": float(np.nanmedian(common_diag["p_theta"])),
                "p05": float(np.nanpercentile(common_diag["p_theta"], 5.0)),
                "p95": float(np.nanpercentile(common_diag["p_theta"], 95.0)),
                "interpretation": "internal model covariance under diagonal observation-noise assumption; empirical uncertainty calibration not measured",
            },
            "common_target_weights_median": np.nanmedian(common_diag["weight_history"], axis=1).tolist(),
            "common_target_r_median": np.nanmedian(common_diag["r_history"], axis=1).tolist(),
            "active_target_count": {
                "min": int(np.min(common_diag["active_count"])),
                "median": float(np.median(common_diag["active_count"])),
                "max": int(np.max(common_diag["active_count"])),
            },
            "common_innovation_correlation": {
                "matrix_scored_frames": common_corr_matrix,
                "summary": common_corr_summary,
                "scope": "Pearson correlation of per-target common-route innovations over frames 220:399; not truth-error covariance",
            },
            "independent_innovation_correlation": {
                "matrix_scored_frames": independent_corr_matrix,
                "summary": independent_corr_summary,
                "scope": "Pearson correlation of per-target independent-route innovations over frames 220:399",
            },
        },
        "score_test_tail": score,
        "score_summaries": {
            "independent_rmse_mean_m": float(np.mean([row["rmse_m"] for row in score["independent_per_target"]])),
            "independent_rmse_median_m": float(np.median([row["rmse_m"] for row in score["independent_per_target"]])),
            "common_vs_single_rmse_reduction": float(1.0 - score["common_state_fusion"]["rmse_m"] / score["single_target"]["rmse_m"]),
            "common_vs_independent_median_rmse_reduction": float(1.0 - score["common_state_fusion"]["rmse_m"] / np.median([row["rmse_m"] for row in score["independent_per_target"]])),
        },
        "implementation_check": {
            "common_matches_retained_q_hat_max_abs_m": retained_delta,
            "truth_error_covariance_measured": False,
            "causal_gain_claim": False,
        },
    }
    _json(output, result)
    shutil.rmtree(package)
    return result


def run_matrix(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    scratch_work = output / "_work"
    scratch_work.mkdir(exist_ok=True)
    trials: list[dict] = []
    for stratum, rms_mm in STRATA:
        for seed in SEEDS:
            trial_id = f"{stratum}__seed{seed}"
            trial_output = output / "results" / f"{trial_id}.json"
            result = run_trial(scratch_work / trial_id, trial_output, stratum, rms_mm, seed)
            trials.append(result)
    # Compact aggregate across the two paired seeds, retaining per-trial rows.
    grouped = {}
    for trial in trials:
        grouped.setdefault(trial["trial"]["stratum"], []).append(trial)
    summary = {"schema": "p3_common_latent_structural_state_fusion_strict_followup", "new_experiments": True, "seed_values": list(SEEDS), "strata": [x[0] for x in STRATA], "score_rule": "frames 220:399 only", "causal_gain_claim": False, "groups": {}}
    for stratum, rows in grouped.items():
        def values(route):
            return [row["score_test_tail"][route]["rmse_m"] for row in rows]
        common = values("common_state_fusion")
        single = values("single_target")
        independent_median = [row["score_summaries"]["independent_rmse_median_m"] for row in rows]
        corr = [row["diagnostics"]["common_innovation_correlation"]["summary"] for row in rows]
        summary["groups"][stratum] = {
            "trial_count": len(rows),
            "seeds": [row["trial"]["seed"] for row in rows],
            "single_rmse_m": single,
            "common_rmse_m": common,
            "independent_median_rmse_m": independent_median,
            "common_vs_single_reduction": [row["score_summaries"]["common_vs_single_rmse_reduction"] for row in rows],
            "common_vs_independent_median_reduction": [row["score_summaries"]["common_vs_independent_median_rmse_reduction"] for row in rows],
            "common_innovation_corr_summary": corr,
            "common_weight_diversity_median": [row["diagnostics"]["common_weight_diversity"]["median"] for row in rows],
        }
    _json(output / "strict_followup_summary.json", summary)
    manifest = {
        "schema": "p3_common_latent_structural_state_fusion_strict_followup_manifest",
        "new_experiments_run": True,
        "raw_captures_retained": False,
        "score_rule": "test frames 220:399 after predeclared 20-frame test warm-up",
        "estimator_truth_free": True,
        "causal_gain_claim": False,
        "cross_target_innovation_correlations": True,
        "correlations_are_truth_error_covariance": False,
        "runner_sha256": _hash_source(Path(__file__).resolve()),
        "trial_count": len(trials),
    }
    _json(output / "strict_followup_manifest.json", manifest)
    shutil.rmtree(scratch_work)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("spatial_recovery_rebuilt/p3_fusion_docs/strict_followup"))
    args = parser.parse_args()
    out = run_matrix(args.output)
    print(json.dumps({"status": "completed", "groups": list(out["groups"]), "output": str(args.output)}, indent=2))
