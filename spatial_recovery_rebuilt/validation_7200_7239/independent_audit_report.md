# Independent audit of validation_7200_7239

This is a read-only audit of the completed rebuilt protocol. It did not rerun trials and makes no numerical-equivalence claim about the lost scratch workspace.

Topology: 200 rows, expected 5 strata × 40 seeds; seed/condition checks: PASS.

## Per-stratum audit

| Stratum | n | accepted | rejected | coverage | accepted-only RMSE mean (µm) | observed all-trial RMSE mean (µm) | all-trial success | rejected seeds |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| stationary | 40 | 38 | 2 | 0.950 | 1.129 | 1.129 | 0.950 | 7227,7238 |
| low_motion_0p005mm | 40 | 38 | 2 | 0.950 | 1.175 | 1.175 | 0.950 | 7227,7238 |
| low_motion_0p010mm | 40 | 38 | 2 | 0.950 | 1.284 | 1.284 | 0.950 | 7227,7238 |
| low_motion_0p020mm | 40 | 38 | 2 | 0.950 | 1.636 | 1.636 | 0.950 | 7227,7238 |
| low_motion_0p050mm | 40 | 39 | 1 | 0.975 | 3.121 | 3.121 | 0.975 | 7227 |

All-trial RMSE including abstentions is undefined because rejected trials have no estimate and the protocol declares no abstention penalty. The observed all-trial RMSE column therefore excludes only the rejected rows and is labeled accordingly. Accepted-only RMSE is conditional on guard-passing data and can be optimistic; the rejection pattern changes by stratum (seed 7238 passes the 0.050 mm stratum but fails several lower strata).

## Rejection and route findings

All 9 rejections are frozen-test ADXL acceleration guard failures; no package-contract or algorithm failures occurred.

The retained route is `range-angle front-end + fixed-beta structural Kalman` in frame mode: Range FFT, angle processing/target detection, local MUSIC/ML refinement, target selection, native-time ADXL preintegration, then fixed-geometry-beta Kalman. The output summaries contain no RO route or RA/RO comparison.

See `independent_audit.json` and `independent_audit_by_stratum.csv` for machine-readable details.
