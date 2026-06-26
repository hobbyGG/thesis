# Phase 1 Extended Experiment Summary

## Metadata

- Seeds: [2026, 2027, 2028, 2029, 2030]
- Monte Carlo scenarios: ['nominal_multifrequency', 'ma2023_balanced_good_targets', 'same_range_far_angles', 'target_snr_drop', 'low_snr_multitarget', 'vehicle_event_nonstationary']
- AoA sensitivity levels: [0.0, 3.0, 6.0, 10.0, 15.0]
- SNR floor levels: [4.0, 6.0, 8.0, 10.0, 12.0]

## Monte Carlo Summary

| scenario_label_zh | validation_purpose_zh | method | n | rmse_mean_mm | rmse_std_mm |
|---|---|---|---|---|---|
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | ma2026_reproduction | 5 | 0.107009 | 0.037355 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed | 5 | 0.086322 | 0.014938 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed_full_pipeline | 5 | 0.086037 | 0.012636 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed_full_pipeline_kappa_confidence | 5 | 0.060245 | 0.010250 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | selected_aoa_fixed_kappa | 5 | 0.072398 | 0.007016 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | single_target_ma_style | 5 | 0.097591 | 0.016445 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | ma2026_reproduction | 5 | 0.226405 | 0.124899 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed | 5 | 0.011247 | 0.005071 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed_full_pipeline | 5 | 0.003960 | 0.000401 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed_full_pipeline_kappa_confidence | 5 | 0.002567 | 0.000299 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | selected_aoa_fixed_kappa | 5 | 0.002793 | 0.000295 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | single_target_ma_style | 5 | 0.028587 | 0.005855 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | ma2026_reproduction | 5 | 0.060768 | 0.050449 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | proposed | 5 | 0.079850 | 0.011802 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | proposed_full_pipeline | 5 | 0.079050 | 0.012985 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | proposed_full_pipeline_kappa_confidence | 5 | 0.019666 | 0.002435 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | selected_aoa_fixed_kappa | 5 | 0.052732 | 0.004870 |
| 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | single_target_ma_style | 5 | 0.088558 | 0.016174 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 5 | 0.121716 | 0.052700 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed | 5 | 0.076415 | 0.011276 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline | 5 | 0.080386 | 0.018359 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_kappa_confidence | 5 | 0.016271 | 0.008718 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_only_mixed_phase | 5 | 0.269230 | 0.137414 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_kappa | 5 | 0.050487 | 0.010166 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | single_target_ma_style | 5 | 0.085745 | 0.016231 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 5 | 0.102793 | 0.051941 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed | 5 | 0.084363 | 0.014146 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline | 5 | 0.084027 | 0.013677 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_kappa_confidence | 5 | 0.056421 | 0.013862 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_kappa | 5 | 0.086099 | 0.012087 |

Showing first 30 of 37 rows. See CSV files for full tables.

## Ablation Summary

