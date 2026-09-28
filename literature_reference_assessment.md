# 参考文献相关性与方法说明

> 说明：本文档保留的是初次批量筛选时的历史判断，部分路径和统计反映当时的暂存状态。当前文献目录以 `ref_papers/00_primary_references`、`ref_papers/01_AoA`、`ref_papers/02_recent_uncollected` 和 `ref_papers/03_future_references` 的 README 为准；PINN/神经网络结构求解类文献已从未来参考目录清除。

本文档根据 `thesis_idea_overview.md` 的主线和 `ref_papers` 中 PDF 前三页/摘要抽取结果整理。判断标准不是“论文质量”，而是“是否能支撑倒挂式毫米波 FMCW 雷达结构位移测量、静止参考 target 选择、相位/IQ 处理、转换因子与多 target 融合”。
## 主攻领域确认
当前论文主攻领域是：倒挂安装的毫米波 FMCW 雷达随结构测点运动时，如何利用环境静止反射体作为参考 target 恢复结构位移，并在线选择可靠 target。核心链路是 `Range FFT/候选峰 -> 静止参考 target 可靠性评价 -> IQ几何与结构频带一致性 -> 相位解缠/转换因子估计 -> 多 target 位移融合`。
这意味着 PINN/结构力学神经求解、6G/ISAC/车载雷达通信、人体生命体征、目标分类等文献即使技术上有价值，也暂时不进入主参考集。
## 分类统计
- 核心必引：8 篇
- 核心/直接相关：19 篇
- 方法支撑-AoA/range-angle：20 篇
- 方法支撑/可选引用：56 篇
- 背景铺垫：4 篇
- 无关-当前不采用PINN/神经场路线：56 篇
- 无关-通信感知/车载雷达主线：27 篇
- 无关-应用场景偏离结构位移：19 篇
- 无关-主题过宽或偏离当前实验链路：7 篇
- 已移动到 `ref_papers/99_irrelevant_literature/`：109 篇

## 逐篇说明

## 核心必引
### 001. Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring
- 文件：`ref_papers/00_primary_references/Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf`
- 是否可作参考：核心必引
- 创新：将加速度先验、相位解缠和相位降噪统一到 Kalman 状态空间中，强调强噪声下不能先解缠再滤波。
- 方法论/数据处理流：雷达相位观测 + 加速度输入 -> 状态预测 -> 2π相位校正 -> Kalman更新 -> 连续降噪相位 -> 位移。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Communicated by S. Laflamme Structural displacement monitoring is essential for ensuring the safety and longevity of civil infrastructures. Millimeter-wave radar offers high-precis...”。

### 002. Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping
- 文件：`ref_papers/00_primary_references/Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf`
- 是否可作参考：核心必引
- 创新：利用多 chirp 估计相位变化率并自适应预测下一帧相位区间，降低大位移相位缠绕对雷达-only测量的限制。
- 方法论/数据处理流：多 chirp 相位 -> 相位变化率估计/解缠 -> 下一帧相位预测 -> 主 chirp 相位恢复 -> 位移序列。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Measurement 262 (2026) 120029 Contents lists available at ScienceDirect Measurement journal homepage: www.elsevier.com/locate/measurement Accurate structural displacement measureme...”。

### 003. Computer vision-based cross-scale structural displacement  estimation using amplitude-phase fusion
- 文件：`ref_papers/00_primary_references/Computer vision-based cross-scale structural displacement  estimation using amplitude-phase fusion.pdf`
- 是否可作参考：核心必引
- 创新：把幅值粗配准和相位亚像素细化结合起来，解决视觉相位法在大伪静态位移与小振动共存时容易相位缠绕的问题。
- 方法论/数据处理流：视频帧 -> 复值 steerable pyramid 分解 -> 幅值互相关粗配准 -> 活动像素选择和相位残差细化 -> 相位-像素尺度自校准 -> 结构位移。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Communicated by Z. Mao Accurate and robust structural displacement monitoring is essential for the safety assessment and maintenance of civil infrastructure. While phase-based visi...”。

### 004. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer
- 文件：`ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`
- 是否可作参考：核心必引
- 创新：面向长期桥梁监测中的目标遮挡，提出雷达、应变、加速度三源切换与融合框架。
- 方法论/数据处理流：雷达/应变/加速度同步采集 -> 目标遮挡检测 -> 可用雷达目标融合；全遮挡时切换应变+加速度 -> 连续位移。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Mechanical Systems and Signal Processing 197 (2023) 110408 Contents lists available at ScienceDirect Mechanical Systems and Signal Processing journal homepage: www.elsevier.com/loc...”。

### 005. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer
- 文件：`ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
- 是否可作参考：核心必引
- 创新：把毫米波雷达+MEMS加速度计封装为低成本现场系统，并自动完成目标选择和转换因子标定。
- 方法论/数据处理流：雷达 cube + MEMS 加速度 -> 自动校准时段识别 -> 目标/转换因子选择 -> 加速度辅助解缠 -> FIR互补融合 -> 位移输出。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Engineering Structures 321 (2024) 118926 Contents lists available at ScienceDirect Engineering Structures journal homepage: www.elsevier.com/locate/engstruct Development and field...”。

### 006. Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar
- 文件：`ref_papers/00_primary_references/Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf`
- 是否可作参考：核心必引
- 创新：反向利用雷达位移来提升低成本 MEMS 加速度估计，重点补偿 MEMS 低频漂移和雷达二次微分高频噪声。
- 方法论/数据处理流：雷达相位位移 + MEMS 加速度 -> 自动目标/转换因子标定 -> 加速度辅助解缠 -> 滑动窗口 FIR 互补滤波 -> 改进加速度。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Measurement 270 (2026) 120848 Contents lists available at ScienceDirect Measurement journal homepage: www.elsevier.com/locate/measurement Improved structural acceleration estimatio...”。

### 007. Measuring Micrometer-Level Vibrations With mmWave Radar
- 文件：`ref_papers/00_primary_references/Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf`
- 是否可作参考：核心必引
- 创新：提出 mmVib 和 VSNR，把商用 77 GHz FMCW 雷达的微米级振动误差、IQ 圆弧拟合、多 chirp 合并和多目标分离统一到一个可复现实验框架。
- 方法论/数据处理流：FMCW ADC/IF -> Range-Angle 定位 -> 多信号合并提高 VSNR -> IQ 圆拟合/背景消除 -> 相位恢复 -> 振动幅值和频率估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Vibration measurement is a crucial task in industrial systems, where vibration characteristics reflect health conditions and indicate anomalies of the devices. Previous approaches...”。

### 008. Structural displacement sensing techniques for civil infrastructure  A review
- 文件：`ref_papers/00_primary_references/Structural displacement sensing techniques for civil infrastructure_ A review.pdf`
- 是否可作参考：核心必引
- 创新：系统综述结构位移传感器谱系和多模态融合，是引言中论证雷达/融合必要性的总背景。
- 方法论/数据处理流：按接触/非接触传感器分类 -> 比较 LVDT、加速度、GNSS、视觉、雷达、LiDAR 等技术 -> 归纳多传感器融合框架 -> 总结长期监测约束。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Journal of Infrastructure Intelligence and Resilience 2 (2023) 100041 Contents lists available at ScienceDirect Journal of Infrastructure Intelligence and Resilience journal homepa...”。


## 核心/直接相关
### 001. A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring
- 文件：`ref_papers/00_primary_references/A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf`
- 是否可作参考：核心/直接相关
- 创新：围绕 FMCW/毫米波雷达的非接触结构位移或振动测量，提供相位测距、干涉测量、精度验证或桥梁场景实证。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“This paper investigates the Frequency Modulation Continuous Wave (FMCW) radar sensor for multi-target displacement measurement in Structural Health Monitoring (SHM). The principle...”。

### 002. A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring
- 文件：`ref_papers/00_primary_references/A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf`
- 是否可作参考：核心/直接相关
- 创新：利用 Doppler 信息辅助毫米波 MIMO 雷达相位解缠，面向结构位移中相邻帧相位跨越半波长限制的场景。
- 方法论/数据处理流：MIMO-FMCW 回波 -> 目标 range/angle 单元提取 -> Doppler/速度约束估计相位增量 -> 相位解缠 -> 结构位移恢复。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Communicated by Z. Mao In this manuscript, the problem of estimating dynamic structural displacements through mmWave multiple-input multiple-output frequency modulated continuous w...”。

### 003. Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion
- 文件：`ref_papers/00_primary_references/Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。

### 004. Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry
- 文件：`ref_papers/00_primary_references/Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“The potential of a coherent microwave radar for infrastructure health monitoring has been investigated over the past decade. Microwave radar measuring based on interferometry proce...”。

### 005. Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring
- 文件：`ref_papers/00_primary_references/Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“www.nature.com/scientificreports OPEN Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring Min Xiao1, Zhixing Han2, Jun...”。

### 006. Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar
- 文件：`ref_papers/00_primary_references/Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf`
- 是否可作参考：核心/直接相关
- 创新：围绕 FMCW/毫米波雷达的非接触结构位移或振动测量，提供相位测距、干涉测量、精度验证或桥梁场景实证。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Millimeter-wave radar is emerging as a key sensor technology not only for au- tonomous driving but also for various industrial applications, such as vital sign monitoring and struc...”。

### 007. FMCW Radar for Noncontact Bridge Structure Displacement Estimation
- 文件：`ref_papers/00_primary_references/FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf`
- 是否可作参考：核心/直接相关
- 创新：围绕 FMCW/毫米波雷达的非接触结构位移或振动测量，提供相位测距、干涉测量、精度验证或桥梁场景实证。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“The displacement on the bridge structure is an condition of bridge structures over the road and railway must essential parameter in identifying the bridge structure’s health. be ma...”。

### 008. Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge
- 文件：`ref_papers/00_primary_references/Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“With the continuous expansion of the high-speed railway network in China, long-span railway bridges carrying multiple tracks demand reliable and fast testing procedures and techniq...”。

### 009. Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge
- 文件：`ref_papers/00_primary_references/Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。

### 010. Radar Sensing of Displacement Motions With High Robustness Against Additive Noise
- 文件：`ref_papers/00_primary_references/Radar_Sensing_of_Displacement_Motions_With_High_Robustness_Against_Additive_Noise.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Doppler radar uses phase demodulation to extract the target displacement motion contained in the phase of the echo signal. The demodulation performance is vulnerable to the additiv...”。

### 011. Scanning Microwave Vibrometer Full-Field Vibration Measurement via Microwave Sensing With Phase-Encoded Beam Scanning
- 文件：`ref_papers/00_primary_references/Scanning_Microwave_Vibrometer_Full-Field_Vibration_Measurement_via_Microwave_Sensing_With_Phase-Encoded_Beam_Scanning.pdf`
- 是否可作参考：核心/直接相关
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Full-field and remote vibration measurements are vibration measurement is commonly required for modal anal- highly desirable for various fields from the natural world to engi- ysis...”。

### 012. Solving Phase Ambiguity in Interferometric Displacement Measurement With Millimeter-Wave FMCW Radar Sensors
- 文件：`ref_papers/00_primary_references/Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf`
- 是否可作参考：核心/直接相关
- 创新：围绕 FMCW/毫米波雷达的非接触结构位移或振动测量，提供相位测距、干涉测量、精度验证或桥梁场景实证。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“The frequency-modulated continuous-wave (FMCW) radar sensor is subject to phase ambiguity in mea- suring large displacement of over half a wavelength, which is particularly severe...”。

### 013. Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing
- 文件：`ref_papers/00_primary_references/Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Rail bridges are essential components of modern transportation networks but often operate beyond their intended service life, leading to growing concerns about structural integrity...”。

### 014. Structural displacement estimation using accelerometer and FMCW millimeter wave radar
- 文件：`ref_papers/00_primary_references/Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf`
- 是否可作参考：核心/直接相关
- 创新：围绕 FMCW/毫米波雷达的非接触结构位移或振动测量，提供相位测距、干涉测量、精度验证或桥梁场景实证。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。

### 015. Structural displacement measurements using DC coupled radar with active transponder
- 文件：`ref_papers/00_primary_references/Structural displacement measurements using DC coupled radar with active transponder.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Structural Displacement Measurements using DC Coupled Radar with Active Transponder Shanyue Guan∗1, Jennifer A. Rice1, Changzhi Li2, Yiran Li2, and Guochao Wang2 1 Engineering Scho...”。

### 016. Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar
- 文件：`ref_papers/00_primary_references/Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Interferometric radars are widely used for monitoring civil structures. Bridges are critical structures that need to be constantly monitored for the safety of the users. In this wo...”。

### 017. Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements
- 文件：`ref_papers/00_primary_references/Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements.pdf`
- 是否可作参考：核心/直接相关
- 创新：把雷达用于结构或桥梁位移/振动监测，补充不同硬件、测点、桥型或多目标测量条件下的证据。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“www.nature.com/scientificreports OPEN Vibration response analysis of simply supported girder bridges using millimeter-wave radar measurements Ruixin Jia1, Jinxi Long1, Fang Dong1,2...”。

### 018. mmVib MobiCom2020
- 文件：`ref_papers/00_primary_references/mmVib_MobiCom2020.pdf`
- 是否可作参考：核心/直接相关
- 创新：把商用 mmWave FMCW 雷达用于微米级振动测量，提出 VSNR 与多 chirp/多天线合并思想，是本文相位-IQ圆弧模型的关键源头。
- 方法论/数据处理流：原始 ADC/IF -> Range/Angle 定位 -> IQ圆弧拟合与背景消除 -> 相位展开 -> 位移/频率/幅值估计。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“Vibration measurement is a crucial task in industrial systems, where vibration characteristics reflect the health and indicate anomalies of the objects. Previous approaches either...”。

