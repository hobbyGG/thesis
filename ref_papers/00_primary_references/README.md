# 主要参考文献速读说明

本目录是论文写作和 AI 辅助阅读时应优先参考的核心文献。下面内容基于对 PDF 全文的研究问题、方法章节、实验验证、结果和局限的精读整理；后续 AI 在一般写作、选题定位、方法对比时应先读本文件，只有需要公式、图表或精确数值出处时再打开 PDF。

## 阅读优先级

1. `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
   - 核心主文献。用于建立“毫米波雷达可实现微米级振动测量”的理论和系统基线。
2. `Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
   - 背景综述。用于写结构位移监测技术谱系、传感器优缺点和研究空白。
3. Ma/Zhanxiong 系列雷达与多传感器论文
   - 用于桥梁/土木结构位移、加速度、相位解缠、长期监测、低成本系统落地等具体方法论。
4. 雷达相位、解缠、精度和多目标测量论文
   - 用于支撑本文的倒挂式相位模型、target 选择、相位连续性、近距离目标互扰和多点桥梁监测对照。
5. 微波/毫米波桥梁现场应用论文
   - 用于写“雷达位移测量已经在桥梁现场成立，但现有工作通常默认雷达固定、目标随结构运动”的研究空白。
6. 自适应 Kalman / 测量噪声协方差论文
   - 用于支撑本文“innovation 变大不能直接归因于测量噪声 R；需要结合过程模型误差、观测质量和异常扰动判断，再决定是否固定 Q、更新 R 或同时自适应 Q/R”的方法设计。尤其是强响应阶段 prediction innovation 变大但 radar target 质量正常时，不应把差值全部归因于 R。

## 文献精读卡片

### Multi-Vib: Precise Multi-point Vibration Monitoring Using mmWave Radar

文件：`Multi-Vib_Precise_Multi-point_Vibration_Monitoring_Using_mmWave_Radar.pdf`

用途：补充单部毫米波雷达进行多测点振动监测的代表性方法。论文用物理标记增强目标点回波，再结合距离、角度和信号处理分别恢复多个测点的振动频率与位移，适合作为多目标振动测量的早期方法参考。

### Measuring Micrometer-Level Vibrations With mmWave Radar

文件：`Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`

用途：作为毫米波微振测量的核心依据，支撑“非接触、低成本、商用毫米波雷达可测微米级振动”的主论点。

创新点：提出 VSNR（Vibration Signal-to-Noise Ratio）作为误差解释指标，把振动幅值、信号 SNR、载频统一到一个量中；提出 mmVib 的 MSC（Multi-Signal Consolidation）框架，用多 chirp 提高 VSNR、用多天线分离多个振动物体；不依赖专用相移器或 OFDM 雷达，只通过商用 FMCW 雷达的信号处理生成虚拟 chirp。

方法论：先在 IQ 平面把微振反射信号建模为圆弧拟合问题，证明测量误差与 VSNR 负相关；CGG 模块把一个 FMCW chirp 的 fast-time 样本拆成多组虚拟 chirp，形成不同起始频率的相干观测；VOD 用 Range-Angle Spectrum 和接收波束形成定位振动物体；CVE 通过基础圆拟合、静态背景消除、合并圆拟合提取振动相位；DVR 根据入射角修正测得振幅的投影误差。

关键结果：TI IWR1642 77 GHz 商用雷达；实验覆盖 10-200 um、20-400 Hz、80-640 cm。总体中位相对幅值误差约 3.946%，中位相对频率误差约 0.02487%；100 um 振动在约 4.8-5 m 距离下平均幅值误差约 3.174 um；相比 CircleFit 和 DirectPhase，80 分位幅值误差分别降低约 69.21% 和 97.99%。还做了遮挡、多角度、动态干扰、多目标、手机振动和钢厂现场泵/电机测试。

局限：金属或厚遮挡会阻断信号；多目标能力受商用雷达角分辨率限制；远距离和低 VSNR 场景仍依赖更强天线阵列、波束成形或更优硬件。

### Structural displacement sensing techniques for civil infrastructure: A review

文件：`Structural displacement sensing techniques for civil infrastructure_ A review.pdf`

用途：作为结构位移监测章节的总背景，说明为什么单一传感器不够、为什么需要雷达/视觉/加速度/应变等多传感器融合。

创新点：不是提出新算法，而是系统梳理土木基础设施位移测量技术，覆盖 13 类传感器、单模态与多模态融合、建筑/桥梁/其他结构应用，以及长期连续监测中的真实工程约束。

方法论：按接触式与非接触式分类比较 LVDT、加速度计、倾角仪、应变、连通管、光纤、GNSS、视觉、雷达、激光、LiDAR、level、total station 等技术；再按多传感器融合梳理“加速度 + 低频位移传感器”的通用框架，包括 Kalman/FIR 融合；最后从应用场景和工程约束讨论可部署性。

关键结论：加速度适合高频但有低频漂移；GNSS 适合大跨长期监测但精度/采样率有限；视觉可全场测量但受光照、计算量和相机固定点影响；雷达可远距离、全天候、高采样，但有 LOS 转换、目标识别和毫米波相位缠绕问题；长期监测还需要考虑安装位置、供电、通信、环境鲁棒性和实时计算。

可引用空白：鲁棒实时长期位移估计、低成本无线/自供能位移传感器、六自由度位移估计、地震位移估计、多物理量同步测量。

### Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer

文件：`Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`

用途：支撑“长期桥梁位移监测必须处理雷达目标遮挡，单靠雷达+加速度不够”的论点。

创新点：针对长期监测中车辆等移动物体造成的间歇性雷达目标遮挡，提出雷达、应变、加速度三传感器融合框架；能自动检测目标遮挡并在多个雷达目标间切换；当所有雷达目标都被遮挡时，切换到应变+加速度估计位移，且不要求预知模态形状或中性轴位置。

方法论：初始校准阶段自动选择稳定雷达目标并估计 LOS 到真实振动方向的转换因子，同时训练 ANN 将低频应变映射为低频位移。连续估计分三阶段：雷达目标可用时，用加速度辅助相位解缠得到雷达位移，再用 FIR 融合雷达低频和加速度高频；雷达目标全遮挡时，用 ANN 应变位移和加速度高频融合；目标恢复时，用应变估计消除雷达相位解缠失败造成的漂移。

关键结果：10 m 梁式结构实验覆盖无遮挡、人工遮挡、温度变化和 75 min 连续监测；45 m 钢箱梁人行桥现场测试覆盖真实交通遮挡。雷达+加速度在遮挡时会出现数毫米到近 10 mm 级误差和遮挡后漂移；三传感器方法在实验室和现场均约 0.1 mm RMSE。

局限：论文中实验是离线后处理，实时性尚未充分验证；ANN 的应变-位移映射可能随长期环境和结构状态变化，需要在线更新。

### Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer

文件：`Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`

用途：支撑“方法可以变成低成本、边缘计算、现场可部署系统”的工程落地论点。

