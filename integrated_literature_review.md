# 第二章 文献综述

本章围绕倒挂式毫米波 FMCW 雷达与加速度计共址传感的结构位移估计问题展开。该类方法的核心在于：雷达安装于梁体测点并随结构共同运动，周围近似静止的环境散射体成为相对位移观测的参考目标，雷达相位中包含结构测点相对参考目标的视线方向距离变化；加速度观测则为结构动力响应提供高采样率先验。与传统固定式雷达直接观测结构靶标不同，倒挂式布置没有改变 FMCW 相位测距的基本物理关系，但改变了参考目标的定义、目标可靠性评价、视线方向转换关系和多目标相位融合方式。因此，本章以“结构位移监测需求—倒挂式毫米波雷达参考目标选择—视线方向转换系数建模—多目标相位融合”为主线梳理国内外研究现状，并在各节末尾归纳尚未解决的问题，为本文研究内容和创新点的提出提供依据。

首先，综述结构位移监测、毫米波雷达位移感知和多源融合的发展现状，明确本文研究所处的传感技术背景。其次，围绕倒挂式安装条件下环境参考目标的识别与筛选，分析从距离单元目标到距离-角度目标的研究基础和不足。再次，围绕视线方向位移到结构振动方向位移的转换问题，讨论方向转换系数、角度几何关系和复合散射目标等效稳定性。最后，围绕相位解缠、加速度辅助 Kalman 滤波和多目标观测融合，梳理多参考目标相位信息统一恢复结构主位移的理论基础。

## 2.1 结构位移监测与毫米波雷达感知研究现状

结构位移和振动响应是桥梁、建筑等土木基础设施安全评估、模态识别、损伤诊断、荷载试验、有限元模型修正和服役状态预警中的基础观测量。相较于加速度、应变等局部响应，位移更直接反映结构整体变形、支承约束变化和服役状态演化，因此在长期健康监测和灾后快速评估中具有不可替代的意义。Ma、Choi 和 Sohn 对土木基础设施结构位移感知技术进行了系统综述，指出位移测量方法通常需要在测量精度、安装条件、参考基准、长期稳定性和现场适应性之间权衡[1]。因此，结构位移监测的难点并不只是传感器本身的分辨率，而是如何在复杂工程现场持续获得具有明确物理含义的位移观测。

从接触式和间接测量方法看，LVDT 等位移计可以提供较高精度，但往往依赖稳定外部参考点，在桥下交通、水域、复杂施工或长期监测场景中布设成本较高[1]。加速度计布设方便、采样率高，适合捕捉结构动态响应，但位移需要由加速度双积分获得，低频噪声、初值误差和传感器偏置会被持续放大。针对这一问题，Gindy 等较早采用状态空间模型由桥梁加速度推导位移，说明动力学约束可用于抑制积分漂移[3]；Sarwar 和 Park 将共址加速度与应变信息结合以估计桥梁位移，利用不同观测量之间的互补关系降低单一传感器误差[4]；Cho 等进一步提出基于 Kalman 滤波的多指标融合方法，在无外部参考位移计条件下融合加速度、应变等多源信息重构桥梁位移[5]。GNSS 能提供绝对位移观测，但其采样率和垂向精度对中小跨桥梁毫米级小振动仍有限，因此也常与加速度计形成互补融合系统[6]。此外，倾角、应变和无线传感网络等方法可降低位移直接测量难度，但通常需要结构模型、边界条件或经验转换关系作为支撑[14,15]。

非接触式位移测量近年来发展迅速。视觉方法可避免传感器直接接触结构，Perez 和 Mora 构建了视觉结构位移测量系统，验证了相机测量在结构响应提取中的可行性[7]；Choi 等提出基于图像凸包优化的无靶标视觉位移传感方法，降低了人工靶标布设需求[8]；Lee 等分别针对服役桥梁中光照退化和相机任意布设问题改进视觉位移测量流程，提高了复杂现场适应性[9,10]。近期基于幅值-相位融合的跨尺度视觉位移估计进一步说明，视觉方法也在尝试同时兼顾大位移趋势和小幅动态响应[39]。LiDAR 方法可以获取三维空间点云，Cha 等通过三维空间优化估计桥梁位移，Kaartinen 等则系统总结了 LiDAR 在土木基础设施健康监测中的应用潜力[11,12]。激光测量在有限元模型验证和高精度现场测量中也有应用，Dai 等利用激光现场测量支撑桥梁有限元模型校核[13]。然而，视觉、LiDAR 和激光方法分别受光照、遮挡、视线、测站稳定性、点云密度和现场布设条件限制，在全天候、长期和低维护监测中仍存在工程约束。

多源信息融合因而成为结构健康监测的重要方向。Wu 和 Jahanshahi 从结构健康监测和系统识别角度总结了数据融合的发展脉络，强调不同传感源在空间尺度、时间频带和噪声特性上的互补性[2]。Zhu、Lu 和 Zhu 面向不同采样频率的多类型传感数据提出 multi-rate Kalman filtering，为多速率结构响应重构提供了状态空间融合框架[40]。这类研究表明，加速度、位移、应变、GNSS、视觉、LiDAR 和雷达等观测源并非彼此替代，而是可以在统一估计框架中弥补单一传感器在低频漂移、采样率、参考基准或环境适应性方面的不足。

