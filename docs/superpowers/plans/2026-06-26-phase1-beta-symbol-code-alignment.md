# Phase 1 Beta Symbol Code Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Phase 1 simulation code, tests, metrics, plots, and method registry so the codebase uses `beta` as the LoS-to-structural-direction conversion factor and no longer exposes the legacy reciprocal-symbol vocabulary.

**Architecture:** The main estimator will use the same coordinate system as the corrected documents: Kalman state is structural main phase `Theta`, wrapped radar observations are LoS phase, phase-branch correction happens in LoS space via `Theta / beta + bias`, then the corrected LoS phase is converted into structural-direction observation `y = beta * (phi_los_corr - bias)` with observation row `H_i = [1, 0]`. Public method and metric names should use `beta`; no compatibility aliases are kept because the requirement is strict no legacy reciprocal symbol.

**Tech Stack:** Python, NumPy, pytest, repository-local Phase 1 simulation modules under `simulation/phase1`, tests under `tests`.

---

## Subagent Strategy

This plan has parallelizable areas, but the first two tasks must be sequential because they change shared public names and core math:

- Not parallel: Task 1 and Task 2. They define the global rename policy, data model, and estimator math. Other edits depend on these names.
- Parallel after Task 2: Task 3 reporting/evaluation, Task 4 frontend/radar/scenario inputs, and Task 5 tests can be split across subagents because their write sets are mostly separate.
- Parallel after Task 5: Task 6 validation-output naming and Task 7 docs/code search cleanup can run independently.

This plan has more than two independent post-core tasks, so it is suitable for subagents. Ask before spawning: "这个 plan 适合开 subagents 并行执行，要我启用吗？"

## File Structure

- Modify `simulation/phase1/algorithm.py`: core estimator data model, structural-direction observation update, beta bootstrap, beta uncertainty R propagation, method names.
- Modify `simulation/phase1/radar.py`: radar truth generation from `beta`, algorithm input fields, true/measured conversion factors.
- Modify `simulation/phase1/frontend.py`: AoA-to-beta conversion, frontend target fields, synthetic ADC LoS phase generation.
- Modify `simulation/phase1/selection.py`: target selection geometry score and data field names.
- Modify `simulation/phase1/scenario_inputs.py`: bridge frontend outputs into algorithm inputs using beta fields.
- Modify `simulation/phase1/baselines.py`: rename fixed-beta and iterative-beta baselines; ensure all fitted slopes are true beta when named beta.
- Modify `simulation/phase1/method_registry.py` and `simulation/phase1/methods.py`: registry names and exports.
- Modify `simulation/phase1/evaluation.py`, `simulation/phase1/reporting.py`, `simulation/phase1/gates.py`, `simulation/phase1/extended_experiments.py`, `simulation/phase1/scenario_catalog.py`: metrics, gates, plots, CSV headers, summary text.
- Modify `simulation/phase1/config.py` and scenario files under `simulation/phase1/scenarios/`: config parameter names from `beta_*` to `beta_*`.
- Modify tests under `tests/test_phase1_*.py`: expected names, fields, gates, plot names, and behavioral assertions.

## Task 1: Add Beta Naming Tests Before Renaming

**Files:**
- Modify: `tests/test_phase1_architecture.py`
- Modify: `tests/test_phase1_methods.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add a repository-wide no-beta test**

Add this test to `tests/test_phase1_architecture.py`:

```python
def test_phase1_code_no_longer_uses_beta_symbol():
    roots = [Path("simulation/phase1"), Path("tests")]
    offenders = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text()
            if "beta" in text or "Beta" in text or "β" in text:
                offenders.append(str(path))
    assert offenders == []
```

Also add `from pathlib import Path` if the file does not already import it.

- [ ] **Step 2: Add expected beta method and metric tests**

In `tests/test_phase1_validation.py`, replace expectations for old full-pipeline names with:

```python
assert "proposed_full_pipeline_beta_confidence" in method_names
assert "selected_aoa_fixed_beta" in method_names
assert "proposed_full_pipeline_beta_confidence" not in method_names
assert "selected_aoa_fixed_beta" not in method_names
```

In metrics row assertions, require:

```python
assert "beta_median_relative_error" in row
assert "beta_median_relative_error" not in row
```

- [ ] **Step 3: Run the new tests and verify they fail**

Run:

```bash
pytest tests/test_phase1_architecture.py::test_phase1_code_no_longer_uses_beta_symbol tests/test_phase1_validation.py -q
```

Expected: failure because existing code still contains old names.

## Task 2: Rewrite Core Estimator Around Beta and Structural Observations

**Files:**
- Modify: `simulation/phase1/algorithm.py`
- Modify: `simulation/phase1/config.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Rename MethodResult fields**

