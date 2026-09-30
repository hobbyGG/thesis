# 文献中的多目标、多方向和多传感器融合方法

本文档专门解释本项目已收集文献中这三个概念的具体实现。需要区分：

- **多目标**：一个雷达视场内有多个反射点，如何定位、分离、跟踪和融合它们；
- **多方向**：一个目标的运动方向与雷达 LOS 不一致，或多个传感器从不同 LOS 观察同一运动，如何恢复目标方向分量；
- **多传感器融合**：雷达、加速度计、应变、光纤、视觉或多雷达数据在哪个处理层被组合。

## 1. 多目标：从“选一个目标”到“多个目标共同参与”

### 1.1 早期/直接基线：先选一个 best target

**Structural displacement estimation using accelerometer and FMCW millimeter wave radar**（Mechanical Systems and Signal Processing，2023）把雷达检测到的多个环境反射峰作为候选，但并不同时使用它们。它先用一段短时同步雷达—加速度数据：

1. 对每个距离峰提取雷达相位；
2. 用加速度得到高频结构位移；
3. 对雷达位移乘以候选转换因子，比较两者高频部分的 RMSE；
4. 选择误差最小的 best target，并确定该目标的 LOS 到结构方向转换因子；
5. 正式运行时只用这个目标做加速度辅助相位解缠，再用 FIR 把雷达位移和加速度位移融合。

这篇论文的多目标处理是“候选目标搜索和最优目标选择”，不是多目标联合观测。它是当前项目需要超越的直接基线。

### 1.2 多目标选择、目标切换和遮挡恢复

**Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer**（Mechanical Systems and Signal Processing，2023）进一步保留多个 good targets，但主要用途仍是遮挡管理：

- 初始短时数据中，对所有距离目标分别估计转换因子和误差，保留多个稳定目标；
- 至少一个目标可见时，使用雷达和加速度进行自适应相位解缠，并在候选目标间切换；
- 所有雷达目标都被车辆等遮挡时，改用应变计经过 ANN 转换得到的位移，再和加速度做 FIR 融合；
- 雷达目标恢复后，重新切回雷达—加速度支路，并用应变位移消除遮挡期间造成的漂移。

因此它的核心是“多目标冗余 + 传感器支路切换”，而不是在同一时刻将多个雷达目标作为共同状态的独立观测。

**Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion**（Mechanical Systems and Signal Processing，2025）把遮挡处理又推进了一步：

- 初始阶段仍然从多个目标中选择 good targets，并离线估计每个目标的方向转换因子；
- 在线阶段只要至少一个目标可见，就做加速度辅助解缠和目标切换；
- 全部目标遮挡时，停止雷达位移更新，但继续记录加速度；
- 目标重新出现后，不依赖遮挡前最后一条已解缠相位，而是使用多个恢复目标的相位构造绝对解缠结果；
- 通过遮挡前后边界位移和遮挡期间加速度，重建遮挡区间的位移，并消除恢复后的漂移。

这篇论文的“多目标”重点是恢复后的绝对相位重建和抗遮挡连续性，仍不是多个目标在每个时刻共同加权估计一个结构状态。

### 1.3 通过距离—角度联合维度分离同距目标

**Multi-scale and full-field vibration measurement via millimetre-wave sensing**（Mechanical Systems and Signal Processing，2022）和相关的 MFMS/mmSHM 路线解决的是另一类多目标问题：目标距离相同或相近，单纯 Range FFT 无法分开。

具体处理为：

1. 对每个 chirp 的 ADC 做距离 FFT；
2. 利用 MIMO 虚拟阵列对接收通道做角度处理；
3. 在 range-angle 联合图中取得每个目标的距离索引和角度索引；
4. 在每个目标的二维频率位置上做相位投影，提取该目标的慢时间相位；
5. 对每个目标分别解缠并恢复位移；
6. 根据目标运动方向与雷达 LOS 的夹角，对每个目标做几何修正。

论文给出的目标位移形式相当于：

\[
q_i=\frac{\lambda}{4\pi\cos\varphi_i}\,\Delta\phi_i,
\]

