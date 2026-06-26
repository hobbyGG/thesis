### 文献综述正文

结构位移是桥梁、建筑等土木基础设施状态评估中的关键响应量，但传感器测得的方向、坐标和安装几何往往不等同于结构真实响应方向。已有综述指出，LVDT、加速度、应变、GNSS、视觉、雷达和 LiDAR 等技术在采样频率、低频稳定性、视场、遮挡、供电通信和长期部署方面各有约束，多传感融合常用于弥补单一传感器在低频漂移、采样率、精度或环境鲁棒性上的不足[1]。在这一背景下，雷达位移测量的关键特点是相位变化首先对应散射体沿雷达视线方向的距离变化，即 LoS displacement；当工程上关注的是桥梁竖向、横向或某一主振动方向位移时，就必须把 LoS 位移转换到结构坐标方向。对于本文关注的倒挂式毫米波雷达，雷达与加速度计共同固定在结构测点并随结构运动，周围环境中的静止散射体成为参考 target。此时雷达相位并不是直接给出结构振动方向位移，而是给出结构测点运动在不同散射方向上的投影，因此 direction conversion factor 或几何投影系数是从雷达相位走向结构位移的必要环节[2]。

Ma、Choi、Sohn 等人的系列工作已经较系统地处理了倒挂式环境 target 和转换因子标定问题。其早期研究将 FMCW 毫米波雷达和加速度计共址安装在结构测点，通过短时同步数据从多个环境反射目标中选择与加速度积分位移最一致的 target，并估计 LoS 到实际振动方向的转换因子，再用互补滤波融合雷达低频位移和加速度高频响应[2]。后续研究进一步面向长期桥梁监测中的 target occlusion，在初始标定中选择多个 good targets 并估计各自转换因子，运行阶段结合遮挡检测、target 切换和应变-加速度替代观测维持连续位移估计[3]；低成本系统研究又把有效标定时段识别、best target 选择和转换因子估计集成到边缘设备中，证明该思路具备工程部署潜力[4]。针对车辆等移动物体造成的间歇遮挡，相关工作还发展了多 target 相位解缠和遮挡恢复策略[5]。这些研究说明，利用环境 target 和加速度参考自动估计 direction conversion factor 已是已有工作的重要基础，而本文不能也不应把 beta 的概念本身作为首次贡献。与此同时，这些方法通常仍以 rangeBin 或选中 target 的相位序列为基本观测对象，隐含该相位可近似代表一个稳定 LoS 几何方向，或至少由单一主散射体主导。

在自然反射环境中，这一 rangeBin 层面的假设并不总是可靠。毫米波微振测量研究从 IQ 复平面说明，目标微位移可通过复数相位演化恢复，但多径、静态背景和邻近散射体会使接收信号成为多个复相量叠加，弱小振动引起的相位变化可能被混合回波扭曲[6]。mmWBat 将微动感知从单 range profile 推进到 range-angle joint dimension，利用 range-angle component 的 interferometric phase evolution 实现全视场微动量化[7]。更贴近结构健康监测的 mmSHM 则明确指出，传统 FMCW 方法主要依赖 range profile 区分目标；当多个目标落入同一 range bin，或相邻 range bin 之间存在干扰时，单 range-bin 相位会出现耦合、aliasing 和错误频率成分，range-angle 联合维度有助于隔离不同目标并分别跟踪相位[8]。这意味着，若直接对整个 rangeBin 的总相位拟合 beta，所得系数可能并非某个物理反射点的 LoS 几何投影，而是由多个散射体的幅值、相对相位、角度分布和结构位移共同决定的混合等效系数。该系数可能在某一标定窗口内看似有效，却随时间窗口、散射状态或位移幅值变化而漂移。

