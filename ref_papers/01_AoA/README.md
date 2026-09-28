# AoA / Range-Angle 方法论文速读说明

本目录用于支撑“TI IWR1843 / 低通道数 FMCW MIMO 毫米波雷达中，如何从 rangeBin target 升级到 range-angle target，并保留可用于相位跟踪的 complex slow-time signal”这一问题。下面内容主要依据各 PDF 的摘要、引言贡献、结论与展望整理；后续写作或继续检索时应先读本文件，只有需要公式、实验参数、图表和精确数值时再打开原文。

## 快速结论

对倒挂式毫米波雷达结构位移监测，最值得优先实现的不是“只输出一个 AoA 数值”的 DOA 峰值估计，而是：

1. `Range FFT + Angle FFT / Bartlett DBF`
   - 最稳 baseline。输入为 range FFT 后的 per-RX/per-virtual-channel 复数数据，输出 range-angle complex bin 或 angle-gated complex slow-time。
2. `Range FFT + Capon/MVDR / LCMV beamforming`
   - 最可能作为主增强方案。能在同一 rangeBin 内压制非目标角度散射体，并天然输出 `w^H x_r[n]` 形式的复数 slow-time。
3. `OMP / LASSO / SBL / MUSIC / RELAX / learning-based SR`
   - 更适合离线对照、分离能力上限分析或论文进阶部分。它们能提高谱峰分辨率，但对低通道数、相干散射、多径、字典失配、实时计算和复数相位连续性更敏感。

## 阅读优先级

1. `TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`
   - 硬件和工程链路基线。先确认 MIMO 虚拟阵列、TDM/BPM、Angle FFT 前数据形态。
2. `Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`
   - 最直接的 same rangeBin 实测证据：TI 低通道 MIMO-FMCW 中，同距离单元的两个目标可通过角度/beamforming 分离，并分别提取相位/位移。
3. `Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf`
   - 商用 3TX/4RX AWR2243 上的 same radial distance 多人生命体征分离，明确用 Capon/beamforming 产生每个目标的复数 slow-time 相位信号。
4. `Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`
   - 从 range-angle joint component 的相位演化恢复微动/振动位移，是结构微振动方向最值得引用的强证据之一。
5. `Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`
   - 直接点出传统 FMCW 只能按 range 区分目标，遇到 same rangeBin 多目标耦合和相邻 rangeBin 干扰会失效；用 range-angle joint dimension 的 phase evolution tracking 做全场多点振动提取。
6. `Full-field 3D displacement measurement via microwave sensing.pdf`
   - 把单雷达 LOS 位移推进到三雷达 full-field 3D 位移，并给出测点在多雷达 range-angle heatmap 中自动匹配、DCS/SCS 坐标转换和 3D 重构方法。
7. `Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`
   - 最贴近“range-angle 定位后，用 beamforming 输出 slow-time phase signal”的处理链。
8. `A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf`
   - 使用 TI IWR1843 和 MVDR beamforming，且明确讨论低天线数导致多目标方向泄漏的局限。
9. `Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`
   - 低天线数 MIMO-FMCW 中用 CS/OMP 做 range-angle 分离的重点参考。
10. `Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`
   - 上一篇的扩展版，加入 Doppler/slow-time 维度和有限测量理论保证。
11. `Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf`
   - SBL 做 joint range-angle 多目标精定位的最新进展，可作为离线上限方法。
12. `Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf`
   - MUSIC/RELAX 超分辨角度估计代表，适合作为 subspace 类对照。
13. `Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf`
   - 低阵元 FMCW DOA 超分辨的 RELAX/外推背景，主要支撑“角度参数可分”，不能单独支撑“相位可用”。
14. `Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf`、`Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf`
   - 学习型 AoA/azimuth super-resolution 候选，只建议作为进阶对照，不建议直接作为相位跟踪主链路。

## 文献速读卡片

### FMCW multiple-input multiple-output radar with iterative adaptive beamforming

文件：`FMCW_multiple-input_multiple-output_radar_with_iterative_adaptive_beamforming.pdf`

用途：作为 MIMO FMCW 迭代自适应波束形成的早期方法参考，重点关注阵列通道、波束形成和角度旁瓣抑制对目标分离的影响。

### Non-Contact Vital Signs Monitoring for Multiple Subjects Using a Millimeter-Wave FMCW Automotive Radar

文件：`Non-Contact_Vital_Signs_Monitoring_for_Multiple_Subjects_Using_a_Millimeter-Wave_FMCW_Automotive_Radar.pdf`

用途：补充 76–81 GHz FMCW 汽车雷达对多个同距离目标进行角度隔离和相位生命体征提取的实测案例，用于支撑“角度分离后保留各目标复数慢时间序列”的方法链路。

### TI MMWAVE-SDK / AoAProc / MIMO Radar app report

文件：`TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`

用途：作为 IWR/AWR 系列 MIMO-AoA 实现的工程基线，解释虚拟阵列、TDM-MIMO、BPM-MIMO、Angle FFT 前后处理顺序。

创新点：不是论文创新，而是 TI 官方实现资料。核心信息是 MIMO 可把 `N_TX x N_RX` 合成为虚拟阵列，从而提升角分辨率；4RX 约 30 度，8RX 约 15 度这一经验量级可用于说明低通道硬件限制。

方法论：TDM-MIMO 中不同 TX 轮流发射，接收后按 TX/RX 通道拼成虚拟阵列；BPM-MIMO 需要先解码 TX 贡献，再做 angle FFT，且非零速度下应注意 Doppler 相位修正。

不足/注意：官方资料偏基础原理，不直接给 IWR1843BOOST 的完整 azimuth/elevation 虚拟阵列可用性；实际实现仍需结合板级天线布局、通道幅相校准和 TDM phase compensation。

与你课题关系：必须优先读。后续保存数据时，至少要保留 Range FFT 后 per-virtual-channel 的复数 cube，而不是只保存点云或 range-angle heatmap magnitude。

### Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor

文件：`Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`

用途：作为“同一个 range bin 内多个目标，经角度分离后分别提取 phase/displacement”的最直接实测参考。

创新点：使用商用 TI 77-81 GHz MIMO-FMCW 毫米波雷达，在 range 分辨率不足以区分两个目标时，利用 MIMO 虚拟阵列的角度维把同 range bin 的目标分开；论文明确展示振动角反射器和人体处于同一 range bin 时，仍可分别恢复位移/生命体征。

方法论：先做 Range FFT 找到目标所在 range bin，再在该 range bin 上做 azimuth FFT/beamforming 得到 range-angle map；对每个目标方向取 beamformed complex slow-time signal，进行相位解缠和 displacement/vital-sign extraction。