| scenario_label_zh | validation_purpose_zh | method | rmse_mm | unwrap_error_rate | selected_target_count |
|---|---|---|---|---|---|
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | single_target_ma_style | 0.037021 | 0.000000 | 5 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | ma2026_reproduction | 0.164934 | 0.000000 | 1 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | multitarget_aoa_fixed_kappa | 0.180458 | 0.000000 | 5 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | selected_aoa_fixed_kappa | 0.002788 | 0.000000 | 5 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed | 0.014885 | 0.000000 | 5 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed_full_pipeline | 0.003905 | 0.000000 | 5 |
| Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | proposed_full_pipeline_kappa_confidence | 0.003032 | 0.000000 | 5 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | single_target_ma_style | 0.080351 | 0.000000 | 4 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_only_mixed_phase | 0.416463 | 0.000000 | 1 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma_style_iterative_beta_range_bin | 8.073679 | 0.000000 | 1 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 0.090558 | 0.000000 | 1 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | multitarget_aoa_fixed_kappa | 0.238050 | 0.000000 | 4 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_kappa | 0.051385 | 0.000000 | 3 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed | 0.067095 | 0.000000 | 4 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline | 0.064288 | 0.000000 | 3 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_kappa_confidence | 0.019840 | 0.000000 | 3 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | single_target_ma_style | 0.146961 | 0.006000 | 5 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 0.177654 | 0.000000 | 1 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | multitarget_aoa_fixed_kappa | 0.255912 | 0.006800 | 5 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_kappa | 0.077267 | 0.000000 | 3 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed | 0.074686 | 0.002400 | 5 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline | 0.075821 | 0.000000 | 3 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_kappa_confidence | 0.069571 | 0.000000 | 3 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | single_target_ma_style | 0.102452 | 0.000000 | 5 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | ma2026_reproduction | 0.111010 | 0.000000 | 1 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | multitarget_aoa_fixed_kappa | 0.228999 | 0.000000 | 5 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | selected_aoa_fixed_kappa | 0.073490 | 0.000500 | 4 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed | 0.080155 | 0.000000 | 5 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed_full_pipeline | 0.077537 | 0.000500 | 4 |
| 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | proposed_full_pipeline_kappa_confidence | 0.062440 | 0.000000 | 4 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | single_target_ma_style | 0.056232 | 0.000000 | 5 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | ma2026_reproduction | 0.035399 | 0.000000 | 1 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | multitarget_aoa_fixed_kappa | 0.216658 | 0.000400 | 5 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | selected_aoa_fixed_kappa | 0.029504 | 0.000000 | 4 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | proposed | 0.040004 | 0.000000 | 5 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | proposed_full_pipeline | 0.036729 | 0.000000 | 4 |
| 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | proposed_full_pipeline_kappa_confidence | 0.020384 | 0.000000 | 4 |

## AoA Sensitivity

| scenario_label_zh | aoa_error_deg | method | rmse_mm | kappa_median_relative_error |
|---|---|---|---|---|
| AoA 初值误差与转换系数收敛 | 0.000000 | multitarget_aoa_fixed_kappa | 0.222938 | 0.000000 |
| AoA 初值误差与转换系数收敛 | 0.000000 | selected_aoa_fixed_kappa | 0.053955 | 0.011418 |
| AoA 初值误差与转换系数收敛 | 0.000000 | proposed | 0.069999 | 0.005685 |
| AoA 初值误差与转换系数收敛 | 0.000000 | proposed_full_pipeline | 0.068810 | 0.013095 |
| AoA 初值误差与转换系数收敛 | 0.000000 | proposed_full_pipeline_kappa_confidence | 0.023215 | 0.010831 |
| AoA 初值误差与转换系数收敛 | 3.000000 | multitarget_aoa_fixed_kappa | 0.230444 | 0.045286 |
| AoA 初值误差与转换系数收敛 | 3.000000 | selected_aoa_fixed_kappa | 0.053955 | 0.011418 |
| AoA 初值误差与转换系数收敛 | 3.000000 | proposed | 0.079227 | 0.040500 |
| AoA 初值误差与转换系数收敛 | 3.000000 | proposed_full_pipeline | 0.068810 | 0.013095 |
| AoA 初值误差与转换系数收敛 | 3.000000 | proposed_full_pipeline_kappa_confidence | 0.023215 | 0.010831 |
| AoA 初值误差与转换系数收敛 | 6.000000 | multitarget_aoa_fixed_kappa | 0.239407 | 0.093188 |
| AoA 初值误差与转换系数收敛 | 6.000000 | selected_aoa_fixed_kappa | 0.053955 | 0.011418 |
| AoA 初值误差与转换系数收敛 | 6.000000 | proposed | 0.095077 | 0.079057 |
| AoA 初值误差与转换系数收敛 | 6.000000 | proposed_full_pipeline | 0.068810 | 0.013095 |
| AoA 初值误差与转换系数收敛 | 6.000000 | proposed_full_pipeline_kappa_confidence | 0.023215 | 0.010831 |
| AoA 初值误差与转换系数收敛 | 10.000000 | multitarget_aoa_fixed_kappa | 0.253766 | 0.160900 |
| AoA 初值误差与转换系数收敛 | 10.000000 | selected_aoa_fixed_kappa | 0.053955 | 0.011418 |
| AoA 初值误差与转换系数收敛 | 10.000000 | proposed | 0.124290 | 0.130850 |
| AoA 初值误差与转换系数收敛 | 10.000000 | proposed_full_pipeline | 0.068810 | 0.013095 |
| AoA 初值误差与转换系数收敛 | 10.000000 | proposed_full_pipeline_kappa_confidence | 0.023215 | 0.010831 |
| AoA 初值误差与转换系数收敛 | 15.000000 | multitarget_aoa_fixed_kappa | 0.275692 | 0.251249 |
| AoA 初值误差与转换系数收敛 | 15.000000 | selected_aoa_fixed_kappa | 0.053955 | 0.011418 |
| AoA 初值误差与转换系数收敛 | 15.000000 | proposed | 0.165400 | 0.191090 |
| AoA 初值误差与转换系数收敛 | 15.000000 | proposed_full_pipeline | 0.068810 | 0.013095 |
| AoA 初值误差与转换系数收敛 | 15.000000 | proposed_full_pipeline_kappa_confidence | 0.023215 | 0.010831 |

