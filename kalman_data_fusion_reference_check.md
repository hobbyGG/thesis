# Kalman / 数据融合参考文献补查

本文档专门检查“后续若使用加速度传感器 + 毫米波雷达做数据融合，尤其涉及 Kalman 滤波、状态空间、FIR/互补融合、多率传感器融合时，非 00 核心文献和无关目录中是否有可参考文献”。

## 结论

当前真正值得纳入后续融合章节的文献主要还在 `ref_papers` 根目录中，不在 `99_irrelevant_literature` 中。被移入无关目录的文献里确实有若干“sensor fusion / Kalman / mmWave radar”关键词，但多为车载感知、雷达相机目标跟踪、自动驾驶综述或移动载具桥梁检测，和“结构测点加速度 + 毫米波雷达位移融合”距离较远，暂不建议移回核心参考。

建议后续写作时把融合文献分成三层：

1. 直接核心：00 文件夹中 Ma/Zhang/Sohn 系列雷达+加速度论文。
2. 方法支撑：Kalman、状态空间、多率传感器融合、strain/vision/GNSS+accelerometer 融合。
3. 可选旁证：车载雷达/相机 Kalman 融合等，只在需要解释非线性滤波或异构传感器关联时少量引用。

## 强烈建议参考

### Multi-rate Kalman filtering for structural dynamic response reconstruction by fusing multi-type sensor data with different sampling frequencies

文件：`ref_papers/Multi-sensor and Multi-frequency Data Fusion for Structural Health Monitoring.pdf`

为什么值得用：这篇标题文件名不够准确，但正文实际是 Engineering Structures 2023 的 multi-rate Kalman filtering (MRKF) 文献。它直接处理“高采样加速度 + 低采样位移传感器”的融合问题，和后续“雷达位移低频/加速度高频融合”非常接近。

方法论：先把结构系统写成状态空间方程；根据当前时刻可用传感器类型切换观测方程。只有加速度可用时用 acceleration observation 更新；低频位移观测到来时把 displacement + acceleration 一起融合。再用 RTS smoother 在精度和实时性之间折中。

可借鉴点：

- 多率数据不必先强行重采样到同一频率，可以通过不同观测方程直接进入 Kalman。
- 加速度用于保留高频动态，位移传感用于约束低频漂移。
- 对本文若使用毫米波雷达低频/准静态位移 + 加速度高频响应，可以借鉴 MRKF 的观测切换写法。

关键结果：实验中用 iPhone 视觉位移 60 fps 和加速度 1000 Hz 融合；MRKF + RTS 的位移误差相比 acceleration-only 明显降低，相比传统低频下采样融合降低超过 90%。

建议状态：建议作为“Kalman 多率融合方法支撑”重点引用。

### Reference-Free Displacement Estimation of Bridges Using Kalman Filter-Based Multimetric Data Fusion

文件：`ref_papers/Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric.pdf`

为什么值得用：这篇不是毫米波雷达，而是 acceleration + strain 的 Kalman 多指标融合；但它解决的问题非常接近：桥梁位移测量缺少固定参考点，单独加速度双积分会漂移，单独应变转换低频强但高频不足。

方法论：状态空间模型表示加速度到位移的双积分关系；measurement update 使用 strain-displacement 关系得到的位移观测；Kalman filter 在频域上相当于让加速度提供高频信息、应变提供低频/幅值约束。

可借鉴点：

- 结构位移融合可以从“各传感器频带优势互补”的角度解释，而不是只说 Kalman 数学。
- 如果本文使用雷达位移替代应变位移，模型逻辑是类似的：加速度预测动态演化，雷达位移更新低频/绝对位移。
- 适合引出“reference-free displacement estimation”这一写法。

关键结果：数值仿真误差约 7.4% 和 6.0%；预应力混凝土桥现场试验中估计位移与激光参考吻合较好。

建议状态：建议作为“桥梁 reference-free Kalman multimetric fusion”引用。

### Real-Time Strong-Motion Broadband Displacements from Collocated GPS and Accelerometers

文件：`ref_papers/Real-time strong-motion broadband displacements from collocated GPS and accelerometers..pdf`

为什么值得用：这篇来自地震/强震监测，但融合逻辑经典：GPS 提供不漂移的低频/绝对位移，加速度提供高采样动态信息，Kalman filter 输出 broadband displacement。它和“雷达位移 + 加速度”的角色分工高度相似。