不足/展望：角分辨率受 3TX/4RX 虚拟阵列限制，论文中的同 rangeBin 分离依赖较大的角度间隔；对结构场景中的强静态散射、多径、相干散射体和长期相位稳定性没有展开。

与你课题关系：强相关。可直接引用来支撑“same rangeBin 内多个散射体并非只能合成一个 rangeBin target；若角度可分，可转化为多个 range-angle component，并分别提取相位序列”。

### Simultaneous Monitoring of Multiple People's Vital Sign Leveraging a Single Phased-MIMO Radar

文件：`Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf`

用途：作为低通道商用 MIMO-FMCW 中 same radial distance 多人分离并提取每人相位生命体征的主参考。

创新点：在 TI AWR2243 3TX/4RX 平台上结合 TX phased beamforming、TDM-MIMO 和 RX Capon beamforming，提升多人同距离场景下的角度隔离能力；论文目标不是只输出位置，而是为每个人恢复呼吸和心跳相位信号。

方法论：先形成多个 TX 波束覆盖不同方向，再利用 RX Capon/MVDR 抑制其他角度目标；对每个角度目标保留 range-DFT 后的复数慢时间序列，经过相位校正和 DACM 等处理提取 breathing/heartbeat。

不足/展望：实验表明角度太近时心跳分量会明显退化，说明低通道数下同 rangeBin 分离不是无条件成立；beamforming 权重和目标角度稳定性会影响相位连续性。

与你课题关系：强相关。适合和 Ahmad 2018 一起作为“商用低通道 mmWave radar 可把同距离目标分离成相位可用分量”的核心引用。

### Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View

文件：`Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`

用途：作为“range-angle joint component 的 interferometric phase evolution 可用于微动/振动位移恢复”的强证据。

创新点：提出 mmWBat，用毫米波 LFMCW 雷达在全视场中定位并量化多个微动目标；相较只看单个 range bin，相位提取建立在 range-angle joint dimension 上，更接近你要的“rangeBin target 升级为 range-angle target”。

方法论：通过 range-angle processing 找到目标在二维空间中的分量，再跟踪该分量的复数相位演化；用毫米波相位位移关系恢复多目标微动，实验覆盖角反射器机械振动、多人生命体征、桥梁/结构模型和 RF microphone 类应用。

不足/展望：不同硬件配置下角分辨率差异较大；论文更强调全场微动成像系统，具体到 IWR1843 单芯片小孔径时仍需要重新验证角度泄漏和相位串扰。

与你课题关系：强相关，尤其适合结构位移/微振动章节。它能支撑“可用的不是单纯角度峰值，而是 range-angle component 的相位轨迹”。

### Multi-scale and Full-field Vibration Measurement via Millimetre-Wave Sensing

文件：`Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`

用途：作为 `Millimeter-Wave Bat` 之后最关键的 SHM 场景延伸文献。它把毫米波 full-field micro-motion sensing 落到结构健康监测，明确处理两类问题：一是大位移跨越 range bin 时 beat frequency 改变导致传统固定频率相位解调失真；二是多测点全场同步监测时，同一 range bin 多目标耦合、相邻 range bin 干扰会让单纯 range 维相位提取失效。

核心创新：

- 提出 `mmSHM`，用 77 GHz MIMO LFMCW 毫米波雷达实现多尺度、全场、多点同步振动测量。
- 提出 `ASPD`（adaptive segmented phase demodulation），针对大尺度位移导致目标跨 range bin 的情况，先做 range ridge tracking，再按 range resolution 自适应分段，每段使用当前 beat frequency 做相位估计，最后把分段相位端到端连接并解缠。
- 在 full-field 部分复用/扩展 MFMS 思路，把相位跟踪从单 range bin 推到 `range-angle joint dimension`。论文明确说传统 FMCW 只按 range profile 区分目标，多个目标落在同一 range bin 时只表现为一个峰，近似最大似然提取的相位会发生 aliasing。
- 给出 2D-FFT heatmap 上的目标索引 `(u_q, v_q)`，再从对应 range-angle component 的复数累加项提取每个目标的 interferometric phase。位移恢复形式为 `x_q = λ_c [φ_q - mean(φ_q)] / (4π cosϕ_q)`，其中 `ϕ_q` 是目标振动方向与雷达 LOS 的夹角。

方法链路：

- SISO 基线：对每个 range bin 通过 beat frequency 和初始相位估计得到 `φ(q,m)`，再用 `λ_c / 4π` 转位移。这个方法隐含前提是目标散射点在 range 维可分。
- ASPD：每个 chirp 做 Range FFT，扣除相邻 chirp 的静态谱以抑制静态杂波；通过热图局部最大值追踪目标 range ridge；当 ridge 变化超过一个 range resolution 时切段，重新计算该段 demodulation beat frequency 和相位。
- Full-field：2TX/4RX TDM-MIMO 形成 8 个 virtual channels；每个 chirp 先对各通道做 range FFT，再做 angle estimation/2D-FFT 得到 range-angle heatmap；对每个目标的 `(range index, angle index)` 跟踪慢时间相位，解缠后按几何关系做 LOS correction。
- 实验里同 range bin 的线性滑台和振动激振器用 range profile 无法准确隔离，但在 range-angle joint dimension 可以分开，传统 LFMCW 输出会出现波形大误差、谐波和 coupling frequency components。

实验设置与精度：

- 多尺度实验：77 GHz 雷达，2TX/4RX，带宽 1 GHz，对应 range resolution 15 cm；用 1 m 线性滑台模拟大尺度位移，用 Keyence LK-G80 激光位移传感器提供小尺度 ground truth。
- 大尺度位移：普通 LFMCW 固定 beat frequency 方法随位移变大偏差增大；ASPD 相对误差小于 `1‰`。
- 小尺度位移：线性滑台按微米步进运动，mmSHM 与激光位移传感器吻合，达到微米级精度。
- 同 range bin 多目标实验：带宽 3 GHz、sweep frequency 1000 Hz，range resolution 5 cm，角分辨率约 15°；线性滑台与激振器放在同一距离，参数包括滑台 0.5 mm / 1 mm、速度 3.93 mm/s、激振器 5 Hz。mmSHM 能分别恢复两个目标，传统 SISO LFMCW 则混叠。
- 全场实验：两个线性滑台和一个激振器位于相邻 range profiles，激振器频率覆盖 5、10、50、100 Hz，线性滑台位移覆盖 1、3、10、15 mm 等设置；range-angle joint method 能同步恢复多个目标的位移和频率。
- SHM 应用：两个悬臂梁，每根梁布置三个小角反射器，释放初始位移后测自由振动；用 TDD 做模态参数提取，前两阶模态形状与有限元仿真基本一致。

