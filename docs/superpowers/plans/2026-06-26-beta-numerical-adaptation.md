# Beta Numerical Adaptation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the public code and paper vocabulary in `beta` while adapting the numerical estimator so RMSE does not drift just because the reciprocal coordinate changed.

**Architecture:** `beta_i` remains the public LoS-to-structural-direction conversion factor. Internally, the bootstrap step may estimate the structural-to-LoS projection slope as a helper quantity, then convert it to `beta_i = 1 / projection_i`; this preserves the stable regression direction while keeping exported state, diagnostics, observations, and documents beta-based. Measurement noise remains in structural direction, with explicit beta/projection uncertainty propagation.

**Tech Stack:** Python, NumPy, `unittest`, repository-local Phase 1 simulation modules under `simulation/phase1`, tests under `tests`.

---

## Subagent Strategy

This plan has several independent investigations after the first characterization task:

- Not parallel at first: Task 1 must run first because it records the current regression and establishes numeric expectations.
- Parallel after Task 1: Task 2 bootstrap logic, Task 3 `R`/variance scaling, Task 4 selection invariance, and Task 5 baseline/report metric checks touch mostly separate files and can be worked in parallel.
- Final sequential step: Task 6 validation refresh must run after code changes and test updates.

This plan has more than two independent post-characterization tasks, so it is suitable for subagents. Ask before spawning: "这个 plan 适合开 subagents 并行执行，要我启用吗？"

## File Structure

- Modify `simulation/phase1/algorithm.py`: beta bootstrap update, internal projection helper, beta variance propagation, diagnostics.
- Modify `simulation/phase1/config.py`: add explicit projection-bootstrap options or rename config descriptions without changing public beta semantics.
- Modify `simulation/phase1/selection.py`: keep geometry gating on projection magnitude and add tests proving beta/projection equivalence in selection.
- Modify `simulation/phase1/baselines.py`: align baseline beta conversion and iterative beta fit with the same stable helper logic where applicable.
- Modify `simulation/phase1/evaluation.py` and `simulation/phase1/reporting.py`: keep beta metrics but optionally add projection diagnostics only if needed for debugging.
- Modify `simulation/phase1/gates.py`: update gate thresholds only after the adapted algorithm is verified.
- Modify `tests/test_phase1_methods.py`, `tests/test_phase1_simulation.py`, `tests/test_phase1_target_selection.py`, `tests/test_phase1_validation.py`: add targeted regression tests around AoA error, bootstrap convergence, R propagation, and selection invariance.
- Refresh `simulation/outputs/phase1_validation/*`, `simulation/outputs/phase1_extended_validation/*`, and report outputs after all tests pass.

---

### Task 1: Characterize Current Large RMSE Changes

**Files:**
- Test: `tests/test_phase1_validation.py`
- Read: `simulation/outputs/phase1_validation/metrics.csv`

- [ ] **Step 1: Add a regression test that isolates the large-change scenario**

Add this test to `tests/test_phase1_validation.py`:

```python
def test_aoa_bootstrap_full_pipeline_stays_below_legacy_tolerance_after_beta_adaptation(self):
    from simulation.phase1.run_phase1 import evaluate_scenario
    from simulation.phase1.scenarios.aoa_error_bootstrap import scenario

    rows = evaluate_scenario(scenario)
    full = next(row for row in rows if row["method"] == "proposed_full_pipeline_beta_confidence")
    fixed = next(row for row in rows if row["method"] == "selected_aoa_fixed_beta")

    self.assertLessEqual(full["rmse_mm"], 0.025)
    self.assertLessEqual(full["beta_median_relative_error"], 0.03)
    self.assertLess(full["rmse_mm"], fixed["rmse_mm"])
```

- [ ] **Step 2: Run the new test and confirm it fails before the adaptation**

Run:

```bash
python3 -m unittest tests.test_phase1_validation.TestPhase1Validation.test_aoa_bootstrap_full_pipeline_stays_below_legacy_tolerance_after_beta_adaptation -q
```

Expected before implementation: failure with current full-pipeline RMSE around `0.057 mm`.

- [ ] **Step 3: Record the current selected target count**

Run:

```bash
python3 - <<'PY'
from simulation.phase1.run_phase1 import evaluate_scenario
from simulation.phase1.scenarios.aoa_error_bootstrap import scenario

for row in evaluate_scenario(scenario):
    if row["method"] in ("selected_aoa_fixed_beta", "proposed_full_pipeline_beta_confidence"):
        print(row["method"], row["rmse_mm"], row["selected_target_count"], row["selected_indices"], row["beta_median_relative_error"])
PY
```

