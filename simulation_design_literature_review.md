# 倒挂式毫米波雷达 + 加速度结构位移估计：仿真实验设计参考文献

本文档只筛选对“仿真实验怎么构造”有直接借鉴价值的文献。重点不是主题相似度，而是这些论文能否提供真值位移、雷达相位、wrapped phase、多 target、噪声、遮挡、加速度噪声、Kalman/phase unwrapping 验证指标等可复用设计。

说明：本地已有 PDF 的文献优先按全文/摘要整理；扫描版 PDF 无法抽取全文时，结合本地速读记录和公开元数据核对。没有看到全文细节的地方均以“未确认/摘要可见”标注。

## 一、优先保留的 11 篇文献

| 推荐 | 文献 | 最值得借鉴的仿真/实验设计点 |
|---|---|---|
| 高 | Ma et al., 2026, acceleration-aided Kalman phase denoising/unwrapping | 预测辅助相位校正、Kalman Q/R、自适应噪声、强噪声下解缠失败验证 |
| 高 | Guerzoni et al., 2025, Doppler-assisted phase unwrapping | 直接统计相位解缠错误概率，按噪声方差、速度、采样间隔画失败曲线 |
| 高 | Liu et al., 2022, FMCW phase ambiguity | 明确生成 wrapped phase、多 target range-bin 干扰、不同位移幅值下相位模糊 |
| 高 | Li et al., 2015, noncontact FMCW radar SHM | 多 target 距离设置、range bin 中心/边缘、谱泄漏导致 target 间扰动 |
| 高 | Li et al., 2022, mmSHM full-field sensing | 同 rangeBin 多 target、range-angle 分离、不同频率/幅值/速度组合 |
| 高 | Ma et al., 2023, accelerometer + FMCW radar | 倒挂/共址传感、环境参考 target、转换系数、雷达低频 + 加速度高频融合 baseline |
| 中高 | Ma et al., 2025, target occlusion | 多 good targets、target 短时遮挡、遮挡后 drift、multi-target phase unwrapping |
| 中高 | Ma et al., 2026, multi-chirp adaptive unwrapping | 大位移跨相位边界、多 chirp 预测、单 target 与多 target 大位移验证 |
| 中 | Zhu et al., 2023, multi-rate Kalman fusion | 结构系统真值、加速度/位移不同采样率、5% measurement noise、NRMSE |
| 中 | Smyth and Wu, 2007, multi-rate Kalman fusion | 经典加速度 + 位移多率 Kalman，适合作为融合 baseline 和 Q/R 讨论 |
| 中 | Pal and Nagarajaiah, 2024, short-term memory Kalman | intermittent displacement、加速度 time-varying bias，适合模拟雷达 target 丢失/恢复 |

## 二、逐篇文献卡片

### 1. Ma et al. 2026 - acceleration-aided Kalman phase denoising/unwrapping

- 题名：Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring
- 作者/出处：Zhanxiong Ma, Tongtong Zhang, Yang Zhu, Shuhan Lin, Jigu Lee, Hoon Sohn, Qiangqiang Zhang. Mechanical Systems and Signal Processing, 248, 113991, 2026.
- DOI/link：https://doi.org/10.1016/j.ymssp.2026.113991
- 是否有仿真实验：全文可见部分显示主要是实验验证，Section 4 为四层建筑模型，Section 5 为 45 m 人行桥；文中还给出 Kalman 递推卷积形式和最小收敛时间分析。未看到独立“数值仿真”章节。
- 对象：FMCW mmWave radar-based structural displacement monitoring；四层建筑模型和现场人行桥。
- 信号生成/处理：把雷达相位建模为离散常加速度系统；测得加速度进入预测；用预测相位对 wrapped radar phase 做 2pi 校正；Kalman 更新输出连续、降噪相位；噪声参数自适应优化；方向转换因子用带通后的雷达相位和加速度积分相位标定。
- 噪声/缠绕：核心问题就是 phase wrapping + high phase noise；摘要报告高噪声条件下旧方法失败，本文方法完成解缠和降噪。
- 指标：phase RMSE，文摘和本地速读记录显示实验中相位误差约 2.1 rad 和 0.2 rad 量级；位移误差可由相位换算。
- 可借鉴：你的后端公式几乎可以把这篇作为 single-target Ma baseline；仿真中应复现其“预测相位 -> 2pi round 校正 -> Kalman 更新”的闭环，并构造高相位噪声导致 Itoh/先解缠再滤波失败的场景。
- 差异：该文状态是单 target LoS 相位；你的状态是结构主相位 Theta，多 target 先把 LoS corrected phase 乘以 beta_i 构造结构方向观测，统一用 `H_i=[1,0]` 融合，且 target selection 阶段不做完整解缠。
- 推荐程度：高。虽然不是纯数值仿真论文，但它是你的核心 baseline 和后端验证模板。