不足/注意：

- 论文默认角度维可以把同 range bin 目标分开；如果两个散射中心同时落在同一个 range-angle cell，方法仍然会退化成混合 phasor。
- 角分辨率约 15°，对 IWR1843 这类低通道硬件，目标角度间隔、通道校准、TDM phase compensation 和旁瓣泄漏都必须实测验证。
- `cosϕ_q` 几何修正要求已知振动方向与 LOS 的夹角。结构真实振动方向不确定或多方向耦合时，不能简单把它当固定常数。
- 文中 full-field 实验大量使用角反射器增强测点可识别性；自然结构散射点的稳定性、强弱目标共存、相干散射和遮挡问题还需要额外处理。

与你课题关系：这篇最适合支撑“rangeBin 级 beta 拟合会失效”的问题定义。它的表述几乎可以直接转化为你的论点：当多个目标 close to each other 只在 range spectrum 形成一个峰时，单 range bin 提取到的相位是 aliased phase；因此 `beta` 如果基于这个相位拟合，就不是某个物理测点的 LOS-to-structure conversion factor，而是混合散射的等效系数。你的改进可以从这里接出：先把 rangeBin target 升级为 range-angle target，再对每个角度隔离后的 complex slow-time signal 单独评价和拟合 beta。

### Full-field 3D Displacement Measurement via Microwave Sensing

文件：`Full-field 3D displacement measurement via microwave sensing.pdf`

用途：作为“从 LOS 位移/几何修正系数走向结构坐标系 3D 位移”的主参考。它不只是继续做 range-angle full-field，而是用三个非共线 microwave transceivers 同时观测同一批测点，把三个 LOS 位移重构为 device coordinate system（DCS）和 structural coordinate system（SCS）中的 3D displacement。

核心创新：

- 提出三雷达 full-field 3D displacement measurement 系统，用三个非共线 transceivers 和三个非共线 reference targets 分别建立 DCS 与 SCS。
- 提出测点自动匹配方法：先用参考目标确定每个雷达 heatmap 的 zero-degree plane normal vector，再把 SCS 中已知的测点坐标投影到每个雷达的 range-angle heatmap，得到每个雷达视角下的 `(R_pq, θ_pq)`。
- 将三路 LOS displacement time series 通过全微分重构为 DCS 中的 3D 位移，再用旋转矩阵 `M` 从 DCS 转到 SCS，得到结构坐标系下的 `dx_S, dy_S, dz_S`。
- 论文强调工程上真正关心的是 SCS 中的 3D 位移，而不是单雷达 LOS 位移或 DCS 下的中间结果。

方法链路：

- 单雷达 1D full-field：每个 transceiver 通过 range-angle joint positioning 感知多目标，并用相邻 sweep 的 interferometric phase difference 得到 LOS 位移增量 `Δx(l,i) = λ_c [φ(l,i)-φ(l,i-1)] / 4π`。
- 坐标建立：DCS 由三个非共线雷达定义，SCS 由结构附近三个非共线参考目标定义。SCS 可以对应桥梁纵向、横向、竖向等实际结构方向。
- 测点匹配：对测点 `Q=(x_Sq,y_Sq,z_Sq)`，根据雷达 `p` 在 SCS 中的位置计算距离 `R_pq`，再用该雷达 zero-degree plane normal vector 计算 `θ_pq`。这样每个结构测点可以自动映射到 A/B/C 三个雷达的 heatmap 中。
- 3D 重构：目标坐标是三个距离 `R_Aq,R_Bq,R_Cq` 的函数；固定雷达位置后，对这些函数求全微分，把三路 LOS 位移 `dR_A,dR_B,dR_C` 线性组合为 DCS 位移 `dx_D,dy_D,dz_D`。
- SCS 转换：用三个雷达在 SCS 中的位置构造 DCS 基向量，得到旋转矩阵 `M`，再把 DCS 位移转换为 SCS 位移。

实验设置与精度：

- 仿真：77 GHz，带宽 4 GHz，256 个 transmit-receive channels，等效位移采样频率 100 Hz，400 帧；四个测点分别做 0.1 mm、1 mm、10 mm 量级的 S/J/T/U 形轨迹，运动平面覆盖 XOY、XOZ、YOZ 和法向量为 `(1,1,0)` 的斜平面。
- 仿真精度：测点 1、2、4 在各轴的 displacement time series RMSE 均小于 `1e-3 mm`；测点 3 最大位移 10 mm，但各轴 RMSE 仍小于 `5e-3 mm`，约为最大位移的 0.05%。
- 实验室验证：三个非共线 transceivers 架在光学平台前，五个角反射器中三个作 reference targets，两个作 measuring points；77 GHz，带宽 4 GHz，等效采样频率 50 Hz，86 个 transmit-receive channels。
- 实验室位移设置：测点 1 分别沿 SCS 的 X/Y/Z 方向做 1 mm 往复；测点 2 沿 `(1,-1,0)` 方向做 10 mm、1 mm、0.1 mm 往复；每组 10 次独立重复，间隔至少 10 min。
- 实验室精度：表 5 中测点 1 在 1 mm 设置下平均约 1.0086、1.0010、0.9909 mm，标准差分别约 0.0009、0.0011、0.0040 mm；测点 2 在 10 mm、1 mm、0.1 mm 设置下平均约 10.0065、0.9931、0.0985 mm，标准差约 0.0073、0.0028、0.0005 mm。最大相对误差为 1.5%，发生在 0.1 mm 量级，绝对误差仅约 1.5 μm。
- 桥梁场测：在校园人行悬索桥上布置 10 cm 角反射器建立 SCS 和三个桥面测点，三雷达在岸边非共线布置；人踩踏激励后重构三测点 3D 位移。中跨点竖向位移最大，与结构预期一致；测点 2 的 Z/Y 方向频谱与安装在桥面/侧面的加速度计频率成分一致。

不足/注意：

