# packet_3 方法模块卡片（2010+雷达候选）

只收录已有摘要或可核验 Crossref 摘要支持具体处理链的 `module` 记录。题名-only 疑似方法保留在 decisions 中为 `pending`，不将题名关键词当作算法证据。

### R0015｜Theory and method of multi-point synchronous deformation and vibration measurement based on millimeter-wave sensing
- DOI：10.1360/sst-2020-0489
- 证据：abstract；摘要：multi-target baseband signal model；multi-point synchronous vibration/displacement extraction；laser comparison。
- 输入→算法→输出：FMCW基带多目标回波→多目标距离分离与位移提取→多点同步振动输出
- 已有基础/论文增量：摘要给出多目标基带模型和多点同步位移提取，属于多目标/全场测量链。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M01, M09, M15

### R0024｜Non-contact Monitoring of Fatigue Driving Using FMCW Millimeter Wave Radar
- DOI：10.1145/3614442
- 证据：abstract；摘要方法证据：In our study, fatigue actions were collected first, and then the different micro-Doppler characteristics produced by human activity were used to classify and recognize the fatigue action using the fine-tuning convolution neural network (FT-CNN) model.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In our study, fatigue actions were collected first, and then the different micro-Doppler characteristics produced by human activity were used to classify and recognize the fatigue action using the fine-tuning convolution neural network (FT-CNN) model.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0027｜Millimeter-Wave Radar-Based Identity Recognition Algorithm Built on Multimodal Fusion
- DOI：10.3390/s24134051
- 证据：abstract；摘要方法证据：Existing identification algorithms mainly rely on a single signal, such as breathing or heartbeat.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Existing identification algorithms mainly rely on a single signal, such as breathing or heartbeat.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M19）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M19

### R0030｜Vibrometry and Sound Reproduction of Acoustic Sources on Moving Platforms Using Millimeter Wave Pulse-Doppler Radar
- DOI：10.1109/access.2020.2971522
- 证据：abstract；摘要：hierarchical direct/indirect motion compensation；fast/slow time；range disambiguation；stretch processing。
- 输入→算法→输出：脉冲Doppler快慢时间回波→分层运动补偿/距离分辨→复基带振动与声学特征
- 已有基础/论文增量：摘要明确使用分层运动补偿、快慢时间参数估计、宽带距离分辨和stretch processing恢复振动。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M02, M05, M07, M09

### R0033｜Detecting the Presence of Intrusive Drilling in Secure Transport Containers Using Non-Contact Millimeter-Wave Radar
- DOI：10.3390/s22072718
- 证据：abstract；摘要方法证据：With the millimeter-wave radar monitoring the microdoppler signature of the container's vibrating walls, we create a novel signal-processing pipeline consisting of range-angle tracking, time-frequency analysis, horizontal stripe image convolution, and principal component analysis to create a robust and powerful detection statistic to alarm if drilling is present.
- 输入→算法→输出：雷达原始回波/慢时间IQ→With the millimeter-wave radar monitoring the microdoppler signature of the container's vibrating walls, we create a novel signal-processing pipeline consisting of range-angle tracking, time-frequency analysis, horizontal stripe image convolution, and principal component analysis to create a robust and powerful detection statistic to alarm if drilling is present.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16,M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16, M18

### R0045｜Spatially Resolved Fast-Time Vibrometry Using Ultrawideband FMCW Radar Systems
- DOI：10.1109/tmtt.2020.3038080
- 证据：abstract；摘要给出fast-time FMCW振动链、瞬时相位、空间分辨多目标和标定。
- 输入→算法→输出：ADC/IF→fast-time range bin与瞬时相位→误差模型/标定→多目标振动位移输出
- 已有基础/论文增量：摘要：fast-time instantaneous phase；error model and calibration；multiple simultaneously vibrating targets；最高至少16 kHz、最低30 nm。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M01, M03, M05, M07, M09

### R0051｜Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View
- DOI：10.34133/2021/9787484
- 证据：abstract；摘要：interferometric phase evolution tracking from range-angle joint dimension; full-field localization; clutter elimination。
- 输入→算法→输出：range-angle回波→相位演化跟踪+全视场定位/杂波消除→多目标微动
- 已有基础/论文增量：摘要明确range-angle联合相位演化跟踪、全视场定位和杂波消除，是多目标/几何/杂波模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M09, M14, M15, M18

### R0057｜A study of millimeter-wave communication in remote biomechanical monitoring
- DOI：10.62617/mcb1747
- 证据：abstract；摘要：STFT, Doppler analysis and deep learning for multi-parameter fusion。
- 输入→算法→输出：毫米波回波→STFT/Doppler+多参数融合→运动/心率/呼吸特征
- 已有基础/论文增量：摘要明确STFT、Doppler分析和深度学习融合多参数生物力学监测，算法可迁移时频链。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M16, M19

### R0063｜Multi-Subject Remote Heart Sound Monitoring Using mmWave MIMO RADAR
- DOI：10.1109/jmw.2025.3579668
- 证据：abstract；摘要方法证据：This work presents a novel non-contact heart sound monitoring approach using millimeter-wave RADAR technology.
- 输入→算法→输出：mmWave MIMO回波→自动目标定位+空间波束形成→多主体心音时频输出
- 已有基础/论文增量：摘要明确给出自动主体检测/定位、空间beamforming和时频心音分析。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M11, M15, M16

### R0066｜Human Radar Cross Section Measurements in a Bio-Radar Scenario Using a 5.8-GHz Continuous-Wave Radar
- DOI：10.1109/tim.2025.3633365
- 证据：abstract；摘要方法证据：Bio-Radar (BR) systems measure physiological activity by using the micro-Doppler effect to detect signal reflections from the human body.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Bio-Radar (BR) systems measure physiological activity by using the micro-Doppler effect to detect signal reflections from the human body.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0078｜A Novel Scheme of High-Precision Heart Rate Detection With a mm-Wave FMCW Radar
- DOI：10.1109/access.2023.3303335
- 证据：abstract；摘要方法证据：This research proposes a novel processing scheme to improve the accuracy and stability of non-contact heart rate detection.
- 输入→算法→输出：FMCW range bin→方差选择→相位平滑/匹配滤波→VME提取心跳
- 已有基础/论文增量：摘要明确range-bin选择、相位spline、matched filter和VME。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M01, M05, M08, M17

### R0102｜Contactless Real-Time Heartbeat Detection via 24 GHz Continuous-Wave Doppler Radar Using Artificial Neural Networks
- DOI：10.3390/s20082351
- 证据：abstract；摘要方法证据：Among the possible ways to wirelessly obtain information related to heart activity, methods based on mm-wave radars proved to be the most accurate in detecting the small mechanical oscillations of the human chest resulting from heartbeats.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Among the possible ways to wirelessly obtain information related to heart activity, methods based on mm-wave radars proved to be the most accurate in detecting the small mechanical oscillations of the human chest resulting from heartbeats.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0105｜Laser Remote Sensing of Seismic Wave with Sub-Millimeter Scale Amplitude Based on Doppler Characteristics Extracted from Wavefront Sensor
- DOI：10.3390/photonics11030204
- 证据：abstract；摘要方法证据：This article shows a Doppler model for laser remote sensing of seismic waves based on a wavefront sensor.
- 输入→算法→输出：雷达原始回波/慢时间IQ→This article shows a Doppler model for laser remote sensing of seismic waves based on a wavefront sensor.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0111｜Nondestructive Evaluation of Localized Rebar Corrosion in Concrete Using Vibro-Radar Based on Pulse Doppler Imaging
- DOI：10.3390/rs14184645
- 证据：abstract；摘要方法证据：Early nondestructive inspection of rebar corrosion in reinforced concrete structures is important, but a practical, accurate, high-speed, and high-resolution method has not yet been proposed.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Early nondestructive inspection of rebar corrosion in reinforced concrete structures is important, but a practical, accurate, high-speed, and high-resolution method has not yet been proposed.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0117｜The Effect of Multi-Directional on Remote Heart Rate Measurement Using PA-LI Joint ICEEMDAN Method with mm-Wave FMCW Radar
- DOI：10.1587/transcom.2021cep0014
- 证据：abstract；摘要方法证据：Heart rate measurement for mm-wave FMCW radar based on phase analysis comprises a variety of noise.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Heart rate measurement for mm-wave FMCW radar based on phase analysis comprises a variety of noise.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M17）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M17

### R0126｜Methods for Doppler Radar Monitoring of Physiological Signals
- DOI：无 DOI
- 证据：abstract；摘要方法证据：The aim of this thesis was to develop methods for monitoring cardiac and respiratory activity with microwave continuous wave (CW) Doppler radar.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The aim of this thesis was to develop methods for monitoring cardiac and respiratory activity with microwave continuous wave (CW) Doppler radar.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0129｜A remaining useful life estimation method for solenoid valve based on mmWave radar and auxiliary particle filter technique
- DOI：10.1587/elex.18.20210344
- 证据：abstract；摘要方法证据：Solenoid valves(SVs) as a kernel component are widely used in various control systems.Through accurately predicting the remaining useful life (RUL) of the SV, predictable maintenance its can be implemented to reduce system maintenance costs and system reliability improves.This paper proposes a frequency modulated continuous wave (FMCW) based on millimeter-wave radar and the auxiliary particle filter (APF) technique t
- 输入→算法→输出：雷达原始回波/慢时间IQ→Solenoid valves(SVs) as a kernel component are widely used in various control systems.Through accurately predicting the remaining useful life (RUL) of the SV, predictable maintenance its can be implemented to reduce system maintenance costs and system reliability improves.This paper proposes a frequency modulated continuous wave (FMCW) based on millimeter-wave radar and the auxiliary particle filter (APF) technique t→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M18

### R0135｜Through-Wall Multi-Subject Localization and Vital Signs Monitoring Using UWB MIMO Imaging Radar
- DOI：10.3390/rs13152905
- 证据：abstract；摘要方法证据：We also apply the three-dimensional (3-D) higher-order cumulant (HOC) to locate multiple subjects and extract the phase sequence of the radar images as the vital signs signal.
- 输入→算法→输出：UWB MIMO/SFCW成像→HOC多主体定位+相位序列提取→多主体生命体征
- 已有基础/论文增量：摘要明确MIMO成像、HOC定位及多主体相位序列提取。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M11, M12, M15, M16

### R0162｜Bridge Dynamic Cable-Tension Estimation with Interferometric Radar and APES-Based Time-Frequency Analysis
- DOI：10.3390/electronics10040501
- 证据：abstract；摘要：APES-based time-frequency analysis；overlapped short sections；string-vibration equation。
- 输入→算法→输出：干涉雷达多索位移→APES短时高分辨时频→基频/弦振动方程→索力
- 已有基础/论文增量：摘要明确以APES时频分析短时位移段并由弦振动方程反推多根索力。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M15, M16