雷达位移测量为结构监测提供了一类具有工程吸引力的非接触方案。FMCW 雷达通过调频连续波获得距离分辨能力，可在不同 range bin 中区分多个散射目标，并进一步利用目标回波相位变化估计雷达视线方向的微小距离变化。Li 等较早将非接触 FMCW 雷达用于结构健康监测中的位移测量，验证了 FMCW 相位法在结构位移估计中的可行性[16]；Pramudita 等进一步面向桥梁结构位移估计开展 FMCW 雷达实验，说明雷达不仅能够测量单一反射体位移，也具备多 target 分辨与毫米级位移测量能力[17]。在更大尺度的桥梁监测中，微波雷达干涉技术已形成较丰富应用：Zou 等总结了微波雷达干涉在可持续桥梁监测中的策略与优势[18]；Huang 等将地基雷达干涉用于多线高速铁路钢桁桥动态性能监测[19]；Zhang 等实现了 1200 m 级悬索桥多点位移雷达测量[20]；Pagnini 等采用多单站 MIMO 雷达识别拱桥横向位移[24]。近年来，面向桥梁非接触监测的高精度毫米波雷达系统和简支梁桥振动响应分析也进一步拓展了毫米波雷达在现场结构监测中的应用边界[21,22]。此外，主动转发器辅助的 DC coupled radar 可改善特定场景下雷达位移测量的可观测性，但需要额外布设专用反射或转发装置[23]。

毫米波微振感知研究进一步深化了相位位移测量的理论基础。mmVib 从 IQ 复平面几何出发，将目标微振引起的回波相位变化解释为复数轨迹中的圆弧运动，并通过振动信噪比、多 chirp 合并和多天线分离说明商用 FMCW 毫米波雷达可以感知微米级振动[25]。Takamatsu 等对毫米波 FMCW 雷达位移测量的精度和重复性进行了实验分析，说明硬件相位稳定性和实验条件会直接影响测量结果[26]；Chen 等研究了加性噪声下高鲁棒位移运动雷达感知方法，强调相位解调和噪声抑制的重要性[27]；Xiong 等提出扫描微波测振方法，将相位编码波束扫描用于全场振动测量[28]。Piotrowsky 等围绕 FMCW 雷达高精度距离测量开展了一系列研究，分别讨论了中距离微米级测距、FMCW 传感器高精度测距实现以及基于无模糊相位算法的个位数微米级距离测量[29,30,31]。国内研究中，高昂针对毫米波雷达两近距离目标微动位移提取问题展开研究，也说明近距离多目标耦合会影响微动相位提取[32]。这些研究共同表明，毫米波雷达相位信息具有很高的位移灵敏度，但其精度依赖硬件相位稳定性、目标反射质量、相位连续性和复杂散射环境控制。

与固定雷达观测结构目标不同，Ma、Choi、Sohn 等提出将 FMCW 毫米波雷达和加速度计共址安装在结构测点处，使雷达随结构共同运动，并利用周围环境中的地面、桥下构件或其他静止散射体作为参考 target。结构运动会改变雷达与这些静止 target 之间的相对距离，该变化反映在 FMCW 回波相位中；通过短时同步数据，可以自动选择与加速度积分位移最一致的 target，估计 LoS 位移到结构实际振动方向位移的 direction conversion factor，并融合雷达低频位移和加速度高频响应[33]。在连续桥梁位移估计研究中，Ma 等将毫米波雷达、应变计和加速度计融合，用多个 good targets 支撑遮挡或单目标失效情况下的连续位移恢复[34]；随后又进一步提出加速度辅助毫米波雷达干涉方法，显式考虑间歇性雷达目标遮挡对桥梁位移估计的影响[35]。面向工程部署，Ma 等开发并现场验证了低成本高精度雷达-加速度融合位移传感系统，将自动校准、边缘计算和现场应用集成到紧凑传感系统中[36]；Lee 等则从低成本 MEMS 加速度计与 FMCW 毫米波雷达融合角度改进结构加速度估计[37]。此外，铁路桥场景中的毫米波雷达、加速度计和非专用多模态感知研究表明，该类共址传感思路正在向更复杂交通基础设施扩展[38]。

综上所述，已有研究已经形成较完整的结构位移监测技术谱系，也证明了毫米波雷达相位测量和雷达-加速度融合的可行性。本文研究并非重新建立结构位移传感或 FMCW 相位测距的基本理论，而是在倒挂式安装这一特殊观测关系下进一步回答三个问题：自然环境中的哪些静止散射体可作为可靠参考目标，不同参考目标的 LoS 位移如何转换为结构振动方向位移，以及多个参考目标的相位观测如何在同一状态空间框架中统一恢复结构位移。上述问题构成本文后续研究内容的逻辑起点。

## 2.2 倒挂式毫米波雷达环境参考目标选择研究

倒挂式毫米波雷达利用环境静止散射体作为参考 target，这一思想已经由 Ma 等人的雷达-加速度融合研究初步建立[33]。在此基础上，连续桥梁位移估计研究进一步引入多个 good targets 与应变、加速度信息融合，以增强目标遮挡或单目标质量下降时的位移恢复能力[34]；后续加速度辅助毫米波雷达干涉研究则将间歇性 target occlusion 作为独立问题处理，强调参考目标可见性对连续位移估计的影响[35]。低成本系统部署、结构加速度估计和铁路桥多模态感知研究进一步表明，环境静止 target 的利用已经从实验验证走向现场系统化应用[36,37,38]。但现有方法多以 range spectrum 中的目标或单一 best range target 为基本对象，即便考虑多个 good targets，也主要服务于遮挡时的切换、漂移补偿或连续位移恢复。这种处理隐含一个前提：被选 range target 的相位序列能够近似代表一个稳定 LoS 几何方向，或至少由单一主散射体主导。然而，自然反射环境与人工角反射器不同，一个 range bin 可能同时包含多个不同角度、不同反射强度和不同稳定性的散射体。直接追踪该 range bin 的总复数相位会形成混合 phasor，导致 IQ 轨迹畸变、相位中心漂移，并使后续转换系数不再对应清晰的物理方向。

