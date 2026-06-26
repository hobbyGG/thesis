# Phase 1 Simulation Validation Summary

## Feasibility Gates

- PASS: nominal_proposed_rmse_le_0p03mm value=0.00736641142358081 threshold=0.03
- PASS: strong_wrapping_rmse_le_0p08mm value=0.039386084420432704 threshold=0.08
- PASS: strong_wrapping_unwrap_errors_le_10pct_itoh value=0 threshold=1
- PASS: target_snr_drop_proposed_beats_fixed_r value=0.008539005136169951 threshold=0.025974203467639033
- PASS: proposed_beats_single_target_in_at_least_4_scenarios value=8 threshold=4
- PASS: nominal_full_pipeline_rmse_le_0p05mm value=0.007264851927915894 threshold=0.05
- PASS: ma2023_balanced_good_targets_full_pipeline_beats_best_target value=0.0012047745422583604 threshold=0.0014603957897170962
- PASS: same_range_far_angles_full_pipeline_selects_two_same_range_targets value=1 threshold=1
- PASS: same_range_far_angles_full_pipeline_rmse_le_0p05mm value=0.025305856861013772 threshold=0.05
- PASS: same_range_far_angles_full_pipeline_beats_range_bin_only_mixed_phase value=0.025305856861013772 threshold=0.03285340574854646
- PASS: same_range_far_angles_range_bin_only_rmse_ge_1p25x_full_pipeline value=1.2982530458852177 threshold=1.25
- PASS: same_range_far_angles_full_pipeline_beats_ma_style_iterative_beta_range_bin value=0.025305856861013772 threshold=0.03379597782955503
- PASS: same_range_far_angles_full_pipeline_beats_ma2026_reproduction value=0.025305856861013772 threshold=0.12733827271309525
- PASS: vehicle_event_full_pipeline_selected_count_between_1_and_4 value=4 threshold=4
- PASS: vehicle_event_full_pipeline_excludes_target4 value=0 threshold=0
- PASS: vehicle_event_full_pipeline_unwrap_error_rate_eq_0 value=0.0 threshold=0.0
- PASS: vehicle_event_full_pipeline_rmse_le_0p03mm value=0.0044738717444606745 threshold=0.03
- PASS: target_snr_drop_full_pipeline_beats_selected_fixed_r value=0.009898995794590618 threshold=0.02831560571049853
- PASS: low_snr_full_pipeline_selects_at_least_2_targets value=4 threshold=2
- PASS: aoa_bootstrap_kappa_median_relative_error_le_0p05 value=0.022888443779122206 threshold=0.05

## Metrics

