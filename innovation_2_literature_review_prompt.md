# Prompt：第二个创新点文献综述写作

你是一名熟悉结构健康监测、毫米波 FMCW/MIMO 雷达、range-angle 处理、微振相位测量和在线目标管理的博士论文写作助手。请基于本地 `ref_papers/` 中的文献，为论文“第二个创新点：基于距离-角度联合维度的在线参考目标选取方法”撰写一段中文文献综述/研究现状。

## 0. 阅读范围与硬性约束

1. 只能使用本地 `ref_papers/` 中的文献，不要联网，不要编造不存在的论文。
2. 优先阅读 `ref_papers/00_primary_references/`、`ref_papers/01_AoA/` 及其 README；必要时再使用 `ref_papers/` 根目录中的目标跟踪、数据融合、结构位移监测文献。
3. 正文必须使用顺序编码引用，如 `[1]`、`[2]`、`[3]`。不要使用 `(Xiong et al., 2021)`、`[Xiong2021]` 或脚注式引用。
4. 文末必须给出“参考文献”列表，并按正文首次出现顺序编号。格式采用 GB/T 7714 风格，例如：
   `[1] XIONG Y, LI S, GU C, et al. Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View[J]. Research, 2021, 2021: 9787484.`
5. 每一个正文引用都必须能在文末找到对应条目；文末每一条也必须在正文中出现。
6. 引用信息必须从 PDF 首页、文末 References、DOI 页或已有摘要卡片中核对。作者、题名、期刊/会议、年份、卷期、页码/文章号尽量完整；无法确认页码时可省略页码，但不要编造。
7. 不要堆砌论文清单。综述要体现“已有结构位移雷达 target 选择的问题 -> range-angle 处理为何必要 -> 低通道 MIMO-FMCW 中可行的相位提取链路 -> 在线确认和结构频带筛选 -> 本文如何吸收并改造”。
8. 不要写成算法说明书。最后一段可以自然引出本文方法，但正文主体要保持文献综述/研究现状风格。

## 1. 先阅读这些高水平论文/材料的写法

请先打开并快速阅读以下文献的 Introduction / Related Work / Method Overview / Research Background 部分，学习它们如何组织研究现状：

1. `ref_papers/00_primary_references/Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
   - 学习写法：先从结构位移监测需求和传感器局限展开，再归纳非接触测量和多传感融合趋势。
2. `ref_papers/00_primary_references/Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
   - 学习写法：先说明毫米波相位感知微小振动的优势，再指出多径、噪声、IQ 几何和多目标分离问题。
3. `ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
   - 学习写法：从微动/振动全场测量需求出发，说明 range-angle joint dimension 中可以保留并提取 interferometric phase evolution。
4. `ref_papers/01_AoA/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
   - 学习写法：重点看它如何指出传统单 range bin 相位跟踪在同 rangeBin 多目标耦合、相邻 rangeBin 干扰和大位移跨 bin 时会失效，并如何转向 range-angle joint phase tracking。
5. `ref_papers/01_AoA/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`
   - 学习写法：看同一 range bin 内多个目标如何通过角度维分离，并从各自方向提取相位/位移序列。
6. `ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
   - 学习写法：看长期监测中 target occlusion 和多 good targets 的问题如何被引出。
7. `ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
   - 学习写法：看自动 target 选择、自动校准、低成本系统部署如何写进研究现状。

综述整体应先宽后窄：从结构位移监测和毫米波雷达相位测量，收束到自然环境参考 target 的在线选择，再聚焦到 range-angle target extraction。

## 2. 本文第二个创新点的核心内容

本文研究的是倒挂式毫米波雷达结构位移监测：雷达固定在结构测点上并随结构共同运动，视场内的地面、桥下构件、支架等静止散射体因雷达自身运动产生相位变化，可作为结构位移恢复的参考 target。

