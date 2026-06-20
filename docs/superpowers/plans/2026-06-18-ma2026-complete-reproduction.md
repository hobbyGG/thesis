# Ma 2026 Complete Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Ma-family baseline with a paper-faithful reproduction of Ma et al. 2026, using Ma 2026 as the canonical method definition and only using Ma 2023 where Ma 2026 explicitly cites or relies on prior acceleration-aided phase-correction details.

**Architecture:** The Ma 2026 package must separate paper method components from simulation adapters. The paper method should expose target-specific functions for LoS phase Kalman filtering, `Q` calibration, direction conversion factor `alpha` calibration, and convergence-time diagnostics. Any automatic range-bin/target selection used to run batch simulations must be labeled as an input adapter, not as part of the Ma 2026 method itself unless the 2026 paper explicitly defines it.

**Tech Stack:** Python 3, NumPy, `unittest`, existing `simulation.phase1` dataclasses and validation pipeline.

---

## Current Gap Summary

The current `simulation/phase1/ma2026/` implementation already includes the single-target LoS phase Kalman core, predictive phase correction, fixed `R=1`, discrete `R_d=R/T_a`, and `Q=10^j` energy selection. It is not yet a complete 2026 reproduction because:

- `alpha/beta` calibration is still implemented as a 2023-style grid search over `beta`, rather than Ma 2026 Eq. (18)-(19) linear fitting of band-pass-filtered acceleration-based phase and radar-derived corrected phase.
- Minimum convergence time from Ma 2026 Section 3.3 is not implemented as a diagnostic module.
- Automatic range-bin target selection is mixed into the method wrapper; Ma 2026 experiments validate selected Target 1 / Target 2 separately, so automatic target choice must be separated from the paper method.
- Documentation still uses some “Ma-family” wording where the intended baseline should be “Ma 2026 reproduction”.
- There is no machine-checkable compliance matrix tying each implemented step to Ma 2026 sections/equations.

## File Structure

- Create: `simulation/phase1/ma2026/spec.py`
  - Contains immutable references to Ma 2026 sections/equations and machine-readable compliance entries.
- Create: `simulation/phase1/ma2026/alpha.py`
  - Implements acceleration integration, phase conversion, band-pass filtering, and Eq. (19) slope-based `alpha` calibration.
- Create: `simulation/phase1/ma2026/convergence.py`
  - Implements Section 3.3 steady-state gain and convergence-time diagnostics.
- Modify: `simulation/phase1/ma2026/calibration.py`
  - Remove `beta_grid` as the canonical Ma 2026 alpha calibration path.
  - Keep any 2023 acceleration-aided branch-correction helper only as explicitly named support if needed.
- Modify: `simulation/phase1/ma2026/config.py`
  - Replace beta-grid defaults with Ma 2026 alpha/Q/convergence parameters.
- Modify: `simulation/phase1/ma2026/kalman.py`
  - Keep the Kalman equations strict to Ma 2026 and expose reusable functions for corrected phase energy.
- Modify: `simulation/phase1/ma2026/method.py`
  - Expose target-specific Ma 2026 method and a separate simulation adapter wrapper.
- Modify: `simulation/phase1/ma2026/__init__.py`
  - Export new Ma 2026-specific public API.
- Modify: `simulation/phase1/method_registry.py`
  - Ensure `ma2026_reproduction` calls the adapter, while diagnostics identify the target-specific paper method.
- Modify: `simulation/phase1/README.md`
  - Clarify Ma 2026 canonical reproduction and adapter boundary.
- Modify: `docs/algorithm_chain_review.md`
  - Update the method-code tracing table.
- Create/Modify: `tests/test_phase1_ma2026_reproduction.py`
  - Convert current tests to 2026 compliance tests.
- Create: `tests/test_phase1_ma2026_spec.py`
  - Tests the paper compliance matrix and bans undocumented enhancements from Ma 2026 core.

---

### Task 1: Add Ma 2026 Compliance Spec

**Files:**
- Create: `simulation/phase1/ma2026/spec.py`
- Create: `tests/test_phase1_ma2026_spec.py`

- [ ] **Step 1: Write the failing tests**