方法论：1 Hz GPS displacement + 100 Hz accelerometer data -> Kalman filter -> 高频不漂移的 broadband displacement / velocity。目标是避免单独积分加速度导致漂移，也避免单独 GPS 采样率低和噪声大。

可借鉴点：

- 可把毫米波雷达类比为 GPS/低频位移传感源，加速度计类比为高频动态源。
- 适合写“低频绝对/相对位移观测 + 高频惯性观测”的通用融合范式。
- 对实时性和漂移问题解释清楚。

建议状态：建议作为跨领域方法类参考，不作为核心桥梁雷达文献。

### A state-space approach for deriving bridge displacement from acceleration

文件：`ref_papers/A state-space approach for deriving bridge displacement from acceleration.pdf`

为什么值得用：这篇只用加速度推桥梁位移，但很适合解释为什么加速度双积分难、低频误差为什么会被放大、状态空间方法如何减少漂移。

方法论：用状态空间解析模型拟合 noise-free acceleration signal，保留低频低幅成分，再积分得到 displacement；与传统 velocity correction / baseline correction 方法比较。

可借鉴点：

- 引言可引用其对“加速度积分漂移”的问题表述。
- 如果本文融合中需要说明加速度单独无法恢复低频/准静态位移，这篇很适合。

建议状态：作为加速度位移重构背景引用。

### Kalman 1960

文件：`ref_papers/Kalman1960.pdf`

为什么值得用：Kalman filter 原典。正文一般不必大段展开，但如果公式章节正式采用 Kalman filter，可以作为基础引用。

建议状态：方法原典，少量引用即可。

## 可作为补充参考

### Unscented filtering and nonlinear estimation

文件：`ref_papers/Unscented filtering and nonlinear estimation.pdf`

用途：若后续融合模型包含非线性投影、转换因子、角度几何或非线性观测方程，可作为 UKF/unscented filter 的基础引用。

注意：这是滤波方法文献，不是结构位移监测案例。只有在实现 EKF/UKF 或讨论非线性状态估计时才需要引用。

### A new method for the nonlinear transformation of means and covariances in filters and estimators

文件：`ref_papers/A_new_method_for_the_nonlinear_transformation_of_means_and_covariances_in_filters_and_estimators.pdf`

用途：无迹变换的基础方法来源，可和 `Unscented filtering and nonlinear estimation.pdf` 搭配。

注意：只适合方法章节，不适合相关工作中展开。

### Data fusion approaches for structural health monitoring and system identification: Past, present, and future

文件：`ref_papers/Data fusion approaches for structural health monitoring and system identification Past, present, and future.pdf`

用途：SHM 数据融合综述，适合引言或相关工作中概括数据融合层级、挑战和发展方向。

注意：偏综述，不提供本文可直接复现的“雷达+加速度”算法。

### Wireless Displacement Sensing System for Bridges Using Multi-Sensor Fusion

文件：`ref_papers/Wireless Displacement Sensing System for Bridges Using Multi-Sensor Fusion.pdf`

用途：基于无线传感器的 strain + acceleration 多指标桥梁位移估计，适合作为“融合算法工程部署”的补充背景。

注意：传感器组合不是 radar + accelerometer，引用时强调“多指标融合思想”，不要把它当毫米波雷达融合文献。

### Sensing Mechanism and Real-Time Bridge Displacement Monitoring for a Laboratory Truss Bridge Using Hybrid Data Fusion

文件：`ref_papers/Sensing Mechanism and Real-Time Bridge Displacement Monitoring for a Laboratory Truss Bridge Using Hybrid Data Fusion.pdf`

用途：加速度 + 应变的实时 hybrid data fusion，用于同时获取 pseudo-static 和 dynamic displacement。

注意：适合作为实时融合和无线/嵌入式实现背景。

### Vision and Vibration Data Fusion-Based Structural Dynamic Displacement Measurement with Test Validation

文件：`ref_papers/Vision and Vibration Data Fusion-Based Structural Dynamic Displacement Measurement with Test Validation.pdf`

用途：vision displacement + acceleration 的 asynchronous multi-rate Kalman filtering。可作为“低采样非接触位移 + 高频加速度”的近邻参考。

注意：非毫米波雷达，但融合结构与本文可能很像。

