# Beta Independent Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn beta self-calibration from a self-consistent posterior fit into a target-independent, scale-anchored bootstrap mechanism that can be evaluated separately from displacement RMSE.

**Architecture:** The radar still observes wrapped LOS phase, and the main Kalman state remains structural-direction phase. For each target `i`, beta update must use `phi_i^{LOS,corr}` plus a structural reference that excludes target `i`; a scale anchor from acceleration or a trusted low-angle peer prevents common-scale drift. The paper method should expose beta convergence diagnostics separately from displacement accuracy.

**Tech Stack:** Python `unittest`, NumPy, existing Phase 1 simulation modules under `simulation/phase1`, Markdown report assets.

---

## File Structure

- Modify `simulation/phase1/algorithm.py`
  - Owns Kalman prediction/update, LOS phase correction, beta update reference modes, beta diagnostics.
- Modify `simulation/phase1/selection.py`
  - Owns final fusion target selection and wider beta calibration peer-pool selection.
- Modify `simulation/phase1/radar.py`
  - Carries `calibration_indices` in `RadarAlgorithmInput`.
- Modify `simulation/phase1/scenario_inputs.py`
  - Builds frontend algorithm input with both `selected_indices` and `calibration_indices`.
- Modify `simulation/phase1/config.py`
  - Add explicit config knobs for independent beta update, scale anchoring, and convergence gates.
- Modify `simulation/phase1/evaluation.py`
  - Report beta convergence separately from displacement RMSE.
- Modify `simulation/phase1/reporting.py`
  - Generate beta bootstrap diagnostics that do not imply target-wise convergence unless gates pass.
- Modify `tests/test_phase1_methods.py`
  - Unit tests for independent reference, scale ambiguity, anchored beta update, and delayed beta application.
- Modify `tests/test_phase1_target_selection.py`
  - Unit tests for calibration peer pool selection.
- Modify `tests/test_phase1_validation.py`
  - Scenario-level gates for beta convergence and displacement improvement.

---

### Task 1: Lock the Failure Mode as Tests

**Files:**
- Modify: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add a test showing posterior zcorr can preserve a wrong beta scale**

Add this test near the existing beta update tests:

```python
def test_beta_fit_from_self_posterior_preserves_wrong_common_scale(self):
    config = Phase1Config()
    true_beta = 1.25
    wrong_scale = 1.18
    los = np.linspace(-2.0, 2.0, 21)
    theta_true = true_beta * los
    theta_self_posterior = wrong_scale * theta_true

    fitted = phase1_algorithm._fit_beta_direct(
        theta_values=theta_self_posterior,
        los_values=los,
        beta_prior=1.0,
        prior_weight=0.0,
        config=config,
    )

    self.assertIsNotNone(fitted)
    self.assertAlmostEqual(fitted[0], wrong_scale * true_beta)
```

- [ ] **Step 2: Run the focused test**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_methods.Phase1KalmanMethodsTest.test_beta_fit_from_self_posterior_preserves_wrong_common_scale
```

Expected: PASS. This test documents the mathematical limitation; it is not supposed to fail.

- [ ] **Step 3: Commit**

```bash
git add tests/test_phase1_methods.py
git commit -m "test: document beta self-posterior scale ambiguity"
```

---

### Task 2: Make Calibration Peer Pool an Explicit Contract

**Files:**
- Modify: `simulation/phase1/selection.py`
- Modify: `simulation/phase1/radar.py`
- Modify: `simulation/phase1/scenario_inputs.py`
- Test: `tests/test_phase1_target_selection.py`

- [ ] **Step 1: Add or keep `calibration_indices` and `calibration_initial_r`**

Ensure `SelectedTargetSet` has:

```python
@dataclass(frozen=True)
class SelectedTargetSet:
    selected_indices: np.ndarray
    quality_score: np.ndarray
    initial_r: np.ndarray
    calibration_indices: np.ndarray
    calibration_initial_r: np.ndarray
    diagnostics: SelectionDiagnostics
