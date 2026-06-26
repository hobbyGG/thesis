### 文献综述正文

结构位移和振动响应是桥梁、建筑等土木基础设施安全评估、模态识别、损伤诊断、荷载试验和有限元模型修正中的基础物理量。相较于加速度或应变等局部响应，位移更直接反映结构整体变形和服役状态，因此在长期健康监测和灾害后快速评估中具有不可替代的意义。已有结构位移监测技术可大体分为接触式和非接触式两类：LVDT 等接触式位移计精度较高，但通常需要稳定参考点，桥下交通、水域或复杂施工条件会显著增加安装难度；加速度计便于布设且采样率高，但由加速度双积分得到位移时，低频噪声、初值误差和传感器偏置会被持续放大；GNSS 能提供绝对位移，但采样率和垂向精度难以满足中小跨桥梁毫米级小振动监测；视觉和激光方法具有非接触优势，却受光照、遮挡、视线、相机稳定性和计算负担影响；应变、倾角或光纤等间接估计方法又往往依赖结构模型、边界条件或经验标定关系[1]。由此可见，单一传感器很难同时满足长期连续、高采样、高精度、低成本和强环境适应性的要求，多源信息融合因而成为结构健康监测的重要发展方向[2]。

在多传感器位移估计中，状态空间方法为不同物理量之间的互补融合提供了统一描述。以加速度推导桥梁位移的研究较早指出，直接双积分会受到低频误差和初始条件不确定性的严重影响，而状态空间模型可以把结构运动状态、观测噪声和递推校正纳入同一框架，从而在一定程度上抑制漂移并恢复动态位移[3]。这类思想后来也被广泛吸收到加速度-GNSS、加速度-视觉、加速度-应变以及加速度-雷达融合中：高频部分通常由加速度提供，低频或准静态部分由另一类位移相关观测补足。其本质并不是简单叠加多个传感器，而是根据不同观测源在频带、噪声、采样率和参考基准上的互补性，构建更加稳定的位移估计过程。

雷达位移测量为结构监测提供了另一类具有工程吸引力的非接触方案。FMCW 雷达通过调频连续波获得距离分辨能力，可在不同 range bin 中区分多个散射目标，并进一步利用目标回波相位变化估计 LoS 方向的微小距离变化。早期 FMCW 雷达结构监测研究已经表明，雷达不仅能够测量单一反射体的位移，也具备多 target 分辨与毫米级位移测量能力[4]。随着 60 GHz、77 GHz 等毫米波雷达芯片的发展，短波长进一步提高了相位对微小位移的敏感性，也使雷达系统更易小型化、低功耗化和现场部署。受控实验表明，毫米波 FMCW 雷达 slow-time IF 相位在硬件稳定条件下可达到微米级位移精度[5]。面向微振测量，mmVib 等工作从 IQ 平面圆弧几何、静态背景、多径叠加和多天线分离出发，提出 VSNR 与多信号融合思想，证明商用毫米波雷达能够感知微米级振动，并可借助 range-angle 信息区分多个振动物体[6]。这些研究共同奠定了毫米波相位位移测量的理论和实验基础。

然而，毫米波雷达用于结构位移监测时也面临一组与高灵敏度相伴而生的问题。首先，雷达相位本质上反映的是目标相对雷达的 LoS 距离变化，而结构工程中关心的往往是竖向、横向或某一主振动方向位移，因此需要建立 LoS 位移与结构实际运动方向之间的转换关系。其次，桥梁、地面、支座、车辆和附属构件会形成复杂散射环境，同一 range bin 或相邻 range-angle 单元中可能存在多径和复合散射，导致 IQ 轨迹偏离理想圆弧。再次，毫米波短波长虽然提升了分辨能力，却也使相位包裹问题更突出：对于 77 GHz 雷达，半波长量级的 LoS 位移就可能造成相位跨越 [-π, π] 区间，若缺乏可靠解缠，位移估计会出现跳变、漂移或长期累积误差。因此，雷达位移监测的关键不仅是“相位可测”，还包括 target 识别、相位质量评价、方向转换、相位解缠和噪声抑制等一系列处理环节。

围绕相位缠绕问题，已有研究形成了多条技术路线。传统 Itoh 类方法根据相邻采样相位差是否超过 π 进行加减 2π 校正，计算简单，但依赖相邻采样间真实相位变化足够小的假设，在大幅、快速或低采样率结构振动中容易失效。为突破这一限制，Liu 等将连续波雷达中的线性相位解调思想迁移到单通道 FMCW 雷达，通过 slow time 合成等效正交 I/Q 信号，使 MDACM 等方法能够用于 FMCW 干涉位移测量，从而解决较大位移下的相位模糊问题[7]。MIMO 毫米波雷达研究进一步利用 Doppler 信息预测跨帧相位变化，在快速运动目标中迭代恢复连续相位轨迹[8]。近期 multi-chirp 自适应解缠方法则利用多 chirp 估计相位变化率，并预测下一时刻相位所在区间，在不依赖额外传感器的条件下处理厘米级结构位移，同时保留多 target 监测能力[9]。这些 radar-only 方法扩展了毫米波雷达相位恢复的适用范围，但其核心仍主要是对某一目标 LoS 相位轨迹进行解缠，且通常把解缠与降噪、target 可靠性评价、方向转换和多目标融合分开处理。

