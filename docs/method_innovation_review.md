# 本地文献的方法论创新审查

## 审查范围

本审查把当前项目中的论文分成三组：

- 原有本地全文中，与本次 2023—2026 清单直接对应的 14 篇；
- 本次补下载并核验为 PDF 的 9 篇；
- 本地较早的基础文献，作为方法来源和对照，不把它们冒充为近三年成果。

“创新”按方法论判断，不按论文标题判断。这里区分四种层次：

1. **核心算法创新**：改变观测模型、相位恢复、噪声抑制或状态估计方法；
2. **方法组合创新**：把已有算法组合成一个能处理新工况的完整流程；
3. **系统/采集创新**：硬件、小型化、边缘计算、自动标定和现场部署；
4. **应用验证**：把已有方法用于新的桥梁、磁浮或荷载试验，算法本身变化较小。

## 原有本地全文中的方法创新

| 文献 | 实际方法 | 创新层次 | 与当前项目的关系 |
|---|---|---|---|
| *FMCW Radar for Noncontact Bridge Structure Displacement Estimation* | FMCW 相位位移提取；用倾角计修正雷达高程/布设引起的几何误差；支持多点检测 | 方法组合/系统 | 说明 LOS 投影和安装几何必须处理，但目标是固定雷达观测桥梁，不是倒挂雷达观测环境反射体 |
| *Structural displacement estimation using accelerometer and FMCW millimeter wave radar* | 雷达与加速度计共址；自动从多个反射体中选择 best target；估计转换因子；FIR 融合雷达低频和加速度高频 | **较强的方法组合创新** | 是当前项目最直接的前序。当前项目把单 best target 推向多个目标、AoA 几何和共同结构相位 |
| *Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer* | 多个 good target；目标遮挡检测；雷达可用、雷达全遮挡、目标恢复三个阶段切换；应变 ANN 补低频、加速度补高频 | **较强的方法组合创新** | 给出连续监测和遮挡管理的先例，但当前项目没有实现在线 tracker、遮挡切换或应变支路 |
| *Development and field deployment validation of a low-cost and high-precision displacement sensing system...* | 自动初始校准；60 GHz 雷达 + ADXL355 + Raspberry Pi；内置相位解缠和互补 FIR；多桥现场验证 | 系统/工程创新 | 证明雷达—加速度融合可低成本部署；硬件边缘计算不是当前算法的理论创新 |
| *Transversal Displacement Detection of an Arched Bridge with a Multimonostatic MIMO Radar* | 多站位/多单站几何；由多个 LOS 观测反演水平、竖向位移；给出几何不确定度 | **几何方法创新** | 支持“多方向投影”思想，但它依赖多个雷达站位，不能直接等同于当前单雷达多环境目标 |
| *Accelerometer-aided millimeter-wave radar interferometry... target occlusion* | 多目标转换因子；遮挡检测和目标切换；加速度辅助相位解缠；遮挡后漂移修正 | **较强的方法组合创新** | 是当前项目最接近的连续监测基线，但仍以物理结构目标和短时校准为前提 |
| *Development of a high-precision nano millimeter-wave radar system...* | 均值消除 + Hamming 窗目标指示；all-phase FFT 提升相位/频率估计；相位干涉得到桥梁位移 | 中等，偏系统信号处理 | 可借鉴静态回波消除和 ap-FFT；没有解决倒挂雷达的参考目标管理 |
| *Vibration response analysis of simply supported girder bridges...* | 雷达动态挠度、模态分析、车辆—桥梁多点接触模型、冲击系数计算 | 应用验证 | 算法创新较弱，适合作为频率和动态挠度的验证场景 |
| *Experimental Analysis of Accuracy and Precision...* | 静态 loopback/waveguide 相位测试；振动台动态测试；把相位误差换算为微米级位移误差 | 计量/硬件评估 | 说明硬件相位精度通常不是唯一瓶颈，当前重点应放在 target 稳定性、叠加散射和解缠 |
| *A novel Doppler-based phase unwrapping algorithm...* | 从 MIMO range-angle-Doppler 结果估计目标 Doppler；用 Doppler 预测下一时刻相位并迭代解缠 | **核心算法创新** | 属于位移恢复阶段的强基线；当前项目不应宣称重新发明 Doppler 解缠 |
| *Accurate structural displacement measurement... multi-chirp-based adaptive phase unwrapping* | 用多个 chirp 估计相位变化率；对变化率解缠；预测下一时刻相位区间，再恢复主 chirp 连续相位 | **核心算法创新** | 与当前 chirp/frame 讨论直接相关；它是 radar-only 解缠，当前项目实际使用的是加速度预测和 Kalman |
| *Acceleration-aided Kalman filtering for joint phase denoising and unwrapping...* | 把相位和相位变化率建成状态；加速度参与预测；Kalman 同时完成降噪和 2π 分支修正；自适应 Q、R 和收敛时间 | **核心算法创新，当前最直接基线** | 当前项目的结构主相位 Kalman 与它有明显重合；当前项目新增的可辩护部分只能放在多目标共同结构相位和 target-wise 观测权重 |
| *Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW radar* | 雷达提供低频位移信息，MEMS 提供高频加速度；滑动窗口 FIR 互补滤波重构加速度 | 方法组合创新 | 当前项目使用加速度做相位预测，但没有把雷达位移二阶微分后再反向改善加速度 |
| *Structural Displacement Estimation of Rail Bridges Through...* | 60 GHz 雷达 + 三轴 MEMS；自动 target 选择；加速度辅助解缠；FIR 融合；再接入非专用分布式光纤 | 系统/方法组合创新 | 是近期铁路桥现场基线；总体仍是既有 radar+accelerometer 路线的工程化扩展 |

