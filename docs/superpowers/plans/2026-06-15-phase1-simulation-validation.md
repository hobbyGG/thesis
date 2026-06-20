# Phase 1 Simulation Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the phase-1 Python simulation so it validates the thesis algorithm innovations and determines whether the full multi-target radar + accelerometer displacement estimation system is feasible under controlled synthetic observations.

**Architecture:** Keep the existing `simulation/phase1` package and extend it from a data generator into a tested validation framework. The framework will generate known truth, radar wrapped phase, and accelerometer observations; run baselines and the proposed multi-target structural-main-phase Kalman method; compute metrics; and emit reproducible CSV/NPZ/Markdown/SVG artifacts for thesis analysis.

**Tech Stack:** Python 3.9, NumPy, standard-library `unittest`, standard-library `csv/json/pathlib`, no required SciPy/matplotlib/pandas dependency.

---

## Context For A No-Memory Agent

Start in `/Users/umep/thesis`. This repository is mostly thesis notes plus an early Python simulation package. Do not assume any conversation memory. Rebuild context from these files:

- `simulation/phase1/config.py`: current phase-1 configuration.
- `simulation/phase1/truth.py`: current multi-frequency displacement truth generator.
- `simulation/phase1/radar.py`: current multi-target radar IQ and wrapped phase generator.
- `simulation/phase1/accelerometer.py`: current noisy accelerometer generator.
- `simulation/phase1/run_phase1.py`: current single data-generation script.
- `tests/test_phase1_simulation.py`: current sanity tests.
- `simulation/phase1/README.md`: current phase-1 data description.
- `innovation_points/multi_target_phase_kalman_fusion.md`: thesis method definition.
- `simulation_design_literature_review.md`: simulation design and reference literature.

Current implementation status:

- The simulation can generate `q_m`, `v_mps`, `a_true_mps2`, `a_meas_mps2`, target-wise `kappa`, target-wise noisy complex `iq`, target-wise `wrapped_phase_rad`, target-wise true unwrapped `los_phase_rad`, and true structural `main_phase_rad`.
- Existing tests only verify data generator behavior. They do not verify the algorithm innovations.
- Default generated component frequencies are seeded near nominal 20, 40, and 60 Hz, with each value within +/-10 Hz and rounded to two decimals.
- Current environment has NumPy but may not have SciPy, matplotlib, pandas, or pytest. Use `python3 -m unittest`.

The proposed thesis method to validate:

- State variable is structural main phase, not single target LoS phase:
  `x_k = [Theta_k, dotTheta_k]^T`, `Theta_k = 4*pi*q_k/lambda`.
- Acceleration predicts structural main phase:
  `x_k^- = A x_{k-1} + B * (4*pi/lambda) * a_{k-1}`.
- Each radar target observes a projected LoS phase:
  `phi_i,k = kappa_i * Theta_k + b_i`.
- Target selection outputs wrapped phase only:
  `psi_i,k = angle(iq_i,k)`.
- AoA cold-start initializes:
  `kappa_hat_i,0 = cos(theta_i_measured)`.
- Prediction-assisted correction chooses the phase branch:
  `z_corr_i,k = psi_i,k + 2*pi*round((phi_hat_i,k^- - psi_i,k)/(2*pi))`.
- The same `z_corr_i,k` enters both Kalman measurement update and online kappa bootstrap.
- Online kappa bootstrap uses a sliding window:
  `kappa_hat_i = sum(Theta_hat * (z_corr_i - b_i)) / sum(Theta_hat^2)`.
- First implementation uses fixed process noise `Q` and target-wise adaptive measurement noise `R_i,k`.

Validation must answer two questions:

- Innovation validation: Does each innovation improve the correct failure mode?
- System feasibility: Does the complete method recover displacement accurately enough across nominal and adverse first-stage scenarios?

Use these feasibility gates for the phase-1 synthetic study:

- Nominal multi-frequency case: displacement RMSE <= 0.03 mm.
- Strong wrapping case: proposed unwrap error count <= 10% of Itoh unwrap error count, and proposed RMSE <= 0.08 mm.
- AoA error case: AoA cold start + bootstrap reaches median relative `kappa` error <= 5% after the configured warmup window.
- Target degradation case: adaptive-R proposed method has lower RMSE than fixed-R multi-target Kalman during the degradation interval.
- Multi-target case: proposed method outperforms single best target in at least 4 of 5 predefined scenarios.

These thresholds are starting feasibility thresholds for synthetic validation. If a threshold is missed, report it honestly and include the scenario artifacts; do not tune silently until it passes.

## File Structure

Create and modify these files:

- Modify `simulation/phase1/config.py`: add Kalman, bootstrap, scenario, target degradation, and mixed-scatterer configuration fields.
- Modify `simulation/phase1/radar.py`: add optional target degradation masks, AoA measurement error, and mixed-scatterer equivalent target generation.
- Create `simulation/phase1/phase_utils.py`: wrapping, Itoh unwrap, prediction-assisted correction, branch-error counting helpers.
- Create `simulation/phase1/metrics.py`: displacement, phase, unwrap, convergence, target degradation, and feasibility metrics.
- Create `simulation/phase1/methods.py`: method result dataclass and implementations for oracle, Itoh+LS, single-target Ma-style Kalman, multi-target fixed-kappa fixed-R Kalman, and proposed method.
- Create `simulation/phase1/scenarios.py`: deterministic scenario factory functions.
- Create `simulation/phase1/evaluate.py`: run methods on scenarios and compute metrics.
- Create `simulation/phase1/reporting.py`: write CSV, JSON summary, Markdown summary, and simple SVG line plots without matplotlib.
- Create `simulation/phase1/run_validation.py`: command-line entry point for full phase-1 validation.
- Modify `simulation/phase1/README.md`: document the full validation workflow.
- Modify `tests/test_phase1_simulation.py`: keep current generator tests and add config/scenario tests.
- Create `tests/test_phase1_phase_utils.py`: utility tests.
- Create `tests/test_phase1_metrics.py`: metrics tests.
- Create `tests/test_phase1_methods.py`: algorithm behavior tests.
- Create `tests/test_phase1_validation.py`: end-to-end validation smoke test.

All generated validation outputs should go under:

- `simulation/outputs/phase1_validation/`

Do not commit generated `.npz` outputs unless the user explicitly asks for committed artifacts.

## Task 1: Rebuild Context And Verify Current Baseline

**Files:**
- Read: `simulation/phase1/config.py`
- Read: `simulation/phase1/truth.py`
- Read: `simulation/phase1/radar.py`
- Read: `simulation/phase1/accelerometer.py`
- Read: `tests/test_phase1_simulation.py`
- Read: `innovation_points/multi_target_phase_kalman_fusion.md`
- Read: `simulation_design_literature_review.md`

- [ ] **Step 1: Inspect current files**

Run:

```bash
find simulation/phase1 tests -maxdepth 2 -type f | sort
```

Expected: current phase-1 Python files and `tests/test_phase1_simulation.py` are listed.

- [ ] **Step 2: Run the existing tests**

Run:

```bash
python3 -m unittest tests/test_phase1_simulation.py -v
```

Expected: existing tests pass before new work starts. If they fail, fix the current code before continuing.

- [ ] **Step 3: Regenerate the current dataset once**

Run:

```bash
python3 -m simulation.phase1.run_phase1 --output simulation/outputs/phase1_multifrequency.npz
```

Expected: command prints generated component frequencies near 20, 40, and 60 Hz and writes the `.npz` file.

- [ ] **Step 4: Summarize context in your implementation notes**

Record these facts in the task log:

```text
Current status: data generation only.
Missing pieces: baselines, proposed Kalman method, innovation ablations, feasibility report.
Algorithm state: structural main phase Theta, not target LoS phase.
First validation truth: multi-frequency vibration near 20/40/60 Hz.
```

## Task 2: Add Scenario And Kalman Configuration

**Files:**
- Modify: `simulation/phase1/config.py`
- Modify: `tests/test_phase1_simulation.py`

- [ ] **Step 1: Add failing tests for new config fields**

Append this test class to `tests/test_phase1_simulation.py`:

```python
class Phase1ConfigExtensionTest(unittest.TestCase):
    def test_default_kalman_and_bootstrap_config_values_are_available(self):
        config = Phase1Config()

        self.assertGreater(config.process_noise_intensity, 0.0)
        self.assertGreater(config.initial_state_variance, 0.0)
        self.assertGreater(config.initial_rate_variance, 0.0)
        self.assertGreater(config.initial_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.max_measurement_variance, config.min_measurement_variance)
        self.assertGreater(config.kappa_window_samples, 2)
        self.assertGreater(config.kappa_update_start_s, 0.0)
        self.assertGreater(config.adaptive_r_forgetting, 0.0)
        self.assertLess(config.adaptive_r_forgetting, 1.0)

    def test_default_scenario_controls_are_available(self):
        config = Phase1Config()

        self.assertEqual(config.scenario_name, "nominal_multifrequency")
        self.assertEqual(config.aoa_error_deg, 0.0)
        self.assertEqual(config.degraded_target_indices, ())
        self.assertEqual(config.dropout_target_indices, ())
        self.assertFalse(config.enable_mixed_scatterer_target)
```

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_simulation.py -v
```

Expected: fails because the new fields are not defined on `Phase1Config`.

- [ ] **Step 3: Extend `Phase1Config`**

Modify `simulation/phase1/config.py` so `Phase1Config` includes these fields:

```python
    scenario_name: str = "nominal_multifrequency"

    process_noise_intensity: float = 5.0
    initial_state_variance: float = 25.0
    initial_rate_variance: float = 25.0
    initial_measurement_variance: float = 9.0
    min_measurement_variance: float = 1.0e-4
    max_measurement_variance: float = 25.0
    adaptive_r_forgetting: float = 0.95

    kappa_window_samples: int = 80
    kappa_update_start_s: float = 0.25
    kappa_min_abs: float = 0.05
    kappa_max_abs: float = 1.2

    aoa_error_deg: float = 0.0

    degraded_target_indices: Sequence[int] = ()
    degradation_start_s: float = 2.0
    degradation_end_s: float = 3.2
    degradation_snr_drop_db: float = 20.0

    dropout_target_indices: Sequence[int] = ()
    dropout_start_s: float = 2.0
    dropout_end_s: float = 3.2

    enable_mixed_scatterer_target: bool = False
    mixed_target_index: int = 0
    mixed_scatterer_kappas: Sequence[float] = (0.95, 0.35)
    mixed_scatterer_amplitudes: Sequence[float] = (0.7, 0.6)
    mixed_scatterer_biases_rad: Sequence[float] = (0.0, 1.2)
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests/test_phase1_simulation.py -v
```

Expected: all tests in `tests/test_phase1_simulation.py` pass.

## Task 3: Extend Radar Simulation For Degradation, Dropout, AoA Error, And Mixed Scatterers

**Files:**
- Modify: `simulation/phase1/radar.py`
- Modify: `tests/test_phase1_simulation.py`

- [ ] **Step 1: Add failing radar scenario tests**

Append these tests to `Phase1SimulationTest` in `tests/test_phase1_simulation.py`:

```python
    def test_radar_target_degradation_reduces_iq_quality_inside_window(self):
        config = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=1000.0,
            seed=41,
            degraded_target_indices=(0,),
            degradation_start_s=1.0,
            degradation_end_s=2.0,
            degradation_snr_drop_db=30.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        in_window = (truth.t >= 1.0) & (truth.t <= 2.0)
        out_window = truth.t < 0.8
        clean = np.exp(1j * radar.true_los_phase_rad[0])
        err_in = np.mean(np.abs(radar.iq[0, in_window] - clean[in_window]) ** 2)
        err_out = np.mean(np.abs(radar.iq[0, out_window] - clean[out_window]) ** 2)

        self.assertGreater(err_in, err_out * 5.0)

    def test_radar_target_dropout_marks_phase_as_nan_inside_window(self):
        config = Phase1Config(
            duration_s=4.0,
            sample_rate_hz=1000.0,
            seed=42,
            dropout_target_indices=(1,),
            dropout_start_s=1.0,
            dropout_end_s=2.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        in_window = (truth.t >= 1.0) & (truth.t <= 2.0)
        out_window = truth.t < 0.8

        self.assertTrue(np.all(np.isnan(radar.wrapped_phase_rad[1, in_window])))
        self.assertFalse(np.any(np.isnan(radar.wrapped_phase_rad[1, out_window])))

    def test_aoa_error_changes_measured_kappa_but_not_true_kappa(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=43, aoa_error_deg=8.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        expected_measured = np.cos(np.deg2rad(radar.target_angles_deg + 8.0))
        np.testing.assert_allclose(radar.measured_kappa, expected_measured)
        self.assertGreater(np.max(np.abs(radar.measured_kappa - radar.kappa)), 1e-3)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_simulation.py -v
```

Expected: fails because degradation/dropout/measured_kappa behavior is not implemented.

- [ ] **Step 3: Modify `RadarObservation`**

Add these fields to the dataclass in `simulation/phase1/radar.py`:

```python
    measured_kappa: np.ndarray
    available_mask: np.ndarray
```

- [ ] **Step 4: Implement measured AoA kappa**

In `simulate_radar_targets`, after true `kappa` is computed, add:

```python
    measured_angles_deg = angles_deg + float(config.aoa_error_deg)
    measured_kappa = np.cos(np.deg2rad(measured_angles_deg))
```

Return `measured_kappa=measured_kappa`.

- [ ] **Step 5: Implement mixed-scatterer equivalent target**

After `clean_iq` is created and before adding noise, add:

```python
    if config.enable_mixed_scatterer_target:
        idx = int(config.mixed_target_index)
        kappas = np.asarray(config.mixed_scatterer_kappas, dtype=float)
        amps = np.asarray(config.mixed_scatterer_amplitudes, dtype=float)
        biases = np.asarray(config.mixed_scatterer_biases_rad, dtype=float)
        if kappas.size != amps.size or kappas.size != biases.size:
            raise ValueError("mixed scatterer kappas, amplitudes, and biases must have the same length")
        mixed = np.zeros_like(clean_iq[idx])
        for scatter_kappa, scatter_amp, scatter_bias in zip(kappas, amps, biases):
            mixed += scatter_amp * np.exp(1j * (scatter_kappa * true_main_phase_rad + scatter_bias))
        clean_iq[idx] = mixed
```

- [ ] **Step 6: Implement degradation and dropout**

After `noise` is created and before `iq = clean_iq + noise`, add:

```python
    available_mask = np.ones(clean_iq.shape, dtype=bool)
    if config.degraded_target_indices:
        in_degradation = (truth.t >= config.degradation_start_s) & (truth.t <= config.degradation_end_s)
        factor = 10.0 ** (float(config.degradation_snr_drop_db) / 20.0)
        for idx in config.degraded_target_indices:
            noise[int(idx), in_degradation] *= factor
    if config.dropout_target_indices:
        in_dropout = (truth.t >= config.dropout_start_s) & (truth.t <= config.dropout_end_s)
        for idx in config.dropout_target_indices:
            available_mask[int(idx), in_dropout] = False
```

After `wrapped_phase_rad = np.angle(iq)`, add:

```python
    wrapped_phase_rad = wrapped_phase_rad.astype(float)
    wrapped_phase_rad[~available_mask] = np.nan
    iq = iq.astype(complex)
    iq[~available_mask] = np.nan + 1j * np.nan
```

Return `available_mask=available_mask`.

- [ ] **Step 7: Run tests**

Run:

```bash
python3 -m unittest tests/test_phase1_simulation.py -v
```

Expected: all tests pass.

## Task 4: Add Phase Utility Functions

**Files:**
- Create: `simulation/phase1/phase_utils.py`
- Create: `tests/test_phase1_phase_utils.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_phase1_phase_utils.py`:

```python
import math
import unittest

import numpy as np

from simulation.phase1.phase_utils import (
    count_branch_errors,
    itoh_unwrap,
    prediction_correct_wrapped_phase,
    wrap_to_pi,
)


class PhaseUtilsTest(unittest.TestCase):
    def test_wrap_to_pi_returns_open_left_closed_right_interval(self):
        values = np.array([-3.0 * math.pi, -math.pi, -0.1, 0.0, math.pi, 3.0 * math.pi])
        wrapped = wrap_to_pi(values)

        self.assertTrue(np.all(wrapped > -math.pi))
        self.assertTrue(np.all(wrapped <= math.pi))
        self.assertAlmostEqual(wrapped[1], math.pi)
        self.assertAlmostEqual(wrapped[4], math.pi)

    def test_prediction_correct_wrapped_phase_selects_nearest_branch(self):
        true_phase = 5.8
        wrapped = wrap_to_pi(true_phase)
        corrected = prediction_correct_wrapped_phase(wrapped, prediction=6.0)

        self.assertAlmostEqual(float(corrected), true_phase, places=12)

    def test_itoh_unwrap_recovers_slow_phase_but_not_large_jump(self):
        slow = np.array([0.1, 0.4, 0.7, 1.0])
        np.testing.assert_allclose(itoh_unwrap(wrap_to_pi(slow)), slow)

        large = np.array([0.1, 3.8])
        unwrapped = itoh_unwrap(wrap_to_pi(large))
        self.assertGreater(abs(unwrapped[-1] - large[-1]), math.pi)

    def test_count_branch_errors_counts_two_pi_branch_mismatches(self):
        truth = np.array([0.0, 2.0 * math.pi + 0.1, 4.0 * math.pi + 0.2])
        estimate = np.array([0.0, 0.1, 4.0 * math.pi + 0.2])

        self.assertEqual(count_branch_errors(estimate, truth), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_phase_utils.py -v
```

Expected: fails because `simulation.phase1.phase_utils` does not exist.

- [ ] **Step 3: Implement `phase_utils.py`**

Create `simulation/phase1/phase_utils.py` with:

```python
import numpy as np


def wrap_to_pi(values):
    arr = np.asarray(values, dtype=float)
    wrapped = (arr + np.pi) % (2.0 * np.pi) - np.pi
    return np.where(wrapped <= -np.pi, wrapped + 2.0 * np.pi, wrapped)


def prediction_correct_wrapped_phase(wrapped, prediction):
    wrapped_arr = np.asarray(wrapped, dtype=float)
    prediction_arr = np.asarray(prediction, dtype=float)
    return wrapped_arr + 2.0 * np.pi * np.round((prediction_arr - wrapped_arr) / (2.0 * np.pi))


def itoh_unwrap(wrapped_phase):
    return np.unwrap(np.asarray(wrapped_phase, dtype=float))


def count_branch_errors(estimated_phase, true_phase, tolerance=np.pi):
    estimated = np.asarray(estimated_phase, dtype=float)
    truth = np.asarray(true_phase, dtype=float)
    valid = np.isfinite(estimated) & np.isfinite(truth)
    if not np.any(valid):
        return 0
    branch_error = np.abs(estimated[valid] - truth[valid]) > float(tolerance)
    return int(np.count_nonzero(branch_error))
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests/test_phase1_phase_utils.py -v
```

Expected: all phase utility tests pass.

## Task 5: Add Metrics And Feasibility Gates

**Files:**
- Create: `simulation/phase1/metrics.py`
- Create: `tests/test_phase1_metrics.py`

- [ ] **Step 1: Write failing metrics tests**

Create `tests/test_phase1_metrics.py`:

```python
import unittest

import numpy as np

from simulation.phase1.metrics import (
    FeasibilityGate,
    convergence_time_s,
    displacement_metrics,
    evaluate_gate,
    interval_mask,
)


class Phase1MetricsTest(unittest.TestCase):
    def test_displacement_metrics_are_reported_in_mm(self):
        truth = np.array([0.0, 0.001, 0.002])
        estimate = np.array([0.0, 0.0015, 0.001])

        metrics = displacement_metrics(estimate, truth)

        self.assertAlmostEqual(metrics["rmse_mm"], 0.6454972243679028)
        self.assertAlmostEqual(metrics["mae_mm"], 0.5)
        self.assertAlmostEqual(metrics["max_error_mm"], 1.0)

    def test_interval_mask_selects_closed_time_window(self):
        t = np.array([0.0, 0.5, 1.0, 1.5])
        mask = interval_mask(t, 0.5, 1.0)

        np.testing.assert_array_equal(mask, np.array([False, True, True, False]))

    def test_convergence_time_returns_first_sustained_time(self):
        t = np.arange(6, dtype=float)
        estimate = np.array([0.6, 0.4, 0.2, 0.04, 0.03, 0.02])
        truth = np.ones_like(estimate)

        self.assertEqual(convergence_time_s(t, estimate, truth, relative_tol=0.05, sustain_samples=2), 3.0)

    def test_feasibility_gate_passes_when_value_is_below_threshold(self):
        gate = FeasibilityGate(name="nominal_rmse", metric="rmse_mm", max_value=0.03)

        self.assertTrue(evaluate_gate({"rmse_mm": 0.02}, gate)["passed"])
        self.assertFalse(evaluate_gate({"rmse_mm": 0.04}, gate)["passed"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_metrics.py -v
```

Expected: fails because `metrics.py` does not exist.

- [ ] **Step 3: Implement `metrics.py`**

Create `simulation/phase1/metrics.py` with:

```python
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FeasibilityGate:
    name: str
    metric: str
    max_value: float


def _valid_pair(estimate, truth):
    estimate_arr = np.asarray(estimate, dtype=float)
    truth_arr = np.asarray(truth, dtype=float)
    valid = np.isfinite(estimate_arr) & np.isfinite(truth_arr)
    return estimate_arr[valid], truth_arr[valid]


def displacement_metrics(estimate_m, truth_m):
    estimate, truth = _valid_pair(estimate_m, truth_m)
    if estimate.size == 0:
        return {"rmse_mm": float("nan"), "mae_mm": float("nan"), "max_error_mm": float("nan")}
    error_mm = (estimate - truth) * 1.0e3
    return {
        "rmse_mm": float(np.sqrt(np.mean(error_mm**2))),
        "mae_mm": float(np.mean(np.abs(error_mm))),
        "max_error_mm": float(np.max(np.abs(error_mm))),
    }


def phase_rmse_rad(estimate_rad, truth_rad):
    estimate, truth = _valid_pair(estimate_rad, truth_rad)
    if estimate.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((estimate - truth) ** 2)))


def interval_mask(t, start_s, end_s):
    arr = np.asarray(t, dtype=float)
    return (arr >= float(start_s)) & (arr <= float(end_s))


def convergence_time_s(t, estimate, truth, relative_tol=0.05, sustain_samples=20):
    t_arr = np.asarray(t, dtype=float)
    est = np.asarray(estimate, dtype=float)
    ref = np.asarray(truth, dtype=float)
    denom = np.maximum(np.abs(ref), 1.0e-12)
    ok = np.abs(est - ref) / denom <= float(relative_tol)
    required = int(sustain_samples)
    if required <= 1:
        matches = np.flatnonzero(ok)
        return float(t_arr[matches[0]]) if matches.size else float("nan")
    for idx in range(0, ok.size - required + 1):
        if np.all(ok[idx : idx + required]):
            return float(t_arr[idx])
    return float("nan")


def evaluate_gate(metrics, gate):
    value = float(metrics.get(gate.metric, float("nan")))
    passed = np.isfinite(value) and value <= float(gate.max_value)
    return {"name": gate.name, "metric": gate.metric, "value": value, "max_value": gate.max_value, "passed": bool(passed)}
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests/test_phase1_metrics.py -v
```

Expected: all metrics tests pass.

## Task 6: Implement Method Result Types And Simple Baselines

**Files:**
- Create: `simulation/phase1/methods.py`
- Create: `tests/test_phase1_methods.py`

- [ ] **Step 1: Write failing tests for oracle and Itoh baselines**

Create `tests/test_phase1_methods.py`:

```python
import unittest

import numpy as np

from simulation.phase1.config import Phase1Config
from simulation.phase1.methods import estimate_itoh_ls, estimate_oracle
from simulation.phase1.radar import simulate_radar_targets
from simulation.phase1.truth import generate_multifrequency_truth


class Phase1MethodsTest(unittest.TestCase):
    def test_oracle_recovers_truth_from_true_main_phase(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=101)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_oracle(truth, radar, config)

        np.testing.assert_allclose(result.q_hat_m, truth.q_m, atol=1e-15)
        self.assertEqual(result.method_name, "oracle")

    def test_itoh_ls_works_in_clean_single_target_small_motion_case(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=102,
            component_amplitudes_mm=(0.01, 0.005, 0.002),
            target_snr_db=(80.0, 80.0, 80.0, 80.0, 80.0),
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_itoh_ls(truth, radar, config, target_index=0)
        rmse_mm = np.sqrt(np.mean((result.q_hat_m - truth.q_m) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.005)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: fails because `methods.py` does not exist.

- [ ] **Step 3: Implement `MethodResult`, oracle, and Itoh+LS**

Create `simulation/phase1/methods.py` with:

```python
from dataclasses import dataclass, field

import numpy as np

from .phase_utils import itoh_unwrap


@dataclass(frozen=True)
class MethodResult:
    method_name: str
    q_hat_m: np.ndarray
    theta_hat_rad: np.ndarray
    theta_dot_hat_radps: np.ndarray
    corrected_phase_rad: np.ndarray
    kappa_hat: np.ndarray
    r_history: np.ndarray
    innovation_rad: np.ndarray
    extra: dict = field(default_factory=dict)


def _phase_to_displacement(theta_rad, config):
    return np.asarray(theta_rad, dtype=float) * config.wavelength_m() / (4.0 * np.pi)


def estimate_oracle(truth, radar, config):
    theta = np.asarray(radar.true_main_phase_rad, dtype=float)
    dt = 1.0 / config.sample_rate_hz
    theta_dot = np.gradient(theta, dt)
    empty_targets = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    return MethodResult(
        method_name="oracle",
        q_hat_m=truth.q_m.copy(),
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=radar.true_los_phase_rad.copy(),
        kappa_hat=radar.kappa.copy(),
        r_history=empty_targets.copy(),
        innovation_rad=empty_targets.copy(),
        extra={},
    )


def estimate_itoh_ls(truth, radar, config, target_index=0):
    idx = int(target_index)
    wrapped = radar.wrapped_phase_rad[idx]
    valid = np.isfinite(wrapped)
    corrected = np.full_like(wrapped, np.nan, dtype=float)
    corrected[valid] = itoh_unwrap(wrapped[valid])
    if np.any(valid):
        corrected[valid] -= corrected[valid][0] - radar.true_los_phase_rad[idx, valid][0]
    kappa = float(radar.kappa[idx])
    theta = (corrected - radar.true_los_phase_rad[idx, 0] + kappa * radar.true_main_phase_rad[0]) / max(abs(kappa), 1e-12)
    dt = 1.0 / config.sample_rate_hz
    theta_dot = np.gradient(np.nan_to_num(theta, nan=0.0), dt)
    corrected_all = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    corrected_all[idx] = corrected
    return MethodResult(
        method_name="itoh_ls",
        q_hat_m=_phase_to_displacement(theta, config),
        theta_hat_rad=theta,
        theta_dot_hat_radps=theta_dot,
        corrected_phase_rad=corrected_all,
        kappa_hat=np.full(radar.kappa.shape, np.nan, dtype=float),
        r_history=np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float),
        innovation_rad=np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float),
        extra={"target_index": idx},
    )
```

- [ ] **Step 4: Run method tests**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: oracle and Itoh tests pass.

## Task 7: Implement Multi-Target Kalman Core

**Files:**
- Modify: `simulation/phase1/methods.py`
- Modify: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add failing tests for fixed-kappa multi-target Kalman and proposed method**

Append to `tests/test_phase1_methods.py`:

```python
from simulation.phase1.methods import estimate_multitarget_fixed, estimate_proposed


class Phase1KalmanMethodsTest(unittest.TestCase):
    def test_multitarget_fixed_kappa_recovers_clean_multitarget_case(self):
        config = Phase1Config(
            duration_s=1.0,
            sample_rate_hz=1000.0,
            seed=111,
            component_amplitudes_mm=(0.02, 0.01, 0.005),
            target_snr_db=(70.0, 70.0, 70.0, 70.0, 70.0),
            accel_noise_std_mps2=0.0,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_multitarget_fixed(truth, radar, config)
        rmse_mm = np.sqrt(np.mean((result.q_hat_m - truth.q_m) ** 2)) * 1e3

        self.assertLess(rmse_mm, 0.01)

    def test_proposed_updates_kappa_from_aoa_initial_values(self):
        config = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=1000.0,
            seed=112,
            aoa_error_deg=8.0,
            target_snr_db=(40.0, 40.0, 40.0, 40.0, 40.0),
            accel_noise_std_mps2=0.0,
            kappa_update_start_s=0.1,
            kappa_window_samples=40,
        )
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_proposed(truth, radar, config)
        initial_error = np.median(np.abs(radar.measured_kappa - radar.kappa))
        final_error = np.median(np.abs(result.kappa_hat - radar.kappa))

        self.assertLess(final_error, initial_error)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: fails because `estimate_multitarget_fixed` and `estimate_proposed` are not implemented.

- [ ] **Step 3: Add shared Kalman helpers**

In `simulation/phase1/methods.py`, add helper functions:

```python
def _state_matrices(config):
    dt = 1.0 / config.sample_rate_hz
    a = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b = np.array([0.5 * dt * dt, dt], dtype=float)
    q0 = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q = float(config.process_noise_intensity) * q0
    return a, b, q


def _initial_state(truth, radar, config):
    theta0 = float(radar.true_main_phase_rad[0])
    return np.array([theta0, 0.0], dtype=float)


def _phase_accel_input(accel_mps2, config):
    return (4.0 * np.pi / config.wavelength_m()) * float(accel_mps2)


def _safe_inverse(matrix):
    return np.linalg.pinv(matrix)
```

- [ ] **Step 4: Implement fixed-kappa multi-target Kalman**

Add `estimate_multitarget_fixed`:

```python
def estimate_multitarget_fixed(truth, radar, config):
    return _run_structural_phase_kalman(
        method_name="multitarget_fixed",
        truth=truth,
        radar=radar,
        config=config,
        initial_kappa=radar.kappa.copy(),
        update_kappa=False,
        adaptive_r=False,
    )
```

- [ ] **Step 5: Implement proposed method entry**

Add `estimate_proposed`:

```python
def estimate_proposed(truth, radar, config):
    return _run_structural_phase_kalman(
        method_name="proposed",
        truth=truth,
        radar=radar,
        config=config,
        initial_kappa=radar.measured_kappa.copy(),
        update_kappa=True,
        adaptive_r=True,
    )
```

- [ ] **Step 6: Implement `_run_structural_phase_kalman`**

Add this function to `methods.py`:

```python
def _run_structural_phase_kalman(method_name, truth, radar, config, initial_kappa, update_kappa, adaptive_r):
    n_targets, n_samples = radar.wrapped_phase_rad.shape
    a_mat, b_vec, q_mat = _state_matrices(config)
    x = _initial_state(truth, radar, config)
    p = np.diag([config.initial_state_variance, config.initial_rate_variance])
    kappa = np.asarray(initial_kappa, dtype=float).copy()
    kappa = np.clip(kappa, -config.kappa_max_abs, config.kappa_max_abs)
    small = np.abs(kappa) < config.kappa_min_abs
    kappa[small] = np.sign(kappa[small] + 1e-12) * config.kappa_min_abs

    theta_hat = np.zeros(n_samples, dtype=float)
    theta_dot_hat = np.zeros(n_samples, dtype=float)
    corrected = np.full((n_targets, n_samples), np.nan, dtype=float)
    innovations = np.full((n_targets, n_samples), np.nan, dtype=float)
    r_values = np.full(n_targets, float(config.initial_measurement_variance), dtype=float)
    r_history = np.full((n_targets, n_samples), np.nan, dtype=float)
    kappa_history = np.full((n_targets, n_samples), np.nan, dtype=float)

    target_bias = radar.true_los_phase_rad[:, 0] - radar.kappa * radar.true_main_phase_rad[0]
    warmup_index = int(round(config.kappa_update_start_s * config.sample_rate_hz))

    for sample_idx in range(n_samples):
        accel_idx = max(sample_idx - 1, 0)
        u = _phase_accel_input(truth.a_mps2[accel_idx], config)
        if sample_idx > 0:
            x_pred = a_mat @ x + b_vec * u
            p_pred = a_mat @ p @ a_mat.T + q_mat
        else:
            x_pred = x
            p_pred = p

        available = np.isfinite(radar.wrapped_phase_rad[:, sample_idx])
        active_indices = np.flatnonzero(available)
        if active_indices.size:
            h_rows = []
            z_rows = []
            bias_rows = []
            r_rows = []
            for target_idx in active_indices:
                prediction = kappa[target_idx] * x_pred[0] + target_bias[target_idx]
                z_corr = prediction_correct_wrapped_phase(radar.wrapped_phase_rad[target_idx, sample_idx], prediction)
                corrected[target_idx, sample_idx] = z_corr
                h_rows.append([kappa[target_idx], 0.0])
                z_rows.append(z_corr)
                bias_rows.append(target_bias[target_idx])
                r_rows.append(r_values[target_idx])

            h = np.asarray(h_rows, dtype=float)
            z = np.asarray(z_rows, dtype=float)
            bias_vec_obs = np.asarray(bias_rows, dtype=float)
            r_mat = np.diag(np.asarray(r_rows, dtype=float))
            innovation = z - (h @ x_pred + bias_vec_obs)
            s_mat = h @ p_pred @ h.T + r_mat
            k_gain = p_pred @ h.T @ _safe_inverse(s_mat)
            x = x_pred + k_gain @ innovation
            p = (np.eye(2) - k_gain @ h) @ p_pred

            for local_idx, target_idx in enumerate(active_indices):
                innovations[target_idx, sample_idx] = innovation[local_idx]
                if adaptive_r:
                    h_i = h[local_idx : local_idx + 1]
                    post_var = float(h_i @ p @ h_i.T)
                    instant_r = float(innovation[local_idx] ** 2 + post_var)
                    blended = config.adaptive_r_forgetting * r_values[target_idx] + (1.0 - config.adaptive_r_forgetting) * instant_r
                    r_values[target_idx] = float(np.clip(blended, config.min_measurement_variance, config.max_measurement_variance))
        else:
            x = x_pred
            p = p_pred

        theta_hat[sample_idx] = x[0]
        theta_dot_hat[sample_idx] = x[1]
        r_history[:, sample_idx] = r_values

        if update_kappa and sample_idx >= warmup_index:
            start = max(0, sample_idx - int(config.kappa_window_samples) + 1)
            theta_window = theta_hat[start : sample_idx + 1]
            denom = float(np.sum(theta_window**2))
            if denom > 1e-12:
                for target_idx in range(n_targets):
                    z_window = corrected[target_idx, start : sample_idx + 1]
                    valid = np.isfinite(z_window)
                    if np.count_nonzero(valid) >= 3:
                        numerator = float(np.sum(theta_window[valid] * (z_window[valid] - target_bias[target_idx])))
                        new_kappa = numerator / denom
                        if abs(new_kappa) >= config.kappa_min_abs:
                            kappa[target_idx] = float(np.clip(new_kappa, -config.kappa_max_abs, config.kappa_max_abs))
        kappa_history[:, sample_idx] = kappa

    return MethodResult(
        method_name=method_name,
        q_hat_m=_phase_to_displacement(theta_hat, config),
        theta_hat_rad=theta_hat,
        theta_dot_hat_radps=theta_dot_hat,
        corrected_phase_rad=corrected,
        kappa_hat=kappa.copy(),
        r_history=r_history,
        innovation_rad=innovations,
        extra={"kappa_history": kappa_history},
    )
```

Also import `prediction_correct_wrapped_phase` at the top:

```python
from .phase_utils import itoh_unwrap, prediction_correct_wrapped_phase
```

- [ ] **Step 7: Run method tests**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: all method tests pass.

## Task 8: Implement Single-Target Ma-Style Baseline

**Files:**
- Modify: `simulation/phase1/methods.py`
- Modify: `tests/test_phase1_methods.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_phase1_methods.py`:

```python
from simulation.phase1.methods import estimate_single_target_ma_style


class Phase1SingleTargetBaselineTest(unittest.TestCase):
    def test_single_target_ma_style_uses_one_target_only(self):
        config = Phase1Config(duration_s=1.0, sample_rate_hz=1000.0, seed=121, accel_noise_std_mps2=0.0)
        truth = generate_multifrequency_truth(config)
        radar = simulate_radar_targets(truth, config)

        result = estimate_single_target_ma_style(truth, radar, config, target_index=0)

        self.assertEqual(result.method_name, "single_target_ma_style")
        used_targets = np.flatnonzero(np.any(np.isfinite(result.corrected_phase_rad), axis=1))
        np.testing.assert_array_equal(used_targets, np.array([0]))
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: fails because `estimate_single_target_ma_style` is not implemented.

- [ ] **Step 3: Implement single-target baseline**

Add to `methods.py`:

```python
def estimate_single_target_ma_style(truth, radar, config, target_index=0):
    idx = int(target_index)
    single_radar = _single_target_view(radar, idx)
    single_result = _run_structural_phase_kalman(
        method_name="single_target_ma_style",
        truth=truth,
        radar=single_radar,
        config=config,
        initial_kappa=np.array([radar.kappa[idx]], dtype=float),
        update_kappa=False,
        adaptive_r=True,
    )
    corrected = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    innovation = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    r_history = np.full_like(radar.wrapped_phase_rad, np.nan, dtype=float)
    corrected[idx] = single_result.corrected_phase_rad[0]
    innovation[idx] = single_result.innovation_rad[0]
    r_history[idx] = single_result.r_history[0]
    return MethodResult(
        method_name="single_target_ma_style",
        q_hat_m=single_result.q_hat_m,
        theta_hat_rad=single_result.theta_hat_rad,
        theta_dot_hat_radps=single_result.theta_dot_hat_radps,
        corrected_phase_rad=corrected,
        kappa_hat=np.full(radar.kappa.shape, np.nan, dtype=float),
        r_history=r_history,
        innovation_rad=innovation,
        extra={"target_index": idx},
    )
```

Add helper:

```python
def _single_target_view(radar, idx):
    from dataclasses import replace

    target_slice = slice(idx, idx + 1)
    return replace(
        radar,
        kappa=radar.kappa[target_slice],
        measured_kappa=radar.measured_kappa[target_slice],
        target_angles_deg=radar.target_angles_deg[target_slice],
        snr_db=radar.snr_db[target_slice],
        true_los_phase_rad=radar.true_los_phase_rad[target_slice],
        iq=radar.iq[target_slice],
        wrapped_phase_rad=radar.wrapped_phase_rad[target_slice],
        available_mask=radar.available_mask[target_slice],
    )
```

- [ ] **Step 4: Run method tests**

Run:

```bash
python3 -m unittest tests/test_phase1_methods.py -v
```

Expected: all method tests pass.

## Task 9: Add Scenarios For Innovation Validation

**Files:**
- Create: `simulation/phase1/scenarios.py`
- Create: `tests/test_phase1_validation.py`

- [ ] **Step 1: Write failing scenario tests**

Create `tests/test_phase1_validation.py`:

```python
import unittest

from simulation.phase1.scenarios import build_phase1_scenarios


class Phase1ScenarioTest(unittest.TestCase):
    def test_phase1_scenarios_cover_required_innovation_cases(self):
        scenarios = build_phase1_scenarios()
        names = [scenario.scenario_name for scenario in scenarios]

        self.assertIn("nominal_multifrequency", names)
        self.assertIn("strong_wrapping", names)
        self.assertIn("aoa_error_bootstrap", names)
        self.assertIn("target_snr_drop", names)
        self.assertIn("target_dropout", names)
        self.assertIn("mixed_scatterer_rangebin", names)
        self.assertIn("low_snr_multitarget", names)
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: fails because `scenarios.py` does not exist.

- [ ] **Step 3: Implement scenario factory**

Create `simulation/phase1/scenarios.py`:

```python
from dataclasses import replace

from .config import Phase1Config


def build_phase1_scenarios():
    base = Phase1Config()
    return [
        replace(base, scenario_name="nominal_multifrequency"),
        replace(
            base,
            scenario_name="strong_wrapping",
            component_amplitudes_mm=(0.45, 0.25, 0.12),
            target_snr_db=(30.0, 25.0, 20.0, 15.0, 10.0),
        ),
        replace(
            base,
            scenario_name="aoa_error_bootstrap",
            aoa_error_deg=10.0,
            kappa_update_start_s=0.2,
            kappa_window_samples=80,
        ),
        replace(
            base,
            scenario_name="target_snr_drop",
            degraded_target_indices=(0, 1),
            degradation_start_s=1.6,
            degradation_end_s=3.4,
            degradation_snr_drop_db=25.0,
        ),
        replace(
            base,
            scenario_name="target_dropout",
            dropout_target_indices=(0,),
            dropout_start_s=1.6,
            dropout_end_s=3.4,
        ),
        replace(
            base,
            scenario_name="mixed_scatterer_rangebin",
            enable_mixed_scatterer_target=True,
            mixed_target_index=0,
            mixed_scatterer_kappas=(0.95, 0.35),
            mixed_scatterer_amplitudes=(0.7, 0.6),
            mixed_scatterer_biases_rad=(0.0, 1.2),
        ),
        replace(
            base,
            scenario_name="low_snr_multitarget",
            target_snr_db=(12.0, 10.0, 8.0, 6.0, 4.0),
        ),
    ]
```

- [ ] **Step 4: Run scenario tests**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: scenario tests pass.

## Task 10: Add Evaluation Runner

**Files:**
- Create: `simulation/phase1/evaluate.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add failing evaluation smoke test**

Append to `tests/test_phase1_validation.py`:

```python
from simulation.phase1.evaluate import evaluate_scenario


class Phase1EvaluationTest(unittest.TestCase):
    def test_evaluate_scenario_returns_metrics_for_all_core_methods(self):
        scenario = build_phase1_scenarios()[0]
        rows, artifacts = evaluate_scenario(scenario)
        method_names = {row["method"] for row in rows}

        self.assertIn("oracle", method_names)
        self.assertIn("itoh_ls", method_names)
        self.assertIn("single_target_ma_style", method_names)
        self.assertIn("multitarget_fixed", method_names)
        self.assertIn("proposed", method_names)
        self.assertIn("truth", artifacts)
        self.assertIn("radar", artifacts)
        self.assertIn("results", artifacts)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: fails because `evaluate.py` does not exist.

- [ ] **Step 3: Implement `evaluate.py`**

Create `simulation/phase1/evaluate.py`:

```python
import numpy as np

from .accelerometer import simulate_accelerometer
from .metrics import displacement_metrics, phase_rmse_rad
from .methods import (
    estimate_itoh_ls,
    estimate_multitarget_fixed,
    estimate_oracle,
    estimate_proposed,
    estimate_single_target_ma_style,
)
from .phase_utils import count_branch_errors
from .radar import simulate_radar_targets
from .truth import generate_multifrequency_truth


def _best_target_index(radar):
    snr = np.asarray(radar.snr_db, dtype=float)
    return int(np.nanargmax(snr))


def _method_rows(scenario, truth, radar, results):
    rows = []
    for result in results:
        disp = displacement_metrics(result.q_hat_m, truth.q_m)
        phase_rmse = phase_rmse_rad(result.theta_hat_rad, radar.true_main_phase_rad)
        corrected_errors = []
        for target_idx in range(radar.true_los_phase_rad.shape[0]):
            corrected_errors.append(count_branch_errors(result.corrected_phase_rad[target_idx], radar.true_los_phase_rad[target_idx]))
        row = {
            "scenario": scenario.scenario_name,
            "method": result.method_name,
            "rmse_mm": disp["rmse_mm"],
            "mae_mm": disp["mae_mm"],
            "max_error_mm": disp["max_error_mm"],
            "theta_rmse_rad": phase_rmse,
            "unwrap_errors": int(np.sum(corrected_errors)),
        }
        rows.append(row)
    return rows


def evaluate_scenario(scenario):
    truth = generate_multifrequency_truth(scenario)
    radar = simulate_radar_targets(truth, scenario)
    accel = simulate_accelerometer(truth, scenario)
    best_idx = _best_target_index(radar)
    results = [
        estimate_oracle(truth, radar, scenario),
        estimate_itoh_ls(truth, radar, scenario, target_index=best_idx),
        estimate_single_target_ma_style(truth, radar, scenario, target_index=best_idx),
        estimate_multitarget_fixed(truth, radar, scenario),
        estimate_proposed(truth, radar, scenario),
    ]
    rows = _method_rows(scenario, truth, radar, results)
    artifacts = {"truth": truth, "radar": radar, "accelerometer": accel, "results": results}
    return rows, artifacts
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: validation tests pass.

## Task 11: Add Feasibility And Innovation Gate Evaluation

**Files:**
- Modify: `simulation/phase1/evaluate.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add failing gate test**

Append to `tests/test_phase1_validation.py`:

```python
from simulation.phase1.evaluate import evaluate_all_scenarios


class Phase1FeasibilityTest(unittest.TestCase):
    def test_evaluate_all_scenarios_reports_feasibility_gates(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:2])

        self.assertIn("rows", summary)
        self.assertIn("gates", summary)
        self.assertGreater(len(summary["rows"]), 0)
        self.assertGreater(len(summary["gates"]), 0)
        self.assertTrue(all("passed" in gate for gate in summary["gates"]))
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: fails because `evaluate_all_scenarios` is not implemented.

- [ ] **Step 3: Implement gate evaluation**

Add to `evaluate.py`:

```python
def _row_lookup(rows, scenario, method):
    for row in rows:
        if row["scenario"] == scenario and row["method"] == method:
            return row
    return None


def _build_gate_results(rows):
    gates = []
    nominal = _row_lookup(rows, "nominal_multifrequency", "proposed")
    if nominal:
        gates.append({
            "name": "nominal_proposed_rmse_le_0p03mm",
            "value": nominal["rmse_mm"],
            "threshold": 0.03,
            "passed": bool(nominal["rmse_mm"] <= 0.03),
        })

    strong_prop = _row_lookup(rows, "strong_wrapping", "proposed")
    strong_itoh = _row_lookup(rows, "strong_wrapping", "itoh_ls")
    if strong_prop and strong_itoh:
        gates.append({
            "name": "strong_wrapping_rmse_le_0p08mm",
            "value": strong_prop["rmse_mm"],
            "threshold": 0.08,
            "passed": bool(strong_prop["rmse_mm"] <= 0.08),
        })
        gates.append({
            "name": "strong_wrapping_unwrap_errors_le_10pct_itoh",
            "value": strong_prop["unwrap_errors"],
            "threshold": max(1, 0.1 * strong_itoh["unwrap_errors"]),
            "passed": bool(strong_prop["unwrap_errors"] <= max(1, 0.1 * strong_itoh["unwrap_errors"])),
        })

    snr_prop = _row_lookup(rows, "target_snr_drop", "proposed")
    snr_fixed = _row_lookup(rows, "target_snr_drop", "multitarget_fixed")
    if snr_prop and snr_fixed:
        gates.append({
            "name": "target_snr_drop_proposed_beats_fixed_r",
            "value": snr_prop["rmse_mm"],
            "threshold": snr_fixed["rmse_mm"],
            "passed": bool(snr_prop["rmse_mm"] < snr_fixed["rmse_mm"]),
        })

    wins = 0
    comparisons = 0
    for scenario_name in sorted({row["scenario"] for row in rows}):
        prop = _row_lookup(rows, scenario_name, "proposed")
        single = _row_lookup(rows, scenario_name, "single_target_ma_style")
        if prop and single:
            comparisons += 1
            if prop["rmse_mm"] < single["rmse_mm"]:
                wins += 1
    if comparisons:
        gates.append({
            "name": "proposed_beats_single_target_in_at_least_4_scenarios",
            "value": wins,
            "threshold": 4,
            "passed": bool(wins >= min(4, comparisons)),
        })
    return gates


def evaluate_all_scenarios(scenarios):
    all_rows = []
    artifacts_by_scenario = {}
    for scenario in scenarios:
        rows, artifacts = evaluate_scenario(scenario)
        all_rows.extend(rows)
        artifacts_by_scenario[scenario.scenario_name] = artifacts
    return {"rows": all_rows, "gates": _build_gate_results(all_rows), "artifacts": artifacts_by_scenario}
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: validation tests pass. Gate pass/fail values may be true or false; the test only verifies that gates are computed.

## Task 12: Add Reporting Artifacts

**Files:**
- Create: `simulation/phase1/reporting.py`
- Create: `simulation/phase1/run_validation.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add failing reporting smoke test**

Append to `tests/test_phase1_validation.py`:

```python
import tempfile
from pathlib import Path

from simulation.phase1.reporting import write_validation_report


class Phase1ReportingTest(unittest.TestCase):
    def test_write_validation_report_creates_csv_json_and_markdown(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)

            self.assertTrue(written["metrics_csv"].exists())
            self.assertTrue(written["gates_json"].exists())
            self.assertTrue(written["summary_md"].exists())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: fails because `reporting.py` does not exist.

- [ ] **Step 3: Implement CSV, JSON, and Markdown reporting**

Create `simulation/phase1/reporting.py`:

```python
import csv
import json
from pathlib import Path


def write_validation_report(summary, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics_csv = output / "metrics.csv"
    gates_json = output / "feasibility_gates.json"
    summary_md = output / "summary.md"

    rows = summary["rows"]
    fieldnames = ["scenario", "method", "rmse_mm", "mae_mm", "max_error_mm", "theta_rmse_rad", "unwrap_errors"]
    with metrics_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    with gates_json.open("w") as f:
        json.dump(summary["gates"], f, indent=2)

    with summary_md.open("w") as f:
        f.write("# Phase 1 Simulation Validation Summary\n\n")
        f.write("## Feasibility Gates\n\n")
        for gate in summary["gates"]:
            status = "PASS" if gate["passed"] else "FAIL"
            f.write(f"- {status}: {gate['name']} value={gate['value']} threshold={gate['threshold']}\n")
        f.write("\n## Metrics\n\n")
        f.write("| Scenario | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for row in rows:
            f.write(
                f"| {row['scenario']} | {row['method']} | "
                f"{row['rmse_mm']:.6f} | {row['mae_mm']:.6f} | "
                f"{row['max_error_mm']:.6f} | {row['unwrap_errors']} |\n"
            )

    return {"metrics_csv": metrics_csv, "gates_json": gates_json, "summary_md": summary_md}
```

- [ ] **Step 4: Implement CLI entry point**

Create `simulation/phase1/run_validation.py`:

```python
import argparse
from pathlib import Path

from .evaluate import evaluate_all_scenarios
from .reporting import write_validation_report
from .scenarios import build_phase1_scenarios


def main():
    parser = argparse.ArgumentParser(description="Run phase-1 algorithm validation.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("simulation/outputs/phase1_validation"),
        help="Directory for validation reports.",
    )
    args = parser.parse_args()

    summary = evaluate_all_scenarios(build_phase1_scenarios())
    written = write_validation_report(summary, args.output_dir)
    print(f"metrics: {written['metrics_csv']}")
    print(f"gates: {written['gates_json']}")
    print(f"summary: {written['summary_md']}")
    failed = [gate for gate in summary["gates"] if not gate["passed"]]
    print(f"feasibility gates passed: {len(summary['gates']) - len(failed)}/{len(summary['gates'])}")
    if failed:
        print("failed gates:")
        for gate in failed:
            print(f"- {gate['name']}: value={gate['value']} threshold={gate['threshold']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run reporting tests**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: reporting tests pass.

## Task 13: Add Minimal SVG Plots Without Matplotlib

**Files:**
- Modify: `simulation/phase1/reporting.py`
- Modify: `tests/test_phase1_validation.py`

- [ ] **Step 1: Add failing SVG test**

Append to `Phase1ReportingTest` in `tests/test_phase1_validation.py`:

```python
    def test_write_validation_report_creates_svg_directory(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)

            self.assertTrue(written["plots_dir"].exists())
            self.assertGreaterEqual(len(list(written["plots_dir"].glob("*.svg"))), 1)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: fails because no SVG plot is written.

- [ ] **Step 3: Add SVG helpers**

Append to `reporting.py`:

```python
def _scale(values, lo, hi, size):
    if hi == lo:
        return [size / 2.0 for _ in values]
    return [size * (float(v) - lo) / (hi - lo) for v in values]


def _polyline(points, color):
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="1.5" />'


def write_basic_svg(path, t, series, title):
    width = 900
    height = 360
    margin = 40
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    all_values = []
    for _, values, _ in series:
        all_values.extend([float(v) for v in values if v == v])
    y_lo = min(all_values) if all_values else -1.0
    y_hi = max(all_values) if all_values else 1.0
    x_scaled = _scale(t, float(t[0]), float(t[-1]), plot_w)
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<text x="{margin}" y="24" font-size="16">{title}</text>',
        f'<rect x="{margin}" y="{margin}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#888" />',
    ]
    for label, values, color in series:
        y_scaled = _scale(values, y_lo, y_hi, plot_h)
        points = [(margin + x, margin + plot_h - y) for x, y in zip(x_scaled, y_scaled)]
        body.append(_polyline(points, color))
    body.append("</svg>")
    path.write_text("\n".join(body))
```

- [ ] **Step 4: Call SVG writer from report**

Inside `write_validation_report`, after Markdown writing, add:

```python
    plots_dir = output / "plots"
    plots_dir.mkdir(exist_ok=True)
    artifacts = summary.get("artifacts", {})
    if artifacts:
        first_name = sorted(artifacts.keys())[0]
        first = artifacts[first_name]
        truth = first["truth"]
        results = first["results"]
        selected = [res for res in results if res.method_name in ("single_target_ma_style", "proposed")]
        series = [("truth", truth.q_m * 1e3, "#111111")]
        colors = {"single_target_ma_style": "#cc5500", "proposed": "#0066cc"}
        for res in selected:
            series.append((res.method_name, res.q_hat_m * 1e3, colors[res.method_name]))
        write_basic_svg(plots_dir / f"{first_name}_displacement.svg", truth.t, series, f"{first_name} displacement")
```

Update return value:

```python
    return {"metrics_csv": metrics_csv, "gates_json": gates_json, "summary_md": summary_md, "plots_dir": plots_dir}
```

- [ ] **Step 5: Run reporting tests**

Run:

```bash
python3 -m unittest tests/test_phase1_validation.py -v
```

Expected: SVG reporting tests pass.

## Task 14: Update README With Validation Meaning

**Files:**
- Modify: `simulation/phase1/README.md`

- [ ] **Step 1: Replace README content**

Rewrite `simulation/phase1/README.md` with:

```markdown
# Phase 1 Simulation Validation

This package implements the first-stage synthetic validation for the thesis method:

- Structural truth is a multi-frequency displacement signal with components near 20 Hz, 40 Hz, and 60 Hz.
- Radar observations are target-wise complex IQ signals whose phases are generated from `phi_i = kappa_i * Theta + b_i`.
- The algorithm receives only wrapped phase and measured acceleration.
- Validation compares baselines and the proposed multi-target structural-main-phase Kalman method.

## Current Method Under Test

The proposed method estimates structural main phase:

```text
x_k = [Theta_k, dotTheta_k]^T
Theta_k = 4*pi*q_k/lambda
```

Each target contributes:

```text
z_corr_i,k = psi_i,k + 2*pi*round((kappa_hat_i*Theta_pred + b_i - psi_i,k)/(2*pi))
```

The same corrected phase is used for Kalman update and online `kappa_i` bootstrap.

## Run Tests

```bash
python3 -m unittest discover tests -v
```

## Run Full Phase-1 Validation

```bash
python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
```

## Main Outputs

- `metrics.csv`: method-by-scenario RMSE/MAE/max error/phase RMSE/unwrap errors.
- `feasibility_gates.json`: pass/fail feasibility checks.
- `summary.md`: readable validation summary.
- `plots/*.svg`: basic displacement plots generated without matplotlib.

## Interpretation

Passing data-generation tests only means the synthetic observations are reproducible and physically shaped. Passing validation gates means the proposed method meets the current synthetic feasibility criteria. If any gate fails, report the failure and inspect the scenario instead of hiding it by tuning parameters.
```

- [ ] **Step 2: No command needed**

README is documentation. It will be verified by the full test and CLI run in Task 15.

## Task 15: Full Verification Run

**Files:**
- All phase-1 files

- [ ] **Step 1: Run all tests**

Run:

```bash
python3 -m unittest discover tests -v
```

Expected: all phase-1 tests pass. If unrelated tests exist and fail, identify whether they predate this work before changing anything.

- [ ] **Step 2: Run the full validation CLI**

Run:

```bash
python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
```

Expected: prints paths to `metrics.csv`, `feasibility_gates.json`, and `summary.md`.

- [ ] **Step 3: Inspect generated metrics**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
print(Path("simulation/outputs/phase1_validation/summary.md").read_text())
PY
```

Expected: summary includes feasibility gates and a metrics table for oracle, Itoh+LS, single-target Ma-style, fixed multi-target, and proposed methods.

- [ ] **Step 4: Inspect gate JSON**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
gates = json.loads(Path("simulation/outputs/phase1_validation/feasibility_gates.json").read_text())
print(json.dumps(gates, indent=2))
failed = [gate for gate in gates if not gate["passed"]]
print("FAILED", len(failed))
PY
```

Expected: output lists all gate results. If `FAILED` is greater than 0, keep the output and report which innovation or feasibility condition is not met.

- [ ] **Step 5: Verify generated plot exists**

Run:

```bash
find simulation/outputs/phase1_validation/plots -type f -name '*.svg' -maxdepth 1 | sort
```

Expected: at least one SVG file is listed.

## Task 16: Final Implementation Notes

**Files:**
- Modify: `simulation/phase1/README.md` only if the actual CLI output differs from documented command names.

- [ ] **Step 1: Record validation status**

In the final response, report:

```text
Tests run:
- python3 -m unittest discover tests -v
- python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation

Artifacts:
- simulation/outputs/phase1_validation/metrics.csv
- simulation/outputs/phase1_validation/feasibility_gates.json
- simulation/outputs/phase1_validation/summary.md
- simulation/outputs/phase1_validation/plots/*.svg

Gate result:
- X/Y feasibility gates passed.
- List failed gates if any.
```

- [ ] **Step 2: Explain what was validated**

State clearly:

```text
This validates the phase-1 synthetic innovation claims: structural-main-phase multi-target fusion, AoA cold start with kappa bootstrap, prediction-assisted wrapped phase correction, and target-wise adaptive R under degradation/dropout/mixed-scatterer scenarios.
```

- [ ] **Step 3: Explain what remains outside phase 1**

State clearly:

```text
This does not yet validate a full maglev track beam finite-element or moving-load structural model. Phase 1 validates the algorithm under multi-frequency structural response near 20/40/60 Hz. A later phase should replace or supplement the truth generator with a maglev track beam moving-load model.
```

## Self-Review Checklist

- This plan tells a no-memory agent which files to read first.
- This plan distinguishes data-generator sanity checks from algorithm validation.
- This plan includes tests before implementation for every new behavior.
- This plan validates each innovation with at least one scenario or gate.
- This plan avoids required dependencies beyond NumPy and Python standard library.
- This plan emits thesis-useful artifacts: CSV, JSON gates, Markdown summary, and SVG plots.
- This plan requires honest reporting of failed feasibility gates.