创新点：把前期雷达+加速度位移融合方法封装为紧凑硬件系统，并把人工初始校准改为自动校准；系统成本低于 500 美元，采样率 100 Hz，目标是中小跨桥梁/停车楼等毫米级位移长期监测。

方法论：硬件由 ADXL355 MEMS 加速度计、Infineon 60 GHz BGT60TR13C FMCW 雷达和 Raspberry Pi 4 MPU 组成。系统先自动等待结构出现较大高频响应，用高通积分和 Hilbert 包络选出有效校准时段；再识别雷达目标、遍历转换因子并选择使雷达高频位移和加速度高频位移 RMSE 最小的目标；连续测量时用加速度辅助相位解缠得到雷达位移，再用互补 FIR 滤波融合雷达低频和加速度高频，只上传最终位移而非原始数据。

关键结果：实验室四层模型和 9 个真实结构现场验证，包括中国、韩国、美国的多座桥梁和 Stanford 停车楼。系统在实验室和现场测试中位移 RMSE 通常小于 0.1 mm，摘要报告所有结构最大 RMSE 小于 0.06 mm；与单独雷达相比，融合后频域噪声更低，自然频率识别与 LDV 基本一致。

局限：未来需要加入 LoRa 等远距离通信、自供能（如太阳能），并进一步验证混凝土徐变、收缩等长期低频位移。

### Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping

文件：`Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf`

用途：支撑“毫米波雷达不依赖额外传感器也可处理大位移相位缠绕”的方法论。

创新点：提出 radar-only 的多 chirp 自适应相位解缠方法，不需要经验阈值、双频雷达或每个测点加装加速度计；保持单频 FMCW 硬件友好，同时支持多目标位移监测。

方法论：在每个时间步利用多 chirp 估计相位变化率，并对相位变化率本身进行解缠以提升鲁棒性；用当前多 chirp 相位变化率预测下一时刻相位所在的大致区间，再以预测相位作为参考恢复主 chirp 的真实连续相位；最终由相位-位移关系得到结构位移。

关键结果：四层框架实验中可估计最高约 5 cm 的大位移，相比传统算法位移 RMSE 最高降低 98.80%；双线性位移台多目标测试误差低于 0.1 mm；人行桥现场测试位移误差约 0.04 mm。

局限：未来还需系统考察雨、雾、电磁干扰等环境影响，并处理复杂桥梁环境下多目标回波重叠和 SNR 差异。

### Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring

文件：`Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`

用途：支撑“在强相位噪声下，相位解缠必须和降噪联合处理”的论点。

创新点：不同于先解缠再滤波的传统流程，本文把雷达相位解缠和降噪统一进加速度辅助 Kalman 状态空间模型；同时提出自适应噪声参数选择、方向转换因子标定和最小收敛时间判定，增强强噪声条件下的稳定性。

方法论：把相位和相位变化率作为状态，采用常加速度离散模型；加速度输入用于预测相位演化，雷达观测通过预测相位校正 2π 跳变；Kalman 更新输出连续且降噪的相位。噪声参数 Q 通过最小化解缠相位能量选择；方向转换因子通过带通后的雷达相位和加速度积分相位线性拟合得到；Kalman 递推被写成卷积形式，用历史权重衰减确定滤波器进入稳定状态前所需的最小静止/小运动收敛时间。

关键结果：四层建筑模型实验中，低噪声目标上加速度辅助法和本文方法都能处理大位移；高噪声目标上 Itoh 和旧加速度辅助法严重失败，本文方法 7 个工况平均相位 RMSE 约 2.096 rad。约 45 m 人行桥现场测试中，高噪声目标 9 个工况本文全部成功，平均相位 RMSE 0.276 rad，对应约 0.084 mm 位移误差；旧加速度辅助法在多工况中发散。

局限：需要结构在 Kalman 初始收敛期内没有明显相位缠绕；未来还需移植到紧凑传感系统并做更广泛现场验证。

### Computer vision-based cross-scale structural displacement estimation using amplitude-phase fusion

文件：`Computer vision-based cross-scale structural displacement  estimation using amplitude-phase fusion.pdf`

用途：作为视觉非接触位移测量的核心对照文献，尤其适合与雷达方法比较“大位移 + 小振动共存”场景。

创新点：提出幅值-相位融合的跨尺度视觉位移估计，不需要加速度计辅助也能处理大伪静态位移和小振动共存；解决相位法大帧间运动下易相位缠绕、相位-像素尺度不明、金字塔层级依赖经验、活动像素选择依赖阈值的问题。

方法论：用复值 steerable pyramid 分解图像。先用高通残差幅值特征做互相关，得到像素级粗配准；再把当前帧按粗位移对齐到参考帧，在选定金字塔层和方向上计算局部相位差，利用活动像素加权得到亚像素残余位移；最后把粗位移和相位残差相加。活动像素通过相关性选择；金字塔层级通过跨尺度相位线性关系优化；相位-像素尺度用合成图像序列自校准。

关键结果：单层建筑模型中可同时处理最高约 50 mm 的大运动和小于 1 mm 的振动，位移 RMSE 低于 0.2 mm；40 m 人行桥现场 8 个工况最大位移约 0.80-2.51 mm，RMSE 为 0.070 +/- 0.015 mm。相位-像素尺度自校准相比既有算法 RMSE 降低约 82.27%；只用活动像素可降低 28.57%-70.77% 位移误差。

局限：现场实验未系统考虑光照变化和背景杂波；当前假设相机固定，未来需通过 IMU 或静止目标跟踪扩展到移动相机场景。

### Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW millimeter-wave radar

文件：`Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf`

用途：支撑“雷达+MEMS 不仅可估计位移，也可提升低成本加速度测量”的论点。

创新点：首次将 FMCW 毫米波雷达融合专门用于结构加速度估计，目标是修正低成本 MEMS 加速度计低频漂移，同时抑制雷达位移二次微分带来的高频噪声。

方法论：同一硬件系统集成 ADXL355 MEMS、60 GHz FMCW 雷达和 Raspberry Pi。先用短时初始数据自动选择雷达目标、估计 LOS 转换因子，并用加速度辅助相位解缠得到雷达位移；再用滑动窗口形式的时域 FIR 互补滤波，把雷达位移提供的低频/准静态信息和 MEMS 加速度提供的高频信息合成加速度。正则化参数 lambda 通过奇异值策略和幂律拟合随窗口长度自适应设定。

关键结果：实验室移动台在 0.1 Hz 和 3 Hz 下验证；低频 0.1 Hz 经 0.15 Hz 低通后，融合加速度 RMSE 约 0.016 mm/s2，MEMS 为 0.299 mm/s2，误差降低约 94.6%。60 m 公路桥现场卡车 20/50/80 km/h 测试中，2 Hz 低通条件下相对 MEMS 的 RMSE 分别降低 85.4%、82.5%、64.5%，频谱峰值更接近 LDV。

