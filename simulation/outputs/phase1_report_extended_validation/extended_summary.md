# Phase 1 Extended Experiment Summary

## Metadata

- Seeds: [2026, 2027, 2028, 2029, 2030]
- Monte Carlo scenarios: ['nominal_multifrequency', 'ma2023_balanced_good_targets', 'same_range_far_angles', 'target_snr_drop', 'low_snr_multitarget', 'vehicle_event_nonstationary']
- AoA sensitivity levels: [0.0, 3.0, 6.0, 10.0, 15.0]
- SNR floor levels: [4.0, 6.0, 8.0, 10.0, 12.0]

## Monte Carlo Summary

| scenario | method | n | rmse_mean_mm | rmse_std_mm |
|---|---|---|---|---|
| low_snr_multitarget | ma2026_reproduction | 5 | 0.041154 | 0.006233 |
| low_snr_multitarget | proposed | 5 | 0.011865 | 0.000653 |
| low_snr_multitarget | proposed_full_pipeline | 5 | 0.012723 | 0.001281 |
| low_snr_multitarget | selected_aoa_fixed_kappa | 5 | 0.030655 | 0.006165 |
| low_snr_multitarget | single_target_ma_style | 5 | 0.014799 | 0.002633 |
| ma2023_balanced_good_targets | ma2026_reproduction | 5 | 0.098337 | 0.092664 |
| ma2023_balanced_good_targets | proposed | 5 | 0.001005 | 0.000116 |
| ma2023_balanced_good_targets | proposed_full_pipeline | 5 | 0.001090 | 0.000253 |
| ma2023_balanced_good_targets | selected_aoa_fixed_kappa | 5 | 0.015537 | 0.003191 |
| ma2023_balanced_good_targets | single_target_ma_style | 5 | 0.001314 | 0.000118 |
| nominal_multifrequency | ma2026_reproduction | 5 | 0.049598 | 0.019556 |
| nominal_multifrequency | proposed | 5 | 0.008062 | 0.001098 |
| nominal_multifrequency | proposed_full_pipeline | 5 | 0.007863 | 0.000989 |
| nominal_multifrequency | selected_aoa_fixed_kappa | 5 | 0.022438 | 0.005360 |
| nominal_multifrequency | single_target_ma_style | 5 | 0.009746 | 0.002271 |
| same_range_far_angles | ma2026_reproduction | 5 | 0.198431 | 0.116342 |
| same_range_far_angles | proposed | 5 | 0.030990 | 0.005872 |
| same_range_far_angles | proposed_full_pipeline | 5 | 0.029297 | 0.005070 |
| same_range_far_angles | range_bin_only_mixed_phase | 5 | 0.044406 | 0.021001 |
| same_range_far_angles | selected_aoa_fixed_kappa | 5 | 0.042758 | 0.012044 |
| same_range_far_angles | single_target_ma_style | 5 | 0.044781 | 0.020033 |
| target_snr_drop | ma2026_reproduction | 5 | 0.134257 | 0.093553 |
| target_snr_drop | proposed | 5 | 0.009705 | 0.000826 |
| target_snr_drop | proposed_full_pipeline | 5 | 0.010236 | 0.000975 |
| target_snr_drop | selected_aoa_fixed_kappa | 5 | 0.027279 | 0.005140 |
| target_snr_drop | single_target_ma_style | 5 | 0.020734 | 0.007324 |
| vehicle_event_nonstationary | ma2026_reproduction | 5 | 0.013217 | 0.004459 |
| vehicle_event_nonstationary | proposed | 5 | 0.004297 | 0.000281 |
| vehicle_event_nonstationary | proposed_full_pipeline | 5 | 0.004233 | 0.000342 |
| vehicle_event_nonstationary | selected_aoa_fixed_kappa | 5 | 0.018542 | 0.003839 |

Showing first 30 of 31 rows. See CSV files for full tables.

## Ablation Summary

