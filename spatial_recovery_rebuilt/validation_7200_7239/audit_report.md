# Independent audit: rebuilt validation 7200–7239

This is a read-only audit of retained artifacts from `rebuilt_protocol`; it did not rerun capture or the algorithm and makes no parity claim with the lost scratch workspace.

Matrix integrity: 200/200 trial records present exactly once; effective seeds are 7200–7239 in every stratum. The run manifest documents that these effective seeds override the protocol's example seeds 20261001–20261040. All trials match 400 radar frames at 100 Hz, 200 calibration frames, and 200 frozen-test frames.

| Stratum | Accepted/40 | Coverage | Reject seeds | Accepted-only RMSE (µm, 21-frame corrected; mean / pooled) | All-trial success | q_true RMS (mm) | q_proxy RMS (mm) |
|---|---:|---:|---|---:|---:|---:|---:|
| stationary | 38/40 | 0.950 | 7227;7238 | 1.129042 / 1.131558 | 0.950 | 0–0 | 0–0 |
| low_motion_0p005mm | 38/40 | 0.950 | 7227;7238 | 1.175308 / 1.179045 | 0.950 | 0.005–0.005 | 0.00482962913–0.00482962913 |
| low_motion_0p010mm | 38/40 | 0.950 | 7227;7238 | 1.284171 / 1.289999 | 0.950 | 0.01–0.01 | 0.00965925826–0.00965925826 |
| low_motion_0p020mm | 38/40 | 0.950 | 7227;7238 | 1.636257 / 1.644793 | 0.950 | 0.02–0.02 | 0.0193185165–0.0193185165 |
| low_motion_0p050mm | 39/40 | 0.975 | 7227 | 3.121115 / 3.128379 | 0.975 | 0.05–0.05 | 0.0482962913–0.0482962913 |

All nine rejections have `package_contract=passed` and fail only `frozen_test_guard.acceleration_within_frozen_limit=false`: seed 7227 in all five strata and seed 7238 in stationary plus 0.005/0.010/0.020 mm. No algorithm output or `test_errors.npy` exists for rejected trials, so a valid all-trial RMSE is not estimable; success/coverage count rejected trials as failures. The retained `test_errors.npy` files use the old 20-frame reference, so pooled 21-frame RMSE here is independently recomputed as the equal-weight RMS of each accepted trial's corrected 21-frame RMSE from `trial_metrics_21frame.csv`. The accepted-only calculation can therefore be selection-biased if guard failure is related to unobserved estimator error. Within this retained matrix, q_true and q_proxy RMS are identical between accepted and rejected trials within each stratum, so no RMS-shift evidence of that bias was found.

Route audit: all 191 accepted outputs use `method=fixed_geometry_beta_structural_kalman` and `radar_mode=frame`, with one q_hat trajectory. This is one fixed-geometry beta structural Kalman reconstruction route; the artifacts do not support an RA/RO comparison.

See `audit_summary.json` for machine-readable details and `audit_stratum.csv`/`audit_trial.csv` for tabular records.
