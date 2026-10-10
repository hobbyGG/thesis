# Local 0.05 mm RMS angle pilot

Exactly three estimator routes, seed 20261001; no cloud 400–402 reproduction. Input is the local synthetic 1 Hz sine and package-builder export, not the A20 physical response. Protocol and source hashes were saved before execution. Raw arrays were temporary only.

## What the old script actually perturbs

The saved 0.005 mm script changes BOTH angle-derived beta and the pseudoinverse steering matrix used to extract test IQ. Thus the measurement phase/amplitude and scale can both change. Pure beta-only sensitivity would hold the complex observations fixed and change beta alone; that route was not executed here. Range bins, target identities, configuration, acceleration and input samples are shared between the three new routes. Geometry is fit once from frames 0–199 and frozen; a test-only ADC perturbation reproduced identical geometry.

## Reference correction and remaining limitation

The old score used the full-record first 21 frames (elapsed <= 0.20s). The retained filter instead estimates phase bias and initial residual R from the first 20 TEST frames. Those references differ. Primary scores below use truth centered on precisely the same 20 test indices, only after all three estimator outputs exist; no output alignment, parameter fitting or truth-driven weighting is performed. Legacy-reference scores are also retained to make the change explicit. The reference difference is 0.001411045 mm. This is geometry-frozen but still exploratory test-prefix cold start, not strict calibration-only phase-reference/R initialization or fully causal output during those first 20 frames.

Physical test truth RMS is 0.0499999814 mm; matched-reference truth RMS is 0.0627387850 mm (RMS includes the reference offset).

| Delta deg | q estimate RMS mm | Matched RMSE mm | Legacy RMSE mm | Bias mm | Finite coverage |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.064525074 | 0.002084585 | 0.001924382 | -0.000933102 | 1.000 |
| -1 | 0.064275840 | 0.001871346 | 0.001790906 | -0.000809910 | 1.000 |
| 1 | 0.064794961 | 0.002326791 | 0.002096853 | -0.001065952 | 1.000 |

| Target | Range bin | Angle deg | Base beta | Beta -1 deg | Beta +1 deg | Theory -1 deg % | Theory +1 deg % |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 230 | 2.615028 | 1.001042448 | 1.000397401 | 1.001993742 | -0.064438 | 0.095030 |
| 1 | 246 | 20.870073 | 1.070216157 | 1.063302904 | 1.077550275 | -0.645968 | 0.685293 |
| 2 | 253 | 25.111109 | 1.104378657 | 1.095584263 | 1.113657356 | -0.796320 | 0.840174 |
| 3 | 238 | 15.441241 | 1.037447704 | 1.032626981 | 1.042632733 | -0.464671 | 0.499787 |
| 4 | 232 | 9.424627 | 1.013682824 | 1.010908255 | 1.016783239 | -0.273712 | 0.305857 |

The theoretical relative error is sec(theta+delta)/sec(theta)-1, valid for the reported angles where cosine is positive. It describes pure projection-scale change with fixed LOS observations, not the combined steering/beta/Kalman error. It is explanatory only and never used to choose weights or offsets.

Matched RMSE changes by -0.000213239 mm (-10.23%) at -1 degree and +0.000242206 mm (+11.62%) at +1 degree. The smaller error at -1 degree is not permission to tune geometry to truth. This pilot does not establish multi-target superiority over a single target, robustness at other LOS angles, or elimination of all calibration.

Package contract and frozen guards passed; estimator copy contains no truth or q_proxy, and scoring begins after all three routes. Coverage is finite-sample availability, not calibrated uncertainty coverage. No matrices were expanded and no Git write was attempted.

Next substantive work should test removal of independent excitation-based DCF fitting and a fair multi-target versus strongest-single comparison, after defining shared initialization/reference. The missing strict calibration-only phase-bias/initial-R interface remains the precise initialization gap.

Command (repository root):

```sh
python3 experiments/cross_review_profile_ls_covariance_2026-10-03/pilot_angle_0p050mm_seed20261001/run_pilot.py
```

The script refuses existing output files; preserve these artifacts when reproducing into a new directory.