Range-angle joint phase tracking 为缓解 rangeBin 混合相位问题提供了关键依据。mmWBat 明确提出在 range-angle 联合维度中定位多个微动目标，并跟踪对应 component 的 interferometric phase evolution，从而实现全视场微动映射和量化[41]。面向结构健康监测的 mmSHM 进一步指出，传统 FMCW 方法若仅按 range profile 区分目标，在同 rangeBin 多目标耦合、相邻 rangeBin 干扰和大位移跨 bin 时会发生相位混叠或波形失真；其改进方法在 MIMO LFMCW 数据的距离-角度联合维度中隔离目标，并从选定 range-angle component 中提取振动位移[42]。Full-field 3D microwave sensing 则进一步表明，多个 LoS 位移与空间几何关系可以共同用于重构结构坐标系响应，为后续把角度信息用于转换关系初始化提供了物理基础[43]。

低通道 MIMO-FMCW 研究也为本文方法提供了可实现链路。TI MIMO Radar 应用报告给出了 TDM/BPM MIMO、虚拟阵列和 Angle FFT 的工程处理基础，同时说明真实角分辨率受虚拟阵列孔径限制，zero-padding 只能细化谱网格而不能改变物理分辨率[44]。多人生命体征监测虽然不是结构位移实证，但 Ahmad 等、Xu 等和 Yang 等的研究均直接展示了商用 FMCW/MIMO 雷达可在同一 rangeBin 或同一径向距离内利用角度维分离多个目标，并从各自方向提取相位 slow-time 信号[45,46,47]。在更一般的多目标参数估计问题中，有限天线条件下的 range-angle 检测和 range-Doppler-angle 联合估计说明低通道雷达仍可通过模型化处理提升多目标分辨能力[48,49]；稀疏谱拟合和频率-空间自适应数字波束形成可用于改善 range-angle 解耦和角度估计[50,51]；宽带 XL MIMO-FMCW 的解耦估计、MIMO 阵列外推、SBL、MUSIC-RELAX、分布式 MIMO 和多相码设计等研究进一步扩展了角度分辨和多目标定位的算法空间[52,53,54,55,56,57,58]；非均匀虚拟阵列优化、自动驾驶雷达方位超分辨、Transformer AoA、稀疏 Bayesian RV 图估计以及联合信道-距离-Doppler 估计则展示了学习型和稀疏贝叶斯方法在雷达角度增强中的潜力[59,60,61,62,63]。

需要指出的是，角度处理方法的有效性仍受虚拟阵列孔径、SNR、旁瓣、相干散射、TDM 相位补偿和通道幅相标定等因素限制。稀疏恢复、SBL、RELAX、学习型超分辨等方法虽然可能提高谱峰分辨率，但它们往往主要优化单帧定位或检测性能，并不天然保证分离后的复数 slow-time 相位在微位移测量中长期连续、物理一致。因此，在倒挂式结构位移估计中，AoA 或超分辨方法更适合作为构建 range-angle reference target 的候选处理手段和对照基线，其输出仍需结合时间稳定性和结构运动相关性进一步筛选。

在线参考目标选择还需要处理候选目标的持续存在性和结构运动相关性。FMCW 雷达多目标跟踪研究中的 track management 通常将未关联量测初始化为 candidate track，再用 M-out-of-N 逻辑根据最近窗口内成功更新次数决定保留、确认或删除[64]。本文并不进行完整运动目标跟踪，也不需要估计环境散射体的运动状态，但可以借鉴这种“候选目标必须在一段时间内稳定出现”的确认思想，将 range-angle 候选峰在滑动窗口内的出现率作为稳定参考 target 的前置条件。另一方面，已有雷达-加速度结构位移融合研究常利用加速度响应确定有效校准时段、结构频带或滤波频带[33,36]；本文可将该信息转化为目标选择阶段的结构频带先验，用候选 target 的中心化复数 IQ slow-time 频谱能量占比判断其相位变化是否主要由结构振动驱动，而不是由随机杂波、弱散射、人体车辆等动态干扰或低信噪比噪声主导。这样的顺序能够避免循环依赖：若在 target 可靠性尚未确认前就依赖相位解缠或转换系数估计，错误分支和错误 beta 可能反过来误导 target 质量判断。

综上所述，已有 range-angle 微动测量和 MIMO-FMCW 多目标分离研究证明，复数 range-angle component 可以承载可用于相位跟踪的 slow-time 信息；倒挂式雷达研究则证明了环境静止 target 可用于结构位移恢复。然而，二者尚未充分结合，现有倒挂式方法仍主要以 rangeBin 或 best target 为参考目标基本单元，难以处理自然散射环境中的同距离单元多角度混合相位。针对这一不足，本文的第一项工作将传统 rangeBin 参考目标扩展为 range-angle reference target，通过二维候选峰、同 rangeBin 角度合并、滑动窗口出现率和加速度结构频带一致性，在线筛选稳定且与结构振动相关的环境参考 target。该阶段不依赖完整相位解缠和转换系数先验，从而避免在目标可靠性尚未确认时引入错误分支或错误转换关系。

## 2.3 视线方向转换系数与复合散射目标稳定性研究

