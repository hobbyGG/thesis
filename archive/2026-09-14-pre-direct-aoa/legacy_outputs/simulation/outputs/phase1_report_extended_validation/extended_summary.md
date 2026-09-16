# Phase 1 Extended Experiment Summary

## Metadata

- Seeds: [2026, 2027, 2028, 2029, 2030]
- Monte Carlo scenarios: ['literature_maglev_modal_response', 'strong_wrapping', 'same_range_far_angles', 'aoa_error_bootstrap', 'target_snr_drop']
- Frontend angle FFT bins: [32, 48, 64, 96, 128]
- SNR floor levels: [4.0, 6.0, 8.0, 10.0, 12.0]

## Monte Carlo Summary

| scenario_label_zh | validation_purpose_zh | method | n | rmse_mean_mm | rmse_std_mm |
|---|---|---|---|---|---|
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | ma2026_reproduction | 5 | 0.600548 | 0.161907 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | proposed_full_pipeline_beta_confidence | 5 | 0.025829 | 0.003446 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | selected_aoa_fixed_beta | 5 | 0.056455 | 0.005671 |
| 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | ma2026_reproduction | 5 | 0.331432 | 0.039540 |
| 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | proposed_full_pipeline_beta_confidence | 5 | 0.018254 | 0.000736 |
| 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | selected_aoa_fixed_beta | 5 | 0.070682 | 0.005590 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 5 | 0.404249 | 0.175618 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_beta_confidence | 5 | 0.038078 | 0.021860 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_only_mixed_phase | 5 | 0.191170 | 0.103847 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_beta | 5 | 0.058237 | 0.006399 |
| 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | ma2026_reproduction | 5 | 0.121363 | 0.048559 |
| 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | proposed_full_pipeline_beta_confidence | 5 | 0.026154 | 0.008658 |
| 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | selected_aoa_fixed_beta | 5 | 32.966678 | 5.915197 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 5 | 0.282398 | 0.057507 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_beta_confidence | 5 | 0.061735 | 0.011698 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_beta | 5 | 0.071565 | 0.008492 |

## Ablation Summary

| scenario_label_zh | validation_purpose_zh | method | rmse_mm | unwrap_error_rate | selected_target_count |
|---|---|---|---|---|---|
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_only_mixed_phase | 0.154131 | 0.000000 | 1 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 0.295380 | 0.000000 | 1 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | multitarget_aoa_fixed_beta | 0.212713 | 0.000000 | 4 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_beta | 0.058812 | 0.000000 | 2 |
| 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_beta_confidence | 0.039996 | 0.000000 | 2 |
| mmWBat 同 rangeBin 角度混叠复刻 | 复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景 | ma2026_reproduction | 0.290717 | 0.000000 | 1 |
| mmWBat 同 rangeBin 角度混叠复刻 | 复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景 | multitarget_aoa_fixed_beta | 0.274793 | 0.000000 | 2 |
| mmWBat 同 rangeBin 角度混叠复刻 | 复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景 | selected_aoa_fixed_beta | 0.066337 | 0.000000 | 2 |
| mmWBat 同 rangeBin 角度混叠复刻 | 复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景 | proposed_full_pipeline_beta_confidence | 0.030984 | 0.000000 | 2 |
| mmSHM 相邻 rangeBin 干扰复刻 | 复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景 | ma2026_reproduction | 0.282011 | 0.000000 | 1 |
| mmSHM 相邻 rangeBin 干扰复刻 | 复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景 | multitarget_aoa_fixed_beta | 0.274793 | 0.000000 | 2 |
| mmSHM 相邻 rangeBin 干扰复刻 | 复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景 | selected_aoa_fixed_beta | 0.056110 | 0.000000 | 2 |
| mmSHM 相邻 rangeBin 干扰复刻 | 复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景 | proposed_full_pipeline_beta_confidence | 0.022272 | 0.000000 | 2 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 0.271081 | 0.000000 | 1 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | multitarget_aoa_fixed_beta | 0.184785 | 0.001600 | 5 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_beta | 0.078685 | 0.000500 | 4 |
| 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_beta_confidence | 0.062566 | 0.000500 | 4 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | ma2026_reproduction | 0.783854 | 0.000000 | 1 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | multitarget_aoa_fixed_beta | 0.181019 | 0.000000 | 5 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | selected_aoa_fixed_beta | 0.057941 | 0.000000 | 4 |
| FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | proposed_full_pipeline_beta_confidence | 0.026086 | 0.000000 | 4 |