另一类重要路线是利用结构上共址布设的加速度计辅助雷达位移估计。与传统地基雷达“雷达固定、结构 target 运动”的观测模式不同，Ma、Choi、Sohn 等提出将毫米波雷达和加速度计安装在结构测点上，使雷达随结构共同运动，并利用周围环境中的地面、桥下构件或其他静止散射体作为参考 target。结构运动会改变雷达与这些静止 target 之间的相对距离，该变化反映在 FMCW 回波相位中；通过短时初始数据，可以自动选择与加速度积分位移最一致的 best target，估计 LoS 位移到实际振动方向位移的 direction conversion factor，并融合雷达低频位移和加速度高频响应[10]。这一倒挂式布置降低了对外部固定雷达基座的依赖，为中小跨桥梁和复杂现场提供了新的测量思路。

在长期连续监测场景中，倒挂式雷达进一步暴露出 target 可靠性和观测连续性的挑战。车辆、行人或其他移动物体可能间歇性遮挡环境静止 target；遮挡不仅造成遮挡期间的相位缺失，还可能在 target 恢复后引发解缠漂移。针对这一问题，后续研究提出雷达、应变和加速度三传感器融合框架：在初始阶段从雷达检测目标中选择多个 good targets 并估计转换因子；当雷达 target 可用时，使用雷达和加速度估计位移；当全部雷达 target 被遮挡时，切换到应变和加速度；当 target 恢复时，再利用应变信息消除雷达相位漂移[11]。进一步的加速度辅助毫米波雷达干涉研究专门考虑 intermittent radar target occlusion，通过多个 good targets、遮挡检测和 target 切换提升桥梁位移连续估计能力[12]。在系统层面，低成本雷达-加速度一体化设备也已将自动 target 选择、转换因子标定、边缘计算和无线传输集成到现场部署流程中，并在多座桥梁和停车结构中验证了其工程潜力[13]。这些工作说明，倒挂式雷达和环境静止 target 已经从方法构想走向现场应用，但其多 target 处理多以“选择一个最佳 target”或“多个 target 之间切换、补偿遮挡”为主。

Kalman 滤波为相位预测、分支校正和多源融合提供了更紧密的状态空间基础。经典 Kalman 滤波通过状态预测、观测更新和误差协方差递推，在含噪线性动态系统中实现最优线性估计[14]。最新加速度辅助 Kalman 相位方法进一步把 FMCW 雷达相位解缠和降噪统一起来：以雷达相位及其变化率作为状态，用加速度输入预测相位演化，再用预测相位对 wrapped phase 进行 2π 分支校正，最后通过 Kalman 更新得到连续且降噪的相位估计[15]。该框架的重要意义在于，它不再把相位解缠视作滤波前的独立预处理，而是在递推估计过程中同时完成相位预测、分支选择和噪声抑制。不过，其状态变量仍主要对应单一 target 的 LoS 连续相位，观测方程也基本是单通道形式；当倒挂式雷达面对多个静止参考 target 时，该模型尚未充分利用多个 target 对同一结构运动的冗余观测关系。

此外，实际监测中的不同 target 观测质量并不一致。强反射 target 不一定具有最稳定的 IQ 轨迹，几何方向合适的 target 也可能受遮挡、多径或复合散射影响；同一 target 的可靠性还可能随车辆经过、环境变化和结构运动幅值而变化。自适应滤波和测量噪声协方差估计研究表明，观测噪声协方差可以作为表达不同观测源可靠性的关键参数，低质量观测应在滤波更新中获得较小权重，高质量观测则可更充分地校正状态预测[16]。这一思想对多静止参考 target 的雷达相位融合具有直接启发：与其把多个 target 仅作为候选列表或遮挡时的替代通道，不如在相位域内把它们看作同一结构状态的多通道投影观测，并根据 target-wise 测量噪声协方差调节其贡献。

