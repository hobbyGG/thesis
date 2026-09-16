"""Fail-closed, batch beta calibration without truth or Kalman feedback.

Three independent estimators live here:

* :func:`calibrate_common_aoa_bias` changes only one shared AoA bias ``delta``
  using multi-target phase consistency.
* :func:`calibrate_static_beta` uses native ADXL acceleration as an independent
  scale reference.  It implements the integral equivalent of
  ``-w^2 Phi = kappa p exp(-j*w*tau) A``, with ``p=1/beta``.
* :func:`calibrate_targetwise_beta` estimates target-specific projection ratios
  from the radar phase rank-1 structure, compares them with the absolute ADXL
  fit, and independently accepts or rejects each frozen beta.

The beta estimators use disjoint fitting and holdout blocks and never update
beta inside a time-recursive filter.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class BetaCalibrationConfig:
    calibration_fraction: float = 0.5
    delay_bounds_s: Tuple[float, float] = (-0.05, 0.05)
    delay_step_s: float = 5.0e-4
    nuisance_polynomial_degree: int = 3
    prior_weight: float = 0.01
    min_block_samples: int = 120
    min_acceleration_rms_mps2: float = 1.0e-4
    min_reference_rms_m: float = 1.0e-7
    min_target_coherence: float = 0.60
    min_holdout_improvement: float = 0.02
    max_fold_delay_difference_s: float = 0.006
    max_fold_beta_relative_difference: float = 0.15
    beta_bounds: Tuple[float, float] = (1.0 / 1.2, 1.0 / 0.05)
    max_relative_beta_change: float = 0.75
    max_relative_beta_std: float = 0.25
    max_unwrapped_phase_step_rad: float = np.pi
    min_relative_scale_targets: int = 3
    min_relative_rank1_fraction: float = 0.90
    scale_mode: str = "aoa_anchored_relative"


@dataclass(frozen=True)
class BetaCalibrationResult:
    beta: np.ndarray
    initial_beta: np.ndarray
    candidate_beta: np.ndarray
    variance: np.ndarray
    confidence: np.ndarray
    delay_s: float
    coherence: np.ndarray
    holdout_coherence: np.ndarray
    holdout_improvement: np.ndarray
    fold_beta: np.ndarray
    fold_delay_s: np.ndarray
    fold_train_coherence: np.ndarray
    fold_holdout_coherence: np.ndarray
    accepted: bool
    reason: str
    calibration_samples: int
    holdout_samples: int


@dataclass(frozen=True)
class TargetwiseBetaCalibrationResult:
    """Per-target beta decisions with a shared ADXL delay reference.

    ``raw_candidate_beta`` keeps the absolute ADXL fit.  The relative
    candidate identifies target-to-target projection ratios from a shared
    radar motion and fixes their otherwise-unidentifiable common scale with
    the AoA prior.  ``relative_holdout_improvement`` is a conditional
    per-target coefficient diagnostic: candidate and AoA baseline are compared
    against the same leave-one-target-out latent motion.  ``beta`` mixes
    accepted candidates with an exact per-target AoA fallback; no Kalman
    output participates in either estimate.
    """

    beta: np.ndarray
    initial_beta: np.ndarray
    candidate_beta: np.ndarray
    raw_candidate_beta: np.ndarray
    relative_candidate_beta: np.ndarray
    variance: np.ndarray
    confidence: np.ndarray
    delay_s: float
    coherence: np.ndarray
    holdout_coherence: np.ndarray
    holdout_improvement: np.ndarray
    raw_holdout_improvement: np.ndarray
    relative_holdout_improvement: np.ndarray
    fold_beta: np.ndarray
    raw_fold_beta: np.ndarray
    relative_fold_beta: np.ndarray
    fold_delay_s: np.ndarray
    fold_common_scale: np.ndarray
    relative_fold_rank1_fraction: np.ndarray
    relative_fold_reference_mask: np.ndarray
    relative_adxl_eligible_mask: np.ndarray
    accepted_mask: np.ndarray
    reason_by_target: Tuple[str, ...]
    accepted: bool
    all_accepted: bool
    reason: str
    scale_mode: str
    calibration_samples: int
    holdout_samples: int


@dataclass(frozen=True)
class CommonAoABiasConfig:
    calibration_fraction: float = 0.5
    delta_bounds_deg: Tuple[float, float] = (-15.0, 15.0)
    delta_step_deg: float = 0.05
    min_targets: int = 2
    min_angle_span_deg: float = 8.0
    min_block_samples: int = 80
    min_phase_rms_rad: float = 1.0e-3
    max_wrapped_phase_step_rad: float = 0.8 * np.pi
    min_abs_projection: float = 0.05
    min_holdout_improvement: float = 0.01
    min_delta_standard_score: float = 1.0
    beta_bounds: Tuple[float, float] = (1.0 / 1.2, 1.0 / 0.05)
    max_relative_beta_change: float = 0.25


@dataclass(frozen=True)
class CommonAoABiasResult:
    beta: np.ndarray
    initial_beta: np.ndarray
    candidate_beta: np.ndarray
    projection: np.ndarray
    delta_deg: float
    variance_deg2: float
    confidence: float
    calibration_residual_ratio: float
    holdout_residual_ratio: float
    holdout_improvement: float
    accepted: bool
    reason: str
    calibration_samples: int
    holdout_samples: int


@dataclass(frozen=True)
class _BlockFit:
    projection: np.ndarray
    variance: np.ndarray
    coherence: np.ndarray
    objective: float


@dataclass(frozen=True)
class _FoldFit:
    projection: np.ndarray
    variance: np.ndarray
    delay_s: float
    train_coherence: np.ndarray
    holdout_coherence: np.ndarray
    holdout_improvement: np.ndarray


@dataclass(frozen=True)
class _RelativePhaseFit:
    projection: np.ndarray
    variance: np.ndarray
    coherence: np.ndarray
    reference_mask: np.ndarray
    rank1_fraction: float


def _ro(values, dtype=float):
    result = np.asarray(values, dtype=dtype).copy()
    result.setflags(write=False)
    return result


def _time(name, values, minimum):
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or result.size < minimum:
        raise ValueError(f"{name} must be one-dimensional with at least {minimum} samples")
    if not np.all(np.isfinite(result)) or np.any(np.diff(result) <= 0.0):
        raise ValueError(f"{name} must be finite and strictly increasing")
    return result.copy()


def _initial_beta(count, initial_beta, initial_projection):
    if (initial_beta is None) == (initial_projection is None):
        raise ValueError("provide exactly one of initial_beta or initial_projection")
    values = np.asarray(initial_beta if initial_beta is not None else initial_projection, dtype=float)
    if values.ndim == 0:
        values = np.full(count, float(values))
    if values.ndim != 1 or values.size != count or not np.all(np.isfinite(values)):
        raise ValueError("AoA initial values must contain one finite value per target")
    if initial_projection is not None:
        if np.any(np.abs(values) <= np.finfo(float).eps):
            raise ValueError("initial_projection must be non-zero")
        values = 1.0 / np.abs(values)
    if np.any(values <= 0.0):
        raise ValueError("initial_beta must be positive")
    return values.copy()


def _integrate_twice(time_s, acceleration):
    dt = np.diff(time_s)
    velocity = np.zeros(time_s.size)
    velocity[1:] = np.cumsum(0.5 * (acceleration[:-1] + acceleration[1:]) * dt)
    displacement = np.zeros(time_s.size)
    displacement[1:] = np.cumsum(0.5 * (velocity[:-1] + velocity[1:]) * dt)
    return displacement


def _nuisance(time_s, degree):
    normalized = time_s - np.mean(time_s)
    scale = np.max(np.abs(normalized))
    if scale:
        normalized /= scale
    return np.column_stack([normalized**power for power in range(degree + 1)])


def _residualize(values, design):
    coefficient, _, _, _ = np.linalg.lstsq(design, values, rcond=None)
    # Some Accelerate/BLAS builds leave benign floating-point status flags set
    # after a preceding underflow (for example exp(-large) in diagnostics).
    # The finite matrix product is still correct; isolate those stale flags so
    # one calibration call cannot emit warnings because of an earlier call.
    with np.errstate(all="ignore"):
        return values - design @ coefficient


def _fit_block(time_s, phase, reference_m, kappa, prior, config):
    nuisance = _nuisance(time_s, config.nuisance_polynomial_degree)
    x = _residualize(kappa * reference_m, nuisance)
    with np.errstate(all="ignore"):
        information = float(x @ x)
    target_count = phase.shape[0]
    fitted = np.full(target_count, np.nan)
    variance = np.full(target_count, np.inf)
    coherence = np.zeros(target_count)
    if information <= 0.0 or np.sqrt(np.mean((x / kappa) ** 2)) < config.min_reference_rms_m:
        return _BlockFit(fitted, variance, coherence, np.inf)
    prior_information = config.prior_weight * information
    dof = max(1, time_s.size - nuisance.shape[1] - 1)
    objective = 0.0
    fitted_targets = 0
    for target in range(target_count):
        y = _residualize(phase[target], nuisance)
        with np.errstate(all="ignore"):
            energy = float(y @ y)
        if energy <= 0.0:
            continue
        with np.errstate(all="ignore"):
            cross = float(x @ y)
        fitted[target] = (cross + prior_information * prior[target]) / (
            information + prior_information
        )
        residual = y - fitted[target] * x
        with np.errstate(all="ignore"):
            rss = float(residual @ residual)
        variance[target] = (rss / dof) / (information + prior_information)
        coherence[target] = abs(cross) / np.sqrt(information * energy)
        penalty = prior_information * (fitted[target] - prior[target]) ** 2
        objective += (rss + penalty) / energy
        fitted_targets += 1
    if fitted_targets == 0:
        objective = np.inf
    else:
        objective /= fitted_targets
    return _BlockFit(fitted, variance, coherence, objective)


def _evaluate_block(time_s, phase, reference_m, kappa, candidate, initial, config):
    nuisance = _nuisance(time_s, config.nuisance_polynomial_degree)
    x = _residualize(kappa * reference_m, nuisance)
    with np.errstate(all="ignore"):
        information = float(x @ x)
    coherence = np.zeros(candidate.size)
    improvement = np.full(candidate.size, -np.inf)
    if information <= 0.0:
        return coherence, improvement
    for target in range(candidate.size):
        y = _residualize(phase[target], nuisance)
        with np.errstate(all="ignore"):
            energy = float(y @ y)
        if energy <= 0.0:
            continue
        with np.errstate(all="ignore"):
            coherence[target] = abs(float(x @ y)) / np.sqrt(information * energy)
        candidate_residual = y - candidate[target] * x
        initial_residual = y - initial[target] * x
        with np.errstate(all="ignore"):
            candidate_rss = float(candidate_residual @ candidate_residual)
            initial_rss = float(initial_residual @ initial_residual)
        if initial_rss > 0.0:
            improvement[target] = 1.0 - candidate_rss / initial_rss
    return coherence, improvement


def _shift_reference(radar_time, acceleration_time, integrated, delay_s):
    return np.interp(radar_time - delay_s, acceleration_time, integrated)


def _fit_fold(
    train,
    holdout,
    radar_time,
    phase,
    acceleration_time,
    integrated,
    kappa,
    fit_prior,
    validation_baseline,
    delays,
    config,
):
    best_delay = np.nan
    best = _BlockFit(
        np.full(fit_prior.size, np.nan),
        np.full(fit_prior.size, np.inf),
        np.zeros(fit_prior.size),
        np.inf,
    )
    for delay in delays:
        reference = _shift_reference(radar_time, acceleration_time, integrated, float(delay))
        fitted = _fit_block(
            radar_time[train],
            phase[:, train],
            reference[train],
            kappa,
            fit_prior,
            config,
        )
        if fitted.objective < best.objective:
            best, best_delay = fitted, float(delay)
    reference = _shift_reference(radar_time, acceleration_time, integrated, best_delay)
    hold_coherence, improvement = _evaluate_block(
        radar_time[holdout], phase[:, holdout], reference[holdout], kappa,
        best.projection, validation_baseline, config,
    )
    return _FoldFit(best.projection, best.variance, best_delay, best.coherence, hold_coherence, improvement)


def _rejected_beta(initial, reason, n1, n2, **diagnostics):
    count = initial.size
    candidate = diagnostics.get("candidate_beta", initial)
    return BetaCalibrationResult(
        _ro(initial), _ro(initial), _ro(candidate),
        _ro(diagnostics.get("variance", np.full(count, np.inf))),
        _ro(diagnostics.get("confidence", np.zeros(count))),
        float(diagnostics.get("delay_s", np.nan)),
        _ro(diagnostics.get("coherence", np.zeros(count))),
        _ro(diagnostics.get("holdout_coherence", np.zeros(count))),
        _ro(diagnostics.get("holdout_improvement", np.zeros(count))),
        _ro(diagnostics.get("fold_beta", np.full((2, count), np.nan))),
        _ro(diagnostics.get("fold_delay_s", np.full(2, np.nan))),
        _ro(diagnostics.get("fold_train_coherence", np.zeros((2, count)))),
        _ro(diagnostics.get("fold_holdout_coherence", np.zeros((2, count)))),
        False, reason, int(n1), int(n2),
    )


def _expand_beta_result(result, valid_mask, initial):
    """Expand a static-beta fit performed on phase-valid target rows."""

    valid_mask = np.asarray(valid_mask, dtype=bool)
    initial = np.asarray(initial, dtype=float)
    count = initial.size
    if valid_mask.shape != (count,):
        raise ValueError("valid_mask must contain one value per target")
    valid_count = int(np.count_nonzero(valid_mask))
    if result.initial_beta.shape != (valid_count,):
        raise ValueError("subset beta result does not match valid_mask")

    def vector(values, fill):
        expanded = np.full(count, fill, dtype=float)
        expanded[valid_mask] = np.asarray(values, dtype=float)
        return expanded

    fold_beta = np.full((2, count), np.nan, dtype=float)
    fold_beta[:, valid_mask] = np.asarray(result.fold_beta, dtype=float)
    fold_train_coherence = np.zeros((2, count), dtype=float)
    fold_train_coherence[:, valid_mask] = np.asarray(
        result.fold_train_coherence,
        dtype=float,
    )
    fold_holdout_coherence = np.zeros((2, count), dtype=float)
    fold_holdout_coherence[:, valid_mask] = np.asarray(
        result.fold_holdout_coherence,
        dtype=float,
    )
    return BetaCalibrationResult(
        _ro(initial),
        _ro(initial),
        _ro(vector(result.candidate_beta, np.nan)),
        _ro(vector(result.variance, np.inf)),
        _ro(vector(result.confidence, 0.0)),
        float(result.delay_s),
        _ro(vector(result.coherence, 0.0)),
        _ro(vector(result.holdout_coherence, 0.0)),
        _ro(vector(result.holdout_improvement, -np.inf)),
        _ro(fold_beta),
        _ro(result.fold_delay_s),
        _ro(fold_train_coherence),
        _ro(fold_holdout_coherence),
        bool(result.accepted and valid_count == count),
        str(result.reason),
        int(result.calibration_samples),
        int(result.holdout_samples),
    )


def calibrate_static_beta(
    radar_time_s: Sequence[float],
    los_phase_rad: np.ndarray,
    acceleration_mps2: Sequence[float],
    *,
    wavelength_m: float,
    initial_beta: Optional[Sequence[float]] = None,
    initial_projection: Optional[Sequence[float]] = None,
    fit_prior_beta: Optional[Sequence[float]] = None,
    acceleration_time_s: Optional[Sequence[float]] = None,
    config: BetaCalibrationConfig = BetaCalibrationConfig(),
) -> BetaCalibrationResult:
    """Calibrate beta from ADXL forcing response, with bidirectional holdout.

    Times are seconds and phase must already be unwrapped.  Positive ``delay``
    means ``r(t-delay)`` predicts the phase response.  Polynomial nuisance
    terms are re-fitted in holdout; beta and delay are not.
    """

    if not 0.0 < config.calibration_fraction < 1.0:
        raise ValueError("calibration_fraction must lie in (0, 1)")
    if config.delay_step_s <= 0.0 or config.delay_bounds_s[0] >= config.delay_bounds_s[1]:
        raise ValueError("delay grid must be positive and increasing")
    if config.nuisance_polynomial_degree not in (1, 2, 3):
        raise ValueError("nuisance_polynomial_degree must be 1, 2, or 3")
    if not np.isfinite(wavelength_m) or wavelength_m <= 0.0:
        raise ValueError("wavelength_m must be finite and positive")
    radar_time = _time("radar_time_s", radar_time_s, 16)
    phase = np.asarray(los_phase_rad, dtype=float)
    if phase.ndim == 1:
        phase = phase[None, :]
    if phase.ndim != 2 or phase.shape[0] == 0 or phase.shape[1] != radar_time.size:
        raise ValueError("los_phase_rad must have shape (targets, radar samples)")
    initial = _initial_beta(phase.shape[0], initial_beta, initial_projection)
    fit_prior = (
        initial.copy()
        if fit_prior_beta is None
        else _initial_beta(phase.shape[0], fit_prior_beta, None)
    )
    acceleration = np.asarray(acceleration_mps2, dtype=float)
    if acceleration.ndim != 1 or not np.all(np.isfinite(acceleration)):
        raise ValueError("acceleration_mps2 must be a finite vector")
    if acceleration_time_s is None:
        if acceleration.size != radar_time.size:
            raise ValueError("acceleration must match radar time when its time is omitted")
        acceleration_time = radar_time.copy()
    else:
        acceleration_time = _time("acceleration_time_s", acceleration_time_s, 2)
        if acceleration.size != acceleration_time.size:
            raise ValueError("acceleration_mps2 must match acceleration_time_s")

    low, high = config.delay_bounds_s
    delays = low + np.arange(int(np.floor((high - low) / config.delay_step_s)) + 1) * config.delay_step_s
    if delays[-1] < high - config.delay_step_s * 1.0e-9:
        delays = np.append(delays, high)
    common = np.flatnonzero(
        (radar_time >= acceleration_time[0] + np.max(delays))
        & (radar_time <= acceleration_time[-1] + np.min(delays))
    )
    split = int(np.floor(common.size * config.calibration_fraction))
    n1, n2 = split, common.size - split
    if n1 < config.min_block_samples or n2 < config.min_block_samples:
        return _rejected_beta(initial, "insufficient_disjoint_window_samples", n1, n2)
    first, second = common[:split], common[split:]
    if not np.all(np.isfinite(phase[:, common])) or np.any(
        np.abs(np.diff(phase[:, common], axis=1)) > config.max_unwrapped_phase_step_rad
    ):
        return _rejected_beta(initial, "nonfinite_or_ambiguous_unwrapped_phase", n1, n2)
    first_accel = acceleration[
        (acceleration_time >= radar_time[first[0]]) & (acceleration_time <= radar_time[first[-1]])
    ]
    second_accel = acceleration[
        (acceleration_time >= radar_time[second[0]]) & (acceleration_time <= radar_time[second[-1]])
    ]
    if first_accel.size < 2 or second_accel.size < 2 or min(np.std(first_accel), np.std(second_accel)) < config.min_acceleration_rms_mps2:
        return _rejected_beta(initial, "insufficient_acceleration_excitation", n1, n2)

    integrated = _integrate_twice(acceleration_time, acceleration)
    kappa = 4.0 * np.pi / wavelength_m
    # A geometry-constrained candidate may be useful as a weak fitting prior,
    # but all holdout and maximum-change gates remain anchored to the original
    # AoA beta in ``initial``.
    prior = 1.0 / fit_prior
    validation_baseline = 1.0 / initial
    folds = (
        _fit_fold(
            first,
            second,
            radar_time,
            phase,
            acceleration_time,
            integrated,
            kappa,
            prior,
            validation_baseline,
            delays,
            config,
        ),
        _fit_fold(
            second,
            first,
            radar_time,
            phase,
            acceleration_time,
            integrated,
            kappa,
            prior,
            validation_baseline,
            delays,
            config,
        ),
    )
    fold_projection = np.stack([fold.projection for fold in folds])
    fold_beta = np.full_like(fold_projection, np.nan)
    fold_positive = np.isfinite(fold_projection) & (fold_projection > 0.0)
    fold_beta[fold_positive] = 1.0 / fold_projection[fold_positive]
    fold_delay = np.array([fold.delay_s for fold in folds])
    projection = np.mean(fold_projection, axis=0)
    candidate = np.full_like(projection, np.nan)
    projection_positive = np.isfinite(projection) & (projection > 0.0)
    candidate[projection_positive] = 1.0 / projection[projection_positive]
    projection_variance = 0.25 * (folds[0].variance + folds[1].variance) + 0.25 * (folds[0].projection - folds[1].projection) ** 2
    variance = np.full_like(projection, np.inf)
    variance[projection_positive] = (
        projection_variance[projection_positive] / projection[projection_positive] ** 4
    )
    coherence = np.minimum(folds[0].train_coherence, folds[1].train_coherence)
    hold_coherence = np.minimum(folds[0].holdout_coherence, folds[1].holdout_coherence)
    improvement = np.minimum(folds[0].holdout_improvement, folds[1].holdout_improvement)
    relative_std = np.sqrt(variance) / candidate
    fold_difference = np.abs(fold_beta[0] - fold_beta[1]) / candidate
    confidence = np.clip(
        np.minimum(coherence, hold_coherence)
        * np.maximum(improvement, 0.0) / max(config.min_holdout_improvement, 1.0e-12)
        * np.exp(-np.minimum(relative_std, 50.0))
        * np.exp(-fold_difference / config.max_fold_beta_relative_difference), 0.0, 1.0,
    )
    diagnostics = dict(
        candidate_beta=candidate, variance=variance, confidence=confidence,
        delay_s=float(np.mean(fold_delay)), coherence=coherence,
        holdout_coherence=hold_coherence, holdout_improvement=improvement,
        fold_beta=fold_beta, fold_delay_s=fold_delay,
        fold_train_coherence=np.stack(
            [fold.train_coherence for fold in folds]
        ),
        fold_holdout_coherence=np.stack(
            [fold.holdout_coherence for fold in folds]
        ),
    )

    def reject(reason):
        return _rejected_beta(initial, reason, n1, n2, **diagnostics)

    if np.any(~np.isfinite(candidate)):
        return reject("non_positive_projection_candidate")
    if np.any(fold_delay == delays[0]) or np.any(fold_delay == delays[-1]):
        return reject("delay_candidate_on_search_boundary")
    if abs(fold_delay[0] - fold_delay[1]) > config.max_fold_delay_difference_s:
        return reject("cross_validation_delay_inconsistent")
    if np.any(fold_difference > config.max_fold_beta_relative_difference):
        return reject("cross_validation_beta_inconsistent")
    if np.any(coherence < config.min_target_coherence) or np.any(hold_coherence < config.min_target_coherence):
        return reject("insufficient_phase_acceleration_coherence")
    if np.any(candidate < config.beta_bounds[0]) or np.any(candidate > config.beta_bounds[1]):
        return reject("beta_candidate_out_of_bounds")
    if np.any(np.abs(candidate - initial) / initial > config.max_relative_beta_change):
        return reject("beta_candidate_change_too_large")
    if np.any(~np.isfinite(relative_std)) or np.any(relative_std > config.max_relative_beta_std):
        return reject("beta_candidate_uncertainty_too_large")
    if np.any(improvement < config.min_holdout_improvement):
        return reject("holdout_residual_not_improved")
    return BetaCalibrationResult(
        _ro(candidate), _ro(initial), _ro(candidate), _ro(variance), _ro(confidence),
        float(np.mean(fold_delay)), _ro(coherence), _ro(hold_coherence), _ro(improvement),
        _ro(fold_beta), _ro(fold_delay),
        _ro(np.stack([fold.train_coherence for fold in folds])),
        _ro(np.stack([fold.holdout_coherence for fold in folds])),
        True, "accepted", n1, n2,
    )


def _weighted_median(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if (
        values.ndim != 1
        or weights.shape != values.shape
        or values.size == 0
        or np.any(~np.isfinite(values))
        or np.any(~np.isfinite(weights))
        or np.any(weights <= 0.0)
    ):
        return np.nan
    order = np.argsort(values)
    ordered_values = values[order]
    ordered_weights = weights[order]
    threshold = 0.5 * float(np.sum(ordered_weights))
    cumulative = np.cumsum(ordered_weights)
    index = int(np.searchsorted(cumulative, threshold, side="left"))
    index = min(index, ordered_values.size - 1)
    if (
        index + 1 < ordered_values.size
        and np.isclose(cumulative[index], threshold, rtol=1.0e-12, atol=1.0e-15)
    ):
        return float(0.5 * (ordered_values[index] + ordered_values[index + 1]))
    return float(ordered_values[index])


def _candidate_from_fold_projection(fold_projection, fold_variance):
    fold_projection = np.asarray(fold_projection, dtype=float)
    fold_variance = np.asarray(fold_variance, dtype=float)
    if fold_projection.ndim != 2 or fold_projection.shape[0] != 2:
        raise ValueError("fold_projection must have shape (2, targets)")
    if fold_variance.shape != fold_projection.shape:
        raise ValueError("fold_variance must match fold_projection")
    valid = (
        np.all(np.isfinite(fold_projection), axis=0)
        & np.all(fold_projection > 0.0, axis=0)
        & np.all(np.isfinite(fold_variance), axis=0)
        & np.all(fold_variance >= 0.0, axis=0)
    )
    projection = np.full(fold_projection.shape[1], np.nan)
    projection[valid] = np.mean(fold_projection[:, valid], axis=0)
    beta = np.full(fold_projection.shape[1], np.nan)
    beta[valid] = 1.0 / projection[valid]
    projection_variance = np.full(fold_projection.shape[1], np.inf)
    projection_variance[valid] = (
        0.25 * np.sum(fold_variance[:, valid], axis=0)
        + 0.25
        * (fold_projection[0, valid] - fold_projection[1, valid]) ** 2
    )
    beta_variance = np.full(fold_projection.shape[1], np.inf)
    beta_variance[valid] = (
        projection_variance[valid] / projection[valid] ** 4
    )
    return beta, beta_variance


def _fit_relative_phase_block(
    time_s,
    phase,
    prior_projection,
    weights,
    eligible_reference_mask,
    config,
):
    eligible_reference_mask = np.asarray(eligible_reference_mask, dtype=bool)
    nuisance = _nuisance(time_s, config.nuisance_polynomial_degree)
    residual = np.stack(
        [_residualize(row, nuisance) for row in np.asarray(phase, dtype=float)]
    )
    target_count = residual.shape[0]
    if eligible_reference_mask.shape != (target_count,):
        raise ValueError("eligible_reference_mask must contain one value per target")
    with np.errstate(all="ignore"):
        energy = np.sum(residual**2, axis=1)
        rms = np.sqrt(np.maximum(energy, 0.0) / max(1, residual.shape[1]))
    valid_energy = np.isfinite(rms) & (rms > 0.0)
    correlation = np.zeros((target_count, target_count), dtype=float)
    for left in range(target_count):
        if not valid_energy[left]:
            continue
        for right in range(left + 1, target_count):
            if not valid_energy[right]:
                continue
            with np.errstate(all="ignore"):
                value = abs(float(residual[left] @ residual[right])) / np.sqrt(
                    energy[left] * energy[right]
                )
            correlation[left, right] = value
            correlation[right, left] = value
    coherence_score = np.zeros(target_count, dtype=float)
    for target in range(target_count):
        others = eligible_reference_mask.copy()
        others[target] = False
        if np.any(others):
            coherence_score[target] = float(
                np.median(correlation[target, others])
            )
    reference_mask = (
        valid_energy
        & eligible_reference_mask
        & (coherence_score >= config.min_target_coherence)
    )
    empty = _RelativePhaseFit(
        np.full(target_count, np.nan),
        np.full(target_count, np.inf),
        np.zeros(target_count),
        reference_mask,
        0.0,
    )
    if np.count_nonzero(reference_mask) < config.min_relative_scale_targets:
        return empty

    weighted = np.sqrt(weights[reference_mask, None]) * residual[reference_mask]
    try:
        _left, singular_values, right = np.linalg.svd(
            weighted,
            full_matrices=False,
        )
    except np.linalg.LinAlgError:
        return empty
    with np.errstate(all="ignore"):
        singular_energy = float(singular_values @ singular_values)
    if singular_energy <= 0.0 or right.shape[0] == 0:
        return empty
    latent = right[0]
    with np.errstate(all="ignore"):
        latent_energy = float(latent @ latent)
    if latent_energy <= 0.0:
        return empty
    with np.errstate(all="ignore"):
        projection = residual @ latent / latent_energy
        orientation = float(
            np.sum(
                weights[reference_mask]
                * projection[reference_mask]
                * prior_projection[reference_mask]
            )
        )
    if orientation < 0.0:
        projection = -projection
        latent = -latent
    ratio = projection[reference_mask] / prior_projection[reference_mask]
    positive_ratio = np.isfinite(ratio) & (ratio > 0.0)
    if np.count_nonzero(positive_ratio) < config.min_relative_scale_targets:
        return empty
    reference_indices = np.flatnonzero(reference_mask)
    normalization = _weighted_median(
        ratio[positive_ratio],
        weights[reference_indices[positive_ratio]],
    )
    if not np.isfinite(normalization) or normalization <= 0.0:
        return empty
    projection = projection / normalization

    coherence = np.zeros(target_count, dtype=float)
    variance = np.full(target_count, np.inf)
    dof = max(1, residual.shape[1] - nuisance.shape[1] - 1)
    for target in range(target_count):
        if energy[target] <= 0.0:
            continue
        predicted = projection[target] * latent * normalization
        with np.errstate(all="ignore"):
            predicted_energy = float(predicted @ predicted)
        if predicted_energy <= 0.0:
            continue
        with np.errstate(all="ignore"):
            coherence[target] = abs(
                float(residual[target] @ predicted)
            ) / np.sqrt(energy[target] * predicted_energy)
        fit_residual = residual[target] - predicted
        with np.errstate(all="ignore"):
            raw_projection_variance = (
                float(fit_residual @ fit_residual) / dof / latent_energy
            )
        variance[target] = raw_projection_variance / normalization**2
    return _RelativePhaseFit(
        projection,
        variance,
        coherence,
        reference_mask,
        float(singular_values[0] ** 2 / singular_energy),
    )


def _evaluate_relative_phase_block(
    time_s,
    phase,
    projection,
    initial_projection,
    weights,
    reference_mask,
    config,
):
    nuisance = _nuisance(time_s, config.nuisance_polynomial_degree)
    residual = np.stack(
        [_residualize(row, nuisance) for row in np.asarray(phase, dtype=float)]
    )
    target_count = residual.shape[0]
    coherence = np.zeros(target_count, dtype=float)
    improvement = np.full(target_count, -np.inf)
    for target in range(target_count):
        references = np.asarray(reference_mask, dtype=bool).copy()
        references[target] = False
        references &= np.isfinite(projection) & (projection > 0.0)
        if np.count_nonzero(references) < 2:
            continue
        with np.errstate(all="ignore"):
            denominator = float(
                np.sum(weights[references] * projection[references] ** 2)
            )
        if denominator <= 0.0:
            continue
        with np.errstate(all="ignore"):
            latent = np.sum(
                weights[references, None]
                * projection[references, None]
                * residual[references],
                axis=0,
            ) / denominator
        # This deliberately keeps the leave-one-target-out latent fixed for
        # both candidates.  It measures whether target i's coefficient became
        # better, without crediting it for corrections made to other targets;
        # it is not an independent whole-family baseline comparison.
        candidate_prediction = projection[target] * latent
        baseline_prediction = initial_projection[target] * latent
        with np.errstate(all="ignore"):
            target_energy = float(residual[target] @ residual[target])
            prediction_energy = float(candidate_prediction @ candidate_prediction)
        if target_energy <= 0.0 or prediction_energy <= 0.0:
            continue
        with np.errstate(all="ignore"):
            coherence[target] = abs(
                float(residual[target] @ candidate_prediction)
            ) / np.sqrt(target_energy * prediction_energy)
        candidate_residual = residual[target] - candidate_prediction
        baseline_residual = residual[target] - baseline_prediction
        with np.errstate(all="ignore"):
            candidate_rss = float(candidate_residual @ candidate_residual)
            baseline_rss = float(baseline_residual @ baseline_residual)
        if baseline_rss > 0.0:
            improvement[target] = 1.0 - candidate_rss / baseline_rss
    return coherence, improvement


def _target_acceptance(
    candidate,
    fold_beta,
    variance,
    coherence,
    holdout_coherence,
    improvement,
    initial,
    config,
):
    candidate = np.asarray(candidate, dtype=float)
    fold_beta = np.asarray(fold_beta, dtype=float)
    variance = np.asarray(variance, dtype=float)
    coherence = np.asarray(coherence, dtype=float)
    holdout_coherence = np.asarray(holdout_coherence, dtype=float)
    improvement = np.asarray(improvement, dtype=float)
    initial = np.asarray(initial, dtype=float)
    accepted = np.ones(candidate.size, dtype=bool)
    reasons = []
    confidence = np.zeros(candidate.size, dtype=float)
    for target in range(candidate.size):
        reason = "accepted"
        value = candidate[target]
        fold_values = fold_beta[:, target]
        relative_std = (
            np.sqrt(variance[target]) / value
            if np.isfinite(value) and value > 0.0 and np.isfinite(variance[target])
            else np.inf
        )
        fold_difference = (
            abs(fold_values[0] - fold_values[1]) / value
            if np.all(np.isfinite(fold_values)) and value > 0.0
            else np.inf
        )
        if not np.isfinite(value) or value <= 0.0:
            reason = "non_positive_projection_candidate"
        elif fold_difference > config.max_fold_beta_relative_difference:
            reason = "cross_validation_beta_inconsistent"
        elif (
            coherence[target] < config.min_target_coherence
            or holdout_coherence[target] < config.min_target_coherence
        ):
            reason = "insufficient_phase_acceleration_coherence"
        elif value < config.beta_bounds[0] or value > config.beta_bounds[1]:
            reason = "beta_candidate_out_of_bounds"
        elif abs(value - initial[target]) / initial[target] > config.max_relative_beta_change:
            reason = "beta_candidate_change_too_large"
        elif not np.isfinite(relative_std) or relative_std > config.max_relative_beta_std:
            reason = "beta_candidate_uncertainty_too_large"
        elif improvement[target] < config.min_holdout_improvement:
            reason = "holdout_residual_not_improved"
        if reason != "accepted":
            accepted[target] = False
        else:
            confidence[target] = float(
                np.clip(
                    min(coherence[target], holdout_coherence[target])
                    * improvement[target]
                    / max(config.min_holdout_improvement, 1.0e-12)
                    * np.exp(-min(relative_std, 50.0))
                    * np.exp(
                        -fold_difference
                        / max(config.max_fold_beta_relative_difference, 1.0e-12)
                    ),
                    0.0,
                    1.0,
                )
            )
        reasons.append(reason)
    return accepted, tuple(reasons), confidence


def calibrate_targetwise_beta(
    radar_time_s: Sequence[float],
    los_phase_rad: np.ndarray,
    acceleration_mps2: Sequence[float],
    *,
    wavelength_m: float,
    initial_beta: Optional[Sequence[float]] = None,
    initial_projection: Optional[Sequence[float]] = None,
    fit_prior_beta: Optional[Sequence[float]] = None,
    acceleration_time_s: Optional[Sequence[float]] = None,
    target_weights: Optional[Sequence[float]] = None,
    config: BetaCalibrationConfig = BetaCalibrationConfig(),
) -> TargetwiseBetaCalibrationResult:
    """Estimate and validate one frozen beta per target before Kalman.

    The absolute ADXL fit and an AoA-anchored radar-relative fit are both
    evaluated on two disjoint temporal folds.  The configured mode is chosen
    from calibration provenance before looking at holdout scores.  Relative
    mode uses cross-target rank-1 phase structure for ratios, anchors their
    common scale to the AoA prior, and still requires independent ADXL
    coherence.  Each target independently accepts its candidate or falls back
    exactly to its own original AoA beta.
    """

    phase = np.asarray(los_phase_rad, dtype=float)
    if phase.ndim == 1:
        phase = phase[None, :]
    if phase.ndim != 2 or phase.shape[0] == 0:
        raise ValueError("los_phase_rad must have shape (targets, radar samples)")
    initial = _initial_beta(phase.shape[0], initial_beta, initial_projection)
    fit_prior = (
        initial.copy()
        if fit_prior_beta is None
        else _initial_beta(phase.shape[0], fit_prior_beta, None)
    )
    if target_weights is None:
        weights = np.ones(phase.shape[0], dtype=float)
    else:
        weights = np.asarray(target_weights, dtype=float)
        if (
            weights.shape != (phase.shape[0],)
            or np.any(~np.isfinite(weights))
            or np.any(weights <= 0.0)
        ):
            raise ValueError("target_weights must contain one positive finite value per target")
    if config.min_relative_scale_targets < 3:
        raise ValueError("min_relative_scale_targets must be at least 3")
    if config.scale_mode not in ("adxl_absolute", "aoa_anchored_relative"):
        raise ValueError(
            "scale_mode must be adxl_absolute or aoa_anchored_relative"
        )
    if (
        not np.isfinite(config.min_relative_rank1_fraction)
        or not 0.0 <= config.min_relative_rank1_fraction <= 1.0
    ):
        raise ValueError("min_relative_rank1_fraction must lie in [0, 1]")
    if not 0.0 < config.calibration_fraction < 1.0:
        raise ValueError("calibration_fraction must lie in (0, 1)")
    if (
        config.delay_step_s <= 0.0
        or config.delay_bounds_s[0] >= config.delay_bounds_s[1]
    ):
        raise ValueError("delay grid must be positive and increasing")

    radar_time = _time("radar_time_s", radar_time_s, 16)
    if phase.shape[1] != radar_time.size:
        raise ValueError("los_phase_rad must have shape (targets, radar samples)")
    acceleration = np.asarray(acceleration_mps2, dtype=float)
    if acceleration.ndim != 1 or not np.all(np.isfinite(acceleration)):
        raise ValueError("acceleration_mps2 must be a finite vector")
    if acceleration_time_s is None:
        if acceleration.size != radar_time.size:
            raise ValueError("acceleration must match radar time when its time is omitted")
        acceleration_time = radar_time.copy()
    else:
        acceleration_time = _time("acceleration_time_s", acceleration_time_s, 2)
        if acceleration.size != acceleration_time.size:
            raise ValueError("acceleration_mps2 must match acceleration_time_s")

    low, high = config.delay_bounds_s
    delays = low + np.arange(
        int(np.floor((high - low) / config.delay_step_s)) + 1
    ) * config.delay_step_s
    if delays[-1] < high - config.delay_step_s * 1.0e-9:
        delays = np.append(delays, high)
    common = np.flatnonzero(
        (radar_time >= acceleration_time[0] + np.max(delays))
        & (radar_time <= acceleration_time[-1] + np.min(delays))
    )
    split = int(np.floor(common.size * config.calibration_fraction))
    first, second = common[:split], common[split:]
    phase_valid = np.ones(phase.shape[0], dtype=bool)
    if common.size:
        phase_valid = np.all(np.isfinite(phase[:, common]), axis=1) & ~np.any(
            np.abs(np.diff(phase[:, common], axis=1))
            > config.max_unwrapped_phase_step_rad,
            axis=1,
        )

    if np.any(phase_valid):
        raw_subset = calibrate_static_beta(
            radar_time,
            phase[phase_valid],
            acceleration,
            wavelength_m=wavelength_m,
            initial_beta=initial[phase_valid],
            fit_prior_beta=fit_prior[phase_valid],
            acceleration_time_s=acceleration_time,
            config=config,
        )
        raw = _expand_beta_result(raw_subset, phase_valid, initial)
    else:
        reason = (
            "insufficient_disjoint_window_samples"
            if first.size < config.min_block_samples
            or second.size < config.min_block_samples
            else "nonfinite_or_ambiguous_unwrapped_phase"
        )
        raw = _rejected_beta(initial, reason, first.size, second.size)

    count = initial.size
    raw_candidate = np.asarray(raw.candidate_beta, dtype=float).copy()
    raw_fold_beta = np.asarray(raw.fold_beta, dtype=float).copy()
    empty_candidate = np.full(count, np.nan)
    empty_fold = np.full((2, count), np.nan)
    empty_improvement = np.full(count, -np.inf)
    empty_reference = np.zeros((2, count), dtype=bool)

    def reject_global(
        reason,
        *,
        relative_candidate=None,
        relative_fold_beta=None,
        relative_rank1=None,
        relative_reference=None,
        adxl_eligible=None,
        fold_common_scale=None,
    ):
        relative_candidate = (
            empty_candidate
            if relative_candidate is None
            else np.asarray(relative_candidate, dtype=float)
        )
        relative_fold_beta = (
            empty_fold
            if relative_fold_beta is None
            else np.asarray(relative_fold_beta, dtype=float)
        )
        relative_rank1 = (
            np.zeros(2)
            if relative_rank1 is None
            else np.asarray(relative_rank1, dtype=float)
        )
        relative_reference = (
            empty_reference
            if relative_reference is None
            else np.asarray(relative_reference, dtype=bool)
        )
        adxl_eligible = (
            np.zeros(count, dtype=bool)
            if adxl_eligible is None
            else np.asarray(adxl_eligible, dtype=bool)
        )
        fold_common_scale = (
            np.full(2, np.nan)
            if fold_common_scale is None
            else np.asarray(fold_common_scale, dtype=float)
        )
        target_reasons = np.full(count, reason, dtype=object)
        target_reasons[~phase_valid] = (
            "nonfinite_or_ambiguous_unwrapped_phase"
        )
        return TargetwiseBetaCalibrationResult(
            _ro(initial),
            _ro(initial),
            _ro(
                relative_candidate
                if config.scale_mode == "aoa_anchored_relative"
                else raw_candidate
            ),
            _ro(raw_candidate),
            _ro(relative_candidate),
            _ro(np.full(count, np.inf)),
            _ro(np.zeros(count)),
            float(raw.delay_s),
            _ro(raw.coherence),
            _ro(raw.holdout_coherence),
            _ro(raw.holdout_improvement),
            _ro(raw.holdout_improvement),
            _ro(empty_improvement),
            _ro(
                relative_fold_beta
                if config.scale_mode == "aoa_anchored_relative"
                else raw_fold_beta
            ),
            _ro(raw_fold_beta),
            _ro(relative_fold_beta),
            _ro(raw.fold_delay_s),
            _ro(fold_common_scale),
            _ro(relative_rank1),
            _ro(relative_reference, dtype=bool),
            _ro(adxl_eligible, dtype=bool),
            _ro(np.zeros(count, dtype=bool), dtype=bool),
            tuple(str(value) for value in target_reasons),
            False,
            False,
            reason,
            "none",
            int(raw.calibration_samples),
            int(raw.holdout_samples),
        )

    global_reasons = {
        "insufficient_disjoint_window_samples",
        "insufficient_acceleration_excitation",
        "delay_candidate_on_search_boundary",
        "cross_validation_delay_inconsistent",
    }
    if not np.any(phase_valid):
        return reject_global(raw.reason)
    if raw.reason in global_reasons:
        return reject_global(raw.reason)
    fold_delay = np.asarray(raw.fold_delay_s, dtype=float)
    if (
        raw_fold_beta.shape != (2, count)
        or fold_delay.shape != (2,)
        or np.any(~np.isfinite(fold_delay))
    ):
        return reject_global("targetwise_fold_fit_unavailable")
    # A target-specific failure can be reported before the shared delay gates.
    # Recheck the fold diagnostics before allowing any target to be accepted.
    if np.any(fold_delay <= delays[0]) or np.any(fold_delay >= delays[-1]):
        return reject_global("delay_candidate_on_search_boundary")
    if abs(fold_delay[0] - fold_delay[1]) > config.max_fold_delay_difference_s:
        return reject_global("cross_validation_delay_inconsistent")
    if first.size != raw.calibration_samples or second.size != raw.holdout_samples:
        return reject_global("targetwise_window_mismatch")

    raw_fold_projection = np.full_like(raw_fold_beta, np.nan)
    raw_positive = np.isfinite(raw_fold_beta) & (raw_fold_beta > 0.0)
    raw_fold_projection[raw_positive] = 1.0 / raw_fold_beta[raw_positive]
    raw_variance = np.asarray(raw.variance, dtype=float).copy()
    raw_coherence = np.asarray(raw.coherence, dtype=float).copy()
    raw_holdout_coherence = np.asarray(
        raw.holdout_coherence,
        dtype=float,
    ).copy()
    raw_fold_train_coherence = np.asarray(
        raw.fold_train_coherence,
        dtype=float,
    ).copy()
    raw_fold_holdout_coherence = np.asarray(
        raw.fold_holdout_coherence,
        dtype=float,
    ).copy()
    raw_improvement = np.asarray(raw.holdout_improvement, dtype=float).copy()
    if (
        raw_fold_train_coherence.shape != (2, count)
        or raw_fold_holdout_coherence.shape != (2, count)
    ):
        return reject_global("targetwise_fold_coherence_unavailable")
    adxl_eligible = (
        phase_valid
        & np.all(np.isfinite(raw_fold_projection), axis=0)
        & np.all(raw_fold_projection > 0.0, axis=0)
        & np.all(
            raw_fold_train_coherence >= config.min_target_coherence,
            axis=0,
        )
        & np.all(
            raw_fold_holdout_coherence >= config.min_target_coherence,
            axis=0,
        )
    )
    # Each fit selects references from its own training block only.  The
    # opposite block remains holdout and cannot retroactively alter that fit.
    fold_adxl_reference = (
        phase_valid[None, :]
        & np.isfinite(raw_fold_projection)
        & (raw_fold_projection > 0.0)
        & (raw_fold_train_coherence >= config.min_target_coherence)
    )
    prior_projection = 1.0 / fit_prior
    validation_baseline = 1.0 / initial
    phase_for_relative = phase.copy()
    phase_for_relative[~phase_valid] = 0.0
    relative_fits = tuple(
        _fit_relative_phase_block(
            radar_time[block],
            phase_for_relative[:, block],
            prior_projection,
            weights,
            fold_adxl_reference[fold],
            config,
        )
        for fold, block in enumerate((first, second))
    )
    relative_fold_projection = np.stack(
        [fit.projection for fit in relative_fits]
    )
    relative_fold_variance = np.stack(
        [fit.variance for fit in relative_fits]
    )
    relative_fold_beta = np.full_like(relative_fold_projection, np.nan)
    relative_positive = np.isfinite(relative_fold_projection) & (
        relative_fold_projection > 0.0
    )
    relative_fold_beta[relative_positive] = (
        1.0 / relative_fold_projection[relative_positive]
    )
    relative_candidate, relative_variance = _candidate_from_fold_projection(
        relative_fold_projection,
        relative_fold_variance,
    )
    relative_rank1 = np.asarray(
        [fit.rank1_fraction for fit in relative_fits],
        dtype=float,
    )
    relative_reference = np.stack(
        [fit.reference_mask for fit in relative_fits]
    )
    enough_adxl_references = bool(
        np.count_nonzero(adxl_eligible) >= config.min_relative_scale_targets
        and all(
            np.count_nonzero(mask) >= config.min_relative_scale_targets
            for mask in fold_adxl_reference
        )
    )
    enough_phase_references = bool(
        all(
            np.count_nonzero(fit.reference_mask)
            >= config.min_relative_scale_targets
            for fit in relative_fits
        )
    )
    rank1_valid = bool(
        np.all(np.isfinite(relative_rank1))
        and np.all(relative_rank1 >= config.min_relative_rank1_fraction)
    )
    relative_available = bool(
        enough_adxl_references
        and enough_phase_references
        and rank1_valid
        and np.any(np.isfinite(relative_candidate))
    )

    fold_common_scale = np.full(2, np.nan)
    for fold, relative_fit in enumerate(relative_fits):
        ratio = raw_fold_projection[fold] / relative_fit.projection
        valid = (
            relative_fit.reference_mask
            & np.isfinite(ratio)
            & (ratio > 0.0)
            & (
                raw_fold_train_coherence[fold]
                >= config.min_target_coherence
            )
        )
        if np.count_nonzero(valid) >= config.min_relative_scale_targets:
            fold_common_scale[fold] = _weighted_median(
                ratio[valid],
                weights[valid],
            )

    if config.scale_mode == "aoa_anchored_relative" and not relative_available:
        if count < config.min_relative_scale_targets:
            relative_reason = "insufficient_relative_scale_targets"
        elif not enough_adxl_references:
            relative_reason = "insufficient_adxl_correlated_reference_targets"
        elif not enough_phase_references:
            relative_reason = "insufficient_relative_scale_targets"
        elif not rank1_valid:
            relative_reason = "relative_phase_rank1_gate_failed"
        else:
            relative_reason = "relative_candidate_unavailable"
        return reject_global(
            relative_reason,
            relative_candidate=relative_candidate,
            relative_fold_beta=relative_fold_beta,
            relative_rank1=relative_rank1,
            relative_reference=relative_reference,
            adxl_eligible=adxl_eligible,
            fold_common_scale=fold_common_scale,
        )

    relative_train_coherence = np.min(
        np.stack([fit.coherence for fit in relative_fits]),
        axis=0,
    )
    relative_fold_holdout_coherence = np.zeros((2, count), dtype=float)
    relative_fold_improvement = np.full((2, count), -np.inf)
    for fold, (holdout, relative_fit) in enumerate(
        zip((second, first), relative_fits)
    ):
        (
            relative_fold_holdout_coherence[fold],
            relative_fold_improvement[fold],
        ) = _evaluate_relative_phase_block(
            radar_time[holdout],
            phase_for_relative[:, holdout],
            relative_fit.projection,
            validation_baseline,
            weights,
            relative_fit.reference_mask,
            config,
        )
    relative_holdout_coherence = np.min(
        relative_fold_holdout_coherence,
        axis=0,
    )
    relative_improvement = np.min(relative_fold_improvement, axis=0)
    raw_mask, raw_reasons, raw_confidence = _target_acceptance(
        raw_candidate,
        raw_fold_beta,
        raw_variance,
        raw_coherence,
        raw_holdout_coherence,
        raw_improvement,
        initial,
        config,
    )
    relative_mask, relative_reasons, relative_confidence = _target_acceptance(
        relative_candidate,
        relative_fold_beta,
        relative_variance,
        relative_train_coherence,
        relative_holdout_coherence,
        relative_improvement,
        initial,
        config,
    )
    raw_reasons = list(raw_reasons)
    relative_reasons = list(relative_reasons)
    for target in range(count):
        if not phase_valid[target]:
            raw_mask[target] = False
            relative_mask[target] = False
            raw_reasons[target] = "nonfinite_or_ambiguous_unwrapped_phase"
            relative_reasons[target] = (
                "nonfinite_or_ambiguous_unwrapped_phase"
            )
        elif not adxl_eligible[target]:
            relative_mask[target] = False
            relative_reasons[target] = (
                "insufficient_phase_acceleration_coherence"
            )
    raw_reasons = tuple(raw_reasons)
    relative_reasons = tuple(relative_reasons)
    relative_confidence[~relative_mask] = 0.0

    scale_mode = config.scale_mode

    if scale_mode == "aoa_anchored_relative":
        candidate = relative_candidate
        variance = relative_variance
        improvement = relative_improvement
        confidence = relative_confidence
        fold_beta = relative_fold_beta
        accepted_mask = relative_mask
        reasons = relative_reasons
        coherence = relative_train_coherence
        holdout_coherence = relative_holdout_coherence
    else:
        candidate = raw_candidate
        variance = raw_variance
        improvement = raw_improvement
        confidence = raw_confidence
        fold_beta = raw_fold_beta
        accepted_mask = raw_mask
        reasons = raw_reasons
        coherence = raw_coherence
        holdout_coherence = raw_holdout_coherence

    beta = initial.copy()
    beta[accepted_mask] = candidate[accepted_mask]
    accepted_count = int(np.count_nonzero(accepted_mask))
    accepted = accepted_count > 0
    all_accepted = accepted_count == count
    if all_accepted:
        reason = "accepted_all"
    elif accepted:
        reason = f"accepted_partial:{accepted_count}/{count}"
    else:
        reason = "no_target_passed"
    return TargetwiseBetaCalibrationResult(
        _ro(beta),
        _ro(initial),
        _ro(candidate),
        _ro(raw_candidate),
        _ro(relative_candidate),
        _ro(variance),
        _ro(confidence),
        float(np.mean(raw.fold_delay_s)),
        _ro(coherence),
        _ro(holdout_coherence),
        _ro(improvement),
        _ro(raw_improvement),
        _ro(relative_improvement),
        _ro(fold_beta),
        _ro(raw_fold_beta),
        _ro(relative_fold_beta),
        _ro(raw.fold_delay_s),
        _ro(fold_common_scale),
        _ro(relative_rank1),
        _ro(relative_reference, dtype=bool),
        _ro(adxl_eligible, dtype=bool),
        _ro(accepted_mask, dtype=bool),
        reasons,
        accepted,
        all_accepted,
        reason,
        scale_mode,
        int(raw.calibration_samples),
        int(raw.holdout_samples),
    )


def _unwrap_contiguous_rows(wrapped):
    unwrapped = np.full_like(wrapped, np.nan, dtype=float)
    for row_index, row in enumerate(wrapped):
        finite = np.isfinite(row)
        boundaries = np.flatnonzero(np.diff(np.r_[False, finite, False]))
        for start, stop in boundaries.reshape(-1, 2):
            unwrapped[row_index, start:stop] = np.unwrap(row[start:stop])
    return unwrapped


def _longest_common_segment(values):
    valid = np.all(np.isfinite(values), axis=0)
    boundaries = np.flatnonzero(np.diff(np.r_[False, valid, False]))
    if boundaries.size == 0:
        return np.empty(0, dtype=int)
    segments = [np.arange(start, stop) for start, stop in boundaries.reshape(-1, 2)]
    return max(segments, key=lambda item: item.size)


def _aoa_objective(phase, projection, weights):
    centered = phase - np.mean(phase, axis=1, keepdims=True)
    denominator = float(np.sum(weights[:, None] * centered**2))
    projection_energy = float(np.sum(weights * projection**2))
    if denominator <= 0.0 or projection_energy <= 0.0:
        return np.inf
    theta = np.sum(weights[:, None] * projection[:, None] * centered, axis=0) / projection_energy
    residual = centered - projection[:, None] * theta[None, :]
    return float(np.sum(weights[:, None] * residual**2)) / denominator


def _rejected_aoa(initial, reason, n1, n2, **diagnostics):
    return CommonAoABiasResult(
        _ro(initial), _ro(initial), _ro(diagnostics.get("candidate_beta", initial)),
        _ro(diagnostics.get("projection", 1.0 / initial)),
        float(diagnostics.get("delta_deg", 0.0)), float(diagnostics.get("variance_deg2", np.inf)),
        float(diagnostics.get("confidence", 0.0)),
        float(diagnostics.get("calibration_residual_ratio", np.inf)),
        float(diagnostics.get("holdout_residual_ratio", np.inf)),
        float(diagnostics.get("holdout_improvement", -np.inf)),
        False, reason, int(n1), int(n2),
    )


def calibrate_common_aoa_bias(
    wrapped_phase_rad: np.ndarray,
    measured_angles_deg: Sequence[float],
    *,
    target_weights: Optional[Sequence[float]] = None,
    config: CommonAoABiasConfig = CommonAoABiasConfig(),
) -> CommonAoABiasResult:
    """Correct one shared AoA bias using multi-target phase consistency.

    Each target is Itoh-unwrapped only within contiguous finite runs.  On each
    candidate ``delta``, ``p_i=cos(angle_i-delta)`` is fixed and a common
    structural phase is estimated independently at every sample.  Only the
    shared delta can change; target-specific beta values cannot drift freely.
    """

    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    if wrapped.ndim != 2:
        raise ValueError("wrapped_phase_rad must have shape (targets, samples)")
    target_count = wrapped.shape[0]
    angles = np.asarray(measured_angles_deg, dtype=float)
    if angles.ndim != 1 or angles.size != target_count or not np.all(np.isfinite(angles)):
        raise ValueError("measured_angles_deg must contain one finite angle per target")
    if target_count < config.min_targets:
        initial = 1.0 / np.maximum(np.abs(np.cos(np.deg2rad(angles))), np.finfo(float).eps)
        return _rejected_aoa(initial, "insufficient_target_count", 0, 0)
    if np.ptp(angles) < config.min_angle_span_deg:
        initial = 1.0 / np.maximum(np.abs(np.cos(np.deg2rad(angles))), np.finfo(float).eps)
        return _rejected_aoa(initial, "insufficient_angle_span", 0, 0)
    if target_weights is None:
        weights = np.ones(target_count)
    else:
        weights = np.asarray(target_weights, dtype=float)
        if weights.ndim != 1 or weights.size != target_count or np.any(~np.isfinite(weights)) or np.any(weights <= 0.0):
            raise ValueError("target_weights must be one positive finite value per target")
    if config.delta_step_deg <= 0.0 or config.delta_bounds_deg[0] >= config.delta_bounds_deg[1]:
        raise ValueError("delta grid must be positive and increasing")
    if not 0.0 < config.calibration_fraction < 1.0:
        raise ValueError("calibration_fraction must lie in (0, 1)")
    if not 0.0 < config.max_wrapped_phase_step_rad < np.pi:
        raise ValueError("max_wrapped_phase_step_rad must lie in (0, pi)")
    if config.min_delta_standard_score < 0.0:
        raise ValueError("min_delta_standard_score cannot be negative")
    if config.max_relative_beta_change < 0.0:
        raise ValueError("max_relative_beta_change cannot be negative")

    unwrapped = _unwrap_contiguous_rows(wrapped)
    common = _longest_common_segment(unwrapped)
    split = int(np.floor(common.size * config.calibration_fraction))
    n1, n2 = split, common.size - split
    initial_projection = np.cos(np.deg2rad(angles))
    initial = 1.0 / np.maximum(np.abs(initial_projection), np.finfo(float).eps)
    if n1 < config.min_block_samples or n2 < config.min_block_samples:
        return _rejected_aoa(initial, "insufficient_disjoint_window_samples", n1, n2)
    wrapped_common = wrapped[:, common]
    circular_step = np.abs(np.angle(np.exp(1j * np.diff(wrapped_common, axis=1))))
    if np.any(circular_step >= config.max_wrapped_phase_step_rad):
        return _rejected_aoa(initial, "ambiguous_wrapped_phase_step", n1, n2)
    train = unwrapped[:, common[:split]]
    holdout = unwrapped[:, common[split:]]
    if min(float(np.sqrt(np.mean((train - np.mean(train, axis=1, keepdims=True)) ** 2))),
           float(np.sqrt(np.mean((holdout - np.mean(holdout, axis=1, keepdims=True)) ** 2)))) < config.min_phase_rms_rad:
        return _rejected_aoa(initial, "insufficient_phase_excitation", n1, n2)

    low, high = config.delta_bounds_deg
    deltas = low + np.arange(int(np.floor((high - low) / config.delta_step_deg)) + 1) * config.delta_step_deg
    objectives = np.full(deltas.size, np.inf)
    for index, delta in enumerate(deltas):
        projection = np.cos(np.deg2rad(angles - delta))
        if np.min(np.abs(projection)) >= config.min_abs_projection:
            objectives[index] = _aoa_objective(train, projection, weights)
    best_index = int(np.argmin(objectives))
    delta = float(deltas[best_index])
    projection = np.cos(np.deg2rad(angles - delta))
    candidate = 1.0 / np.abs(projection)
    train_ratio = float(objectives[best_index])
    holdout_ratio = _aoa_objective(holdout, projection, weights)
    initial_holdout_ratio = _aoa_objective(holdout, initial_projection, weights)
    improvement = 1.0 - holdout_ratio / initial_holdout_ratio if initial_holdout_ratio > 0.0 else -np.inf

    variance = np.inf
    if 0 < best_index < objectives.size - 1:
        curvature = objectives[best_index - 1] - 2.0 * objectives[best_index] + objectives[best_index + 1]
        if curvature > 0.0:
            variance = config.delta_step_deg**2 * max(train_ratio, 1.0e-12) / curvature
    confidence = float(np.clip(max(improvement, 0.0) / max(config.min_holdout_improvement, 1.0e-12) * np.exp(-np.sqrt(variance) / max(np.ptp(angles), 1.0)), 0.0, 1.0))
    diagnostics = dict(
        candidate_beta=candidate, projection=projection, delta_deg=delta,
        variance_deg2=variance, confidence=confidence,
        calibration_residual_ratio=train_ratio, holdout_residual_ratio=holdout_ratio,
        holdout_improvement=improvement,
    )

    def reject(reason):
        return _rejected_aoa(initial, reason, n1, n2, **diagnostics)

    if best_index in (0, deltas.size - 1):
        return reject("aoa_bias_candidate_on_search_boundary")
    if np.any(candidate < config.beta_bounds[0]) or np.any(candidate > config.beta_bounds[1]):
        return reject("beta_candidate_out_of_bounds")
    if np.any(
        np.abs(candidate - initial) / initial
        > config.max_relative_beta_change
    ):
        return reject("beta_candidate_change_too_large")
    if not np.isfinite(variance):
        return reject("aoa_bias_not_identifiable")
    standard_score = abs(delta) / max(np.sqrt(variance), np.finfo(float).eps)
    if standard_score < config.min_delta_standard_score:
        return reject("aoa_bias_not_significant")
    if improvement < config.min_holdout_improvement:
        return reject("holdout_residual_not_improved")
    return CommonAoABiasResult(
        _ro(candidate), _ro(initial), _ro(candidate), _ro(projection), delta, variance,
        confidence, train_ratio, holdout_ratio, improvement, True, "accepted", n1, n2,
    )


calibrate_beta = calibrate_static_beta

__all__ = [
    "BetaCalibrationConfig", "BetaCalibrationResult", "CommonAoABiasConfig",
    "CommonAoABiasResult", "TargetwiseBetaCalibrationResult", "calibrate_beta",
    "calibrate_common_aoa_bias", "calibrate_static_beta",
    "calibrate_targetwise_beta",
]