### 019. 基于毫米波雷达的两近距离目标微动位移提取方法 高昂
- 文件：`ref_papers/00_primary_references/基于毫米波雷达的两近距离目标微动位移提取方法_高昂.pdf`
- 是否可作参考：核心/直接相关
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议纳入正文核心参考，优先用于问题定义、理论模型、实验对照或现有方法边界。
- 摘要判断依据：摘要/首页显示主题约为“分类号 学号 M202170482 学校代码 1 0 4 8 7 密级 硕士学位论文 （学术型 专业型□） 基于毫米波雷达的两近距离目标微动 位移提取方法 学位申请人：高昂 学 科 专 业：机械工程 指 导 教 师：轩建平 教授 答 辩 日 期：2024 年 05 月 17 日 A Dissertation Submitted in Partial Ful...”。


## 方法支撑-AoA/range-angle
### 001. A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars
- 文件：`ref_papers/01_AoA/A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Modern radars employing wideband signals and To improve range and angle resolution in MIMO frequency extremely large (XL) multiple-input multiple-output (MIMO) modulated continuous...”。

### 002. A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring
- 文件：`ref_papers/01_AoA/A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Noncontact vital sign monitoring based on radar has attracted great interest in many fields. Heart Rate Variability (HRV), which measures the fluctuation of heartbeat intervals, ha...”。

### 003. An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting
- 文件：`ref_papers/01_AoA/An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The work presented in this paper is about implementing a frequency-modulated continuous wave (FMCW) multiple-input multiple-output (MIMO) positioning radar and a sparse spectrum fi...”。

### 004. Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability
- 文件：`ref_papers/01_AoA/Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“processing and data representation techniques to fully lever- age the potential of MIMO radar systems in autonomous Automotive Multiple-Input Multiple-Output (MIMO) radars have gai...”。

### 005. Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution
- 文件：`ref_papers/01_AoA/Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, the extrapolation of a 2D multiple-input multiple-output (MIMO) array is proposed using the Burg algorithm to achieve higher angular resolution beyond that of the co...”。

### 006. Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar
- 文件：`ref_papers/01_AoA/Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Accurate identification and positioning of mul- tiple vehicles is a critical challenge in autonomous driving, particularly over long distances. While sparse Bayesian learning (SBL)...”。

### 007. Frequency-Spatial Adaptive Digital Beamforming Technique for Range-Angle Decoupling With High-Resolution MIMO Radar
- 文件：`ref_papers/01_AoA/Frequency-Spatial_Adaptive_Digital_Beamforming_Technique_for_Range-Angle_Decoupling_With_High-Resolution_MIMO_Radar.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“High-resolution multiple-input multiple-output (MIMO) radar has been extensively employed for imaging across a wide range of applications. However, when radar systems are designed...”。

### 008. High-Resolution Localization Using Distributed MIMO FMCW Radars
- 文件：`ref_papers/01_AoA/High-Resolution Localization Using Distributed MIMO FMCW Radars.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Due to its fast processing time and robustness against harsh environmental con- ditions, the frequency modulated continuous waveform (FMCW) multiple-input multiple- output (MIMO) r...”。

### 009. High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning
- 文件：`ref_papers/01_AoA/High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Range-velocity (RV) map (also called the range- signal whose frequency is proportional to the target range [7]. Doppler map) is used in radar to detect targets and estimate the A f...”。

### 010. Joint Estimation of Channel Range and Doppler for FMCW Radar with Sparse Bayesian Learning
- 文件：`ref_papers/01_AoA/Joint_Estimation_of_Channel_Range_and_Doppler_for_FMCW_Radar_with_Sparse_Bayesian_Learning.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The adoption of Advanced Driver Assistance Sys- tems (ADAS) and autonomous driving systems poses great tions require the resolution of the sensing environment to be challenges for...”。

### 011. Li Azimuth Super-Resolution for FMCW Radar in Autonomous Driving CVPR 2023 paper
- 文件：`ref_papers/01_AoA/Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Ours Input ADC signals Predicted uncaptured ADC signals We tackle the task of Azimuth (angular dimension) super- ADC resolution for Frequency Modulated Continuous Wave Super Resolu...”。

### 012. MIMO FMCW Radar with Doppler-Insensitive Polyphase
- 文件：`ref_papers/01_AoA/MIMO FMCW Radar with Doppler-Insensitive Polyphase.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Co-located MIMO is used to enlarge the antenna aperture virtually and increase the angular resolution. This paper shows FMCW radar using MIMO VAA. Polyphase codes are designed for...”。

### 013. Millimeter Wave Real-Time Tracking and Imaging of Moving Objects Based on Virtual MIMO Array and State Vector Prediction
- 文件：`ref_papers/01_AoA/Millimeter_Wave_Real-Time_Tracking_and_Imaging_of_Moving_Objects_Based_on_Virtual_MIMO_Array_and_State_Vector_Prediction.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Millimeter wave imaging systems are being rapidly applied to indoor security, industrial nondestructive evaluation and automotive radar systems. Millimeter wave real-time imaging i...”。

### 014. Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas
- 文件：`ref_papers/01_AoA/Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Multiple-input multiple-output (MIMO) radar has achieves a better angular resolution than conventional radar several advantages with respect to the traditional radar array sys- by...”。

### 015. Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements
- 文件：`ref_papers/01_AoA/Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Multiple-input multiple-output (MIMO) radar of- FMCW radars transmit a finite number of linear frequency- fers several performance and flexibility advantages over tradi- modulated...”。

### 016. Multitarget Vital Signs Detection Based on MIMO-FMCW Radar
- 文件：`ref_papers/01_AoA/Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In order to tackle the challenge of accurately detecting vital signs of multiple people with multiple-input-multiple-output (MIMO) frequency modulated continuous wave (FMCW) 2024 P...”。

### 017. Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement
- 文件：`ref_papers/01_AoA/Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Laboratory, Electronics and This paper presents a method for enhancing the angular resolution of multiple Telecommunications Research Institute, input multiple output (MIMO) radar...”。

### 018. Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar
- 文件：`ref_papers/01_AoA/Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“A novel super-resolution angle estimation algorithm using low complexity-multiple signal classiﬁcation (LC-MUSIC)-based relaxation (RELAX) for multiple-input multiple-output (MIMO)...”。

### 019. TI MMWAVE-SDK : AoAProc : MIMO Radar app report
- 文件：`ref_papers/01_AoA/TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“MIMO radar is a key technology in improving the angle resolution (spatial resolution) of mmwave-radars. This article introduces the basic principles of the MIMO-radar and the diffe...”。

### 020. Variational Signal Separation for Automotive Radar Interference Mitigation
- 文件：`ref_papers/01_AoA/Variational Signal Separation for Automotive Radar Interference Mitigation .pdf`
- 是否可作参考：方法支撑-AoA/range-angle
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Algorithms for mutual interference mitigation and models the specific form of interference in the received radar object parameter estimation are a key enabler for automotive signal...”。


## 方法支撑/可选引用
### 001. A Doppler aliasing free micro-motion parameter estimation method in the terahertz band
- 文件：`ref_papers/A Doppler aliasing free micro-motion parameter estimation method in the terahertz band.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Micro-Doppler, induced by micro-motion of targets, is an important characteristic for target recognition once extracted via parameter estimation. However, micro-Doppler is usually...”。

### 002. A Novel Elastomer-Based Inclinometer for Ultrasensitive Bridge Rotation Measurement
- 文件：`ref_papers/A Novel Elastomer-Based Inclinometer for Ultrasensitive Bridge Rotation Measurement.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Bridge deformation consists of cross-section rotation and deflection, which are crucial parameters for bridge capacity evaluation and damage detection. The maximum value of deflect...”。

### 003. A Software-Synchronization Based, Flexible, Low-Cost FMCW Radar
- 文件：`ref_papers/A Software-Synchronization Based, Flexible, Low-Cost FMCW Radar.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“With the development of the Internet of Things, FMCW (Frequency Modulated Continuous Wave) radars are widely used in medical treatment, human behavior detection, Internet of Vehicl...”。

### 004. A Study on Millimeter Wave SAR Imaging for Non-Destructive Testing of Rebar in Reinforced Concrete
- 文件：`ref_papers/A Study on Millimeter Wave SAR Imaging for Non-Destructive Testing of Rebar in Reinforced Concrete.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In this study, we investigate a millimeter wave (mmWave) synthetic aperture radar (SAR) imaging scheme utilizing a low-cost frequency modulated continuous wave (FMCW) radar to take...”。

### 005. A Target-Less Vision-Based Displacement Sensor Based on Image Convex Hull Optimization for Measuring the Dynamic Response of Building Structures
- 文件：`ref_papers/A Target-Less Vision-Based Displacement Sensor Based on Image Convex Hull Optimization for Measuring the Dynamic Response of Building Structures.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Existing vision-based displacement sensors (VDSs) extract displacement data through changes in the movement of a target that is identified within the image using natural or artific...”。