```

Ensure `RadarAlgorithmInput` has:

```python
@dataclass(frozen=True)
class RadarAlgorithmInput:
    measured_beta: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    selected_indices: Optional[np.ndarray] = None
    calibration_indices: Optional[np.ndarray] = None
    initial_r: Optional[np.ndarray] = None
    selection_scores: Optional[np.ndarray] = None
    extra: Optional[dict] = None
```

- [ ] **Step 2: Keep selected and calibration pools separate**

In `selected_frontend_algorithm_input`, use:

```python
return RadarAlgorithmInput(
    measured_beta=frontend_targets.measured_beta.copy(),
    wrapped_phase_rad=frontend_targets.wrapped_phase_rad.copy(),
    available_mask=frontend_targets.available_mask.copy(),
    selected_indices=selected.selected_indices.copy(),
    calibration_indices=selected.calibration_indices.copy(),
    initial_r=selected.calibration_initial_r.copy(),
    selection_scores=selected.quality_score.copy(),
)
```

- [ ] **Step 3: Run selection tests**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_target_selection
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add simulation/phase1/selection.py simulation/phase1/radar.py simulation/phase1/scenario_inputs.py tests/test_phase1_target_selection.py
git commit -m "feat: separate beta calibration peer pool from fusion targets"
```

---

### Task 3: Implement Target-Independent Beta Reference

**Files:**
- Modify: `simulation/phase1/algorithm.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Ensure LOO reference excludes target `i`**

In `run_structural_phase_kalman`, construct peer indices with:

```python
peer_indices = np.asarray(
    [
        peer_idx
        for peer_idx in correction_indices
        if peer_idx != target_idx
        and calibration_mask[peer_idx]
        and np.isfinite(y_obs_by_target[peer_idx])
    ],
    dtype=int,
)
```

- [ ] **Step 2: Add a test excluding bad non-calibration candidates**

Use this expected behavior:

```python
self.assertAlmostEqual(float(loo_reference[0, 1]), 2.25, places=5)
self.assertAlmostEqual(float(loo_reference[1, 1]), 1.75, places=5)
```

The fourth target with phase `100.0` must not enter the LOO reference if it is not in `calibration_indices`.

- [ ] **Step 3: Run method tests**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_methods
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add simulation/phase1/algorithm.py tests/test_phase1_methods.py
git commit -m "feat: update beta from leave-one-target-out reference"
```

---

### Task 4: Add Scale Anchoring for LOO Beta Update

**Files:**
- Modify: `simulation/phase1/algorithm.py`
- Modify: `simulation/phase1/config.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add helper to scale LOO theta to acceleration anchor**

Add:

```python
def _scale_theta_reference_to_anchor(theta_values, anchor_values):
    theta = np.asarray(theta_values, dtype=float)
    anchor = np.asarray(anchor_values, dtype=float)
    valid = np.isfinite(theta) & np.isfinite(anchor)
    if np.count_nonzero(valid) < 3:
        return theta

    theta_valid = theta[valid]
    anchor_valid = anchor[valid]
    theta_fit = theta_valid - float(np.mean(theta_valid))
    anchor_fit = anchor_valid - float(np.mean(anchor_valid))
    denom = float(np.dot(theta_fit, theta_fit))
    if denom <= 1.0e-12:
        return theta
    scale = float(np.dot(theta_fit, anchor_fit) / denom)
    if not np.isfinite(scale) or scale <= 0.0:
        return theta
    return theta * scale
```

- [ ] **Step 2: Add mode `loo_accel_scaled_direct_ls`**

In beta update:

```python
if beta_reference_mode == "loo_accel_scaled_direct_ls":
    anchor_window = beta_fft_reference_theta[start : sample_idx + 1]
    theta_valid = _scale_theta_reference_to_anchor(theta_valid, anchor_window[valid])