## 本次新增全文中的方法创新

| 文献 | 实际方法 | 创新层次 | 与当前项目的关系 |
|---|---|---|---|
| *Real-Time Malfunction Detection of Maglev Suspension Controllers* | SST 定位每个悬浮控制器通过时段；用幅值、主频和车速构造速度归一化 FI；Bayesian Dynamic Linear Model 实时报警 | 中等，面向故障诊断 | 可借鉴时段切分和概率判别，但不是位移估计主线 |
| *Periodic-Filtering Method for Low-SNR Vibration Radar Signal* | 先在 Doppler 域估计振动频率，再按周期做梳状平均；圆拟合估计静态杂波；差分相位反演位移 | **明确的核心算法创新** | 与当前 IQ/相位前端最相关。优点是低 SNR 下不要求传统低通过采样；限制是依赖近似单频、周期稳定 |
| *Measurement Refinements of Ground-Based Radar Interferometry in Bridge Load Test Monitoring* | 相位跳变检测与恢复；把目标自身变形纳入精确 LOS 投影；保留慢变趋势 | **几何与相位处理创新** | 直接提醒当前项目不能只用固定投影系数解释所有慢趋势；但地基大雷达场景与倒挂小雷达不同 |
| *Analysis of bridge dynamic load test based on millimeter wave radar* | 雷达动态挠度时程、频谱和模态频率；计算动态冲击系数 | 应用验证 | 主要贡献是把雷达输出接入荷载试验评价，算法创新较弱 |
| *Research on Modal Identification of High-Speed Maglev Guideway Structure Based on Data Fusion and Genetic Algorithm* | 遗传算法优化有限传感器布置；EIKF 重构响应；NExT-ERA 识别导轨梁模态 | 中高，方法组合创新 | 可借鉴“多源数据—统一响应—模态输出”的验证层次，但不是雷达相位主线 |
| *Online Monitoring System for Short Stator Maglev Train* | 同步采集车体、悬浮间隙、电磁铁电流、轨道梁加速度、应变和位移；按线路区段分析异常 | 系统工程创新 | 可借鉴采集包字段和同步设计；不应把系统监控层引入离线算法 |
| *Technology Innovation in Developing the Health Monitoring Cloud Platform...* | 车载/轨旁/桥梁 200 余个传感器；同步、清洗、重采样、云计算、虚拟传感器和可视化 | 平台工程创新 | 对当前学术算法本身创新很弱；当前代码边界明确排除云平台和服务层 |
| *Portable Radar-Based Measurement System for Vibration Analysis of Large Infrastructures* | IWR6843ISK + DCA1000EVM；LVDS/UDP 读取 IQ；Range FFT 选主距离单元；多天线去静态向量；解缠和位移换算 | 系统/流程创新 | 与当前采集链路高度相似，但 Range FFT、静态向量消除和普通 unwrap 都不是当前算法的核心新意 |
| *Using Geometrical Information to Measure the Vibration of a Swaying Millimeter-wave Radar* | 用参考几何体的平面面积差/空间体积差估计雷达自身摆动，不用 IMU 或第二雷达 | 中等，特殊场景方法 | 可作为雷达自运动补偿的未来参考；当前项目尚未做平台自运动估计 |