- 系统成本与实现复杂度明显高于单 IWR1843：需要三个同步 transceivers、非共线布置、参考目标、测点坐标或结构模型。
- 方法假设每个目标在每个雷达的 range-angle heatmap 中可被可靠匹配；如果某个视角下目标被遮挡、与其他散射点同 cell 混叠，3D 重构会受到污染。
- 实验大量依赖角反射器来定义 reference/measuring points，自然散射点能否稳定作为测点需要单独验证。
- 3D 重构对雷达/参考点坐标、安装角度、SCS 定义和同步误差敏感；论文中也观察到 1D 滑台安装方向偏差会造成 X/Y 分量轻微不一致。
- 它解决的是 LOS 到 3D/SCS 的几何重构，不直接解决单个 range-angle cell 内多个散射中心的 phasor mixture。这个问题仍需在单雷达或每个雷达视角内先做 target isolation。

与你课题关系：这篇适合支撑 `beta` 的升级方向。传统做法把 `beta` 当一个经验标量，用加速度/位移参考去拟合；这篇说明更物理的路线是先明确测点在结构坐标系的位置和每个雷达 LOS 方向，再通过几何关系把 LOS 位移转换到结构坐标系。对你的问题，可以把 `beta` 从“rangeBin 经验拟合系数”改写为“target-aware 几何投影系数 + 小范围校准残差”。如果只有单雷达，就至少应估计测点 AoA 和结构振动方向，形成 `cosϕ` 类几何约束；如果多雷达可用，则可以进一步用多 LOS 方程替代单一 beta。

### Multitarget Vital Signs Detection Based on MIMO-FMCW Radar

文件：`Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`

用途：作为“range-angle target -> beamformed slow-time phase signal”的最直接参考，虽然场景是生命体征而不是结构位移。

创新点：将 Range FFT、Capon angle estimation、2D-CFAR、DBSCAN 和 LCMV beamforming 串成多目标生命体征检测链路；先在 range-angle map 上定位每个目标，再用 LCMV 数字波束形成得到每个目标的 slow-time signal。

方法论：IF 信号先做 Range FFT 和 Capon 角度估计生成 range-angle map；用 2D-CFAR 和 DBSCAN 提取目标 range/angle；再按 LCMV 准则对每个目标做 beamforming，得到 slow-time 复数信号；最后从相位中提取呼吸和心跳。

不足/展望：论文主要验证人体 RR/HR，未讨论结构静止散射体、多径、强相干散射和长期相位稳定性；实验评价以频率估计误差为主，不是 IQ 圆弧或位移转换因子。

与你课题关系：非常重要。可以把“人体 slow-time phase”直接替换为“结构位移 slow-time phase”，处理链可迁移为 `Range FFT -> Capon/RA map -> CFAR/cluster -> LCMV/DBF -> IQ circle/phase unwrapping`。

### A Real-Time Evaluation Algorithm for Noncontact HRV Monitoring

文件：`A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf`

用途：作为 TI IWR1843 + beamforming + 相位 slow-time 的低通道实证参考。

创新点：用 FMCW 雷达的距离分辨和 MVDR beamforming 提升胸壁相位信号质量，再通过二阶差分/加速度增强心跳、抑制呼吸，并用联合优化切分心跳间隔。

方法论：先按目标距离和方位提取心脏方向 echo signal；对相位解调后的胸壁位移求加速度，突出快速心跳成分；再通过平滑功率和联合优化估计 IBI/HRV。

不足/展望：作者明确指出，多目标同时存在时抗干扰能力有限；即使用 MVDR，受硬件天线数量限制，另一个人体方向的回波不能完全抑制。咳嗽、抓挠、长时间监测也会使模板和加速度波形失效。未来计划用于睡眠监测。

与你课题关系：重要旁证。它说明 IWR1843 这类低通道雷达即使使用 MVDR，也只能降低角度外泄漏，不能保证完全分离近角度/强散射目标。

### Multi-target Range and Angle Detection for MIMO-FMCW Radar with Limited Antennas

文件：`Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`

用途：低天线数 MIMO-FMCW 中做 range-angle 多目标分离的核心参考。

创新点：针对 sparse random array 的 MIMO-FMCW，提出先用 DFT focusing 检测 range，再在每个 detected range 上用 CS/OMP/SOMP 恢复 angle 的多目标定位方法。

方法论：FMCW IF 信号建模为 range 和 angle 的二维频率问题；range 方向用 DFT focusing 和跨 pulse/虚拟通道 binary integration 提高检测概率；angle 方向利用目标稀疏性，用 SMV/MMV compressive sensing 恢复 AoA。

不足/展望：数值实验为主；range 估计和 angle 估计有分步假设；角度恢复依赖网格、稀疏性和阵列字典，实际 IWR1843 的非理想天线、互耦、通道标定误差会影响效果。

与你课题关系：适合作为“同一 rangeBin 内多个不同角度散射体能否拆开”的离线候选。若要保留相位 slow-time，应在每帧或滑窗内恢复角度复幅度，或用估计角度再回到 DBF/LCMV 输出复数序列。

### Multi-target Range, Doppler and Angle Estimation in MIMO-FMCW Radar with Limited Measurements

文件：`Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`

用途：作为上一篇的扩展版，覆盖 range-Doppler-angle 三维估计和有限测量条件。

创新点：提出 MIMO-FMCW 中用随机 sparse linear array 和稀疏 chirp 子集同时降低空间和 slow-time 测量数；用 DFT focusing / Range-OMP 做 range，用 2D-CS 做 Doppler-angle 联合估计，并给出恢复保证。

方法论：fast-time、slow-time、spatial domain 分别对应 range、Doppler、angle 维度；Range-OMP 可提升 range 分辨率并降低计算量；2D-OMP 直接估计 Doppler-angle support，比 1D vectorized OMP/BP/LASSO 更高效。

不足/展望：作者在未来工作中明确指出，实际硬件的相位噪声、RF 非线性、天线互耦、多径、遮挡、clutter，以及大孔径下的空间宽带/近场效应都会造成模型失配；后续需要 calibration-aware、model-adaptive 和 robust dictionary。

与你课题关系：适合进阶。对倒挂雷达，Doppler 维可类比为 slow-time 结构运动维，但静止参考散射体随雷达运动产生相干相位变化，是否满足稀疏独立模型需要实测验证。

### Enhanced Two-Stage SBL for Multi-Vehicle Localization with MIMO-FMCW Radar

文件：`Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf`

用途：SBL 做 joint range-angle 多目标超分辨定位的最新进展参考。

创新点：提出 coarse-to-fine 两阶段 SBL：先在稀疏粗网格上找潜在目标区域，再在局部高分辨网格迭代细化；加入 Sigmoid local maximization 缓解字典相干旁瓣干扰，并用 iterative interference cancellation 降低多目标互扰。

方法论：将目标分布看成 range-angle 稀疏图；SBL 的 ARD 机制自动促进稀疏，不需要预先知道目标数；局部细网格和干扰消除用于提升多车场景下的 range/angle 精度。