Add `tests/test_phase1_ma2026_spec.py`:

```python
import unittest

from simulation.phase1.ma2026.spec import MA2026_COMPLIANCE, compliance_by_id


class Ma2026SpecTest(unittest.TestCase):
    def test_compliance_matrix_covers_required_2026_modules(self):
        ids = {entry.id for entry in MA2026_COMPLIANCE}

        self.assertIn("ma2026_state_space_model", ids)
        self.assertIn("ma2026_predictive_phase_correction", ids)
        self.assertIn("ma2026_q_energy_selection", ids)
        self.assertIn("ma2026_alpha_linear_fit", ids)
        self.assertIn("ma2026_convergence_time", ids)
        self.assertIn("ma2026_target_input_boundary", ids)

    def test_each_compliance_entry_declares_paper_source_and_code_owner(self):
        for entry in MA2026_COMPLIANCE:
            self.assertTrue(entry.paper_source)
            self.assertTrue(entry.implementation_files)
            self.assertIn(entry.status, {"implemented", "planned", "adapter"})

    def test_alpha_calibration_is_marked_as_ma2026_not_ma2023_grid_search(self):
        entry = compliance_by_id("ma2026_alpha_linear_fit")

        self.assertIn("Section 3.2", entry.paper_source)
        self.assertIn("Eq. (18)", entry.paper_source)
        self.assertIn("Eq. (19)", entry.paper_source)
        self.assertNotIn("beta grid", entry.algorithm_invariant.lower())
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_spec -v
```

Expected: import failure because `simulation.phase1.ma2026.spec` does not exist.

- [ ] **Step 3: Implement the spec module**

Create `simulation/phase1/ma2026/spec.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Ma2026ComplianceEntry:
    id: str
    paper_source: str
    algorithm_invariant: str
    implementation_files: tuple[str, ...]
    status: str


MA2026_COMPLIANCE = (
    Ma2026ComplianceEntry(
        id="ma2026_state_space_model",
        paper_source="Ma et al. 2026 Section 3.1, Eqs. (6)-(15)",
        algorithm_invariant="State is single-target LoS phase and phase rate; acceleration is converted by 4*pi*a/(alpha*lambda).",
        implementation_files=("simulation/phase1/ma2026/kalman.py",),
        status="implemented",
    ),
    Ma2026ComplianceEntry(
        id="ma2026_predictive_phase_correction",
        paper_source="Ma et al. 2026 Section 3.1, phase correction before Kalman update",
        algorithm_invariant="The wrapped phase branch is selected using the predicted LoS phase before the measurement update.",
        implementation_files=("simulation/phase1/ma2026/kalman.py",),
        status="implemented",
    ),
    Ma2026ComplianceEntry(
        id="ma2026_q_energy_selection",
        paper_source="Ma et al. 2026 Section 3.2, Eqs. (16)-(17)",
        algorithm_invariant="R is fixed to 1, Q candidates are 10^j, and Qopt is argmin of corrected phase energy.",
        implementation_files=("simulation/phase1/ma2026/kalman.py", "simulation/phase1/ma2026/config.py"),
        status="implemented",
    ),
    Ma2026ComplianceEntry(
        id="ma2026_alpha_linear_fit",
        paper_source="Ma et al. 2026 Section 3.2, Eqs. (18)-(19), Fig. 12",
        algorithm_invariant="Alpha is obtained by linear fitting between band-pass-filtered acceleration-based phase and radar-derived corrected phase; this is not beta grid search.",
        implementation_files=("simulation/phase1/ma2026/alpha.py", "simulation/phase1/ma2026/calibration.py"),
        status="planned",
    ),
    Ma2026ComplianceEntry(
        id="ma2026_convergence_time",
        paper_source="Ma et al. 2026 Section 3.3, Fig. 13",
        algorithm_invariant="Minimum convergence time is computed from converged Kalman-gain convolution coefficients.",
        implementation_files=("simulation/phase1/ma2026/convergence.py",),
        status="planned",
    ),
    Ma2026ComplianceEntry(
        id="ma2026_target_input_boundary",
        paper_source="Ma et al. 2026 Sections 4.2.1 and 5.2.1",
        algorithm_invariant="The paper method is target-specific; automatic range-bin selection is a simulation adapter unless paper-defined target labels are supplied.",
        implementation_files=("simulation/phase1/ma2026/method.py", "simulation/phase1/ma2026/rangebin.py"),
        status="adapter",
    ),
)


def compliance_by_id(entry_id: str) -> Ma2026ComplianceEntry:
    for entry in MA2026_COMPLIANCE:
        if entry.id == entry_id:
            return entry
    raise KeyError(entry_id)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_spec -v
```

