# Prompt：第一个创新点文献综述写作

你是一名熟悉结构健康监测、毫米波 FMCW 雷达位移测量、多传感器融合和 Kalman 滤波的博士论文写作助手。请基于本地 `ref_papers/` 中的文献，为论文“第一个创新点：面向多静止参考目标的结构主相位 Kalman 融合框架”撰写一段中文文献综述/研究现状。

## 0. 阅读范围与硬性约束

1. 只能使用本地 `ref_papers/` 中的文献，不要联网，不要编造不存在的论文。
2. 优先阅读 `ref_papers/00_primary_references/`，必要时再使用 `ref_papers/` 根目录中的 Kalman、数据融合、视觉/雷达对照文献。
3. 正文必须使用顺序编码引用，如 `[1]`、`[2]`、`[3]`。不要使用 `(Ma et al., 2023)`、`[Ma2023]` 或脚注式引用。
4. 文末必须给出“参考文献”列表，并按正文首次出现顺序编号。格式采用 GB/T 7714 风格，例如：
   `[1] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.`
5. 每一个正文引用都必须能在文末找到对应条目；文末每一条也必须在正文中出现。
6. 引用信息必须从 PDF 首页、文末 References、DOI 页或文件名/已有摘要卡片中核对。作者、题名、期刊/会议、年份、卷期、页码/文章号尽量完整；无法确认页码时可省略页码，但不要编造。
7. 不要堆砌文献清单。综述要体现“研究问题-已有解决路线-与本文方向最相关的研究-现有不足-本文吸收并改造的思路”。
8. 不要写成“本文方法章节”或“创新点证明”，而是写成博士论文中的研究现状/文献综述。最后一段可以自然引出本文工作。

## 1. 先阅读这些高水平论文的写法

请先打开并快速阅读以下论文的 Introduction / Related Work / Research Background 部分，学习它们组织研究现状的方式：

1. `ref_papers/00_primary_references/Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
   - 学习写法：先说明结构位移监测的重要性，再按接触式/非接触式和单传感/多传感融合分类，最后归纳单一传感器的局限。
2. `ref_papers/00_primary_references/Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
   - 学习写法：先从振动测量需求讲起，再比较传统传感器、光学设备和 RF/mmWave 方法，最后落到毫米波相位测量中的噪声、多径和 IQ 几何问题。
3. `ref_papers/00_primary_references/Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`
   - 学习写法：先介绍位移监测和毫米波雷达优势，再集中讨论短波长导致的相位缠绕问题，按 radar-only、dual-frequency、acceleration-aided 等路线评述，最后指出“只解缠、不降噪”的不足。
4. `ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
   - 学习写法：先讲长期桥梁监测的连续性需求，再指出雷达目标遮挡会导致位移缺失和解缠漂移，最后提出多目标/多传感切换的必要性。
5. `ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
   - 学习写法：从工程部署、成本、实时性、自动校准切入，说明已有方法从算法走向系统落地时仍存在自动 target 选择和转换因子标定问题。

综述的整体行文应参考这些论文：先宽后窄，先问题后方法，按技术路线归类，不要一篇一篇机械复述。

## 2. 本文第一个创新点的核心内容

本文研究的是倒挂式毫米波雷达结构位移监测：雷达安装在结构测点上并随结构共同运动，环境中的地面、桥下构件、支架等静止散射体作为参考 target。结构运动会引起雷达与这些静止 target 之间的相对距离变化，从而反映在 FMCW 雷达回波相位中。

第一个创新点不是重新发明毫米波雷达相位测距，也不是普通的单 target 雷达+加速度融合，而是：

> 面向多静止参考目标，建立以结构振动方向主相位为共享状态的 Kalman 融合框架。利用加速度预测结构主相位；将多个 target 的 wrapped phase 作为该主相位在不同 LoS 方向上的投影观测；通过预测辅助相位校正完成多 target 分支选择；再用多行观测矩阵和 target-wise 测量噪声协方差进行相位域融合。

要写清楚它和已有工作的关系：

1. mmVib 等工作证明了毫米波雷达相位可感知微米级/毫米级振动，并提供了相位-距离关系、IQ 圆弧、背景/多径影响、range-angle 分离等基础。
2. 结构位移监测综述说明了加速度、GNSS、视觉、雷达等传感器各有局限，多传感融合是重要趋势。
3. Ma/Zhanxiong/Sohn 系列论文已经提出了“雷达安装在结构测点上、利用周围环境 target、用加速度辅助位移估计、自动选择 target、估计 direction conversion factor”的基本可行性。
4. 后续工作进一步考虑 target occlusion、多 good targets、三传感器切换、低成本系统部署，说明实际桥梁监测中 target 可靠性和连续性是关键问题。
5. 最新 acceleration-aided Kalman filtering 工作把相位解缠和降噪统一进 Kalman 状态空间，但其状态相位主要是单个 target 的 LoS 连续相位，观测矩阵为单 target 观测。
6. 本文吸收上述思想，但将状态从“某一个 target 的 LoS 相位”改为“结构振动方向主相位”，把各 target 的方向转换系数放进观测矩阵，使多个静止参考 target 成为同一结构状态的多通道相位观测。

## 3. 建议引用的文献群

请从以下文献群中选择最相关的 10-18 篇引用。不要全部硬塞，优先保证论证链完整。

### A. 结构位移监测和多传感融合总背景

- `Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
- `Data fusion approaches for structural health monitoring and system identification Past, present, and future.pdf`
- `A state-space approach for deriving bridge displacement from acceleration.pdf`
- `Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric.pdf`
- `Real-time strong-motion broadband displacements from collocated GPS and accelerometers..pdf`

### B. 毫米波/微波雷达位移与振动测量基础

- `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
- `mmVib_MobiCom2020.pdf`（如已引用 TMC 期刊版，可不再引用会议版）
- `Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf`
- `A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf`
- `FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf`
- `Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf`
- `Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge.pdf`
- `Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge.pdf`