### 006. A Vision-Based System for Structural Displacement Measurement
- 文件：`ref_papers/A Vision-Based System for Structural Displacement Measurement.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“– Current structural displacement measurement methods for structural health monitoring (SHM) are based on displacement data of acceleration, strain, laser doppler vibrometer, Light...”。

### 007. A state-space approach for deriving bridge displacement from acceleration
- 文件：`ref_papers/A state-space approach for deriving bridge displacement from acceleration.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The dynamic response (i.e., acceleration and...”。

### 008. A 130-nm Fusion-Based Deconvolution Kernel Generator IC for Real-Time mmWave Radar Motion Compensation
- 文件：`ref_papers/A_130-nm_Fusion-Based_Deconvolution_Kernel_Generator_IC_for_Real-Time_mmWave_Radar_Motion_Compensation.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“High-resolution mmWave radar represents an attractive sensing modality for precise, real-time sensing on resource-limited edge devices. Inherent parasitic platform motion such as v...”。

### 009. A new method for the nonlinear transformation of means and covariances in filters and estimators
- 文件：`ref_papers/A_new_method_for_the_nonlinear_transformation_of_means_and_covariances_in_filters_and_estimators.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“This paper describes a new approach for generalizing the mean and Kalman filter to nonlinear systems. A set of samples are used to param- T eterize the mean and covariance of a (no...”。

### 010. An Innovative Sensor Integrated with GNSS and Accelerometer for Bridge Health Monitoring
- 文件：`ref_papers/An Innovative Sensor Integrated with GNSS and Accelerometer for Bridge Health Monitoring.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“This paper presents an innovative integrated sensor that combines GNSS and a low-cost ac- celerometer for bridge health monitoring. GNSS and accelerometers are both significant and...”。

### 011. An Unambiguous Phase-Based Algorithm for Single-Digit Micron Accuracy Distance Measurements using FMCW Radar
- 文件：`ref_papers/An_Unambiguous_Phase-Based_Algorithm_for_Single-Digit_Micron_Accuracy_Distance_Measurements_using_FMCW_Radar.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In this paper an algorithm for accurate distance estimation using a frequency modulated continuous wave Radar Target Laser Interferometer-Reﬂector Radar (FMCW) radar is presented....”。

### 012. Anchor-Based, Real-Time Motion Compensation for High-Resolution mmWave Radar
- 文件：`ref_papers/Anchor-Based, Real-Time Motion Compensation for High-Resolution mmWave Radar.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In the modern domain of edge sensing and physically compact smart devices, mmWave radar has emerged as a prominent modality, simultaneously offering high-resolution perception capa...”。

### 013. Computer Vision-Based Structural Displacement Measurement Robust to Light-Induced Image Degradation for In-Service Bridges
- 文件：`ref_papers/Computer Vision-Based Structural Displacement Measurement Robust to Light-Induced Image Degradation for In-Service Bridges.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The displacement responses of a civil engineering structure can provide important information regarding structural behaviors that help in assessing safety and serviceability. A dis...”。

### 014. Computer Vision-based Displacement Measurement Method With Arbitrarily Positioned Camera
- 文件：`ref_papers/Computer Vision-based Displacement Measurement Method With Arbitrarily Positioned Camera.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“firstly processed to detect features to be tracked. The detected features location in the image plane are then Displacement is broadly used in structural health monitoring transfor...”。

### 015. Computer aided Civil Eng - 2025 - Jeon - Dual‐reference approach for vision‐based structural displacement measurement using
- 文件：`ref_papers/Computer aided Civil Eng - 2025 - Jeon - Dual‐reference approach for vision‐based structural displacement measurement using.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Cheongju, South Korea Accurate displacement measurement is essential for structural health moni- 2 Department of Civil, Construction, and toring (SHM) to ensure infrastructure safe...”。

### 016. Computer vision-based bridge displacement measurements using rotation-invariant image processing technique
- 文件：`ref_papers/Computer vision-based bridge displacement measurements using rotation-invariant image processing technique.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Bridges are exposed to various kinds of external loads, including vehicle and hurricanes, during their life cycle. These loads cause structural damage, which may lead to bridge col...”。

### 017. Continuous structural health monitoring with a modified dual Kalman filter applied with optical fiber sensing data
- 文件：`ref_papers/Continuous structural health monitoring with a modified dual Kalman filter applied with optical fiber sensing data.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Computers and Structures 329 (2026) 108284 Contents lists available at ScienceDirect Computers and Structures journal homepage: www.elsevier.com/locate/cas Continuous structural he...”。

### 018. Data fusion approaches for structural health monitoring and system identification Past, present, and future
- 文件：`ref_papers/Data fusion approaches for structural health monitoring and system identification Past, present, and future.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“During the past decades, significant efforts have been dedicated to develop reliable methods in structural health monitor- ing. The health assessment for the target structure of in...”。

### 019. Developing Bridge Monitor Platform Using GPS and Communication Technology
- 文件：`ref_papers/Developing Bridge Monitor Platform Using GPS and Communication Technology.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In order to maintain security of the bridge and prevent life and property losses caused by earthquakes, typhoons, erosion and other disasters, it is worthwhile to explore the insta...”。

### 020. Development and Validation of a Framework for Smart Wireless Strain and Acceleration Sensing
- 文件：`ref_papers/Development and Validation of a Framework for Smart Wireless Strain and Acceleration Sensing.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Civil infrastructure worldwide is subject to factors such as aging and deterioration. Struc- tural health monitoring (SHM) can be used to assess the impact of these processes on st...”。

### 021. Distance Measurement Using mmWave Radar Micron Accuracy at Medium Range
- 文件：`ref_papers/Distance_Measurement_Using_mmWave_Radar_Micron_Accuracy_at_Medium_Range.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“This work provides a proof-of-concept for a a systematic source of errors. As shown here, these errors can linear-position sensor using an ultrawideband (UWB) frequency- exceed the...”。

### 022. Enabling High Accuracy Distance Measurements With FMCW Radar Sensors
- 文件：`ref_papers/Enabling_High_Accuracy_Distance_Measurements_With_FMCW_Radar_Sensors.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“With the integrated radar technology being increasingly common in the automotive segment, it becomes even more cost-effective in other applications as well. Taking into account its...”。

### 023. Fast and Accurate Angle Estimation for MIMO Radar With a Virtual Nonrectangular Array
- 文件：`ref_papers/Fast_and_Accurate_Angle_Estimation_for_MIMO_Radar_With_a_Virtual_Nonrectangular_Array.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“I. INTRODUCTION Modern radar sensing has become an indispensable Fast and Accurate Angle technology for a wide range of applications requiring robust perception, such as autonomous...”。

### 024. Image Analysis Applications for Building Inter-Story Drift Monitoring
- 文件：`ref_papers/Image Analysis Applications for Building Inter-Story Drift Monitoring.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Structural health monitoring techniques have been applied to several important structures and infrastructure facilities, such as buildings, bridges, and power plants. For buildings...”。

### 025. Incoherent Interference Detection and Mitigation for Millimeter-Wave FMCW Radars
- 文件：`ref_papers/Incoherent Interference Detection and Mitigation for Millimeter-Wave FMCW Radars.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Current automotive radar technology is almost exclusively implemented using frequency modulated continuous wave (FMCW) radar in the millimeter wave bands. Unfortunately, incoherent...”。

### 026. Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric
- 文件：`ref_papers/Journal of Sensors - 2016 - Cho - Reference‐Free Displacement Estimation of Bridges Using Kalman Filter‐Based Multimetric.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Hindawi Publishing Corporation Journal of Sensors Volume 2016, Article ID 3791856, 9 pages http://dx.doi.org/10.1155/2016/3791856 Research Article Reference-Free Displacement Estim...”。

### 027. Kalman1960
- 文件：`ref_papers/Kalman1960.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“abstractly, any expression of the form (6) as “point” Proof: By Theorem 5, (A) (see Appendix), conditional distribu- or “vector” in Y(t); this use of the word “vector” should not b...”。

### 028. LiDAR-Based Bridge Displacement Estimation Using 3D Spatial Optimization
- 文件：`ref_papers/LiDAR-Based Bridge Displacement Estimation Using 3D Spatial Optimization.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“As civil engineering structures become larger, non-contact inspection technology is required to measure the overall shape and size of structures and evaluate safety. Structures are...”。

### 029. LiDAR-Based Structural Health Monitoring Applications in Civil Infrastructure Systems
- 文件：`ref_papers/LiDAR-Based Structural Health Monitoring Applications in Civil Infrastructure Systems.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“As innovative technologies emerge, extensive research has been undertaken to develop new structural health monitoring procedures. The current methods, involving on-site visual insp...”。

### 030. Low cost bridge load test calculating bridge displacement from acceleration for load assessment calculations
- 文件：`ref_papers/Low cost bridge load test calculating bridge displacement from acceleration for load assessment calculations.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Engineering Structures 143 (2017) 358–374 Contents lists available at ScienceDirect Engineering Structures journal homepage: www.elsevier.com/locate/engstruct Low cost bridge load...”。

### 031. Method for Improving Range Resolution of Indoor FMCW Radar Systems Using DNN
- 文件：`ref_papers/Method for Improving Range Resolution of Indoor FMCW Radar Systems Using DNN.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Various studies on object detection are being conducted, and in this regard, research on frequency-modulated continuous wave (FMCW) RADAR is being actively conducted. FMCW RADAR re...”。

### 032. Miniaturized Millimeter-Wave Radar Sensor for High-Accuracy Applications
- 文件：`ref_papers/Miniaturized_Millimeter-Wave_Radar_Sensor_for_High-Accuracy_Applications.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“A highly miniaturized and commercially available where the machined parts become smaller and smaller but the millimeter wave (mmw) radar sensor working in the frequency size of the...”。

### 033. Multi-sensor and Multi-frequency Data Fusion for Structural Health Monitoring
- 文件：`ref_papers/Multi-sensor and Multi-frequency Data Fusion for Structural Health Monitoring.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Engineering Structures 293 (2023) 116573 Contents lists available at ScienceDirect Engineering Structures journal homepage: www.elsevier.com/locate/engstruct Multi-rate Kalman filt...”。

### 034. Multiple-target tracking and track management for an FMCW radar network
- 文件：`ref_papers/Multiple-target tracking and track management for an FMCW radar network.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“A multiple-target tracking problem for a frequency-modulated continuous-wave (FMCW) radar network is formulated and an integrated track management system is presented to solve the...”。

### 035. Non-Target Structural Displacement Measurement Using Reference Frame-Based Deepflow
- 文件：`ref_papers/Non-Target Structural Displacement Measurement Using Reference Frame-Based Deepflow.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Displacement is crucial for structural health monitoring, although it is very challenging to measure under field conditions. Most existing displacement measurement methods are cost...”。

### 036. Real-time strong-motion broadband displacements from collocated GPS and accelerometers.
- 文件：`ref_papers/Real-time strong-motion broadband displacements from collocated GPS and accelerometers..pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“We present a new solution to the classical problem of deriving displace- ments from seismic data that is suitable for real-time monitoring. It relies on an optimal combination of c...”。

### 037. Recent Advances in mmWave-Radar-Based Sensing, Its Applications, and Machine Learning Techniques: A Review
- 文件：`ref_papers/Recent Advances in mmWave-Radar-Based Sensing, Its Applications, and Machine Learning Techniques: A Review.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Human gesture detection, obstacle detection, collision avoidance, parking aids, automotive driving, medical, meteorological, industrial, agriculture, defense, space, and other rele...”。

### 038. Reduced complexity angle-Doppler-range estimation for MIMO radar that employs compressive sensing
- 文件：`ref_papers/Reduced complexity angle-Doppler-range estimation for MIMO radar that employs compressive sensing.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The authors recently proposed a MIMO radar sys- The transmit nodes transmit periodic pulses. The receive nodes tem that is implemented by a small wireless network. By applying forw...”。

### 039. Research on a Super-Resolution and Low-Complexity Positioning Algorithm Using FMCW Radar Based on OMP and FFT in 2D Driving Scene
- 文件：`ref_papers/Research on a Super-Resolution and Low-Complexity Positioning Algorithm Using FMCW Radar Based on OMP and FFT in 2D Driving Scene.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Multitarget positioning technology, such as FMCW millimeter-wave radar, has broad application prospects in autonomous driving and related mobile scenarios. However, it is difficult...”。

### 040. Sensing Mechanism and Real-Time Bridge Displacement Monitoring for a Laboratory Truss Bridge Using Hybrid Data Fusion
- 文件：`ref_papers/Sensing Mechanism and Real-Time Bridge Displacement Monitoring for a Laboratory Truss Bridge Using Hybrid Data Fusion.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Remote and real-time displacement measurements are crucial for a successful bridge health monitoring program. Researchers have attempted to monitor the deformation of bridges using...”。

### 041. Structural Contr   Hlth - 2013 - Liu - Reliability analysis of bridge evaluations based on 3D Light Detection and Ranging
- 文件：`ref_papers/Structural Contr   Hlth - 2013 - Liu - Reliability analysis of bridge evaluations based on 3D Light Detection and Ranging.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“STRUCTURAL CONTROL AND HEALTH MONITORING Struct. Control Health Monit. 2013; 20:1397–1409 Published online 31 January 2013 in Wiley Online Library (wileyonlinelibrary.com). DOI: 10...”。

### 042. Structural Contr   Hlth - 2017 - Li - Structural health monitoring of maglev guideway PC girders with distributed
- 文件：`ref_papers/Structural Contr   Hlth - 2017 - Li - Structural health monitoring of maglev guideway PC girders with distributed.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Received: 20 October 2016 Revised: 6 April 2017 Accepted: 2 May 2017 DOI: 10.1002/stc.2046 RESEARCH ARTICLE Structural health monitoring of maglev guideway PC girders with distribu...”。

### 043. Structural Contr   Hlth - 2019 - Lee - Long‐term displacement measurement of bridges using a LiDAR system
- 文件：`ref_papers/Structural Contr   Hlth - 2019 - Lee - Long‐term displacement measurement of bridges using a LiDAR system.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Received: 9 October 2018 Revised: 7 April 2019 Accepted: 2 July 2019 DOI: 10.1002/stc.2428 RESEARCH ARTICLE Long‐term displacement measurement of bridges using a LiDAR system Junhw...”。

### 044. Structural Reliability Estimation with Participatory Sensing and Mobile Cyber-Physical Structural Health Monitoring Systems
- 文件：`ref_papers/Structural Reliability Estimation with Participatory Sensing and Mobile Cyber-Physical Structural Health Monitoring Systems.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“With the help of community participants, smartphones can become useful wireless sensor network (WSN) components, form a self-governing structural health monitoring (SHM) system, an...”。

### 045. Subspace-Based Detector For Distributed Mmwave Mimo Radar Sensors
- 文件：`ref_papers/Subspace-Based Detector For Distributed Mmwave Mimo Radar Sensors.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“𝐩2 Radar 2 Driven by emerging applications, mmWave radars are in- IWR6843ISK mmWave Sensor R2 creasingly being integrated into indoor scene monitoring Antenna Configuration 𝐩3 syst...”。

### 046. Transforming Structural Health Monitoring Leveraging Multisource Data Fusion With Two-Stage Encoder Transformer for Bridge Deformation Prediction
- 文件：`ref_papers/Transforming_Structural_Health_Monitoring_Leveraging_Multisource_Data_Fusion_With_Two-Stage_Encoder_Transformer_for_Bridge_Deformation_Prediction.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Bridge deformation monitoring is critical for ensur- I. I NTRODUCTION ing the structural integrity and safety of bridges, as it enables early detection of potential issues that may...”。

### 047. Unscented filtering and nonlinear estimation
- 文件：`ref_papers/Unscented filtering and nonlinear estimation.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：以状态空间/非线性滤波处理传感器噪声、漂移或非线性传播，是融合与相位跟踪的基础方法。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The Kalman filter(KF) is one of the most widely used methods for tracking and estimation due to its simplicity, optimality, tractability and robustness. However, the application of...”。

### 048. Vision and Vibration Data Fusion-Based Structural Dynamic Displacement Measurement with Test Validation
- 文件：`ref_papers/Vision and Vibration Data Fusion-Based Structural Dynamic Displacement Measurement with Test Validation.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“The dynamic measurement and identification of structural deformation are essential for structural health monitoring. Traditional contact-type displacement monitoring inevitably req...”。

### 049. Wireless Data Acquisition from Bridge Monitoring
- 文件：`ref_papers/Wireless Data Acquisition from Bridge Monitoring.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“This paper introduces composition of a system platform to collect data from a wireless monitoring bridge, II. COMPOSITION OF THE SYSTEM PLATFORM develops software to receive data f...”。

### 050. Wireless Displacement Sensing System for Bridges Using Multi-Sensor Fusion
- 文件：`ref_papers/Wireless Displacement Sensing System for Bridges Using Multi-Sensor Fusion.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Accurate displacement sensing or estimation is an important task for reliably assessing the condition of civil infrastructure such as bridges and buildings, because the structural...”。

### 051. cha-et-al-2019-a-terrestrial-lidar-based-detection-of-shape-deformation-for-maintenance-of-bridge-structures
- 文件：`ref_papers/cha-et-al-2019-a-terrestrial-lidar-based-detection-of-shape-deformation-for-maintenance-of-bridge-structures.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“A terrestrial light detection and ranging (LiDAR) can be used to construct the building information modeling as well as to measure shape deformation that varies with time or load d...”。

### 052. dai-et-al-2013-laser-based-field-measurement-for-a-bridge-finite-element-model-validation
- 文件：`ref_papers/dai-et-al-2013-laser-based-field-measurement-for-a-bridge-finite-element-model-validation.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“In bridge engineering, laser-based measurement techniques show promise in assisting field tests due to their noncontact features. Downloaded from ascelibrary.org by Tongji Universi...”。

### 053. 基于FBG监测及多传感器数据融合的高速磁浮轨道梁结构参数识别技术研究
- 文件：`ref_papers/基于FBG监测及多传感器数据融合的高速磁浮轨道梁结构参数识别技术研究.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“硕士学位论文 （专业学位） 基于 FBG 监测及多传感器数据融合的 高速磁浮轨道梁结构参数识别技术研究 姓 名：沈佳璇 学 号：2132355 学 院：土木工程学院 学科门类：工学 专业学位类别：土木水利 专业领域：建筑与土木工程 研究方向：结构工程 指导教师： 黄靖宇 同等学力硕士博士（打印时删除） 二〇二五年七月 I A thesis submitted...”。

### 054. 基于多传感器信息融合的桥梁健康监测系统的研究与实现
- 文件：`ref_papers/基于多传感器信息融合的桥梁健康监测系统的研究与实现.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“单位代码： 10293 密 级： 专 业 学 位 硕 士 论 文 论文题目： 基于多传感器信息融合的桥梁健康监 测系统的研究与实现 学 号 1214022626 姓 名 沈健 导 师 钱国明 教授 专业学位类别 工程硕士 类申请 型 全 日 制 专业（领域） 申请 电子与通信工程 论文提交日期 二零一七年二月 万方数据 Bridge health monit...”。

### 055. 多传感器空时偏差补偿和数据融合方法
- 文件：`ref_papers/多传感器空时偏差补偿和数据融合方法.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“博士学位论文 多传感器空时偏差补偿和数据融合方法 SPATIOTEMPORAL BIAS COMPENSATION AND DATA FUSION FOR MULTISENSOR SYSTEMS 卜石哲 哈尔滨工业大学 2022 年 12 月 万方数据 国内图书分类号：TN958.3 学校代码：10213 国际图书分类号：621.396.969.1 密级：公...”。

### 056. 多径利用雷达目标探测技术综述与展望
- 文件：`ref_papers/多径利用雷达目标探测技术综述与展望.pdf`
- 是否可作参考：方法支撑/可选引用
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：建议作为方法支撑或对照参考，按需要放入 target selection、range-angle 分离、滤波/融合或非接触位移背景。
- 摘要判断依据：摘要/首页显示主题约为“Abstract: The Multipath Exploitation Radar (MER) target detection technology is primarily based on the Non- Line-Of-Sight (NLOS) multipath propagation characteristics of electromag...”。


## 背景铺垫
### 001. A Review of Sensing Technologies for Non-Destructive Evaluation of Structural Composite Materials
- 文件：`ref_papers/A Review of Sensing Technologies for Non-Destructive Evaluation of Structural Composite Materials.pdf`
- 是否可作参考：背景铺垫
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：可作为引言和相关工作背景，引用时只保留与结构位移监测或传感器谱系有关的句子。
- 摘要判断依据：摘要/首页显示主题约为“The growing demand and diversity in the application of industrial composites and the current inability of present non-destructive evaluation (NDE) methods to perform detailed inspe...”。

### 002. A wireless piezoelectric sensor network for distributed structural health monitoring
- 文件：`ref_papers/A_wireless_piezoelectric_sensor_network_for_distributed_structural_health_monitoring.pdf`
- 是否可作参考：背景铺垫
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：可作为引言和相关工作背景，引用时只保留与结构位移监测或传感器谱系有关的句子。
- 摘要判断依据：摘要/首页显示主题约为“This paper presents the development of a newly degradation, defects and damages (e.g. cracks), the designed wireless piezoelectric (PZT) sensor platform for characteristics of the...”。

### 003. Design Of A Bridge Structural Integrity Wireless Monitoring System For Computer Engineering Education
- 文件：`ref_papers/Design Of A Bridge Structural Integrity Wireless Monitoring System For Computer Engineering Education.pdf`
- 是否可作参考：背景铺垫
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：可作为引言和相关工作背景，引用时只保留与结构位移监测或传感器谱系有关的句子。
- 摘要判断依据：摘要/首页显示主题约为“A wireless sensors based system is designed for computer engineering students to remotely monitor the structural integrity of a truss metal bridge model. Triple axes accelerometers...”。

### 004. Recent Advancements in Non-Destructive Testing Techniques for Structural Health Monitoring
- 文件：`ref_papers/Recent Advancements in Non-Destructive Testing Techniques for Structural Health Monitoring.pdf`
- 是否可作参考：背景铺垫
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：可作为引言和相关工作背景，引用时只保留与结构位移监测或传感器谱系有关的句子。
- 摘要判断依据：摘要/首页显示主题约为“Structural health monitoring (SHM) is an important aspect of the assessment of various structures and infrastructure, which involves inspection, monitoring, and maintenance to supp...”。


## 无关-当前不采用PINN/神经场路线
### 001. A Machine Learning Approach to Bridge-Damage Detection Using Responses Measured on a Passing Vehicle
- 文件：`ref_papers/99_irrelevant_literature/A Machine Learning Approach to Bridge-Damage Detection Using Responses Measured on a Passing Vehicle.pdf`
- 原位置：`ref_papers/A Machine Learning Approach to Bridge-Damage Detection Using Responses Measured on a Passing Vehicle.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper proposes a new two-stage machine learning approach for bridge damage detection using the responses measured on a passing vehicle. In the first stage, an artificial neura...”。

### 002. A Physics-Guided Neural Network Framework for Elastic Plates: Comparison of Governing Equations-Based and Energy-Based Approaches
- 文件：`ref_papers/99_irrelevant_literature/A Physics-Guided Neural Network Framework for Elastic Plates: Comparison of Governing Equations-Based and Energy-Based Approaches.pdf`
- 原位置：`ref_papers/A Physics-Guided Neural Network Framework for Elastic Plates: Comparison of Governing Equations-Based and Energy-Based Approaches.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“A P HYSICS -G UIDED N EURAL N ETWORK F RAMEWORK FOR E LASTIC P LATES : C OMPARISON OF G OVERNING E QUATIONS -BASED AND E NERGY-BASED A PPROACHES A P REPRINT Wei Li a Martin Z. Baza...”。

### 003. A transfer learning enhanced the physics-informed neural network model for vortex-induced vibration
- 文件：`ref_papers/99_irrelevant_literature/A transfer learning enhanced the physics-informed neural network model for vortex-induced vibration.pdf`
- 原位置：`ref_papers/A transfer learning enhanced the physics-informed neural network model for vortex-induced vibration.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Vortex-induced vibration (VIV) is a typical nonlinear fluid-structure interaction phenomenon, which widely exists in practical engineering (the flexible riser, the bridge and the a...”。

### 004. Bayesian Parameter Estimation of Vibrating Systems via Physics-Based Biases from Neural Networks
- 文件：`ref_papers/99_irrelevant_literature/Bayesian Parameter Estimation of Vibrating Systems via Physics-Based Biases from Neural Networks.pdf`
- 原位置：`ref_papers/Bayesian Parameter Estimation of Vibrating Systems via Physics-Based Biases from Neural Networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. Often, Structural Health Monitoring (SHM) campaigns draw damage- identifiers from vibration-based monitoring data. One of the downstream tasks of vibration-based SHM is that of s...”。

### 005. Characterizing possible failure modes in physics-informed neural networks
- 文件：`ref_papers/99_irrelevant_literature/Characterizing possible failure modes in physics-informed neural networks.pdf`
- 原位置：`ref_papers/Characterizing possible failure modes in physics-informed neural networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Recent work in scientific machine learning has developed so-called physics- informed neural network (PINN) models. The typical approach is to incorporate physical domain knowledge...”。

### 006. Correcting model misspecification in physics-informed neural networks (PINNs)
- 文件：`ref_papers/99_irrelevant_literature/Correcting model misspecification in physics-informed neural networks (PINNs).pdf`
- 原位置：`ref_papers/Correcting model misspecification in physics-informed neural networks (PINNs).pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Data-driven discovery of governing equations in computational science has emerged as a new paradigm for obtaining accurate physical models and as a possible alternative to theoreti...”。

### 007. DPM: A Novel Training Method for Physics-Informed Neural Networks in Extrapolation
- 文件：`ref_papers/99_irrelevant_literature/DPM: A Novel Training Method for Physics-Informed Neural Networks in Extrapolation.pdf`
- 原位置：`ref_papers/DPM: A Novel Training Method for Physics-Informed Neural Networks in Extrapolation.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“been dominant choices for solving such nonlinear time- dependent PDEs, as they have demonstrated their effective- We present a method for learning dynamics of complex physi- ness i...”。

### 008. Deep Autoencoder based Energy Method for the Bending, Vibration, and Buckling Analysis of Kirchhoff Plates
- 文件：`ref_papers/99_irrelevant_literature/Deep Autoencoder based Energy Method for the Bending, Vibration, and Buckling Analysis of Kirchhoff Plates.pdf`
- 原位置：`ref_papers/Deep Autoencoder based Energy Method for the Bending, Vibration, and Buckling Analysis of Kirchhoff Plates.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, we present a deep autoencoder based energy method (DAEM) for the bending, vibration and buckling analysis of Kirchhoff plates. The DAEM exploits the higher order con...”。

### 009. Deep learning for solution and inversion of structural mechanics and vibrations
- 文件：`ref_papers/99_irrelevant_literature/Deep learning for solution and inversion of structural mechanics and vibrations.pdf`
- 原位置：`ref_papers/Deep learning for solution and inversion of structural mechanics and vibrations.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“D EEP LEARNING FOR SOLUTION AND INVERSION OF STRUCTURAL MECHANICS AND VIBRATIONS ∗ Ehsan Haghighat Ali C. Bekar arXiv:2105.09477v1 [cs.LG] 18 May 2021 Department of Civil Engineeri...”。

### 010. Dynamic Predictions from Time Series Data — An Artificial Neural Network Approach
- 文件：`ref_papers/99_irrelevant_literature/Dynamic Predictions from Time Series Data — An Artificial Neural Network Approach.pdf`
- 原位置：`ref_papers/Dynamic Predictions from Time Series Data — An Artificial Neural Network Approach.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Dynamic Predictions from Time Series Data - An Artificial Neural Network Approach D. R. Kulkarni1, A.S. Pandya2 and J. C. Parikh1 arXiv:comp-gas/9707001v1 27 Jun 1997 1 Physical Re...”。

### 011. Effect of training algorithms on neural networks aided pavement diagnosis
- 文件：`ref_papers/99_irrelevant_literature/Effect of training algorithms on neural networks aided pavement diagnosis.pdf`
- 原位置：`ref_papers/Effect of training algorithms on neural networks aided pavement diagnosis.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Routine pavement maintenance necessitates present structural diagnosis and condition evaluation of pavements by employing non-destructive test equipment such as the Falling Weight...”。

### 012. Enhanced physics‐informed neural networks for hyperelasticity
- 文件：`ref_papers/99_irrelevant_literature/Enhanced physics‐informed neural networks for hyperelasticity.pdf`
- 原位置：`ref_papers/Enhanced physics‐informed neural networks for hyperelasticity.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“E NHANCED PHYSICS - INFORMED NEURAL NETWORKS FOR HYPERELASTICITY A P REPRINT Diab W. Abueidda∗ Seid Koric National Center for Supercomputing Applications National Center for Superc...”。

### 013. Error convergence and engineering-guided hyperparameter search of PINNs: towards optimized I-FENN performance
- 文件：`ref_papers/99_irrelevant_literature/Error convergence and engineering-guided hyperparameter search of PINNs: towards optimized I-FENN performance.pdf`
- 原位置：`ref_papers/Error convergence and engineering-guided hyperparameter search of PINNs: towards optimized I-FENN performance.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In our recently proposed Integrated Finite Element Neural Network (I-FENN) framework [1] we showcased how PINNs can be deployed on a finite element-level basis to swiftly approxima...”。

### 014. Estimates on the generalization error of Physics Informed Neural Networks (PINNs) for approximating PDEs
- 文件：`ref_papers/99_irrelevant_literature/Estimates on the generalization error of Physics Informed Neural Networks (PINNs) for approximating PDEs.pdf`
- 原位置：`ref_papers/Estimates on the generalization error of Physics Informed Neural Networks (PINNs) for approximating PDEs.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics informed neural networks (PINNs) have recently been widely used for robust and accurate approximation of PDEs. We provide upper bounds on the generalization error of PINNs...”。

### 015. Extreme Theory of Functional Connections: A Physics-Informed Neural Network Method for Solving Parametric Differential Equations
- 文件：`ref_papers/99_irrelevant_literature/Extreme Theory of Functional Connections: A Physics-Informed Neural Network Method for Solving Parametric Differential Equations.pdf`
- 原位置：`ref_papers/Extreme Theory of Functional Connections: A Physics-Informed Neural Network Method for Solving Parametric Differential Equations.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this work we present a novel, accurate, and robust physics-informed method for solving problems involving parametric differential equations (DEs) called the Extreme Theory of Fu...”。

### 016. Gradient Statistics-Based Multi-Objective Optimization in Physics-Informed Neural Networks
- 文件：`ref_papers/99_irrelevant_literature/Gradient Statistics-Based Multi-Objective Optimization in Physics-Informed Neural Networks.pdf`
- 原位置：`ref_papers/Gradient Statistics-Based Multi-Objective Optimization in Physics-Informed Neural Networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Modeling and simulation of complex non-linear systems are essential in physics, engineer- ing, and signal processing. Neural networks are widely regarded for such tasks due to thei...”。

### 017. Identification of Human Motion Using Radar Sensor in an Indoor Environment
- 文件：`ref_papers/99_irrelevant_literature/Identification of Human Motion Using Radar Sensor in an Indoor Environment.pdf`
- 原位置：`ref_papers/Identification of Human Motion Using Radar Sensor in an Indoor Environment.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, we propose a method of identifying human motions, such as standing, walking, running, and crawling, using a millimeter wave radar sensor. In our method, two signal p...”。

### 018. Investigating and Mitigating Failure Modes in Physics-informed Neural Networks (PINNs)
- 文件：`ref_papers/99_irrelevant_literature/Investigating and Mitigating Failure Modes in Physics-informed Neural Networks (PINNs).pdf`
- 原位置：`ref_papers/Investigating and Mitigating Failure Modes in Physics-informed Neural Networks (PINNs).pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. This paper explores the difficulties in solving partial differential equations (PDEs) using physics-informed neural networks (PINNs). PINNs use physics as a reg- ularization term...”。

### 019. Lagrangian PINNs: A causality-conforming solution to failure modes of physics-informed neural networks
- 文件：`ref_papers/99_irrelevant_literature/Lagrangian PINNs: A causality-conforming solution to failure modes of physics-informed neural networks.pdf`
- 原位置：`ref_papers/Lagrangian PINNs: A causality-conforming solution to failure modes of physics-informed neural networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics–informed neural networks (PINNs) leverage neural–networks to find the solutions of partial differential equa- tion (PDE)–constrained optimization problems with initial cond...”。

### 020. Learning and correcting non-Gaussian model errors
- 文件：`ref_papers/99_irrelevant_literature/Learning and correcting non-Gaussian model errors.pdf`
- 原位置：`ref_papers/Learning and correcting non-Gaussian model errors.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“All discretized numerical models contain modelling errors – this reality is ampliﬁed when reduced-order models are used. The ability to accurately approximate modelling errors info...”。

### 021. Learning in Sinusoidal Spaces With Physics-Informed Neural Networks
- 文件：`ref_papers/99_irrelevant_literature/Learning in Sinusoidal Spaces With Physics-Informed Neural Networks.pdf`
- 原位置：`ref_papers/Learning in Sinusoidal Spaces With Physics-Informed Neural Networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“A physics-informed neural network (PINN) uses The uniqueness of a PINN lies in incorporating the residual physics-augmented loss functions, e.g., incorporating the residual term fo...”。

### 022. Learning solution of nonlinear constitutive material models using physics-informed neural networks: COMM-PINN
- 文件：`ref_papers/99_irrelevant_literature/Learning solution of nonlinear constitutive material models using physics-informed neural networks: COMM-PINN.pdf`
- 原位置：`ref_papers/Learning solution of nonlinear constitutive material models using physics-informed neural networks: COMM-PINN.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“We applied physics-informed neural networks to solve the constitutive relations for nonlin- ear, path-dependent material behavior. As a result, the trained network not only satisfi...”。

### 023. Moving load induced dynamic response analysis of bridge based on physics-informed neural network
- 文件：`ref_papers/99_irrelevant_literature/Moving load induced dynamic response analysis of bridge based on physics-informed neural network.pdf`
- 原位置：`ref_papers/Moving load induced dynamic response analysis of bridge based on physics-informed neural network.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Advanced Engineering Informatics 65 (2025) 103215 Contents lists available at ScienceDirect Advanced Engineering Informatics journal homepage: www.elsevier.com/locate/aei Moving lo...”。

### 024. Neural modal ordinary differential equations: Integrating physics-based modeling with neural ordinary differential equations for modeling high-dimensional monitored structures
- 文件：`ref_papers/99_irrelevant_literature/Neural modal ordinary differential equations: Integrating physics-based modeling with neural ordinary differential equations for modeling high-dimensional monitored structures.pdf`
- 原位置：`ref_papers/Neural modal ordinary differential equations: Integrating physics-based modeling with neural ordinary differential equations for modeling high-dimensional monitored structures.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The dimension of models derived on the basis of data is commonly restricted by the number of observations, or in the context of monitored systems, sensing nodes. This is particular...”。

### 025. NeuralPDE: Automating Physics-Informed Neural Networks (PINNs) with Error Approximations
- 文件：`ref_papers/99_irrelevant_literature/NeuralPDE: Automating Physics-Informed Neural Networks (PINNs) with Error Approximations.pdf`
- 原位置：`ref_papers/NeuralPDE: Automating Physics-Informed Neural Networks (PINNs) with Error Approximations.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-informed neural networks (PINNs) are an increasingly power- ful way to solve partial differential equations, generate digital twins, and create neural surrogates of physica...”。

### 026. NeuralSI: Structural Parameter Identification in Nonlinear Dynamical Systems
- 文件：`ref_papers/99_irrelevant_literature/NeuralSI: Structural Parameter Identification in Nonlinear Dynamical Systems.pdf`
- 原位置：`ref_papers/NeuralSI: Structural Parameter Identification in Nonlinear Dynamical Systems.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. Structural monitoring for complex built environments often suffers from mismatch between design, laboratory testing, and actual built parameters. Additionally, real-world structu...”。

### 027. Novel Physics-Informed Artificial Neural Network Architectures for System and Input Identification of Structural Dynamics PDEs
- 文件：`ref_papers/99_irrelevant_literature/Novel Physics-Informed Artificial Neural Network Architectures for System and Input Identification of Structural Dynamics PDEs.pdf`
- 原位置：`ref_papers/Novel Physics-Informed Artificial Neural Network Architectures for System and Input Identification of Structural Dynamics PDEs.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Herein, two novel Physics Informed Neural Network (PINN) architectures are proposed for output‑only system identification and input estimation of dynamic systems. Using merely spar...”。

### 028. On spike-and-slab priors for Bayesian equation discovery of nonlinear dynamical systems via sparse linear regression
- 文件：`ref_papers/99_irrelevant_literature/On spike-and-slab priors for Bayesian equation discovery of nonlinear dynamical systems via sparse linear regression.pdf`
- 原位置：`ref_papers/On spike-and-slab priors for Bayesian equation discovery of nonlinear dynamical systems via sparse linear regression.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper presents the use of spike-and-slab (SS) priors for discovering governing diﬀerential equations of motion of nonlinear structural dynamic systems. The problem of discover...”。

### 029. On the convergence of PINNs
- 文件：`ref_papers/99_irrelevant_literature/On the convergence of PINNs.pdf`
- 原位置：`ref_papers/On the convergence of PINNs.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-informed neural networks (PINNs) are a promising approach that combines the power of neural networks with the interpretability of physical modeling. PINNs have shown good p...”。

### 030. Optimal control of PDEs using physics-informed neural networks
- 文件：`ref_papers/99_irrelevant_literature/Optimal control of PDEs using physics-informed neural networks.pdf`
- 原位置：`ref_papers/Optimal control of PDEs using physics-informed neural networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-informed neural networks (PINNs) have recently become a popular method for solving forward and arXiv:2111.09880v4 [math.OC] 4 Nov 2022 inverse problems governed by partial...”。

### 031. Optimally weighted loss functions for solving PDEs with Neural Networks
- 文件：`ref_papers/99_irrelevant_literature/Optimally weighted loss functions for solving PDEs with Neural Networks.pdf`
- 原位置：`ref_papers/Optimally weighted loss functions for solving PDEs with Neural Networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Optimally weighted loss functions for solving PDEs with Neural Networks Remco van der Meer,1, 2 Cornelis Oosterlee,1, 2 and Anastasia Borovykh1, 3 1 CWI, Science Park 123, 1098 XG...”。

### 032. PHYSICS-INFORMED NEURAL NETWORKS FOR ELASTIC PLATE PROBLEMS WITH BENDING AND WINKLER-TYPE CONTACT EFFECTS
- 文件：`ref_papers/99_irrelevant_literature/PHYSICS-INFORMED NEURAL NETWORKS FOR ELASTIC PLATE PROBLEMS WITH BENDING AND WINKLER-TYPE CONTACT EFFECTS.pdf`
- 原位置：`ref_papers/PHYSICS-INFORMED NEURAL NETWORKS FOR ELASTIC PLATE PROBLEMS WITH BENDING AND WINKLER-TYPE CONTACT EFFECTS.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Kirchhoff plate bending and Winkler-type contact problems with different boundary conditions are solved with the use of physics-informed neural networks (PINN). The PINN is built o...”。

### 033. Parametric Neural Networks as Full-Field Surrogates for Material Model Calibration
- 文件：`ref_papers/99_irrelevant_literature/Parametric Neural Networks as Full-Field Surrogates for Material Model Calibration.pdf`
- 原位置：`ref_papers/Parametric Neural Networks as Full-Field Surrogates for Material Model Calibration.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. Parametric neural networks as full-field surrogates have recently gained increasing interest in the context of many-query tasks such as real-time simulations, uncertainty quantif...”。

### 034. Physical Activation Functions (PAFs): An Approach for More Efficient Induction of Physics into Physics-Informed Neural Networks (PINNs)
- 文件：`ref_papers/99_irrelevant_literature/Physical Activation Functions (PAFs): An Approach for More Efficient Induction of Physics into Physics-Informed Neural Networks (PINNs).pdf`
- 原位置：`ref_papers/Physical Activation Functions (PAFs): An Approach for More Efficient Induction of Physics into Physics-Informed Neural Networks (PINNs).pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In recent years, the evolution of Physics-Informed Neural Networks (PINNs) has reduced the gap between Deep Learning (DL) based methods and analytical/numerical approaches in scien...”。

### 035. Physics Informed Deep Learning (Part I): Data-driven Solutions of Nonlinear Partial Differential Equations
- 文件：`ref_papers/99_irrelevant_literature/Physics Informed Deep Learning (Part I): Data-driven Solutions of Nonlinear Partial Differential Equations.pdf`
- 原位置：`ref_papers/Physics Informed Deep Learning (Part I): Data-driven Solutions of Nonlinear Partial Differential Equations.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“We introduce physics informed neural networks – neural networks that are trained to solve supervised learning tasks while respecting any given law of physics described by general n...”。

### 036. Physics informed deep learning for computational elastodynamics without labeled data
- 文件：`ref_papers/99_irrelevant_literature/Physics informed deep learning for computational elastodynamics without labeled data.pdf`
- 原位置：`ref_papers/Physics informed deep learning for computational elastodynamics without labeled data.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Numerical methods such as finite element have been flourishing in the past decades for modeling solid mechanics problems via solving governing partial differential equations (PDEs)...”。

### 037. Physics-Informed Neural Network (PINN) Evolution and Beyond: A Systematic Literature Review and Bibliometric Analysis
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed Neural Network (PINN) Evolution and Beyond: A Systematic Literature Review and Bibliometric Analysis.pdf`
- 原位置：`ref_papers/Physics-Informed Neural Network (PINN) Evolution and Beyond: A Systematic Literature Review and Bibliometric Analysis.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This research aims to study and assess state-of-the-art physics-informed neural networks (PINNs) from different researchers’ perspectives. The PRISMA framework was used for a syste...”。

### 038. Physics-Informed Neural Networks for Material Model Calibration from Full-Field Displacement Data
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed Neural Networks for Material Model Calibration from Full-Field Displacement Data.pdf`
- 原位置：`ref_papers/Physics-Informed Neural Networks for Material Model Calibration from Full-Field Displacement Data.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The identification of material parameters occurring in constitutive models has a wide range of applications in practice. One of these applications is the monitoring and assessment...”。

### 039. Physics-Informed Neural Networks for Power Systems
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed Neural Networks for Power Systems.pdf`
- 原位置：`ref_papers/Physics-Informed Neural Networks for Power Systems.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper introduces for the first time, to our inside the training procedure. Exploiting advances in auto- knowledge, a framework for physics-informed neural networks matic diffe...”。

### 040. Physics-Informed Neural Networks for Solving Forward and Inverse Problems in Complex Beam Systems
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed Neural Networks for Solving Forward and Inverse Problems in Complex Beam Systems.pdf`
- 原位置：`ref_papers/Physics-Informed Neural Networks for Solving Forward and Inverse Problems in Complex Beam Systems.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This article proposes a new framework using catenary–pantograph interactions in railways (damped beam physics-informed neural networks (PINNs) to simulate complex equations) [3] to...”。

### 041. Physics-Informed Neural networks for Advanced modeling
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed Neural networks for Advanced modeling.pdf`
- 原位置：`ref_papers/Physics-Informed Neural networks for Advanced modeling.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“abstract interfaces not only for better structure of the source code but especially to give the final user an easy entry point to implement their own extensions, like new loss func...”。

### 042. Physics-Informed Neural Network based Damage Ident
- 文件：`ref_papers/99_irrelevant_literature/Physics-Informed_Neural_Network_based_Damage_Ident.pdf`
- 原位置：`ref_papers/Physics-Informed_Neural_Network_based_Damage_Ident.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Railroad bridges are a crucial component of the U.S. freight rail system, which moves over 40 percent of the nation’s freight and plays a critical role in the economy. However, agi...”。

### 043. Physics-informed neural networks for structural health monitoring: a case study for Kirchhoff–Love plates
- 文件：`ref_papers/99_irrelevant_literature/Physics-informed neural networks for structural health monitoring: a case study for Kirchhoff–Love plates.pdf`
- 原位置：`ref_papers/Physics-informed neural networks for structural health monitoring: a case study for Kirchhoff–Love plates.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-informed neural networks (PINNs), which are a recent development and incorporate physics-based know- ledge into neural networks (NNs) in the form of constraints (e.g., disp...”。

### 044. Physics-informed surrogate modeling for a damaged rotating shaft
- 文件：`ref_papers/99_irrelevant_literature/Physics-informed surrogate modeling for a damaged rotating shaft.pdf`
- 原位置：`ref_papers/Physics-informed surrogate modeling for a damaged rotating shaft.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. In online structural health monitoring frameworks, surrogate modeling approaches aim to reproduce the dynamics of an underlying high-fidelity model for facilitating fast simulati...”。

### 045. Real-Time Hybrid Simulation with Deep Learning Computational Substructures: System Validation Using Linear Specimens
- 文件：`ref_papers/99_irrelevant_literature/Real-Time Hybrid Simulation with Deep Learning Computational Substructures: System Validation Using Linear Specimens.pdf`
- 原位置：`ref_papers/Real-Time Hybrid Simulation with Deep Learning Computational Substructures: System Validation Using Linear Specimens.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Hybrid simulation (HS) is an advanced simulation method that couples experimental testing and analytical modeling to better understand structural systems and individual components’...”。

### 046. Respecting causality is all you need for training physics-informed neural networks
- 文件：`ref_papers/99_irrelevant_literature/Respecting causality is all you need for training physics-informed neural networks.pdf`
- 原位置：`ref_papers/Respecting causality is all you need for training physics-informed neural networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“R ESPECTING CAUSALITY IS ALL YOU NEED FOR TRAINING PHYSICS - INFORMED NEURAL NETWORKS Sifan Wang Shyam Sankaran Graduate Group in Applied Mathematics Department of Mechanical Engin...”。

### 047. Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What’s Next
- 文件：`ref_papers/99_irrelevant_literature/Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What’s Next.pdf`
- 原位置：`ref_papers/Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What’s Next.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-Informed Neural Networks (PINN) are neural networks (NNs) that encode model equations, like Partial Differential Equations (PDE), as a component of the neural network itsel...”。

### 048. Simultaneous Target Classification and Moving Direction Estimation in Millimeter-Wave Radar System
- 文件：`ref_papers/99_irrelevant_literature/Simultaneous Target Classification and Moving Direction Estimation in Millimeter-Wave Radar System.pdf`
- 原位置：`ref_papers/Simultaneous Target Classification and Moving Direction Estimation in Millimeter-Wave Radar System.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this study, we propose a method to identify the type of target and simultaneously determine its moving direction in a millimeter-wave radar system. First, using a frequency-modu...”。

### 049. Solving differential equations using physics informed deep learning: a hand-on tutorial with benchmark tests
- 文件：`ref_papers/99_irrelevant_literature/Solving differential equations using physics informed deep learning: a hand-on tutorial with benchmark tests.pdf`
- 原位置：`ref_papers/Solving differential equations using physics informed deep learning: a hand-on tutorial with benchmark tests.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“We revisit the original approach of using deep learning and neural networks to solve differential equations by incorporating the knowledge of the equation. This is done by adding a...”。

### 050. Target Classification Using Frontal Images Measured by 77 GHz FMCW Radar through DCNN
- 文件：`ref_papers/99_irrelevant_literature/Target Classification Using Frontal Images Measured by 77 GHz FMCW Radar through DCNN.pdf`
- 原位置：`ref_papers/Target Classification Using Frontal Images Measured by 77 GHz FMCW Radar through DCNN.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper proposes a target classification method using radar frontal imaging measured by millimeter-wave multiple-input multiple-output (MW-MIMO) radar through deep convolutional...”。

### 051. Transfer learning based physics-informed neural networks for solving inverse problems in engineering structures under different loading scenarios
- 文件：`ref_papers/99_irrelevant_literature/Transfer learning based physics-informed neural networks for solving inverse problems in engineering structures under different loading scenarios.pdf`
- 原位置：`ref_papers/Transfer learning based physics-informed neural networks for solving inverse problems in engineering structures under different loading scenarios.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Recently, a class of machine learning methods called physics-informed neural networks (PINNs) has been proposed and gained prevalence in solving various scientific computing proble...”。

### 052. Understanding Physics-Informed Neural Networks: Techniques, Applications, Trends, and Challenges
- 文件：`ref_papers/99_irrelevant_literature/Understanding Physics-Informed Neural Networks: Techniques, Applications, Trends, and Challenges.pdf`
- 原位置：`ref_papers/Understanding Physics-Informed Neural Networks: Techniques, Applications, Trends, and Challenges.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Physics-informed neural networks (PINNs) represent a significant advancement at the intersection of machine learning and physical sciences, offering a powerful framework for solvin...”。

### 053. Understanding and mitigating gradient pathologies in physics-informed neural networks
- 文件：`ref_papers/99_irrelevant_literature/Understanding and mitigating gradient pathologies in physics-informed neural networks.pdf`
- 原位置：`ref_papers/Understanding and mitigating gradient pathologies in physics-informed neural networks.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“U NDERSTANDING AND MITIGATING GRADIENT PATHOLOGIES IN PHYSICS - INFORMED NEURAL NETWORKS A P REPRINT Sifan Wang Yujun Teng Graduate Group in Applied Mathematics Department of Mecha...”。

### 054. Variational Physics-Informed Neural Networks For Solving Partial Differential Equations
- 文件：`ref_papers/99_irrelevant_literature/Variational Physics-Informed Neural Networks For Solving Partial Differential Equations.pdf`
- 原位置：`ref_papers/Variational Physics-Informed Neural Networks For Solving Partial Differential Equations.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. Physics-informed neural networks (PINNs) [31] use automatic differentiation to solve partial differ- ential equations (PDEs) by penalizing the PDE in the loss function at a rando...”。

### 055. When and why PINNs fail to train: A neural tangent kernel perspective
- 文件：`ref_papers/99_irrelevant_literature/When and why PINNs fail to train: A neural tangent kernel perspective.pdf`
- 原位置：`ref_papers/When and why PINNs fail to train: A neural tangent kernel perspective.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新集中在 PINN/物理约束神经网络、神经算子或结构力学正反问题求解。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“W HEN AND WHY PINN S FAIL TO TRAIN : A NEURAL TANGENT KERNEL PERSPECTIVE A P REPRINT Sifan Wang Xinling Yu Graduate Group in Applied Mathematics Graduate Group in Applied Mathemati...”。

### 056. YOLO-Based Simultaneous Target Detection and Classification in Automotive FMCW Radar Systems
- 文件：`ref_papers/99_irrelevant_literature/YOLO-Based Simultaneous Target Detection and Classification in Automotive FMCW Radar Systems.pdf`
- 原位置：`ref_papers/YOLO-Based Simultaneous Target Detection and Classification in Automotive FMCW Radar Systems.pdf`
- 是否可作参考：无关-当前不采用PINN/神经场路线
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：物理方程/边界条件/少量观测 -> 构造 PINN/神经网络损失 -> 迭代训练 -> PDE解、材料参数或结构响应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper proposes a method to simultaneously detect and classify objects by using a deep learning model, specifically you only look once (YOLO), with pre-processed automotive rad...”。


## 无关-通信感知/车载雷达主线
### 001. 6G for Vehicle-to-Everything (V2X) Communications: Enabling Technologies, Challenges, and Opportunities
- 文件：`ref_papers/99_irrelevant_literature/6G for Vehicle-to-Everything (V2X) Communications: Enabling Technologies, Challenges, and Opportunities.pdf`
- 原位置：`ref_papers/6G for Vehicle-to-Everything (V2X) Communications: Enabling Technologies, Challenges, and Opportunities.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“/ We are on the cusp of a new era of connected Manuscript received December 26, 2020; revised March 14, 2022; accepted autonomous vehicles with unprecedented user experiences, Apri...”。

### 002. A Receiver Architecture for Dual-Functional Massive MIMO OFDM RadCom Systems
- 文件：`ref_papers/99_irrelevant_literature/A Receiver Architecture for Dual-Functional Massive MIMO OFDM RadCom Systems.pdf`
- 原位置：`ref_papers/A Receiver Architecture for Dual-Functional Massive MIMO OFDM RadCom Systems.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This study1 introduces a receiver architecture for dual-functional communication and radar (RadCom) base-stations (BS), which exploits the spatial diversity between the received ra...”。

### 003. A Review on Autonomous Vehicles: Progress, Methods and Challenges
- 文件：`ref_papers/99_irrelevant_literature/A Review on Autonomous Vehicles: Progress, Methods and Challenges.pdf`
- 原位置：`ref_papers/A Review on Autonomous Vehicles: Progress, Methods and Challenges.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Vehicular technology has recently gained increasing popularity, and autonomous driving is a hot topic. To achieve safe and reliable intelligent transportation systems, accurate pos...”。

### 004. A Survey of Autonomous Vehicles: Enabling Communication Technologies and Challenges
- 文件：`ref_papers/99_irrelevant_literature/A Survey of Autonomous Vehicles: Enabling Communication Technologies and Challenges.pdf`
- 原位置：`ref_papers/A Survey of Autonomous Vehicles: Enabling Communication Technologies and Challenges.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The Department of Transport in the United Kingdom recorded 25,080 motor vehicle fatali- ties in 2019. This situation stresses the need for an intelligent transport system (ITS) tha...”。

### 005. A Two-Stage Radar Sensing Approach based on MIMO-OFDM Technology
- 文件：`ref_papers/99_irrelevant_literature/A Two-Stage Radar Sensing Approach based on MIMO-OFDM Technology.pdf`
- 原位置：`ref_papers/A Two-Stage Radar Sensing Approach based on MIMO-OFDM Technology.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Abstract—Recently, integrating the communication and sens- when applying the correlation processing. On the other hand, arXiv:2011.06161v1 [eess.SP] 12 Nov 2020 ing functions into...”。

### 006. Compressive Sensing-Based Radar Imaging and Subcarrier Allocation for Joint MIMO OFDM Radar and Communication System
- 文件：`ref_papers/99_irrelevant_literature/Compressive Sensing-Based Radar Imaging and Subcarrier Allocation for Joint MIMO OFDM Radar and Communication System.pdf`
- 原位置：`ref_papers/Compressive Sensing-Based Radar Imaging and Subcarrier Allocation for Joint MIMO OFDM Radar and Communication System.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：提供角度估计、稀疏恢复、波束形成或虚拟阵列增强思路，可支撑从 rangeBin target 升级到 range-angle target。
- 方法论/数据处理流：ADC/IF 或 range FFT 数据 -> 虚拟阵列/协方差/稀疏字典 -> AoA/range-angle 谱或波束输出 -> 目标定位/复 slow-time 信号。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, a joint multiple-input multiple-output (MIMO OFDM) radar and communication (RadCom) system is proposed, in which orthogonal frequency division multiplexing (OFDM) wa...”。

### 007. Evolution of Non-Terrestrial Networks From 5G to 6G: A Survey
- 文件：`ref_papers/99_irrelevant_literature/Evolution of Non-Terrestrial Networks From 5G to 6G: A Survey.pdf`
- 原位置：`ref_papers/Evolution of Non-Terrestrial Networks From 5G to 6G: A Survey.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Non-terrestrial networks (NTNs) traditionally have (HAPs), and satellite networks, are traditionally used for cer- certain limited applications. However, the recent technological t...”。

### 008. Feasibility of Non-Line-of-Sight Integrated Sensing and Communication at mmWave
- 文件：`ref_papers/99_irrelevant_literature/Feasibility of Non-Line-of-Sight Integrated Sensing and Communication at mmWave.pdf`
- 原位置：`ref_papers/Feasibility of Non-Line-of-Sight Integrated Sensing and Communication at mmWave.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“One rarely addressed direction in the context of reuse of the same infrastructure deployed for communication Integrated Sensing and Communication (ISAC) is non-line-of- purposes wi...”。

### 009. IEEE 802.11ad Based Joint Radar Communication Transceiver: Design, Prototype and Performance Analysis
- 文件：`ref_papers/99_irrelevant_literature/IEEE 802.11ad Based Joint Radar Communication Transceiver: Design, Prototype and Performance Analysis.pdf`
- 原位置：`ref_papers/IEEE 802.11ad Based Joint Radar Communication Transceiver: Design, Prototype and Performance Analysis.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Rapid beam alignment is required to support high to the high propagation loss at these carrier frequencies, gain millimeter wave (mmW) communication links between they are meant to...”。

### 010. Intelligent metasurfaces: control, communication and computing
- 文件：`ref_papers/99_irrelevant_literature/Intelligent metasurfaces: control, communication and computing.pdf`
- 原位置：`ref_papers/Intelligent metasurfaces: control, communication and computing.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Controlling electromagnetic waves and information simultaneously by information metasurfaces is of central impor- tance in modern society. Intelligent metasurfaces are smart platfo...”。

### 011. Internet of Radars: Sensing versus Sending with Joint Radar-Communications
- 文件：`ref_papers/99_irrelevant_literature/Internet of Radars: Sensing versus Sending with Joint Radar-Communications.pdf`
- 原位置：`ref_papers/Internet of Radars: Sensing versus Sending with Joint Radar-Communications.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Abstract—The Internet of Things (IoT) are interconnected de- developments on system on chip structures, more and more arXiv:2002.00196v1 [eess.SP] 1 Feb 2020 vices for exchanging i...”。

### 012. JCR70: A Low-Complexity Millimeter-Wave Proof-of-Concept Platform for a Fully-Digital SIMO Joint Communication-Radar
- 文件：`ref_papers/99_irrelevant_literature/JCR70: A Low-Complexity Millimeter-Wave Proof-of-Concept Platform for a Fully-Digital SIMO Joint Communication-Radar.pdf`
- 原位置：`ref_papers/JCR70: A Low-Complexity Millimeter-Wave Proof-of-Concept Platform for a Fully-Digital SIMO Joint Communication-Radar.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“A fully-digital wideband joint communication-radar (JCR) with a single-input-multiple-output (SIMO) architecture at the millimeter-wave (mmWave) band will enable high joint communi...”。

### 013. Joint Localization and Environment Sensing by Harnessing NLOS Components in RIS-Aided mmWave Communication Systems
- 文件：`ref_papers/99_irrelevant_literature/Joint Localization and Environment Sensing by Harnessing NLOS Components in RIS-Aided mmWave Communication Systems.pdf`
- 原位置：`ref_papers/Joint Localization and Environment Sensing by Harnessing NLOS Components in RIS-Aided mmWave Communication Systems.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This study explores the use of non-line-of-sight (NLOS) components in millimeter-wave (mmWave) communication systems for joint localization and environment sensing. The radar cross...”。

### 014. Joint radar and communication: A survey
- 文件：`ref_papers/99_irrelevant_literature/Joint radar and communication: A survey.pdf`
- 原位置：`ref_papers/Joint radar and communication: A survey.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Joint radar and communication (JRC) networking through communication techniques to technology has become important for civil and obtain rapid fusion of large amount of detection da...”。

### 015. Millimeter-wave Foresight Sensing for Safety and Resilience in Autonomous Operations
- 文件：`ref_papers/99_irrelevant_literature/Millimeter-wave Foresight Sensing for Safety and Resilience in Autonomous Operations.pdf`
- 原位置：`ref_papers/Millimeter-wave Foresight Sensing for Safety and Resilience in Autonomous Operations.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Robotic platforms are highly programmable, century towards the necessary steps required for future scalable and versatile to complete several tasks including automation. The amalga...”。

### 016. Multi-functional Coexistence of Radar-Sensing and Communication Waveforms
- 文件：`ref_papers/99_irrelevant_literature/Multi-functional Coexistence of Radar-Sensing and Communication Waveforms.pdf`
- 原位置：`ref_papers/Multi-functional Coexistence of Radar-Sensing and Communication Waveforms.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Abstract—In this study, a novel transmission scheme is pro- posed to serve radar-sensing and communication objectives at the 𝑇" 𝑇# same time and allocated bandwidth. The proposed t...”。

### 017. Non-Orthogonal Multicarrier Waveform for Radar With Communications Systems: 24 GHz GFDM RadCom
- 文件：`ref_papers/99_irrelevant_literature/Non-Orthogonal Multicarrier Waveform for Radar With Communications Systems: 24 GHz GFDM RadCom.pdf`
- 原位置：`ref_papers/Non-Orthogonal Multicarrier Waveform for Radar With Communications Systems: 24 GHz GFDM RadCom.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, we propose the usage of Generalized Frequency Division Multiplexing (GFDM), a non-orthogonal multicarrier waveform for radar. We presented a novel method that cancel...”。

### 018. On the Integration of Enabling Wireless Technologies and Sensor Fusion for Next-Generation Connected and Autonomous Vehicles
- 文件：`ref_papers/99_irrelevant_literature/On the Integration of Enabling Wireless Technologies and Sensor Fusion for Next-Generation Connected and Autonomous Vehicles.pdf`
- 原位置：`ref_papers/On the Integration of Enabling Wireless Technologies and Sensor Fusion for Next-Generation Connected and Autonomous Vehicles.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The automotive industry is transitioning towards intelligent, connected, and autonomous vehicles to avoid traffic congestion, conflicts, and collisions with increased driver safety...”。

### 019. Optimum Waveform Selection for Target State Estimation in the Joint Radar-Communication System
- 文件：`ref_papers/99_irrelevant_literature/Optimum Waveform Selection for Target State Estimation in the Joint Radar-Communication System.pdf`
- 原位置：`ref_papers/Optimum Waveform Selection for Target State Estimation in the Joint Radar-Communication System.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The widespread usage of the Radio Frequency (RF) spectrum for wireless and mobile communication systems generated a significant spectrum scarcity. The Joint Radar-Communication Sys...”。

### 020. RETRACTED ARTICLE: Research and Simulation of Signal Processing and Recognition Based on Integrated Radar Communication System
- 文件：`ref_papers/99_irrelevant_literature/RETRACTED ARTICLE: Research and Simulation of Signal Processing and Recognition Based on Integrated Radar Communication System.pdf`
- 原位置：`ref_papers/RETRACTED ARTICLE: Research and Simulation of Signal Processing and Recognition Based on Integrated Radar Communication System.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The integrated radar communication system combines the functions of radar and communication systems. It has attracted wide attention because of its advantages in effectively reduci...”。

### 021. Radar2: Passive Spy Radar Detection and Localization Using COTS mmWave Radar
- 文件：`ref_papers/99_irrelevant_literature/Radar2: Passive Spy Radar Detection and Localization Using COTS mmWave Radar.pdf`
- 原位置：`ref_papers/Radar2: Passive Spy Radar Detection and Localization Using COTS mmWave Radar.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Millimeter-wave (mmWave) radars have found ap- also imperative to locate the radar(s) and act accordingly once plications in a wide range of domains, including human tracking, they...”。

### 022. Research of Target Detection and Classification Techniques Using Millimeter-Wave Radar and Vision Sensors
- 文件：`ref_papers/99_irrelevant_literature/Research of Target Detection and Classification Techniques Using Millimeter-Wave Radar and Vision Sensors.pdf`
- 原位置：`ref_papers/Research of Target Detection and Classification Techniques Using Millimeter-Wave Radar and Vision Sensors.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The development of autonomous vehicles and unmanned aerial vehicles has led to a current research focus on improving the environmental perception of automation equipment. The unman...”。

### 023. Sensor and Sensor Fusion Technology in Autonomous Vehicles: A Review
- 文件：`ref_papers/99_irrelevant_literature/Sensor and Sensor Fusion Technology in Autonomous Vehicles: A Review.pdf`
- 原位置：`ref_papers/Sensor and Sensor Fusion Technology in Autonomous Vehicles: A Review.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“With the significant advancement of sensor and communication technology and the reliable application of obstacle detection techniques and algorithms, automated driving is becoming...”。

### 024. Survey on 6G Frontiers: Trends, Applications, Requirements, Technologies and Future Research
- 文件：`ref_papers/99_irrelevant_literature/Survey on 6G Frontiers: Trends, Applications, Requirements, Technologies and Future Research.pdf`
- 原位置：`ref_papers/Survey on 6G Frontiers: Trends, Applications, Requirements, Technologies and Future Research.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Emerging applications such as Internet of Everything, Holographic Telepresence, collab- orative robots, and space and deep-sea tourism are already highlighting the limitations of e...”。

### 025. Toward Joint Radar, Communication, Computation, Localization, and Sensing in IoT
- 文件：`ref_papers/99_irrelevant_literature/Toward Joint Radar, Communication, Computation, Localization, and Sensing in IoT.pdf`
- 原位置：`ref_papers/Toward Joint Radar, Communication, Computation, Localization, and Sensing in IoT.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在通信感知一体化、车联网、6G、ISAC/RadCom 或自动驾驶雷达体系。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Since the 1960s, joint sensing and communication (JSAC) has been proposed as an attractive technique with advantages of enhanced spectral and hardware efficiency along with low lat...”。

### 026. Visual and Acoustic Data Analysis for the Bridge Deck Inspection Robotic System
- 文件：`ref_papers/99_irrelevant_literature/Visual and Acoustic Data Analysis for the Bridge Deck Inspection Robotic System.pdf`
- 原位置：`ref_papers/Visual and Acoustic Data Analysis for the Bridge Deck Inspection Robotic System.pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：通信/雷达波形或车载传感数据 -> 波束/资源/目标检测处理 -> 通信性能、感知定位或自动驾驶指标。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“is desirable. Automated multi-sensor NDE techniques Bridge deck inspection is essential task to monitor the have been proposed to meet the increasing demands health of the bridges....”。

### 027. Wireless safety monitoring of a water pipeline construction site using LoRa comm(1)
- 文件：`ref_papers/99_irrelevant_literature/Wireless safety monitoring of a water pipeline construction site using LoRa comm(1).pdf`
- 原位置：`ref_papers/Wireless safety monitoring of a water pipeline construction site using LoRa comm(1).pdf`
- 是否可作参考：无关-通信感知/车载雷达主线
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“. Despite efforts to reduce unexpected accidents at confined construction sites, choking accidents continue to occur. Because of the poorly ventilated atmosphere, particularly in l...”。


## 无关-应用场景偏离结构位移
### 001. A MINI REVIEW ON RADAR FUNDAMENTALS AND CONCEPT OF JAMMING
- 文件：`ref_papers/99_irrelevant_literature/A MINI REVIEW ON RADAR FUNDAMENTALS AND CONCEPT OF JAMMING.pdf`
- 原位置：`ref_papers/A MINI REVIEW ON RADAR FUNDAMENTALS AND CONCEPT OF JAMMING.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper presents a mini review on the basics of Radars. The parameters considered for determining the target location are explained in detail. Also the concept of Jamming and va...”。

### 002. A Radar-Enabled Collaborative Sensor Network Integrating COTS Technology for Surveillance and Tracking
- 文件：`ref_papers/99_irrelevant_literature/A Radar-Enabled Collaborative Sensor Network Integrating COTS Technology for Surveillance and Tracking.pdf`
- 原位置：`ref_papers/A Radar-Enabled Collaborative Sensor Network Integrating COTS Technology for Surveillance and Tracking.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“The feasibility of using Commercial Off-The-Shelf (COTS) sensor nodes is studied in a distributed network, aiming at dynamic surveillance and tracking of ground targets. Data acqui...”。

### 003. A low-noise photonic heterodyne synthesizer and its application to millimeter-wave radar
- 文件：`ref_papers/99_irrelevant_literature/A low-noise photonic heterodyne synthesizer and its application to millimeter-wave radar.pdf`
- 原位置：`ref_papers/A low-noise photonic heterodyne synthesizer and its application to millimeter-wave radar.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“ARTICLE https://doi.org/10.1038/s41467-021-24637-0 OPEN A low-noise photonic heterodyne synthesizer and its application to millimeter-wave radar Eric A. Kittlaus 1 ✉, Danny Eliyahu...”。

### 004. Application of Linear-Frequency-Modulated Continuous-Wave LFMCW Radars for Tracking of Vital Signs
- 文件：`ref_papers/99_irrelevant_literature/Application_of_Linear-Frequency-Modulated_Continuous-Wave_LFMCW_Radars_for_Tracking_of_Vital_Signs.pdf`
- 原位置：`ref_papers/Application_of_Linear-Frequency-Modulated_Continuous-Wave_LFMCW_Radars_for_Tracking_of_Vital_Signs.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper focuses on the exploitation of linear-fre- exploited to analyze the human gait or to classify helicopters quency-modulated continuous-wave (LFMCW) radars for [5]–[7]. no...”。

### 005. Automated Highway Pavement Management Systems From Inspection to Maintenance
- 文件：`ref_papers/99_irrelevant_literature/Automated Highway Pavement Management Systems From Inspection to Maintenance.pdf`
- 原位置：`ref_papers/Automated Highway Pavement Management Systems From Inspection to Maintenance.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Highway pavement assets require intensive management due to their large scale and deteriorating nature. Traditional pavement management depends on inspections using dedicated senso...”。

### 006. BlueFMCW: random frequency hopping radar for mitigation of interference and spoofing
- 文件：`ref_papers/99_irrelevant_literature/BlueFMCW: random frequency hopping radar for mitigation of interference and spoofing.pdf`
- 原位置：`ref_papers/BlueFMCW: random frequency hopping radar for mitigation of interference and spoofing.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“1 Department of Electrical Radars form a central piece in a variety of emerging applications requiring higher and Computer Engineering, University of Illinois at Urbana degrees of...”。

### 007. Classification of Targets Using Statistical Features from Range FFT of mmWave FMCW Radars
- 文件：`ref_papers/99_irrelevant_literature/Classification of Targets Using Statistical Features from Range FFT of mmWave FMCW Radars.pdf`
- 原位置：`ref_papers/Classification of Targets Using Statistical Features from Range FFT of mmWave FMCW Radars.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Radars with mmWave frequency modulated continuous wave (FMCW) technology accu- M.B.; Yalavarthy, P.K.; Kumar, A.; rately estimate the range and velocity of targets in their field o...”。

### 008. Contactless Stethoscope Enabled by Radar Technology
- 文件：`ref_papers/99_irrelevant_literature/Contactless Stethoscope Enabled by Radar Technology.pdf`
- 原位置：`ref_papers/Contactless Stethoscope Enabled by Radar Technology.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Contactless vital sign measurement technologies have the potential to greatly improve patient experiences and practitioner safety while creating the opportunity for comfortable con...”。

### 009. Detecting the Presence of Intrusive Drilling in Secure Transport Containers Using Non-Contact Millimeter-Wave Radar
- 文件：`ref_papers/99_irrelevant_literature/Detecting the Presence of Intrusive Drilling in Secure Transport Containers Using Non-Contact Millimeter-Wave Radar.pdf`
- 原位置：`ref_papers/Detecting the Presence of Intrusive Drilling in Secure Transport Containers Using Non-Contact Millimeter-Wave Radar.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“We employ a 77–81 GHz frequency-modulated continuous-wave (FMCW) millimeter-wave radar to sense anomalous vibrations during vehicle transport at highway speeds for the first time....”。

### 010. Doppler-Spectrum Feature-Based Human–Vehicle Classification Scheme Using Machine Learning for an FMCW Radar Sensor
- 文件：`ref_papers/99_irrelevant_literature/Doppler-Spectrum Feature-Based Human–Vehicle Classification Scheme Using Machine Learning for an FMCW Radar Sensor.pdf`
- 原位置：`ref_papers/Doppler-Spectrum Feature-Based Human–Vehicle Classification Scheme Using Machine Learning for an FMCW Radar Sensor.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, we propose a Doppler-spectrum feature-based human–vehicle classification scheme for an FMCW (frequency-modulated continuous wave) radar sensor. We introduce three no...”。

### 011. Highly efficient photonic radar by incorporating MDM-WDM and machine learning classifiers under adverse weather conditions
- 文件：`ref_papers/99_irrelevant_literature/Highly efficient photonic radar by incorporating MDM-WDM and machine learning classifiers under adverse weather conditions.pdf`
- 原位置：`ref_papers/Highly efficient photonic radar by incorporating MDM-WDM and machine learning classifiers under adverse weather conditions.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Photonic radar, a cornerstone in the innovative applications of microwave photonics, emerges as a pivotal technology for future Intelligent Transportation Systems (ITS). Offering O...”。

### 012. How Will Radar Be Integrated Into Daily Life mm-Wave Radar Architectures for Modern Daily Life Applications
- 文件：`ref_papers/99_irrelevant_literature/How_Will_Radar_Be_Integrated_Into_Daily_Life_mm-Wave_Radar_Architectures_for_Modern_Daily_Life_Applications.pdf`
- 原位置：`ref_papers/How_Will_Radar_Be_Integrated_Into_Daily_Life_mm-Wave_Radar_Architectures_for_Modern_Daily_Life_Applications.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“How Will Radar Be Integrated Into Daily Life? Wael Abdullah Ahmad and Xiang Yi A lthough the word ra dar is currently widely used as a stan- dard word in our daily lives, it is, in...”。

### 013. Implementation of a drive-by monitoring system for transport infrastructure utilising smartphone technology and GNSS
- 文件：`ref_papers/99_irrelevant_literature/Implementation of a drive-by monitoring system for transport infrastructure utilising smartphone technology and GNSS.pdf`
- 原位置：`ref_papers/Implementation of a drive-by monitoring system for transport infrastructure utilising smartphone technology and GNSS.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Ageing and deterioration of infrastructure are a...”。

### 014. Non-Contact Monitoring of Human Vital Signs Using FMCW Millimeter Wave Radar in the 120 GHz Band
- 文件：`ref_papers/99_irrelevant_literature/Non-Contact Monitoring of Human Vital Signs Using FMCW Millimeter Wave Radar in the 120 GHz Band.pdf`
- 原位置：`ref_papers/Non-Contact Monitoring of Human Vital Signs Using FMCW Millimeter Wave Radar in the 120 GHz Band.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“A non-contact heartbeat/respiratory rate monitoring system was designed using narrow beam millimeter wave radar. Equipped with a special low sidelobe and small-sized antenna lens a...”。

### 015. Screen-Printed Carbon Nanotube Polymer Composites For Impact Sensing InElectric Vehicle Batteries
- 文件：`ref_papers/99_irrelevant_literature/Screen-Printed Carbon Nanotube Polymer Composites For Impact Sensing InElectric Vehicle Batteries.pdf`
- 原位置：`ref_papers/Screen-Printed Carbon Nanotube Polymer Composites For Impact Sensing InElectric Vehicle Batteries.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Under-floor impacts are a major cause of thermal-runaway in EV battery packs, yet existing metal or MEMS sensors are heavy, costly, and cover only limited areas, leaving significan...”。

### 016. Signal Identification and Entrainment for Practical FMCW Radar Spoofing Attacks
- 文件：`ref_papers/99_irrelevant_literature/Signal Identification and Entrainment for Practical FMCW Radar Spoofing Attacks.pdf`
- 原位置：`ref_papers/Signal Identification and Entrainment for Practical FMCW Radar Spoofing Attacks.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper proposes a method of passively esti- chirp slopes in the 10s of MHz/µs, these radars only sample arXiv:2307.11072v1 [eess.SP] 20 Jul 2023 mating the parameters of freque...”。

### 017. Study on Multi-Heterogeneous Sensor Data Fusion Method Based on Millimeter-Wave Radar and Camera
- 文件：`ref_papers/99_irrelevant_literature/Study on Multi-Heterogeneous Sensor Data Fusion Method Based on Millimeter-Wave Radar and Camera.pdf`
- 原位置：`ref_papers/Study on Multi-Heterogeneous Sensor Data Fusion Method Based on Millimeter-Wave Radar and Camera.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：利用多传感器融合弥补单一传感器的低频漂移、遮挡、采样或部署限制。
- 方法论/数据处理流：多源传感数据同步 -> 去噪/积分/特征提取 -> 滤波、回归或互补融合 -> 位移/加速度/结构状态估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This study presents a novel multimodal heterogeneous perception cross-fusion framework for intelligent vehicles that combines data from millimeter-wave radar and camera to enhance...”。

### 018. 基于多传感器融合的交通场景三维目标检测方法研究
- 文件：`ref_papers/99_irrelevant_literature/基于多传感器融合的交通场景三维目标检测方法研究.pdf`
- 原位置：`ref_papers/基于多传感器融合的交通场景三维目标检测方法研究.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“中圈料孽艘求 爨、灌 Ｕｎｉｖｅｒｓｉｔｙ ｏｆ Ｓｃｉｅｎｃｅ ａｎｄ Ｔｅｃｈｎｏｌｏｇｙ 麟 。魅 ■Ｉ ， ｌ Ｉ ／一 ● ／１ ＼／， ｊ＜． ｖ，－ ／１ 气／ Ｉ＿＿－ ｌ●－ Ｉ．ｒ ‘ 、 Ｊ ｆ、－＿ ＿－、 论文题目 基于多传感器融合的交通场景三维 目标检测方法研究 作者姓名 李矗 学科专业 计算机科学与技术 导师姓名 袭．孝啄放籀...”。

### 019. 基于多源信息融合的列车状态估计方法研究
- 文件：`ref_papers/99_irrelevant_literature/基于多源信息融合的列车状态估计方法研究.pdf`
- 原位置：`ref_papers/基于多源信息融合的列车状态估计方法研究.pdf`
- 是否可作参考：无关-应用场景偏离结构位移
- 创新：创新集中在人体生命体征、目标分类、安防检测、交通场景或其他应用任务。
- 方法论/数据处理流：特定应用传感数据 -> 特征提取/分类/检测/估计 -> 输出生命体征、类别、安防或交通目标状态。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“万方数据 独创性声明 本人所呈交的学位论文是在导师指导下进行的研究 工 作及取得的成果。尽我所知 ， 除特别加以标泣的地方外，论文 中 不包含其他人的研究成果 。 与我 一 同工作的同志对 本 文的研究 工 作和成果的任何贡献均已在论文中作了明确的说明并己致谢 。 本论文及其相关资料若有不实之处，由本人承担 一 切相关责任 论文作者签名:金永萍 νP 年 l...”。


## 无关-主题过宽或偏离当前实验链路
### 001. Automotive Radar — From First Efforts to Future Systems
- 文件：`ref_papers/99_irrelevant_literature/Automotive Radar — From First Efforts to Future Systems.pdf`
- 原位置：`ref_papers/Automotive Radar — From First Efforts to Future Systems.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Although the beginning of research on automotive radar sensors goes back to the 1960s, automotive radar has remained one of the main drivers of innovation in millimeter wave techno...”。

### 002. Closing the gap towards super-long suspension bridges using computational morphogenesis
- 文件：`ref_papers/99_irrelevant_literature/Closing the gap towards super-long suspension bridges using computational morphogenesis.pdf`
- 原位置：`ref_papers/Closing the gap towards super-long suspension bridges using computational morphogenesis.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“ARTICLE https://doi.org/10.1038/s41467-020-16599-6 OPEN Closing the gap towards super-long suspension bridges using computational morphogenesis Mads Baandrup 1,2 ✉, Ole Sigmund 3,...”。

### 003. Driven by Data or Derived Through Physics? A Review of Hybrid Physics Guided Machine Learning Techniques With Cyber-Physical System (CPS) Focus
- 文件：`ref_papers/99_irrelevant_literature/Driven by Data or Derived Through Physics? A Review of Hybrid Physics Guided Machine Learning Techniques With Cyber-Physical System (CPS) Focus.pdf`
- 原位置：`ref_papers/Driven by Data or Derived Through Physics? A Review of Hybrid Physics Guided Machine Learning Techniques With Cyber-Physical System (CPS) Focus.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“A multitude of cyber-physical system (CPS) applications, including design, control, diagnosis, prognostics, and a host of other problems, are predicated on the assumption of model...”。

### 004. Investigation of Frequency-Domain Dimension Reduction for A2M-Based Bridge Damage Detection Using Accelerations of Moving Vehicles
- 文件：`ref_papers/99_irrelevant_literature/Investigation of Frequency-Domain Dimension Reduction for A2M-Based Bridge Damage Detection Using Accelerations of Moving Vehicles.pdf`
- 原位置：`ref_papers/Investigation of Frequency-Domain Dimension Reduction for A2M-Based Bridge Damage Detection Using Accelerations of Moving Vehicles.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“Recent decades have witnessed a rise in interest in bridge health monitoring utilizing the vibrations of passing vehicles. However, existing studies commonly rely on constant speed...”。

### 005. Linear Discriminant Analysis-Based Motion Classification Using Distributed Micro-Doppler Radars with Limited Backhaul
- 文件：`ref_papers/99_irrelevant_literature/Linear Discriminant Analysis-Based Motion Classification Using Distributed Micro-Doppler Radars with Limited Backhaul.pdf`
- 原位置：`ref_papers/Linear Discriminant Analysis-Based Motion Classification Using Distributed Micro-Doppler Radars with Limited Backhaul.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：FMCW IF/复回波 -> range bin 或目标峰提取 -> 相位/IQ/干涉处理 -> 解缠或补偿 -> 距离/位移/振动估计。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“In this paper, we propose a cooperative linear discriminant analysis (LDA)-based motion classification algorithm for distributed micro-Doppler (MD) radars which are connected to a...”。

### 006. Multifunctional Integrated Sensors for Multiparameter Monitoring Applications
- 文件：`ref_papers/99_irrelevant_literature/Multifunctional_Integrated_Sensors_for_Multiparameter_Monitoring_Applications.pdf`
- 原位置：`ref_papers/Multifunctional_Integrated_Sensors_for_Multiparameter_Monitoring_Applications.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：创新点与当前主线联系较弱，更多体现为某一传感器、工程场景或泛化算法的背景性改进。
- 方法论/数据处理流：数据处理流与本文的雷达 IQ、静止参考 target 选择和结构位移恢复链路不直接对应。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“We present multifunctional integrated sensors could deploy to measure acoustic, seismic, magnetic, and (MFISES) that combine temperature, humidity, pressure, air weather events [3]...”。

### 007. Research of the Vibration Source Tracking in Phase-Sensitive Optical Time-Domain Reflectometry Signals Based by Image Processing Method
- 文件：`ref_papers/99_irrelevant_literature/Research of the Vibration Source Tracking in Phase-Sensitive Optical Time-Domain Reflectometry Signals Based by Image Processing Method.pdf`
- 原位置：`ref_papers/Research of the Vibration Source Tracking in Phase-Sensitive Optical Time-Domain Reflectometry Signals Based by Image Processing Method.pdf`
- 是否可作参考：无关-主题过宽或偏离当前实验链路
- 创新：从视觉、LiDAR 或激光侧提供非接触结构位移测量对照，强调固定参考、光照、视角和全场测量问题。
- 方法论/数据处理流：图像/点云序列 -> 特征/目标/参考点检测 -> 帧间匹配或三维优化 -> 像素/点云位移换算 -> 结构位移。
- 与本文关系：当前 thesis 不建议引用；已整理到无关文献文件夹，仅作为以后改题或扩展时的备查材料。
- 摘要判断依据：摘要/首页显示主题约为“This paper aims to improve the source tracking efficiency of distributed vibration signals generated by phase-sensitive optical time-domain reflectometry (Φ-OTDR). Considering the...”。
