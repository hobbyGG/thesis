# Pending 条目补充证据（2026-10-08）

本文件只记录本轮对 pending 条目的补充证据，不修改 `review_2026_10_08/decisions_merged.jsonl`。证据等级严格区分：`fulltext_local` 为本地可提取正文；`publisher_abstract` 为 DOI/出版社或作者机构页面公开摘要；`secondary_abstract` 为二手索引页面摘要；`title_only` 仅有题名，不能据此宣称方法模块。

## R0001 — Structural displacement estimation using accelerometer and FMCW millimeter wave radar

**证据等级：`fulltext_local`（补充作者公开 PDF 镜像提取文本 `priority_fulltext/text/R0001.txt`（原 PDF 临时下载为 `/tmp/R0001.pdf`），来源为作者公开 PDF 镜像；同时有 HKUST 机构摘要）。** 正文摘要明确：共址加速度计与 FMCW 毫米波雷达融合；短于 1 min 的初始数据自动选最佳目标并估计 LOS 到结构振动方向的转换因子；加速度辅助相位解缠；雷达位移与加速度经 FIR 滤波融合。正文第 3 节进一步给出三步最佳目标/转换因子标定、加速度辅助解缠和 FIR 位移融合。四层楼模型及人行桥实验误差均小于 1 mm。

**可迁移模块：** `radar_accel_fusion`（目标选择/方向因子标定、加速度辅助解缠、FIR 融合）。输入为雷达相位/目标回波和共址加速度；输出连续结构位移。迁移条件是目标反射稳定、传感器共址或几何方向可标定，并接受 FIR 的短时延与加速度低频漂移限制。建议由 pending 升为 `module`，但保留实验场景边界。

## R0202 — Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring

**证据等级：`fulltext_local`（`text/R0202.txt`，对应本地 PDF）。** 摘要及正文式(6)–(15)明确：将雷达相位建模为离散常加速度状态 `[phase, phase-rate]`；加速度进入状态预测；以观测相位为量测；按预测相位执行 `2π round((x_pred-z)/2π)` 校正后递归 Kalman 更新，同时完成去噪和解缠。式(16)–(17)用解缠相位能量最小化自适应选择过程噪声，式(18)–(19)用带通后的加速度相位与雷达相位线性拟合方向转换因子。四层楼模型和 45 m 人行桥实验报告高噪声下有效解缠，误差分别约 2.1 rad、0.2 rad（相位误差指标）。

**可迁移模块：** `accel_aided_kalman_phase_unwrap`。输入是 FMCW 包裹相位、采样间隔和同向加速度；输出连续去噪相位及按波长换算的 LOS 位移。迁移条件是加速度与雷达目标运动方向一致、采样时间同步，并需重新标定 `Q/R`、波长及方向系数；论文验证对象为结构振动，不能直接推断其他雷达体制。

## R1491 — Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping

**证据等级：`publisher_abstract`（ScienceDirect 条目，DOI `10.1016/j.measurement.2025.120029`）。** 出版社摘要/Highlights 明确提出 multi-chirp 自适应解缠：每个时间步由多 chirp 估计相位变化率，预测下一时刻相位并据此确定解缠参考范围；不依赖经验阈值或额外传感器。实验覆盖最大约 5 cm 位移，实验室 RMSE 降低 98.80%，脚桥现场误差约 0.04 mm。

当前证据是公开摘要而非本地正文；可确认方法方向和实验边界，不能核验全部公式、chirp 配置或异常值处理。建议升级为 `module`（摘要级），模块为 `multi_chirp_predictive_phase_unwrap`，迁移时需保留多 chirp 帧内相位率估计和结构位移场景限制。

## R1751 — FMCW Radar for Noncontact Bridge Structure Displacement Estimation

**证据等级：`secondary_abstract`（ResearchGate 公开记录复现 IEEE 摘要；IEEE 页面可核对题名/DOI，但正文闭源）。** 摘要指出改进 FMCW 雷达通过相位信息提取获得位移分辨率；用倾角仪检测雷达仰角以修正布置导致的精度下降；仿真和桥模型实验验证；支持跨桥梁多点检测并获取位移剖面。

摘要足以确认“相位位移 + 倾角/几何修正 + 多点检测”模块，但来源不是出版社全文，不能补写未公开的滤波、解缠或误差模型。建议升级为 `module`（摘要级），模块为 `fmcw_phase_displacement_geometry_correction`；迁移条件是需要倾角/安装几何信息，且验证边界为桥梁模型与多点桥跨剖面。

## R1729 — Displacement Estimation of Reactor Containment Buildings Using Accelerometer and FMCW Millimeter-Wave Radar

**证据等级：`fulltext_local`（proceedings PDF 提取文本 `priority_fulltext/text/R1729.txt`（原 PDF 临时下载为 `/tmp/R1729.pdf`）；出版社页面同时提供同一全文 PDF）。** 正文摘要明确：三轴 MEMS 加速度计与 60 GHz FMCW 雷达相位融合；短时雷达/加速度数据自动最佳目标选择和 LOS→实际方向转换因子；加速度辅助自适应解缠；雷达位移与加速度经 FIR 滤波抑制噪声和漂移；结构模型实验误差低于 1 mm，摘要宣称静态/动态分辨率优于 0.1 mm。

可迁移模块与 R0001 同类，为 `radar_accel_fusion` 的 RCB 场景实例。证据只支持摘要和 proceedings 正文中明确的链路；“核设施可部署、低于 1000 美元”等是作者设计/预测，不能当作已验证性能。建议升级为 `module`，并标注 RCB 结构模型实验边界。

## R1719 — Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion

**证据等级：`publisher_abstract`（ScienceDirect 文章页及 KAIST 作者机构页，DOI `10.1016/j.ymssp.2024.111888`）。** 摘要明确：短时雷达/加速度数据选多个稳定目标并估计方向转换因子；至少一个目标可见时执行加速度辅助解缠、遮挡检测和目标切换；全部目标遮挡时用加速度重建遮挡段位移；目标恢复后用多目标绝对相位解缠去除漂移。10 m 桥模型及两跨脚桥验证，整体误差低于 0.1 mm。

当前为公开摘要证据，未把出版社付费正文当作已获取全文。建议升级为 `module`（摘要级），模块为 `occlusion_aware_multitarget_radar_accel_fusion`；迁移条件包括多稳定反射目标、遮挡检测和加速度积分重建，不能将 0.1 mm 直接外推到其他结构或雷达体制。
