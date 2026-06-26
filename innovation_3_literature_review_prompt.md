# Prompt：第三个创新点文献综述写作

你是一名熟悉结构健康监测、毫米波 FMCW/MIMO 雷达、相位位移测量、LoS 几何投影、方向转换系数和多散射体复数叠加建模的博士论文写作助手。请基于本地 `ref_papers/` 中的文献，为论文“第三个创新点：Range-Angle Target 的转换系数估计与等效稳定性”撰写一段中文文献综述/研究现状。

## 0. 阅读范围与硬性约束

1. 只能使用本地 `ref_papers/` 中的文献，不要联网，不要编造不存在的论文。
2. 优先阅读 `ref_papers/00_primary_references/`、`ref_papers/01_AoA/` 及其 README；必要时再使用 `ref_papers/` 根目录中的几何测量、Kalman/融合、视觉/雷达位移对照文献。
3. 正文必须使用顺序编码引用，如 `[1]`、`[2]`、`[3]`。不要使用 `(Ma et al., 2024)`、`[Ma2024]` 或脚注式引用。
4. 文末必须给出“参考文献”列表，并按正文首次出现顺序编号。格式采用 GB/T 7714 风格，例如：
   `[1] MA Z, HAN K, CHOI J, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.`
5. 每一个正文引用都必须能在文末找到对应条目；文末每一条也必须在正文中出现。
6. 引用信息必须从 PDF 首页、文末 References、DOI 页或已有摘要卡片中核对。作者、题名、期刊/会议、年份、卷期、页码/文章号尽量完整；无法确认页码时可省略页码，但不要编造。
7. 不要堆砌文献清单。综述要体现“LoS 位移转换为何重要 -> 已有 direction conversion factor 怎么估计 -> rangeBin 混合散射为什么会让转换系数不稳定 -> range-angle target 如何降低混叠 -> 本文如何把几何初值、局部连续相位和稳定性检查结合起来”。
8. 不要写成公式推导章节。可以概述关键机理，但主体要保持博士论文研究现状/文献综述风格。

## 1. 先阅读这些高水平论文/材料的写法

请先打开并快速阅读以下文献的 Introduction / Research Background / Method Overview 部分，学习它们如何组织研究现状：

1. `ref_papers/00_primary_references/Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
   - 学习写法：先说明不同传感器位移测量坐标、安装位置和长期监测条件的限制，再归纳多传感融合需求。
2. `ref_papers/00_primary_references/Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
   - 学习写法：重点看雷达与加速度计共址安装、环境 target、LoS 位移到结构振动方向位移的 direction conversion factor、自动 target 选择和初始标定。
3. `ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
   - 学习写法：看它如何在长期监测和 target occlusion 语境下讨论多 good targets、转换因子和连续位移恢复。
4. `ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
   - 学习写法：看自动校准时段识别、best target 选择和转换因子估计如何被组织成工程落地问题。
5. `ref_papers/01_AoA/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
   - 学习写法：重点看同 rangeBin 多目标耦合、range-angle joint dimension 和 LoS correction 的表述。
6. `ref_papers/01_AoA/Full-field 3D displacement measurement via microwave sensing.pdf`
   - 学习写法：看 LOS 位移如何通过几何关系转换到结构坐标系，理解经验 beta 与几何投影关系的区别。
7. `ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
   - 学习写法：看 range-angle component 的相位演化如何用于微动量化，为“range-angle target 相位”提供基础。

综述整体应先从 LoS 位移与结构真实位移的转换问题讲起，再进入 direction conversion factor 的已有估计方式，最后收束到 rangeBin 混合散射导致的等效转换系数稳定性问题。

## 2. 本文第三个创新点的核心内容

倒挂式毫米波雷达中，雷达安装在结构测点上并随结构共同运动，环境中的静止散射体因雷达自身位移产生相位变化。雷达相位直接反映的是该 target 的 LoS 距离变化，而论文关心的是结构振动方向上的位移。因此，需要方向转换系数 `beta` 或投影系数 `eta` 将 LoS 相位/位移映射到结构振动方向。

已有雷达+加速度结构位移监测研究通常在初始标定窗口内选择一个 target，并通过加速度参考位移或频带一致性估计 direction conversion factor。这在单一散射体主导时有效。但在自然反射环境中，一个 rangeBin 可能包含多个不同角度散射体，rangeBin 总回波是多个相量的叠加。若直接对整个 rangeBin 相位拟合转换系数，得到的 `beta` 可能不是某个物理反射点的几何系数，而是一个窗口相关、幅值相关、散射状态相关的混合等效系数。