局限：仍可能受雨、雾、多路径和桥下局部环境影响；当前主要是单轴测量，未来需扩展多轴、同步、规模化部署和自供能。

### Structural displacement estimation using accelerometer and FMCW millimeter wave radar

文件：`Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`

用途：作为“雷达安装在结构测点上、利用周围环境反射目标估计结构位移”的直接前序文献，尤其适合支撑本文倒挂式安装的基本可行性、自动 target 选择和方向转换因子标定。

创新点：提出将 FMCW 毫米波雷达和加速度计共址安装在结构测点处，不要求雷达固定在地面参考点；通过短时初始数据自动选择周围环境中最优雷达 target，并估计 LOS 位移到结构实际振动方向位移的转换因子；再用互补 FIR 融合雷达低频位移和加速度高频响应。

方法论：短时同步采集雷达和加速度；从雷达检测到的多个环境反射 target 中进行自动校准，选择与加速度积分位移最一致的 target，并确定 direction conversion factor；连续测量阶段对选定 target 的相位进行位移转换，再用 FIR 滤波融合雷达和加速度，得到结构位移。

关键结果：四层结构模型和人行桥现场实验验证了方法有效性；文献摘要和论文主页显示位移估计 RMSE 低于 0.1 mm 量级，适合毫米级结构响应监测。该文的“best target + conversion factor”是本文进一步扩展为“多 target 在线选择和可靠性权重”的重要基础。

局限：仍以选择单个 best target 为主，target selection 依赖短时校准和解缠后的位移一致性；对倒挂场景下多个静止散射体的 IQ 复合、动态遮挡和在线 target 集合维护讨论不足。

### Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion

文件：`Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf`

用途：用于支撑“长期桥梁监测中 radar target 会被车辆等移动物体间歇遮挡，因此 target 选择、遮挡检测和 target 切换必须在线化”的论点。

创新点：显式考虑桥下车辆造成的 intermittent radar target occlusion，不再假设单个雷达 target 长期稳定可见；先从短时测量中选择多个 good targets 并估计各自转换因子，再在连续监测中利用加速度辅助算法处理目标遮挡期，提出 target 遮挡期位移重构和多 target 相位解缠以抑制遮挡后漂移。

方法论：短时雷达/加速度同步采集 -> 多个 good radar targets 选择和 direction-converting factors 标定 -> 连续监测中检测 target occlusion -> 可见 target 正常估计位移 -> 遮挡 target 用重构算法补偿 -> 多 target 相位解缠去除遮挡造成的位移漂移。

关键结果：10 m 桥梁实验和两跨人行桥现场测试验证；论文摘要报告总体误差低于 0.1 mm，可用于毫米级桥梁位移连续估计。与本文关系最紧的是：它已经从“单 best target”走向“多个 good targets + 遮挡管理”，但目标仍主要服务于相位解缠和连续位移恢复。

局限：仍需加速度作为辅助参考；good target 的筛选依赖短时校准，不是完全 unwrap-free 的在线 target selection；对倒挂式雷达中静止参考 target 的 IQ 几何质量、频带一致性和复合散射稳定性没有单独建模。

### A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring

文件：`A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf`

用途：作为较早的 FMCW 雷达多 target 结构位移测量基础文献，用来说明 FMCW 不只可测单点距离，也可以在不同距离上同时区分多个结构 target。

创新点：从 3D 结构位移测量需求出发，分析高精度一维距离变化与三维位移之间的关系；建立 FMCW 雷达位移测量和多 target 分辨的数学模型；用商用雷达前端和 DAQ 自制原型，并讨论硬件相位异步对位移误差的影响。

方法论：FMCW 发射/接收 -> beat signal 和 Range FFT 得到目标距离单元 -> 通过相位变化估计每个 target 的微小距离变化 -> 分析 phase asynchronism 带来的误差 -> 户外单 target 和三 target 实验验证。

关键结果：户外实验表明三个不同距离 target 可同时区分，并达到毫米级位移精度。该结果可用于本文引言中说明“多 target radar displacement measurement”早已有基础，但其 target 通常是结构上的反射体，而本文 target 是环境静止参考体。

局限：主要处理不同 range 上的目标，未解决同一 range bin 内多个散射体复合、倒挂式雷达运动引起的背景相位旋转，以及在线 target 可靠性评价问题。

### Solving Phase Ambiguity in Interferometric Displacement Measurement With Millimeter-Wave FMCW Radar Sensors

文件：`Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf`

用途：用于支撑“毫米波短波长带来高位移灵敏度，同时也使大位移相位模糊更严重；相位解缠是位移恢复阶段的核心问题”。

创新点：针对单通道 FMCW 雷达相位模糊，提出从 slow time 合成等效正交 I/Q 信号的方法，使原本主要用于单音 CW 雷达的线性相位解调技术可以迁移到 FMCW 雷达；目标是无需额外硬件通道也能处理超过半波长的大位移。

方法论：单通道 FMCW 回波 -> range bin 选择 -> 在 slow time 上构造等效正交 I/Q -> 使用线性相位解调算法恢复连续相位 -> 由相位-位移关系得到大位移运动。

关键结果：实验表明可从单通道 FMCW 雷达中提取约 10 倍波长量级的大位移运动，并达到微米级精度。对本文而言，它适合作为“位移恢复阶段可选解缠方法”，但不适合直接作为 target selection 判据。

局限：重点在单 target 的相位模糊解决；对多散射体叠加、遮挡、动态干扰和倒挂式静止参考 target 选择没有展开。

### A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring

文件：`A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf`

用途：作为 MIMO mmWave 雷达中利用 Doppler 信息辅助相位解缠的参考，可放在“位移恢复阶段的解缠策略”或“大位移/快速运动下传统 Itoh 解缠失效”小节。

创新点：指出当相邻帧之间目标径向位移超过雷达波长四分之一时，传统相位解缠会失败；提出利用估计到的 Doppler 信息迭代修正相位轨迹，以恢复快速运动目标的连续相位和径向位移。

方法论：MIMO-FMCW 数据 cube -> range/angle/Doppler 处理 -> 对特定目标点获取相位轨迹和 Doppler 估计 -> 用 Doppler 约束预测跨帧相位变化 -> 迭代 phase unwrapping -> 径向位移重建。

关键结果：实验结果显示该方法能在传统解缠方法失败的快速运动场景中重建目标相位轨迹，并保持较小计算复杂度。它支持本文“target selection 阶段不应依赖未确认可靠 target 的 unwrap 结果”的设计边界。

局限：主要解决运动 target 的相位轨迹恢复，不直接回答静止参考散射体的选择和复合 IQ 稳定性问题；依赖 Doppler 估计质量，低 SNR 或多散射体相干叠加时仍需谨慎。

### Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar

文件：`Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf`

用途：用于量化商用/集成式 77-81 GHz FMCW 雷达做微小位移测量时，IF 相位本身能达到的精度上限和误差量级。