Range-angle target 因而提供了更合理的转换系数估计尺度。Full-field 3D microwave sensing 表明，工程上真正关心的是结构坐标系位移，多个 LoS 位移可通过测点位置、雷达视线和坐标转换关系重构为结构坐标系响应，这为用 AoA/几何关系给 beta 或 eta 初值提供了物理依据[9]。在实现层面，MIMO-FMCW 的虚拟阵列、Angle FFT 和数字波束形成提供了角度隔离基础，TI 应用报告给出了 TDM/BPM MIMO、虚拟阵列和角分辨率之间的工程链路[10]。多人生命体征监测文献也提供了直接旁证：即使多个对象位于相同 radial distance，仍可通过 range-azimuth map、beamforming 或 Capon 方法在角度维分离，并对各方向的复数 slow-time signal 提取相位[11][12]；进一步的 MIMO-FMCW 多目标处理还将 range FFT、Capon 角度估计、CFAR/聚类和 LCMV beamforming 串联起来，为每个 target 输出可分析的慢时间相位序列[13]。这些研究支撑本文把转换关系从 rangeBin 推进到 range-angle target，但也提示不能夸大角度处理能力：角分辨率受虚拟阵列孔径、SNR、旁瓣、相干散射、TDM 相位补偿和通道幅相标定限制，Angle FFT 或 beamforming 只能降低混叠，不能保证完全分离任意自然散射体。

转换系数估计还依赖可信的连续相位。毫米波短波长提高了位移灵敏度，也使 wrapped phase 更容易跨越 2π 分支；若直接用包裹相位拟合 beta，分支跳变会被误认为实际位移变化，从而污染转换因子。围绕相位连续性，已有研究提出从单通道 FMCW 的 slow-time 数据合成等效正交 I/Q，从而借鉴 CW 雷达线性相位解调方法解决相位模糊[14]；也有研究利用 MIMO 雷达中的 Doppler 信息预测并校正快速运动目标的相位轨迹[15]。面向结构位移，multi-chirp 自适应解缠方法通过多 chirp 估计相位变化率并预测下一时刻相位范围，在无需额外传感器的情况下恢复大位移连续相位[16]；加速度辅助 Kalman 方法则将相位解缠和降噪统一到状态空间模型中，用预测相位修正 2π 跳变，并在滤波收敛后输出连续相位[17]。这些工作说明，转换系数估计不能建立在未经校正的 wrapped phase 上，也不宜在 target selection 阶段依赖完整全时程解缠结果。更稳妥的策略是先用 unwrap-free、beta-free 的 target 质量指标完成候选筛选，再在通过筛选的 target 上利用初始小位移无绕转窗口、短窗口局部连续相位或 Kalman 预测辅助校正相位递推修正 beta。

基于上述脉络，本文第三个创新点不是重新提出 direction conversion factor，而是把已有 conversion factor 标定思想、AoA/range-angle 相位跟踪、full-field 几何 LoS 修正和预测辅助相位校正结合起来，提出 range-angle target 级转换系数估计与等效稳定性分析。对于角度可分的散射体，本文将其拆分为不同 range-angle target，并分别建立 LoS 到结构振动方向的转换关系；对于角度接近且难以可靠分开的散射簇，则将其作为一个等效 angle cluster，beta 不再解释为单个物理点的几何系数，而是解释为该散射簇在当前观测条件下的等效转换系数。该等效系数的稳定性有明确条件：当 target 内主要散射体的投影系数接近、单一散射体占主导，或结构位移幅值不足以引起明显相对相位变化时，固定 beta 近似合理；当多个强散射体的几何投影差异较大，且相对相位会随结构位移显著变化时，固定 beta 会表现为窗口相关和散射状态相关的漂移。因而，本文将 beta 的几何初值、局部连续相位修正和稳定性检查结合起来，把转换系数稳定性作为 target 质量评价、后续多目标融合权重或测量噪声设置的依据；不稳定 target 应被降权或剔除，而不是被强行纳入固定 beta 的融合框架。

### 参考文献

[1] MA Z, CHOI J, SOHN H. Structural displacement sensing techniques for civil infrastructure: A review[J]. Journal of Infrastructure Intelligence and Resilience, 2023, 2: 100041.