综上，既有研究已经分别解决或部分解决了毫米波相位位移测量、相位解缠、加速度辅助位移估计、倒挂式环境 target 利用、target occlusion 管理和低成本系统部署等问题，但这些研究之间仍存在一个值得进一步整合的空白：对于同一结构测点，多个环境静止 reference targets 本质上观测的是同一个结构运动，只是各自沿不同 LoS 方向对该运动进行投影。现有工作多从 target selection 或 target switching 角度使用这些目标，尚未将多个 wrapped phase 统一建模为共享结构主相位的多行观测。因此，本文拟吸收 mmVib 等工作中的相位-距离关系和 IQ 几何认识，吸收倒挂式雷达研究中的环境 target、转换因子标定和加速度辅助思想，吸收 Kalman 相位解缠/降噪框架中的预测辅助分支校正机制，并引入 target-wise 测量噪声协方差表达不同参考 target 的观测可靠性。在此基础上，将状态从“某一个 target 的 LoS 相位”提升为“结构振动方向主相位”：由加速度预测共享主相位，每个静止 target 的 wrapped phase 通过方向转换系数构成观测矩阵的一行，再通过预测辅助相位校正和多通道 Kalman 更新实现多静止参考目标的相位域融合。

### 参考文献

[1] MA Z, CHOI J, SOHN H. Structural displacement sensing techniques for civil infrastructure: A review[J]. Journal of Infrastructure Intelligence and Resilience, 2023, 2: 100041.

[2] WU R T, JAHANSHAHI M R. Data fusion approaches for structural health monitoring and system identification: Past, present, and future[J]. Structural Health Monitoring, 2020, 19(2): 552-586.

[3] GINDY M, VACCARO R, NASSIF H, VELDE J. A state-space approach for deriving bridge displacement from acceleration[J]. Computer-Aided Civil and Infrastructure Engineering, 2008, 23: 281-290.

[4] LI C, CHEN W, LIU G, YAN R, XU H, QI Y. A noncontact FMCW radar sensor for displacement measurement in structural health monitoring[J]. Sensors, 2015, 15(4): 7412-7433.

[5] TAKAMATSU H, HINOHARA N, SUZUKI K, SAKAI F. Experimental analysis of accuracy and precision in displacement measurement using millimeter-wave FMCW radar[J]. Applied Sciences, 2025, 15(6): 3316.

[6] GUO J, HE Y, JIANG C, JIN M, LI S, ZHANG J, XI R, LIU Y. Measuring micrometer-level vibrations with mmWave radar[J]. IEEE Transactions on Mobile Computing, 2023, 22(4): 2248-2261.

[7] LIU J, LI Y, GU C. Solving phase ambiguity in interferometric displacement measurement with millimeter-wave FMCW radar sensors[J]. IEEE Sensors Journal, 2022, 22(9): 8482-8489.

[8] GUERZONI G, FAGHAND E, VINCENZI L, BASSOLI E, VITETTA G M. A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring[J]. Mechanical Systems and Signal Processing, 2025, 235: 112777.

[9] MA Z, HAI L, ZHANG T, WANG B, JING X, ZHANG Q, SOHN H. Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping[J]. Measurement, 2026, 262: 120029.

[10] MA Z, CHOI J, YANG L, SOHN H. Structural displacement estimation using accelerometer and FMCW millimeter wave radar[J]. Mechanical Systems and Signal Processing, 2023, 182: 109582.

[11] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.

[12] MA Z, CHOI J, LEE J, SOHN H. Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion[J]. Mechanical Systems and Signal Processing, 2025, 223: 111888.

[13] MA Z, HAN K, CHOI J, LEE J, KWON O, SOHN H, LIU J, HWANG D, AGGARWAL J, NOH H, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.

[14] KALMAN R E. A new approach to linear filtering and prediction problems[J]. Transactions of the ASME-Journal of Basic Engineering, 1960, 82: 35-45.

[15] MA Z, ZHANG T, ZHU Y, LIN S, LEE J, SOHN H, ZHANG Q. Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring[J]. Mechanical Systems and Signal Processing, 2026, 248: 113991.

[16] LI Z, ZHANG H, ZHOU Q, CHE H. An adaptive low-cost INS/GNSS tightly-coupled integration architecture based on redundant measurement noise covariance estimation[J]. Sensors, 2017, 17(9): 2032.

### 自检清单

- 已只使用本地 `ref_papers/` 中的 PDF 和 `ref_papers/00_primary_references/README.md` 信息，未联网检索。
- 正文引用采用 `[1]` 至 `[16]` 顺序编码，参考文献按正文首次出现顺序排列。
- 正文中出现的每个编号均在文末有对应条目，文末每条参考文献也均在正文中出现。
- 参考文献信息已优先从 PDF 首页、PDF References 或本地精读卡片核对；未确认额外页码时未编造。
- 综述覆盖了结构位移监测、多传感融合、毫米波雷达相位测量、相位解缠、倒挂式环境 target、Kalman 融合和多 target 主相位观测链条。
- 已避免将本文表述为“首次提出毫米波雷达结构位移监测”或“首次使用加速度辅助相位解缠”。
- 已区分本文多 target 的含义：同一结构测点在多个环境静止散射体 LoS 方向上的投影观测，而不是多个结构测点的多点监测。