第三个创新点不是简单提出“再估计一个 beta”，而是：

> 将转换系数估计从 rangeBin 层面推进到 range-angle target 层面。对每个通过筛选的 target `T=(b,C)` 建立方向转换关系；若 target 是单个 range-angle bin，则 beta 对应该方向的 LoS 投影；若 target 是角度接近的 angle cluster，则 beta 是该散射簇的等效转换系数。本文利用 AoA/几何关系给出初值，并在局部连续相位或 Kalman 预测辅助校正相位的基础上递推修正；同时分析等效转换系数何时稳定，指出当 target 内主要散射体投影系数接近或由单一散射体主导时，固定 beta 合理；当多个强散射体投影差异大且相对相位随结构位移明显变化时，固定 beta 会漂移。

要写清楚它和已有工作的关系：

1. 雷达位移测量文献普遍承认相位测得的是 LoS displacement，结构真实位移需要几何修正或 direction conversion factor。
2. Ma/Zhanxiong/Sohn 系列工作已经提出通过加速度辅助标定 target 和转换因子，并在低成本系统中自动完成 target 选择与 beta 估计。
3. mmVib/mmWBat/mmSHM 和 full-field microwave sensing 说明 range-angle component 的复数相位可用于微动/振动恢复，也说明同 rangeBin 多目标耦合会污染单 rangeBin 相位。
4. 本文吸收已有 conversion factor 标定思想，但将其适用对象从 rangeBin 改为 range-angle target，并进一步讨论角度接近散射簇可等效为一个 target 的条件。
5. 本文还把转换系数稳定性作为 target 质量检查或后续多目标融合权重/测量噪声的依据，而不是在前置 target selection 阶段依赖完整解缠和 beta 估计。

## 3. 建议引用的文献群

请从以下文献群中选择最相关的 10-18 篇引用。不要全部硬塞，优先保证论证链完整。

### A. 结构位移监测、LoS 修正和传感器融合背景

- `Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
- `Data fusion approaches for structural health monitoring and system identification Past, present, and future.pdf`
- `Bridge Displacement Estimation Using a Co-Located Acceleration and Strain.pdf`
- `Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric.pdf`
- `Real-time strong-motion broadband displacements from collocated GPS and accelerometers..pdf`

### B. 雷达结构位移、direction conversion factor 和倒挂式安装

- `Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
- `Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
- `Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
- `Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf`
- `Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf`
- `FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf`
- `Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf`

### C. Range-angle 相位、同 rangeBin 混合和全场/多目标微振

- `ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
- `ref_papers/01_AoA/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
- `ref_papers/01_AoA/Full-field 3D displacement measurement via microwave sensing.pdf`
- `ref_papers/01_AoA/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`
- `ref_papers/01_AoA/Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf`
- `ref_papers/01_AoA/Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`

### D. 相位缠绕、局部连续相位和预测辅助校正

- `Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf`
- `A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf`
- `Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf`
- `Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`

### E. 目标分离、低通道 AoA 和复数 slow-time 输出支撑

- `ref_papers/01_AoA/TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`
- `ref_papers/01_AoA/Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`
- `ref_papers/01_AoA/Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`
- `ref_papers/01_AoA/Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf`
- `ref_papers/01_AoA/Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf`

## 4. 综述结构要求

请写 1200-1800 字左右的中文文献综述，可分为 4-6 个自然段，不要写小标题也可以；如果使用小标题，最多 3 个。

推荐结构如下：

第一段：从结构位移监测中“传感器测量方向”和“结构真实响应方向”不完全一致的问题切入。说明雷达、视觉、GNSS、加速度/应变等都涉及坐标转换、安装几何或频带互补；其中雷达相位测得的是 LoS displacement，必须转换到结构振动方向。

第二段：介绍已有雷达结构位移研究中的 direction conversion factor。说明 Ma 等人及后续低成本系统如何利用共址加速度、初始标定窗口、目标选择和加速度参考位移来估计 beta，并将 radar LoS 位移与加速度高频/低频融合；指出这些工作证明了倒挂式安装和环境 target 的可行性。

第三段：介绍 rangeBin 层面转换因子的潜在问题。结合 mmVib 的 IQ 复数相位模型、mmWBat/mmSHM 的 range-angle phase tracking，以及 same rangeBin 多目标/全场振动测量文献，说明自然环境中一个 rangeBin 可能含有多个角度散射体；其总相位是多个相量叠加，不一定对应单一 LoS 几何方向，因此基于 rangeBin 相位拟合得到的 beta 可能是混合等效系数。