Expected before implementation: full pipeline selected count is currently lower than before the semantic migration, and RMSE is the main failing symptom.

---

### Task 2: Make Beta Bootstrap Numerically Stable

**Files:**
- Modify: `simulation/phase1/algorithm.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add a unit test for projection-assisted beta bootstrap**

Add this test to `tests/test_phase1_methods.py`:

```python
def test_beta_bootstrap_uses_stable_projection_fit_under_aoa_error(self):
    from dataclasses import replace
    from simulation.phase1.accelerometer import simulate_accelerometer
    from simulation.phase1.algorithm import estimate_proposed_full_pipeline_beta_confidence
    from simulation.phase1.radar import simulate_radar_targets, to_algorithm_radar_input
    from simulation.phase1.scenarios.aoa_error_bootstrap import scenario
    from simulation.phase1.truth import generate_truth

    config = replace(
        scenario,
        beta_update_start_s=0.1,
        beta_bootstrap_prior_weight=0.0,
        target_snr_db=(35.0, 32.0, 30.0, 28.0, 26.0),
    )
    truth = generate_truth(config)
    radar = simulate_radar_targets(truth, config)
    accel = simulate_accelerometer(truth, config)
    radar_input = to_algorithm_radar_input(radar)
    result = estimate_proposed_full_pipeline_beta_confidence(radar_input, accel, config)

    self.assertLess(float(abs(result.beta_hat[0] - radar.beta[0]) / radar.beta[0]), 0.03)
    self.assertLess(float(abs(result.beta_hat[1] - radar.beta[1]) / radar.beta[1]), 0.03)
```

- [ ] **Step 2: Introduce a helper that estimates projection then returns beta**

In `simulation/phase1/algorithm.py`, add near `_clip_beta`:

```python
def _fit_beta_via_projection(theta_values, los_values, beta_prior, prior_weight, config):
    theta = np.asarray(theta_values, dtype=float)
    los = np.asarray(los_values, dtype=float)
    valid = np.isfinite(theta) & np.isfinite(los)
    if np.count_nonzero(valid) < 3:
        return None

    theta_valid = theta[valid]
    los_valid = los[valid]
    theta_fit = theta_valid - float(np.mean(theta_valid))
    los_fit = los_valid - float(np.mean(los_valid))
    denom = float(np.dot(theta_fit, theta_fit))
    if denom <= 1.0e-12:
        return None

    projection_prior = 1.0 / max(abs(float(beta_prior)), config.beta_min_abs)
    numerator = float(np.dot(theta_fit, los_fit))
    if prior_weight > 0.0:
        projection = (numerator + prior_weight * projection_prior) / (denom + prior_weight)
    else:
        projection = numerator / denom
    projection_abs = abs(float(projection))
    if projection_abs <= 1.0e-12:
        return None

    beta = 1.0 / projection_abs
    beta = float(np.clip(beta, config.beta_min_abs, config.beta_max_abs))
    residual = los_fit - projection * theta_fit
    dof = max(int(np.count_nonzero(valid)) - 1, 1)
    residual_var = float(np.dot(residual, residual) / dof)
    projection_var = residual_var / max(denom, 1.0e-12)
    beta_var = projection_var / max(projection_abs**4, 1.0e-12)
    beta_var = float(
        np.clip(
            beta_var,
            config.beta_confidence_min_variance,
            config.beta_confidence_max_variance,
        )
    )
    return beta, beta_var
```

- [ ] **Step 3: Replace direct beta LS in `run_structural_phase_kalman`**

In the update block inside `run_structural_phase_kalman`, replace the current `x_valid/y_valid` centered beta LS with:

```python
los_without_bias = los_window[valid] - target_bias[target_idx]
theta_valid = theta_window[valid]
if beta_update_mode == "plain_window_ls":
    denom_valid = float(np.dot(los_without_bias, los_without_bias))
    if denom_valid <= 1.0e-12:
        continue
    new_beta = float(np.dot(los_without_bias, theta_valid) / denom_valid)
    beta_var_estimate = None
else:
    fitted = _fit_beta_via_projection(
        theta_values=theta_valid,
        los_values=los_without_bias,
        beta_prior=beta_prior[target_idx],
        prior_weight=beta_prior_weight,
        config=config,
    )
    if fitted is None:
        continue
    new_beta, beta_var_estimate = fitted
```

Then keep the existing clipping assignment to `beta[target_idx]`. When `beta_var_estimate is not None`, use it in the beta confidence variance update instead of recomputing residuals from the direct beta regression.

- [ ] **Step 4: Run the targeted method tests**

Run:

```bash
python3 -m unittest tests.test_phase1_methods -q
```

Expected: all tests pass, including the new projection-assisted beta bootstrap test.

---

### Task 3: Recalibrate Beta Confidence and Structural-Direction R

**Files:**
- Modify: `simulation/phase1/algorithm.py`
- Modify: `simulation/phase1/config.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add a test that beta uncertainty decreases after stable bootstrap**