| scenario | method | rmse_mm | unwrap_error_rate | selected_target_count |
|---|---|---|---|---|
| ma2023_balanced_good_targets | single_target_ma_style | 0.001460 | 0.000000 | 5 |
| ma2023_balanced_good_targets | ma2026_reproduction | 0.037064 | 0.000000 | 1 |
| ma2023_balanced_good_targets | multitarget_aoa_fixed_kappa | 0.019298 | 0.000000 | 5 |
| ma2023_balanced_good_targets | selected_aoa_fixed_kappa | 0.016383 | 0.000000 | 4 |
| ma2023_balanced_good_targets | proposed | 0.001109 | 0.000000 | 5 |
| ma2023_balanced_good_targets | proposed_full_pipeline | 0.001205 | 0.000000 | 4 |
| same_range_far_angles | single_target_ma_style | 0.031874 | 0.000000 | 4 |
| same_range_far_angles | range_bin_only_mixed_phase | 0.032853 | 0.000000 | 1 |
| same_range_far_angles | ma_style_iterative_beta_range_bin | 0.033796 | 0.000000 | 1 |
| same_range_far_angles | ma2026_reproduction | 0.127338 | 0.000000 | 1 |
| same_range_far_angles | multitarget_aoa_fixed_kappa | 0.044323 | 0.000000 | 4 |
| same_range_far_angles | selected_aoa_fixed_kappa | 0.036103 | 0.000000 | 4 |
| same_range_far_angles | proposed | 0.026568 | 0.000000 | 4 |
| same_range_far_angles | proposed_full_pipeline | 0.025306 | 0.000000 | 4 |
| target_snr_drop | single_target_ma_style | 0.018043 | 0.000200 | 5 |
| target_snr_drop | ma2026_reproduction | 0.299926 | 0.000000 | 1 |
| target_snr_drop | multitarget_aoa_fixed_kappa | 0.025974 | 0.000440 | 5 |
| target_snr_drop | selected_aoa_fixed_kappa | 0.028316 | 0.001100 | 4 |
| target_snr_drop | proposed | 0.008539 | 0.000200 | 5 |
| target_snr_drop | proposed_full_pipeline | 0.009899 | 0.000850 | 4 |
| low_snr_multitarget | single_target_ma_style | 0.016939 | 0.000000 | 5 |
| low_snr_multitarget | ma2026_reproduction | 0.047153 | 0.000000 | 1 |
| low_snr_multitarget | multitarget_aoa_fixed_kappa | 0.022874 | 0.000000 | 5 |
| low_snr_multitarget | selected_aoa_fixed_kappa | 0.031592 | 0.000050 | 4 |
| low_snr_multitarget | proposed | 0.011296 | 0.000000 | 5 |
| low_snr_multitarget | proposed_full_pipeline | 0.013590 | 0.000000 | 4 |
| vehicle_event_nonstationary | single_target_ma_style | 0.004710 | 0.000000 | 5 |
| vehicle_event_nonstationary | ma2026_reproduction | 0.016125 | 0.000000 | 1 |
| vehicle_event_nonstationary | multitarget_aoa_fixed_kappa | 0.021629 | 0.000000 | 5 |
| vehicle_event_nonstationary | selected_aoa_fixed_kappa | 0.019849 | 0.000000 | 4 |
| vehicle_event_nonstationary | proposed | 0.004721 | 0.000000 | 5 |
| vehicle_event_nonstationary | proposed_full_pipeline | 0.004474 | 0.000000 | 4 |

## AoA Sensitivity

| aoa_error_deg | method | rmse_mm | kappa_median_relative_error |
|---|---|---|---|
| 0.000000 | multitarget_aoa_fixed_kappa | 0.023770 | 0.000000 |
| 0.000000 | selected_aoa_fixed_kappa | 0.022540 | 0.011418 |
| 0.000000 | proposed | 0.007367 | 0.016162 |
| 0.000000 | proposed_full_pipeline | 0.007267 | 0.022888 |
| 3.000000 | multitarget_aoa_fixed_kappa | 0.024632 | 0.045286 |
| 3.000000 | selected_aoa_fixed_kappa | 0.022540 | 0.011418 |
| 3.000000 | proposed | 0.007609 | 0.054804 |
| 3.000000 | proposed_full_pipeline | 0.007267 | 0.022888 |
| 6.000000 | multitarget_aoa_fixed_kappa | 0.025642 | 0.093188 |
| 6.000000 | selected_aoa_fixed_kappa | 0.022540 | 0.011418 |
| 6.000000 | proposed | 0.007964 | 0.100776 |
| 6.000000 | proposed_full_pipeline | 0.007267 | 0.022888 |
| 10.000000 | multitarget_aoa_fixed_kappa | 0.027245 | 0.160900 |
| 10.000000 | selected_aoa_fixed_kappa | 0.022540 | 0.011418 |
| 10.000000 | proposed | 0.008644 | 0.151039 |
| 10.000000 | proposed_full_pipeline | 0.007267 | 0.022888 |
| 15.000000 | multitarget_aoa_fixed_kappa | 0.029674 | 0.251249 |
| 15.000000 | selected_aoa_fixed_kappa | 0.022540 | 0.011418 |
| 15.000000 | proposed | 0.009863 | 0.217682 |
| 15.000000 | proposed_full_pipeline | 0.007267 | 0.022888 |

## SNR Sensitivity

| snr_floor_db | method | rmse_mm | selected_target_count |
|---|---|---|---|
| 4.000000 | single_target_ma_style | 0.016939 | 5 |
| 4.000000 | ma2026_reproduction | 0.047153 | 1 |
| 4.000000 | selected_aoa_fixed_kappa | 0.031592 | 4 |
| 4.000000 | proposed | 0.011296 | 5 |
| 4.000000 | proposed_full_pipeline | 0.013590 | 4 |
| 6.000000 | single_target_ma_style | 0.014372 | 5 |
| 6.000000 | ma2026_reproduction | 0.049670 | 1 |
| 6.000000 | selected_aoa_fixed_kappa | 0.029693 | 4 |
| 6.000000 | proposed | 0.010111 | 5 |
| 6.000000 | proposed_full_pipeline | 0.011734 | 4 |
| 8.000000 | single_target_ma_style | 0.012445 | 5 |
| 8.000000 | ma2026_reproduction | 0.051485 | 1 |
| 8.000000 | selected_aoa_fixed_kappa | 0.027475 | 4 |
| 8.000000 | proposed | 0.009242 | 5 |
| 8.000000 | proposed_full_pipeline | 0.010219 | 4 |
| 10.000000 | single_target_ma_style | 0.011016 | 5 |
| 10.000000 | ma2026_reproduction | 0.052094 | 1 |
| 10.000000 | selected_aoa_fixed_kappa | 0.025491 | 4 |
| 10.000000 | proposed | 0.008490 | 5 |
| 10.000000 | proposed_full_pipeline | 0.009130 | 4 |
| 12.000000 | single_target_ma_style | 0.009972 | 5 |
| 12.000000 | ma2026_reproduction | 0.051615 | 1 |
| 12.000000 | selected_aoa_fixed_kappa | 0.023676 | 4 |
| 12.000000 | proposed | 0.007889 | 5 |
| 12.000000 | proposed_full_pipeline | 0.008239 | 4 |