### R0171｜Experimental validation of spaceborne SAR for measurement of structural vibrations
- DOI：10.58286/33941
- 证据：abstract；摘要方法证据：The alternative presented here is micro-Doppler SAR (MDSAR), which measures motion using a single SAR image and can achieve the sampling rates required, providing a complement to conventional SHM approaches.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The alternative presented here is micro-Doppler SAR (MDSAR), which measures motion using a single SAR image and can achieve the sampling rates required, providing a complement to conventional SHM approaches.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0174｜High Accuracy Motion Detection Algorithm via ISM Band FMCW Radar
- DOI：10.3390/rs14010058
- 证据：abstract；摘要方法证据：The conventional frequency modulated continuous wave (FMCW) radar accuracy range detection algorithm is based on the frequency estimation and additional phase evaluation which contains Fourier transform and frequency refining analysis in each chirp, so it has the disadvantages of being computationally expensive, and not being suitable for real-time motion measurement.
- 输入→算法→输出：FMCW beat FFT→椭圆近似相位校正/DC偏置抑制→位移
- 已有基础/论文增量：摘要明确频谱泄漏相位修正、椭圆近似和静态物体DC偏置滤除。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M01, M03, M05, M08

### R0183｜Monitoring Bridge Vibrations Based on GBSAR and Validation by High-Rate GPS Measurements
- DOI：10.1109/jstars.2021.3083494
- 证据：abstract；摘要明确提出最小二乘调整与triangular-chain处理高频噪声/大气相位。
- 输入→算法→输出：GBSAR相位序列→大气相消/最小二乘triangular-chain去噪→位移精度评估
- 已有基础/论文增量：摘要：denoising based on least-squares adjustment and a triangular chain；永久散射点精度5–6 mm。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M06, M08, M20

### R0192｜Micro-Doppler measurement of insect wing-beat frequencies with W-band coherent radar
- DOI：10.1038/s41598-017-01616-4
- 证据：abstract；摘要方法证据：Principally, the radar echo signal can be used to extract wingbeat information, because both the signal amplitude and phase could be modulated by wing-beating.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Principally, the radar echo signal can be used to extract wingbeat information, because both the signal amplitude and phase could be modulated by wing-beating.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16

### R0195｜A 77-GHz Six-Port Sensor for Accurate Near-Field Displacement and Doppler Measurements
- DOI：10.3390/s18082565
- 证据：abstract；摘要方法证据：A continuous-wave (CW) radar sensor design based on a millimetre-wave six-port interferometer is proposed.
- 输入→算法→输出：77GHz六端口CW复数回波→I/Q/相位测量+Doppler→距离与速度
- 已有基础/论文增量：摘要明确six-port准确相位、距离和Doppler测量。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M03, M05

### R0201｜Robust Vibration Displacement Extraction for FMCW Radar by Incorporating Optimized Beat Frequency and Maximum Likelihood Estimation
- DOI：10.1109/jsen.2025.3569403
- 证据：abstract；摘要明确提出beat优化与MLE相位序列的稳健位移提取。
- 输入→算法→输出：FMCW IF→Nelder–Mead beat频率优化→跨sweep MLE相位→振动位移
- 已有基础/论文增量：摘要：optimized beat frequency + maximum likelihood estimation；beat误差0.0087 Hz；相位RMSE改善。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M01, M05, M20

### R0204｜Target Range Selection of FMCW Radar for Accurate Vital Information Extraction
- DOI：10.1109/access.2020.3043013
- 证据：abstract；摘要方法证据：In this paper, an effective method for selecting the range bin with accurate vital information is proposed.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In this paper, an effective method for selecting the range bin with accurate vital information is proposed.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M01,M09）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M01, M09

### R0207｜High-Efficiency Super-Resolution FMCW Radar Algorithm Based on FFT Estimation
- DOI：10.3390/s21124018
- 证据：abstract；摘要给出FFT粗估后MUSIC超分辨，属于距离/超分辨处理链。
- 输入→算法→输出：FMCW快时间→FFT粗距离→按距离裁剪样本→MUSIC超分辨参数
- 已有基础/论文增量：摘要：FFT粗估距离后将缩短样本输入MUSIC；复杂度平均降低88%。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M01, M12

### R0216｜Estimation of Compression Depth During CPR Using FMCW Radar with Deep Convolutional Neural Network
- DOI：10.3390/s25195947
- 证据：abstract；摘要：This study introduces a method using frequency-modulated continuous-wave (FMCW) radar to remotely and accurately monitor chest compressions.
- 输入→算法→输出：FMCW微动/呼吸回波→时频/深度模型→CPR压深估计
- 已有基础/论文增量：摘要说明由FMCW雷达估计胸部压深，微动时频特征可迁移。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：可作为场景背景；不能据此声称算法首创。
- 模块：M02, M16

### R0225｜Efficient Implementation for SBL-Based Coherent Distributed mmWave Radar Imaging
- DOI：10.3390/rs15041054
- 证据：abstract；摘要方法证据：In a distributed frequency-modulated continuous waveform (FMCW) radar system, the echo data collected are not continuous in the azimuth direction, so the imaging effect of the traditional range-Doppler (RD) algorithm is poor.
- 输入→算法→输出：FMCW分布式回波→range-Doppler与快速SBL→高角分辨成像
- 已有基础/论文增量：摘要明确SBL、TBT矩阵快速实现和range-Doppler成像。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M01, M02, M13

### R0234｜Advancing Ground-Based Radar Processing for Bridge Infrastructure Monitoring
- DOI：10.3390/s21062172
- 证据：abstract；摘要明确列出外部影响剔除、三维分解和不确定度。
- 输入→算法→输出：多雷达LOS→动态扰动/静态杂波/大气剔除→LOS到3D分解→不确定度
- 已有基础/论文增量：摘要：remove moving-object/static-clutter/atmospheric influences；decompose LOS into 3D；uncertainty <0.1 mm。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M08, M14, M20

### R0243｜Environment-aware Multi-person Tracking in Indoor Environments with MmWave Radars
- DOI：10.1145/3610902
- 证据：abstract；摘要方法证据：Device-free indoor localization and tracking using commercial millimeter wave radars have attracted much interest lately due to their non-intrusive nature and high spatial resolution.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Device-free indoor localization and tracking using commercial millimeter wave radars have attracted much interest lately due to their non-intrusive nature and high spatial resolution.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M18

### R0255｜Smart Spread Spectrum Modulated Tags for Detection of Vulnerable Road Users with Automotive Radar
- DOI：10.3390/s23052730
- 证据：abstract；摘要方法证据：Since the speed of these users is usually low, they can be confused with clutter due to the presence of large objects.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Since the speed of these users is usually low, they can be confused with clutter due to the presence of large objects.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M08）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M08

### R0264｜Interference Mitigation Method for Millimeter-Wave Frequency-Modulation Continuous-Wave Radar Based on Outlier Detection and Variational Modal Decomposition
- DOI：10.3390/rs15143654
- 证据：abstract；摘要方法证据：Aiming at the problem of mutual interference between millimeter-wave frequency-modulation continuous-wave (FMCW) radars, an interference mitigation method based on outlier detection and variational mode decomposition (VMD) is proposed in this paper.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Aiming at the problem of mutual interference between millimeter-wave frequency-modulation continuous-wave (FMCW) radars, an interference mitigation method based on outlier detection and variational mode decomposition (VMD) is proposed in this paper.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M08,M17）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M08, M17

### R0267｜Real-time detection and management of rockfall hazards by ground-based Doppler radar
- DOI：10.1007/s10346-023-02144-1
- 证据：abstract；摘要方法证据：Here, we describe the field application of a ground-based Doppler radar that performs real-time, long-range, wide-area detection and tracking of rockfalls and related slope hazards.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Here, we describe the field application of a ground-based Doppler radar that performs real-time, long-range, wide-area detection and tracking of rockfalls and related slope hazards.→结构振动/位移或频率输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16,M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M02, M16, M18

### R0273｜Advances in object detection for autonomous driving using mmwave radar and camera: A comprehensive survey
- DOI：10.1007/s44443-025-00302-0
- 证据：abstract；摘要方法证据：This paper aims to offer a comprehensive guide for radar-camera fusion, focusing on the object detection task.
- 输入→算法→输出：雷达原始回波/慢时间IQ→This paper aims to offer a comprehensive guide for radar-camera fusion, focusing on the object detection task.→目标/生理/运动特征输出
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M19）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M19

### R0300｜SPECal: Spatial Calibration Based on Self-Pose-Estimation Between mmWave Radar and Camera
- DOI：10.1145/3749456
- 证据：abstract；摘要方法证据：In this paper, we propose SPECal to perform spatial calibration between mmWave radars and cameras mounted on a moving platform.
- 输入→算法→输出：mmWave雷达+相机→自姿态/空间标定→共定位观测
- 已有基础/论文增量：摘要/题名明确SPECal空间标定和雷达-相机自姿态估计。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景仅迁移处理思想。
- 模块：M14, M20

### R0324｜A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring
- DOI：10.1016/j.ymssp.2025.112777
- 证据：abstract；摘要明确提出Doppler辅助迭代相位解缠。
- 输入→算法→输出：wrapped相位→Doppler增量→迭代phase unwrap→径向位移
- 已有基础/论文增量：摘要：iterative phase unwrapping based on estimated Doppler；解决每采样超过λ/4的wrap。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M06

### R0333｜Calibration Method for Large-Aperture Antenna Surface Measurement Based on Spatial Ranging Correction
- DOI：10.3390/s26010312
- 证据：abstract；摘要方法证据：To address the accuracy calibration issue of the high-precision FMCW laser scanning measurement system for the large-aperture antenna of the Fengyun-4 microwave sounding satellite in orbit, this paper proposes a system calibration method based on space ranging correction.
- 输入→算法→输出：雷达原始回波/慢时间IQ→To address the accuracy calibration issue of the high-precision FMCW laser scanning measurement system for the large-aperture antenna of the Fengyun-4 microwave sounding satellite in orbit, this paper proposes a system calibration method based on space ranging correction.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M15,M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M15, M20

### R0336｜M‐sequence‐based ultra‐wideband sensor network for vitality monitoring of elders at home
- DOI：10.1049/iet-rsn.2014.0214
- 证据：abstract；摘要：UWB radio sensor network; localization, breathing motion, fall detection and gait features。
- 输入→算法→输出：UWB M-sequence多点回波→定位/运动跟踪→生命体征与步态
- 已有基础/论文增量：摘要明确6–8.5 GHz UWB M-sequence雷达网络的定位、呼吸运动、跌倒和步态跟踪。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M09, M15, M18

### R0339｜Fault Diagnosis of the Autonomous Driving Perception System Based on Information Fusion
- DOI：10.3390/s23115110
- 证据：abstract；摘要：map MMW radar points onto camera ROI; spatiotemporal fusion。
- 输入→算法→输出：MMW点云+相机→空间/时间映射与融合→感知故障诊断
- 已有基础/论文增量：摘要明确毫米波雷达点映射到相机图像并做时空融合辅助故障诊断，属于跨传感标定/融合。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M14, M19, M20

### R0342｜A W-Band 3-D Integrated Mini-SAR System With High Imaging Resolution on UAV Platform
- DOI：10.1109/access.2020.3003273
- 证据：abstract；摘要：compact W-band Mini-SAR; high-linearity waveform; motion compensation and imaging。
- 输入→算法→输出：W-band SAR原始回波→波形/运动补偿与成像→高分辨图像
- 已有基础/论文增量：摘要明确W-band UAV Mini-SAR系统、波形/运动补偿和高分辨成像链，属于雷达成像入口模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M01, M15