创新点：不是提出复杂算法，而是从硬件相位稳定性和振动台参考实验出发，系统评估毫米波 FMCW 雷达 slow-time IF phase 的准确度和精密度；区分静态 loopback/waveguide 测试和动态振动目标测试。

方法论：77-81 GHz radar transceiver MMIC -> 刚性 RF waveguide 静态相位测试 -> 统计相位偏移和 3-sigma 精密度 -> 工业振动台动态实验 -> 将相位误差换算成等效目标位移误差。

关键结果：摘要报告最大准确度误差约 +0.359 度，对应约 1.907 um 位移；最大 3-sigma 精密度约 +/-0.358 度，对应约 +/-1.180 um 位移。该文可用于支撑“理论上 mmWave 相位足够灵敏，难点转向 target 稳定性、IQ 叠加、解缠和工程环境”。

局限：实验环境较可控，更多验证硬件和单 target 相位测量能力；对桥梁现场多路径、遮挡、动态干扰和倒挂式安装未展开。

### Radar Sensing of Displacement Motions With High Robustness Against Additive Noise

文件：`Radar_Sensing_of_Displacement_Motions_With_High_Robustness_Against_Additive_Noise.pdf`

用途：用于支撑“低 SNR、远距离或微小位移条件下，I/Q 相位解调对加性噪声敏感，因此 target selection 应考虑 IQ 轨迹质量和信噪比”的论点。

创新点：分析 Doppler radar 位移相位解调中加性高斯噪声和相位噪声的影响，提出将 I/Q 加性噪声转化为相位噪声的鲁棒相位解调思路，以提高低 SNR 下位移重建能力。

方法论：Doppler radar I/Q 信号 -> 噪声影响数学分析 -> I/Q 预处理或变换以降低加性噪声对 arctangent 相位解调的破坏 -> 相位解调 -> 位移运动重建 -> 仿真和实验验证。

关键结果：仿真和实验均显示该方法在低 SNR 场景下比传统 arctangent 类相位解调更稳健。它不直接解决本文 target 选择，但能解释为什么“强反射、稳定幅值、规则 IQ 轨迹”应成为 target 可靠性指标。

局限：主要面向 CW/Doppler radar 的位移解调问题；没有处理 FMCW range-angle target 管理和倒挂式多静止散射体叠加。

### Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring

文件：`Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring.pdf`

用途：用于说明毫米波雷达系统经过硬件小型化和信号处理优化后，可用于桥梁非接触位移监测的工程系统开发。

创新点：构建高精度 nano millimeter-wave radar system，并将 mean cancellation、Hamming window、all-phase FFT 等信号处理模块整合到桥梁位移识别流程中，强调轻量、非侵入和现场部署。

方法论：固定雷达观测桥梁动态响应 -> mean cancellation 和 Hamming window 进行目标指示/谱泄漏抑制 -> all-phase FFT 提高频率/距离估计精度 -> 相位变化转换为桥梁位移 -> 控制环境和现场桥梁实验验证。

关键结果：论文结论认为系统在受控环境和实际桥梁应用中均能实现准确、非接触、易部署的桥梁结构行为评估。对本文的价值在于补足“毫米波雷达桥梁位移监测系统化实现”的工程背景。

局限：仍是固定雷达观测运动桥梁 target 的传统几何；对雷达随结构运动、环境静止 target 选择和多 target 在线管理没有讨论。

### FMCW Radar for Noncontact Bridge Structure Displacement Estimation

文件：`FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf`

用途：作为桥梁非接触位移估计中 FMCW 参数设计和雷达安装几何影响的参考。

创新点：围绕桥梁小位移估计所需的 range resolution 和相位精度，讨论 FMCW 带宽、雷达放置位置、目标距离和测量准确度之间的关系；重点指出桥梁位移估计不能只看距离分辨率，还要考虑实际雷达布设导致的几何误差。

方法论：建立 FMCW 雷达信号模型 -> 分析 beat frequency/range resolution 与小位移估计关系 -> 讨论不同 radar placement 下 LOS 位移和真实桥梁位移的换算 -> 用仿真或实验评估估计误差。

关键结果：该文适合用来支撑“LOS 投影和雷达安装几何会影响桥梁位移估计”，与本文的投影系数 `eta_i` 和转换因子 `beta_i` 有直接概念关系。

局限：更多关注固定雷达布设和桥梁 target 位移，不处理倒挂雷达中环境 target 的选择、IQ 复合散射和在线可靠性评价。

### Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry

文件：`Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf`

用途：作为微波雷达干涉测量用于桥梁监测的综述/策略型背景文献，适合放在引言或相关工作中说明雷达桥梁监测的工程谱系。

创新点：梳理日本和意大利桥梁监测中使用的三类微波雷达系统，包括 full polarimetric real aperture radar、SFCW linear synthetic aperture 和 MIMO array sensor，并提出极化分析与干涉技术结合的桥梁监测思路。

方法论：微波雷达干涉测量 -> LOS 位移和频谱提取 -> 极化/阵列/合成孔径处理增强目标解释 -> 桥梁现场案例对比不同系统的测量能力。

关键结果：文中强调 microwave radar interferometry 可远程、非侵入、以亚毫米精度测量大型基础设施 LOS 位移，并可同时获得振动频谱。它为本文提供宏观背景，但不是本文算法主依据。

局限：偏综述和系统展示；不涉及倒挂式安装、静止参考 target 的 IQ 质量评价和多 target 在线选择。

### Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge

文件：`Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge.pdf`

用途：作为地基雷达干涉仪在大型铁路桥现场动态监测中的实证参考，适合用于说明雷达在桥梁空间多点响应捕捉上的优势。

创新点：使用 IBIS-S 地面微波雷达干涉仪监测南京大胜关多线高速铁路桥，在不同雷达站位和视角下获取高铁、地铁、风等荷载工况下的桥梁动态响应，并用 LiDAR 点云辅助解释雷达测点位置。

方法论：地基雷达多站位布设 -> 获取 LOS 动态位移 -> LiDAR 点云辅助测点定位和结构解释 -> 与既有 SHM 系统数据对比 -> 分析列车/风荷载下桥梁动态响应和空间变形特征。

关键结果：论文报告雷达具有约 0.5 m 空间分辨率和 50-200 Hz 时间分辨率，能够捕捉最大列车诱导位移和偏载下桥面空间变形细节，部分动态细节优于既有 SHM 系统。

局限：设备是地基雷达干涉仪，通常体积和成本高于本文考虑的低成本毫米波 FMCW 雷达；目标定义仍是桥梁结构反射点，不是倒挂雷达的环境静止参考点。

### Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge

文件：`Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge.pdf`

用途：用于说明雷达干涉法可对超长跨桥梁进行多点位移测量，并输出位移影响线、模态和动静载响应。

创新点：开发并应用地基微波干涉雷达系统，对主跨 1200 m 悬索桥进行静载、环境振动和移动车辆荷载试验；提出利用三个参考点测量桥梁主梁位移的方法，实现主梁、桥塔和缆索多点位移监测。