### C. 相位缠绕、相位解缠和加速度辅助

- `Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf`
- `A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf`
- `Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf`
- `Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`

### D. 倒挂式雷达、环境 target、转换因子、多 target/遮挡

- `Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
- `Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
- `Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
- `Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf`
- `Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf`
- `Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf`

### E. 多 target / range-angle / 投影观测 / 方法支撑

- `Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf`
- `ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
- `ref_papers/01_AoA/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
- `ref_papers/01_AoA/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`
- `ref_papers/01_AoA/Full-field 3D displacement measurement via microwave sensing.pdf`

### F. Kalman / 自适应测量噪声 / 多观测通道

- `Kalman1960.pdf`
- `Approaches_to_adaptive_filtering.pdf`
- `Adaptive Kalman Filtering for INS GPS.pdf`
- `An Adaptive Low-Cost INS GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation.pdf`
- `Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage-Husa Adaptive Robust Kalman Filter.pdf`
- `Multi-sensor and Multi-frequency Data Fusion for Structural Health Monitoring.pdf`

## 4. 综述结构要求

请写 1200-1800 字左右的中文文献综述，可分为 4-6 个自然段，不要写小标题也可以；如果使用小标题，最多 3 个。

推荐结构如下：

第一段：结构位移/振动监测的重要性，以及单一传感器的局限。说明加速度双积分会漂移，GNSS/视觉/应变/雷达各有约束，多传感融合成为趋势。

第二段：毫米波/微波雷达用于结构位移和振动测量的基础。说明雷达相位对 LoS 距离变化敏感，毫米波短波长带来高精度和小型化优势；同时指出多径、IQ 叠加、target 识别、LOS 转换和相位缠绕是关键难点。

第三段：已有相位解缠和融合方法。按路线评述：传统 Itoh/MDACM、dual-frequency、Doppler/multi-chirp、acceleration-aided、Kalman joint denoising/unwrapping。重点说明 Ma 等人的 Kalman 框架把加速度预测、相位分支校正和降噪结合起来，但主要面向单 target LoS 相位。

第四段：倒挂式雷达和环境静止 target。说明已有研究已将雷达与加速度计共址安装在结构测点，通过周围环境 target 恢复结构位移，并使用自动 target 选择、direction conversion factor、FIR/Kalman 融合等；后续研究考虑了 target occlusion、多 good targets、低成本系统和现场部署。指出这些工作多以“选择单个 best target”或“多 target 切换/补偿”为主，尚未把多个静止 reference targets 统一建模为同一结构主相位的多通道投影观测。

第五段：引出本文创新点。写明本文吸收了哪些人的做法：吸收 mmVib 的相位-距离和 IQ 几何思想，吸收 Ma 等人的加速度辅助相位预测、转换因子标定和 Kalman 相位解缠/降噪思想，吸收多 target 遮挡管理和自适应滤波中按观测质量调节权重的思想。在本文场景下进一步改造为：以结构振动方向主相位作为共享状态；加速度直接预测主相位；每个 target 的 wrapped phase 通过方向转换系数构成观测矩阵的一行；采用预测辅助相位校正和 target-wise 测量噪声协方差，实现多静止参考目标的相位域融合。

## 5. 关键表述边界

写作时请注意这些边界，避免说错：

1. 不要说本文“首次提出毫米波雷达结构位移监测”；已有大量雷达桥梁位移和振动测量文献。
2. 不要说本文“首次使用加速度辅助相位解缠”；已有 Ma 等工作。
3. 不要把本文的多 target 写成“多个结构测点的多点监测”。本文的多 target 是同一个结构测点位移在多个环境静止散射体 LoS 方向上的投影观测。
4. 不要把转换因子简单等同于 AoA。转换因子本质是 LoS 位移到结构振动方向位移的比例关系，可由几何/AoA 提供初值，但也可能是复合散射 target 的等效转换系数。
5. 不要写成 target selection 依赖完整相位解缠。本文倾向于目标选择阶段 unwrap-free，后续 Kalman 融合阶段再进行预测辅助相位校正。
6. 不要夸大固定 Q、自适应 R。可以写成：已有 adaptive filtering / covariance matching 思想说明测量噪声可随观测质量变化；本文在第一版中固定过程噪声 Q，并主要通过 target-wise R 表达不同 target 的观测可靠性。

## 6. 输出格式

请按以下格式输出：

### 文献综述正文

直接给出可放入论文的中文正文。正文中使用 `[1]` 这种顺序编码引用。

### 参考文献

按正文首次出现顺序列出 GB/T 7714 风格参考文献。示例格式：

`[1] 作者. 题名[J]. 期刊名, 年份, 卷(期): 页码或文章号.`

会议论文可写：

`[n] 作者. 题名[C]//会议名. 出版地: 出版者, 年份: 页码.`

学位论文可写：

`[n] 作者. 题名[D]. 城市: 学校, 年份.`

如果 PDF 信息不足，请在参考文献条目后用括号注明“页码信息未在本地文件中确认”，不要编造页码。

### 自检清单

最后用 5-8 条列出你已检查的事项，包括：

- 是否只使用了 `ref_papers` 中的文献；
- 正文引用和文末条目是否一一对应；
- 是否按 GB/T 7714 风格整理；
- 是否覆盖结构位移监测、毫米波雷达、相位解缠、倒挂式 target、Kalman 融合、多 target 主相位这条论证链；
- 是否避免把本文贡献夸大成已有工作的首次提出。
