### 文献综述正文

结构位移与振动响应是桥梁、建筑等土木基础设施安全评估、模态识别、有限元模型修正和服役状态预警的重要观测量。已有综述指出，LVDT、加速度计、应变、GNSS、视觉、激光、LiDAR 和雷达等位移测量技术在精度、采样率、安装条件、长期稳定性和多点测量能力上各有取舍；其中雷达具备非接触、远距离、高采样率和全天候测量潜力，但在真实工程现场仍面临目标识别、LOS 位移到结构振动方向的转换、多路径杂波、遮挡、供电通信和相位缠绕等限制[1]。早期 FMCW 雷达结构位移研究已经证明，利用距离维分辨多个反射目标并跟踪 beat signal 相位，可以同时测量不同距离目标的毫米级位移[2]。这类工作奠定了雷达相位用于结构位移测量的基础，也提示“被跟踪的 target 到底是什么”会直接影响相位质量、几何转换和长期可用性。

毫米波雷达的短波长进一步放大了微小位移引起的相位变化，为微米级振动和结构小位移监测提供了物理基础。mmVib 从 IQ 几何、振动信噪比和多信号合并角度说明，商用 FMCW 毫米波雷达可通过多 chirp、多天线信息提高微振相位估计精度，并在多径和多目标环境中提取振动信号[3]。针对 77-81 GHz FMCW 雷达的精度实验也表明，慢时间 IF 相位在受控条件下可对应微米量级位移精度[4]。不过，毫米波相位灵敏度越高，对目标稳定性、IQ 轨迹纯净性和相位解缠连续性的要求也越高。对于倒挂式结构监测，问题还进一步改变：雷达不是固定在地面参考点观测结构目标，而是安装在结构测点上并随结构共同运动，视场内的地面、桥下构件、支架等静止散射体因雷达自身运动产生相位变化，成为恢复结构位移的环境参考 target[5]。因此，本文关注的核心不只是“如何从相位估计位移”，还包括“如何在自然反射环境中在线选出可靠参考 target”。

围绕倒挂式毫米波雷达，Ma 等提出将加速度计与 FMCW 毫米波雷达共址安装在结构测点，通过初始同步数据从周围环境反射目标中自动选择 best target，并估计 LOS 位移到结构振动方向位移的转换系数[5]。这一思路把传统“固定雷达观测结构靶标”的几何关系转化为“运动雷达观测静止环境散射体”的参考关系，为低成本、免固定基准点的结构位移监测提供了重要路径。后续长期桥梁监测研究进一步考虑车辆等移动物体造成的间歇性雷达 target 遮挡，提出多 good targets 选择、遮挡检测、目标切换以及雷达、应变和加速度的连续融合框架[6]；低成本系统化研究则将自动校准、边缘计算和现场部署集成到紧凑传感系统中，验证了雷达与加速度融合在中小跨结构长期监测中的工程可行性[7]。这些工作已经从人工选靶走向自动 target selection 和 target management，但其基本对象多仍是 range spectrum 中的目标或单一 best range target。自然反射环境中，一个 rangeBin 可能同时包含多个不同角度、不同散射强度和不同稳定性的散射体，直接追踪该 rangeBin 的总复数相位会形成混合 phasor，使 IQ 轨迹畸变、相位中心漂移，并使后续转换系数不再对应单一清晰的物理方向。

range-angle joint phase tracking 为上述问题提供了关键依据。mmWBat 明确提出在 range-angle 联合维度中定位多个微动目标，并跟踪对应 component 的干涉相位演化，从而实现全视场微动映射和量化[8]。面向结构健康监测的 mmSHM 进一步指出，传统 FMCW 方法若仅按 range profile 区分目标，在同 rangeBin 多目标耦合、相邻 rangeBin 干扰和大位移跨 bin 时会发生相位混叠或波形失真；其改进方法在 MIMO LFMCW 数据的距离-角度联合维度中隔离目标，并从选定 range-angle component 中提取振动位移[9]。这些工作说明，对于相位型微位移测量，有价值的处理单元不必止步于 rangeBin，而可以是具有空间方向约束的 range-angle component。

低通道 MIMO-FMCW 研究也为本文方法提供了可实现链路。多人生命体征监测虽然不是结构位移实证，但直接展示了商用 FMCW/MIMO 雷达可在同一 rangeBin 或同一径向距离内利用角度维分离多个目标，并从各自方向提取相位 slow-time 信号[10][11]。TI MIMO Radar 应用报告给出了 TDM/BPM MIMO、虚拟阵列和 Angle FFT 的工程处理基础，也说明真实角分辨率受虚拟阵列孔径限制，zero-padding 只能细化谱网格而不能改变物理分辨率[12]。进一步的 MIMO-FMCW 多目标方法采用 Range FFT、Capon、2D-CFAR、DBSCAN 和 LCMV beamforming，在 range-angle map 上确定目标范围与角度后形成每个目标的 slow-time 复数信号[13]。这些文献并不意味着低通道雷达能够无条件分开所有近角度散射体，但足以说明：当角度可分、波束泄漏可控且复数通道数据被保留下来时，将参考目标从 rangeBin 升级为 range-angle bin 或 angle cluster 是可行且必要的。