方法论：I/Q 信号 FFT -> 目标距离单元相位提取 -> 干涉相位换算 LOS 位移 -> 多点位移影响线和频谱分析 -> 与常规传感/加载试验结果比较。

关键结果：现场测试获得了主梁、塔和缆索多点位移，并实现桥梁主梁多点位移影响线同步测量。该文可用于写“雷达多点监测能力”背景，但本文的多 target 是一个测点位移的多个参考观测，概念上需区分。

局限：多点指桥上多个物理测点响应，而本文多 target 指同一结构测点位移在多个环境反射方向上的投影观测；二者不能直接等同。

### Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar

文件：`Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf`

用途：用于支撑“单一 LOS 位移不足以完整描述桥梁响应，多个观测方向可反推出位移分量”的观点，与本文多 target 投影观测有概念共鸣。

创新点：将 FMCW MIMO 雷达用于意大利 Catanzaro 拱桥监测，通过 monostatic 和 multimonostatic 两种配置估计桥面位移分量，并给出基于几何配置的位移和振动方向不确定度预测公式。

方法论：FMCW MIMO 雷达多几何布设 -> 不同 LOS 位移观测 -> 根据 multimonostatic 几何反演水平/竖向位移分量 -> 估计自然频率和优先振动方向 -> 分析几何不确定度。

关键结果：现场测得桥梁水平位移分量显著大于竖向分量，水平位移超过 4 mm，并识别出 6 个自然频率。该文可用于支撑本文“多个 LOS 观测本质上是结构位移在不同方向上的投影”。

局限：依赖多个雷达几何/站位，而本文希望单个倒挂雷达从多个环境 target 中获得多投影观测；多观测来源不同，算法不可直接照搬。

### Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing

文件：`Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf`

用途：作为铁路桥低成本雷达-加速度融合监测的近期工程案例，支撑“毫米波雷达融合传感器可以用于实际铁路桥高精度位移和加速度测量”。

创新点：集成 60 GHz FMCW 雷达、三轴 MEMS 加速度计和带无线接口的微控制器，面向预算受限的小型/中型铁路桥；使用自动校准、加速度辅助自适应相位解缠和 FIR 滤波实现实时位移估计，并提出进一步结合非专用多模态传感的扩展方向。

方法论：雷达 + MEMS 加速度同步采集 -> 自动校准和转换因子估计 -> 加速度辅助相位解缠 -> FIR 融合 -> 与 LDV 参考数据对比 -> 铁路桥现场验证。

关键结果：摘要报告位移 RMSE 低于 0.1 mm；结论中 Gongju-Osong 高速铁路桥现场验证相对 LDV 的位移误差低于 0.05 mm。该文可作为低成本现场系统的补充证据。

局限：依然沿用雷达+加速度融合和自动 best target 选择思路；对于倒挂式多 target 选择、同一 range bin 内复合散射和 unwrap-free 可靠性评价未展开。

### Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements

文件：`Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements.pdf`

用途：用于说明毫米波雷达测得的桥梁位移/振动响应可以进一步服务于车辆-桥梁耦合分析和冲击系数评估。

创新点：建立考虑桥面粗糙度、车速和车辆重量的车辆-桥梁耦合模型，并使用毫米波雷达测量对小中跨简支梁桥振动响应进行对比验证；采用多点接触轮模型和与轮胎宽度匹配的桥面粗糙度模型。

方法论：车辆-桥梁耦合建模 -> 多点接触轮/桥面粗糙度输入 -> 计算冲击系数和振动响应 -> 毫米波雷达现场或实验测量桥梁响应 -> 模型与雷达测量对比。

关键结果：结论中指出多点接触模型相比单点接触模型更能模拟车辆-桥梁耦合，精度提高约 9.59%；雷达测量用于验证桥梁振动响应和冲击系数分析。

局限：重点是桥梁动力分析而非雷达信号处理；可作应用背景，不宜作为本文 target selection 或相位恢复算法依据。

### Structural displacement measurements using DC coupled radar with active transponder

文件：`Structural displacement measurements using DC coupled radar with active transponder.pdf`

用途：作为 radar displacement sensing 中“主动增强 target / transponder”路线的对照，用于说明本文希望避免额外靶标或主动设备，转而利用自然环境静止反射体。

创新点：为低功耗 CW radar 位移测量设计 active transponder，通过放大雷达信号提高回波 SNR，相比被动 backscatter 可改善结构位移测量信号质量。

方法论：CW radar + active transponder -> 实验比较主动转发与被动反射信号功率和位移测量效果 -> 分析多路径导致的放大模式随 radar-transponder 距离变化 -> 全尺寸桥梁测试。

关键结果：实验显示 active transponder 相比被动散射可将信号功率放大最高约 4.5 倍；全尺寸桥梁测试验证了其用于结构位移测量的可行性。

局限：需要在结构上布设主动 transponder，不符合本文“无专用靶标、利用自然静止反射体”的目标；但可作为对照说明自然 target 选择为何重要。

### Scanning Microwave Vibrometer: Full-Field Vibration Measurement via Microwave Sensing With Phase-Encoded Beam Scanning

文件：`Scanning_Microwave_Vibrometer_Full-Field_Vibration_Measurement_via_Microwave_Sensing_With_Phase-Encoded_Beam_Scanning.pdf`

用途：作为微波相干振动测量从单点走向全场扫描的代表文献，可用于相关工作中说明“雷达/微波振动测量不局限于单点，但复杂系统通常依赖阵列扫描和合成波束”。

创新点：提出 scanning microwave vibrometer (SMV)，利用 fast phase-encoded synthesis beam scanning 和相干合成 LFMCW 信号进行远程全场振动测量，兼顾大尺度、非接触和恶劣环境适应性。

方法论：LFMCW 相干合成发射 -> phase-encoded beam scanning -> 按空间位置获取微小振动相位 -> 标定相位编码向量和阵列稀疏性 -> 重构全场振动位移。

关键结果：论文通过真实系统实现和实验展示了 SMV 的全场振动测量能力。对本文的价值在于说明相位编码/波束扫描可以解决空间分离问题，但本文更倾向于利用商用低通道雷达的 range/range-angle target 选择。

局限：系统复杂度和硬件假设高于本文目标；并不直接解决倒挂式结构测点上低成本雷达的静止参考 target 选择问题。

### mmVib MobiCom 2020

文件：`mmVib_MobiCom2020.pdf`

用途：作为 mmVib 的会议版溯源文献。通常正文优先引用同目录中的 TMC 期刊扩展版 `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`；需要说明方法最早发表来源时再引用该版本。

创新点：与 TMC 版一致，核心是 VSNR、Multi-Signal Consolidation、Range-Angle 振动物体定位、IQ 圆拟合和多 chirp/多天线合并。

方法论：FMCW 数据 -> Range-Doppler/Range-Angle 搜索振动 bin -> chirp group 形成多观测 -> IQ 圆拟合和静态背景消除 -> 相位恢复 -> 振动幅值/频率估计。