不足/展望：作者明确说当前实现优先定位精度而非速度，未来需 GPU 并行和 GAMP-SBL 混合算法满足嵌入式实时要求。真实实验 SNR 也无法直接精确量化，只能近似初始化。

与你课题关系：适合作为离线上限方法。若要用于相位跟踪，需要额外验证每个 sparse component 的复幅度 slow-time 是否连续稳定，不能只看单帧定位误差。

### Super-Resolution Angle Estimation Using LC-MUSIC-Based RELAX

文件：`Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf`

用途：MUSIC/RELAX 类超分辨角度估计代表，可作为 Angle FFT 的对照算法。

创新点：提出 LC-MUSIC-based RELAX，即先用 RELAX/CLEAN 思路逐个估计和消除目标，再结合低复杂度 MUSIC 提高 MIMO-FMCW 的 DOA 分辨力。

方法论：在 MIMO 虚拟阵列上估计角度谱；对近角度多目标，RELAX 用迭代方式降低强目标对弱目标的污染，LC-MUSIC 用子空间结构提高角度分辨率。

不足/展望：主要输出角度峰值/谱峰，不天然输出长期稳定的复数 slow-time；对目标数、协方差估计、相干源和通道标定敏感。论文显示 12 虚拟阵元仿真中 2 度目标可被区分，但这类结果需要谨慎迁移到 IWR1843 实测场景。

与你课题关系：适合作为进阶对照和“同 rangeBin 是否存在多个角度成分”的诊断工具，不建议作为第一主链路。

### Extrapolation-RELAX Estimator Based on Spectrum Partitioning for DOA Estimation of FMCW Radar

文件：`Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf`

用途：作为低阵元 FMCW 雷达中用外推和 RELAX 提升 DOA 分辨率的背景参考。

创新点：针对 FMCW radar module 物理阵元数量有限导致角分辨率不足的问题，先对阵列谱进行分区和外推，再用 RELAX 迭代估计多个目标 DOA，目标是提升近角度多目标可分性。

方法论：从 FMCW 雷达的阵列接收数据构造角度谱；通过 spectrum partitioning 降低全局搜索复杂度和强弱目标互扰；用 extrapolation 扩展等效孔径，再用 RELAX 逐个估计并扣除目标成分。

不足/展望：论文主要验证 DOA/角度谱分辨率，不以 slow-time complex signal 的相位稳定性为目标；外推得到的角度分量是否能长期用于微位移相位跟踪，需要额外实测验证。

与你课题关系：有用但不能单独作为强证据。它适合支撑“低通道同 rangeBin 多目标可通过超分辨角度估计被发现/分开”，不适合直接支撑“分离后的相位一定可用”。

### An Implementation Scheme of Range and Angular Measurements via Sparse Spectrum Fitting

文件：`An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting.pdf`

用途：较早但相关的 FMCW MIMO sparse spectrum fitting 实验实现参考。

创新点：实现 4TX/4RX S-band FMCW MIMO 定位雷达，并将 SpSF 用于 range 和 angle 估计；强调在小 snapshots 和低 SNR 下比 MUSIC/Capon 更好。

方法论：TDM-MIMO 形成虚拟孔径；利用信号空间稀疏性进行 sparse spectrum fitting，同时估计目标距离和角度；用仿真和外场双目标实验验证。

不足/展望：作者指出 SpSF 还没有跑在系统板上，后续要移植到板端并优化 switching time 实现实时估计。硬件频段和系统结构与 TI IWR1843 不同。

与你课题关系：可作为 sparse 类早期 baseline。对你的场景，核心价值是说明 sparse 方法在小 snapshot/低 SNR 下可能有优势，但实时性和板端实现仍是问题。

### Frequency-Spatial Adaptive DBF for Range-Angle Decoupling

文件：`Frequency-Spatial_Adaptive_Digital_Beamforming_Technique_for_Range-Angle_Decoupling_With_High-Resolution_MIMO_Radar.pdf`

用途：range-angle coupling 处理和 adaptive DBF 的最新参考。

创新点：针对宽带大孔径 MIMO 雷达中的 range-angle coupling，提出 FSADBF：根据 IF 信号的 frequency-spatial phase 生成频率相关 steering vector，使每个离散频率分量独立做角度估计，缓解 off-boresight 下角度单元迁移。

方法论：不再用窄带固定 steering vector，而是考虑不同频率分量的相位差；先把目标聚焦到正确 angular cell，再对每个 angle cell 做 Range FFT，从而避免 RAC 导致目标在 range-angle map 中扩散。

不足/展望：实验使用 TI AWR2243 cascaded radar、86 个半波长阵元、43λ 孔径，远大于 IWR1843；论文场景是高分辨大孔径雷达，不是低通道单芯片。

与你课题关系：理论动机有用，尤其用于解释“range-angle map 中目标扩散/迁移”。但 IWR1843 孔径小，RAC 不是首要矛盾，不能作为第一阶段主算法。

### A Decoupling-Based Approach for Wideband XL MIMO-FMCW Radars

文件：`A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars.pdf`

用途：range-angle coupling、overlapping target cluster 和 XL-MIMO 宽带效应的理论参考。

创新点：将 joint range-angle estimation 改写为 decoupled sequential frequency estimation；用 OMP 做 1D sparse recovery，先估一个维度再条件估另一个维度；扩展到 spatial wideband XL-MIMO，处理 range squint、beam squint、RAC 造成的重叠目标响应。

方法论：对空间窄带 MIMO-FMCW，把 IF 信号表示为二维复指数；对 XL-MIMO 宽带场景，先估 DoA，利用低索引性质补偿空间宽带效应，再估 range，从而分离因 RAC 重叠的目标簇。

不足/展望：仿真和理论为主，文中也提示详细数值分析仍在更新；假设 XL 阵列和宽孔径，与 IWR1843 的小孔径/低通道差距较大。

与你课题关系：适合写“同一 range-angle cell 重叠和 range-angle coupling 的理论背景”，但不适合作为 IWR1843 主算法。

### Burg-Aided 2D MIMO Array Extrapolation

文件：`Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution.pdf`

用途：低物理阵元下通过阵列外推提升角分辨率的候选方法。

创新点：将 Burg autoregressive extrapolation 从 1D 扩展到 2D MIMO 虚拟阵列，用外推/插值生成更大等效阵列，以较少硬件获得更细角分辨率。

方法论：基于 AR/Burg 算法预测虚拟阵列缺失或外推位置的数据，再对外推后的 1D/2D 阵列做成像；通过 77 GHz 仿真和实验验证 range-azimuth-elevation 数据。