雷达相位首先对应散射体沿雷达视线方向的距离变化，而工程上关注的是结构坐标系下的竖向、横向或某一主振动方向位移，因此 LoS 位移到结构位移的方向转换是毫米波雷达结构监测中的必要环节。Ma 等人的倒挂式雷达-加速度融合工作已经通过短时同步数据估计 direction conversion factor，并将其用于雷达位移与加速度位移之间的互补融合[33]；连续桥梁位移估计研究将多个 good targets 的转换因子标定作为雷达、应变和加速度融合的前置步骤[34]；考虑 target occlusion 的研究进一步说明转换因子与目标可用性、目标切换和遮挡补偿密切相关[35]；低成本系统现场部署研究则将转换因子估计纳入自动校准流程，服务于长期工程应用[36]。这些研究确立了转换因子标定的基础地位，也表明进一步研究的重点应从转换因子概念本身转向其在自然散射环境中的估计尺度、适用条件和稳定性。

本文需要进一步关注的是转换系数的观测尺度和稳定性。若直接对整个 rangeBin 的总相位拟合 beta，所得系数可能并非某个物理反射点的 LoS 几何投影，而是由多个散射体的幅值、相对相位、角度分布和结构位移共同决定的混合等效系数。该系数可能在某一标定窗口内看似有效，却随时间窗口、散射状态或位移幅值变化而漂移。range-angle target 因而提供了更合理的转换系数估计尺度：对于角度可分的散射体，可分别建立 LoS 到结构振动方向的转换关系；对于角度接近且难以可靠分开的散射簇，则可将其作为一个等效 angle cluster，并估计其等效转换系数。

AoA 与几何关系可以为转换系数提供初值，但不能被简单等同于转换系数本身。Full-field 3D microwave sensing 已经表明，工程上真正关心的是结构坐标系位移，多个 LoS 位移可通过测点位置、雷达视线和坐标转换关系重构为结构坐标系响应[43]。MIMO-FMCW 的虚拟阵列和 Angle FFT 为目标视线方向估计提供基础处理框架[44]；多人生命体征和多目标检测研究说明，角度维可以帮助从同距或近距目标中提取相对独立的 slow-time 相位观测[45,46,47,48,49]；稀疏谱拟合、自适应波束形成、阵列外推、MUSIC/RELAX、SBL 和学习型 AoA 方法则为角度门控复数观测提供了更丰富的算法选择[50,51,52,53,54,55,56,57,58,59,60,61,62,63]。然而，倒挂式自然环境中选出的 target 可能并非单一散射点，而是 angle cluster 或复合散射体。此时 beta 不再严格对应某个物理点的几何投影系数，而应被解释为该散射簇在当前观测条件下的等效转换系数。

复合 target 的等效转换系数是否稳定，取决于散射体几何投影、相对幅值和结构位移幅值。当 target 内主要散射体的 LoS 投影系数接近、单一散射体占主导，或结构位移幅值不足以引起明显相对相位变化时，固定 beta 近似合理；当多个强散射体的几何投影差异较大，且相对相位会随结构位移显著变化时，固定 beta 会表现为窗口相关和散射状态相关的漂移。直观地说，同一 angle cluster 内各散射体的幅值权重、相对初相和投影系数共同决定总相位；车辆遮挡、弱散射消失或结构位移幅值变化都可能改变这些权重，使一个窗口内有效的 beta 在另一个窗口内失效。既有微振 IQ 几何研究已经说明，多径、背景和复合散射会影响相位轨迹形态[25]；range-angle full-field 研究也说明，若多个目标落入同一 range 或 range-angle 单元，传统单单元相位提取会出现耦合和错误频率成分[42]。这些现象在倒挂式环境参考 target 中并非例外，而是需要被显式建模和筛查。

转换系数估计还依赖可信的连续相位。毫米波短波长提高了位移灵敏度，也使 wrapped phase 更容易跨越 \(2\pi\) 分支；若直接用包裹相位拟合 beta，分支跳变会被误认为实际位移变化，从而污染转换因子。Liu、Li 和 Gu 针对毫米波 FMCW 雷达干涉位移测量中的相位模糊问题提出 radar-only 解缠思路[66]；Guerzoni 等利用 Doppler 信息辅助 MIMO 毫米波雷达相位解缠，以适应结构健康监测中的较快位移变化[67]；Ma 等提出 multi-chirp adaptive phase unwrapping，通过多 chirp 相位变化率预测下一时刻相位分支[68]；最新加速度辅助 Kalman 方法则将相位降噪与解缠统一在状态空间递推框架中[69]。这些研究说明，相位连续性不能被当作默认条件。因此，目标选择阶段不宜依赖完整全时程解缠结果，也不宜依赖尚未确定的 beta。较为合理的策略是先采用不依赖完整解缠和转换系数先验的 target 质量指标完成候选筛选，再在通过筛选的 target 上利用 AoA 几何初值、初始小位移无绕转窗口、短窗口局部连续相位或 Kalman 预测辅助校正相位递推修正 beta。

综上所述，已有研究已经提出并使用 direction conversion factor，但通常默认被标定 target 具有较稳定的 LoS 物理方向。自然反射环境中的 rangeBin 或 angle cluster 可能由多个散射体叠加而成，其转换系数更应被理解为观测单元层面的等效关系，并需要分析其稳定条件。针对这一不足，本文的第二项工作在 range-angle target 尺度上建立转换系数估计与等效稳定性分析，区分角度可分 target 和角度接近的等效 cluster，利用 AoA 几何初值与预测辅助局部连续相位递推修正 beta，并将 beta 稳定性作为 target 质量、融合权重或测量噪声设置的重要依据。

