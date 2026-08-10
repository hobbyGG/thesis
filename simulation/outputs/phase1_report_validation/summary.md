# Phase 1 Simulation Validation Summary

## Feasibility Gates

- PASS: strong_wrapping_full_pipeline_beats_range_bin_itoh value=0.037236114214796834 threshold=7.763018544941675
- PASS: strong_wrapping_range_bin_itoh_rmse_ge_2x_full_pipeline value=208.48089841385269 threshold=2.0
- PASS: strong_wrapping_full_pipeline_rmse_le_reasonable_threshold value=0.037236114214796834 threshold=0.5
- PASS: same_range_far_angles_full_pipeline_selects_two_same_range_targets value=1 threshold=1
- PASS: same_range_far_angles_full_pipeline_rmse_le_0p10mm value=0.03999557902768956 threshold=0.1
- PASS: target_snr_drop_full_pipeline_beats_selected_fixed_r value=0.06256558596524327 threshold=0.07868454819203342
- PASS: aoa_bootstrap_beta_median_relative_error_le_0p10 value=0.027593130126966015 threshold=0.1

## Metrics

| Scenario | 中文场景 | 验证目的 | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors | Selected | Selected Indices | Corrected Obs | Unwrap Error Rate | Beta Rel Err | Beta Initial Rel Err | Beta Improvement Ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000000 | 0.000000 |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | range_bin_itoh | 0.026555 | 0.021305 | 0.093896 | 0 | 1 | [-1] | 1000 | 0.000000 |  |  |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | ma2026_reproduction | 0.376029 | 0.310384 | 0.785863 | 0 | 1 | [-1] | 1000 | 0.000000 |  |  |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | selected_aoa_fixed_beta | 0.067747 | 0.044374 | 0.326011 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.002582 | 0.002582 | 1.000000 |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | proposed_full_pipeline_beta_confidence | 0.018748 | 0.014913 | 0.067049 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.005751 | 0.002582 | 2.227000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | range_bin_itoh | 7.763019 | 6.119332 | 13.890220 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | ma2026_reproduction | 0.082161 | 0.062394 | 0.198524 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | selected_aoa_fixed_beta | 29.826083 | 22.647848 | 46.390063 | 1928 | 4 | [0, 1, 2, 3] | 2000 | 0.964000 | 0.011563 | 0.011563 | 1.000000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | proposed_full_pipeline_beta_confidence | 0.037236 | 0.024399 | 0.358650 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.108249 | 0.011563 | 9.361581 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000000 | 0.000000 |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_itoh | 0.180771 | 0.135997 | 1.044723 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 0.295380 | 0.243583 | 0.693106 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_beta | 0.058812 | 0.047025 | 0.144477 | 0 | 2 | [0, 1] | 1000 | 0.000000 | 0.014731 | 0.014731 | 1.000000 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | proposed_full_pipeline_beta_confidence | 0.039996 | 0.031072 | 0.149262 | 0 | 2 | [0, 1] | 1000 | 0.000000 | 0.026395 | 0.014731 | 1.791813 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | range_bin_itoh | 0.232154 | 0.186489 | 0.712804 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | ma2026_reproduction | 0.783854 | 0.652180 | 1.450427 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | selected_aoa_fixed_beta | 0.057941 | 0.044799 | 0.154507 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.011563 | 0.011563 | 1.000000 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 收敛 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，在线 beta bootstrap 能否收敛 | proposed_full_pipeline_beta_confidence | 0.026086 | 0.021135 | 0.075295 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.027593 | 0.011563 | 2.386315 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | range_bin_itoh | 0.087776 | 0.057735 | 0.449093 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 0.271081 | 0.223912 | 0.633792 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_beta | 0.078685 | 0.064123 | 0.212419 | 1 | 4 | [0, 1, 2, 3] | 2000 | 0.000500 | 0.011563 | 0.011563 | 1.000000 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | proposed_full_pipeline_beta_confidence | 0.062566 | 0.047062 | 0.268931 | 1 | 4 | [0, 1, 2, 3] | 2000 | 0.000500 | 0.014199 | 0.011563 | 1.227987 |