已有研究通常先从 range spectrum 中选择一个或多个强反射 target，再估计方向转换系数并恢复结构位移。该思路在单一散射体主导时有效，但自然反射环境中一个 rangeBin 可能包含多个不同角度的散射体，直接追踪 rangeBin 总相位会带来相位混叠、IQ 轨迹畸变和转换系数不稳定。

第二个创新点不是重新提出 MIMO 雷达 AoA，也不是普通多目标检测，而是：

> 将参考目标的基本单元从 rangeBin 升级为 range-angle bin 或 angle cluster，构建在线参考 target 选择流程。方法先保留复数 range-angle map，再在距离-角度二维幅值图中发现候选峰；对同一 rangeBin 内角度接近的 peaks 进行合并，形成 `T=(b,C)` 的 range-angle reference target；通过滑动窗口出现率确认 target 稳定性；再利用加速度识别结构振动频带，并用 target 的中心化复数 slow-time 频谱能量占比判断其是否主要由结构运动驱动。目标选择阶段不依赖相位解缠和转换系数，输出可进入后续转换系数估计与 Kalman 融合的复数 slow-time 序列。

要写清楚它和已有工作的关系：

1. mmVib/mmWBat/mmSHM 等工作证明毫米波雷达可以从复数相位中提取微动/振动，并且 range-angle joint component 的 phase evolution 可用于多目标或全场振动测量。
2. 低通道 MIMO-FMCW 雷达已有 Range FFT + Angle FFT/DBF/Capon/LCMV 等链路，可在同一 rangeBin 内分离角度不同的目标，并输出可做相位跟踪的 complex slow-time signal。
3. Ma/Zhanxiong/Sohn 系列结构位移监测论文已有自动 target 选择、转换因子标定、target occlusion 检测和多 good targets 管理，但多数仍以 range target 或 best target 为基本对象。
4. 多目标跟踪中的 M-out-of-N/candidate confirmation 思想可借鉴为“候选参考 target 在滑动窗口内稳定出现”的确认机制，但本文不做完整运动目标跟踪。
5. 加速度频谱在已有文献中用于确定结构主频和滤波频带；本文将其改造为 target selection 阶段的结构频带先验，用于判断候选 IQ 变化是否由结构振动驱动。

## 3. 建议引用的文献群

请从以下文献群中选择最相关的 10-18 篇引用。不要全部硬塞，优先保证论证链完整。

### A. 结构位移监测与毫米波雷达背景

- `Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
- `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
- `Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf`
- `A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf`
- `Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf`

### B. 倒挂式雷达、环境参考 target、自动 target 选择