不足/展望：作者指出外推因子过高、近场转变、目标非点状等都会限制有效性；未来要结合多种 beamforming 方法生成道路环境增强图像。

与你课题关系：可作为“提高 IWR1843 有效孔径”的进阶想法，但对相位连续性风险较高。外推生成的通道是模型预测值，是否适合微位移相位跟踪必须单独验证。

### Non-Uniform Virtual Array Position Optimization and NN Imaging Enhancement

文件：`Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement.pdf`

用途：非均匀虚拟阵列 + 神经网络旁瓣抑制的成像增强参考。

创新点：用遗传算法优化非均匀 MIMO Tx/Rx 位置，以更大孔径提升角分辨率；再用 CNN 抑制非均匀阵列引入的旁瓣伪影；训练数据主要由 radar target model 仿真生成，并用 TI AWR cascade 实测验证。

方法论：保持 Tx/Rx 数量不变，通过非均匀阵列扩展孔径；先优化阵列布局降低旁瓣，再用神经网络把旁瓣污染的 range-angle image 还原为更干净图像。

不足/展望：真实测量中仍有残余旁瓣，作者认为是支架等额外散射没有被训练模型覆盖；未来需要更多样、更贴近真实雷达工况的训练模型。

与你课题关系：不适用于已有 IWR1843BOOST 硬件布局优化，但可作为“学习法对未建模散射很敏感”的证据。相位跟踪不应直接依赖 NN 输出的 sharpened image。

### Li et al. Azimuth Super-Resolution for FMCW Radar in Autonomous Driving

文件：`Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf`

用途：学习型 azimuth super-resolution 的重要 CVPR 参考。

创新点：提出 ADC-SR，从少数接收通道的 complex ADC signal 直接预测/幻觉未采集天线信号；相比从 RA/RAD magnitude map 做超分，ADC 输入保留更多通道间关系，参数量比 RAD-SR baseline 少约 50 倍；Hybrid-SR 结合 ADC-SR 和 RAD-SR 进一步提升检测。

方法论：输入低通道 raw ADC/complex radar signal，输出额外虚拟接收通道或高分辨 RAD/RA map，再用于下游 object detection。论文还提出 Pitt-Radar 数据集，并在 RADIal 等数据上验证。

不足/展望：目标是自动驾驶检测 mAP，不是物理相位连续性；“hallucinated antennas” 可能改善图像，但不保证微位移相位真实可靠。

与你课题关系：只适合进阶。可以用于生成候选 range-angle ROI 或分离能力上限，但不建议直接把网络输出相位用于结构位移恢复。

### AAETR: Angle of Arrival Estimation with Transformer

文件：`Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf`

用途：Transformer/gridless AoA 的学习型新方法参考。

创新点：提出 AAETR，作为 fully differentiable transformer-based AoA model；声称比 IAA 等传统超分辨方法更高效，具有 sparse、gridless angle-finding 能力，并可从仿真数据 zero-shot 迁移到真实自动驾驶雷达数据。

方法论：输入低层雷达数据表示，如 RD cube，经 AoA 模块输出 RAD/BEV 特征；用检测式 transformer 架构预测稀疏角度成分，避免高密度角度网格搜索和 straddling loss。

不足/展望：评价主要围绕 BEV feature、object detection/segmentation 和 sidelobe suppression；没有证明输出复数相位对微位移连续跟踪是物理一致的。

与你课题关系：可作为 learning-based AoA 文献综述，不建议投入大量时间做主方法，除非后续有自采标定数据和相位一致性验证。

### MIMO FMCW Radar with Doppler-Insensitive Polyphase Codes

文件：`MIMO FMCW Radar with Doppler-Insensitive Polyphase.pdf`

用途：MIMO waveform / 虚拟阵列相位一致性背景资料。

创新点：为多发射 FMCW 雷达设计 Doppler-insensitive polyphase codes，使不同 TX 的编码在 Doppler mismatch 下仍保持低互相关，从而改善 MIMO VAA 角度估计。

方法论：用模拟退火优化 polyphase code，调制到 successive chirps；在 range-Doppler processing 后做 VAA beamforming 和 angle estimation。

不足/展望：偏 waveform/code design，不是 AoA 后处理；IWR1843 常用 TDM-MIMO，用户通常不能自由实现复杂编码波形。

与你课题关系：用于提醒：虚拟阵列拼接依赖不同 TX chirp 间的相位一致性。倒挂位移监测中若结构运动或 chirp 间相位补偿不当，会污染 angle FFT/DBF 的复数相位。

### High-Resolution Localization Using Distributed MIMO FMCW Radars

文件：`High-Resolution Localization Using Distributed MIMO FMCW Radars.pdf`

用途：多雷达分布式定位和低角分辨率补偿的参考。

创新点：不是传输 raw signal 或 MUSIC spectrum，而是各雷达只上传本地 range-angle 位置估计，再在统一坐标系中按可达分辨率加权平均，从而降低通信量和复杂度。

方法论：每个 FMCW MIMO 雷达可用 2D FFT 或 2D MUSIC 得到本地 range/angle；分析 range/angle 误差如何投影到统一坐标系；根据每个雷达布置和分辨率给权重。

不足/展望：实验重点是单目标，用于隔离加权平均和布置影响；多目标扩展需要数据关联/gating。

与你课题关系：不是单 IWR1843 主方法。但它明确指出 FMCW MIMO 雷达通常因天线数有限导致 azimuth resolution 低，这可作为低通道限制的背景引用。

### High-Resolution and Accurate RV Map Estimation by Sparse Bayesian Learning

文件：`High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning.pdf`

用途：SBL 在 FMCW range-velocity map 上做高分辨估计的基础参考。

创新点：不用 DFT 字典，而是从宽带 FMCW 模型构造 sparse dictionary，缓解宽带/高速目标时 DFT 字典模型失配导致的 range bias 和分辨率下降；提出快速边际似然最大化版本降低计算量。

方法论：把 RV map 看作稀疏表示问题，SBL 通过层级先验自适应学习超参数，不需要手动调 LASSO 正则项；FSBL-RV 用 fast marginal likelihood maximization 加速。

不足/展望：只处理 range-velocity，不直接处理 angle；可借鉴 SBL 建模思想，但不能直接解决同 rangeBin 多角度散射体。

与你课题关系：作为 SBL 方法论背景，说明“字典必须符合 FMCW 物理模型”。如果做 range-angle SBL，也应避免简单套 DFT 字典而忽略 IWR1843 阵列几何和校准误差。