[2] MA Z, CHOI J, YANG L, et al. Structural displacement estimation using accelerometer and FMCW millimeter wave radar[J]. Mechanical Systems and Signal Processing, 2023, 182: 109582.

[3] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.

[4] MA Z, HAN K, CHOI J, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.

[5] MA Z, CHOI J, LEE J, et al. Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion[J]. Mechanical Systems and Signal Processing, 2025, 223: 111888.

[6] GUO J, HE Y, JIANG C, et al. Measuring micrometer-level vibrations with mmWave radar[J]. IEEE Transactions on Mobile Computing, 2023, 22(4): 2248-2261.

[7] XIONG Y, LI S, GU C, et al. Millimeter-wave bat for mapping and quantifying micromotions in full field of view[J]. Research, 2021, 2021: 9787484.

[8] LI S, XIONG Y, SHEN X, et al. Multi-scale and full-field vibration measurement via millimetre-wave sensing[J]. Mechanical Systems and Signal Processing, 2022, 177: 109178.

[9] XIONG Y, GOU Y, TIAN W, et al. Full-field 3D displacement measurement via microwave sensing[J]. Mechanical Systems and Signal Processing, 2025, 234: 112804.

[10] RAO S. MIMO Radar[R]. Dallas: Texas Instruments, 2018.

[11] AHMAD A, ROH J C, WANG D, et al. Vital signs monitoring of multiple people using a FMCW millimeter-wave sensor[C]//2018 IEEE Radar Conference (RadarConf18). Oklahoma City: IEEE, 2018: 1450-1455.

[12] XU Z, SHI C, ZHANG T, et al. Simultaneous monitoring of multiple people's vital sign leveraging a single phased-MIMO radar[J]. IEEE Journal of Electromagnetics, RF, and Microwaves in Medicine and Biology, 2022, 6(3): 311-320.

[13] YANG Y, QU L, YANG Y, et al. Multitarget vital signs detection based on MIMO-FMCW radar[C]//2024 Photonics & Electromagnetics Research Symposium (PIERS). Chengdu: IEEE, 2024. (页码信息未在本地文件中确认)

[14] LIU J, LI Y, GU C. Solving phase ambiguity in interferometric displacement measurement with millimeter-wave FMCW radar sensors[J]. IEEE Sensors Journal, 2022, 22(9): 8482-8489.

[15] GUERZONI G, FAGHAND E, VINCENZI L, et al. A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring[J]. Mechanical Systems and Signal Processing, 2025, 235: 112777.

[16] MA Z, LU H, ZHANG T, et al. Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping[J]. Measurement, 2026, 262: 120029.

[17] MA Z, ZHANG T, ZHU Y, et al. Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring[J]. Mechanical Systems and Signal Processing, 2026, 248: 113991.

### 自检清单

- 已只使用 `/Users/umep/thesis/ref_papers/` 中存在的本地文献及其 README 信息，未联网检索。
- 正文引用 `[1]` 至 `[17]` 均在参考文献中出现，参考文献每条也均在正文中被引用。
- 参考文献按正文首次出现顺序排列，并按 GB/T 7714 风格整理；PIERS 论文页码未能在本地文件中确认，已明确注明。
- 正文覆盖了 LoS 位移转换、direction conversion factor、倒挂式环境 target、range-angle target、同 rangeBin 混合散射、局部连续相位和等效 beta 稳定性。
- 已避免将 direction conversion factor / beta 写成本文首次提出；相关已有工作已归于 Ma、Choi、Sohn 等人的雷达-加速度融合研究。
- 已避免把 beta 简单等同于 AoA；正文将 AoA/几何关系表述为 beta 初值或约束来源。
- 已避免宣称 Angle FFT 或 beamforming 能完全解决混合散射，并说明角分辨率、SNR、旁瓣、相干散射和通道标定限制。
- 已明确 target selection 保持 unwrap-free / beta-free，转换系数估计发生在 target 筛选之后，并依赖局部连续相位或预测辅助校正相位。