- `Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
- `Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
- `Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
- `Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf`
- `Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf`

### C. Range-angle phase tracking 和全场/多目标振动测量

- `ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
- `ref_papers/01_AoA/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
- `ref_papers/01_AoA/Full-field 3D displacement measurement via microwave sensing.pdf`
- `ref_papers/01_AoA/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`
- `ref_papers/01_AoA/Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf`
- `ref_papers/01_AoA/Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`
- `ref_papers/01_AoA/A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf`

### D. AoA / MIMO-FMCW / 低通道分离方法支撑

- `ref_papers/01_AoA/TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`
- `ref_papers/01_AoA/Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`
- `ref_papers/01_AoA/Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`
- `ref_papers/01_AoA/Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf`
- `ref_papers/01_AoA/Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf`
- `ref_papers/01_AoA/Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf`

### E. 目标管理、窗口确认和异常/动态干扰

- `Multiple-target tracking and track management for an FMCW radar network.pdf`
- `ref_papers/01_AoA/Variational Signal Separation for Automotive Radar Interference Mitigation .pdf`
- `ref_papers/01_AoA/Millimeter_Wave_Real-Time_Tracking_and_Imaging_of_Moving_Objects_Based_on_Virtual_MIMO_Array_and_State_Vector_Prediction.pdf`

## 4. 综述结构要求

请写 1200-1800 字左右的中文文献综述，可分为 4-6 个自然段，不要写小标题也可以；如果使用小标题，最多 3 个。

推荐结构如下：

第一段：从结构位移/振动监测需求出发，说明非接触毫米波雷达的优势，但也指出实际结构场景中 target 识别、LOS 转换、多路径/杂波和长期稳定性是影响位移恢复的关键问题。

第二段：介绍已有毫米波雷达位移/振动测量的相位基础。重点写 mmVib 等工作如何利用相位-距离关系、IQ 圆弧和多信号合并实现高精度微振测量；随后指出固定雷达观测振动物体和倒挂式雷达观测静止环境 target 在 target 定义上不同。

第三段：介绍 range-angle joint phase tracking。说明 mmWBat、mmSHM、多人生命体征/多目标相位提取等文献已经证明，在 MIMO-FMCW 数据中，目标不仅可按 range 区分，也可在 angle 维度隔离；选定 range-angle component 后可保留复数 slow-time 相位序列。强调这些工作为“从 rangeBin target 升级到 range-angle target”提供依据。

第四段：介绍已有结构位移监测中的 target selection 和 target occlusion 处理。说明 Ma 等人使用环境 target、自动选择 best target、估计 direction conversion factor，并在后续研究中考虑多 good targets、遮挡检测、目标切换和低成本现场系统；但这些方法多以 range spectrum 中的目标或单 best target 为核心，对同一 rangeBin 内角度不同散射体导致的混合相位关注不足。

第五段：介绍在线稳定性确认和结构频带一致性。可引用 M-out-of-N/candidate track confirmation 说明“候选目标需要在窗口内稳定出现”；再引用 Ma 等人用加速度频谱确定结构主频/滤波频带的做法，说明本文将该信息改造成 target IQ 频谱筛选先验。

第六段：引出本文创新点。写明本文吸收了哪些做法：吸收 mmWBat/mmSHM 的 range-angle phase tracking，吸收低通道 MIMO-FMCW 的 Angle FFT/DBF/Capon/LCMV 复数 slow-time 输出思想，吸收目标管理中的窗口确认思想，吸收雷达+加速度结构监测中的结构主频先验。在本文倒挂式场景下改造为：基于复数 range-angle map 的在线参考 target 选择；同 rangeBin 内角度可分则拆分、角度接近则合并为等效 target；目标选择不依赖相位解缠和转换系数，只输出稳定且结构频带一致的复数相位观测。

## 5. 关键表述边界

写作时请注意这些边界，避免说错：

1. 不要说本文“首次提出 MIMO-FMCW range-angle 处理”或“首次做 AoA”。已有大量 MIMO/AoA/beamforming 文献。
2. 不要把生命体征多人分离文献直接说成结构位移监测实证。可以说它们证明了低通道 MIMO-FMCW 在同 rangeBin 目标角度分离和相位 slow-time 提取上的可行性。
3. 不要把 range-angle target 等同于必然唯一的物理散射点。它可以是单个 angleBin，也可以是角度接近的 angle cluster 或等效散射簇。
4. 不要说 Angle FFT zero-padding 提高了真实角分辨率。zero-padding 只是细化角度网格，真实分辨率仍受虚拟阵列孔径限制。
5. 不要写成 target selection 依赖完整相位解缠或已知转换系数。本文目标选择阶段是 unwrap-free / beta-free，只使用幅值、出现率、复数 IQ 频谱和加速度结构频带先验。
6. 不要把“多 target”写成多个结构测点的多点监测。本文多 target 是同一结构测点位移在多个环境静止反射方向上的候选参考观测。
7. 不要把超分辨 AoA、SBL、Transformer 等方法写成本文必用主链路。可写为候选/对照/离线分离上限，主链路优先是稳定输出复数 slow-time 的 Range FFT + Angle FFT/DBF/Capon/LCMV。

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
- 是否覆盖结构位移监测、毫米波相位测量、range-angle phase tracking、低通道 MIMO-FMCW、target selection、窗口确认和结构频带一致性；
- 是否避免把本文贡献夸大成已有工作的首次提出。