### R0345｜Signal processing for abnormalities estimation analysis
- DOI：10.11591/ijaas.v13.i3.pp600-610
- 证据：abstract；摘要方法证据：This is due to ineffective signal clutter removal and body movement removal algorithms for collecting accurate breathing signals.
- 输入→算法→输出：雷达原始回波/慢时间IQ→This is due to ineffective signal clutter removal and body movement removal algorithms for collecting accurate breathing signals.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M08）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M08

### R0348｜SAR Multi-Angle Observation Method for Multipath Suppression in Enclosed Spaces
- DOI：10.3390/rs16040621
- 证据：abstract；摘要：multi-angle observation; center-vector-distance multipath suppression。
- 输入→算法→输出：多角度SAR图像→中心向量距离/多径鬼影抑制→增强目标图像
- 已有基础/论文增量：摘要明确多角度SAR观测和中心向量距离算法抑制封闭空间多径鬼影。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M15

### R0360｜Radar Interferometry Using gNB Base Stations: Estimation and Compensation of Mast Motion and Atmospheric Effects
- DOI：10.3390/s26010151
- 证据：abstract；摘要方法证据：A technique for estimating radar movements based on the displacement tracking of multiple permanent scatterers (PSs) in the scenario is presented.
- 输入→算法→输出：多永久散射体位移跟踪→线性回归估计桅杆运动/大气→真实目标位移
- 已有基础/论文增量：摘要明确PS跟踪、固定PS线性回归和支撑运动/大气补偿。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需要按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景算法只能迁移处理思想，不能直接复用参数。
- 模块：M08, M14, M18, M20

### R0366｜Multi-Monostatic Interferometric Radar for Bridge Monitoring
- DOI：10.3390/electronics10030247
- 证据：abstract；摘要：two independent displacement components from multi-monostatic MIMO interferometric radar with transponder。
- 输入→算法→输出：多单站MIMO干涉回波→两条独立LOS分量→二维位移向量
- 已有基础/论文增量：摘要提出多单站/MIMO干涉雷达和转发器，同时获取两个独立位移分量，属于LOS几何扩展。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M14

### R0369｜Multi-Monostatic Interferometric Radar with Radar Link for Bridge Monitoring
- DOI：10.3390/electronics10222777
- 证据：abstract；摘要：radio-linked transponder enables second displacement component。
- 输入→算法→输出：雷达+无线转发器双通道→多LOS相位→二维位移分量
- 已有基础/论文增量：摘要提出带无线链路的多单站干涉雷达，通过远置转发器取得第二位移分量。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M14

### R0372｜3D Vibration Estimation from Ground-Based Radar
- DOI：10.3390/rs10111670
- 证据：abstract；摘要：calibrators remove tropospheric turbulence/radial motion；fixed-target interference compensation；2D/3D deformation。
- 输入→算法→输出：同步雷达相位→校准器大气/径向运动补偿+固定目标干扰抑制→2D/3D变形场
- 已有基础/论文增量：摘要明确用校准器消除大气湍流/径向运动并抑制固定目标干扰，再估计2D/3D变形场。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M08, M14, M20

### R0381｜Long-Term Dynamic Monitoring for Structural Health Assessment of Bisantis Bridge
- DOI：10.1016/j.prostr.2026.06.054
- 证据：abstract；摘要方法证据：Two models were created: one focusing on the main arch, and a full model including the deck and piers.
- 输入→算法→输出：雷达OMA+三轴加速度→频率/模态/位移→长期结构状态
- 已有基础/论文增量：摘要明确雷达OMA与无线三轴加速度计联合获取频率、模态和位移。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需要按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景算法只能迁移处理思想，不能直接复用参数。
- 模块：M16, M19

### R0384｜DEM-Assisted 3-D Reconstruction of Aletsch Glacier Displacements Using Monostatic and Bistatic Differential Interferometry
- DOI：10.1109/tgrs.2025.3586272
- 证据：abstract；摘要方法证据：This study presents a set of differential interferometric observations retrieved in Aletsch glacier during a winter campaign in March 2022, using KAPRI, a Ku-Band a ground-based radar interferometer.
- 输入→算法→输出：单/双基地干涉LOS→DEM辅助3D向量重建→冰川位移场
- 已有基础/论文增量：摘要明确双基地额外LOS和DEM辅助三维位移重建。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需要按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景算法只能迁移处理思想，不能直接复用参数。
- 模块：M14, M20

### R0387｜Determining and Investigating the Variability of Bridges’ Natural Frequencies with Ground-Based Radar
- DOI：10.3390/app12115354
- 证据：abstract；摘要明确用最小二乘/FDD估计频率并进行温度回归修正。
- 输入→算法→输出：雷达位移→衰减段最小二乘/FDD固有频率→温度回归校正
- 已有基础/论文增量：摘要：least squares + FDD；linear regression corrects temperature influence。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M16, M20

### R0390｜Static Testing of a Bridge Using an Interferometric Radar: The Case Study of “Ponte degli Alpini,” Belluno, Italy
- DOI：10.1155/2013/504958
- 证据：abstract；摘要：horizontal shift correction；transverse radar arrangement reduces geometric distortion。
- 输入→算法→输出：干涉雷达位移→水平偏移识别/几何配置校正→位移图
- 已有基础/论文增量：摘要报告横向位移偏移校正和横向架设下的位移图几何解释，属于几何/误差修正模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M14, M20

### R0393｜Comparison of natural and artificial forcing to study the dynamic behaviour of bell towers in low wind context by means of ground-based radar interferometry: the case of the Leaning Tower in Pisa
- DOI：10.1088/1742-2132/11/5/055004
- 证据：abstract；摘要：spectral analysis estimates first modal frequencies along two orthogonal directions。
- 输入→算法→输出：雷达位移时序→功率谱分析→正交方向前几阶固有频率
- 已有基础/论文增量：摘要采用功率谱分析从自然和人工激励中识别正交方向的模态频率。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M16

### R0411｜Denoising microwave interferometry data for high-Rise buildings with CEEMDAN energy-Correlation dual Criteria
- DOI：10.5194/isprs-archives-xlix-b1-2026-217-2026
- 证据：abstract；摘要方法证据：However, practical measurements are often contaminated by thermal noise, atmospheric phase delays, and multipath effects, resulting in strong nonstationary and nonlinear characteristics that limit the accuracy of dynamic parameter identification and micro deformation extraction.
- 输入→算法→输出：微波干涉位移→CEEMDAN+能量/相关双准则→去噪结构响应
- 已有基础/论文增量：摘要明确CEEMDAN分解、能量-相关准则筛选IMF并与小波/Kalman比较。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需要按IWR带宽、SNR、采样同步和目标几何重新标定；跨场景算法只能迁移处理思想，不能直接复用参数。
- 模块：M08, M17

### R0429｜DEFORMATION MONITORING OF LARGE STRUCTURES BY GROUND-BASED SAR INTERFEROMETRY
- DOI：10.1590/s1982-21702016000100003
- 证据：abstract；摘要：extract atmospheric phase using permanent scatterer analysis；atmospheric correction。
- 输入→算法→输出：GB-SAR干涉相位→永久散射体大气相位估计/校正→有效位移
- 已有基础/论文增量：摘要明确通过永久散射体分析提取大气相位并做大气校正后恢复位移。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M08, M20

### R0432｜An Improved Second-Order Blind Identification (SOBI) Signal De-Noising Method for Dynamic Deflection Measurements of Bridges Using Ground-Based Synthetic Aperture Radar (GBSAR)
- DOI：10.3390/app9173561
- 证据：abstract；摘要：three adjacent monitoring points；whitening、joint approximate diagonalization、FFT spectrum noise selection、inverse reconstruction。
- 输入→算法→输出：多邻近点位移观测→白化/SOBI联合对角化→FFT识别噪声分量→置零与逆变换去噪
- 已有基础/论文增量：摘要完整描述改进 SOBI：白化、协方差联合对角化、FFT识别噪声分量、置零重构时序。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需要多个相邻观测点及噪声与结构分量可分离；单IWR点位需用多range/多天线或ADXL355补足观测维。
- 模块：M08, M17

### R0435｜Persistent Scatterer Interferometry Processing of COSMO-SkyMed StripMap HIMAGE Time Series to Depict Deformation of the Historic Centre of Rome, Italy
- DOI：10.3390/rs61212593
- 证据：abstract；摘要：Persistent Scatterer Interferometry processing of COSMO-SkyMed time series。
- 输入→算法→输出：SAR影像时序→PS-InSAR干涉处理→历史城区形变序列
- 已有基础/论文增量：摘要明确对COSMO-SkyMed StripMap HIMAGE做持久散射点干涉时序处理，属于SAR相位/不确定度模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R0438｜A Morphology Filter-Assisted Extreme-Point Symmetric Mode Decomposition (MF-ESMD) Denoising Method for Bridge Dynamic Deflection Based on Ground-Based Microwave Interferometry
- DOI：10.1155/2020/8430986
- 证据：abstract；摘要：MF-ESMD；noise-dominant IMFs by Spearman rho；morphological filter residual-noise removal。
- 输入→算法→输出：雷达动态挠度→ESMD/IMF→Spearman rho筛噪声IMF→重构→形态学滤波
- 已有基础/论文增量：摘要明确提出 ESMD 分解、Spearman rho 筛除噪声主导 IMF，再用 morphology filter 去残余噪声。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：形态结构元素、IMF选择需按IWR噪声频带和<100 Hz模态重调；过度滤波可能削弱微米振幅。
- 模块：M08, M17

### R0477｜Domain Knowledge Embedded InSAR‐Based 3D Displacement Monitoring of Urban Buildings
- DOI：10.1155/stc/8864614
- 证据：abstract；摘要：domain-knowledge embedded InSAR-based 3D displacement monitoring。
- 输入→算法→输出：InSAR相位/域知识→3D几何位移重建→城市建筑位移
- 已有基础/论文增量：摘要明确域知识嵌入InSAR三维位移监测，涉及干涉相位、几何三维和质量约束。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M14, M20

### R0504｜Monitoring Displacements and Damage Detection through Satellite MT-InSAR Techniques: A New Methodology and Application to a Case Study in Rome (Italy)
- DOI：10.3390/rs15051177
- 证据：abstract；摘要：multi-temporal InSAR displacement and damage detection methodology。
- 输入→算法→输出：多时相SAR→MT-InSAR时序→建筑位移/损伤指标
- 已有基础/论文增量：摘要明确多时相InSAR形变与损伤时序分析，属于相位时序/散射点质量模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R0510｜Thermal deformation monitoring of a highway bridge: combined analysis of geodetic and satellite-based InSAR measurements with structural simulations
- DOI：10.1007/s13349-024-00779-9
- 证据：abstract；摘要：satellite InSAR and geodetic measurements cross-checked with structural simulations。
- 输入→算法→输出：InSAR+测地→热形变时序与结构模拟→桥梁位移
- 已有基础/论文增量：摘要将卫星InSAR与测地和结构模拟联合做桥梁热形变监测，包含相位时序和交叉验证。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R0513｜Measurement Refinements of Ground-Based Radar Interferometry in Bridge Load Test Monitoring: Comprehensive Analysis on a Multi-Span Cable-Stayed Bridge
- DOI：10.3390/rs16111882
- 证据：abstract；摘要明确提出phase jump恢复和目标变形投影修正。
- 输入→算法→输出：雷达相位→phase-jump检测恢复→考虑目标变形的LOS投影→位移/沉降
- 已有基础/论文增量：摘要：phase jumps detected and recovered；precise displacement projection considering target deformation。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M06, M14, M20