```

- [ ] **Step 3: Add tests**

Add:

```python
def test_theta_reference_scaling_matches_acceleration_anchor_slope(self):
    theta = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
    anchor = np.array([3.0, 5.0, 7.0, 9.0], dtype=float)

    scaled = phase1_algorithm._scale_theta_reference_to_anchor(theta, anchor)

    np.testing.assert_allclose(scaled, 2.0 * theta)
```

- [ ] **Step 4: Run method tests**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_methods
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add simulation/phase1/algorithm.py simulation/phase1/config.py tests/test_phase1_methods.py
git commit -m "feat: anchor leave-one-out beta update scale"
```

---

### Task 5: Add Delayed Beta Application Option

**Files:**
- Modify: `simulation/phase1/config.py`
- Modify: `simulation/phase1/algorithm.py`
- Test: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add config flag**

Add to `Phase1Config`:

```python
beta_update_apply_delay_samples: int = 1
```

- [ ] **Step 2: Apply beta updates after the current sample**

Inside `run_structural_phase_kalman`, store beta updates in a pending vector:

```python
pending_beta = beta.copy()
```

When beta LS produces `new_beta`, write:

```python
pending_beta[target_idx] = float(
    np.clip(beta[target_idx] + delta, config.beta_min_abs, config.beta_max_abs)
)
```

At the end of the sample, apply:

```python
if int(config.beta_update_apply_delay_samples) <= 0:
    beta[:] = pending_beta
elif sample_idx > 0:
    beta[:] = pending_beta
```

The first implementation can use a one-sample delay only; do not implement a general queue unless tests require it.

- [ ] **Step 3: Add test that current-sample LOS correction uses previous beta**

Create a small two-sample synthetic test where a beta update at sample 1 should not alter `los_corrected_phase_rad[:, 1]`. Assert the corrected LOS phase equals the value from the pre-update beta.

- [ ] **Step 4: Run focused and full method tests**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_methods
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add simulation/phase1/config.py simulation/phase1/algorithm.py tests/test_phase1_methods.py
git commit -m "feat: delay beta updates until after current correction"
```

---

### Task 6: Define Scenario Gates for Method Claims

**Files:**
- Modify: `simulation/phase1/evaluation.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add explicit beta convergence fields**

In `method_rows`, add fields:

```python
row["beta_initial_median_relative_error"] = _beta_initial_median_relative_error(
    result,
    radar,
    selected_indices_internal,
    target_reference_indices,
)
row["beta_improvement_ratio"] = (
    row["beta_median_relative_error"] / row["beta_initial_median_relative_error"]
    if row["beta_initial_median_relative_error"] > 0.0
    else float("nan")
)
```

- [ ] **Step 2: Add scenario-specific tests**

For `literature_maglev_modal_response` with `aoa_error_deg=10.0`, assert:

```python
self.assertLess(full["rmse_mm"], 0.015)
self.assertLess(full["beta_median_relative_error"], 0.12)
self.assertLess(full["beta_improvement_ratio"], 0.6)
```

For `vehicle_event_nonstationary`, assert only:

```python
self.assertLess(full["rmse_mm"], fixed["rmse_mm"])
self.assertLess(full["beta_median_relative_error"], full["beta_initial_median_relative_error"])
```

Do not assert target-wise convergence below 5% for vehicle events unless diagnostics support it.