### 2. Guerzoni et al. 2025 - Doppler-assisted phase unwrapping

- 题名：A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring
- 作者/出处：Giorgio Guerzoni, Elahe Faghand, Loris Vincenzi, Elisa Bassoli, Giorgio Matteo Vitetta. Mechanical Systems and Signal Processing, 235, 112777, 2025.
- DOI/link：https://doi.org/10.1016/j.ymssp.2025.112777
- 是否有仿真实验：有。主体 Section 5 是实验；Appendix B.3 明确有 computer simulations，统计 TPU/DAPU probability of failure。
- 对象：mmWave MIMO FMCW radar；单点/多点结构位移；四层钢框架和 footbridge 实验，附录为单 target constant-speed 数值仿真。
- 信号生成/处理：先生成 noiseless phase trajectory，再叠加相位噪声；DAPU 还生成同一 frame 内两条 chirp phase 序列和相关噪声；使用 Doppler rate 预测跨帧 phase rotations。
- 噪声/缠绕：相邻帧目标径向位移超过 lambda/4 时传统解缠失败；仿真改变 noise variance、noise correlation、frame/chirp time ratio、target speed。
- 指标：unwrapping error count / input length，即 phase unwrapping failure probability；实验中还比较位移时程。
- 可借鉴：非常适合你的“强响应导致 phase 跨越 pi”章节。建议直接学习它的失败概率曲线：横轴 SNR/相位噪声方差/峰值速度，纵轴解缠错误率。
- 差异：它用 Doppler 辅助，未融合加速度；主要是径向运动 target，不是倒挂雷达利用静止环境 target 估计结构主相位。
- 推荐程度：高。它的“解缠错误次数/失败概率”评价方式尤其适合你的仿真。

### 3. Liu et al. 2022 - FMCW phase ambiguity

- 题名：Solving Phase Ambiguity in Interferometric Displacement Measurement With Millimeter-Wave FMCW Radar Sensors
- 作者/出处：Jingxiao Liu, Yaochao Li, Changzhan Gu. IEEE Sensors Journal, 22(9), 8482-8489, 2022.
- DOI/link：https://doi.org/10.1109/JSEN.2022.3158657
- 是否有仿真实验：有。Section III 包含 Linear Phase Extraction 和多 target simulation；Fig. 6-10 展示等效 I/Q、phase ambiguity 和多 target tracking。
- 对象：79 GHz single-channel FMCW radar；点目标、三目标、机械振动台实验。
- 信号生成/处理：设定点目标距离，如 600.1 mm；生成 FMCW range profile 和 slow-time phase；位移超过毫米波半波长时 raw arctangent phase 出现 wrapping；多目标仿真包括一个目标从 0.1 m 起始运动、一个目标在 0.2 m 附近做正弦运动、第三目标在 0.8 m 做复合运动。
- 噪声/缠绕/多 target：主要讨论 phase ambiguity 和 range-bin/clutter 干扰；文中强调 target #1 接近 target #2 所在 range bin 时会扰乱 #2 phase。
- 加速度：不涉及。
- 指标：实验给出 RMSE，如 90 um、0.9 mm、4 cm 位移场景下传统方法与 proposed method 对比。
- 可借鉴：你的雷达信号级仿真可以从这里抽象：先生成 complex target return，再取 range bin phase；设不同初始距离、不同位移幅值，专门展示 wrapped phase 如何破坏传统相位恢复。
- 差异：它解决单通道 FMCW 等效 I/Q 和线性相位解调，不处理 AoA/beta、多 target Kalman、加速度辅助。
- 推荐程度：高。它是“wrapped phase 怎么模拟”的直接模板。

### 4. Li et al. 2015 - noncontact FMCW radar SHM