### R0516｜An Interferometric MIMO Radar for Bridge Monitoring
- DOI：10.1109/lgrs.2019.2900405
- 证据：abstract；摘要明确采用压缩感知和SAR相干成像。
- 输入→算法→输出：MIMO阵列回波→压缩感知+合成孔径相干成像→桥梁视场位移观测
- 已有基础/论文增量：摘要：compressive sensing and synthetic aperture radar for coherent images。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M11, M13, M15

### R0531｜Time-Series Analysis on Persistent Scatter-Interferometric Synthetic Aperture Radar (PS-InSAR) Derived Displacements of the Hong Kong–Zhuhai–Macao Bridge (HZMB) from Sentinel-1A Observations
- DOI：10.3390/rs13040546
- 证据：abstract；摘要：time-series PS-InSAR displacement of HZMB；validation data。
- 输入→算法→输出：Sentinel-1 PS-InSAR时序→桥梁形变/沉降→水准与角反射器验证
- 已有基础/论文增量：摘要明确PS-InSAR时间序列桥梁形变并用沉降/角反射器验证。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R0534｜Post-Event Surface Deformation of the 2018 Baige Landslide Revealed by Ground-Based and Spaceborne Radar Observations
- DOI：10.3390/rs15163996
- 证据：abstract；摘要方法证据：Secondly, with the Sentinel-1A ascending and descending orbit images from December 2018 to February 2022, the InSAR-stacking technology assisted by the generic atmospheric correction online service (GACOS) and the multidimensional small baseline subset (MSBAS) method are utilized to obtain the annual deformation velocity and cumulative deformation in the satellite radar line of sight (LOS) direction of the landslide.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Secondly, with the Sentinel-1A ascending and descending orbit images from December 2018 to February 2022, the InSAR-stacking technology assisted by the generic atmospheric correction online service (GACOS) and the multidimensional small baseline subset (MSBAS) method are utilized to obtain the annual deformation velocity and cumulative deformation in the satellite radar line of sight (LOS) direction of the landslide.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M08,M14）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M08, M14

### R0537｜Analysis and correction of meteorological disturbance observed by ground radars in complex environment
- DOI：10.1371/journal.pone.0258168
- 证据：abstract；题名/摘要：analysis and correction of meteorological disturbance observed by ground radars。
- 输入→算法→输出：地面雷达相位→气象扰动估计/校正→有效位移或观测量
- 已有基础/论文增量：摘要主题是复杂环境地面雷达气象扰动分析与校正，属于外部扰动/大气校正模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08

### R0543｜Coherent Dynamic Clutter Suppression in Structural Health Monitoring via the Image Plane Technique
- DOI：10.3390/rs17203459
- 证据：abstract；摘要：Time Domain Backprojection transfers Doppler-aliasing clutter to image plane for cancellation。
- 输入→算法→输出：地基雷达回波→TDBP图像平面动态杂波压缩→杂波抑制/结构位移
- 已有基础/论文增量：摘要明确把动态杂波经时域反投影压缩到图像平面再抑制，属于雷达杂波处理模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08

### R0552｜Monitoring of High-Speed Railway Ground Deformation Using Interferometric Synthetic Aperture Radar Image Analysis
- DOI：10.3390/app15084318
- 证据：abstract；摘要：29 SAR images; PS-InSAR time series; validation by leveling/corner reflectors。
- 输入→算法→输出：SAR干涉时间序列→PS-InSAR散射点筛选/时序估计→毫米级形变
- 已有基础/论文增量：摘要明确采用PS-InSAR时间序列处理、持续散射点与角反射器验证，实现毫米级地表形变。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M06, M08, M20

### R0603｜Georeferencing of terrestrial radar images in geomonitoring using kernel correlation
- DOI：10.1080/01431161.2023.2274321
- 证据：abstract；摘要：提出自动TRI图像地理配准；用雷达幅度与3D点云入射角匹配特征，再以Kernel Density Correlation估计变换参数。
- 输入→算法→输出：TRI幅度/LOS图像+3D点云→特征匹配+Kernel Density Correlation配准→雷达图像3D空间定位
- 已有基础/论文增量：摘要明确提出KDC自动地理配准和雷达-3D点云坐标变换，属于几何/质量模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M14

### R0612｜ESMD-WSST High-Frequency De-Noising Method for Bridge Dynamic Deflection Using GB-SAR
- DOI：10.3390/electronics12010054
- 证据：abstract；摘要：ESMD + mutual-information entropy + wavelet synchrosqueezing denoising。
- 输入→算法→输出：GB-SAR挠度→ESMD/MIE分解筛选+WSST→去噪挠度
- 已有基础/论文增量：摘要明确ESMD分解、MIE筛选和WSST高频去噪重构GB-SAR桥梁挠度。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M17

### R0621｜Multi-target Vital Sign Detection by Fusion of Biological Radar and Convolutional Neural Network
- DOI：10.12694/scpe.v26i3.4328
- 证据：abstract；摘要：multi-target vital-sign detection combining biological radar and CNN object detection。
- 输入→算法→输出：生物雷达回波→CNN多目标检测/分类→多目标生命体征
- 已有基础/论文增量：摘要明确生物雷达多目标检测与CNN目标检测融合，属于候选检测/多目标分离模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M17

### R0630｜Improving GNSS Landslide Monitoring with the Use of Low-Cost MEMS Accelerometers
- DOI：10.3390/app9235075
- 证据：abstract；摘要方法证据：Using low-cost sensors could be an interesting alternative solution if the accuracy requirements can be satisfied.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Using low-cost sensors could be an interesting alternative solution if the accuracy requirements can be satisfied.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R0672｜Quaternionic analysis of the influences of systematic biases on radar data processing
- DOI：10.18610/jg3.2015.072501
- 证据：abstract；摘要：quaternionic analysis; measurement frame with radar systematic biases; KF tracking。
- 输入→算法→输出：雷达偏置测量→measurement-frame四元数偏差建模→KF轨迹
- 已有基础/论文增量：摘要提出含系统偏差的测量框架、四元数工具和KF轨迹估计，属于偏差建模/跟踪模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M18, M20

### R0675｜Accurate and Contactless Vital Sign Detection in Short Time Window with 24 GHz Doppler Radar
- DOI：10.1155/2021/1565567
- 证据：abstract；摘要：two-step I/Q mismatch correction; extended differentiate-and-cross-multiply; differential-evolution search。
- 输入→算法→输出：CW Doppler I/Q→失配/DC校正→extended DACM→差分进化频率估计
- 已有基础/论文增量：摘要明确两步I/Q失配校正、extended differentiate-and-cross-multiply解调和差分进化频率搜索。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M03, M05, M16, M20

### R0678｜An FCNN-Based Super-Resolution Mmwave Radar Framework for Contactless Musical Instrument Interface
- DOI：10.1109/tmm.2021.3079695
- 证据：abstract；摘要：regressive FCNN spatial super-resolution and tracking from MIMO radar waveform。
- 输入→算法→输出：MIMO复数回波→FCNN空间超分辨→手部位置/速度轨迹
- 已有基础/论文增量：摘要明确MIMO雷达FCNN空间超分辨定位和跟踪，属于角度/位置精化与跟踪模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M12, M18

### R0726｜Under the Sand: Navigation and Localization of a Micro Aerial Vehicle for Landmine Detection with Ground-Penetrating Synthetic Aperture Radar
- DOI：10.55417/fr.2022034
- 证据：abstract；摘要：GPSAR系统以RTK-GNSS+IMU因子图状态估计平台姿态，并通过时空标定/同步支持相干SAR成像。
- 输入→算法→输出：机载GPR-SAR回波+RTK-GNSS/IMU→因子图姿态估计与同步标定→相干SAR成像/目标定位
- 已有基础/论文增量：摘要明确给出因子图状态估计、平台姿态与时空同步融合，属于几何/多传感融合模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R0762｜MILLIMETRE-WAVE RADAR FOR REAL-TIME CATTLE ACTIVITIES MONITORING: LARGE-SCALE FARMING USING KEYSTONE TRANSFORM AND 2-DIMENSIONAL FAST FOURIER TRANSFORM
- DOI：10.63748/feticon2025.v3i1p6
- 证据：abstract；摘要方法证据：Traditional monitoring methods, however, often rely on subjective visual observations, accelerometers, or Radio Frequency Identification (RFID) tags, which are limited by their accuracy and reliability.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Traditional monitoring methods, however, often rely on subjective visual observations, accelerometers, or Radio Frequency Identification (RFID) tags, which are limited by their accuracy and reliability.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R0771｜Beneficial Effects of Self-Motion for the Continuous Phase Analysis of Ac-Coupled Doppler Radars
- DOI：10.3390/electronics13040772
- 证据：abstract；摘要：high-pass distortion and uncorrelated phase during stationary intervals; continuous phase analysis。
- 输入→算法→输出：AC-coupled Doppler→高通失真分析/连续相位→位移相位观测
- 已有基础/论文增量：摘要讨论AC耦合Doppler雷达高通失真及连续相位分析，属于相位链路/耦合校正模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M03, M05

### R0774｜EarthCARE's cloud profiling radar antenna pointing correction using surface Doppler measurements
- DOI：10.5194/amt-18-5607-2025
- 证据：abstract；摘要方法证据：The Earth Cloud Aerosol and Radiation Explorer (EarthCARE) mission, a joint effort between the European Space Agency (ESA) and the Japan Aerospace Exploration Agency (JAXA), aims to advance our understanding of aerosols, clouds, precipitation, and radiation using a comprehensive payload of active and passive sensors.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The Earth Cloud Aerosol and Radiation Explorer (EarthCARE) mission, a joint effort between the European Space Agency (ESA) and the Japan Aerospace Exploration Agency (JAXA), aims to advance our understanding of aerosols, clouds, precipitation, and radiation using a comprehensive payload of active and passive sensors.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0780｜Concurrent Respiration Monitoring of Multiple Subjects by Phase-Comparison Monopulse Radar Using Independent Component Analysis (ICA) With JADE Algorithm and Direction of Arrival (DOA)
- DOI：10.1109/access.2020.2988038
- 证据：abstract；摘要：ICA-JADE; DOA; SNR-based decision and beam switching。
- 输入→算法→输出：单脉冲阵列回波→ICA-JADE+DOA/波束切换→多主体呼吸信号
- 已有基础/论文增量：摘要明确ICA-JADE、DOA、SNR决策和波束切换，用于近距多主体分离。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M12, M17

### R0783｜Characterization Technique for a Doppler Radar Occupancy Sensor
- DOI：10.3390/electronics12244888
- 证据：abstract；摘要：characterization technique and reproducible mobile target for Doppler radar occupancy sensor。
- 输入→算法→输出：CW Doppler回波→可重复目标灵敏度/覆盖表征→占用检测质量指标
- 已有基础/论文增量：摘要给出单通道CW Doppler占用传感器可重复小运动标定/灵敏度表征方法。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M20