In `simulation/phase1/algorithm.py`, change `MethodResult` to:

```python
@dataclass(frozen=True)
class MethodResult:
    method_name: str
    q_hat_m: np.ndarray
    theta_hat_rad: np.ndarray
    theta_dot_hat_radps: np.ndarray
    los_corrected_phase_rad: np.ndarray
    beta_hat: np.ndarray
    r_theta_history: np.ndarray
    innovation_rad: np.ndarray
    extra: dict = field(default_factory=dict)
```

Do not keep `corrected_phase_rad`, `beta_hat`, or `r_history` properties.

- [ ] **Step 2: Rename config parameters**

In `simulation/phase1/config.py`, replace the conversion-factor block with:

```python
    beta_window_samples: int = 80
    beta_update_start_s: float = 0.25
    beta_bootstrap_prior_weight: float = 500.0
    beta_confidence_initial_variance: float = 0.04
    beta_confidence_min_variance: float = 1.0e-6
    beta_confidence_max_variance: float = 0.25
    beta_confidence_forgetting: float = 0.90
    beta_min_abs: float = 1.0 / 1.2
    beta_max_abs: float = 1.0 / 0.05
```

Update every config use in `algorithm.py` to the new names.

- [ ] **Step 3: Implement beta clipping helper**

Add this helper near `_safe_inverse`:

```python
def _clip_beta(beta, config):
    arr = np.asarray(beta, dtype=float).copy()
    arr = np.clip(arr, config.beta_min_abs, config.beta_max_abs)
    small = np.abs(arr) < config.beta_min_abs
    arr[small] = config.beta_min_abs
    return arr
```

- [ ] **Step 4: Rename cold-start state initializer**

Replace `_initial_state_from_cold_start(..., beta, ...)` with beta semantics:

```python
def _initial_state_from_cold_start(radar, beta, target_bias, config, selected_indices=None):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    count = cold_start_sample_count(config, n_samples)
    theta0_estimates = []
    indices = range(n_targets) if selected_indices is None else np.asarray(selected_indices, dtype=int)
    for target_idx in indices:
        beta_i = float(beta[target_idx])
        if abs(beta_i) < config.beta_min_abs:
            continue
        wrapped = radar.wrapped_phase_rad[target_idx, :count]
        valid = np.isfinite(wrapped)
        if not np.any(valid):
            continue
        unwrapped = itoh_unwrap(wrapped[valid])
        aligned_first = prediction_correct_wrapped_phase(wrapped[valid][0], target_bias[target_idx])
        unwrapped = unwrapped + (aligned_first - unwrapped[0])
        theta_samples = beta_i * (unwrapped - target_bias[target_idx])
        theta0_estimates.append(float(theta_samples[0]))
    theta0 = float(np.median(theta0_estimates)) if theta0_estimates else 0.0
    return np.array([theta0, 0.0], dtype=float)
```

- [ ] **Step 5: Replace old LoS observation update with structural observation update**

Inside `run_structural_phase_kalman`, use this active-target loop:

```python
for target_idx in active_indices:
    los_prediction = x_pred[0] / beta[target_idx] + target_bias[target_idx]
    los_corrected = prediction_correct_wrapped_phase(
        radar.wrapped_phase_rad[target_idx, sample_idx],
        los_prediction,
    )
    los_corrected_phase[target_idx, sample_idx] = los_corrected
    y_obs = beta[target_idx] * (los_corrected - target_bias[target_idx])
    if use_beta_confidence_r:
        beta_uncertainty_r_values[target_idx] = float(
            (los_corrected - target_bias[target_idx]) ** 2 * beta_variance[target_idx]
        )
        effective_r_values[target_idx] = float(
            np.clip(
                r_theta_values[target_idx] + beta_uncertainty_r_values[target_idx],
                config.min_measurement_variance,
                config.max_measurement_variance,
            )
        )
    h_rows.append([1.0, 0.0])
    y_rows.append(y_obs)
    r_rows.append(effective_r_values[target_idx])
```

Then compute:

```python
h = np.asarray(h_rows, dtype=float)
y = np.asarray(y_rows, dtype=float)
r_mat = np.diag(np.asarray(r_rows, dtype=float))
innovation = y - (h @ x_pred)
```

Remove `bias_rows` from the Kalman update because bias is already removed when constructing `y_obs`.