## 尚未保存为本地 PDF、但需要纳入方法比较的 DeepVib

*Contactless Micron-Level Vibration Measurement with Millimeter Wave Radar* 提出 DeepVib：先用信号处理提取目标反射，再用神经网络抑制噪声，最后用几何方法消除静态反射。其公开摘要报告微米级测量和小于 100 μm 振幅下的误差改善。它的核心创新是“物理信号处理 + 学习型去噪”，不属于当前项目的直接路线，因为当前项目要求数组、方程和显式滤波流程可解释，不准备引入训练数据依赖。

公开全文入口：[DeepVib 论文页面](https://www.nowpublishers.com/article/OpenAccessDownload/SIP-2023-0073)。当前没有把错误的 `mmSafe` PDF 作为该论文收录文件。

## 本地较早基础文献的作用

- *Measuring Micrometer-Level Vibrations With mmWave Radar*：VSNR、IQ 圆拟合、Multi-Signal Consolidation、多 chirp/多天线组合，是微振测量的重要信号模型前序。它已经把“多 chirp 提升有效 SNR”和“多天线分离目标”讲得很清楚。
- *A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring*：多目标距离单元、相位测位移和硬件相位异步误差，是较早的 FMCW 结构位移基础。
- *Solving Phase Ambiguity in Interferometric Displacement Measurement With Millimeter-Wave FMCW Radar Sensors*：在 slow time 构造等效 I/Q，把线性相位解调迁移到单通道 FMCW，是大位移解缠的前序。
- *Radar Sensing of Displacement Motions With High Robustness Against Additive Noise*：分析加性噪声如何破坏 I/Q 反正切相位，支撑用 IQ 轨迹质量和 SNR 做 target 质量判据。
- `Approaches to Adaptive Filtering`、`Adaptive Kalman Filtering for INS GPS`、`Adaptive Adjustment of Noise Covariance...`、`Bridge Displacement Estimation Using a Co-Located Acceleration and Strain` 等自适应滤波文献，主要提供 Q/R、innovation、residual 和 covariance matching 的方法依据，本身不是毫米波雷达创新。

## 与当前代码的对照结论

当前代码实际链路是：

```text
capture package
→ Range FFT / angle processing
→ 记录级距离—角度候选
→ 局部 MUSIC + 最小二乘 AoA
→ beta_i = 1 / |cos(theta_i)|，整段冻结
→ native-time ADXL 区间预积分
→ 加速度预测的 wrapped-phase 分支修正
→ 多目标加权观测
→ 共享结构主相位 Kalman
→ q_hat 位移
```

因此，当前项目最可辩护的研究增量不是“提出了新的通用相位解缠算法”，而是：

1. **无需离线角度转换因子的加速度辅助 Kalman 解缠**：前序 acceleration-aided Kalman 方法先用一段离线同步数据估计雷达 LOS 位移到结构位移的方向转换因子，再进入在线解缠和滤波；当前算法从当前记录的距离—角度观测中直接估计每个 target 的 AoA，并在线形成 `beta_i`，再把它写入 Kalman 观测模型。因此不需要先激励结构、积分加速度、拟合转换因子，再开始正式测量，方法可以按“采集—运行”直接使用。当前代码仍需要正确的阵列几何、载频和安装方向配置，但不需要现场专门的位移转换标定阶段；
2. **倒挂式运动雷达下的多环境反射目标共同观测**：把多个环境 target 视为同一个结构位移的不同投影观测，而不是把 target 当成独立结构测点；
3. **AoA 驱动的 target-specific 几何统一**：用每个 target 的 AoA 形成 `beta_i`，把多目标 LoS 相位统一到共同结构主相位；`1/|cos(theta)|` 公式本身不是新公式，创新在于它被用于当前这种多目标、运动雷达、共同状态观测；
4. **异步时间轴上的加速度区间预积分**：直接在原生 ADXL 时间戳上积分到相邻雷达时刻，避免把加速度简单重采样后当作同步数据；这使“安装即用”不依赖额外的离线对时和转换因子估计，但单独作为理论创新仍需通过消融实验支撑；
5. **共同结构相位状态与 target-wise 观测权重**：多个 target 先经过预测校正，再以观测方差合成为一个结构相位观测，代码还按后验残差更新各 target 的测量方差。这是当前算法与单 target FIR、单 target Kalman 的主要差异，但需要实验消融才能证明有效。

### 相位解缠创新的准确表述

当前创新不是把 `unwrap` 函数换成另一种 `unwrap` 函数，而是改变 acceleration-aided Kalman 的使用方式：

```text
前序方法：
离线同步采集 → 加速度积分/雷达相位带通 → 拟合方向转换因子 → 在线相位解缠

当前方法：
当前记录的 Range-Angle 观测 → AoA → beta_i
                         ↘ 加速度原生时间区间预积分 → 在线 Kalman 预测
雷达 wrapped phase + beta_i → 预测相位校正分支 → 多 target 共同结构相位
```

因此论文中应把贡献写成“基于在线 AoA 几何观测的免离线方向转换因子 acceleration-aided Kalman 相位解缠”，而不是写成“完全不需要标定”。阵列位置、载频、波长、安装方向和角度定义仍属于传感器配置条件。

### 多目标、多方向和多传感器融合的创新边界

- **多目标**：当前代码从 range-angle cube 检测多个候选峰，对同一距离单元用局部 MUSIC/最小二乘细化 AoA；每个 target 保留自己的 wrapped phase、角度和 `beta_i`，再由共同 Kalman 状态融合。已有工作通常选择一个 best target，或用多个 target 管理遮挡；当前差异在于多个 target 同时作为共同结构状态的观测，而不是只做目标切换。
- **多方向**：不同 target 的 AoA 产生不同 LOS 投影系数，当前模型把它们统一到一个结构主相位。它是“多方向投影统一”，不是完整三维位姿估计；当前代码没有估计结构转角、横向分量或完整姿态，因此不能宣称 3D 几何标定。
- **多传感器**：雷达提供带几何关系的 wrapped phase 观测，ADXL 提供原生时间轴上的位移增量和速度增量，用于 Kalman 预测；这和已有雷达低频 + 加速度高频 FIR 融合不同，当前重点是“加速度预测解缠 + 多 target 雷达观测更新”。
- **系统**：标准 capture package 使真实采集和半实测桥梁驱动场景输出同一种算法输入，算法不依赖采集硬件生命周期；再加上在线 AoA 生成 `beta_i`，系统不需要针对每个安装点保存一份离线转换因子。这是可重复实验和快速部署价值，属于系统/工程化贡献，不应冒充新的物理公式。

## 不能直接宣称为当前创新的内容

- Range FFT、角度 FFT、MUSIC、最小二乘 AoA 本身都是成熟工具；
- 相位与位移的基本关系、普通 `unwrap`、预测加减 `2π`、标准 Kalman 都不是新算法；
- 固定 `beta_i = 1/|cos(theta_i)|` 是简化几何模型，不等于完整三维姿态标定；
- 当前代码没有在线新增/删除/重关联 target，也没有完整遮挡管理；
- 当前代码没有实现 multi-chirp 自适应解缠、Doppler 解缠、周期滤波、DeepVib 学习型去噪或多雷达三维反演；
- Raspberry Pi、DCA、UDP、边缘输出属于采集/系统实现，不应写成算法理论创新。

## 当前项目最合适的创新定位

建议把论文主方法定位为：

> **面向高刚度磁浮轨道梁的倒挂式 FMCW 雷达多目标 AoA 几何统一与加速度辅助共同结构相位估计方法。**

这个定位避开了已经较成熟的“再提出一种相位解缠算法”，把贡献集中到当前文献相对少处理的组合：雷达随结构运动、环境静止散射体、多目标投影不一致、异步加速度输入和共同结构状态估计。

## 必须做的创新性消融

为了让上述定位成立，实验至少需要比较：

1. 单 target 与多 target；
2. 固定 `beta=1` 与 AoA-derived `beta_i`；
3. 所有 target 等权与 target-wise 自适应 `R_i`；
4. 简单重采样加速度与 native-time 区间预积分；
5. 共享结构主相位 Kalman 与单 target 独立滤波；
6. 普通相位分支修正与 B05 周期滤波、B10 相位跳变处理、multi-chirp/Doppler 解缠基线。

只有这些对照能显示多目标几何统一和共同状态估计确实降低误差，当前代码才具有清晰的方法学创新，而不只是已有雷达—加速度流程在磁浮场景中的迁移。