### An Innovative Sensor Integrated with GNSS and Accelerometer for Bridge Health Monitoring

文件：`ref_papers/An Innovative Sensor Integrated with GNSS and Accelerometer for Bridge Health Monitoring.pdf`

用途：GNSS + accelerometer 集成传感器，解决时间/空间参考同步问题。适合作为“共址多传感器硬件集成与同步”的背景。

注意：没有毫米波雷达；适合写同步和多传感器互补，不适合支撑雷达相位处理。

## 被丢弃目录中的相关性复查

### Study on Multi-Heterogeneous Sensor Data Fusion Method Based on Millimeter-Wave Radar and Camera

文件：`ref_papers/99_irrelevant_literature/Study on Multi-Heterogeneous Sensor Data Fusion Method Based on Millimeter-Wave Radar and Camera.pdf`

复查结果：有 mmWave radar、camera、adaptive root-mean-square cubature Kalman filter、joint probability data association 等关键词，但任务是智能车辆目标跟踪和碰撞风险感知，不是结构位移或加速度-雷达融合。

建议：暂不移回。若后续想写“异构传感器 Kalman/CKF 融合在雷达领域很常见”，可作为一句旁证；不建议作为 thesis 方法依据。

### Sensor and Sensor Fusion Technology in Autonomous Vehicles: A Review

文件：`ref_papers/99_irrelevant_literature/Sensor and Sensor Fusion Technology in Autonomous Vehicles: A Review.pdf`

复查结果：是自动驾驶传感器校准、融合和目标检测综述，与结构位移监测弱相关。

建议：不引用，除非论文需要非常泛化地解释 radar/camera/LiDAR 融合分类。

### On the Integration of Enabling Wireless Technologies and Sensor Fusion for Next-Generation Connected and Autonomous Vehicles

文件：`ref_papers/99_irrelevant_literature/On the Integration of Enabling Wireless Technologies and Sensor Fusion for Next-Generation Connected and Autonomous Vehicles.pdf`

复查结果：车联网和自动驾驶综述，融合对象为 radar/LiDAR/camera/通信，不适合结构位移融合。

建议：不引用。

### Implementation of a drive-by monitoring system for transport infrastructure utilising smartphone technology and GNSS

文件：`ref_papers/99_irrelevant_literature/Implementation of a drive-by monitoring system for transport infrastructure utilising smartphone technology and GNSS.pdf`

复查结果：与交通基础设施监测有关，但是 drive-by / smartphone / GNSS 路线，不是固定结构测点的雷达+加速度融合。

建议：暂不引用。

### Investigation of Frequency-Domain Dimension Reduction for A2M-Based Bridge Damage Detection Using Accelerations of Moving Vehicles

文件：`ref_papers/99_irrelevant_literature/Investigation of Frequency-Domain Dimension Reduction for A2M-Based Bridge Damage Detection Using Accelerations of Moving Vehicles.pdf`

复查结果：使用移动车辆加速度做桥梁损伤检测，关注频域降维和分类，不涉及位移融合。

建议：不引用。

## 对本文后续融合章节的建议写法

如果后续写“加速度 + 毫米波雷达数据融合”，建议把雷达位移和加速度的关系写成频带互补：

- 加速度：高采样、高频动态响应好，但双积分导致低频漂移。
- 毫米波雷达：相位位移灵敏，低频/准静态约束更好，但受 target 选择、相位解缠、遮挡、LOS 投影影响。
- Kalman/FIR 融合：用状态方程表达位移-速度-加速度动力学；加速度作为输入或观测预测高频动态；雷达位移作为观测更新，约束低频漂移。
- 多率问题：若雷达和加速度采样频率不同，可参考 MRKF，不必简单重采样。
- 非线性问题：若把转换因子、角度投影、target 权重也放进状态，可考虑 EKF/UKF；此时再引用 UKF/无迹变换文献。

优先阅读顺序：

1. `ref_papers/00_primary_references/Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
2. `ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
3. `ref_papers/00_primary_references/Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`
4. `ref_papers/Multi-sensor and Multi-frequency Data Fusion for Structural Health Monitoring.pdf`
5. `ref_papers/Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric.pdf`
6. `ref_papers/Real-time strong-motion broadband displacements from collocated GPS and accelerometers..pdf`
7. `ref_papers/Kalman1960.pdf`
