# Phase 1 Simulation Validation Summary

## Feasibility Gates

- PASS: nominal_proposed_rmse_le_0p03mm value=0.006741100335908755 threshold=0.03
- PASS: strong_wrapping_rmse_le_0p08mm value=0.035220282472705464 threshold=0.08
- PASS: strong_wrapping_unwrap_errors_le_10pct_itoh value=0 threshold=1
- PASS: target_snr_drop_proposed_beats_fixed_r value=0.00784944344030745 threshold=0.012713339447949194
- PASS: proposed_beats_single_target_in_at_least_4_scenarios value=5 threshold=4

## Metrics

| Scenario | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors |
|---|---:|---:|---:|---:|---:|
| nominal_multifrequency | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| nominal_multifrequency | itoh_ls | 0.014137 | 0.011356 | 0.060269 | 0 |
| nominal_multifrequency | single_target_ma_style | 0.006348 | 0.004906 | 0.033426 | 0 |
| nominal_multifrequency | multitarget_fixed | 0.009401 | 0.006023 | 0.058621 | 0 |
| nominal_multifrequency | proposed | 0.006741 | 0.005361 | 0.031290 | 1 |
| strong_wrapping | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| strong_wrapping | itoh_ls | 0.007697 | 0.006137 | 0.028900 | 0 |
| strong_wrapping | single_target_ma_style | 0.036636 | 0.027772 | 0.209465 | 0 |
| strong_wrapping | multitarget_fixed | 0.057695 | 0.035621 | 0.359719 | 0 |
| strong_wrapping | proposed | 0.035220 | 0.028045 | 0.152851 | 0 |
| aoa_error_bootstrap | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| aoa_error_bootstrap | itoh_ls | 0.014137 | 0.011356 | 0.060269 | 0 |
| aoa_error_bootstrap | single_target_ma_style | 0.006348 | 0.004906 | 0.033426 | 0 |
| aoa_error_bootstrap | multitarget_fixed | 0.009401 | 0.006023 | 0.058621 | 0 |
| aoa_error_bootstrap | proposed | 0.006883 | 0.005447 | 0.037359 | 1 |
| target_snr_drop | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| target_snr_drop | itoh_ls | 9.146085 | 6.995922 | 14.403290 | 3361 |
| target_snr_drop | single_target_ma_style | 0.015102 | 0.009972 | 0.078848 | 2 |
| target_snr_drop | multitarget_fixed | 0.012713 | 0.008932 | 0.058621 | 9 |
| target_snr_drop | proposed | 0.007849 | 0.006223 | 0.031290 | 13 |
| target_dropout | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| target_dropout | itoh_ls | 0.014028 | 0.011281 | 0.052995 | 0 |
| target_dropout | single_target_ma_style | 0.060025 | 0.034570 | 0.178763 | 0 |
| target_dropout | multitarget_fixed | 0.009448 | 0.006086 | 0.058621 | 0 |
| target_dropout | proposed | 0.006941 | 0.005474 | 0.031290 | 1 |
| mixed_scatterer_rangebin | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| mixed_scatterer_rangebin | itoh_ls | 0.027430 | 0.022092 | 0.085498 | 0 |
| mixed_scatterer_rangebin | single_target_ma_style | 0.395505 | 0.395412 | 0.417510 | 0 |
| mixed_scatterer_rangebin | multitarget_fixed | 0.133960 | 0.133656 | 0.150146 | 1 |
| mixed_scatterer_rangebin | proposed | 0.013161 | 0.006908 | 0.120415 | 1 |
| low_snr_multitarget | oracle | 0.000000 | 0.000000 | 0.000000 | 0 |
| low_snr_multitarget | itoh_ls | 0.064146 | 0.051265 | 0.263934 | 0 |
| low_snr_multitarget | single_target_ma_style | 0.010508 | 0.008187 | 0.049919 | 0 |
| low_snr_multitarget | multitarget_fixed | 0.009900 | 0.006513 | 0.066043 | 0 |
| low_snr_multitarget | proposed | 0.009264 | 0.007214 | 0.066043 | 1 |
