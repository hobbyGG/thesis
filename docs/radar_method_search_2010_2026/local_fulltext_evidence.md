# 已下载雷达全文的首轮方法证据

以下条目来自本地 PDF 的题名/摘要页或正文全文，不是只根据检索结果标题推断。页码以 PDF 页码 1 为起点；正式论文引用仍需按正文方程和实验章节复核。

| 本地全文 | 体制/场景 | 摘要中明确的输入→算法→输出 | 模块 |
|---|---|---|---|
| `ref_papers/radar_method_modules/_web_supplements/anghel2014_short_range_fmcw.pdf` p.1 | X-band 短距宽带 FMCW | beat/宽带扫频 → heterodyne 解决 DC/self-mixing/1/f，HAF + time-resampling 修正 VCO 非线性 → range profile/SAR 干涉相位位移 | M01/M05/M08 |
| `ref_papers/radar_method_modules/_web_supplements/bi2018_multi_arc.pdf` p.1 | 2.4 GHz 正交 CW + phase shifter | 多个相移 IQ 弧段 → multi-arc circle fitting → 3 mm 位移；误差由 4.529% 降至 1.073% | M04/M07 |
| `ref_papers/radar_method_modules/_web_supplements/high_efficiency_superresolution_fmcw.pdf` p.1 | FMCW 参数估计 | FFT 粗距离 → 按估计距离缩短输入样本 → MUSIC 超分辨；平均复杂度降低 88% | M01/M12 |
| `ref_papers/radar_method_modules/_web_supplements/hosseiny2023_mimo_gbsar.pdf` p.1–3 | W-band MIMO GBSAR 结构监测 | MIMO/SAR 复数回波 → range-angle/干涉处理 → 多目标结构形变 | M09/M11/M14 |
| `ref_papers/radar_method_modules/_web_supplements/kim2022_fmcw_reduced_search_music.pdf` p.1 | FMCW 高分辨估计 | FFT 粗估目标参数 → 缩小 MUSIC 输入和伪谱搜索区 → 低复杂度高分辨 range/参数 | M01/M12 |
| `ref_papers/radar_method_modules/_web_supplements/lee2021_cw_detrending.pdf` p.1 | 5.8 GHz CW | 基带波形 → 多项式 detrending 去除 DC drift → circle fitting/IQ imbalance 校准；位移误差平均 1.34 mm→0.62 mm | M03/M08 |
| `ref_papers/radar_method_modules/_web_supplements/michel2022_natural_frequency_gbr.pdf` p.1 | GBIR 桥梁 | 雷达位移衰减段 → least-squares 正弦拟合 + FDD → 固有频率；线性回归校正温度 | M16/M20 |
| `ref_papers/radar_method_modules/_web_supplements/rodrigues2022_modwt_jump_removal.pdf` p.1 | Doppler 雷达结构长期测量 | 位移序列 → wavelet multi-resolution / Haar-MODWT 检出短时跳变和畸变 → 修复后的连续位移 | M08/M17 |
| `ref_papers/radar_method_modules/_web_supplements/sipos2021_sfcw_static_echo_cancellation.pdf` p.1 | SFCW/GPR/TWIR 静态杂波 | 各频点回波 → 主动 IC 生成相消回波 → 多静态目标/天线耦合抑制，实测最高约 38 dB | M08 |
| `ref_papers/radar_method_modules/_web_supplements/wang2022_gbrar_colored_noise.pdf` p.1 | GB-RAR 高速铁路桥 | 形变序列 → 功率谱识别白/有色噪声 + MLE → 有色噪声修正形变；与水准测量优于 0.27 mm | M08/M20 |
| `ref_papers/radar_method_modules/_web_supplements/zakrzewski2014_ellipse_thesis.pdf` | 微波 CW IQ 校准 | IQ 椭圆 → ellipse fitting + affine normalization → 圆化复数轨迹/相位校准 | M03 |
| `ref_papers/radar_method_modules/_web_supplements/sotoudeh2025_gbir_review.pdf` p.1–3, 约 p.8 | GBIR 桥梁系统综述 | 104 篇 GBIR 研究 → 目标提取、位移/模态、融合与不确定度方法分类 | 索引，不作为单一算法 |

这些全文证据说明，方法模块确实大量来自不同雷达体制之间的迁移：CW/QFG 的 IQ 几何和圆拟合、FMCW 的 beat/range-bin 和 MUSIC、SAR/GBIR 的相位干涉和大气/几何校正，最后才在结构应用中组合成完整链路。
| `ref_papers/radar_method_modules/_web_supplements/marino2018_ground_based_radar_bridge_vibration.pdf` pp.1–4 | 5–6 GHz SFCW 地基雷达桥梁 | stepped-frequency 回波 → iFFT 距离压缩、相邻脉冲相位差、5-bin 相干性检查 → 3-bin boxcar 与经验三角波匹配滤波，检测车辆引起的桥梁振动峰 | M01/M05/M08/M16/M20 |
| `ref_papers/radar_method_modules/_web_supplements/lasri2025_insar_bridge_anomaly.pdf` pp.2–7 | Sentinel-1 MT-DInSAR 桥梁长期监测 | 分区 LOS 位移 → 升/降轨 East/Up 反演、温度-位移线性回归 → 残差与 Hotelling T² 控制图异常检测 | M05/M08/M14/M16/M20 |