- [ ] **Step 6: Replace beta bootstrap**

Replace the update block with centered LS for beta:

```python
if update_beta and sample_idx >= warmup_index:
    start = max(0, sample_idx - int(config.beta_window_samples) + 1)
    theta_window = theta_hat[start : sample_idx + 1]
    for target_idx in selected_indices_arr:
        los_window = los_corrected_phase[target_idx, start : sample_idx + 1]
        valid = np.isfinite(los_window) & np.isfinite(theta_window)
        if np.count_nonzero(valid) < 3:
            continue
        x_valid = los_window[valid] - target_bias[target_idx]
        y_valid = theta_window[valid]
        if beta_update_mode == "plain_window_ls":
            denom_valid = float(np.sum(x_valid**2))
            x_fit = x_valid
            y_fit = y_valid
        else:
            x_fit = x_valid - float(np.mean(x_valid))
            y_fit = y_valid - float(np.mean(y_valid))
            denom_valid = float(np.sum(x_fit**2))
        if denom_valid <= 1.0e-12:
            continue
        numerator = float(np.sum(x_fit * y_fit))
        if beta_prior_weight > 0.0 and beta_update_mode != "plain_window_ls":
            new_beta = (numerator + beta_prior_weight * beta_prior[target_idx]) / (
                denom_valid + beta_prior_weight
            )
        else:
            new_beta = numerator / denom_valid
        if abs(new_beta) >= config.beta_min_abs:
            beta[target_idx] = float(np.clip(new_beta, config.beta_min_abs, config.beta_max_abs))
```

Update the variance estimate residual to:

```python
residual = y_fit - new_beta * x_fit
variance_estimate = residual_var / max(float(denom_valid), 1.0e-12)
```

- [ ] **Step 7: Run core method tests**

Run:

```bash
pytest tests/test_phase1_methods.py -q
```

Expected after implementation: all tests in this file pass after they are updated in Task 5.

## Task 3: Rewrite Radar, Frontend, and Selection Data Models

**Files:**
- Modify: `simulation/phase1/radar.py`
- Modify: `simulation/phase1/frontend.py`
- Modify: `simulation/phase1/selection.py`
- Modify: `simulation/phase1/scenario_inputs.py`
- Test: `tests/test_phase1_frontend.py`
- Test: `tests/test_phase1_simulation.py`
- Test: `tests/test_phase1_target_selection.py`

- [ ] **Step 1: Rename radar dataclass fields**

In `simulation/phase1/radar.py`, define:

```python
@dataclass(frozen=True)
class RadarObservation:
    beta: np.ndarray
    measured_beta: np.ndarray
    target_angles_deg: np.ndarray
    snr_db: np.ndarray
    true_main_phase_rad: np.ndarray
    true_los_phase_rad: np.ndarray
    iq: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
```

And:

```python
@dataclass(frozen=True)
class RadarAlgorithmInput:
    measured_beta: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    selected_indices: Optional[np.ndarray] = None
    initial_r: Optional[np.ndarray] = None
    selection_scores: Optional[np.ndarray] = None
    extra: Optional[dict] = None
```

- [ ] **Step 2: Generate LoS phase from beta**

In `simulate_radar_targets`, replace projection generation with:

```python
projection = np.cos(np.deg2rad(angles_deg))
measured_projection = np.cos(np.deg2rad(measured_angles_deg))
beta = 1.0 / np.clip(np.abs(projection), 1.0e-12, None)
measured_beta = 1.0 / np.clip(np.abs(measured_projection), 1.0e-12, None)
true_los_phase_rad = true_main_phase_rad[None, :] / beta[:, None] + target_bias[:, None]
```

For mixed scatterers, rename scenario config fields to `mixed_scatterer_beta` and use:

```python
mixed += scatter_amp * np.exp(1j * (true_main_phase_rad / scatter_beta + scatter_bias))
```

- [ ] **Step 3: Rename frontend conversion helper**

In `simulation/phase1/frontend.py`, replace `angle_deg_to_measured_beta` with:

```python
def angle_deg_to_measured_beta(angle_deg, radar_mount: str = "downward"):
    """Map an angle estimate into the LoS-to-structural beta conversion factor."""
    if radar_mount != "downward":
        raise ValueError(f"unsupported radar_mount: {radar_mount}")
    projection = np.cos(np.deg2rad(np.asarray(angle_deg, dtype=float)))
    beta = 1.0 / np.clip(np.abs(projection), 1.0e-12, None)
    if np.isscalar(angle_deg):
        return float(beta)
    return beta
```

