# Phase 1 Simulation Validation Summary

## Feasibility Gates


## Metrics

| Scenario | 中文场景 | 验证目的 | Method | RMSE mm | MAE mm | Max Error mm | Unwrap Errors | Selected | Selected Indices | Corrected Obs | Unwrap Error Rate | Beta Rel Err | Beta Initial Rel Err | Beta Improvement Ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000000 | 0.000000 |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | range_bin_itoh | 0.026555 | 0.021305 | 0.093896 | 0 | 1 | [-1] | 1000 | 0.000000 |  |  |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | ma2026_reproduction | 0.376034 | 0.310386 | 0.785869 | 0 | 1 | [-1] | 1000 | 0.000000 |  |  |  |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | selected_aoa_fixed_beta | 0.066692 | 0.043732 | 0.321337 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000072 | 0.000072 | 1.000000 |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | direct_aoa_fixed_beta | 0.018550 | 0.014906 | 0.065880 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000072 | 0.000072 | 1.000000 |
| literature_maglev_modal_response | 文献主频驱动磁浮轨道梁响应 | 基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真 | superres_selfcal_aoa_fixed_beta | 0.018549 | 0.014906 | 0.065870 | 0 | 5 | [0, 1, 2, 3, 4] | 5000 | 0.000000 | 0.000032 | 0.000032 | 1.000000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | range_bin_itoh | 7.763019 | 6.119332 | 13.890220 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | ma2026_reproduction | 0.083064 | 0.062990 | 0.202622 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | selected_aoa_fixed_beta | 34.276924 | 25.486260 | 56.065227 | 1925 | 4 | [0, 1, 2, 3] | 2000 | 0.962500 | 0.000064 | 0.000064 | 1.000000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | direct_aoa_fixed_beta | 0.018818 | 0.015257 | 0.062978 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000064 | 0.000064 | 1.000000 |
| strong_wrapping | 强相位缠绕 | 验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕 | superres_selfcal_aoa_fixed_beta | 0.019007 | 0.015355 | 0.064863 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000069 | 0.000069 | 1.000000 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000000 | 0.000000 |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | range_bin_itoh | 0.180771 | 0.135997 | 1.044723 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | ma2026_reproduction | 0.295380 | 0.243583 | 0.693106 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | selected_aoa_fixed_beta | 0.075026 | 0.053733 | 0.236715 | 0 | 2 | [0, 1] | 1000 | 0.000000 | 0.034825 | 0.034825 | 1.000000 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | direct_aoa_fixed_beta | 0.045815 | 0.031402 | 0.155051 | 0 | 2 | [0, 1] | 1000 | 0.000000 | 0.034825 | 0.034825 | 1.000000 |
| same_range_far_angles | 同 rangeBin 远角度多目标 | 验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题 | superres_selfcal_aoa_fixed_beta | 0.023885 | 0.019572 | 0.068185 | 85 | 3 | [-1, 0, 1] | 1500 | 0.056667 | 0.110456 | 0.110456 | 1.000000 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | range_bin_itoh | 0.232154 | 0.186489 | 0.712804 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | ma2026_reproduction | 0.782403 | 0.651072 | 1.461143 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | selected_aoa_fixed_beta | 0.056596 | 0.043754 | 0.151048 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000070 | 0.000070 | 1.000000 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | direct_aoa_fixed_beta | 0.020161 | 0.016199 | 0.054912 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000070 | 0.000070 | 1.000000 |
| aoa_error_bootstrap | FFT AoA 初值误差与 beta 预校准 | 验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退 | superres_selfcal_aoa_fixed_beta | 0.020218 | 0.016253 | 0.055605 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000121 | 0.000121 | 1.000000 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | oracle | 0.000000 | 0.000000 | 0.000000 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000000 | 0.000000 |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | range_bin_itoh | 0.087776 | 0.057735 | 0.449093 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | ma2026_reproduction | 0.270958 | 0.223789 | 0.629633 | 0 | 1 | [-1] | 500 | 0.000000 |  |  |  |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | selected_aoa_fixed_beta | 0.078104 | 0.063807 | 0.205385 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000076 | 0.000076 | 1.000000 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | direct_aoa_fixed_beta | 0.058103 | 0.044138 | 0.219241 | 0 | 4 | [0, 1, 2, 3] | 2000 | 0.000000 | 0.000076 | 0.000076 | 1.000000 |
| target_snr_drop | 目标 SNR 退化 | 验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染 | superres_selfcal_aoa_fixed_beta | 0.056553 | 0.042885 | 0.213351 | 0 | 5 | [0, 1, 2, 3, 4] | 2500 | 0.000000 | 0.000137 | 0.000137 | 1.000000 |