关键结果：会议版展示了 mmVib 在 10-200 um、几十到数百 Hz 振动中的高精度测量能力，并验证遮挡、多目标和实际工业设备振动测量。数值引用建议以 TMC 期刊版为准。

局限：同 TMC 版；核心场景是固定雷达观测振动物体，不是雷达随结构运动观测静止参考体。

### 基于毫米波雷达的两近距离目标微动位移提取方法

文件：`基于毫米波雷达的两近距离目标微动位移提取方法_高昂.pdf`

用途：用于支撑“两个近距离 target 处于同一或相邻 range 分辨单元时，频谱泄漏和邻近杂波会影响微位移相位提取”的问题意识；可作为本文复合 target 和角度/峰簇过滤的中文参考。

创新点：以两个近距离 target 为例研究毫米波雷达多目标微动位移测量，基于 all-phase DTFT 提出利用相位谱周期极值和宽过渡带特性的双密集分量频率估计方法，并提出 Accurate Displacement Extraction Method (ADEM) 用一组收发天线区分和提取同一距离分辨率内两个目标的位移。

方法论：毫米波雷达基带信号 -> all-phase DTFT/dense spectrum 分析 -> 双近距离分量频率估计 -> 邻近杂波干扰建模 -> ADEM 提取两个近距离目标的相位序列和位移 -> 仿真和 LFMCW 平台实验验证。

关键结果：摘要显示无噪声条件下两个密集分量频率估计误差低于 0.03 bins；SNR 大于 30 dB 时两个近距离分量相位序列平均绝对百分比误差低于 7%；实验中可识别距离小于一个距离分辨率的两个目标，毫米级位移幅值准确率超过 88%，厘米级位移更好。

局限：硕士论文场景更偏雷达信号处理和两个主动/可控近距离目标；本文更关注自然环境静止反射体的在线筛选和等效 target 稳定性，因此可作方法启发，不宜作为主算法依据。

### Approaches to Adaptive Filtering

文件：`Approaches to Adaptive Filtering.pdf`

用途：作为 adaptive Kalman filtering、innovation-based adaptive estimation 和 covariance matching 的经典源头文献。正文中可用于支撑“当过程噪声和测量噪声统计特性先验不准确时，可以根据观测数据在线调整滤波器参数”的基本合理性。

创新点：将自适应滤波方法归纳为 Bayesian、maximum likelihood、correlation 和 covariance matching 等类别，并讨论错误先验噪声统计会导致 Kalman 滤波估计误差增大甚至发散。该文不是具体桥梁或雷达应用，但适合作为方法理论依据。

方法论：从离散状态空间模型出发，指出传统 Kalman 滤波假设过程噪声和测量噪声统计已知；当这些统计量未知或时变时，可从 innovation、residual 或观测序列中估计噪声协方差，或直接估计等效 Kalman gain。

对本文的启发：本文可引用该文说明 adaptive R 并非工程凑参数，而是 covariance matching / innovation-based adaptive filtering 的标准做法。由于本文主要不确定性来自 radar target 观测关系和 beta 收敛状态，因此可固定 Q，仅对 target-wise R 做在线调整。

### Adaptive Kalman Filtering for INS GPS

文件：`Adaptive Kalman Filtering for INS GPS.pdf`

用途：作为“惯性预测 + 外部观测更新”场景中使用 innovation-based adaptive estimation 的代表文献，和本文“加速度预测 + 雷达相位观测”的融合结构最接近。

创新点：面向 INS/GPS 组合导航，系统比较 innovation-based adaptive estimation (IAE) 和 multiple-model-based adaptive estimation (MMAE)，并给出基于最大似然思想的自适应 Kalman 滤波。论文结果表明，通过调整 Q、R 或二者，adaptive Kalman filter 可优于常规固定噪声 Kalman filter。

方法论：利用 innovation 序列反映实际测量与预测之间的不一致程度，并据此调整滤波器权重和 Kalman gain。文中明确讨论 Q 和 R 先验不准时会影响滤波精度和稳定性。

对本文的启发：本文可借鉴其 IAE 叙事，但不必同时自适应 Q 和 R。加速度预测模型在短时窗口内相对稳定，而 beta 未收敛会直接导致 radar measurement equation 不可靠，因此将自适应集中在 R 上更容易解释。

### Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation

文件：`Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation.pdf`

用途：作为“innovation/residual 分别对应 Q/R 自适应”的直接依据。它比一般 IAE 文献更明确地说明：Kalman 滤波性能取决于 Q/R 的相对设置，innovation 变大并不天然等价于测量噪声变大，也可能是过程噪声或模型预测能力不足。

创新点：面向同步发电机动态状态估计，提出 adaptive EKF，在每个校正步同时估计过程噪声协方差 Q 和测量噪声协方差 R。论文用简单线性模型展示 Q/R 比值决定滤波表现：沿真实 Q/R 比例附近误差最低，偏离该比例会显著增大误差甚至导致常规 EKF 发散。

方法论：以 covariance matching 为基础，把 prediction innovation 定义为观测与先验预测观测的差，把 residual 定义为观测与后验估计观测的差；用 residual-based adaptive estimation 更新 R，以避免直接用 innovation 估 R 时两个正定矩阵相减导致 R 非正定；用 innovation-based scaling 更新 Q，并用遗忘因子平滑 Q/R 的递推估计。

对本文的启发：本文强响应阶段 prediction innovation 变大时，要先问“预测模型是否低估了真实结构动力响应”而不是立刻增大 radar target 的 R。若 target 的 SNR、IQ 稳定性、AoA 几何和 beta 状态正常，大 innovation 更可能包含 Q/模型误差或输入未建模响应，此时把差值全部归因于 R 会错误降权可靠 radar 观测。

### Bridge Displacement Estimation Using a Co-Located Acceleration and Strain

文件：`Bridge Displacement Estimation Using a Co-Located Acceleration and Strain.pdf`

用途：这是最适合放进本文方法依据的结构健康监测文献之一。它同样处理桥梁位移估计，同样使用加速度预测与另一类 pseudo-displacement 观测融合，并且明确采用 adaptive Kalman filter 递推估计测量噪声协方差。

创新点：提出将梁中部应变转换为 pseudo-static displacement，再与单个加速度计通过 adaptive Kalman filter 融合，实现 reference-free bridge displacement estimation。其关键不是复杂滤波器结构，而是承认 strain-derived displacement 的测量噪声会随测量条件变化，并在线更新其测量噪声协方差。

方法论：状态变量为位移和速度，加速度作为输入参与状态预测；应变换算得到的位移作为观测。论文保持过程噪声 Q 相对固定，并递推更新观测噪声 R，典型形式可写为遗忘因子平滑的 residual-based R 更新。

对本文的启发：该文可直接支撑“固定 Q、自适应 R”的选择。本文中的 radar wrapped phase 类似该文的 strain-derived displacement，都是外部观测量，其可靠性会随 target 质量、beta 收敛和局部环境变化而变化，因此应主要通过 R 调整 radar 观测权重。

