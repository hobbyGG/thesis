# 雷达–加速度融合：优先全文证据卡（工作稿）

本表聚焦“雷达位移 + 加速度计”这条主线。全文证据与摘要/题名证据分开标注；没有正文证据的条目不能作为算法来源或精度依据。

| ID / 状态 | 论文与观测 | 已核验算法链 | 实验与精度边界 | 可迁移到 IWR + ADXL355 的部分 | 证据 |
|---|---|---|---|---|---|
| R0007 / pending→全文候选 | 60 GHz BGT60TR13C + ADXL355 | 加速度双积分高通 → Hilbert/FFT 选有效段 → 雷达目标与比例系数自动标定 → 加速度辅助相位解缠 → 雷达低频/加速度高频互补滤波输出位移 | 9 个结构现场，最大 RMSE <0.06 mm；系统输出 100 Hz，不能证明 <100 Hz 全频带；0.4 mm 标定阈值是作者实验设定，不是普适检测下限 | 最直接的 ADXL355 先例：目标选择、比例标定、相位解缠和互补融合都可作为基线；你的主创新应放在更高带宽、微振幅质量门控和共同状态方程 | 本地全文：`../../../ref_papers/radar_method_modules/07_radar_sensor_fusion/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`，PDF pp.2–15；`priority_fulltext/structural_direct.md` |
| LOCAL-ACC2026 / 本地全文 | 60 GHz BGT60TR13C + 低成本 MEMS 加速度计 | 雷达位移/加速度 + MEMS 加速度 → FIR 互补滤波，低频取雷达、高频取 MEMS → 连续加速度 | 实验室 0.1/3 Hz；实桥 20/50/80 km/h 的 DC–2 Hz 频带 RMSE 相对 MEMS 降低 85.4%/82.5%/64.5%；输出是加速度，不能直接当位移精度 | 说明“频带互补”已有直接先例；ADXL355 可替代其 MEMS，但需要把状态量扩展到 0–100 Hz，并量化双积分漂移 | 本地全文：`../../../ref_papers/radar_method_modules/07_radar_sensor_fusion/Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf`，PDF pp.1,3–12；`priority_fulltext/structural_direct.md` |
| R1715 / pending→全文候选 | FMCW 雷达 + 加速度 + 应变计 | 自动多目标/LOS 标定 → 雷达遮挡检测 → 无遮挡时雷达+加速度互补融合；全遮挡时应变+加速度切换；ANN 学习应变到位移 | 75 min 连续桥梁测试，整体约 0.1 mm；三传感器系统，不应简化成二传感器论文 | 可迁移“质量门控 + 故障切换 + 互补融合”框架；当前二传感器版本可把全遮挡状态改为 ADXL355 预测并显式标记不确定度 | 本地全文：`../../../ref_papers/radar_method_modules/07_radar_sensor_fusion/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`，PDF pp.2–16；`priority_fulltext/structural_direct.md` |
| R0215 / pending→全文候选 | 60 GHz 雷达 + 同址 IMU（含陀螺） | 雷达 LOS 位移数值导数 → 分离 IMU 平移/重力 → 转角感知 LOS 比例标定 → 转角/角速度优化融合 → 位移与转角 | 100 Hz 雷达/IMU，6.5° 转动时平均位移误差 <0.3 mm；转角 RMSE 0.043°/0.095°；不是高刚度梁小转角的 10 μm 证据 | 可迁移旋转耦合和动态比例校准；ADXL355 没有陀螺，不能照搬完整转角链，可退化为结构几何先验或另加角速度传感器 | 本地全文：`../../../ref_papers/radar_method_modules/05_multi_target_full_field/B42_Simultaneous_displacement_and_rotation_estimation_for_flexible_structures_through_millimeter-wave_radar_and_inertial_sensor_fusion.pdf`，PDF pp.3–13；`priority_fulltext/structural_direct.md` |
| R0001 / pending | FMCW 雷达 + 加速度计 | 题名/既有索引指向“加速度辅助相位解缠 + FIR 融合”，但本地扫描 PDF 无可提取正文 | 不能据当前证据写精度、采样率或具体状态方程；应补出版社全文后再升级为 module | 是与你题目最直接的候选来源之一，但必须先核验其与 R0007 的方法重合和真实增量 | 当前仅有候选记录与本地扫描文件；保留 pending |
| R0202 / pending | FMCW 雷达 + 加速度辅助 Kalman | 题名指向 joint phase denoising/unwrapping 的 acceleration-aided KF，但当前缓存没有摘要/正文 | 不能把“Kalman + 解缠”当作论文已证实方法；需要全文和引用链 | 可能与论文主胶水高度接近，优先查是否已有完整的观测方程、加速度噪声模型和失锁切换 | 当前无摘要/全文证据，保留 pending |
| R1719 / pending | 毫米波雷达 + 加速度，间歇目标遮挡 | 题名指向遮挡情况下的 uninterrupted displacement estimation；本地文件为扫描版，正文未提取 | 不能据题名声称遮挡检测、状态切换或精度 | 重点检查是否已有“雷达质量门控 → 加速度预测 → 雷达恢复时重置”的完整胶水；这是你可形成主创新的直接竞争工作 | 当前仅题名/扫描文件，保留 pending |
| R1109 / module | IWR1642 77–81 GHz 雷达（无加速度） | 虚拟 chirp → range-angle 分离 → 多弧配准与圆拟合 → LOS 投影；用于产生高精度雷达位移 | 10–200 μm、20–400 Hz，典型 100 μm/约 5 m 平均幅值误差 3.174 μm；不是 10–20 m 桥梁现场验证 | 作为雷达观测支路基线；ADXL355 可接在相位解缠、质量评估和状态融合层 | `priority_fulltext/structural_direct.md`；本地 PDF pp.2–13 |
| R1151 / pending | AWR1843 多天线雷达（无加速度） | 反射标记 → 距离/角度分离 → beamforming/null steering → 天线排列多组观测 → 相位细化 → 多点位移 | 2 kHz 慢时间采样；峰峰值 RMSE 中位约 14.5 μm；峰峰值指标不能直接等于时域波形 RMSE | 适合作为雷达多点观测和质量支路；再由 ADXL355 提供动态先验或相位质量判断 | `priority_fulltext/structural_direct.md`；本地 PDF pp.3–17 |
| R0310 / transferable | 梁结构加速度/其他传感器数据融合（非毫米波雷达主线） | 动态位移重构与多种数据重构方法对比 | 可作通用加速度重构基线，但不能写成毫米波雷达方法来源 | 可借鉴状态变量、边界条件和重构误差评价；必须单独接入雷达绝对位移观测 | 当前优先队列摘要/公开全文入口，需在写作前补正文页码 |

## 当前结论

R0007 是目前本地全文中与 ADXL355 最直接的先例，但它的 100 Hz 输出、现场约 0.06 mm RMSE 和自动标定机制不能直接满足“前六阶 <100 Hz、约 10 μm”的目标。现有全文证据支持把以下部分列为已有模块：互补滤波、加速度积分、FIR/KF、雷达相位解缠、目标标定、遮挡切换。真正有机会形成你的胶水方法的是：

1. 以 ADXL355 加速度预测约束雷达相位增量和整数周选择；
2. 把 IQ 几何残差、相位连续性、SNR、加速度创新量统一成目标级观测协方差；
3. 在雷达失锁、散射点切换和多模态同时出现时做状态切换，并由雷达绝对位移重新校正积分漂移。