- [ ] **Step 3: Run validation tests**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_validation
```

Expected: tests pass or fail with real numeric evidence. If a threshold fails, record the numeric result before changing the threshold.

- [ ] **Step 4: Commit**

```bash
git add simulation/phase1/evaluation.py tests/test_phase1_validation.py
git commit -m "test: gate beta bootstrap claims separately from displacement"
```

---

### Task 7: Generate Diagnostic Tables and Figures

**Files:**
- Modify: `simulation/phase1/reporting.py`
- Modify or create: `simulation/phase1/beta_bootstrap_diagnostics.py`
- Output: `simulation/outputs/phase1_validation/plots/*beta_bootstrap*.svg`

- [ ] **Step 1: Add diagnostic table output**

For each selected target, output:

```text
target_idx, reference_idx, beta_true, beta_initial, beta_final,
initial_relative_error, final_relative_error, last20_median_relative_error,
gate_on_ratio, abs_corr_median, residual_ratio_median
```

- [ ] **Step 2: Add figure rule**

The beta bootstrap figure title must say one of:

```text
beta self-calibration diagnostics
```

or:

```text
beta error reduction under AoA initialization bias
```

Do not title it `beta convergence` unless final relative error and last-20% median relative error both pass the scenario gate.

- [ ] **Step 3: Run validation report generation**

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m simulation.phase1.run_validation --scenario-set paper --output-dir simulation/outputs/phase1_validation
```

Expected: report writes metrics and plots without exceptions.

- [ ] **Step 4: Commit**

```bash
git add simulation/phase1/reporting.py simulation/phase1/beta_bootstrap_diagnostics.py simulation/outputs/phase1_validation
git commit -m "docs: report beta bootstrap diagnostics explicitly"
```

---

### Task 8: Update Thesis/PPT Method Claim

**Files:**
- Modify: `reports/phase1_method_and_simulation_report.md`
- Modify: `docs/algorithm_chain_review.md`
- Modify: `next_chat_memory_prompt.md`

- [ ] **Step 1: Update method statement**

Use this wording:

```markdown
本文不将同一 target 参与生成的后验结构相位直接作为该 target 的 beta 收敛证据。为避免自反馈，beta_i 的在线更新使用第 i 个 target 的 LOS corrected phase 与不含该 target 的结构方向参考状态进行最小二乘拟合；同时引入加速度参考或可靠几何 target 作为尺度锚定，以抑制多 target 共同尺度漂移。
```

- [ ] **Step 2: Update limitation statement**

Use this wording:

```markdown
车辆事件等短时非平稳激励场景可以验证 AoA 初值误差对位移估计影响被降低，但不必然证明所有 target-wise beta 均收敛到真值。beta 收敛应通过 target-wise beta error、last-window median error 和更新 gate 共同判断，不能由 displacement RMSE 单独替代。
```

- [ ] **Step 3: Search forbidden old wording**

Run:

```bash
rg -n "beta 收敛|target-wise beta|位移 RMSE.*beta|kappa|κ" reports/phase1_method_and_simulation_report.md docs/algorithm_chain_review.md next_chat_memory_prompt.md
```

Expected: no `kappa`/`κ`; beta convergence claims are qualified.

- [ ] **Step 4: Commit**

```bash
git add reports/phase1_method_and_simulation_report.md docs/algorithm_chain_review.md next_chat_memory_prompt.md
git commit -m "docs: qualify beta bootstrap convergence claims"
```

---

## Subagent Strategy

- Suitable for subagents:
  - Task 6 validation gates: independent from algorithm internals once method modes exist.
  - Task 7 diagnostic tables/figures: mostly reporting output, can be done in parallel with docs.
  - Task 8 thesis/PPT wording: documentation-only, no code writes overlapping with algorithm files.

- Not suitable for subagents:
  - Task 3 and Task 4 should be implemented by one agent because they both modify `simulation/phase1/algorithm.py` and depend on the exact beta update data flow.
  - Task 5 should also stay with the algorithm owner because delayed beta application can subtly change phase correction and beta histories.

- Recommended execution:
  - First run Tasks 1-5 sequentially in one coding stream.
  - Then parallelize Tasks 6-8 after method behavior is stable.

Because Tasks 6, 7, and 8 are independent and write mostly non-overlapping files, this plan is suitable for subagents after the core algorithm tasks are complete.

---

## Verification Checklist

Run:

```bash
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_methods
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_target_selection
/Users/umep/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_phase1_validation
git diff --check
```

Expected:

```text
OK
OK
OK
no output from git diff --check
```

If `tests.test_phase1_validation` fails, do not change thresholds until the failing numeric table is recorded in the final answer.