Expected: OK.

---

### Task 2: Implement Ma 2026 Alpha Calibration by Eq. (18)-(19)

**Files:**
- Create: `simulation/phase1/ma2026/alpha.py`
- Modify: `simulation/phase1/ma2026/config.py`
- Modify: `simulation/phase1/ma2026/calibration.py`
- Modify: `tests/test_phase1_ma2026_reproduction.py`

- [ ] **Step 1: Write failing tests for slope-based alpha**

Append to `tests/test_phase1_ma2026_reproduction.py`:

```python
from simulation.phase1.ma2026.alpha import (
    acceleration_to_phase,
    bandpass_rows,
    calibrate_alpha_linear_fit,
)


class Ma2026AlphaCalibrationTest(unittest.TestCase):
    def test_alpha_linear_fit_recovers_known_direction_factor(self):
        phase1 = Phase1Config(duration_s=4.0, sample_rate_hz=100.0, carrier_frequency_hz=77.0e9)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz)) / phase1.sample_rate_hz
        q_struct = 0.001 * np.sin(2.0 * np.pi * 2.0 * t)
        alpha_true = 1.2
        radar_phase = 4.0 * np.pi * q_struct / (alpha_true * phase1.wavelength_m())
        acceleration = -(2.0 * np.pi * 2.0) ** 2 * q_struct

        result = calibrate_alpha_linear_fit(
            corrected_phase_rad=radar_phase,
            acceleration_mps2=acceleration,
            sample_rate_hz=phase1.sample_rate_hz,
            wavelength_m=phase1.wavelength_m(),
            band_hz=(0.5, 3.0),
        )

        self.assertAlmostEqual(result.alpha, alpha_true, delta=0.01)
        self.assertGreater(result.r2, 0.99)

    def test_alpha_calibration_uses_bandpass_on_both_phase_series(self):
        phase1 = Phase1Config(duration_s=4.0, sample_rate_hz=100.0, carrier_frequency_hz=77.0e9)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz)) / phase1.sample_rate_hz
        low_q = 0.001 * np.sin(2.0 * np.pi * 2.0 * t)
        radar_only_high_q = 0.0002 * np.sin(2.0 * np.pi * 20.0 * t)
        alpha_true = 1.1
        radar_phase = 4.0 * np.pi * (low_q + radar_only_high_q) / (alpha_true * phase1.wavelength_m())
        acceleration = -(2.0 * np.pi * 2.0) ** 2 * low_q

        result = calibrate_alpha_linear_fit(
            corrected_phase_rad=radar_phase,
            acceleration_mps2=acceleration,
            sample_rate_hz=phase1.sample_rate_hz,
            wavelength_m=phase1.wavelength_m(),
            band_hz=(0.5, 3.0),
        )

        self.assertAlmostEqual(result.alpha, alpha_true, delta=0.02)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026AlphaCalibrationTest -v
```

Expected: import failure because `simulation.phase1.ma2026.alpha` does not exist.

- [ ] **Step 3: Implement alpha calibration**

Create `simulation/phase1/ma2026/alpha.py`:

```python
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026AlphaCalibrationResult:
    alpha: float
    slope: float
    intercept: float
    r2: float
    band_hz: tuple[float, float]
    acceleration_phase_rad: np.ndarray
    radar_phase_band_rad: np.ndarray


def bandpass_rows(values, sample_rate_hz, band_hz):
    arr = np.asarray(values, dtype=float)
    was_1d = arr.ndim == 1
    if was_1d:
        arr = arr[None, :]
    if arr.size == 0:
        return arr[0] if was_1d else arr.copy()
    low_hz, high_hz = (float(band_hz[0]), float(band_hz[1]))
    if low_hz < 0.0 or high_hz <= low_hz:
        raise ValueError("band_hz must be an increasing non-negative pair")
    centered = arr - np.nanmean(arr, axis=1, keepdims=True)
    freqs = np.fft.rfftfreq(arr.shape[1], d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0), axis=1)
    keep = (freqs >= low_hz) & (freqs <= high_hz)
    spectrum[:, ~keep] = 0.0
    filtered = np.fft.irfft(spectrum, n=arr.shape[1], axis=1)
    return filtered[0] if was_1d else filtered


def acceleration_to_displacement(acceleration_mps2, sample_rate_hz, low_cutoff_hz):
    accel = np.asarray(acceleration_mps2, dtype=float)
    if accel.size == 0:
        return accel.copy()
    centered = accel - float(np.nanmean(accel))
    freqs = np.fft.rfftfreq(accel.size, d=1.0 / float(sample_rate_hz))
    spectrum = np.fft.rfft(np.nan_to_num(centered, nan=0.0))
    displacement_spectrum = np.zeros_like(spectrum, dtype=complex)
    band = freqs >= float(low_cutoff_hz)
    omega = 2.0 * np.pi * freqs[band]
    displacement_spectrum[band] = -spectrum[band] / np.maximum(omega**2, 1e-18)
    return np.fft.irfft(displacement_spectrum, n=accel.size)


def acceleration_to_phase(acceleration_mps2, sample_rate_hz, wavelength_m, low_cutoff_hz):
    displacement = acceleration_to_displacement(acceleration_mps2, sample_rate_hz, low_cutoff_hz)
    return 4.0 * np.pi * displacement / float(wavelength_m)


def calibrate_alpha_linear_fit(corrected_phase_rad, acceleration_mps2, sample_rate_hz, wavelength_m, band_hz):
    radar_phase = np.asarray(corrected_phase_rad, dtype=float)
    accel_phase = acceleration_to_phase(acceleration_mps2, sample_rate_hz, wavelength_m, float(band_hz[0]))
    radar_band = bandpass_rows(radar_phase, sample_rate_hz, band_hz)
    accel_band = bandpass_rows(accel_phase, sample_rate_hz, band_hz)
    valid = np.isfinite(radar_band) & np.isfinite(accel_band)
    if np.count_nonzero(valid) < 3:
        return Ma2026AlphaCalibrationResult(
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            (float(band_hz[0]), float(band_hz[1])),
            accel_band,
            radar_band,
        )
    x = radar_band[valid]
    y = accel_band[valid]
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0
    return Ma2026AlphaCalibrationResult(
        alpha=float(slope),
        slope=float(slope),
        intercept=float(intercept),
        r2=float(r2),
        band_hz=(float(band_hz[0]), float(band_hz[1])),
        acceleration_phase_rad=accel_band,
        radar_phase_band_rad=radar_band,
    )
```

- [ ] **Step 4: Add config fields**

Modify `simulation/phase1/ma2026/config.py`:

```python
alpha_band_low_hz: float = 0.5
alpha_band_high_hz: float = 3.0
```

Keep `Q` fields:

```python
q_exponent_min: int = 0
q_exponent_max: int = 20
measurement_noise_r: float = 1.0
```

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026AlphaCalibrationTest -v
```

Expected: OK.

---

### Task 3: Replace Canonical Beta Grid Calibration With Ma 2026 Alpha Fitting

**Files:**
- Modify: `simulation/phase1/ma2026/calibration.py`
- Modify: `simulation/phase1/ma2026/method.py`
- Modify: `tests/test_phase1_ma2026_reproduction.py`

- [ ] **Step 1: Write failing test that canonical calibration does not expose beta grid as the method result**

Add to `tests/test_phase1_ma2026_reproduction.py`:

```python
class Ma2026CanonicalCalibrationTest(unittest.TestCase):
    def test_ma2026_reproduction_reports_alpha_not_beta_as_canonical_conversion_factor(self):
        phase1 = Phase1Config(
            duration_s=2.0,
            sample_rate_hz=100.0,
            carrier_frequency_hz=77.0e9,
            cold_start_duration_s=0.02,
            accel_noise_std_mps2=0.0,
        )
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz)) / phase1.sample_rate_hz
        q = 0.001 * np.sin(2.0 * np.pi * 2.0 * t)
        alpha_true = 1.15
        wrapped = np.angle(np.exp(1j * (4.0 * np.pi * q / (alpha_true * phase1.wavelength_m()))))
        acceleration = -(2.0 * np.pi * 2.0) ** 2 * q
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=wrapped[None, :],
            available_mask=np.ones((1, t.size), dtype=bool),
            range_bins=np.array([9], dtype=int),
        )
        accel = AccelerometerObservation(
            true_mps2=acceleration,
            measured_mps2=acceleration,
            bias_mps2=np.zeros_like(acceleration),
            noise_mps2=np.zeros_like(acceleration),
        )

        result = estimate_ma2026_reproduction(radar_input, accel, phase1, Ma2026Config())

        self.assertIn("selected_alpha", result.extra)
        self.assertAlmostEqual(result.extra["selected_alpha"], alpha_true, delta=0.03)
        self.assertNotIn("selected_beta", result.extra)
        self.assertNotIn("beta_grid", result.extra)
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026CanonicalCalibrationTest -v
```

Expected: FAIL because current result reports `selected_beta`.

- [ ] **Step 3: Implement two-pass Ma 2026 calibration**

Modify `simulation/phase1/ma2026/calibration.py` so the canonical path is:

1. Use an initial `alpha=1.0` or provided candidate target alpha to run Ma 2026 Kalman and obtain corrected radar phase.
2. Run `calibrate_alpha_linear_fit(...)` on the corrected radar phase and measured acceleration.
3. Re-run Ma 2026 `Q` selection and Kalman with the calibrated `alpha`.

Add dataclass:

```python
@dataclass(frozen=True)
class Ma2026TargetCalibrationResult:
    target_index: int
    range_bin: int
    alpha: float
    alpha_r2: float
    alpha_band_hz: tuple[float, float]
    selected_q: float
    q_candidates: np.ndarray
    q_energy: np.ndarray
```

Use `alpha` in the same place where current code uses `beta`; in Ma 2026 notation, displacement is:

```python
displacement = alpha * wavelength * phase_delta / (4.0 * np.pi)
phase_accel = 4.0 * np.pi * acceleration / (alpha * wavelength)
```

- [ ] **Step 4: Update method result keys**

Modify `simulation/phase1/ma2026/method.py` so `extra` contains:

```python
"selected_alpha": float(calibration.alpha)
"alpha_r2": float(calibration.alpha_r2)
"alpha_band_hz": tuple(calibration.alpha_band_hz)
"q_grid": calibration.q_candidates
"q_energy": calibration.q_energy
"selected_q": float(calibration.selected_q)
"source": "Ma 2026 acceleration-aided Kalman with Ma 2026 alpha/Q calibration"
```

Do not include `selected_beta` or `beta_grid` in `ma2026_reproduction`.

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction -v
```

Expected: update old beta-grid tests to either move to a legacy support class or remove them from canonical Ma 2026 reproduction tests.

---

### Task 4: Separate Paper Method From Simulation Target Adapter

**Files:**
- Modify: `simulation/phase1/ma2026/method.py`
- Modify: `simulation/phase1/method_registry.py`
- Modify: `tests/test_phase1_ma2026_reproduction.py`

- [ ] **Step 1: Write failing tests for target-specific API**

Add:

```python
class Ma2026TargetBoundaryTest(unittest.TestCase):
    def test_target_specific_api_runs_only_requested_target(self):
        phase1 = Phase1Config(duration_s=1.0, sample_rate_hz=100.0, carrier_frequency_hz=77.0e9)
        t = np.arange(int(phase1.duration_s * phase1.sample_rate_hz)) / phase1.sample_rate_hz
        q = 0.0005 * np.sin(2.0 * np.pi * 2.0 * t)
        acceleration = -(2.0 * np.pi * 2.0) ** 2 * q
        phase0 = 4.0 * np.pi * q / phase1.wavelength_m()
        phase1_target = 0.7 * phase0
        radar_input = Ma2026RangeBinInput(
            wrapped_phase_rad=np.vstack([np.angle(np.exp(1j * phase0)), np.angle(np.exp(1j * phase1_target))]),
            available_mask=np.ones((2, t.size), dtype=bool),
            range_bins=np.array([10, 20], dtype=int),
        )
        accel = AccelerometerObservation(acceleration, acceleration, np.zeros_like(acceleration), np.zeros_like(acceleration))

        from simulation.phase1.ma2026.method import estimate_ma2026_target

        result = estimate_ma2026_target(radar_input, accel, phase1, target_index=1, ma_config=Ma2026Config())

        self.assertEqual(result.extra["selected_target_index"], 1)
        self.assertEqual(result.extra["selected_range_bin"], 20)
        self.assertEqual(result.extra["selected_target_count"], 1)
```

- [ ] **Step 2: Run failing test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026TargetBoundaryTest -v
```

Expected: import failure because `estimate_ma2026_target` does not exist.

- [ ] **Step 3: Implement target-specific API**

Add to `simulation/phase1/ma2026/method.py`:

```python
def estimate_ma2026_target(rangebin_input, accel, phase1_config, target_index, ma_config: Ma2026Config = Ma2026Config()):
    # Validate target_index.
    # Run Ma 2026 alpha calibration and Q selection for exactly this target.
    # Return MethodResult with only target_index filled in corrected_phase_rad; all other targets remain NaN.
```

The existing `estimate_ma2026_reproduction(...)` may remain as a simulation adapter:

```python
def estimate_ma2026_reproduction(...):
    target_index = choose_adapter_target(...)
    return estimate_ma2026_target(..., target_index=target_index, ...)
```

Document in `extra`:

```python
"adapter_target_policy": "range-bin candidate selected by calibration energy for batch simulation; not a Ma 2026 paper contribution"
```

- [ ] **Step 4: Run target boundary test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026TargetBoundaryTest -v
```

Expected: OK.

---

### Task 5: Implement Ma 2026 Minimum Convergence Time Diagnostic

**Files:**
- Create: `simulation/phase1/ma2026/convergence.py`
- Modify: `simulation/phase1/ma2026/method.py`
- Modify: `tests/test_phase1_ma2026_reproduction.py`

- [ ] **Step 1: Write failing tests**

Add:

```python
class Ma2026ConvergenceTimeTest(unittest.TestCase):
    def test_convergence_time_is_positive_and_decreases_with_larger_q_in_stable_range(self):
        from simulation.phase1.ma2026.convergence import ma2026_convergence_time

        dt = 0.01
        low_q = ma2026_convergence_time(dt=dt, q_value=1.0e4, measurement_r_discrete=100.0)
        high_q = ma2026_convergence_time(dt=dt, q_value=1.0e7, measurement_r_discrete=100.0)

        self.assertGreater(low_q.steps, 0)
        self.assertGreater(low_q.seconds, 0.0)
        self.assertLessEqual(high_q.steps, low_q.steps)
        self.assertEqual(high_q.seconds, high_q.steps * dt)
```

- [ ] **Step 2: Run failing test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026ConvergenceTimeTest -v
```

Expected: import failure because `convergence.py` does not exist.

- [ ] **Step 3: Implement convergence diagnostic**

Create `simulation/phase1/ma2026/convergence.py`:

```python
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ma2026ConvergenceResult:
    steps: int
    seconds: float
    measurement_coefficients: np.ndarray
    acceleration_coefficients: np.ndarray


def steady_state_gain(dt, q_value, measurement_r_discrete, iterations=10000, tolerance=1e-12):
    a_mat = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    h = np.array([[1.0, 0.0]], dtype=float)
    q_base = np.array([[dt**3 / 3.0, dt**2 / 2.0], [dt**2 / 2.0, dt]], dtype=float)
    q_mat = float(q_value) * q_base
    p = np.zeros((2, 2), dtype=float)
    previous_k = np.zeros((2, 1), dtype=float)
    for _ in range(int(iterations)):
        p_pred = a_mat @ p @ a_mat.T + q_mat
        s_value = float((h @ p_pred @ h.T)[0, 0] + float(measurement_r_discrete))
        k_gain = p_pred @ h.T / s_value
        p = (np.eye(2) - k_gain @ h) @ p_pred
        if np.max(np.abs(k_gain - previous_k)) < float(tolerance):
            return k_gain.reshape(2)
        previous_k = k_gain
    return previous_k.reshape(2)


