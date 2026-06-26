# Phase 1 Scenario Diagnostics

## Parameter Summary

| Scenario | 中文场景 | 验证目的 | Profile | Duration s | fs Hz | Peak mm | Quiet mm | Micro mm | Ramp mm | Main mm | Dominant Hz |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| nominal_multifrequency | 标准多频振动 | 验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| measured_bridge_point4_transverse | 实测桥梁位移驱动 | 验证算法在真实桥梁单点非平稳位移波形上的可用性 | measured_bridge | 4.00 | 100.0 | 2.221 | 0.242 | 2.139 | 2.174 | 2.221 | 0.25;0.5;50 |
| ma2023_balanced_good_targets | Ma 2023 多优质目标仿真 | 模拟文献中多个候选目标质量接近的情况，检验多目标融合是否优于单目标选择 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.045 | 0.759 | 1.500 | 0.4;0.2;1 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | cold_start_ramp_strong_wrapping | 5.00 | 100.0 | 5.000 | 0.000 | 0.164 | 3.779 | 5.000 | 5;12;5.2 |
| aoa_error_bootstrap | AoA 初值误差与转换系数收敛 | 验证 AoA 冷启动存在误差时，在线转换系数 bootstrap 能否收敛 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| target_snr_drop | 目标 SNR 退化 | 验证 target-wise 自适应 R 能否降低退化目标对融合状态的污染 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| target_dropout | 目标遮挡/丢失 | 验证部分目标不可用时，多目标融合能否依靠剩余目标维持位移估计 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| mixed_scatterer_rangebin | 同 rangeBin 复合散射 | 验证同一距离单元内复合散射造成相位畸变时，前端筛选与自适应 R 的鲁棒性 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.100 | 1.147 | 1.500 | 1.4;1.2;5.2 |
| low_snr_multitarget | 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| vehicle_event_nonstationary | 车辆事件非平稳响应 | 验证由微弱振动逐渐进入强响应的车辆事件过程中，完整闭环能否稳定运行 | cold_start_vehicle_event | 5.00 | 100.0 | 1.500 | 0.000 | 0.096 | 0.182 | 1.500 | 1.4;1.2;1.6 |

## Plots

### nominal_multifrequency

- [time displacement](plots/nominal_multifrequency_time_displacement.svg)
- [time acceleration](plots/nominal_multifrequency_time_acceleration.svg)
- [frequency displacement](plots/nominal_multifrequency_frequency_displacement.svg)
- [frequency acceleration](plots/nominal_multifrequency_frequency_acceleration.svg)

### measured_bridge_point4_transverse

- [time displacement](plots/measured_bridge_point4_transverse_time_displacement.svg)
- [time acceleration](plots/measured_bridge_point4_transverse_time_acceleration.svg)
- [frequency displacement](plots/measured_bridge_point4_transverse_frequency_displacement.svg)
- [frequency acceleration](plots/measured_bridge_point4_transverse_frequency_acceleration.svg)

### ma2023_balanced_good_targets

- [time displacement](plots/ma2023_balanced_good_targets_time_displacement.svg)
- [time acceleration](plots/ma2023_balanced_good_targets_time_acceleration.svg)
- [frequency displacement](plots/ma2023_balanced_good_targets_frequency_displacement.svg)
- [frequency acceleration](plots/ma2023_balanced_good_targets_frequency_acceleration.svg)

### strong_wrapping

- [time displacement](plots/strong_wrapping_time_displacement.svg)
- [time acceleration](plots/strong_wrapping_time_acceleration.svg)
- [frequency displacement](plots/strong_wrapping_frequency_displacement.svg)
- [frequency acceleration](plots/strong_wrapping_frequency_acceleration.svg)

### aoa_error_bootstrap

- [time displacement](plots/aoa_error_bootstrap_time_displacement.svg)
- [time acceleration](plots/aoa_error_bootstrap_time_acceleration.svg)
- [frequency displacement](plots/aoa_error_bootstrap_frequency_displacement.svg)
- [frequency acceleration](plots/aoa_error_bootstrap_frequency_acceleration.svg)

### target_snr_drop

- [time displacement](plots/target_snr_drop_time_displacement.svg)
- [time acceleration](plots/target_snr_drop_time_acceleration.svg)
- [frequency displacement](plots/target_snr_drop_frequency_displacement.svg)
- [frequency acceleration](plots/target_snr_drop_frequency_acceleration.svg)

### target_dropout

- [time displacement](plots/target_dropout_time_displacement.svg)
- [time acceleration](plots/target_dropout_time_acceleration.svg)
- [frequency displacement](plots/target_dropout_frequency_displacement.svg)
- [frequency acceleration](plots/target_dropout_frequency_acceleration.svg)

### mixed_scatterer_rangebin

- [time displacement](plots/mixed_scatterer_rangebin_time_displacement.svg)
- [time acceleration](plots/mixed_scatterer_rangebin_time_acceleration.svg)
- [frequency displacement](plots/mixed_scatterer_rangebin_frequency_displacement.svg)
- [frequency acceleration](plots/mixed_scatterer_rangebin_frequency_acceleration.svg)

### same_range_far_angles

- [time displacement](plots/same_range_far_angles_time_displacement.svg)
- [time acceleration](plots/same_range_far_angles_time_acceleration.svg)
- [frequency displacement](plots/same_range_far_angles_frequency_displacement.svg)
- [frequency acceleration](plots/same_range_far_angles_frequency_acceleration.svg)

### low_snr_multitarget

- [time displacement](plots/low_snr_multitarget_time_displacement.svg)
- [time acceleration](plots/low_snr_multitarget_time_acceleration.svg)
- [frequency displacement](plots/low_snr_multitarget_frequency_displacement.svg)
- [frequency acceleration](plots/low_snr_multitarget_frequency_acceleration.svg)

### vehicle_event_nonstationary

- [time displacement](plots/vehicle_event_nonstationary_time_displacement.svg)
- [time acceleration](plots/vehicle_event_nonstationary_time_acceleration.svg)
- [frequency displacement](plots/vehicle_event_nonstationary_frequency_displacement.svg)
- [frequency acceleration](plots/vehicle_event_nonstationary_frequency_acceleration.svg)