### R0795｜Motion Detection Method For Clutter Rejection In The Bio-Radar Signal Processing
- DOI：10.5281/zenodo.1340481
- 证据：abstract；摘要：motion detection for clutter rejection and DC-offset removal。
- 输入→算法→输出：生理Doppler回波→运动检测/DC offset去除→呼吸率
- 已有基础/论文增量：摘要提出随机运动检测与DC offset去除以抑制生理雷达杂波。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08

### R0807｜Enhancing FMCW Radar-Based Human Activity Recognition using DI-ResNet
- DOI：10.21553/rev-jec.433
- 证据：abstract；摘要方法证据：This paper proposes a method to enhance the quality of Human Activity Recognition (HAR) based on Frequency Modulated Continuous Wave (FMCW) radar.
- 输入→算法→输出：雷达原始回波/慢时间IQ→This paper proposes a method to enhance the quality of Human Activity Recognition (HAR) based on Frequency Modulated Continuous Wave (FMCW) radar.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R0810｜Ultra-Wide Patch Antenna Array Design at 60 GHz Band for Remote Vital Sign Monitoring with Doppler Radar Principle
- DOI：10.1007/s10762-016-0344-z
- 证据：abstract；摘要方法证据：In this paper, ultra-wide patch antenna arrays have been presented at 60 GHz band (57.24–65.88 GHz) with improved gain and beam-width capabilities for remote detection of respiration and heart beat rate of a person with Doppler radar principle.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In this paper, ultra-wide patch antenna arrays have been presented at 60 GHz band (57.24–65.88 GHz) with improved gain and beam-width capabilities for remote detection of respiration and heart beat rate of a person with Doppler radar principle.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0819｜Noncontact Sleeping Heartrate Monitoring Method Using Continuous-Wave Doppler Radar Based on the Difference Quadratic Sum Demodulation and Search Algorithm
- DOI：10.3390/s22197646
- 证据：abstract；摘要：difference quadratic-sum demodulation and constrained nearest-neighbor search。
- 输入→算法→输出：CW Doppler相位→差分平方和解调+近邻搜索→心率
- 已有基础/论文增量：摘要提出差分平方和解调和约束近邻搜索，从呼吸辅助提取心跳。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M05, M16

### R0822｜Measuring ocean total surface current velocity with the KuROS and KaRADOC airborne near-nadir Doppler radars: a multi-scale analysis in preparation for the SKIM mission
- DOI：10.5194/os-16-1399-2020
- 证据：abstract；摘要方法证据：Satellite-borne Doppler wave and current scatterometers (DWaCSs) are among the proposed techniques to fill this observation gap.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Satellite-borne Doppler wave and current scatterometers (DWaCSs) are among the proposed techniques to fill this observation gap.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0825｜A Noninvasive and Noncontact Jugular Venous Pulse Measurement Using a 60-GHz mmWave Sensor
- DOI：10.46620/25-0004
- 证据：abstract；摘要：eigen beamforming; localization within DOA range; surface venous pulsation。
- 输入→算法→输出：60GHz FMCW→eigen-beamforming/DOA→JVP脉搏
- 已有基础/论文增量：摘要明确60GHz FMCW雷达eigen-beamforming和DOA范围定位，再提取JVP脉搏。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M16

### R0831｜Application of Terahertz Detection Technology in Non-Destructive Thickness Measurement
- DOI：10.3390/photonics12121191
- 证据：abstract；摘要：time-domain/frequency-domain spectroscopy and model-based inversion/deep learning。
- 输入→算法→输出：THz时频回波→光谱/模型反演/学习→多层厚度
- 已有基础/论文增量：摘要明确THz时域/频域光谱、模型反演和深度学习厚度估计，属于高频雷达/波形测量迁移。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M01, M20

### R0837｜Software-Defined 1550-nm Full-Fiber Doppler Lidar for Contactless Vibration Measurement of High Voltage Power Equipment
- DOI：10.13164/re.2023.0391
- 证据：abstract；摘要方法证据：In this work, a 1550-nm full-fiber Doppler lidar via software-defined platform is built to realize flexible and low-cost contactless vibration measurement of highvoltage power equipment.A 1550-nm fiber layout is designed to generate optical interference between vibration signal and carrier wave.The reflected vibration signal is collected by an optical transceiver and the carrier wave is generated by an acousto-optic 
- 输入→算法→输出：雷达原始回波/慢时间IQ→In this work, a 1550-nm full-fiber Doppler lidar via software-defined platform is built to realize flexible and low-cost contactless vibration measurement of highvoltage power equipment.A 1550-nm fiber layout is designed to generate optical interference between vibration signal and carrier wave.The reflected vibration signal is collected by an optical transceiver and the carrier wave is generated by an acousto-optic →结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0840｜UAV-Based Bistatic SAR-Imaging Using a Stationary Repeater
- DOI：10.1109/jmw.2023.3253667
- 证据：abstract；摘要：bistatic repeater-SAR; multiple observation angles; signal separation。
- 输入→算法→输出：双基地SAR回波→多角观测/信号分离→高分辨图像
- 已有基础/论文增量：摘要明确双基地SAR有源转发器、多角观测、信号分离和成像链。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M15

### R0849｜Ka-Band Doppler Scatterometry: A Strong Wind Case Study
- DOI：10.3390/rs14061348
- 证据：abstract；摘要方法证据：Global joint measurements of sea surface winds and currents are planned using satellite-based Doppler scatterometers operating in the Ka-band to achieve improved spatial resolution and retrieval accuracy.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Global joint measurements of sea surface winds and currents are planned using satellite-based Doppler scatterometers operating in the Ka-band to achieve improved spatial resolution and retrieval accuracy.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16,M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16, M20

### R0858｜Directional amplitude backscatter modulation with suppressed Doppler based on rotating resonant loop
- DOI：10.1038/s41598-022-26609-w
- 证据：abstract；摘要方法证据：The directional amplitude backscatter modulation with suppressed Doppler is demonstrated based on the scattering from a symmetrically rotating resonant loop.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The directional amplitude backscatter modulation with suppressed Doppler is demonstrated based on the scattering from a symmetrically rotating resonant loop.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0864｜Robust SAR STAP via Kronecker decomposition
- DOI：10.1109/taes.2016.150712
- 证据：abstract；摘要：space-time adaptive processing; low-rank Kronecker covariance; separable clutter cancellation。
- 输入→算法→输出：多通道SAR→Kronecker低秩STAP→静态杂波抑制/动目标检测
- 已有基础/论文增量：摘要明确Kronecker低秩协方差估计与可分离STAP杂波抑制。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M17

### R0870｜Analysis of the lightning production of convective cells
- DOI：10.5194/amt-12-5573-2019
- 证据：abstract；摘要方法证据：The cells were detected by the MeteoSwiss Thunderstorms Radar Tracking (TRT) algorithm in the course of a lightning measurement campaign that took place in the summer of 2017 in the area surrounding the Säntis mountain, in the northeastern part of Switzerland.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The cells were detected by the MeteoSwiss Thunderstorms Radar Tracking (TRT) algorithm in the course of a lightning measurement campaign that took place in the summer of 2017 in the area surrounding the Säntis mountain, in the northeastern part of Switzerland.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M18

### R0876｜A Motion Compensation Method for Shipborne HFSWR by Using Dual Reference RF Signals Generated Onshore
- DOI：10.3390/rs14051055
- 证据：abstract；摘要：dual reference RF signals; 6-DOF motion compensation without sinusoidal model。
- 输入→算法→输出：HFSWR回波→双参考RF六自由度运动估计→平台运动补偿
- 已有基础/论文增量：摘要明确双参考RF信号估计船载HFSWR六自由度运动并做非正弦模型补偿。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M20

### R0897｜Design and Experimental Demonstration of an Integrated Sensing and Communication System for Vital Sign Detection
- DOI：10.3390/s25123766
- 证据：abstract；摘要：unified OFDM signal for communication and vital-sign sensing。
- 输入→算法→输出：OFDM ISAC回波→生命体征相位/时频估计→呼吸心跳
- 已有基础/论文增量：摘要明确OFDM ISAC统一信号同时通信和呼吸/心跳感知，属于联合波形/相位时频模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M05, M16

### R0903｜Development of Raw Data Processing System for CP-SAR On-board JX-2 UAV using Mobile Heterogeneous Computing
- DOI：10.21535/just.v4i2.914
- 证据：abstract；摘要：raw SAR processing with Range-Doppler Algorithm on CPU-GPU platform。
- 输入→算法→输出：CP-SAR原始数据→Range-Doppler算法→机载图像
- 已有基础/论文增量：摘要明确UAV CP-SAR原始数据Range-Doppler处理并在移动异构平台实时实现。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M01, M02

### R0933｜Wind-Induced Displacement Analysis for a Traffic Light Structure Based on a Low-Cost Doppler Radar Array
- DOI：10.1109/tim.2021.3098380
- 证据：abstract；摘要明确由多雷达阵列解调获得频率和模态。
- 输入→算法→输出：多点Doppler阵列解调→位移→瞬时固有频率/模态→加速度计对照
- 已有基础/论文增量：摘要：multiple Doppler radar array；instantaneous natural frequencies and mode shapes；accelerometer comparison。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、目标几何和噪声重新标定；仅迁移处理思想。
- 模块：M15, M16

### R0936｜Temporal Convolutional Neural Networks for Radar Micro-Doppler Based Gait Recognition
- DOI：10.3390/s21020381
- 证据：abstract；摘要方法证据：This paper proposes an approach based on a temporal convolutional deep neural networks classifier applied to radar micro-Doppler signatures in order to identify individuals.
- 输入→算法→输出：雷达原始回波/慢时间IQ→This paper proposes an approach based on a temporal convolutional deep neural networks classifier applied to radar micro-Doppler signatures in order to identify individuals.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0939｜Classification and Discrimination of Birds and Small Drones Using Radar Micro-Doppler Spectrogram Images
- DOI：10.3390/signals4020018
- 证据：abstract；摘要方法证据：Using a custom-designed 10-GHz continuous wave (CW) radar system, measurements from different scenarios on a variety of targets were recorded to create datasets for image classification.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Using a custom-designed 10-GHz continuous wave (CW) radar system, measurements from different scenarios on a variety of targets were recorded to create datasets for image classification.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0942｜Millimeter-Wave Radar-Based Elderly Fall Detection Fed by One-Dimensional Point Cloud and Doppler
- DOI：10.1109/access.2023.3297512
- 证据：abstract；摘要方法证据：In the proposed technique, the long short-term memory (LSTM) network is created and then employed as an intelligent classifier of fall detection.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In the proposed technique, the long short-term memory (LSTM) network is created and then employed as an intelligent classifier of fall detection.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0945｜Three-Dimensional Human Pose Estimation from Micro-Doppler Signature Based on SISO UWB Radar
- DOI：10.3390/rs16071295
- 证据：abstract；摘要方法证据：In this paper, we propose an innovative approach for transforming 2D human pose estimation into 3D models using Single Input–Single Output (SISO) Ultra-Wideband (UWB) radar technology.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In this paper, we propose an innovative approach for transforming 2D human pose estimation into 3D models using Single Input–Single Output (SISO) Ultra-Wideband (UWB) radar technology.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0948｜High Range Resolution Micro-Doppler Radar Theory and Its Application to Human Gait Classification
- DOI：无 DOI
- 证据：abstract；摘要方法证据：This work advances the use of radar for target classification.High range resolution (HRR) and micro-Doppler signal analysis both provide radar operators the ability to classify observed targets.However, traditional micro-Doppler analysis does not account for a target moving in range and is therefore not compatible with high range resolution waveforms.We propose the use of a joint-range-time-frequency (JRTF)signature 
- 输入→算法→输出：雷达原始回波/慢时间IQ→This work advances the use of radar for target classification.High range resolution (HRR) and micro-Doppler signal analysis both provide radar operators the ability to classify observed targets.However, traditional micro-Doppler analysis does not account for a target moving in range and is therefore not compatible with high range resolution waveforms.We propose the use of a joint-range-time-frequency (JRTF)signature →目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0951｜High Fidelity Physics Simulation-Based Convolutional Neural Network for Automotive Radar Target Classification Using Micro-Doppler
- DOI：10.1109/access.2021.3085985
- 证据：abstract；摘要方法证据：Specifically, machine learning (ML) algorithms can be trained to classify VRUs using the spectral content of radar signals.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Specifically, machine learning (ML) algorithms can be trained to classify VRUs using the spectral content of radar signals.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0954｜Portable UWB RADAR Sensing System for Transforming Subtle Chest Movement Into Actionable Micro-Doppler Signatures to Extract Respiratory Rate Exploiting ResNet Algorithm
- DOI：10.1109/jsen.2021.3110367
- 证据：abstract；摘要方法证据：Contactless methods are crucial specifically during the COVID-19 epidemic as they require the least amount of involvement from infected individuals as well as healthcare personnel.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Contactless methods are crucial specifically during the COVID-19 epidemic as they require the least amount of involvement from infected individuals as well as healthcare personnel.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R0966｜Radar-Based Air-Writing Gesture Recognition Using a Novel Multistream CNN Approach
- DOI：10.1109/jiot.2022.3189395
- 证据：abstract；摘要方法证据：Existing radar-based solutions often perform the mid-air writing recognition by tracking the hand trajectory using multiple monostatic or bistatic radars.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Existing radar-based solutions often perform the mid-air writing recognition by tracking the hand trajectory using multiple monostatic or bistatic radars.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M18