Update synthetic ADC generation to:

```python
los_phase = theta / float(scatterer.beta) + float(scatterer.phase_bias_rad)
```

- [ ] **Step 4: Rename selection fields**

In `simulation/phase1/selection.py`, replace `measured_beta` with `measured_beta`, and use `1 / beta` only as local projection quality:

```python
projection_abs = 1.0 / max(abs(float(beta[target_idx])), 1.0e-12)
score = _selection_score(presence, band_ratio, snr_est, projection_abs, min_snr_db, min_projection_abs)
```

Rename `min_abs_beta` to `min_projection_abs`.

- [ ] **Step 5: Run data model tests**

Run:

```bash
pytest tests/test_phase1_frontend.py tests/test_phase1_simulation.py tests/test_phase1_target_selection.py -q
```

Expected after updates: all pass and no test references `beta`.

## Task 4: Rename Methods, Metrics, Gates, Plots, and Outputs

**Files:**
- Modify: `simulation/phase1/method_registry.py`
- Modify: `simulation/phase1/methods.py`
- Modify: `simulation/phase1/evaluation.py`
- Modify: `simulation/phase1/reporting.py`
- Modify: `simulation/phase1/gates.py`
- Modify: `simulation/phase1/extended_experiments.py`
- Modify: `simulation/phase1/scenario_catalog.py`
- Test: `tests/test_phase1_validation.py`
- Test: `tests/test_phase1_extended_experiments.py`

- [ ] **Step 1: Rename method names**

Use these replacements:

```text
proposed_full_pipeline_beta_confidence -> proposed_full_pipeline_beta_confidence
proposed_full_pipeline_beta_confidence_r -> proposed_full_pipeline_beta_confidence_r
selected_aoa_fixed_beta -> selected_aoa_fixed_beta
multitarget_aoa_fixed_beta -> multitarget_aoa_fixed_beta
multitarget_true_beta_fixed_r -> multitarget_true_beta_fixed_r
```

Do not leave old aliases in `method_registry.py`.

- [ ] **Step 2: Rename evaluation metric**

In `evaluation.py`, replace `_beta_median_relative_error` with:

```python
def _beta_median_relative_error(result, radar, selected_indices, target_reference_indices):
    if result.beta_hat.shape[0] != target_reference_indices.size:
        return float("nan")
    selected = np.asarray(selected_indices, dtype=int)
    if selected.size == 0:
        selected = np.arange(result.beta_hat.shape[0], dtype=int)
    errors = []
    for target_idx in selected:
        if target_idx < 0 or target_idx >= result.beta_hat.shape[0]:
            continue
        reference_idx = int(target_reference_indices[target_idx])
        if reference_idx < 0 or reference_idx >= radar.beta.size:
            continue
        denom = max(abs(float(radar.beta[reference_idx])), 1.0e-12)
        errors.append(abs(float(result.beta_hat[target_idx]) - float(radar.beta[reference_idx])) / denom)
    if not errors:
        return float("nan")
    return float(np.median(errors))
```

Write the row field as `beta_median_relative_error`.

- [ ] **Step 3: Rename reporting plot**

In `reporting.py`, rename `_write_beta_bootstrap_plot` to `_write_beta_bootstrap_plot`, output file to:

```python
plots_dir / "aoa_error_bootstrap_beta_bootstrap.svg"
```

Use series labels:

```python
series.append((f"beta_hat_{target_idx}", beta_history[target_idx], colors[target_idx % len(colors)]))
series.append((f"beta_true_{target_idx}", np.full_like(truth.t, radar.beta[reference_idx]), "#111111"))
```

Set title and y-axis:

```python
title = f"aoa_error_bootstrap {result.method_name} beta bootstrap"
y_label = "LoS-to-structural conversion factor beta"
```

- [ ] **Step 4: Rename gates**

In `gates.py`, rename the gate to:

```python
{
    "name": "aoa_bootstrap_beta_median_relative_error_le_0p05",
    "value": aoa.get("beta_median_relative_error", 0.0),
    "threshold": 0.05,
    "passed": bool(aoa.get("beta_median_relative_error", 0.0) <= 0.05),
}
```

- [ ] **Step 5: Run validation tests**

Run:

```bash
pytest tests/test_phase1_validation.py tests/test_phase1_extended_experiments.py -q
```

Expected: all pass and generated/expected plot names use `beta`.

## Task 5: Rewrite Baselines Without Beta Leakage

