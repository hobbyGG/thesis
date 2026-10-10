# Matched factorial diagnostic report: profile-LS vs Bartlett

Status: `NEW_SYNTHETIC_MATCHED_FACTORIAL`. This is a bounded synthetic diagnostic built on the independent 2026-10-06 profile-LS implementation. It does not recover historical 400–402 artifacts and does not modify the retained algorithm.

## Execution and guard

- 3 matched blocks (`4201, 4202, 4203`), 3 factors, 2 estimators, 2 initialization routes = **36 rows**.
- All **36/36** rows passed finite/amplitude guard; every row scores frames **148–255** (108 samples).
- Cold routes reference frame 128 during estimation and are rebased at frame 148 for paired scoring; warm routes consume the legal prefix 128–147 and reference frame 148. Their paired post-rebase metrics are identical in this deterministic setup.
- Geometry/angle estimation receives calibration IQ only. Truth enters only in the post-run score fields.

## Factor-level paired differences

Values are medians across the three matched seeds. `profile − Bartlett`; a positive RMSE difference means profile-LS is worse.

| factor | RMSE Bartlett (mm) | RMSE profile (mm) | Δ RMSE (mm) | dynamic Δ RMSE (mm) | angle abs error Bartlett/profile (°) | conversion error Bartlett/profile |
|---|---:|---:|---:|---:|---:|---:|
| `offgrid_only` | 0.002335557 | 0.002619620 | 0.000284063 | -0.000001047 | 0.120000 / 0.000000 | -0.000653 / -0.000000 |
| `offgrid_beta` | 0.014185214 | 0.014746788 | 0.000561574 | 0.000047803 | 0.120000 / 0.000000 | +0.014338 / +0.015000 |
| `offgrid_array` | 0.002334989 | 0.002565251 | 0.000230262 | -0.000001021 | 0.120000 / 0.020000 | -0.000653 / -0.000109 |

## Per-seed RMSE deltas

`profile − Bartlett`, in seed order 4201 / 4202 / 4203:

- `offgrid_only`: -0.000047188, +0.000284063, +0.000424824 mm; profile-LS improves **1/3** seeds.
- `offgrid_beta`: +0.000370696, +0.000561574, +0.000630704 mm; profile-LS improves **0/3** seeds.
- `offgrid_array`: -0.000045418, +0.000230262, +0.000349749 mm; profile-LS improves **1/3** seeds.

## Interaction readout

The interaction is computed descriptively as the factor median ΔRMSE minus the `offgrid_only` median ΔRMSE:

- beta mismatch: +0.000277511 mm.
- array-position mismatch: -0.000053801 mm.

## Phase/reference diagnostics

Phase-residual values below are medians across seeds after the common frame-148 rebase:

| factor | phase bias Bartlett/profile (rad) | phase RMSE Bartlett/profile (rad) |
|---|---:|---:|
| `offgrid_only` | -0.000927233 / -0.000877951 | 0.007886807 / 0.007854475 |
| `offgrid_beta` | -0.000928956 / -0.000879711 | 0.007931096 / 0.007900623 |
| `offgrid_array` | -0.000932024 / -0.000890946 | 0.007884893 / 0.007858148 |

## Interpretation and stopping boundary

- Profile-LS removes the 0.12° Bartlett grid error in all three factors (profile angle error is 0° in the no-array-mismatch and beta cases, and −0.02° with the fixed position mismatch).
- That angle improvement does not translate into a uniform displacement improvement: the RMSE median is positive for all three factors. It helps one of three matched seeds in `offgrid_only`, none in `offgrid_beta`, and one in `offgrid_array`.
- The beta factor leaves a roughly +1.5% conversion-scale residual after angle refinement (`conversion error ≈ +0.015` for profile-LS); this isolates beta sensitivity rather than proving a beta correction.
- The array-position factor is mixed and remains a bounded synthetic mechanism check. No universal off-grid claim, field/LVDT equivalence, absolute 0.01 mm claim, full covariance/GLS claim, or historical artifact recovery is supported.
- This diagnostic is stopped at the registered 3-seed block. Any larger sweep requires a new protocol and is not implied by these rows.

## Reproduction

```bash
capture_program/.venv/bin/python -m py_compile experiments/profile_ls_factorial_diagnostic_2026-10-06/run_factorial.py
capture_program/.venv/bin/python experiments/profile_ls_factorial_diagnostic_2026-10-06/run_factorial.py
```