Add this test to `tests/test_phase1_methods.py`:

```python
def test_beta_confidence_variance_decays_after_stable_projection_bootstrap(self):
    from dataclasses import replace
    from simulation.phase1.accelerometer import simulate_accelerometer
    from simulation.phase1.algorithm import estimate_proposed_full_pipeline_beta_confidence
    from simulation.phase1.radar import simulate_radar_targets, to_algorithm_radar_input
    from simulation.phase1.scenarios.aoa_error_bootstrap import scenario
    from simulation.phase1.truth import generate_truth

    config = replace(scenario, beta_update_start_s=0.1, beta_bootstrap_prior_weight=0.0)
    truth = generate_truth(config)
    radar = simulate_radar_targets(truth, config)
    accel = simulate_accelerometer(truth, config)
    result = estimate_proposed_full_pipeline_beta_confidence(to_algorithm_radar_input(radar), accel, config)
    variance = result.extra["beta_variance_history"][0]
    finite = variance[np.isfinite(variance)]

    self.assertGreater(finite.size, 10)
    self.assertLess(float(finite[-1]), float(finite[0]))
```

- [ ] **Step 2: Ensure beta variance update uses beta-coordinate variance**

In `simulation/phase1/algorithm.py`, when `_fit_beta_via_projection` returns `beta_var_estimate`, update:

```python
beta_variance[target_idx] = float(
    np.clip(
        forgetting * beta_variance[target_idx] + (1.0 - forgetting) * beta_var_estimate,
        config.beta_confidence_min_variance,
        config.beta_confidence_max_variance,
    )
)
```

- [ ] **Step 3: Keep structural R formula unchanged but document units in config**

In `simulation/phase1/config.py`, add inline comments above beta confidence fields:

```python
    # beta variance is expressed in beta-coordinate units. It is propagated into
    # structural phase observation noise as (phi_los_corr - bias)^2 * var(beta).
```

- [ ] **Step 4: Run confidence-related tests**

Run:

```bash
python3 -m unittest tests.test_phase1_methods.TestPhase1Methods.test_beta_confidence_variance_decays_after_stable_projection_bootstrap tests.test_phase1_methods.TestPhase1Methods.test_beta_confidence_full_pipeline_tracks_beta_uncertainty_in_r -q
```

Expected: both tests pass.

---

### Task 4: Verify Target Selection Is Projection-Invariant

**Files:**
- Modify: `tests/test_phase1_target_selection.py`
- Modify: `simulation/phase1/selection.py` only if the test exposes a real mismatch.

- [ ] **Step 1: Add a selection invariance test**

Add to `tests/test_phase1_target_selection.py`:

```python
def test_selection_geometry_uses_projection_not_beta_magnitude(self):
    import numpy as np
    from simulation.phase1.selection import select_targets_from_measurements

    n_targets = 3
    n_samples = 320
    t = np.arange(n_samples) / 100.0
    iq = np.exp(1j * 2.0 * np.pi * 4.0 * t)[None, :].repeat(n_targets, axis=0)
    wrapped = np.angle(iq)
    available = np.ones((n_targets, n_samples), dtype=bool)
    accel = np.sin(2.0 * np.pi * 4.0 * t)
    projection = np.array([0.9, 0.6, 0.2], dtype=float)
    beta = 1.0 / projection

    selected = select_targets_from_measurements(
        iq=iq,
        wrapped_phase_rad=wrapped,
        available_mask=available,
        measured_beta=beta,
        measured_acceleration_mps2=accel,
        sample_rate_hz=100.0,
        min_projection_abs=0.45,
        min_snr_db=0.0,
        min_band_energy_ratio=0.0,
    )

    self.assertIn(0, selected.selected_indices.tolist())
    self.assertIn(1, selected.selected_indices.tolist())
    self.assertNotIn(2, selected.selected_indices.tolist())
```

- [ ] **Step 2: Run target selection tests**

Run:

```bash
python3 -m unittest tests.test_phase1_target_selection -q
```

Expected: all tests pass. If the new test fails, fix `selection.py` by keeping all geometry thresholds and scores in projection units through `_projection_abs_from_beta`.

---

### Task 5: Align Baselines and Diagnostics With the Adapted Beta Logic

**Files:**
- Modify: `simulation/phase1/baselines.py`
- Modify: `simulation/phase1/evaluation.py`
- Modify: `simulation/phase1/reporting.py`
- Test: `tests/test_phase1_methods.py`, `tests/test_phase1_validation.py`