## 2.4 多参考目标相位解缠与状态空间融合研究

相位解缠和噪声抑制是毫米波雷达位移恢复中的核心问题。传统 Itoh 类方法依赖相邻采样间真实相位变化小于 \(\pi\) 的假设，在大幅、快速或低采样率结构振动中容易失效。为突破这一限制，已有研究将连续波雷达中的线性相位解调思想迁移到单通道 FMCW 雷达，通过 slow-time 数据合成等效正交 I/Q 信号，使 MDACM 等方法能够用于 FMCW 干涉位移测量[66]；MIMO 毫米波雷达研究进一步利用 Doppler 信息预测跨帧相位变化，在快速运动目标中恢复连续相位轨迹[67]；multi-chirp 自适应解缠方法利用多 chirp 估计相位变化率并预测下一时刻相位区间，在不依赖额外传感器的条件下处理大位移相位缠绕[68]。这些方法扩展了 radar-only 位移恢复能力，但其核心通常仍是对某一目标的 LoS 相位轨迹进行解缠。

Kalman 滤波通过状态预测、观测更新和误差协方差递推，在含噪动态系统中实现递推估计，是多源融合、相位预测和降噪的重要工具[65]。在自适应滤波方面，Mehra 早期系统讨论了基于创新统计和协方差匹配的自适应滤波思路，为动态调整噪声统计量提供了理论基础[71]；Mohamed 和 Schwarz 将自适应 Kalman 滤波用于 INS/GPS 融合，说明测量噪声协方差调节可改善多传感器导航估计的鲁棒性[72]；Li 等进一步在低成本 INS/GNSS 紧耦合架构中利用冗余量测估计测量噪声协方差，体现了观测质量驱动权重调节的工程意义[70]。最新加速度辅助 Kalman 相位方法进一步把 FMCW 雷达相位解缠和降噪统一起来：以雷达相位及其变化率作为状态，用加速度输入预测相位演化，再用预测相位对 wrapped phase 进行 \(2\pi\) 分支校正，最后通过 Kalman 更新得到连续且降噪的相位估计[69]。该框架的重要意义在于，它不再把相位解缠视作滤波前的独立预处理，而是在递推估计过程中同时完成相位预测、分支选择和噪声抑制。

然而，既有加速度辅助 Kalman 模型的状态相位主要对应单一 target 的 LoS 连续相位，观测方程也基本是单通道形式。对于倒挂式多环境静止参考 target 场景，不同 target 具有不同视线方向和方向转换系数。如果仍以某一个 target 的 LoS 相位作为统一状态，其他 target 的相位观测都需要额外映射到该状态，物理含义不够自然，也会使状态预测依赖某个特定 target。当该 target 噪声升高、遮挡或临时失效时，整个滤波状态会受到不必要的约束。因此，倒挂式多 target 场景需要一个不依附于任何单一 target、同时能够被所有 target 观测到的共享状态量。

针对这一缺口，多 target 倒挂式场景需要把状态变量从“某个 target 的 LoS 相位”提升为“结构振动方向的共享主相位”。这样，加速度输入可以直接约束结构主运动，而不依附于某个具体 target；各参考 target 的差异则通过转换系数进入观测模型。经过 range-angle target selection 后，进入 Kalman 框架的仍是各 target 的原始包裹相位，而不是已经完整解缠的连续相位；滤波预测先给出结构主相位先验，再映射到各 target 的 LoS 相位分支，用于辅助分支选择和后续局部 beta 修正。该思路能够缓解“转换系数需要连续相位、连续相位又需要转换系数”的循环依赖，使相位分支校正、转换系数更新和状态融合在同一递推框架内协同完成。

在多目标观测更新中，一个重要区别是：多个 target 不应简单地各自恢复位移后再做平均。后处理平均容易掩盖单个 target 的错误分支、转换系数漂移和相位质量变化，也无法在解缠阶段利用目标间冗余性。相反，将各 target 的相位作为同一结构主相位的多通道投影观测，可以在状态更新之前保留 target-wise 几何关系和可靠性差异。当某个 target 噪声升高或临时失效时，只需移除或降权该观测，状态仍可由其他 target 和加速度维持；当多个 target 同时可靠时，它们对同一主相位的冗余约束可抑制单 target 分支误判。

实际监测中的不同 target 观测质量并不一致。强反射 target 不一定具有最稳定的 IQ 轨迹，几何方向合适的 target 也可能受遮挡、多径、复合散射或转换系数漂移影响；同一 target 的可靠性还可能随车辆经过、环境变化和结构运动幅值而变化。自适应滤波研究表明，观测噪声协方差可以作为表达不同观测源可靠性的关键参数：Mehra 的经典工作给出了利用创新序列调整滤波统计量的基本思想[71]，Mohamed 和 Schwarz 在 INS/GPS 融合中验证了自适应噪声调节对传感器融合鲁棒性的作用[72]，Li 等则说明冗余量测可用于在线估计测量噪声协方差并调节观测权重[70]。这一思想可自然扩展到多静止参考 target 的雷达相位融合中：固定过程噪声 \(Q\) 保持结构主相位动力学模型清晰，target-wise adaptive \(R_k\) 表征各 target 的相位噪声、转换系数误差、IQ 稳定性、遮挡异常和创新残差。