其中 (arphi_i) 是第 (i) 个目标的运动方向与雷达 LOS 的夹角。它可以同时测量同一距离单元内的多个目标，但各目标仍然是独立输出，不会把它们合成为一个共享结构状态。

### 1.4 全视场多目标微动测量

**Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View**（mmWBat）采用类似的 range-angle 联合相位演化跟踪：

- 多发射、多接收天线形成虚拟阵列；
- 快时间用于距离，天线维用于角度，慢时间用于 chirp/sweep 序列；
- 对 range-angle 热图中的每个目标保留其复数相位历史；
- 通过二维定位和逐目标相位解缠，同时跟踪多个目标的微动；
- 对每个目标按照其 LOS 与运动方向夹角做位移修正。

它还演示了多人生命体征和多个声源的分离，但本质仍是“空间分离后逐目标输出”，没有加速度或应变传感器参与。

### 1.5 IQ 级多目标信号融合

**Measuring Micrometer-Level Vibrations With mmWave Radar**（IEEE Transactions on Mobile Computing，2023）把“多传感器”理解为多 chirp、多接收通道和多目标信号的雷达内部融合，而不是雷达与外部加速度计融合：

- 用 chirp-group generation（CGG）和多接收通道提高有效信噪比；
- 在 range FFT/angle FFT 热图中迭代寻找局部峰，得到目标的距离和角度；
- 对每个 chirp 的复数 IQ 轨迹做圆拟合，估计静态反射造成的圆心偏移；
- 将不同通道的 IQ 轨迹平移、缩放到公共圆后进行 IQ aggregation，再提取相位；
- 对每个目标分别做相位解调和位移输出；
- 用目标角度修正 LOS 位移到已知振动方向的投影。

它解决的是“弱微动、静态杂波和多通道相位质量”问题。多个通道被合成为一个更干净的雷达观测，仍然没有建立多个目标共享的结构状态。

**Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring**（Scientific Reports，2025）采用慢时间均值抵消静止目标能量、Hamming 窗抑制旁瓣，再在多个距离单元用 FFT/all-phase FFT 提取目标相位。实验中可同时看到多个角反射器，但目标主要按距离分离，各目标仍输出自己的 LOS 位移；径向到竖向的转换因子需要安装几何配置，不属于多目标状态融合。

### 1.5 当前项目和这些多目标方法的差异

当前代码的处理位置介于上述两类方法之间：

- 它首先像 mmSHM/mmWBat 一样，在距离—角度图中检测多个目标，并用局部 MUSIC/最小二乘细化 AoA；
- 但它不是像 best-target 方法那样只保留一个目标，也不是只在遮挡时切换目标；
- 当前每个可用目标都产生一个统一后的结构相位观测，之后通过逆方差权重共同更新一个结构 Kalman 状态；
- 目标级 (R_i) 根据后验残差自适应更新，因此目标的作用是“同时观测、按质量加权”，而不是“候选排序”或“目标切换”。

## 2. 多方向：从单雷达投影修正到多 LOS 反演

### 2.1 单雷达多目标的方向修正

**FMCW Radar for Noncontact Bridge Structure Displacement Estimation**（IEEE Transactions on Instrumentation and Measurement，2023）使用单通道 FMCW 雷达进行多点测量：

- 不同距离峰代表不同反射位置；
- 每个峰提取相位变化；
- 由外接 MPU6050 倾角计测量雷达仰角；
- 用仰角把 LOS 位移修正为桥梁目标方向位移；
- 对距离 FFT 中主峰前后的多个频率单元继续提取相位，实现桥面多点位移剖面。

它的方向信息来自外部倾角传感器和固定几何，而不是雷达 AoA。它说明了“相位位移值”和“结构真实方向位移”之间必须有几何关系，但没有多个 LOS 反演完整位移向量。

**Multi-scale and full-field vibration measurement via millimetre-wave sensing**则在同一雷达内对不同目标使用不同 (cosarphi_i) 修正。它的多方向含义是“每个目标各自有一个投影系数”，输出仍是一维位移。

### 2.2 双 LOS 同步反演二维位移

**Transversal Displacement Detection of an Arched Bridge with a Multimonostatic MIMO Radar**（Sensors，2024）没有使用加速度或应变，而是用一个雷达和一个通过射频链路同步的 transponder，形成两个不同站位的同时 LOS 观测：