def ma2026_convergence_time(dt, q_value, measurement_r_discrete, coefficient_threshold=1e-3, max_steps=10000):
    dt = float(dt)
    a_mat = np.array([[1.0, dt], [0.0, 1.0]], dtype=float)
    b_vec = np.array([0.5 * dt * dt, dt], dtype=float)
    k_gain = steady_state_gain(dt, q_value, measurement_r_discrete)
    c_mat = np.eye(2) - k_gain[:, None] @ np.array([[1.0, 0.0]], dtype=float)
    transition = c_mat @ a_mat
    measurement_coefficients = []
    acceleration_coefficients = []
    power = np.eye(2)
    for _ in range(int(max_steps)):
        measurement_coefficients.append(float((power @ k_gain)[0]))
        acceleration_coefficients.append(float((power @ c_mat @ b_vec)[0]))
        power = power @ transition
    measurement = np.asarray(measurement_coefficients, dtype=float)
    acceleration = np.asarray(acceleration_coefficients, dtype=float)
    combined = np.maximum(np.abs(measurement), np.abs(acceleration))
    above = np.flatnonzero(combined > float(coefficient_threshold))
    steps = int(above[-1] + 1) if above.size else 0
    return Ma2026ConvergenceResult(
        steps=steps,
        seconds=steps * dt,
        measurement_coefficients=measurement,
        acceleration_coefficients=acceleration,
    )
```

- [ ] **Step 4: Add method diagnostics**

Add to `MethodResult.extra` in `simulation/phase1/ma2026/method.py`:

```python
"minimum_convergence_steps": int(convergence.steps)
"minimum_convergence_time_s": float(convergence.seconds)
```

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction.Ma2026ConvergenceTimeTest -v
```

Expected: OK.

---

### Task 6: Update Validation, Reporting, and Docs for Canonical Ma 2026

**Files:**
- Modify: `simulation/phase1/README.md`
- Modify: `docs/algorithm_chain_review.md`
- Modify: `reports/phase1_method_and_simulation_report.md` if it is still used for reporting
- Modify: `tests/test_phase1_validation.py`
- Modify: `tests/test_phase1_ma2026_spec.py`

- [ ] **Step 1: Write failing documentation tests**

Add to `tests/test_phase1_ma2026_spec.py`:

```python
from pathlib import Path


class Ma2026DocumentationTest(unittest.TestCase):
    def test_docs_describe_ma2026_as_canonical_method_not_2023_2026_splice(self):
        readme = Path("simulation/phase1/README.md").read_text()
        review = Path("docs/algorithm_chain_review.md").read_text()

        combined = readme + "\n" + review
        self.assertIn("Ma 2026 reproduction", combined)
        self.assertIn("alpha", combined)
        self.assertIn("Qopt=argmin E(Q)", combined)
        self.assertNotIn("Ma2023 calibration + Ma2026", combined)
        self.assertNotIn("selected_beta", combined)
```

- [ ] **Step 2: Run failing test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_spec.Ma2026DocumentationTest -v
```

Expected: FAIL until docs are updated.

- [ ] **Step 3: Update docs**

Update `simulation/phase1/README.md` wording:

```text
ma2026_reproduction: Ma 2026 canonical reproduction. The method uses a target-specific LoS phase Kalman state, fixed R=1, Q=10^j energy selection, Ma 2026 alpha calibration by band-pass-filtered phase linear fitting, and Section 3.3 convergence-time diagnostics. Any automatic target choice in batch validation is a simulation adapter and is not claimed as a Ma 2026 contribution.
```

Update `docs/algorithm_chain_review.md` M3e row to include:

```text
alpha calibration: Section 3.2, Eqs. (18)-(19)
Q calibration: Section 3.2, Eqs. (16)-(17)
convergence time: Section 3.3
target boundary: Target-specific method; automatic selection is an adapter
```

- [ ] **Step 4: Run documentation tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_spec -v
```