第四段：介绍 range-angle target 和几何投影关系。说明 MIMO-FMCW 可以通过 Angle FFT/DBF/Capon/LCMV 等方法在 angle 维隔离同 rangeBin 目标，并输出复数 slow-time 序列；full-field/3D microwave sensing 文献说明 LOS 位移可通过几何关系转换到结构坐标，启发本文用 AoA/几何关系给 beta 初值，再用局部连续相位和加速度参考进行校正。

第五段：介绍相位缠绕和局部连续相位问题。说明直接用 wrapped phase 估计 beta 会被 `2π` 分支跳变污染；已有 radar-only、多 chirp、Doppler、acceleration-aided 和 Kalman 方法都在解决相位连续性。本文不要求在 target selection 阶段完成全时程解缠，而是在 target 通过筛选后，使用初始小位移无绕转窗口、短窗口局部解缠或 Kalman 预测辅助校正相位来更新 beta。

第六段：引出本文创新点。写明本文吸收了哪些做法：吸收已有 direction conversion factor 标定、AoA/range-angle phase tracking、full-field 几何 LoS 修正和预测辅助相位校正；在本文倒挂式自然散射场景下进一步提出 range-angle target 级转换系数与等效稳定性分析。强调角度可分则拆分并分别估计 beta；角度接近且无法可靠分开则作为等效 target；若散射体投影系数接近或单一散射体主导，等效 beta 稳定；若多强散射体投影差异大且相对相位随位移变化，beta 应被判为不稳定并降权或剔除。

## 5. 关键表述边界

写作时请注意这些边界，避免说错：

1. 不要说本文“首次提出方向转换系数”或“首次利用加速度标定 beta”。Ma 等人已有相关工作。
2. 不要把 beta 简单等同于 AoA。beta 是 LoS 位移到结构振动方向位移的比例关系；AoA/几何角可以给 beta 初值或约束，但 beta 也可能是复合散射簇的等效转换系数。
3. 不要把 range-angle target 说成一定是单个物理点。它可以是单 angleBin，也可以是角度接近、物理上可等效的 angle cluster。
4. 不要说只要做了 Angle FFT 就能完全解决混合散射。角分辨率受虚拟阵列孔径、SNR、旁瓣、相干散射和通道标定限制；角度不可分时仍可能需要等效 target 或降权。
5. 不要在 target selection 阶段依赖完整相位解缠或 beta。本文的 target selection 保持 unwrap-free / beta-free；转换系数估计发生在 target 通过筛选之后。
6. 不要直接用 wrapped phase 做 beta 拟合，除非明确是在小位移无绕转窗口。一般应使用局部连续相位或预测辅助校正相位。
7. 不要把多 target 写成多个结构测点。本文讨论的是同一结构测点位移在多个环境静止散射方向上的参考观测和转换关系。
8. 不要夸大等效转换系数稳定性。它成立的条件是散射体投影系数接近、单一散射体占主导，或结构位移幅值不足以引起明显相对相位变化。

## 6. 输出格式

请按以下格式输出：

### 文献综述正文

直接给出可放入论文的中文正文。正文中使用 `[1]` 这种顺序编码引用。

### 参考文献

按正文首次出现顺序列出 GB/T 7714 风格参考文献。示例格式：

`[1] 作者. 题名[J]. 期刊名, 年份, 卷(期): 页码或文章号.`

会议论文可写：

`[n] 作者. 题名[C]//会议名. 出版地: 出版者, 年份: 页码.`

技术报告/应用报告可写：

`[n] 作者或机构. 题名[R]. 出版地: 出版者或机构, 年份.`

如果 PDF 信息不足，请在参考文献条目后用括号注明“页码信息未在本地文件中确认”，不要编造页码。

### 自检清单

最后用 5-8 条列出你已检查的事项，包括：

- 是否只使用了 `ref_papers` 中的文献；
- 正文引用和文末条目是否一一对应；
- 是否按 GB/T 7714 风格整理；
- 是否覆盖 LoS 位移转换、direction conversion factor、倒挂式环境 target、range-angle target、同 rangeBin 混合散射、局部连续相位和等效 beta 稳定性；
- 是否避免把本文贡献夸大成已有工作的首次提出。