\[
\begin{bmatrix}
\Delta R_1\\
\Delta R_2
\end{bmatrix}
=
\begin{bmatrix}
\hat u_1\cdot \hat e_y & \hat u_1\cdot \hat e_z\\
\hat u_2\cdot \hat e_y & \hat u_2\cdot \hat e_z
\end{bmatrix}
\begin{bmatrix}
\Delta y\\
\Delta z
\end{bmatrix}.
\]

然后求逆得到桥梁横向和竖向位移，并通过误差传播分析基线 (B)、桥高 (H) 和 LOS 测量误差对方向分量的影响。

这类方法的关键是“空间上增加独立观测方向”，不是对单雷达多个环境反射目标做状态融合。它要求两个接收链路同步，否则两个 LOS 位移不能直接组成同一时刻的方程组。

### 2.3 三雷达全场三维重建

**Full-field 3D displacement measurement via microwave sensing**（Mechanical Systems and Signal Processing，2025）采用三个不共线的微波收发机和三个参考目标：

1. 用三个收发机建立 device coordinate system（DCS）；
2. 用三个结构参考目标建立 structural coordinate system（SCS）；
3. 通过参考目标的距离—角度坐标，求每个收发机到 SCS 的几何变换；
4. 把结构坐标中的测点自动映射到三个雷达各自的 range-angle 热图；
5. 对同一个测点取得三个 LOS 位移；
6. 解三元线性方程得到 DCS 中的三维位移，再变换到 SCS。

这里的“多目标”是多个结构测点的跨雷达匹配，“多方向”是三个不同 LOS 的空间反演，最终确实输出 3D 位移。它和当前项目的差别很大：当前项目只有一个雷达，多个环境目标只用于同一结构主方向的共同观测，不能据此宣称三维重建。

### 2.4 利用几何信息估计雷达自身运动

**Using Geometrical Information to Measure the Vibration of a Swaying Millimeter-wave Radar**（预印本）把两个或多个稳定参考物当作几何基准：

- 平面摆动时，用参考物相对雷达的面积差估计平面位移；
- 空间摆动时，用体积差估计三维自运动幅值；
- 根据多个参考点的变化符号推断粗略摆动方向。

它解决的是“雷达自身在动时如何估计平台运动”，不是结构位移的多 LOS 反演。对当前倒挂雷达场景，它是潜在的自运动补偿方向，但当前代码还没有实现平台位姿估计。

### 2.5 动态几何和相位跳变处理

**Measurement Refinements of Ground-Based Radar Interferometry in Bridge Load Test Monitoring**（Remote Sensing，2024）主要讨论地基雷达的单源处理，但对多方向解释有两个重要做法：

- 用滑动均值或异常值判据检测被车辆等目标造成的相位跳变，删除异常点后用 Akima 插值，再做一维解缠和平滑；
- 不把结构几何固定成初始 LOS，而是把目标变形后的 LOS/竖向距离带入投影关系，同时保留慢变趋势。

它不是多目标共同 Kalman，也没有外部传感器融合，但说明当结构变形或遮挡改变反射几何时，固定投影系数可能失效。

早期的 **Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge** 通过多个距离单元同时观察桥梁梁、塔和缆索，并用三个参考距离单元估计参考点/基座运动，再对目标 LOS 位移做几何补偿。**Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge** 则用多个距离单元和不同雷达视角观察不同轨道，借助激光点云解释几何关系；雷达和加速度计主要做模态结果对照，不是同一状态方程中的融合。

## 3. 多传感器融合：融合发生在不同层次

### 3.1 雷达位移与加速度的 FIR 频带互补

**Structural displacement estimation using accelerometer and FMCW millimeter wave radar**和**Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer**使用的是同一类思想：

- 雷达相位提供直接位移，但会有相位缠绕和噪声；
- 加速度双积分可提供动态变化，但低频漂移严重；
- 初始短时同步数据用于自动选目标和估计 LOS 到结构方向的转换因子；
- 运行时先用加速度辅助相位解缠，再将雷达位移和加速度位移通过互补 FIR 融合；
- 典型设计是雷达保留低频位移基准，加速度补充高频动态成分。