- 题名：A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring
- 作者/出处：Cunlong Li, Weimin Chen, Gang Liu, Rong Yan, Hengyi Xu, Yi Qi. Sensors, 15, 7412-7433, 2015.
- DOI/link：https://doi.org/10.3390/s150407412
- 是否有仿真实验：有。Section 4 是 Displacement Measurement of Multiple Targets，Section 4.2 为 Simulation Analysis of Displacement Measurement of Multiple Targets。
- 对象：SHM 多 target FMCW 位移测量；三目标位于不同距离。
- 信号生成/处理：仿真三 target，距离分别落在 range bin 中心或边缘；target 1 在 10 m range bin 内先后退再前进，步长 1 mm，总位移 20 mm，target 2 和 target 3 保持静止；通过 DFT spectrum 和 phase demodulation 得到位移。
- 噪声/多 target：重点不是白噪声，而是 spectrum leakage；target 位于 range bin 边缘时泄漏更明显，静止 target 出现更大波动。
- 加速度：不涉及。
- 指标：target displacement fluctuation；文中指出多 target 间扰动小于 0.1 mm。
- 可借鉴：你可以把“同 rangeBin 多散射体等效 target”和“相邻 rangeBin 干扰”拆成两个仿真：前者用复相量混合，后者用谱泄漏/旁瓣干扰。
- 差异：目标是结构上的人工反射 target，且主要靠 range 区分；你的 target 是环境静止散射体，且雷达随结构运动。
- 推荐程度：高。它给了多 target range-bin 设置的干净模板。

### 5. Li et al. 2022 - mmSHM range-angle full-field sensing

- 题名：Multi-scale and full-field vibration measurement via millimetre-wave sensing
- 作者/出处：Songxu Li, Yuyong Xiong, Xiangtian Shen, Zhike Peng. Mechanical Systems and Signal Processing, 177, 109178, 2022.
- DOI/link：https://doi.org/10.1016/j.ymssp.2022.109178
- 是否有仿真实验：主要是实验验证；文中也用 cantilever beam modal simulation 对比模态结果。Section 4.1-4.3 分别做 multi-scale、同 rangeBin multi-target、full-field cantilever beam。
- 对象：77 GHz MIMO LFMCW radar；线性位移台、振动激励器、同 rangeBin 多 target、双悬臂梁。
- 信号生成/处理：从 range-angle joint dimension 选择 target；对每个 range-angle target 提取 interferometric phase；用几何角度修正 LoS displacement。multi-scale 部分通过 linear stage 产生从微米到分米尺度运动。
- 噪声/多 target：明确指出传统 range-only 方法无法分离同一 range bin 的多个目标，会造成 coupling/aliasing；range-angle 方法可以隔离 target。
- 加速度：不涉及。
- 指标：位移时程、频率识别、模态结果与仿真/参考传感器对比。
- 可借鉴：你的前端仿真应至少包含“同 rangeBin 两个 target、不同角度、不同 beta_i”的场景，用来证明 range-angle target 比 rangeBin 总相位更合理。
- 差异：雷达固定，目标/结构运动；你的雷达随结构运动，环境散射 target 近似静止。
- 推荐程度：高。它支撑 multi target/range-angle 这条实验线。

### 6. Ma et al. 2023 - accelerometer + FMCW radar displacement estimation

- 题名：Structural displacement estimation using accelerometer and FMCW millimeter wave radar
- 作者/出处：Zhanxiong Ma, Jaemook Choi, Liu Yang, Hoon Sohn. Mechanical Systems and Signal Processing, 182, 109582, 2023.
- DOI/link：https://doi.org/10.1016/j.ymssp.2022.109582
- 是否有仿真实验：本地 PDF 为扫描版，未能抽取全文；公开摘要和本地速读记录显示主要通过四层结构模型和人行桥现场实验验证，未确认独立数值仿真章节。
- 对象：共址 accelerometer + FMCW mmWave radar；雷达安装在结构测点，利用周围环境 target。
- 信号生成/处理：短时同步采集加速度和 radar target phase；选择与加速度积分位移最一致的 target；估计 LoS 到结构振动方向的 direction conversion factor；连续阶段用雷达低频和加速度高频 FIR 融合。
- 噪声/多 target：多 target 主要用于 best target selection，不是多 target 同时 Kalman 观测；相位解缠由加速度辅助。
- 指标：公开记录显示 RMSE 可达 0.1 mm 量级；具体工况指标需回看全文。
- 可借鉴：它是你的 baseline 0：single best target + conversion factor + accelerometer fusion。你的仿真应复现其局限：如果 best target SNR 下降或 target 失效，单 target 方法会退化。
- 差异：该文以单 best target 为主，转换系数多在初始校准得到；你的方法要处理多 target wrapped phase、不预先完整解缠、AoA 冷启动和在线 beta 自举。
- 推荐程度：高。它不是最佳“数值仿真模板”，但必须作为前序方法和 baseline。