- [ ] **Step 1: Update iterative beta range-bin fit to use projection-assisted fitting**

In `simulation/phase1/baselines.py`, change `_fit_iterative_beta_from_mixed_phase` so the update estimates projection first:

```python
theta = theta_ref[valid]
los = corrected[valid] - bias
theta_c = theta - float(np.mean(theta))
los_c = los - float(np.mean(los))
denom = float(np.dot(theta_c, theta_c))
if denom <= 1.0e-12:
    break
projection = float(np.dot(theta_c, los_c) / denom)
new_beta = float(np.clip(1.0 / max(abs(projection), 1.0e-12), config.beta_min_abs, config.beta_max_abs))
new_bias = float(np.mean(corrected[valid] - theta / new_beta))
residual = float(np.sqrt(np.mean((los_c - projection * theta_c) ** 2)))
```

- [ ] **Step 2: Keep `range_bin_itoh` as a pure beta conversion baseline**

Leave `estimate_range_bin_itoh` as:

```python
theta = beta * (corrected - phase_ref)
```

This method is supposed to reflect fixed measured beta; do not add bootstrap behavior to it.

- [ ] **Step 3: Ensure beta metric uses true beta and selected references**

Confirm `simulation/phase1/evaluation.py` computes:

```python
abs(result.beta_hat[target_idx] - radar.beta[reference_idx]) / abs(radar.beta[reference_idx])
```

No code change is needed if this is already present.

- [ ] **Step 4: Run baseline and validation tests**

Run:

```bash
python3 -m unittest tests.test_phase1_methods tests.test_phase1_validation -q
```

Expected: all tests pass and `aoa_error_bootstrap` full pipeline is below the threshold from Task 1.

---

### Task 6: Refresh Outputs and Recompare RMSE

**Files:**
- Modify generated outputs under `simulation/outputs/phase1_validation`
- Modify generated outputs under `simulation/outputs/phase1_extended_validation`
- Modify report plots/assets as needed

- [ ] **Step 1: Run the full unit test subset**

Run:

```bash
python3 -m unittest tests.test_phase1_phase_utils tests.test_phase1_metrics tests.test_phase1_simulation tests.test_phase1_frontend tests.test_phase1_target_selection tests.test_phase1_methods tests.test_phase1_validation tests.test_phase1_extended_experiments tests.test_phase1_architecture tests.test_phase1_ma2026_reproduction -q
```

Expected: `Ran 136 tests ... OK` or higher if new tests are added.

- [ ] **Step 2: Refresh validation outputs**

Run the repository’s current validation commands used for the existing outputs:

```bash
python3 -m simulation.phase1.run_phase1 --output-dir simulation/outputs/phase1_validation
python3 -m simulation.phase1.extended_experiments --output-dir simulation/outputs/phase1_extended_validation
```

Expected: CSV and SVG outputs refresh without errors.

- [ ] **Step 3: Recompare current RMSE against the pre-adaptation beta run**

Run:

```bash
python3 - <<'PY'
import csv
from pathlib import Path

rows = list(csv.DictReader(Path("simulation/outputs/phase1_validation/metrics.csv").open()))
for row in rows:
    if row["scenario"] == "aoa_error_bootstrap" and row["method"] in (
        "selected_aoa_fixed_beta",
        "proposed_full_pipeline_beta_confidence",
    ):
        print(row["method"], row["rmse_mm"], row["beta_median_relative_error"], row["selected_target_count"], row["selected_indices"])
PY
```

Expected after adaptation: full pipeline RMSE returns near the old small-error regime, remains below selected fixed beta, and beta relative error is clearly below `0.10`.

- [ ] **Step 4: Run formatting and symbol checks**

Run:

```bash
git diff --check
rg -n "<removed reciprocal symbol spellings>" . --glob '!/.git/**' --glob '!**/__pycache__/**' --glob '!*.pyc'
find . \( -iname '*<removed reciprocal symbol spellings>*' \) -print
```

Expected: `git diff --check` exits 0; the two symbol scans print no results.

---

## Self-Review

- Spec coverage: The plan covers every adaptation point found in code inspection: bootstrap regression direction, beta variance/R propagation, target selection geometry, baseline range-bin iterative fit, beta metrics, gates, and refreshed outputs.
- Placeholder scan: No step contains open-ended placeholders; every code task names concrete files and commands.
- Type consistency: Public names stay `beta`, `measured_beta`, `beta_hat`, `beta_history`, `r_theta_history`, and `beta_median_relative_error`. Internal helper names use `projection` only as a numeric auxiliary and do not reintroduce the removed legacy symbol.
