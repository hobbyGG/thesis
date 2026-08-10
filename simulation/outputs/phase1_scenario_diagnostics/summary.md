# Phase 1 Scenario Diagnostics

## Parameter Summary

| Scenario | 中文场景 | 验证目的 | Profile | Duration s | fs Hz | Peak mm | Quiet mm | Micro mm | Ramp mm | Main mm | Dominant Hz |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | literature_maglev_modal | 5.00 | 200.0 | 1.800 | 0.018 | 0.214 | 0.440 | 1.800 | 7.8;7.6;11.6 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | cold_start_ramp_strong_wrapping | 5.00 | 100.0 | 5.000 | 0.000 | 0.164 | 3.779 | 5.000 | 5;12;5.2 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.100 | 1.147 | 1.500 | 1.4;1.2;5.2 |
| literature_mmwbats_same_range_aliasing | mmWBat 同 rangeBin 角度混叠复刻 | 复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| literature_mmshm_adjacent_range_clutter | mmSHM 相邻 rangeBin 干扰复刻 | 复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| mixed_scatterer_rangebin | 同 rangeBin 复合散射 | 验证同一距离单元内复合散射造成相位畸变时，前端筛选与 confidence-aware R 的鲁棒性 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |
| low_snr_multitarget | 低 SNR 多目标 | 验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度 | cold_start_ramp | 5.00 | 100.0 | 1.500 | 0.000 | 0.101 | 1.148 | 1.500 | 1.4;1.2;5.2 |

## Plots

### literature_maglev_modal_response

- [time displacement](plots/literature_maglev_modal_response_time_displacement.svg)
- [time acceleration](plots/literature_maglev_modal_response_time_acceleration.svg)
- [frequency displacement](plots/literature_maglev_modal_response_frequency_displacement.svg)
- [frequency acceleration](plots/literature_maglev_modal_response_frequency_acceleration.svg)

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

### same_range_far_angles

- [time displacement](plots/same_range_far_angles_time_displacement.svg)
- [time acceleration](plots/same_range_far_angles_time_acceleration.svg)
- [frequency displacement](plots/same_range_far_angles_frequency_displacement.svg)
- [frequency acceleration](plots/same_range_far_angles_frequency_acceleration.svg)

### literature_mmwbats_same_range_aliasing

- [time displacement](plots/literature_mmwbats_same_range_aliasing_time_displacement.svg)
- [time acceleration](plots/literature_mmwbats_same_range_aliasing_time_acceleration.svg)
- [frequency displacement](plots/literature_mmwbats_same_range_aliasing_frequency_displacement.svg)
- [frequency acceleration](plots/literature_mmwbats_same_range_aliasing_frequency_acceleration.svg)

### literature_mmshm_adjacent_range_clutter

- [time displacement](plots/literature_mmshm_adjacent_range_clutter_time_displacement.svg)
- [time acceleration](plots/literature_mmshm_adjacent_range_clutter_time_acceleration.svg)
- [frequency displacement](plots/literature_mmshm_adjacent_range_clutter_frequency_displacement.svg)
- [frequency acceleration](plots/literature_mmshm_adjacent_range_clutter_frequency_acceleration.svg)

### mixed_scatterer_rangebin

- [time displacement](plots/mixed_scatterer_rangebin_time_displacement.svg)
- [time acceleration](plots/mixed_scatterer_rangebin_time_acceleration.svg)
- [frequency displacement](plots/mixed_scatterer_rangebin_frequency_displacement.svg)
- [frequency acceleration](plots/mixed_scatterer_rangebin_frequency_acceleration.svg)

### low_snr_multitarget

- [time displacement](plots/low_snr_multitarget_time_displacement.svg)
- [time acceleration](plots/low_snr_multitarget_time_acceleration.svg)
- [frequency displacement](plots/low_snr_multitarget_frequency_displacement.svg)
- [frequency acceleration](plots/low_snr_multitarget_frequency_acceleration.svg)