### 7. Ma et al. 2025 - intermittent radar target occlusion

- 题名：Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion
- 作者/出处：Zhanxiong Ma, Jaemook Choi, Jigu Lee, Hoon Sohn. Mechanical Systems and Signal Processing, 223, 111888, 2025.
- DOI/link：https://doi.org/10.1016/j.ymssp.2024.111888
- 是否有仿真实验：本地 PDF 为扫描版，未能抽取全文；公开摘要显示通过 10 m 桥梁结构实验和 footbridge field tests 验证。未确认独立数值仿真章节。
- 对象：桥梁 displacement estimation；多 good radar targets；车辆等移动物体造成 intermittent target occlusion。
- 信号生成/处理：短时雷达/加速度测量选择多个 good targets，并估计 direction-converting factors；连续阶段检测遮挡，用 displacement reconstruction 和 multi-target phase-unwrapping 去除遮挡导致的 drift。
- 噪声/遮挡：核心变量是 target short-term occlusion、target recovery 后 drift、multi-target 冗余。
- 加速度：作为 phase unwrapping / reconstruction 辅助。
- 指标：公开摘要报告实验和现场验证；具体 RMSE 表格需看全文。
- 可借鉴：你的仿真可以设置 target mask_i(k)：某 target 在若干秒内不可用，或 R_i(k) 突增；比较单 target、简单平均、自适应 R、多 target Kalman 的鲁棒性。
- 差异：该文仍依赖多个 good targets 和已有 DCF 标定；你的方法强调 wrapped phase 进入后端、beta 在线自举和 target-wise R。
- 推荐程度：中高。它是 target 失效/遮挡仿真的核心参考。

### 8. Ma et al. 2026 - multi-chirp adaptive phase unwrapping

- 题名：Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping
- 作者/出处：Zhanxiong Ma, Hai Lu, Tongtong Zhang, Boran Wang, Xin Jing, Qiangqiang Zhang, Hoon Sohn. Measurement, 262, 120029, 2026.
- DOI/link：https://doi.org/10.1016/j.measurement.2025.120029
- 是否有仿真实验：主要是实验验证，Section 4 包含四层建筑模型、大位移、多 target linear stages 和 footbridge field test；未看到独立数值仿真章节。
- 对象：FMCW mmWave radar-only displacement；大位移相位缠绕；多 target。
- 信号生成/处理：每个 time step 多 chirp 相位用于估计 phase change rate，再预测下一时刻 phase range，对 main chirp phase 解缠。实验包含最高约 5 cm 大位移。
- 噪声/多 target：讨论多 chirp 数量与 SNR；未来工作明确提到 overlapping echoes 和 varying SNRs。
- 加速度：不需要额外加速度，适合作为 radar-only baseline。
- 指标：实验 RMSE；四层建筑模型中 proposed algorithm 在多个工况 RMSE < 0.6 mm，双 linear stage 多 target 测试 RMSE < 0.1 mm，footbridge 约 0.04-0.05 mm。
- 可借鉴：你的 baseline 可加入“radar-only adaptive phase unwrapping”；强响应场景下比较加速度辅助和 radar-only 的解缠边界。
- 差异：它使用同一 time step 多 chirp 预测，不处理多环境 target 的 beta_i 自举，也不利用加速度。
- 推荐程度：中高。用于“大位移 wrapped phase”场景很合适。

### 9. Zhu et al. 2023 - multi-rate Kalman structural response reconstruction