### An Adaptive Low-Cost INS GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation

文件：`An Adaptive Low-Cost INS GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation.pdf`

用途：用于支撑“不同观测源或不同观测通道应有不同测量噪声协方差”的设计，尤其适合类比本文多个 radar targets 的 target-wise R。

创新点：针对低成本 INS/GNSS 紧组合中 GNSS 观测质量随环境变化的问题，提出 redundant measurement noise covariance estimation (RMNCE)，并将在线估计的测量噪声协方差用于卫星选择和 adaptive UKF。论文还设计了 measurement noise covariance expanding 机制，用于多路径和异常观测条件下放大测量噪声。

方法论：重点放在测量噪声协方差 R 的在线估计，而不是一味调过程噪声 Q。每颗卫星的观测质量不同，因此需要按观测通道估计或修正测量噪声，再通过滤波器自然改变对应观测的权重。

对本文的启发：多个 GNSS satellite 可以类比多个 radar targets。每个 target 的 SNR、AoA 几何、IQ 稳定性和 beta 收敛程度不同，因此 R 应按 target 单独自适应，而不是对所有 target 使用同一个全局测量噪声。

### A Robust Adaptive Extended Kalman Filter Based on an Improved Measurement Noise Covariance Matrix for the Monitoring and Isolation of Abnormal Disturbances in GNSS/INS Vehicle Navigation

文件：`A Robust Adaptive Extended Kalman Filter Based on an Improved Measurement Noise Covariance Matrix for the Monitoring and Isolation of Abnormal Disturbances in GNSS_INS Vehicle Navigation.pdf`

用途：用于支撑“R 的更新应结合观测质量指标和 abnormal disturbance 判断，而不是仅由 innovation 大小触发”的设计。它和本文 radar target 的质量门控最接近：GNSS 观测的 PDOP、measurement factor、位置标准差可类比 target 的 SNR、IQ 轨迹质量、range-angle 稳定性和 beta 可信度。

创新点：提出 Robust Adaptive EKF，通过改进测量噪声协方差矩阵和 Huber/IGGIII 鲁棒权重监测并隔离异常扰动。论文明确指出复杂环境中经验方差或固定 R 难以描述真实观测质量，因此构造动态 R，并在观测异常扰动时增大测量噪声协方差、降低异常观测对状态更新的影响。

方法论：先用位置精度因子、measurement factor 和位置标准差合成动态测量噪声协方差 R；再根据 prediction residual 的统计量构造两阶段 adaptive factor；同时用标准化 residual 和 IGGIII 权函数形成鲁棒 Kalman 更新；最后通过 Huber 模型在 adaptive filtering 和 robust filtering 结果之间加权融合。

对本文的启发：如果 radar target 质量指标显示异常，例如幅值突降、IQ 圆弧破坏、angle/range 跳变或 beta 未收敛，才应把 innovation 的一部分解释为 measurement-side 异常并增大该 target 的 R。若强响应阶段 target 质量仍正常，则应避免用单一 innovation 阈值把正常结构响应误判为测量异常。

### Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage-Husa Adaptive Robust Kalman Filter

文件：`Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage-Husa Adaptive Robust Kalman Filter.pdf`

用途：作为雷达领域中 Sage-Husa adaptive Kalman filter 和测量噪声约束更新的参考文献。它不如桥梁位移文献贴近本文主场景，但适合作为“雷达观测噪声时变且需要限制 R 范围”的对比依据。

创新点：针对无人艇雷达目标跟踪中平台和目标振动引起的测量白噪声变化，提出 square root Sage-Husa adaptive robust Kalman filter。文中通过平方根分解保证协方差非负定，并结合自适应因子和测量噪声上下限提升稳定性。

方法论：Sage-Husa 方法递推估计噪声统计，鲁棒部分通过 adaptive scale factor 平衡预测与观测。论文特别强调对 measurement noise covariance 的范围约束，避免 R 更新不合理导致滤波发散。

对本文的启发：本文不必采用完整 Sage-Husa 框架，但应保留其稳定性思想：target-wise R 更新后必须进行正定性和上下限约束。实际写法可采用 `clip(r_i, r_i^{min}, r_i^{max})`，以避免异常 target 或短时 phase jump 过度影响融合结果。

### Robust Kalman Filter with Recursive Measurement Noise Covariance Estimation Against Measurement Faults

文件：`Robust Kalman Filter with Recursive Measurement Noise Covariance Estimation Against Measurement Faults.pdf`

用途：用于支撑“innovation 是故障监测统计量，但它的变化需要区分 additive bias、measurement noise increment 和正常模型误差”的论点。该文特别适合回应本文当前问题：prediction innovation 变大本身不是 R 增大的充分条件。

创新点：提出 innovation-based recursive measurement noise covariance estimator，用于构造抗测量故障的 robust Kalman filter。论文分别分析 additive sensor fault 和 multiplicative/noise-increment fault 对 innovation 的影响：测量 bias 会转移为 innovation bias，测量噪声增大会增加 innovation covariance。

方法论：先证明正常工作时 innovation 应近似为零均值、协方差为理论 innovation covariance；当测量通道发生 bias 或 noise increment 时，innovation 的均值或协方差会改变。随后用当前 innovation square 递推估计 R，使 measurement fault 出现时 R 增大、Kalman gain 变小，从而降低故障观测对状态更新的影响。

对本文的启发：本文可以把 innovation 作为异常检测入口，但 R 更新应只针对 measurement-side fault 或 target quality degradation。强响应阶段若 acceleration-driven prediction 模型滞后、结构动力输入未充分建模或 Q 偏小，innovation 也会变大；这种情况下盲目增大 R 会使滤波器更相信错误预测，反而压制真实 radar 位移信息。

## 主题索引