### R0978｜Passive Radar Antenna Array Design and Assembly
- DOI：无 DOI
- 证据：abstract；摘要方法证据：Digitally scanned arrays are highly beneficial for use in passive radar systems due to their adaptive beam-and null-steering capabilities, critical for reliable wide area surveillance as well as multi-target tracking.Furthermore, the lack of moving components needed to perform scanning operations reduces long term maintenance costs.A large, low-cost overlapped subarray architecture was designed, assembled, and charac
- 输入→算法→输出：雷达原始回波/慢时间IQ→Digitally scanned arrays are highly beneficial for use in passive radar systems due to their adaptive beam-and null-steering capabilities, critical for reliable wide area surveillance as well as multi-target tracking.Furthermore, the lack of moving components needed to perform scanning operations reduces long term maintenance costs.A large, low-cost overlapped subarray architecture was designed, assembled, and charac→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M18,M15）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M18, M15

### R0987｜Micro-Motion Estimation of Maritime Targets Using Pixel Tracking in Cosmo-Skymed Synthetic Aperture Radar Data—An Operative Assessment
- DOI：10.3390/rs11141637
- 证据：abstract；摘要方法证据：In this paper, we propose a novel strategy to estimate the micro-motion (m-m) of ships from synthetic aperture radar (SAR) images.
- 输入→算法→输出：雷达原始回波/慢时间IQ→In this paper, we propose a novel strategy to estimate the micro-motion (m-m) of ships from synthetic aperture radar (SAR) images.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M18

### R0990｜An Adaptive Filtering Algorithm Based on Range-Doppler Information Guidance
- DOI：10.1109/access.2023.3344631
- 证据：abstract；摘要：frame mean subtraction; distance-Doppler guided mask; fractional STFT。
- 输入→算法→输出：FMCW range-Doppler→均值/掩膜杂波滤波→分数阶STFT→目标特征
- 已有基础/论文增量：摘要明确帧均值静态杂波去除、距离-Doppler引导滤波、分数阶STFT和目标跟踪先验。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M16, M18

### R0996｜An Image Focusing Method for Sparsity-Driven Radar Imaging of Rotating Targets
- DOI：10.3390/s18061840
- 证据：abstract；摘要：cluster atoms in sparse reconstruction and estimate true off-grid scatterers。
- 输入→算法→输出：稀疏雷达图像→off-grid原子聚类+散射点重估→聚焦图像
- 已有基础/论文增量：摘要明确稀疏成像的off-grid原子聚类与散射点重估，属于稀疏重构/聚焦模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M13

### R1002｜Micro-Doppler Ambiguity Resolution Based on Short-Time Compressed Sensing
- DOI：10.1155/2015/864508
- 证据：abstract；摘要：short-time compressed sensing; OMP; unambiguous micro-Doppler。
- 输入→算法→输出：稀疏慢时间回波→CS感知矩阵+OMP→无歧义micro-Doppler频谱
- 已有基础/论文增量：摘要明确随机稀疏脉冲、短时窗口CS感知矩阵和OMP恢复无歧义micro-Doppler。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M13

### R1005｜Development of a High-Resolution All-Fiber Homodyne Laser Doppler Vibrometer
- DOI：10.3390/s20205801
- 证据：abstract；摘要方法证据：Based on the homodyne detection, a compact and cost-effective all-fiber laser Doppler vibrometer (LDV) with high resolution is presented.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Based on the homodyne detection, a compact and cost-effective all-fiber laser Doppler vibrometer (LDV) with high resolution is presented.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R1011｜Detecting vibration features from remote objects based on high-speed imagery
- DOI：10.1117/1.oe.60.1.013102
- 证据：abstract；摘要方法证据：The well-established laser Doppler vibrometry technique is widely used as a high-sensitivity, noncontact method.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The well-established laser Doppler vibrometry technique is widely used as a high-sensitivity, noncontact method.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R1014｜GBSAR Geocoding Based on Bayes Theorem
- DOI：10.4018/ijitsa.380648
- 证据：abstract；摘要：Bayesian maximum-a-posteriori geocoding; Doppler projection; sub-mm RMS。
- 输入→算法→输出：GB-SAR回波→Doppler投影+Bayesian MAP/先验筛选→3D位移
- 已有基础/论文增量：摘要明确Bayesian MAP、Doppler投影和多源融合做GB-SAR近场3D geocoding。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M14, M20

### R1020｜Omni-Directional Navigation Mobile Robot using Radar Ultrasonic Sensors
- DOI：10.58915/ijaris.v2i1.3194
- 证据：abstract；摘要方法证据：A servo-driven HC-SR04 ultrasonic sensor performs radar-like scanning from 0° to 180°, providing real-time environmental information to an Arduino Uno executing a reactive obstacle avoidance algorithm.
- 输入→算法→输出：雷达原始回波/慢时间IQ→A servo-driven HC-SR04 ultrasonic sensor performs radar-like scanning from 0° to 180°, providing real-time environmental information to an Arduino Uno executing a reactive obstacle avoidance algorithm.→目标/运动特征
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M15）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M15

### R1026｜Multi-Sensor Mobile Laser Doppler Vibrometry for Internal Damage Detection in Reinforced Concrete Structures
- DOI：10.3390/s26175612
- 证据：abstract；摘要方法证据：These damages can be detected using the vibration response of the structures, and laser Doppler vibrometry (LDV) on a moving platform offers an efficient, long-range sensing approach for structural vibration monitoring.
- 输入→算法→输出：雷达原始回波/慢时间IQ→These damages can be detected using the vibration response of the structures, and laser Doppler vibrometry (LDV) on a moving platform offers an efficient, long-range sensing approach for structural vibration monitoring.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16

### R1032｜Research on Ultra-Wideband Radar Echo Signal Processing Method Based on P-Order Extraction and VMD
- DOI：10.3390/s22186726
- 证据：abstract；摘要：P-order physical-sign extraction and VMD IMF reconstruction suppress interference。
- 输入→算法→输出：UWB雷达回波→P阶特征+VMD/IMF选择→呼吸/心跳信号
- 已有基础/论文增量：摘要明确P阶物理信息提取与VMD分解重构生命体征，属于分解/抑制干扰模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M17

### R1044｜Passive acoustic tracking of an unmanned underwater vehicle using bearing-Doppler-speed measurements
- DOI：10.1121/10.0009568
- 证据：abstract；摘要方法证据：Tracking unmanned underwater vehicles (UUVs) in the presence of shipping traffic is a critical task for passive acoustic harbor security systems.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Tracking unmanned underwater vehicles (UUVs) in the presence of shipping traffic is a critical task for passive acoustic harbor security systems.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述可拆出的具体雷达处理链（M02,M16,M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M02, M16, M18

### R1053｜Scalable Multisubject Vital Sign Monitoring With mmWave FMCW Radar and FPGA Prototyping
- DOI：10.1109/jsen.2024.3507951
- 证据：abstract；摘要：scalable multisubject monitoring; FPGA prototyping; mmWave FMCW。
- 输入→算法→输出：FMCW回波→FPGA实时处理+多主体检测→多目标生命体征
- 已有基础/论文增量：摘要明确mmWave FMCW多主体生命体征、FPGA实时处理和多目标检测，可迁移目标选择/并行化模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M09, M10, M15

### R1059｜A novel target state detection method for accurate cardiopulmonary signal extraction based on FMCW radar signals
- DOI：10.3389/fphys.2023.1206471
- 证据：abstract；摘要：mixed-modal threshold; frequency-domain confidence; range-bin variance.。
- 输入→算法→输出：FMCW range-bin→频域置信度+时域方差→目标状态/候选range选择
- 已有基础/论文增量：摘要明确用频域置信度和时域range-bin方差判断目标状态并选取高SNR range bin。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M20

### R1062｜Contactless Stethoscope Enabled by Radar Technology
- DOI：10.3390/bioengineering10020169
- 证据：abstract；摘要方法证据：We leverage millimeter wave frequency-modulated continuous wave radar and multi-input multi-output beamforming techniques to capture fine skin vibrations that result from the cardiac movements that cause heart sounds.
- 输入→算法→输出：雷达原始回波/慢时间IQ→We leverage millimeter wave frequency-modulated continuous wave radar and multi-input multi-output beamforming techniques to capture fine skin vibrations that result from the cardiac movements that cause heart sounds.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M11,M12）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M11, M12

### R1065｜Detection and Monitoring of People in Collapsed Buildings Using a Rotating Radar on a UAV
- DOI：10.1109/trs.2023.3342368
- 证据：abstract；摘要方法证据：A framework including motion estimation, motion compensation, tracking and clustering is proposed.
- 输入→算法→输出：雷达原始回波/慢时间IQ→A framework including motion estimation, motion compensation, tracking and clustering is proposed.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M08,M18）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M08, M18

### R1068｜Three-Dimensional Micro-Motion Feature Extraction of the Vibrating Target Based on Multi-Channel Radar in the Terahertz Band
- DOI：10.3390/s20010008
- 证据：abstract；摘要：phase-derived-range; interference and autocorrelation; 3D micro-motion.。
- 输入→算法→输出：多通道雷达→phase-derived range/干涉/自相关→三维微动幅值频率方向
- 已有基础/论文增量：摘要明确多通道THz雷达的phase-derived range、干涉和自相关实现三维微动特征估计。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M14, M16