- 题名：Multi-rate Kalman filtering for structural dynamic response reconstruction by fusing multi-type sensor data with different sampling frequencies
- 作者/出处：Zimo Zhu, Jubin Lu, Songye Zhu. Engineering Structures, 293, 116573, 2023.
- DOI/link：https://doi.org/10.1016/j.engstruct.2023.116573
- 是否有仿真实验：有。Section 3 是 numerical examples，使用 eight-story shear frame model；Section 4 是 cantilever beam laboratory validation。
- 对象：八层 shear frame；加速度和位移多率观测；未观测 DOF virtual sensing。
- 信号生成/处理：二阶结构动力方程生成真实 displacement/velocity/acceleration；离散状态空间；100 Hz acceleration、5 Hz displacement；根据当前是否有 displacement observation 切换观测方程；可加 RTS smoother。
- 噪声：measurement noise 标准差取真实响应标准差的 5%；R_k 用 sigma^2；system noise 也显式设置；还做 noise level/system noise parametric analysis。
- 指标：RMSE、NRMSE、频域对比、不同 scheme 的表格比较。
- 可借鉴：你的结构真值可以采用 SDOF/MDOF 状态空间生成，而不是只用正弦；加速度噪声、位移观测噪声和 Q/R 可学习其比例设定。
- 差异：它融合的是直接位移传感器和加速度，不涉及 radar phase/wrapping/beta/multi target。
- 推荐程度：中。适合“结构真值 + 加速度噪声 + Kalman 指标”部分。

### 10. Smyth and Wu 2007 - classical multi-rate Kalman fusion

- 题名：Multi-rate Kalman filtering for the data fusion of displacement and acceleration response measurements in dynamic system monitoring
- 作者/出处：Andrew W. Smyth, Meiliang Wu. Mechanical Systems and Signal Processing, 21(2), 706-723, 2007.
- DOI/link：https://doi.org/10.1016/j.ymssp.2006.03.005
- 是否有仿真实验：有。该文是经典多率 Kalman fusion 方法文献，公开元数据和后续文献均将其作为 displacement + acceleration data fusion 的基础。
- 对象：动态系统监测中的 displacement and acceleration response measurements。
- 信号生成/处理：多率传感器观测进入 Kalman filter；加速度提供高频动态，位移观测约束低频漂移。
- 噪声：用于讨论不同采样率、不同 measurement noise 下的融合；具体参数需全文核对。
- 指标：位移/加速度重构误差。
- 可借鉴：适合作为加速度-位移融合 baseline 的方法源头，尤其用于解释为何不能只做加速度双积分。
- 差异：不涉及毫米波雷达、wrapped phase、多 target 或 AoA。
- 推荐程度：中。作为方法支撑引用，不必作为核心仿真复现对象。

### 11. Pal and Nagarajaiah 2024 - short-term memory Kalman with intermittent displacement

- 题名：Data fusion based on short-term memory Kalman filtering using intermittent-displacement and acceleration signal with a time-varying bias
- 作者/出处：Ashish Pal, Satish Nagarajaiah. Mechanical Systems and Signal Processing, 216, 111482, 2024.
- DOI/link：https://doi.org/10.1016/j.ymssp.2024.111482
- 是否有仿真实验：公开摘要/元数据显示该文提出 intermittent displacement + acceleration + time-varying bias 的数据融合算法；具体仿真章节和参数需全文确认。
- 对象：高采样 acceleration 与间歇 displacement measurement；加速度含 unknown time-varying bias。
- 信号生成/处理：短时记忆 Kalman 思想，处理位移观测间歇可用和加速度 bias；公开摘要提到 two-stage Kalman estimator。
- 噪声/漂移：加速度 time-varying bias 是核心；位移 intermittent observation 可类比 radar target 短时失效。
- 指标：动态位移估计误差；具体 RMSE/NRMSE 需全文确认。
- 可借鉴：你的仿真可设置 acceleration bias + low-frequency drift，并模拟 radar target 缺测；用它支撑“间歇位移观测 + 高频加速度”的建模合理性。
- 差异：没有 radar phase 和 beta_i；位移观测通常是物理位移，不是 wrapped phase。
- 推荐程度：中。适合加速度 bias 和 target 丢失场景，不是核心 radar-phase 文献。

## 三、建议的仿真实验框架

### 1. 结构位移真值 q(t)

建议至少设置四类真值，逐步增加难度：

1. 单频正弦：
   - q(t) = A sin(2 pi f t)，如 A = 0.1, 0.5, 1, 3, 10 mm；f = 1, 3, 5 Hz。
   - 用来验证相位比例、wrapped phase、Kalman 收敛。
2. 多频结构振动：
   - q(t) = sum_j A_j sin(2 pi f_j t + varphi_j)，f_j 取结构一阶/二阶频率。
   - 用来验证结构频带一致性筛选、加速度预测和频谱误差。