## SNR Sensitivity

| scenario_label_zh | snr_floor_db | method | rmse_mm | selected_target_count |
|---|---|---|---|---|
| 低 SNR 多目标 | 4.000000 | single_target_ma_style | 0.102452 | 5 |
| 低 SNR 多目标 | 4.000000 | ma2026_reproduction | 0.111010 | 1 |
| 低 SNR 多目标 | 4.000000 | selected_aoa_fixed_kappa | 0.073490 | 4 |
| 低 SNR 多目标 | 4.000000 | proposed | 0.080155 | 5 |
| 低 SNR 多目标 | 4.000000 | proposed_full_pipeline | 0.077537 | 4 |
| 低 SNR 多目标 | 4.000000 | proposed_full_pipeline_kappa_confidence | 0.062440 | 4 |
| 低 SNR 多目标 | 6.000000 | single_target_ma_style | 0.097287 | 5 |
| 低 SNR 多目标 | 6.000000 | ma2026_reproduction | 0.088572 | 1 |
| 低 SNR 多目标 | 6.000000 | selected_aoa_fixed_kappa | 0.069315 | 4 |
| 低 SNR 多目标 | 6.000000 | proposed | 0.074830 | 5 |
| 低 SNR 多目标 | 6.000000 | proposed_full_pipeline | 0.074375 | 4 |
| 低 SNR 多目标 | 6.000000 | proposed_full_pipeline_kappa_confidence | 0.051217 | 4 |
| 低 SNR 多目标 | 8.000000 | single_target_ma_style | 0.093578 | 5 |
| 低 SNR 多目标 | 8.000000 | ma2026_reproduction | 0.070314 | 1 |
| 低 SNR 多目标 | 8.000000 | selected_aoa_fixed_kappa | 0.065594 | 4 |
| 低 SNR 多目标 | 8.000000 | proposed | 0.072190 | 5 |
| 低 SNR 多目标 | 8.000000 | proposed_full_pipeline | 0.072149 | 4 |
| 低 SNR 多目标 | 8.000000 | proposed_full_pipeline_kappa_confidence | 0.042582 | 4 |
| 低 SNR 多目标 | 10.000000 | single_target_ma_style | 0.090908 | 5 |
| 低 SNR 多目标 | 10.000000 | ma2026_reproduction | 0.056383 | 1 |
| 低 SNR 多目标 | 10.000000 | selected_aoa_fixed_kappa | 0.062484 | 4 |
| 低 SNR 多目标 | 10.000000 | proposed | 0.070626 | 5 |
| 低 SNR 多目标 | 10.000000 | proposed_full_pipeline | 0.070443 | 4 |
| 低 SNR 多目标 | 10.000000 | proposed_full_pipeline_kappa_confidence | 0.035356 | 4 |
| 低 SNR 多目标 | 12.000000 | single_target_ma_style | 0.088976 | 5 |
| 低 SNR 多目标 | 12.000000 | ma2026_reproduction | 0.046117 | 1 |
| 低 SNR 多目标 | 12.000000 | selected_aoa_fixed_kappa | 0.059497 | 4 |
| 低 SNR 多目标 | 12.000000 | proposed | 0.069656 | 5 |
| 低 SNR 多目标 | 12.000000 | proposed_full_pipeline | 0.069121 | 4 |
| 低 SNR 多目标 | 12.000000 | proposed_full_pipeline_kappa_confidence | 0.029349 | 4 |