### R1071｜Adaptive Separation of Respiratory and Heartbeat Signals among Multiple People Based on Empirical Wavelet Transform Using UWB Radar
- DOI：10.3390/s20174913
- 证据：abstract；摘要：empirical wavelet transform; adaptive separation of respiration/heartbeat/interference。
- 输入→算法→输出：UWB雷达相位→EWT自适应分解→多主体呼吸/心跳分量
- 已有基础/论文增量：摘要明确EWT自适应边界和紧框经验小波分离呼吸/心跳与体动干扰。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M16, M17

### R1074｜Noncontact Measurement of the Instantaneous Heart Rate in a Multi-Person Scenario Using ${X}$ -Band Array Radar and Adaptive Array Processing
- DOI：10.1109/jetcas.2018.2809582
- 证据：abstract；摘要：Capon; directionally constrained minimization-of-power; adaptive array。
- 输入→算法→输出：X-band阵列→Capon DOA+方向约束最小功率→目标心率
- 已有基础/论文增量：摘要明确Capon DOA、方向约束最小功率和自适应阵列合并。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M12

### R1080｜A Reliable Observation Point Selection Method for GB-SAR in Low-Coherence Areas
- DOI：10.3390/rs16071251
- 证据：abstract；摘要：MLE stability; phase correction; variance-based adaptive filtering/wavelet thresholds。
- 输入→算法→输出：GB-SAR相位→MLE稳定性+解缠相位校正+方差/小波滤波→可靠测点
- 已有基础/论文增量：摘要明确MLE稳定性评估、phase correction、方差估计和wavelet adaptive filtering选取GB-SAR可靠点。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M08, M20

### R1089｜PmTrack
- DOI：10.1145/3631433
- 证据：abstract；摘要：PmTrack uses IMU orientation as identity indicator for radar target matching。
- 输入→算法→输出：mmWave目标→检测与姿态匹配→IMU辅助个体跟踪
- 已有基础/论文增量：摘要明确mmWave个性化跟踪以IMU姿态作身份关联，属于检测/数据关联/跨传感融合。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M18, M19

### R1110｜Enhancing Noncontact Vibration Monitoring With mmWave Radar and Camera Fusion
- DOI：10.1109/jiot.2024.3520674
- 证据：abstract；摘要：VibCamera uses CV semantic segmentation to select radar observation points。
- 输入→算法→输出：mmWave回波+视觉分割→观测点定位/方向约束→振动位移
- 已有基础/论文增量：摘要明确CV语义分割辅助mmWave雷达定位观测点和方向，属于雷达-视觉几何融合。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M14, M19

### R1122｜Human Multi-Activities Classification Using mmWave Radar: Feature Fusion in Time-Domain and PCANet
- DOI：10.3390/s24165450
- 证据：abstract；题名：feature fusion in time-domain and PCANet。
- 输入→算法→输出：mmWave点云/慢时间→时域特征融合+PCANet→活动类别
- 已有基础/论文增量：摘要明确时域特征融合和PCANet用于mmWave活动分类，属于时频/特征分解模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M16, M17

### R1125｜Towards mmWave Altimetry for UAS: Exploring the Potential of 77 GHz Automotive Radars
- DOI：10.3390/drones8030094
- 证据：abstract；摘要方法证据：Moreover, clutter estimation with hardware specifications of a pure look-down mmWave radar is unreported.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Moreover, clutter estimation with hardware specifications of a pure look-down mmWave radar is unreported.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M08）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M08

### R1134｜Road target recognition based on radar range-Doppler spectrum with GS – ResNet
- DOI：10.1080/01431161.2024.2398823
- 证据：abstract；题名：radar range-Doppler spectrum with GS-ResNet。
- 输入→算法→输出：雷达快慢时间→range-Doppler谱→GS-ResNet分类
- 已有基础/论文增量：摘要明确range-Doppler谱和GS-ResNet目标识别，可迁移距离-速度特征构造。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M01, M02, M16

### R1137｜The Degradation of Automotive Radar Sensor Signals Caused by Vehicle Vibrations and Other Nonlinear Movements
- DOI：10.3390/s20216195
- 证据：abstract；题名：degradation caused by vehicle vibrations and nonlinear movements。
- 输入→算法→输出：FMCW回波→车辆振动退化建模/质量评估→稳健雷达观测
- 已有基础/论文增量：摘要分析车辆振动和非线性运动造成的汽车雷达信号退化，提供运动扰动/质量模型。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M20

### R1146｜mmSign: mmWave-based Few-Shot Online Handwritten Signature Verification
- DOI：10.1145/3605945
- 证据：abstract；摘要：mmWave senses hand movements for online signature verification。
- 输入→算法→输出：mmWave回波→手部轨迹检测/少样本匹配→签名验证
- 已有基础/论文增量：摘要明确mmWave手写轨迹感知和少样本在线验证，目标跟踪/轨迹特征可迁移。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M18

### R1161｜Enabling Indoor Multi-Person Tracking With 6G mmWave ISAC Systems
- DOI：10.1109/lwc.2026.3698810
- 证据：abstract；摘要：modified MTI; target identification; Kalman filter with penalty association。
- 输入→算法→输出：mmWave ISAC CSI→MTI杂波去除+目标识别→KF/关联多目标轨迹
- 已有基础/论文增量：摘要明确稀疏OFDM参考信号、MTI静态杂波去除、目标识别和KF惩罚关联。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M10, M18

### R1164｜Mutual Interference Mitigation of Millimeter-Wave Radar Based on Variational Mode Decomposition and Signal Reconstruction
- DOI：10.3390/rs15030557
- 证据：abstract；摘要：VMD separates broadband interference and single-frequency target。
- 输入→算法→输出：毫米波雷达回波→VMD模态分解/重构→抑制互扰
- 已有基础/论文增量：摘要明确VMD分解宽带干扰与单频目标并重构干净信号。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M17

### R1173｜A Fusion Localization System for Security Robots Based on Millimeter Wave Radar and Inertial Sensors
- DOI：10.3390/s24237551
- 证据：abstract；摘要：radar/inertial measurement and state equations; Kalman fusion。
- 输入→算法→输出：毫米波位置+惯性状态→KF融合→机器人位姿
- 已有基础/论文增量：摘要明确mmWave测量方程+惯性状态方程并用KF融合定位。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M18, M19

### R1182｜Real-Time Speed Measurement of Moving Objects with Continuous Wave Doppler Radar Using Software-Defined Radio: Implementation and Performance Analysis
- DOI：10.3390/electronics14214225
- 证据：abstract；摘要：Doppler deviations processed with Welch spectral estimator。
- 输入→算法→输出：CW Doppler→Welch谱估计→速度
- 已有基础/论文增量：摘要明确CW Doppler频移经Welch谱估计提取速度。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M16

### R1185｜A Software-Synchronization Based, Flexible, Low-Cost FMCW Radar
- DOI：10.1109/access.2020.3004597
- 证据：abstract；题名：software-synchronization based flexible low-cost FMCW radar。
- 输入→算法→输出：FMCW ADC/ chirp→软件同步与时序标定→稳定距离/相位
- 已有基础/论文增量：摘要明确FMCW软件同步和低成本硬件时序，属于采样/同步标定模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M01, M20

### R1197｜LoCal
- DOI：10.1145/3631436
- 证据：abstract；摘要：moving robot reference point; static multipath separation; radar-to-room calibration。
- 输入→算法→输出：mmWave range-speed-angle→移动参考点+SLAM标定→房间坐标跟踪
- 已有基础/论文增量：摘要明确利用移动机器人参考点和SLAM处理室内mmWave雷达坐标标定/静态多径。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M14, M18, M20

### R1200｜Water Salinity Sensing with UAV-Mounted IR-UWB Radar
- DOI：10.1145/3633515
- 证据：abstract；摘要方法证据：Water salinity sensing could be challenging when it comes to surface water with complicated basin and tributaries, where existing methods fail to satisfy both efficiency and accuracy requirements.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Water salinity sensing could be challenging when it comes to surface water with complicated basin and tributaries, where existing methods fail to satisfy both efficiency and accuracy requirements.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1215｜Ground-Based MIMO-SAR Fast Imaging Algorithm Based on Geometric Transformation
- DOI：10.3390/electronics12061466
- 证据：abstract；摘要：near-field phase-center error; geometric transformation avoids point-by-point interpolation。
- 输入→算法→输出：MIMO-SAR回波→几何变换/相位中心校正→快速相干成像
- 已有基础/论文增量：摘要明确非共线阵列近场相位中心误差分析和几何变换快速合成成像。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M14

### R1218｜FPGA-Based Moving Array Beamforming for Robust Mixed-Source MIMO Estimation
- DOI：10.24138/jcomss-2025-0278
- 证据：abstract；摘要：min-max beamforming; adaptive diagonal loading; array manifold uncertainty。
- 输入→算法→输出：MIMO阵列→鲁棒beamforming+min-max/diagonal loading→混合源估计
- 已有基础/论文增量：摘要明确移动阵列鲁棒beamforming、min-max优化、自适应diagonal loading和深度展开。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M11, M13, M20

### R1230｜New Robust Sparse Convolutional Coding Inversion Algorithm for Ground Penetrating Radar Images
- DOI：10.1109/tgrs.2023.3268477
- 证据：abstract；摘要：sparse convolutional coding + low-rank ADMM; Huber outlier handling。
- 输入→算法→输出：GPR B-scan→稀疏卷积+低秩ADMM/Huber→去噪目标图像
- 已有基础/论文增量：摘要明确GPR稀疏卷积编码+低秩、ADMM和Huber范数去噪/重构。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M13

### R1251｜Three More Decades in Array Signal Processing Research: An optimization and structure exploitation perspective
- DOI：10.1109/msp.2023.3255558
- 证据：abstract；摘要方法证据：The signal processing community is currently witnessing the emergence of sensor array processing and direction-of-arrival (DoA) estimation in various modern applications, such as automotive radar, mobile user and millimeter wave indoor localization, and drone surveillance, as well as in new paradigms, such as joint sensing and communication in future wireless systems.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The signal processing community is currently witnessing the emergence of sensor array processing and direction-of-arrival (DoA) estimation in various modern applications, such as automotive radar, mobile user and millimeter wave indoor localization, and drone surveillance, as well as in new paradigms, such as joint sensing and communication in future wireless systems.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M11,M12）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M11, M12

### R1260｜Remote Sensing for Vital Information Based on Spectral-Domain Harmonic Signatures
- DOI：10.1109/taes.2019.2917489
- 证据：abstract；摘要：higher-order spectral harmonics and adaptive heart-rate algorithm。
- 输入→算法→输出：UWB雷达谱→高阶谐波分析/自适应频率估计→心率
- 已有基础/论文增量：摘要明确利用高阶谐波频谱恢复心跳基频，属于频谱特征模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M16

### R1272｜Upper Limb Tremors Classification for Parkinson’s Disease Using W-Band (76–81 GHz) Doppler Millimeter-Wave Sensing and Deep-Learning-Based Classifier
- DOI：10.3390/s26123955
- 证据：abstract；题名：Doppler millimeter-wave tremor sensing and deep classifier。
- 输入→算法→输出：W-band Doppler→micro-Doppler/时频特征→震颤分类
- 已有基础/论文增量：摘要明确W-band Doppler微动特征和深度分类，用于震颤频率特征提取。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M16