3. 车辆激励非平稳响应：
   - 用半正弦/高斯包络调制多频响应，或用 SDOF/MDOF 状态空间在移动荷载/脉冲荷载下生成。
   - 用来测试自适应 R、target 短时失效和非平稳强响应。
4. 强响应跨 pi 场景：
   - 令相邻采样位移增量满足 |Delta phi_i| > pi，或位移幅值远超 lambda/4。
   - 用来统计 phase unwrapping error count。

### 2. 雷达 target 仿真

每个 target i 设定：

- beta_i 表示 LoS 到结构真实振动方向的转换系数，可由几何投影初值 `p_i=|cos(theta_i)|` 得到 `beta_i=1/max(p_i, epsilon)`，例如 [1.05, 1.18, 1.54, 2.22, 4.0]，同时设置 AoA 初值误差 theta_i + epsilon_theta。
- LoS phase 真值：
  phi_i(k) = Theta(k) / beta_i + b_i，Theta(k) = 4 pi q(k) / lambda。
- complex observation：
  y_i(k) = A_i(k) exp(j phi_i(k)) + n_i(k)，n_i 为 complex Gaussian noise。
- wrapped phase：
  psi_i(k) = angle(y_i(k))。

建议四个 target 难度层级：

1. 单 target clean：固定 beta、固定 SNR、无遮挡。
2. 多 target 不同几何：不同 beta_i、不同 b_i、不同 SNR_i。
3. target 质量变化：某些 target 在 [t1, t2] 内 SNR 降低 10-20 dB，或 A_i(k) 突然衰减。
4. 同 rangeBin 多散射体等效 target：
   - y_i(k) = sum_l A_il exp(j(Theta(k)/beta_il + b_il)) + n_i(k)。
   - 当 beta_il 接近时等效 beta 稳定；当强散射体 beta 差异大且幅值接近时，等效相位会非线性漂移。

### 3. Wrapped phase 生成

推荐不要直接对无噪声相位 wrap 后再加相位噪声，优先从 complex observation 取 angle：

```text
Theta_k = 4*pi*q_k/lambda
phi_i,k = Theta_k/beta_i + b_i
y_i,k = A_i,k*exp(j*phi_i,k) + sigma_i*(randn + j*randn)/sqrt(2)
psi_i,k = angle(y_i,k)
```

如果需要可控相位噪声，也可以在高 SNR 近似下写：

```text
psi_i,k = wrapToPi(phi_i,k + eta_i,k), eta_i,k ~ N(0, sigma_phi_i^2)
```

但论文中最好说明 complex-noise model 更接近 radar I/Q。

### 4. 加速度生成

- 真实加速度：a_true(t) = d^2 q(t) / dt^2。正弦信号可解析求导；非平稳/仿真结构响应可用状态空间直接输出 acceleration。
- 测量加速度：
  a_m(k) = a_true(k) + b_a(k) + d_a(k) + eta_a(k)。
- 噪声项建议包含：
  - white noise：eta_a ~ N(0, sigma_a^2)，sigma_a 可按 0.3-1 mg 或按真实 RMS 的 1%-5%；
  - bias：常值或 random walk；
  - low-frequency drift：一阶 Gauss-Markov 或低频正弦；
  - synchronization error：a_m(k) = a_true(k - Delta t_sync) + noise。

### 5. Baseline 设计

建议至少对比：

1. 单 target Ma 式 acceleration-aided Kalman：
   - 选择 SNR 最高或初始相关性最高的 target；
   - 固定 conversion factor。
2. 离线固定转换系数：
   - 用前 T_cal 秒 unwrap 后最小二乘估计 beta_i；
   - 后续不再更新。
3. 无 AoA 冷启动：
   - beta_i 初值统一设 1 或随机；
   - 用来展示 AoA 初值减少收敛时间。
4. 固定 R：
   - 所有 target 同一 R；
   - 用来展示 target-wise adaptive R 的必要性。
5. 多 target 简单平均：
   - 对各 target 校正后的位移直接平均或按 SNR 固定加权。
6. 本文方法：
   - 结构主相位 multi-target Kalman；
   - AoA 冷启动；
   - beta_i/beta_i 滑动窗口自举；
   - target-wise adaptive R；
   - target 缺测和低质量降权。