- 微米级振动测量：优先读 `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`。
- 土木结构位移监测技术背景：优先读 `Structural displacement sensing techniques for civil infrastructure_ A review.pdf`。
- 倒挂式雷达 + 环境 target + 转换因子：优先读 `Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`。
- 在线遮挡和多 target 切换：读 `Accelerometer-aided millimeter-wave radar interferometry ... intermittent radar target occlusion.pdf`。
- 雷达相位缠绕但不加额外传感器：读 `Accurate structural displacement measurement ... multi-chirp-based adaptive phase unwrapping.pdf`。
- 强噪声相位解缠和降噪：读 `Acceleration-aided Kalman filtering ... .pdf`。
- 长期桥梁监测、目标遮挡、三传感器切换：读 `Continuous bridge displacement estimation ... .pdf`。
- 低成本实时系统和现场部署：读 `Development and field deployment validation ... .pdf`。
- 视觉位移测量与雷达对照：读 `Computer vision-based cross-scale ... .pdf`。
- 低成本加速度测量：读 `Improved structural acceleration estimation ... .pdf`。
- 多 target / 近距离 target 干扰：读 `A Noncontact FMCW Radar Sensor ... .pdf` 和 `基于毫米波雷达的两近距离目标微动位移提取方法_高昂.pdf`。
- LOS 多方向投影和位移分量：读 `Transversal Displacement Detection ... .pdf`。
- 桥梁现场微波雷达实证：读 `Ground-based radar interferometry ... .pdf` 和 `Radar-based multipoint displacement measurements ... .pdf`。
- 硬件相位精度上限：读 `Experimental Analysis of Accuracy and Precision ... .pdf`。
- innovation/covariance matching、Q/R 同时或分别自适应：读 `Approaches to Adaptive Filtering.pdf`、`Adaptive Kalman Filtering for INS GPS.pdf`、`Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation.pdf` 和 `Bridge Displacement Estimation Using a Co-Located Acceleration and Strain.pdf`。
- 多观测通道 target-wise R、观测质量门控和异常观测降权：读 `An Adaptive Low-Cost INS GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation.pdf`、`A Robust Adaptive Extended Kalman Filter Based on an Improved Measurement Noise Covariance Matrix for the Monitoring and Isolation of Abnormal Disturbances in GNSS_INS Vehicle Navigation.pdf`、`Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage-Husa Adaptive Robust Kalman Filter.pdf` 和 `Robust Kalman Filter with Recursive Measurement Noise Covariance Estimation Against Measurement Faults.pdf`。

<!-- FULL_FILE_INDEX:START -->

## 全量文件索引

| # | 文件 | 论文题名 | 索引说明 |
|---:|---|---|---|
| 1 | `A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf` | A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 2 | `A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf` | A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring | FMCW 相位测量与相位解缠方法，用于主算法基线和局限对比。 |
| 3 | `A Robust Adaptive Extended Kalman Filter Based on an Improved Measurement Noise Covariance Matrix for the Monitoring and Isolation of Abnormal Disturbances in GNSS_INS Vehicle Navigation.pdf` | A Robust Adaptive Extended Kalman Filter Based on an Improved Measurement Noise Covariance Matrix for the Monitoring and Isolation of Abnormal Disturbances in GNSS/INS Vehicle Navigation | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 4 | `Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf` | Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 5 | `Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf` | Accelerometer-aided millimeter-wave rad...ng intermittent radar target occlusion | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 6 | `Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf` | Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping | FMCW 相位测量与相位解缠方法，用于主算法基线和局限对比。 |
| 7 | `Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation.pdf` | Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 8 | `Adaptive Kalman Filtering for INS GPS.pdf` | 1900017 193..203 | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 9 | `An Adaptive Low-Cost INS GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation.pdf` | An Adaptive Low-Cost INS/GNSS Tightly-Coupled Integration Architecture Based on Redundant Measurement Noise Covariance Estimation | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 10 | `Approaches to Adaptive Filtering.pdf` | Approaches to adaptive filtering | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 11 | `Bridge Displacement Estimation Using a Co-Located Acceleration and Strain.pdf` | Bridge Displacement Estimation Using a Co-Located Acceleration and Strain | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 12 | `Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf` | Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 13 | `Computer vision-based cross-scale structural displacement  estimation using amplitude-phase fusion.pdf` | Computer vision-based cross-scale structural displacement estimation using amplitude-phase fusion | 结构健康监测或位移测量基础文献，用于方法背景和实验对照。 |
| 14 | `Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf` | Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 15 | `Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf` | Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 16 | `Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring.pdf` | Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 17 | `Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf` | Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 18 | `FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf` | FMCW Radar for Noncontact Bridge Structure Displacement Estimation | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 19 | `Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge.pdf` | Ground-Based Radar Interferometry for Monitoring the Dynamic Performance of a Multitrack Steel Truss High-Speed Railway Bridge | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 20 | `Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf` | Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW millimeter-wave radar | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 21 | `Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf` | Measuring Micrometer-Level Vibrations With mmWave Radar | 毫米波微振/多点振动测量，用于精度、目标分离和振动实验对照。 |
| 22 | `mmVib_MobiCom2020.pdf` | mmVib: Micrometer-Level Vibration Measurement with mmWave Radar | 毫米波微振/多点振动测量，用于精度、目标分离和振动实验对照。 |
| 23 | `Multi-Vib_Precise_Multi-point_Vibration_Monitoring_Using_mmWave_Radar.pdf` | Multi-Vib: Precise Multi-point Vibration Monitoring Using mmWave Radar | 毫米波微振/多点振动测量，用于精度、目标分离和振动实验对照。 |
| 24 | `Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage-Husa Adaptive Robust Kalman Filter.pdf` | Radar Target Tracking for Unmanned Surface Vehicle Based on Square Root Sage–Husa Adaptive Robust Kalman Filter | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 25 | `Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge.pdf` | Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 26 | `Radar_Sensing_of_Displacement_Motions_With_High_Robustness_Against_Additive_Noise.pdf` | Radar Sensing of Displacement Motions With High Robustness Against Additive Noise | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 27 | `Robust Kalman Filter with Recursive Measurement Noise Covariance Estimation Against Measurement Faults.pdf` | Robust Kalman Filter with Recursive Measurement Noise Covariance Estimation Against Measurement Faults | 自适应滤波与 Q/R 协方差依据，用于加速度预测和雷达观测更新。 |
| 28 | `Scanning_Microwave_Vibrometer_Full-Field_Vibration_Measurement_via_Microwave_Sensing_With_Phase-Encoded_Beam_Scanning.pdf` | Scanning Microwave Vibrometer: Full-Field Vibration Measurement via Microwave Sensing With Phase-Encoded Beam Scanning | 毫米波微振/多点振动测量，用于精度、目标分离和振动实验对照。 |
| 29 | `Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf` | Solving Phase Ambiguity in Interferometric Displacement Measurement With Millimeter-Wave FMCW Radar Sensors | FMCW 相位测量与相位解缠方法，用于主算法基线和局限对比。 |
| 30 | `Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf` | Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 31 | `Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf` | Structural displacement estimation usin...rometer and FMCW millimeter wave radar | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 32 | `Structural displacement measurements using DC coupled radar with active transponder.pdf` | Structural displacement measurements using DC coupled radar with active transponder | FMCW/微波雷达位移测量基础，用于距离、相位和非接触测量链路。 |
| 33 | `Structural displacement sensing techniques for civil infrastructure_ A review.pdf` | Structural displacement sensing techniques for civil infrastructure  A review | 结构位移/雷达监测综述，用于背景、技术谱系和研究空白。 |
| 34 | `Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf` | Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar | 桥梁/轨道结构位移或动力响应，用于结构监测场景和现场验证对照。 |
| 35 | `Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements.pdf` | Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements | 毫米波微振/多点振动测量，用于精度、目标分离和振动实验对照。 |
| 36 | `基于毫米波雷达的两近距离目标微动位移提取方法_高昂.pdf` | 基于毫米波雷达的两近距离目标微动位移提取方法 高昂 | 结构健康监测或位移测量基础文献，用于方法背景和实验对照。 |

<!-- FULL_FILE_INDEX:END -->