### R1305｜From Radar Cardiography to Electrocardiograms: Conditional Diffusion Model Enabled Contactless ECG Monitoring Using mmWave Radar
- DOI：10.1109/jiot.2026.3672898
- 证据：abstract；题名：conditional diffusion model enabled contactless ECG with mmWave radar。
- 输入→算法→输出：mmWave心动相位→条件扩散重建→ECG/心动信号
- 已有基础/论文增量：摘要明确mmWave雷达心动图经条件扩散模型重建ECG，涉及相位/时频表征和学习重建。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M05, M16

### R1326｜Deck and Cable Dynamic Testing of a Single-span Bridge Using Radar Interferometry and Videometry Measurements
- DOI：10.1515/jag-2015-0030
- 证据：abstract；摘要：combined DIC and GBMI; modal parameters; PSD and STFT; cable tension。
- 输入→算法→输出：GBMI+DIC位移→PSD/STFT与模态参数→桥面/索振动及索力
- 已有基础/论文增量：摘要明确将GBMI与DIC联合做模态/索力/PSD/STFT分析，是多点测量与多传感器频谱融合模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355的带宽、同步、目标几何和噪声重新标定。
- 模块：M15, M16, M19

### R1371｜A Radar-Enabled Collaborative Sensor Network Integrating COTS Technology for Surveillance and Tracking
- DOI：10.3390/s120201336
- 证据：abstract；题名：radar-enabled collaborative sensor network for surveillance and tracking。
- 输入→算法→输出：COTS雷达网络→协同检测/跟踪→目标轨迹
- 已有基础/论文增量：摘要是雷达协同传感网络用于监视/跟踪，具体链偏目标跟踪，具有跨场景数据关联参考价值。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M18

### R1383｜Magnetic and Radar Sensing for Multimodal Remote Health Monitoring
- DOI：10.1109/jsen.2018.2872894
- 证据：abstract；题名：magnetic and radar sensing for multimodal remote health monitoring。
- 输入→算法→输出：雷达+磁传感→多模态融合→远程健康指标
- 已有基础/论文增量：摘要明确磁传感与雷达多模态健康监测融合，可借鉴跨传感状态融合结构。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M19

### R1401｜Embedded DSP-Based Telehealth Radar System for Remote In-Door Fall Detection
- DOI：10.1109/jbhi.2014.2361252
- 证据：abstract；题名：embedded DSP radar system for remote fall detection。
- 输入→算法→输出：雷达回波→DSP检测/事件跟踪→跌倒告警
- 已有基础/论文增量：摘要明确嵌入式DSP雷达跌倒检测，涉及实时检测与事件跟踪。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M18

### R1404｜Smart guided missile using accelerometer and gyroscope based on backpropagation neural network method for optimal control output feedback
- DOI：10.14203/j.mev.2020.v11.55-63
- 证据：abstract；摘要方法证据：The right method can provide a high level of accuracy in controlling missiles to the targeted object.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The right method can provide a high level of accuracy in controlling missiles to the targeted object.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1500｜Monitoring Line-Infrastructure With Multisensor SAR Interferometry: Products and Performance Assessment Metrics
- DOI：10.1109/jstars.2018.2803074
- 证据：abstract；摘要方法证据：Here, we propose several new monitoring products and quality metrics for a-priori and a-posteriori performance assessment using multisensor InSAR.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Here, we propose several new monitoring products and quality metrics for a-priori and a-posteriori performance assessment using multisensor InSAR.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1509｜On the Design of Radar Corner Reflectors for Deformation Monitoring in Multi-Frequency InSAR
- DOI：10.3390/rs9070648
- 证据：abstract；题名：radar corner reflectors for deformation monitoring。
- 输入→算法→输出：InSAR回波→角反射器/散射增强→形变测量质量
- 已有基础/论文增量：摘要/题名明确InSAR角反射器设计以增强形变监测散射和质量。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M08, M20

### R1530｜Mining Subsidence Monitoring With Modified Time-Series SAR Interferometry Method Based on the Multi-Level Processing Strategy
- DOI：10.1109/access.2021.3099633
- 证据：abstract；题名：modified time-series SAR interferometry with multi-level processing。
- 输入→算法→输出：多时相SAR→多级时序干涉处理→沉降形变
- 已有基础/论文增量：摘要明确多级时序SAR干涉处理用于采矿沉降，属于时序相位/质量模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R1542｜Monitoring of deforestation events in the tropics using multidimensional features of Sentinel 1 radar data
- DOI：10.3389/ffgc.2023.1257806
- 证据：abstract；摘要方法证据：Currently, most SAR image-based deforestation identification uses manually supervised methods, which rely on high quality and sufficient samples.
- 输入→算法→输出：雷达原始回波/慢时间IQ→Currently, most SAR image-based deforestation identification uses manually supervised methods, which rely on high quality and sufficient samples.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1566｜Structural Health Monitoring of Flood Protection Structures through Improved InSAR Processing
- DOI：10.1016/j.prostr.2026.08.039
- 证据：abstract；摘要：persistent/distributed scatterers and reliability strategies。
- 输入→算法→输出：InSAR→PS/DS散射点筛选+频段/季节质量策略→结构形变
- 已有基础/论文增量：摘要明确PS/DS散射点、频段和季节策略提升InSAR测点密度与可靠性。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R1569｜Microwave Imaging and Sensing Techniques for Breast Cancer Detection
- DOI：10.3390/mi14071462
- 证据：abstract；摘要方法证据：The manuscript also delves into integrating machine learning algorithms to enhance the accuracy and efficiency of microwave imaging in breast cancer detection.
- 输入→算法→输出：雷达原始回波/慢时间IQ→The manuscript also delves into integrating machine learning algorithms to enhance the accuracy and efficiency of microwave imaging in breast cancer detection.→目标/运动特征
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1578｜Remote monitoring of a concrete bridge using PSInSAR
- DOI：10.1002/cepa.2189
- 证据：abstract；题名：remote monitoring concrete bridge using PSInSAR。
- 输入→算法→输出：PSInSAR→散射点时序→桥梁位移
- 已有基础/论文增量：题名/摘要确认PSInSAR桥梁位移时序，可迁移散射点和相位质量流程。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R1590｜Using TerraSAR X-Band and Sentinel-1 C-Band SAR Interferometry for Deformation Along Beijing-Tianjin Intercity Railway Analysis
- DOI：10.1109/jstars.2021.3076244
- 证据：abstract；题名：TerraSAR X and Sentinel-1 C-band interferometry for railway deformation。
- 输入→算法→输出：X/C-band SAR→双频干涉时序→铁路沿线形变
- 已有基础/论文增量：摘要/题名明确TerraSAR-X与Sentinel-1双频InSAR铁路形变分析，属于多频相位质量对照。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M06, M20

### R1602｜Landslide Prediction Method Based on a Ground-Based Micro-Deformation Monitoring Radar
- DOI：10.3390/rs12081230
- 证据：abstract；摘要方法证据：As remote sensing methods have received a lot of attention, ground-based micro- deformation monitoring radars have been widely used in recent years due to their wide range, high accuracy, and all-day monitoring capability.
- 输入→算法→输出：雷达原始回波/慢时间IQ→As remote sensing methods have received a lot of attention, ground-based micro- deformation monitoring radars have been widely used in recent years due to their wide range, high accuracy, and all-day monitoring capability.→结构振动/位移/频率
- 已有基础/论文增量：摘要明确描述具体雷达处理链（M20）；记录为可迁移模块，不声称论文首创。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定；仅迁移处理思想。
- 模块：M20

### R1608｜Loudspeaker Analysis: A Radar Based Approach
- DOI：10.1109/jsen.2019.2946987
- 证据：abstract；题名：loudspeaker analysis: radar based approach。
- 输入→算法→输出：雷达回波→Doppler/相位振动→扬声器振幅频率
- 已有基础/论文增量：摘要为雷达测量扬声器振动，使用Doppler/相位链可迁移声振测量。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M05

### R1614｜Classification of Ground Targets Based on Radar Micro-Doppler Signatures Using Deep Learning and Conventional Supervised Learning Methods
- DOI：10.13164/re.2018.0835
- 证据：abstract；摘要：STFT on raw Doppler radar; DCNN/SVM/NB comparison。
- 输入→算法→输出：K-band Doppler→STFT micro-Doppler→监督/深度分类
- 已有基础/论文增量：摘要明确micro-Doppler经STFT后用DCNN/SVM分类，保留时频特征模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M02, M16

### R1620｜Peak Detection Algorithm for Vital Sign Detection Using Doppler Radar Sensors
- DOI：10.3390/s19071575
- 证据：abstract；题名：peak detection algorithm for vital signs using Doppler radar。
- 输入→算法→输出：Doppler生命体征→峰值检测→心肺频率
- 已有基础/论文增量：题名明确Doppler雷达生命体征峰值检测，属于频谱候选检测模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M16

### R1647｜Deep Radar Perception Network With RTK Supervision for Slow-Moving UAV Detection
- DOI：10.1109/tim.2026.3687291
- 证据：abstract；题名：Deep Radar Perception Network with RTK supervision。
- 输入→算法→输出：雷达点云→深度检测+RTK监督→UAV目标
- 已有基础/论文增量：摘要明确深度雷达感知网络结合RTK监督做慢速UAV检测，属于目标检测/跟踪。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：需按IWR/ADXL355带宽、同步、几何和噪声重新标定。
- 模块：M10, M18

### R1770｜Kim et al., 2022, FMCW Radar Estimation Algorithm with High Resolution and Low Complexity Based on Reduced Search Area
- DOI：10.3390/s22031202
- 证据：abstract；Crossref abstract evidence: Crossref摘要：FFT与MUSIC取长处，在reduced search area上降低复杂度并保持高分辨。 DOI: https://doi.org/10.3390/s22031202
- 输入→算法→输出：FMCW→FFT粗估候选→缩小搜索区域→MUSIC高分辨参数估计
- 已有基础/论文增量：摘要/题名明确为先FFT再MUSIC的高分辨低复杂度FMCW参数估计，属于可迁移的距离/超分辨模块。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：MUSIC对协方差、SNR和目标数敏感；用于振动时需再接相位连续跟踪。
- 模块：M01, M12

### R1773｜Enhanced Beamspace MUSIC for Cost-Effective FMCW Automotive Radar
- DOI：10.1049/iet-rsn.2019.0342
- 证据：abstract；Crossref abstract evidence: Crossref摘要：low-complexity beamspace MUSIC；prior beamformer、modified MUSIC、sub-matrix averaging、Toeplitz recovery。 DOI: https://doi.org/10.1049/iet-rsn.2019.0342
- 输入→算法→输出：FMCW阵列→先验beamspace→改进MUSIC→子矩阵平均/Toeplitz恢复→DOA
- 已有基础/论文增量：摘要明确提出利用先验设计 beamformer、改进 MUSIC、子矩阵平均和 Toeplitz 恢复以提升低SNR单快拍DOA，算法可迁移到角度分离。 仅按当前摘要证据归档，不声称论文首创。
- 迁移到 IWR/ADXL355：汽车雷达的小孔径/单快拍条件与结构测振不同；需验证角度估计相位保真而非只看检测精度。
- 模块：M11, M12