低成本部署论文进一步把雷达、加速度计和微处理器封装在一个小型节点中，采样率约 100 Hz，并在多座桥上验证。它的创新重点是自动初始校准和现场工程化，仍依赖离线转换因子。

### 3.2 雷达、加速度和应变的支路切换

**Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer**不是把三种传感器直接放进同一个 Kalman 状态，而是按雷达可用性切换：

- 雷达可用：雷达相位解缠 + 加速度预测，再用 FIR 融合；
- 雷达全部遮挡：应变经过 ANN 转成位移，再与加速度 FIR 融合；
- 雷达恢复：用应变位移校正遮挡导致的雷达漂移，再恢复雷达支路。

这里的优点是能覆盖长期遮挡，缺点是需要应变网络、ANN 初始训练和多阶段逻辑，系统比当前论文算法复杂得多。

### 3.3 雷达和加速度在 Kalman 状态层融合

**Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring**把融合位置前移到状态预测阶段：

- 状态包含雷达结构相位及其变化率；
- 加速度在状态预测方程中提供相位增量和变化率增量；
- wrapped radar phase 先在预测相位附近进行 (2\pi) 分支校正；
- 校正后的相位再进入 Kalman 更新，同时抑制相位噪声；
- (Q/R) 通过候选搜索或自适应策略调整，并分析滤波器收敛时间；
- 方向转换因子仍通过雷达相位和加速度相位的带通结果离线标定。

这篇论文和当前代码最接近。当前项目的改动不是重新发明 Kalman，而是用当前记录的 AoA 在线产生每个目标的方向系数，并把多个目标统一后共同更新结构相位。

### 3.4 加速度、应变与模态识别响应融合

**Research on Modal Identification of High-Speed Maglev Guideway Structure Based on Data Fusion and Genetic Algorithm**（会议论文，2023）不是雷达相位算法，但对磁浮轨道梁的“多传感器融合”很有参考价值：

1. 用有限元模态矩阵和 Fisher 信息矩阵建立传感器布置优化问题；
2. 用遗传算法选择压电加速度计和 FBG 应变计位置；
3. 现场采集加速度和应变；
4. 用 excitation identification Kalman filter（EIKF）重构未布置位置的结构响应；
5. 对重构响应做 NExT-ERA，识别频率和振型；
6. 用跨中激光位移计验证重构结果。

它的融合层次是“结构响应场重构和模态识别”，而不是雷达 wrapped phase 的实时解缠。对当前项目的启发是：如果以后要从局部位移估计扩展到磁浮轨道梁模态或空间响应场，可以把相位位移、加速度和应变统一到结构响应重构层。

### 3.5 雷达、加速度和分布式光纤的多模态平台

**Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing**（会议论文，2025）实际完成的核心仍是：

- 60 GHz FMCW 雷达 + 三轴 MEMS 加速度计共址；
- 短时同步数据自动选择反射目标并估计方向转换因子；
- 加速度辅助相位解缠；
- FIR 融合雷达位移和加速度；
- 现场用 LDV 作参考。

论文提出进一步利用已有通信光纤做 Rayleigh/OFDR 分布式应变测量，以提供长桥空间连续信息，但这部分属于未来扩展，不应说成已经完成的雷达—光纤实时融合算法。

### 3.7 融合后再估计结构加速度

**Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW millimeter-wave radar**（Measurement，2026）与当前项目的方向相反：它先用短时校准选择雷达目标并估计转换因子，得到雷达位移；然后将雷达位移二阶差分的低频部分与 MEMS 加速度的高频部分通过滑动窗口 FIR 互补融合，最终输出结构加速度。它不是多目标共同相位 Kalman，也不解决当前项目的在线 AoA 转换因子问题。

### 3.8 加速度与应变的状态估计

**Bridge Displacement Estimation Using a Co-Located Acceleration and Strain** 先根据 Euler–Bernoulli 梁关系把应变变成伪静态位移，再用共址加速度的二阶差分做无参考尺度校准，最后在自适应 Kalman 中以加速度作为输入、应变位移作为观测，递推估计位移和速度。它说明“传感器进入状态方程”与“频带互补 FIR”是两种不同的融合方式，但没有雷达相位和 AoA。