**Files:**
- Modify: `simulation/phase1/baselines.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Convert fixed-projection baselines to beta names**

Rename functions:

```text
estimate_multitarget_true_beta_fixed_r -> estimate_multitarget_true_beta_fixed_r
estimate_multitarget_aoa_fixed_beta -> estimate_multitarget_aoa_fixed_beta
estimate_selected_aoa_fixed_beta -> estimate_selected_aoa_fixed_beta
```

Pass `initial_beta=radar.beta.copy()` or `initial_beta=radar_input.measured_beta.copy()`.

- [ ] **Step 2: Fix iterative beta baseline math**

In `_fit_iterative_beta_from_mixed_phase`, make the fitted slope true beta by fitting structural phase as a function of LoS corrected phase:

```python
x = corrected[valid] - bias
y = theta_ref[valid]
design = np.column_stack([x, np.ones_like(x)])
fitted, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
new_beta = float(np.clip(abs(fitted[0]), config.beta_min_abs, config.beta_max_abs))
new_bias = float(bias)
residual = float(np.sqrt(np.mean((y - new_beta * x) ** 2)))
```

Use prediction:

```python
prediction = theta_ref / beta + bias
```

- [ ] **Step 3: Run baseline-focused tests**

Run:

```bash
pytest tests/test_phase1_methods.py -q
```

Expected: all pass with beta method and artifact names.

## Task 6: Update Tests and Remove All Beta Strings

**Files:**
- Modify: all `tests/test_phase1_*.py`
- Modify: `simulation/phase1/*.py`
- Modify: `simulation/phase1/scenarios/*.py`

- [ ] **Step 1: Mechanical search**

Run:

```bash
rg -n "beta|Beta|β" simulation/phase1 tests
```

Expected before cleanup: list of remaining references.

- [ ] **Step 2: Replace remaining references by category**

Use these exact replacement categories:

```text
beta_hat -> beta_hat
beta_history -> beta_history
beta_variance_history -> beta_variance_history
beta_uncertainty_r_history -> beta_uncertainty_r_history
beta_update_mode -> beta_update_mode
beta_confidence -> beta_confidence
beta_median_relative_error -> beta_median_relative_error
measured_beta -> measured_beta
true_beta -> true_beta
abs_beta -> projection_abs
min_abs_beta -> min_projection_abs
```

- [ ] **Step 3: Verify no beta remains**

Run:

```bash
rg -n "beta|Beta|β" simulation/phase1 tests
```

Expected: no output, exit code 1.

## Task 7: Run Full Verification and Refresh Outputs

**Files:**
- Generated outputs under `simulation/outputs/phase1_validation` only if validation is intentionally refreshed.
- No source files beyond previous tasks.

- [ ] **Step 1: Run full Phase 1 test suite**

Run:

```bash
pytest tests/test_phase1_phase_utils.py tests/test_phase1_metrics.py tests/test_phase1_simulation.py tests/test_phase1_frontend.py tests/test_phase1_target_selection.py tests/test_phase1_methods.py tests/test_phase1_validation.py tests/test_phase1_extended_experiments.py tests/test_phase1_architecture.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run validation smoke**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m simulation.phase1.run_validation --output-dir /tmp/phase1_beta_validation
```

Expected: command exits 0; generated metrics contain `proposed_full_pipeline_beta_confidence`, `selected_aoa_fixed_beta`, and `beta_median_relative_error`.

- [ ] **Step 3: Check generated validation names**

Run:

```bash
rg -n "beta|Beta|β" /tmp/phase1_beta_validation
```

Expected: no output, exit code 1.

- [ ] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

## Task 8: Commit in Logical Units

**Files:**
- All modified source and test files.

- [ ] **Step 1: Commit core beta estimator**

Run:

```bash
git add simulation/phase1 tests
git commit -m "refactor: align phase1 estimator with beta conversion model"
```

- [ ] **Step 2: Commit validation output refresh only if generated outputs were intentionally updated**

Run only if repository-tracked generated outputs changed:

```bash
git add simulation/outputs
git commit -m "test: refresh phase1 beta validation outputs"
```

---

## Self-Review

- Spec coverage: The plan removes the legacy reciprocal-symbol vocabulary from code, tests, method names, metrics, gates, plots, config, and scenario fields. It also changes the main estimator from old LoS observation form to structural-direction observation, matching the corrected documents.
- Placeholder scan: No task uses "TBD" or vague "add tests" instructions; each task names concrete files, replacements, and verification commands.
- Type consistency: Public result fields are `los_corrected_phase_rad`, `beta_hat`, and `r_theta_history`; downstream tasks consistently reference those names.