在线 target selection 还需要处理候选目标的持续存在性和结构运动相关性。FMCW 雷达多目标跟踪研究中的 track management 通常将未关联量测初始化为 candidate track，再用 M-out-of-N 逻辑根据最近窗口内成功更新次数决定保留、确认或删除[14]。本文并不进行完整运动目标跟踪，也不需要估计候选散射体的运动状态，但可以借鉴这种“候选目标必须在一段时间内稳定出现”的确认思想，将 range-angle 候选峰在滑动窗口内的出现率作为稳定参考 target 的前置条件。另一方面，已有雷达-加速度结构位移融合研究常利用加速度响应确定有效校准时段、结构频带或滤波频带[5][7]；本文可将该信息改造成 target selection 阶段的结构频带先验，用候选 target 的中心化复数 IQ slow-time 频谱能量占比判断其相位变化是否主要由结构振动驱动，而不是由随机杂波、弱散射、人体车辆等动态干扰或低信噪比噪声主导。

综上，已有研究分别证明了毫米波相位微位移测量、倒挂式环境参考 target、range-angle 相位跟踪、低通道 MIMO-FMCW 角度分离以及目标窗口确认的可行性。本文第二个创新点并不声称首次提出 AoA、MIMO-FMCW 或 range-angle 处理，而是在倒挂式结构位移监测场景下吸收并改造这些思想：保留复数 range-angle map，在距离-角度二维幅值图中发现候选峰；对同一 rangeBin 内角度可分的散射体拆分，对角度接近的 peaks 合并为等效 angle cluster，形成 `T=(b,C)` 的 range-angle reference target；再用滑动窗口出现率和加速度识别的结构频带一致性筛除不稳定或非结构驱动目标。该选择阶段不依赖相位解缠和已知转换系数，只使用幅值、出现率、复数 IQ 频谱和结构频带先验，最终输出稳定且结构相关的复数 slow-time 观测，供后续转换系数估计与 Kalman 融合使用。这样既继承了已有毫米波相位测量和 target management 的成果，又针对自然反射场景中 rangeBin 混合相位导致的参考 target 不确定性进行了面向结构位移恢复的改造。

### 参考文献

[1] MA Z, CHOI J, SOHN H. Structural displacement sensing techniques for civil infrastructure: A review[J]. Journal of Infrastructure Intelligence and Resilience, 2023, 2: 100041.

[2] LI C, CHEN W, LIU G, et al. A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring[J]. Sensors, 2015, 15(4): 7412-7433.

[3] GUO J, HE Y, JIANG C, et al. Measuring Micrometer-Level Vibrations With mmWave Radar[J]. IEEE Transactions on Mobile Computing, 2023, 22(4): 2248-2261.

[4] TAKAMATSU H, HINOHARA N, SUZUKI K, et al. Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar[J]. Applied Sciences, 2025, 15(6): 3316.

[5] MA Z, CHOI J, YANG L, et al. Structural displacement estimation using accelerometer and FMCW millimeter wave radar[J]. Mechanical Systems and Signal Processing, 2023, 182: 109582.

[6] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.

[7] MA Z, HAN K, CHOI J, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.

[8] XIONG Y, LI S, GU C, et al. Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View[J]. Research, 2021, 2021: 9787484.

[9] LI S, XIONG Y, SHEN X, et al. Multi-scale and full-field vibration measurement via millimetre-wave sensing[J]. Mechanical Systems and Signal Processing, 2022, 177: 109178.

[10] AHMAD A, ROH J C, WANG D, et al. Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor[C]//2018 IEEE Radar Conference (RadarConf18). Piscataway: IEEE, 2018: 1450-1455.

[11] XU Z, SHI C, ZHANG T, et al. Simultaneous Monitoring of Multiple People's Vital Sign Leveraging a Single Phased-MIMO Radar[J]. IEEE Journal of Electromagnetics, RF and Microwaves in Medicine and Biology, 2022, 6(3): 311-320.

[12] RAO S. MIMO Radar[R]. Dallas: Texas Instruments, 2018.

[13] YANG Y, QU L, YANG Y, et al. Multitarget Vital Signs Detection Based on MIMO-FMCW Radar[C]//2024 Photonics & Electromagnetics Research Symposium (PIERS). Piscataway: IEEE, 2024: 1-10.

[14] KIM D B, HONG S M. Multiple-target tracking and track management for an FMCW radar network[J]. EURASIP Journal on Advances in Signal Processing, 2013, 2013: 159.

### 自检清单

- 已只使用本地 `ref_papers/` 中存在的 PDF 和两个 README 摘要卡片，未联网补充文献。
- 已按最新要求解除原 `1200-1800` 字限制，优先保留完整论证链和文献关系。
- 正文引用编号 `[1]` 至 `[14]` 与文末参考文献一一对应，文末每条均在正文出现。
- 参考文献按正文首次出现顺序排列，并采用 GB/T 7714 风格整理。
- 已覆盖结构位移监测、毫米波相位测量、倒挂式环境参考 target、range-angle phase tracking、低通道 MIMO-FMCW、target selection、窗口确认和结构频带一致性。
- 已避免把本文贡献表述为首次提出 AoA、MIMO-FMCW 或 range-angle 处理。
- 已将生命体征多人分离文献限定为同 rangeBin 角度分离和复数相位 slow-time 提取的可行性证据，没有写成结构位移实证。
- 已明确 target selection 阶段为 unwrap-free / beta-free，只使用幅值、出现率、复数 IQ 频谱和加速度结构频带先验。
- 已避免把 zero-padding 写成提高真实角分辨率，并强调角分辨率受虚拟阵列孔径限制。
