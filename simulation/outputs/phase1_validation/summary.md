# Phase 1 Simulation Validation Summary

## Feasibility Gates

- PASS: strong_wrapping_full_pipeline_beats_range_bin_itoh value=0.014334129193976817 threshold=5.547728952857639
- PASS: strong_wrapping_range_bin_itoh_rmse_ge_2x_full_pipeline value=387.0293673081158 threshold=2.0
- PASS: strong_wrapping_full_pipeline_rmse_le_reasonable_threshold value=0.014334129193976817 threshold=0.5
- PASS: same_range_far_angles_full_pipeline_selects_two_same_range_targets value=3 threshold=1
- PASS: same_range_far_angles_full_pipeline_rmse_le_0p10mm value=0.013990775171946222 threshold=0.1
- PASS: same_range_far_angles_full_pipeline_beats_ma2026_reproduction value=0.013990775171946222 threshold=0.0905575799242464
- PASS: vehicle_event_full_pipeline_selected_count_ge_1 value=4 threshold=1
- PASS: vehicle_event_full_pipeline_excludes_target4 value=0 threshold=0
- PASS: vehicle_event_full_pipeline_unwrap_error_rate_eq_0 value=0.0 threshold=0.0
- PASS: vehicle_event_full_pipeline_rmse_le_0p05mm value=0.014336096473320665 threshold=0.05
- PASS: target_snr_drop_full_pipeline_beats_selected_fixed_r value=0.06040964044135153 threshold=0.07726744666845607
- PASS: aoa_bootstrap_kappa_median_relative_error_le_0p05 value=0.009933754162751801 threshold=0.05

## Metrics

| Scenario | 中文场景 | 验证目的 | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors | Selected | Selected Indices | Corrected Obs | Unwrap Error Rate | Kappa Rel Err |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000000 |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | range_bin_itoh | 0.013603 | 0.010818 | 0.051414 | 0 | 1 | [-1] | 1000 | 0.000000 |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | ma2026_reproduction | 0.012246 | 0.009908 | 0.039904 | 0 | 1 | [-1] | 1000 | 0.000000 |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | selected_aoa_fixed_kappa | 0.058853 | 0.037609 | 0.263249 | 0 | 5 | [1, 0, 2, 3, 4] | 5000 | 0.000000 | 0.001907 |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | proposed_full_pipeline_kappa_confidence | 0.008715 | 0.007043 | 0.030932 | 0 | 5 | [1, 0, 2, 3, 4] | 5000 | 0.000000 | 0.001781 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | range_bin_itoh | 5.547729 | 4.389774 | 11.891334 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | ma2026_reproduction | 0.034060 | 0.027102 | 0.112841 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | selected_aoa_fixed_kappa | 12.386050 | 10.079380 | 24.324625 | 1214 | 4 | [0, 1, 2, 3] | 2000 | 0.607000 | 0.011418 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | proposed_full_pipeline_kappa_confidence | 0.014334 | 0.011242 | 0.044075 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.010163 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000000 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_itoh | 0.074487 | 0.051408 | 0.286286 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 0.090558 | 0.060796 | 0.310925 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_kappa | 0.051385 | 0.039433 | 0.137304 | 0 | 3 | [0, 2, 1] | 1500 | 0.000000 | 0.022859 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_kappa_confidence | 0.013991 | 0.010686 | 0.039336 | 0 | 3 | [0, 2, 1] | 1500 | 0.000000 | 0.026147 |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | range_bin_itoh | 0.016731 | 0.013439 | 0.049775 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | ma2026_reproduction | 0.038633 | 0.031051 | 0.121285 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | selected_aoa_fixed_kappa | 0.053955 | 0.041141 | 0.144356 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.011418 |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | proposed_full_pipeline_kappa_confidence | 0.015254 | 0.012201 | 0.043458 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.009934 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | range_bin_itoh | 2.495128 | 1.760443 | 4.444193 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 0.177654 | 0.158982 | 0.343301 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_kappa | 0.077267 | 0.062431 | 0.201678 | 0 | 3 | [0, 2, 3] | 1500 | 0.000000 | 0.015013 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_kappa_confidence | 0.060410 | 0.048215 | 0.210195 | 0 | 3 | [0, 2, 3] | 1500 | 0.000000 | 0.009121 |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | range_bin_itoh | 0.022440 | 0.018447 | 0.071383 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | ma2026_reproduction | 0.035399 | 0.028096 | 0.132997 | 0 | 1 | [-1] | 500 | 0.000000 |  |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | selected_aoa_fixed_kappa | 0.029504 | 0.018263 | 0.141226 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.011418 |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | proposed_full_pipeline_kappa_confidence | 0.014336 | 0.011763 | 0.036269 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.011447 |