## Frontend Angle FFT Sensitivity

| scenario_label_zh | frontend_num_virtual_rx | frontend_num_angle_bins | method | rmse_mm | beta_median_relative_error |
|---|---|---|---|---|---|
| FFT AoA 初值误差与 beta 收敛 | 8 | 32 | selected_aoa_fixed_beta | 0.057372 | 0.011991 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 32 | proposed_full_pipeline_beta_confidence | 0.028851 | 0.035088 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 48 | selected_aoa_fixed_beta | 0.057326 | 0.015392 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 48 | proposed_full_pipeline_beta_confidence | 0.034096 | 0.045619 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 64 | selected_aoa_fixed_beta | 0.057941 | 0.011563 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 64 | proposed_full_pipeline_beta_confidence | 0.026086 | 0.027593 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 96 | selected_aoa_fixed_beta | 0.057437 | 0.005622 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 96 | proposed_full_pipeline_beta_confidence | 0.026365 | 0.029203 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 128 | selected_aoa_fixed_beta | 0.057339 | 0.007812 |
| FFT AoA 初值误差与 beta 收敛 | 8 | 128 | proposed_full_pipeline_beta_confidence | 0.033522 | 0.043647 |

## SNR Sensitivity

| scenario_label_zh | snr_floor_db | method | rmse_mm | selected_target_count |
|---|---|---|---|---|
| 目标 SNR 退化 | 4.000000 | range_bin_itoh | 1.241061 | 1 |
| 目标 SNR 退化 | 4.000000 | ma2026_reproduction | 0.108096 | 1 |
| 目标 SNR 退化 | 4.000000 | selected_aoa_fixed_beta | 0.146839 | 2 |
| 目标 SNR 退化 | 4.000000 | proposed_full_pipeline_beta_confidence | 0.145419 | 2 |
| 目标 SNR 退化 | 6.000000 | range_bin_itoh | 2.645795 | 1 |
| 目标 SNR 退化 | 6.000000 | ma2026_reproduction | 0.138529 | 1 |
| 目标 SNR 退化 | 6.000000 | selected_aoa_fixed_beta | 0.107115 | 3 |
| 目标 SNR 退化 | 6.000000 | proposed_full_pipeline_beta_confidence | 0.102296 | 3 |
| 目标 SNR 退化 | 8.000000 | range_bin_itoh | 2.511648 | 1 |
| 目标 SNR 退化 | 8.000000 | ma2026_reproduction | 0.088444 | 1 |
| 目标 SNR 退化 | 8.000000 | selected_aoa_fixed_beta | 0.091684 | 3 |
| 目标 SNR 退化 | 8.000000 | proposed_full_pipeline_beta_confidence | 0.079989 | 3 |
| 目标 SNR 退化 | 10.000000 | range_bin_itoh | 0.114855 | 1 |
| 目标 SNR 退化 | 10.000000 | ma2026_reproduction | 0.111555 | 1 |
| 目标 SNR 退化 | 10.000000 | selected_aoa_fixed_beta | 0.078494 | 4 |
| 目标 SNR 退化 | 10.000000 | proposed_full_pipeline_beta_confidence | 0.060572 | 4 |
| 目标 SNR 退化 | 12.000000 | range_bin_itoh | 0.086391 | 1 |
| 目标 SNR 退化 | 12.000000 | ma2026_reproduction | 0.271520 | 1 |
| 目标 SNR 退化 | 12.000000 | selected_aoa_fixed_beta | 0.072537 | 4 |
| 目标 SNR 退化 | 12.000000 | proposed_full_pipeline_beta_confidence | 0.049634 | 4 |