### Joint Estimation of Channel, Range and Doppler for FMCW Radar with SBL

文件：`Joint_Estimation_of_Channel_Range_and_Doppler_for_FMCW_Radar_with_Sparse_Bayesian_Learning.pdf`

用途：SBL 与先验信息融合、协同感知的参考。

创新点：将 SBL 用于 76 GHz FMCW beat frequency signal 的 channel、range、Doppler 联合估计，并允许把邻车 CAM 信息作为 range/Doppler prior 融入 SBL，提高弱目标检测和降低虚警。

方法论：beat frequency signal 中每个目标对应一个正弦分量；SBL 用先验和稀疏恢复提升目标峰值 SNR，相比 FFT+CFAR 在密集/clutter/干扰环境中更可靠。

不足/展望：偏 ADAS/ISAC 协同感知，不做 angle；硬件参数是 1TX 等设置，不接近 IWR1843 MIMO AoA 链路。

与你课题关系：可作为“有外部先验时 SBL 可增强弱目标”的参考。你的外部先验可能来自加速度、已知结构运动频段或历史稳定 angle gate，而不是 CAM。

### Variational Signal Separation for Automotive Radar Interference Mitigation

文件：`Variational Signal Separation for Automotive Radar Interference Mitigation .pdf`

用途：FMCW 干扰/动态干扰和 sparse probabilistic signal separation 参考。

创新点：把目标回波和互扰信号联合建模为多个 line spectral estimation 问题；受 SBL 启发，构建 Gamma-Gaussian 层级先验，并用 variational EM 联合估计和逐步抵消干扰。

方法论：目标 echo 是 coherent object channel，干扰是 non-coherent interference channel；算法迭代做 object estimation 和 interference estimation，以接近无干扰情况下的目标参数估计性能。

不足/展望：假设每个 ramp 至多一个干扰 chirp，且干扰覆盖接收机 AAF 全通带；作者指出这些假设限制了实际场景泛化，需要进一步验证不同干扰场景。

与你课题关系：不是 AoA 主文献，但可用于处理倒挂场景中的动态干扰、车辆/行人强回波或雷达互扰。可作为异常检测和数据清洗的进阶方向。

### Millimeter Wave Real-Time Tracking and Imaging Based on Virtual MIMO Array

文件：`Millimeter_Wave_Real-Time_Tracking_and_Imaging_of_Moving_Objects_Based_on_Virtual_MIMO_Array_and_State_Vector_Prediction.pdf`

用途：3TX/4RX 类低通道虚拟 MIMO 点云实时成像参考。

创新点：用 3 x 4 虚拟 MIMO 阵列提取目标点云，再用 Kalman filter 预测和跟踪目标状态，实现约 100 ms 延迟的人体移动目标点云成像。

方法论：由虚拟阵列 echo data 提取 range、angle、velocity 等空间信息，映射到笛卡尔坐标；用常加速度模型 Kalman filter 平滑/预测点云轨迹。

不足/展望：作者指出与合成孔径相比，点云成像分辨率较差，少天线导致点云密度不足，不能完整显示目标形状；未来更合理的 12 x 16 阵列会改善效果。

与你课题关系：可作为低通道实时性的参考，但它更偏点云/跟踪，不保留稳定复数相位序列。不要把点云轨迹直接等同于你的结构位移相位测量。

### Burg / Nonuniform / Learning Imaging Papers as a Group

文件：
- `Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution.pdf`
- `Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement.pdf`
- `Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf`
- `Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf`

用途：共同支撑“低通道数雷达可以通过外推、稀疏、学习等方式增强角分辨率，但这些增强未必适合相位测量主链路”的判断。

共同不足：这些方法大多优化图像清晰度、角度峰值、检测性能或 BEV 下游任务，而不是验证 beamformed complex slow-time 的相位连续性。对结构位移监测，必须额外检查 IQ 圆弧残差、相位解缠稳定性和转换因子滑动稳定性。

## 主题索引

- TI / IWR 工程基线：优先读 `TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`。
- 同 rangeBin 多目标分离并输出可用相位的强证据：优先读 `Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`、`Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf`、`Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf` 和 `Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`。
- 结构 SHM 全场毫米波振动测量主线：优先读 `Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`；它最直接说明 same rangeBin 多目标耦合和相邻 rangeBin 干扰为什么会破坏 range-bin phase。
- LOS 位移到结构坐标/几何转换：优先读 `Full-field 3D displacement measurement via microwave sensing.pdf`；它适合支撑把经验 `beta` 改成 target-aware geometry-constrained conversion。
- 能输出 slow-time phase 的 range-angle 链路：优先读 `Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf` 和 `A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf`。
- 低通道数 / limited antennas / CS：读 `Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`。
- 加入 Doppler/slow-time 维度的有限测量估计：读 `Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`。
- SBL joint range-angle：读 `Enhanced Two-Stage Sparse Bayesian Learning Algorithm ... .pdf`。
- MUSIC/RELAX 超分辨角度对照：读 `Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX ... .pdf` 和 `Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf`。
- Range-angle coupling / 宽带大孔径理论：读 `Frequency-Spatial_Adaptive_Digital_Beamforming...pdf` 和 `A Decoupling-based Approach ... XL MIMO-FMCW Radars.pdf`。
- 学习型 AoA / azimuth super-resolution：读 `Li_Azimuth_Super-Resolution...pdf` 和 `Angle of Arrival Estimation with Transformer...pdf`。
- 阵列外推/非均匀阵列：读 `Burg-Aided 2D MIMO Array Extrapolation...pdf` 和 `Non-uniform virtual array position optimization...pdf`。
- 干扰/动态异常分离：读 `Variational Signal Separation for Automotive Radar Interference Mitigation .pdf`。

## 对倒挂式 IWR1843 位移监测的建议

1. 第一阶段实现 `Range FFT + Angle FFT/Bartlett DBF`
   - 保存 raw ADC、Range FFT 后 per-virtual-channel 复数 cube、TDM phase compensation 后 virtual array cube、range-angle complex output。
   - 对每个候选 `range-angle target` 计算 IQ 圆弧残差、相位解缠跳变次数、主峰/次峰比和角度间隔。
2. 第二阶段实现 `Capon/MVDR` 或 `LCMV`
   - 用校准段或慢滑窗估计 covariance，加入 diagonal loading，避免每帧权重剧烈变化引入伪相位。
   - 与 Bartlett 输出比较：看 angle gate 后 IQ 圆弧是否更薄、加速度-雷达转换因子拟合残差是否下降、滑动窗口转换因子是否更稳定。