综上所述，已有相位解缠和 Kalman 降噪方法证明了预测辅助分支校正的重要性，但其状态变量多对应单一 target 的 LoS 相位；已有倒挂式研究虽使用多个 good targets，却主要服务于遮挡切换或后续补偿，尚未充分利用多个静止参考 target 同时观测同一个结构运动的冗余关系。针对这一不足，本文的第三项工作将 Kalman 状态相位由单目标 LoS 相位改写为结构振动方向主相位，把多个 range-angle reference targets 的 wrapped phase 作为同一结构状态的多通道投影观测，并通过 target-wise 自适应测量噪声表达各 target 可靠性。由此，target 选择、转换系数稳定性和 Kalman 融合形成闭环：稳定 target 获得更大权重，不稳定 target 被降权或剔除，多 target 的冗余观测共同约束结构主相位。

## 2.5 本章小结

本章综述表明，本文研究建立在结构位移监测、毫米波雷达相位测量、倒挂式雷达-加速度融合、range-angle 微动感知和 Kalman 相位解缠等已有研究基础上，重点面向“雷达随结构共同运动并利用自然环境静止散射体作为参考 target”这一具体场景展开。已有研究已经证明了相位可测、融合可行和环境参考目标可用，但仍存在三个尚未充分整合的问题：其一，参考 target 的基本单元仍多停留在 rangeBin 或 best target 层面，缺少面向自然散射环境的 range-angle 在线选择；其二，转换系数通常被视为单一 target 的固定几何标定，缺少对复合 target 等效稳定性的分析；其三，多个静止参考 target 多被用于切换或补偿，缺少在相位域中作为同一结构主相位多通道观测的统一建模。

据此，本文的三项创新形成递进闭环：第一，针对“哪些环境散射体可作为参考 target”的问题，将 rangeBin 参考目标升级为 range-angle reference target，并以不依赖完整相位解缠和转换系数先验的方式进行在线选择；第二，针对“这些 target 的 LoS 相位如何转换到结构振动方向”的问题，在 range-angle target 尺度上分析转换系数估计和复合 target 等效稳定性；第三，针对“多个 target 的 wrapped phase 如何共同恢复同一结构位移”的问题，将 Kalman 状态定义为结构主相位，并将多 target 相位作为多通道投影观测进行融合。由此，论文主线形成从参考目标识别、转换关系建模到多目标相位融合的完整逻辑链条。

## 参考文献

[1] MA Z, CHOI J, SOHN H. Structural displacement sensing techniques for civil infrastructure: A review[J]. Journal of Infrastructure Intelligence and Resilience, 2023, 2: 100041.

[2] WU R T, JAHANSHAHI M R. Data fusion approaches for structural health monitoring and system identification: Past, present, and future[J]. Structural Health Monitoring, 2020, 19(2): 552-586.

[3] GINDY M, VACCARO R, NASSIF H, VELDE J. A state-space approach for deriving bridge displacement from acceleration[J]. Computer-Aided Civil and Infrastructure Engineering, 2008, 23: 281-290.

[4] SARWAR M Z, PARK J W. Bridge displacement estimation using a co-located acceleration and strain[J]. Sensors, 2020, 20: 1109.

[5] CHO S, PARK J W, PALANISAMY R P, et al. Reference-free displacement estimation of bridges using Kalman filter-based multimetric data fusion[J]. Journal of Sensors, 2016, 2016: 3791856.

[6] XIE Y, ZHANG S, MENG X, et al. An innovative sensor integrated with GNSS and accelerometer for bridge health monitoring[J]. Remote Sensing, 2024, 16: 607.

[7] PEREZ F J, MORA O E. A vision-based system for structural displacement measurement[C]//Proceedings of the 7th World Congress on Civil, Structural, and Environmental Engineering. Lisbon/Virtual: [s.n.], 2022: ICSECT 127.

[8] CHOI I, KIM J, KIM D. A target-less vision-based displacement sensor based on image convex hull optimization for measuring the dynamic response of building structures[J]. Sensors, 2016, 16: 2085.

[9] LEE J, LEE K C, CHO S, et al. Computer vision-based structural displacement measurement robust to light-induced image degradation for in-service bridges[J]. Sensors, 2017, 17: 2317.

[10] LEE J, CHO S, SIM S H. Computer vision-based displacement measurement method with arbitrarily positioned camera[C]//Asia Pacific Conference of the Prognostics and Health Management Society. 2017.

[11] CHA G, SIM S H, PARK S, et al. LiDAR-based bridge displacement estimation using 3D spatial optimization[J]. Sensors, 2020, 20: 7117.

[12] KAARTINEN E, DUNPHY K, SADHU A. LiDAR-based structural health monitoring: applications in civil infrastructure systems[J]. Sensors, 2022, 22: 4610.

[13] DAI K, BOYAJIAN D, LIU W, et al. Laser-based field measurement for a bridge finite-element model validation[J]. Journal of Performance of Constructed Facilities, 2014, 28(5): 04014024.

[14] ZHOU D, WANG N, FU C, et al. A novel elastomer-based inclinometer for ultrasensitive bridge rotation measurement[J]. Sensors, 2022, 22: 2715.

[15] PARK J W, SIM S H, JUNG H J. Wireless displacement sensing system for bridges using multi-sensor fusion[J]. Smart Materials and Structures, 2014, 23: 045022.

[16] LI C, CHEN W, LIU G, YAN R, XU H, QI Y. A noncontact FMCW radar sensor for displacement measurement in structural health monitoring[J]. Sensors, 2015, 15(4): 7412-7433.