### 6. 指标

主指标：

- displacement RMSE / MAE / max error；
- phase RMSE；
- unwrapping error count：|z_corr - phi_true| > pi 或 2pi branch 选择错误次数；
- jump count：估计位移中非物理跳变次数；
- beta_i convergence time：|beta_hat_i - beta_i| / |beta_i| < 5% 所需时间；
- innovation statistics：target-wise innovation RMS、NIS 或残差方差；
- frequency error：主频识别误差、PSD 峰值误差；
- robustness score：target 失效期间和恢复后的 RMSE。

### 7. 推荐图

- q_true 与各方法 q_hat 时程对比；
- psi_i wrapped phase 与 z_i,corr corrected phase；
- 每个 target 的 beta_hat_i 或 beta_hat_i 收敛曲线；
- target-wise R_i(k) 自适应变化，叠加 target SNR/遮挡区间；
- innovation/residual heatmap，横轴 time，纵轴 target；
- SNR sweep：RMSE vs SNR；
- target number sweep：RMSE vs m；
- phase wrapping intensity sweep：RMSE / unwrap error count vs max |Delta phi|;
- 同 rangeBin 多散射体：等效 phase bias vs beta spread / amplitude ratio。

### 8. 推荐表格

- 不同方法的 RMSE / MAE / max error；
- unwrapping error count 和 jump count；
- beta convergence time；
- target failure 场景下失效前、失效中、恢复后的 RMSE；
- 不同 SNR、不同 target 数量、不同 beta 分布下的鲁棒性表；
- 消融实验表：AoA 冷启动、beta 自举、自适应 R、多 target Kalman 分别去掉后的误差。

## 四、可直接写进论文的仿真叙述骨架

建议仿真章节按以下顺序组织：

1. 仿真信号模型：
   - 给出 q_k、Theta_k、phi_i,k、complex radar observation、wrapped phase、accelerometer observation。
2. Case 1：单 target 小位移无缠绕：
   - 验证公式正确性和 Kalman 收敛。
3. Case 2：单 target 强响应有缠绕：
   - 对比 Itoh、Ma single-target Kalman、本文方法。
4. Case 3：多 target 不同 beta/SNR：
   - 验证 multi-target Kalman 优于 single best target 和 simple average。
5. Case 4：AoA 初值误差和 beta 自举：
   - 展示 beta_hat 收敛和无 AoA 冷启动的慢收敛/误收敛。
6. Case 5：target 短时失效/SNR 突降：
   - 展示 adaptive R 和缺测处理的鲁棒性。
7. Case 6：同 rangeBin 多散射体：
   - 证明 rangeBin 总相位可能产生等效 beta 漂移，range-angle target 更稳。
8. Sensitivity analysis：
   - SNR、target 数量、phase wrapping intensity、acceleration bias、synchronization error。

## 五、参考链接

- Ma et al. 2026, MSSP, Kalman phase denoising/unwrapping: https://doi.org/10.1016/j.ymssp.2026.113991
- Guerzoni et al. 2025, MSSP, Doppler-assisted phase unwrapping: https://doi.org/10.1016/j.ymssp.2025.112777
- Liu et al. 2022, IEEE Sensors Journal, phase ambiguity: https://doi.org/10.1109/JSEN.2022.3158657
- Li et al. 2015, Sensors, noncontact FMCW radar SHM: https://doi.org/10.3390/s150407412
- Li et al. 2022, MSSP, mmSHM full-field sensing: https://doi.org/10.1016/j.ymssp.2022.109178
- Ma et al. 2023, MSSP, accelerometer + FMCW radar: https://doi.org/10.1016/j.ymssp.2022.109582
- Ma et al. 2025, MSSP, intermittent target occlusion: https://doi.org/10.1016/j.ymssp.2024.111888
- Ma et al. 2026, Measurement, multi-chirp adaptive unwrapping: https://doi.org/10.1016/j.measurement.2025.120029
- Zhu et al. 2023, Engineering Structures, multi-rate Kalman fusion: https://doi.org/10.1016/j.engstruct.2023.116573
- Smyth and Wu 2007, MSSP, multi-rate Kalman fusion: https://doi.org/10.1016/j.ymssp.2006.03.005
- Pal and Nagarajaiah 2024, MSSP, short-term memory Kalman: https://doi.org/10.1016/j.ymssp.2024.111482