3. 转换系数 `beta` 的处理建议
   - 不要在原始 rangeBin 上直接拟合 `beta`。如果一个 rangeBin 里有多个散射中心，该 bin 的复数回波是多个 phasor 的叠加，拟合出的 `beta` 只是混合等效系数，换窗口、换姿态或散射强度变化就会漂移。
   - 先把候选点升级为 `range-angle target`：对每个目标保留 angle-gated/beamformed complex slow-time，再分别做 IQ 圆弧、相位解缠、与加速度/参考位移的相干性检验。
   - 能估计 AoA 和结构振动方向时，优先构造 `cosϕ` 几何投影系数，把 `beta` 限制在几何合理范围内；经验拟合只作为残差校准，而不是自由标量。
   - 如果多个角度目标不可分，直接标记该 rangeBin 为 beta 不可信，避免把不可观测混叠硬拟合成稳定系数。
4. 离线候选和分离上限分析
   - OMP/LASSO/SBL/MUSIC/RELAX 用于判断同一 rangeBin 是否有多个角度成分，以及估计“可分离上限”。
   - Learning-based SR/array extrapolation 只能作为 ROI 提示或图像增强，不应直接产出位移相位，除非完成相位物理一致性验证。

最终原则：凡是不能输出或保留 `complex slow-time signal` 的方法，只能作为目标选择/角度诊断工具；真正进入位移恢复链路的，应是经过 angle gate / beamforming 后的复数序列。

<!-- FULL_FILE_INDEX:START -->

## 全量文件索引

| # | 文件 | 论文题名 | 索引说明 |
|---:|---|---|---|
| 1 | `A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars.pdf` | A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars | 波束形成、角度解耦或旁瓣抑制，用于同距离目标分离。 |
| 2 | `A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf` | A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring | MIMO FMCW 角度、目标检测或雷达成像方法，用于 AoA 链路对照。 |
| 3 | `An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting.pdf` | An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 4 | `Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf` | Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 5 | `Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution.pdf` | Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 6 | `Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf` | Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multivehicle Precise Detection and Localization With MIMO-FMCW Radar | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 7 | `Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf` | Extrapolation-RELAX Estimator Based on Spectrum Partitioning for DOA Estimation of FMCW Radar | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 8 | `FMCW_multiple-input_multiple-output_radar_with_iterative_adaptive_beamforming.pdf` | FMCW multiple‐input multiple‐output radar with iterative adaptive beamforming | 波束形成、角度解耦或旁瓣抑制，用于同距离目标分离。 |
| 9 | `Frequency-Spatial_Adaptive_Digital_Beamforming_Technique_for_Range-Angle_Decoupling_With_High-Resolution_MIMO_Radar.pdf` | Frequency-Spatial Adaptive Digital Beamforming Technique for Range-Angle Decoupling With High-Resolution MIMO Radar | 波束形成、角度解耦或旁瓣抑制，用于同距离目标分离。 |
| 10 | `Full-field 3D displacement measurement via microwave sensing.pdf` | Full-field 3D displacement measurement via microwave sensing | 全场/多尺度微动测量，关注 range-angle 联合目标和多点相位跟踪。 |
| 11 | `High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning.pdf` | High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 12 | `High-Resolution Localization Using Distributed MIMO FMCW Radars.pdf` | High-Resolution Localization Using Distributed MIMO FMCW Radars | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 13 | `Joint_Estimation_of_Channel_Range_and_Doppler_for_FMCW_Radar_with_Sparse_Bayesian_Learning.pdf` | Joint Estimation of Channel, Range, and Doppler for FMCW Radar with Sparse Bayesian Learning | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 14 | `Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf` | Azimuth Super-Resolution for FMCW Radar in Autonomous Driving | MIMO FMCW 角度、目标检测或雷达成像方法，用于 AoA 链路对照。 |
| 15 | `Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf` | Research_9787484 1..13 | 多目标生命体征或微动分离，重点关注 range-angle 定位后复数慢时间相位提取。 |
| 16 | `Millimeter_Wave_Real-Time_Tracking_and_Imaging_of_Moving_Objects_Based_on_Virtual_MIMO_Array_and_State_Vector_Prediction.pdf` | Millimeter Wave Real-Time Tracking and Imaging of Moving Objects Based on Virtual MIMO Array and State Vector Prediction | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 17 | `MIMO FMCW Radar with Doppler-Insensitive Polyphase.pdf` | MIMO FMCW Radar with Doppler-Insensitive Polyphase Codes | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 18 | `Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf` | Multi-scale and full-field vibration measurement via millimetre-wave sensing | 全场/多尺度微动测量，关注 range-angle 联合目标和多点相位跟踪。 |
| 19 | `Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf` | Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 20 | `Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf` | Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 21 | `Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf` | Multitarget Vital Signs Detection Based on MIMO-FMCW Radar | 多目标生命体征或微动分离，重点关注 range-angle 定位后复数慢时间相位提取。 |
| 22 | `Non-Contact_Vital_Signs_Monitoring_for_Multiple_Subjects_Using_a_Millimeter-Wave_FMCW_Automotive_Radar.pdf` | Non-Contact Vital Signs Monitoring for Multiple Subjects Using a Millimeter Wave FMCW Automotive Radar | 多目标生命体征或微动分离，重点关注 range-angle 定位后复数慢时间相位提取。 |
| 23 | `Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement.pdf` | Non‐uniform virtual array position optimization for MIMO radar and neural network‐based radar imaging enhancement | MIMO 虚拟阵列、阵列外推或波形设计，用于分析角分辨率和通道相位一致性。 |
| 24 | `Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf` | Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar | 多目标生命体征或微动分离，重点关注 range-angle 定位后复数慢时间相位提取。 |
| 25 | `Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf` | Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar  | 稀疏/子空间超分辨角度或 range-angle 估计，适合作为离线对照。 |
| 26 | `TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf` | MIMO Radar (Rev. A) | TI MIMO/AoA 工程基线，说明虚拟阵列、TDM/BPM 和 Angle FFT 数据链路。 |
| 27 | `Variational Signal Separation for Automotive Radar Interference Mitigation .pdf` | Variational Signal Separation for Automotive Radar Interference Mitigation | 雷达干扰与信号分离，用于动态干扰和异常回波处理参考。 |
| 28 | `Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf` | Vital signs monitoring of multiple people using a FMCW millimeter-wave sensor | 多目标生命体征或微动分离，重点关注 range-angle 定位后复数慢时间相位提取。 |

<!-- FULL_FILE_INDEX:END -->