[17] PRAMUDITA A A, LIN D B, DHIYANI A A, et al. FMCW radar for noncontact bridge structure displacement estimation[J]. IEEE Transactions on Instrumentation and Measurement, 2023, 72: 8504914.

[18] ZOU L, FENG W, MASCI O, et al. Bridge monitoring strategies for sustainable development with microwave radar interferometry[J]. Sustainability, 2024, 16: 2607.

[19] HUANG Q, WANG Y, LUZI G, et al. Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge[J]. Remote Sensing, 2020, 12: 2594.

[20] ZHANG G, et al. Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge[J]. ISPRS Journal of Photogrammetry and Remote Sensing, 2020, 167: 71-84.

[21] XIAO M, HAN Z, YU J, et al. Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring[J]. Scientific Reports, 2026, 16: 2030.

[22] JIA R, LONG J, DONG F, et al. Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements[J]. Scientific Reports, 2025, 15: 6679.

[23] Structural displacement measurements using DC coupled radar with active transponder[J]. Structural Control and Health Monitoring, 2017, 24: e1909.

[24] PAGNINI L, MICCINESI L, BENI A, et al. Transversal displacement detection of an arched bridge with a multimonostatic multiple-input multiple-output radar[J]. Sensors, 2024, 24: 1839.

[25] GUO J, HE Y, JIANG C, JIN M, LI S, ZHANG J, XI R, LIU Y. Measuring micrometer-level vibrations with mmWave radar[J]. IEEE Transactions on Mobile Computing, 2023, 22(4): 2248-2261.

[26] TAKAMATSU H, HINOHARA N, SUZUKI K, SAKAI F. Experimental analysis of accuracy and precision in displacement measurement using millimeter-wave FMCW radar[J]. Applied Sciences, 2025, 15(6): 3316.

[27] CHEN Z, XU W, DONG S, et al. Radar sensing of displacement motions with high robustness against additive noise[J]. IEEE Transactions on Microwave Theory and Techniques, 2023, 71(8): 3678-3690.

[28] XIONG Y, LIU Z, LI S, et al. Scanning microwave vibrometer: full-field vibration measurement via microwave sensing with phase-encoded beam scanning[J]. IEEE Transactions on Instrumentation and Measurement, 2023, 72: 3507611.

[29] PIOTROWSKY L, KUEPPERS S, JAESCHKE T, et al. Distance measurement using mmWave radar: micron accuracy at medium range[J]. IEEE Transactions on Microwave Theory and Techniques, 2022, 70(11): 5259-5270.

[30] PIOTROWSKY L, JAESCHKE T, KUEPPERS S, et al. Enabling high accuracy distance measurements with FMCW radar sensors[J]. IEEE Transactions on Microwave Theory and Techniques, 2019, 67(12): 5360-5371.

[31] PIOTROWSKY L, JAESCHKE T, KUEPPERS S, et al. An unambiguous phase-based algorithm for single-digit micron accuracy distance measurements using FMCW radar[C]//2019 IEEE MTT-S International Microwave Symposium. Piscataway: IEEE, 2019: 552-555.

[32] 高昂. 基于毫米波雷达的两近距离目标微动位移提取方法[D]. 武汉: 华中科技大学, 2024.

[33] MA Z, CHOI J, YANG L, SOHN H. Structural displacement estimation using accelerometer and FMCW millimeter wave radar[J]. Mechanical Systems and Signal Processing, 2023, 182: 109582.

[34] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.

[35] MA Z, CHOI J, LEE J, SOHN H. Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion[J]. Mechanical Systems and Signal Processing, 2025, 223: 111888.

[36] MA Z, HAN K, CHOI J, LEE J, KWON O, SOHN H, LIU J, HWANG D, AGGARWAL J, NOH H, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.

[37] LEE J, et al. Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW millimeter-wave radar[J]. Measurement, 2026, 270: 120848.

[38] SOHN H, LEE J, IL S, et al. Structural displacement estimation of rail bridges through millimeter-wave radar, accelerometers, and non-dedicated multi-modal sensing[Z]. [S.l.]: [s.n.], 2025?.

[39] MA Z, et al. Computer vision-based cross-scale structural displacement estimation using amplitude-phase fusion[J]. Mechanical Systems and Signal Processing, 2026, 244: 113738.

[40] ZHU Z, LU J, ZHU S. Multi-rate Kalman filtering for structural dynamic response reconstruction by fusing multi-type sensor data with different sampling frequencies[J]. Engineering Structures, 2023, 293: 116573.

[41] XIONG Y, LI S, GU C, et al. Millimeter-wave bat for mapping and quantifying micromotions in full field of view[J]. Research, 2021, 2021: 9787484.

[42] LI S, XIONG Y, SHEN X, et al. Multi-scale and full-field vibration measurement via millimetre-wave sensing[J]. Mechanical Systems and Signal Processing, 2022, 177: 109178.

[43] XIONG Y, GOU Y, TIAN W, et al. Full-field 3D displacement measurement via microwave sensing[J]. Mechanical Systems and Signal Processing, 2025, 234: 112804.

[44] RAO S. MIMO Radar[R]. Dallas: Texas Instruments, 2018.

[45] AHMAD A, ROH J C, WANG D, et al. Vital signs monitoring of multiple people using a FMCW millimeter-wave sensor[C]//2018 IEEE Radar Conference. Piscataway: IEEE, 2018: 1450-1455.

[46] XU Z, SHI C, ZHANG T, et al. Simultaneous monitoring of multiple people's vital sign leveraging a single phased-MIMO radar[J]. IEEE Journal of Electromagnetics, RF and Microwaves in Medicine and Biology, 2022, 6(3): 311-320.