| Scenario | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors | Selected | Selected Indices | Corrected Obs | Unwrap Error Rate | Kappa Rel Err |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| nominal_multifrequency | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| nominal_multifrequency | itoh_ls | 0.013007 | 0.010436 | 0.056920 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| nominal_multifrequency | single_target_ma_style | 0.008483 | 0.005767 | 0.072524 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| nominal_multifrequency | range_bin_only_mixed_phase | 0.144713 | 0.137617 | 0.624253 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| nominal_multifrequency | ma_style_iterative_beta_range_bin | 0.128369 | 0.122109 | 0.533417 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| nominal_multifrequency | ma2026_reproduction | 0.053692 | 0.049763 | 0.129057 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| nominal_multifrequency | multitarget_true_kappa_fixed_r | 0.023770 | 0.019112 | 0.084206 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| nominal_multifrequency | multitarget_aoa_fixed_kappa | 0.023770 | 0.019112 | 0.084206 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| nominal_multifrequency | selected_aoa_fixed_kappa | 0.022540 | 0.018074 | 0.072170 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.011418 |
| nominal_multifrequency | proposed | 0.007366 | 0.005409 | 0.055688 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.016162 |
| nominal_multifrequency | proposed_full_pipeline | 0.007265 | 0.005540 | 0.048361 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.022888 |
| ma2023_balanced_good_targets | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| ma2023_balanced_good_targets | itoh_ls | 0.004053 | 0.003239 | 0.013828 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| ma2023_balanced_good_targets | single_target_ma_style | 0.001460 | 0.001160 | 0.004549 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| ma2023_balanced_good_targets | range_bin_only_mixed_phase | 0.001434 | 0.001141 | 0.012484 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| ma2023_balanced_good_targets | ma_style_iterative_beta_range_bin | 0.056705 | 0.044767 | 0.124079 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| ma2023_balanced_good_targets | ma2026_reproduction | 0.037064 | 0.029208 | 0.083293 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| ma2023_balanced_good_targets | multitarget_true_kappa_fixed_r | 0.019298 | 0.015325 | 0.043733 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| ma2023_balanced_good_targets | multitarget_aoa_fixed_kappa | 0.019298 | 0.015325 | 0.043733 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| ma2023_balanced_good_targets | selected_aoa_fixed_kappa | 0.016383 | 0.012803 | 0.036944 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.001510 |
| ma2023_balanced_good_targets | proposed | 0.001109 | 0.000846 | 0.004030 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.002000 |
| ma2023_balanced_good_targets | proposed_full_pipeline | 0.001205 | 0.000903 | 0.005356 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.004530 |
| strong_wrapping | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| strong_wrapping | itoh_ls | 0.007302 | 0.005820 | 0.027537 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| strong_wrapping | single_target_ma_style | 0.049198 | 0.030086 | 0.417257 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| strong_wrapping | range_bin_only_mixed_phase | 0.087519 | 0.065547 | 0.543257 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| strong_wrapping | ma_style_iterative_beta_range_bin | 0.087250 | 0.064932 | 0.544620 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| strong_wrapping | ma2026_reproduction | 0.220250 | 0.190397 | 0.697956 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| strong_wrapping | multitarget_true_kappa_fixed_r | 0.059513 | 0.038427 | 0.456027 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| strong_wrapping | multitarget_aoa_fixed_kappa | 0.059513 | 0.038427 | 0.456027 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| strong_wrapping | selected_aoa_fixed_kappa | 0.055089 | 0.036802 | 0.415117 | 0 | 4 | [1, 2, 0, 3] | 20000 | 0.000000 | 0.011418 |
| strong_wrapping | proposed | 0.039386 | 0.028929 | 0.278306 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.023696 |
| strong_wrapping | proposed_full_pipeline | 0.038741 | 0.028836 | 0.266961 | 0 | 4 | [1, 2, 0, 3] | 20000 | 0.000000 | 0.025496 |
| aoa_error_bootstrap | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| aoa_error_bootstrap | itoh_ls | 0.013007 | 0.010436 | 0.056920 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| aoa_error_bootstrap | single_target_ma_style | 0.008483 | 0.005767 | 0.072524 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| aoa_error_bootstrap | range_bin_only_mixed_phase | 0.144713 | 0.137617 | 0.624253 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| aoa_error_bootstrap | ma_style_iterative_beta_range_bin | 0.128369 | 0.122109 | 0.533417 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| aoa_error_bootstrap | ma2026_reproduction | 0.053692 | 0.049763 | 0.129057 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| aoa_error_bootstrap | multitarget_true_kappa_fixed_r | 0.023770 | 0.019112 | 0.084206 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| aoa_error_bootstrap | multitarget_aoa_fixed_kappa | 0.027245 | 0.021859 | 0.089649 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.160900 |
| aoa_error_bootstrap | selected_aoa_fixed_kappa | 0.022540 | 0.018074 | 0.072170 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.011418 |
| aoa_error_bootstrap | proposed | 0.008644 | 0.006482 | 0.054179 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.151039 |
| aoa_error_bootstrap | proposed_full_pipeline | 0.007267 | 0.005542 | 0.048361 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.022888 |
| target_snr_drop | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| target_snr_drop | itoh_ls | 9.148472 | 6.997330 | 14.406640 | 4524 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.904800 |  |
| target_snr_drop | single_target_ma_style | 0.018043 | 0.011493 | 0.103682 | 1 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000200 |  |
| target_snr_drop | range_bin_only_mixed_phase | 0.144713 | 0.137617 | 0.624253 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_snr_drop | ma_style_iterative_beta_range_bin | 0.128369 | 0.122109 | 0.533417 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_snr_drop | ma2026_reproduction | 0.299926 | 0.146040 | 1.310817 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_snr_drop | multitarget_true_kappa_fixed_r | 0.025974 | 0.021066 | 0.084206 | 11 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000440 | 0.000000 |
| target_snr_drop | multitarget_aoa_fixed_kappa | 0.025974 | 0.021066 | 0.084206 | 11 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000440 | 0.000000 |
| target_snr_drop | selected_aoa_fixed_kappa | 0.028316 | 0.022345 | 0.077932 | 22 | 4 | [0, 1, 2, 3] | 20000 | 0.001100 | 0.011418 |
| target_snr_drop | proposed | 0.008539 | 0.006367 | 0.055688 | 5 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000200 | 0.016162 |
| target_snr_drop | proposed_full_pipeline | 0.009899 | 0.007530 | 0.048373 | 17 | 4 | [0, 1, 2, 3] | 20000 | 0.000850 | 0.022888 |
| target_dropout | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| target_dropout | itoh_ls | 0.012921 | 0.010369 | 0.049646 | 0 | 5 | [0, 1, 2, 3, 4] | 3199 | 0.000000 |  |
| target_dropout | single_target_ma_style | 1.274598 | 0.925233 | 2.036505 | 1599 | 5 | [0, 1, 2, 3, 4] | 3199 | 0.499844 |  |
| target_dropout | range_bin_only_mixed_phase | 0.144713 | 0.137617 | 0.624253 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_dropout | ma_style_iterative_beta_range_bin | 0.128369 | 0.122109 | 0.533417 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_dropout | ma2026_reproduction | 0.053692 | 0.049763 | 0.129057 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| target_dropout | multitarget_true_kappa_fixed_r | 0.025789 | 0.020923 | 0.084206 | 0 | 5 | [0, 1, 2, 3, 4] | 23199 | 0.000000 | 0.000000 |
| target_dropout | multitarget_aoa_fixed_kappa | 0.025789 | 0.020923 | 0.084206 | 0 | 5 | [0, 1, 2, 3, 4] | 23199 | 0.000000 | 0.000000 |
| target_dropout | selected_aoa_fixed_kappa | 0.027775 | 0.022534 | 0.088323 | 0 | 3 | [1, 2, 3] | 15000 | 0.000000 | 0.015013 |
| target_dropout | proposed | 0.007503 | 0.005518 | 0.055688 | 0 | 5 | [0, 1, 2, 3, 4] | 23199 | 0.000000 | 0.016162 |
| target_dropout | proposed_full_pipeline | 0.008592 | 0.006440 | 0.051413 | 0 | 3 | [1, 2, 3] | 15000 | 0.000000 | 0.027537 |
| mixed_scatterer_rangebin | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| mixed_scatterer_rangebin | itoh_ls | 0.026781 | 0.021570 | 0.084257 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| mixed_scatterer_rangebin | single_target_ma_style | 0.016109 | 0.013615 | 0.075440 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| mixed_scatterer_rangebin | range_bin_only_mixed_phase | 0.011574 | 0.008830 | 0.076334 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| mixed_scatterer_rangebin | ma_style_iterative_beta_range_bin | 0.009920 | 0.006564 | 0.082439 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| mixed_scatterer_rangebin | ma2026_reproduction | 0.049107 | 0.046821 | 0.127520 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| mixed_scatterer_rangebin | multitarget_true_kappa_fixed_r | 0.023369 | 0.018925 | 0.085610 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| mixed_scatterer_rangebin | multitarget_aoa_fixed_kappa | 0.023369 | 0.018925 | 0.085610 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| mixed_scatterer_rangebin | selected_aoa_fixed_kappa | 0.023389 | 0.018791 | 0.072687 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.015688 |
| mixed_scatterer_rangebin | proposed | 0.009160 | 0.007204 | 0.057264 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.028600 |
| mixed_scatterer_rangebin | proposed_full_pipeline | 0.007109 | 0.005364 | 0.047654 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.010535 |
| same_range_far_angles | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.000000 |
| same_range_far_angles | itoh_ls | 0.005664 | 0.004521 | 0.020566 | 0 | 4 | [0, 1, 2, 3] | 5000 | 0.000000 |  |
| same_range_far_angles | single_target_ma_style | 0.031874 | 0.018797 | 0.291877 | 0 | 4 | [0, 1, 2, 3] | 5000 | 0.000000 |  |
| same_range_far_angles | range_bin_only_mixed_phase | 0.032853 | 0.020739 | 0.298449 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| same_range_far_angles | ma_style_iterative_beta_range_bin | 0.033796 | 0.019362 | 0.304586 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| same_range_far_angles | ma2026_reproduction | 0.127338 | 0.103441 | 0.490034 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| same_range_far_angles | multitarget_true_kappa_fixed_r | 0.044323 | 0.029233 | 0.328252 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.000000 |
| same_range_far_angles | multitarget_aoa_fixed_kappa | 0.044323 | 0.029233 | 0.328252 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.000000 |
| same_range_far_angles | selected_aoa_fixed_kappa | 0.036103 | 0.025129 | 0.260670 | 0 | 4 | [0, 2, 3, 1] | 20000 | 0.000000 | 0.008578 |
| same_range_far_angles | proposed | 0.026568 | 0.019149 | 0.196970 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.027754 |
| same_range_far_angles | proposed_full_pipeline | 0.025306 | 0.018961 | 0.185912 | 0 | 4 | [0, 2, 3, 1] | 20000 | 0.000000 | 0.029811 |
| low_snr_multitarget | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| low_snr_multitarget | itoh_ls | 0.059297 | 0.047257 | 0.249219 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| low_snr_multitarget | single_target_ma_style | 0.016939 | 0.013914 | 0.085995 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| low_snr_multitarget | range_bin_only_mixed_phase | 0.182136 | 0.175214 | 0.786480 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| low_snr_multitarget | ma_style_iterative_beta_range_bin | 0.156783 | 0.150731 | 0.652731 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| low_snr_multitarget | ma2026_reproduction | 0.047153 | 0.042717 | 0.143518 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| low_snr_multitarget | multitarget_true_kappa_fixed_r | 0.022874 | 0.018298 | 0.088581 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| low_snr_multitarget | multitarget_aoa_fixed_kappa | 0.022874 | 0.018298 | 0.088581 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| low_snr_multitarget | selected_aoa_fixed_kappa | 0.031592 | 0.025262 | 0.103588 | 1 | 4 | [0, 1, 2, 3] | 20000 | 0.000050 | 0.011418 |
| low_snr_multitarget | proposed | 0.011296 | 0.008817 | 0.062518 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.054509 |
| low_snr_multitarget | proposed_full_pipeline | 0.013590 | 0.010964 | 0.061152 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.061256 |
| vehicle_event_nonstationary | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| vehicle_event_nonstationary | itoh_ls | 0.012959 | 0.010407 | 0.055843 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| vehicle_event_nonstationary | single_target_ma_style | 0.004710 | 0.003630 | 0.022197 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 |  |
| vehicle_event_nonstationary | range_bin_only_mixed_phase | 0.140643 | 0.134388 | 0.619528 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| vehicle_event_nonstationary | ma_style_iterative_beta_range_bin | 0.106807 | 0.101483 | 0.468006 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| vehicle_event_nonstationary | ma2026_reproduction | 0.016125 | 0.011482 | 0.072599 | 0 | 1 | [-1] | 5000 | 0.000000 |  |
| vehicle_event_nonstationary | multitarget_true_kappa_fixed_r | 0.021629 | 0.017385 | 0.046454 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| vehicle_event_nonstationary | multitarget_aoa_fixed_kappa | 0.021629 | 0.017385 | 0.046454 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000000 |
| vehicle_event_nonstationary | selected_aoa_fixed_kappa | 0.019849 | 0.015503 | 0.044113 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.011418 |
| vehicle_event_nonstationary | proposed | 0.004721 | 0.003642 | 0.031520 | 0 | 5 | [0, 1, 2, 3, 4] | 25000 | 0.000000 | 0.000613 |
| vehicle_event_nonstationary | proposed_full_pipeline | 0.004474 | 0.003316 | 0.019178 | 0 | 4 | [0, 1, 2, 3] | 20000 | 0.000000 | 0.007238 |
| measured_bridge_point4_transverse | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 20000 | 0.000000 | 0.000000 |
| measured_bridge_point4_transverse | itoh_ls | 0.011141 | 0.008890 | 0.039845 | 0 | 5 | [0, 1, 2, 3, 4] | 4000 | 0.000000 |  |
| measured_bridge_point4_transverse | single_target_ma_style | 0.002967 | 0.002310 | 0.012652 | 0 | 5 | [0, 1, 2, 3, 4] | 4000 | 0.000000 |  |
| measured_bridge_point4_transverse | range_bin_only_mixed_phase | 0.057748 | 0.046627 | 0.111318 | 0 | 1 | [-1] | 4000 | 0.000000 |  |
| measured_bridge_point4_transverse | ma_style_iterative_beta_range_bin | 0.238905 | 0.152605 | 0.442497 | 0 | 1 | [-1] | 4000 | 0.000000 |  |
| measured_bridge_point4_transverse | ma2026_reproduction | 0.616525 | 0.413192 | 1.119246 | 0 | 1 | [-1] | 4000 | 0.000000 |  |
| measured_bridge_point4_transverse | multitarget_true_kappa_fixed_r | 0.017803 | 0.014608 | 0.039931 | 0 | 5 | [0, 1, 2, 3, 4] | 20000 | 0.000000 | 0.000000 |
| measured_bridge_point4_transverse | multitarget_aoa_fixed_kappa | 0.017803 | 0.014608 | 0.039931 | 0 | 5 | [0, 1, 2, 3, 4] | 20000 | 0.000000 | 0.000000 |
| measured_bridge_point4_transverse | selected_aoa_fixed_kappa | 0.013626 | 0.011332 | 0.035019 | 0 | 4 | [0, 1, 2, 3] | 16000 | 0.000000 | 0.005112 |
| measured_bridge_point4_transverse | proposed | 0.007445 | 0.005413 | 0.019350 | 0 | 5 | [0, 1, 2, 3, 4] | 20000 | 0.000000 | 0.005024 |
| measured_bridge_point4_transverse | proposed_full_pipeline | 0.003400 | 0.002729 | 0.011332 | 0 | 4 | [0, 1, 2, 3] | 16000 | 0.000000 | 0.002980 |