### 3.6 磁浮系统级多传感器监测

**Online Monitoring System for Short Stator Maglev Train**和**Technology Innovation in Developing the Health Monitoring Cloud Platform for Maglev Vehicle-Suspension-Guideway Coupling System**展示的是系统层融合：

- 车体加速度、悬浮间隙、电磁铁电流、轨道梁加速度、FBG 应变、位移和温度等多类数据；
- 车载和轨旁系统按统一时间组织数据；
- 做清洗、同步、区段化分析和异常识别；
- 云平台进一步加入数据融合、虚拟传感器和可视化；部分方案还使用 Probabilistic Data Association 关联同一测点数据，用 Particle Filter、协方差一致性和 Bayesian/BDLM 预测做状态诊断。

它们的融合目标是车辆—悬浮—导轨耦合系统状态监控，不是毫米波相位解缠。对当前研究可借鉴的是同步数据组织和结构响应验证，不能直接把云平台或多传感器监控层塞进论文算法核心。

## 4. 各类方法的横向比较

| 文献路线 | 多目标怎么做 | 多方向怎么做 | 传感器怎么融合 | 输出 | 主要限制 |
|---|---|---|---|---|---|
| best-target + FIR | 候选目标中选一个最优目标 | 离线估计 LOS 转换因子 | 雷达位移与加速度按频带互补 | 单点位移 | 需要离线转换因子，不能同时利用多个目标 |
| multi-target + occlusion | 多个 good target，用于切换和遮挡恢复 | 每个目标各自离线 DCF | 雷达/加速度/应变按可用性切换 | 连续单点位移 | 流程复杂，目标不是共同状态观测 |
| range-angle 多目标 | 距离 FFT + 角度 FFT/MUSIC 分离目标 | 每个目标单独几何修正 | 通常只有雷达 | 多目标一维位移 | 没有跨目标状态融合 |
| 双/三雷达几何反演 | 跨设备匹配同一测点 | 多 LOS 线性反演二维/三维 | 多雷达同步 | 向量位移 | 设备多、同步和坐标标定复杂 |
| radar + IMU Kalman | 通常单目标 | 转换因子仍离线标定 | 加速度进状态预测，雷达进状态更新 | 连续相位/位移 | 前序方法存在离线阶段 |
| 当前项目 | 多个目标同时作为候选观测 | 单雷达多 AoA 投影统一 | ADXL 原生时间预积分 + 多目标雷达更新 | 共同结构相位/主方向位移 | 尚无三维反演、在线遮挡跟踪和平台自运动估计 |

## 5. 对当前论文创新表述的直接启发

当前项目不应声称首次提出“多目标”“多方向”或“雷达—加速度融合”。这些概念在文献中已有多种实现。更准确的贡献组合是：

1. 前序 acceleration-aided Kalman 方法依赖离线方向转换因子；当前方法由当前记录的 AoA 直接生成目标级 (eta_i)，取消现场专门的转换因子估计阶段；
2. 前序多目标方法主要用于 best-target 选择、目标切换或遮挡恢复；当前方法将多个目标作为同一结构相位的同时观测，并用逆方差和自适应 (R_i) 共同更新；
3. 前序多方向方法通常依赖倾角计、双雷达或三雷达；当前方法不做完整三维反演，而是用单雷达多个 AoA 对不同 LOS 投影做共同主相位统一；
4. 前序多传感器方法多采用 FIR 频带互补或遮挡时支路切换；当前方法把 ADXL 原生时间区间预积分放进 Kalman 预测，并让多目标雷达观测在同一状态层更新；
5. 系统贡献是把真实采集和论文参数仿真场景统一成同一个 capture package，使上述方法能够在同一算法入口下重复验证。

因此，当前项目的真正研究位置不是“发明多目标、多方向、多传感器融合这些大概念”，而是把它们组合成一个面向高刚度磁浮轨道梁、单个倒挂 FMCW 雷达、环境多反射目标和加速度辅助解缠的可直接运行方法。