[47] YANG Y, QU L, YANG Y, et al. Multitarget vital signs detection based on MIMO-FMCW radar[C]//2024 Photonics & Electromagnetics Research Symposium. Piscataway: IEEE, 2024: 1-10.

[48] SINGH H, CHATTOPADHYAY A. Multi-target range and angle detection for MIMO-FMCW radar with limited antennas[Z]. [S.l.]: [s.n.], 2023?.

[49] RAI C, SINGH H, CHATTOPADHYAY A. Multi-target range, Doppler and angle estimation in MIMO-FMCW radar with limited measurements[EB/OL]. arXiv:2502.01147, 2025.

[50] HUANG L, WANG X, HUANG M, et al. An implementation scheme of range and angular measurements for FMCW MIMO radar via sparse spectrum fitting[J]. Electronics, 2020, 9: 389.

[51] ZHANG J, LI Y, ZHANG Z, et al. Frequency-spatial adaptive digital beamforming technique for range-angle decoupling with high-resolution MIMO radar[J]. IEEE Microwave and Wireless Technology Letters, 2025, 35(6): 888-891.

[52] RAI C, ROY D, SEN D. A decoupling-based approach for signature estimation of wideband XL MIMO-FMCW radars[EB/OL]. arXiv:2603.14542, 2026.

[53] BEKAR M, BEKAR A, PIRKANI A, et al. Burg-aided 2D MIMO array extrapolation for improved spatial resolution[J]. Sensors, 2025, 25: 6310.

[54] ZOU Y, DING H, LI J, et al. Enhanced two-stage sparse Bayesian learning algorithm for multivehicle precise detection and localization with MIMO-FMCW radar[J]. IEEE Sensors Journal, 2026, 26(7): 11107-11119.

[55] KIM B S, JIN Y, LEE J, et al. Super-resolution angle estimation algorithm using low complexity MUSIC-based RELAX for MIMO FMCW radar[J]. Journal of Electromagnetic Engineering and Science, 2025, 25(1): 41-53.

[56] KIM S, KIM B S, JIN Y, et al. Extrapolation-RELAX estimator based on spectrum partitioning for DOA estimation of FMCW radar[J]. IEEE Access, 2019, 7: 98771-98780.

[57] PARK H, CHUNG S, PARK J, et al. High-resolution localization using distributed MIMO FMCW radars[J]. Sensors, 2025, 25: 3579.

[58] KIM E. MIMO FMCW radar with Doppler-insensitive polyphase codes[J]. Remote Sensing, 2022, 14: 2595.

[59] KIM H J, YOU S J, JEONG B J, HWANG J H, PARK K H. Non-uniform virtual array position optimization for MIMO radar and neural network-based radar imaging enhancement[J]. ETRI Journal, 2026, 48: 367-380.

[60] LI Y J, HUNT S, PARK J, O'TOOLE M, KITANI K. Azimuth super-resolution for FMCW radar in autonomous driving[C]//IEEE/CVF Conference on Computer Vision and Pattern Recognition. 2023.

[61] ZHU Z, CHEN C, YANG B. Angle of arrival estimation with Transformer: a sparse and gridless method with zero-shot capability[EB/OL]. arXiv:2408.09362, 2024.

[62] FU M, LI Y, DENG Z, et al. High-resolution and accurate RV map estimation by sparse Bayesian learning[J]. IEEE Transactions on Vehicular Technology, 2022, 71(9): 9613-9624.

[63] ASHURY M, XIAO F, RODRIGUEZ-PINEIRO J, et al. Joint estimation of channel, range, and Doppler for FMCW radar with sparse Bayesian learning[C]//2024 IEEE 25th International Workshop on Signal Processing Advances in Wireless Communications. Piscataway: IEEE, 2024: 111-115.

[64] KIM D B, HONG S M. Multiple-target tracking and track management for an FMCW radar network[J]. EURASIP Journal on Advances in Signal Processing, 2013, 2013: 159.

[65] KALMAN R E. A new approach to linear filtering and prediction problems[J]. Transactions of the ASME-Journal of Basic Engineering, 1960, 82: 35-45.

[66] LIU J, LI Y, GU C. Solving phase ambiguity in interferometric displacement measurement with millimeter-wave FMCW radar sensors[J]. IEEE Sensors Journal, 2022, 22(9): 8482-8489.

[67] GUERZONI G, FAGHAND E, VINCENZI L, BASSOLI E, VITETTA G M. A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring[J]. Mechanical Systems and Signal Processing, 2025, 235: 112777.

[68] MA Z, HAI L, ZHANG T, WANG B, JING X, ZHANG Q, SOHN H. Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping[J]. Measurement, 2026, 262: 120029.

[69] MA Z, ZHANG T, ZHU Y, LIN S, LEE J, SOHN H, ZHANG Q. Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring[J]. Mechanical Systems and Signal Processing, 2026, 248: 113991.

[70] LI Z, ZHANG H, ZHOU Q, CHE H. An adaptive low-cost INS/GNSS tightly-coupled integration architecture based on redundant measurement noise covariance estimation[J]. Sensors, 2017, 17(9): 2032.

[71] MEHRA R K. Approaches to adaptive filtering[J]. IEEE Transactions on Automatic Control, 1972, 17(5): 693-698.

[72] MOHAMED A H, SCHWARZ K P. Adaptive Kalman filtering for INS/GPS[J]. Journal of Geodesy, 1999, 73: 193-203.