Expected: OK.

---

### Task 7: Full Verification and Output Refresh

**Files:**
- Generated outputs under `simulation/outputs/phase1_validation/`
- Generated outputs under `simulation/outputs/phase1_extended_validation/`

- [ ] **Step 1: Run Ma 2026 targeted tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_phase1_ma2026_reproduction tests.test_phase1_ma2026_spec -v
```

Expected: all tests pass.

- [ ] **Step 2: Run full unit tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover tests -v
```

Expected: all tests pass; TDMS-backed local tests may skip unless `PHASE1_RUN_MEASURED_BRIDGE_TESTS=1` is set.

- [ ] **Step 3: Regenerate validation outputs**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
```

Expected:

```text
metrics: simulation/outputs/phase1_validation/metrics.csv
gates: simulation/outputs/phase1_validation/feasibility_gates.json
summary: simulation/outputs/phase1_validation/summary.md
feasibility gates passed: 23/23
```

If gates change because Ma 2026 becomes stricter, inspect only gates that compare against `ma2026_reproduction`; do not weaken main-method gates without documenting why.

- [ ] **Step 4: Regenerate extended validation**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m simulation.phase1.run_extended_validation --output-dir simulation/outputs/phase1_extended_validation
```

Expected: CSV files and `extended_summary.md` are written.

- [ ] **Step 5: Inspect Ma 2026 metrics and diagnostics**

Run:

```bash
python3 - <<'PY'
import csv
from pathlib import Path

rows = list(csv.DictReader(Path("simulation/outputs/phase1_validation/metrics.csv").open()))
for row in rows:
    if row["method"] == "ma2026_reproduction":
        print(row["scenario"], row["rmse_mm"], row["unwrap_error_rate"])
PY
```

Expected: output includes all scenarios with `ma2026_reproduction`; values may differ from previous runs because the baseline is now stricter.

---

## Subagent Strategy

This plan is suitable for subagent-driven development after the compliance spec is written. The work has more than two independent write scopes:

- Worker A: `spec.py`, documentation compliance tests, README/review wording.
- Worker B: `alpha.py` and alpha calibration tests.
- Worker C: `kalman.py`, `calibration.py`, `method.py` canonical Ma 2026 method changes.
- Worker D: `convergence.py` and convergence diagnostics tests.
- Worker E: final validation, metrics refresh, and review of output interpretation.

Tasks that should not run in parallel:

- Worker C should not start rewriting `method.py` until Worker B defines the alpha calibration API.
- Documentation final wording should wait until Worker C and D settle public keys like `selected_alpha` and `minimum_convergence_time_s`.
- Final validation must run after all code changes are complete.

Because this plan has more than two independent tasks with mostly non-overlapping files, it is a good candidate for subagents. Ask the user before spawning them.

---

## Self-Review

Spec coverage:

- Ma 2026 Section 3.1 state-space Kalman: covered by Task 3 and existing `kalman.py` tests.
- Ma 2026 predictive phase correction: covered by existing `run_ma2026_los_kalman` and compliance spec.
- Ma 2026 Section 3.2 Q selection: covered by Task 1 and current `q_grid` / `argmin E(Q)` tests.
- Ma 2026 Section 3.2 alpha calibration: covered by Task 2 and Task 3.
- Ma 2026 Section 3.3 convergence time: covered by Task 5.
- Target boundary / automatic adapter distinction: covered by Task 4 and docs in Task 6.

Placeholder scan:

- No “TBD” or “implement later” placeholders are intentionally left.
- Where implementation bodies are summarized, the task includes concrete required keys, test assertions, and equations.

Type consistency:

- Public names introduced in tests are `calibrate_alpha_linear_fit`, `bandpass_rows`, `acceleration_to_phase`, `estimate_ma2026_target`, and `ma2026_convergence_time`.
- Result keys are consistently `selected_alpha`, `alpha_r2`, `alpha_band_hz`, `selected_q`, `q_grid`, `q_energy`, `minimum_convergence_steps`, and `minimum_convergence_time_s`.
