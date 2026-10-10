# 全文核验优先队列（阶段性）

候选来源：659 条有摘要证据的 `module` 记录；按结构直接相关、雷达–加速度融合、相位/解缠、阵列与质量评估关键词排序。该排序是工作队列，不是论文质量排名。

历史全文/公开记录审计索引见 [`MODULE_INDEX_FULLTEXT_AUDITED_V2.md`](../review_2026_10_08/MODULE_INDEX_FULLTEXT_AUDITED_V2.md)；当前最终一致性审计索引见 [`MODULE_INDEX_FINAL.md`](../review_2026_10_08/MODULE_INDEX_FINAL.md)：700 module、566 context、508 exclude、5 pending。三批 pending 审计和最后 R1691/R1727 补证据见 [`final_audit/README.md`](../final_audit/README.md)。

模块如何落到 IWR+ADXL355 的测量链路，以及哪些位置更适合定义胶水方法，见 [模块迁移矩阵](method_transfer_matrix.md)。

已完成第一批结构直接相关全文核验：实际读取 29 个本地 PDF（27 个可提取正文），形成 22 张证据卡，见 [结构直接相关全文证据](structural_direct.md) 和机器可读版本 [structural_direct_evidence.jsonl](structural_direct_evidence.jsonl)。这批证据不改写原始 `decisions_N.jsonl` 的判定；其中 20 条带联合候选 R 编号，2 条为本地全文补充条目。

本目录 `pdfs/` 中另有 12 个可提取 PDF，均已通过 `pdftotext` 首页校验；3 个服务器错误下载（HTML/空文件）移入 `rejected_downloads/`，不作为全文证据。校验记录见 `final_audit/download_validation.jsonl`。

另外，93 条 `pending` 中有一批虽然还没有摘要级模块证据，但题名直接命中“加速度辅助解缠、雷达–加速度融合、桥梁位移、multi-chirp 解缠”等高价值主题，已单独列在 `priority_pending.jsonl`。其中 R0001、R0007、R0202、R1715、R1719 是雷达–加速度融合主线的优先全文核验对象；它们不能计入 659 条 `module`，直到补齐摘要或全文证据。

已经完成的全文初核结果见：[结构直接相关](structural_direct.md)、[可迁移模块](transferable_modules.md)。两份文件都区分了论文作者声称的组合增量、已有基础算子和迁移限制；数值也区分了终点偏差、峰峰值 RMSE、频率误差和标称精度。

雷达–加速度融合主线另见 [radar_accel_fusion.md](radar_accel_fusion.md)。其中 R0007 是目前本地正文里与 ADXL355 最直接的先例；R0001、R0202、R1719 等的补充证据见 [pending_upgrade_evidence.md](pending_upgrade_evidence.md)，其证据等级不同，不能一律当作本地全文。

全文核验后建议升级的记录单独写入 `fulltext_upgrade_recommendations.jsonl`。这些建议暂不改写 1,779 条阶段性合并统计，避免把“摘要阶段计数”和“全文升级计数”混在一起。

应用首批 13 条升级建议后的独立索引是 `../review_2026_10_08/MODULE_INDEX_FULLTEXT_UPGRADED.md`，当前为 672 条 `module`；它仍保留每条记录的证据等级，不能理解为 672 篇都已完成全文精读。

|优先级|ID|年份|论文|模块|标签|排序理由|
|---:|---|---:|---|---|---|---|
|1|R0397|2021|[Transport Infrastructure SHM Using Integrated SAR Data and On-Site Vibrational Acquisitions: “Ponte Della Musica–Armando Trovajoli” Case Study](https://doi.org/10.3390/app11146504)|M14/M16|array,fusion,phase|融合/辅助传感器；相位/解缠；阵列或质量|
|2|R1417|2023|[A Vibration Sensing Device Using a Six-Axis IMU and an Optimized Beam Structure for Activity Monitoring](https://doi.org/10.3390/s23198045)|M19/M20|fusion,quality|融合/辅助传感器；阵列或质量|
|3|R0553|2025|[A method for reconstructing the dynamic displacement of floating structures based on acceleration measurements and comparison with data-reconstruction techniques](https://doi.org/10.1038/s44172-025-00402-9)|M19|fusion,phase|融合/辅助传感器；相位/解缠|
|4|R0709|2025|[Improving the Accuracy of Ground Displacement Estimation Using IMU with Low-Pass Butterworth Filter](https://doi.org/10.35877/jetech4580)|M19/M08|fusion,phase|融合/辅助传感器；相位/解缠|
|5|R0328|2026|[Design, Development, and Laboratory Validation of a Low-Cost Multi-Sensor System for Bridge Structural Health Monitoring with Scour-Related Environmental Sensing](https://doi.org/10.3390/s26185957)|M19/M20|fusion|融合/辅助传感器|
|6|R0418|2023|[Accuracy Analysis and Appropriate Strategy for Determining Dynamic and Quasi-Static Bridge Structural Response Using Simultaneous Measurements with Two Real Aperture Ground-Based Radars](https://doi.org/10.3390/rs15030837)|M14/M20|fusion,phase|融合/辅助传感器；相位/解缠|
|7|R0310|2022|[Theoretical derivation and experimental investigation of dynamic displacement reconstruction based on data fusion for beam structures](https://doi.org/10.1038/s41598-022-24449-2)|M19/M20|fusion|融合/辅助传感器|
|8|R1291|2010|[Ambient vibration testing of bridges by non-contact microwave interferometer](https://doi.org/10.1109/maes.2010.5463952)|M01/M05/M16|fusion,phase|融合/辅助传感器；相位/解缠|
|9|R0340|2023|[Comparison between Compressive Sensing and Non-Uniform Array for a MIMO GBSAR with Elevation Resolution: Simulations and Experimental Tests](https://doi.org/10.3390/electronics12051100)|M11/M13|array,fusion,phase|融合/辅助传感器；相位/解缠；阵列或质量|
|10|R0376|2012|[Ambient vibration monitoring of slender structures by microwave interferometer remote sensing](https://doi.org/10.1515/jag-2012-0029)|M01/M05/M16|fusion,phase|融合/辅助传感器；相位/解缠|
|11|R0370|2023|[STRUCTURAL HEALTH MONITORING OF CURVED ROADWAY BRIDGES THROUGH SATELLITE RADAR INTERFEROMETRY AND COLLAPSE SIMULATION](https://doi.org/10.1002/cepa.2201)|M14/M16|fusion,phase|融合/辅助传感器；相位/解缠|
|12|R0715|2013|[A localization algorithm for railway vehicles based on sensor fusion between tachometers and inertial measurement units](https://doi.org/10.1177/0954409713481769)|M19|fusion,phase|融合/辅助传感器；相位/解缠|
|13|R0670|2020|[Design and Testing of Inertial System for Landslide Displacement Distribution Measurement](https://doi.org/10.3390/s20247154)|M19/M20|fusion|融合/辅助传感器|
|14|R1026|2026|[Multi-Sensor Mobile Laser Doppler Vibrometry for Internal Damage Detection in Reinforced Concrete Structures](https://doi.org/10.3390/s26175612)|M02/M16|fusion,phase|融合/辅助传感器；相位/解缠|
|15|R1288|2013|Vibration Monitoring and Live Load Tests of Civil Infrastructure with Interferometric Radar|M01/M05/M16|phase|相位/解缠|
|16|R1500|2018|[Monitoring Line-Infrastructure With Multisensor SAR Interferometry: Products and Performance Assessment Metrics](https://doi.org/10.1109/jstars.2018.2803074)|M20|fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量|
|17|R0385|2019|[Effective Processing of Radar Data for Bridge Damage Detection](https://doi.org/10.1155/2019/2621092)|M08/M16|fusion,phase|融合/辅助传感器；相位/解缠|
|18|R0393|2014|[Comparison of natural and artificial forcing to study the dynamic behaviour of bell towers in low wind context by means of ground-based radar interferometry: the case of the Leaning Tower in Pisa](https://doi.org/10.1088/1742-2132/11/5/055004)|M16|fusion,phase|融合/辅助传感器；相位/解缠|
|19|R0034|2015|[A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring](https://doi.org/10.3390/s150407412)|M01/M05/M09|phase,quality|相位/解缠；阵列或质量|
|20|R0688|2024|[Acceleration-Based Low-Cost CW Radar System for Real-Time Elderly Fall Detection](https://doi.org/10.1109/jerm.2024.3368688)|M19/M05|fusion,phase|融合/辅助传感器；相位/解缠|
|21|R0761|2024|[A Novel Data Fusion Method to Estimate Bridge Acceleration with Surrogate Inclination Mode Shapes through Independent Component Analysis](https://doi.org/10.3390/app14188556)|M17/M19|fusion|融合/辅助传感器|
|22|R0665|2023|[Deformation Monitoring of Monopole Communication Towers Based on Multi-Source Data Fusion](https://doi.org/10.3390/buildings13112709)|M19/M20|fusion|融合/辅助传感器|
|23|R0201|2025|[Robust Vibration Displacement Extraction for FMCW Radar by Incorporating Optimized Beat Frequency and Maximum Likelihood Estimation](https://doi.org/10.1109/jsen.2025.3569403)|M01/M05/M20|fusion,quality|融合/辅助传感器；阵列或质量|
|24|R1594|2013|[Design and Analysis of a 60-GHz CMOS Doppler Micro-Radar System-in-Package for Vital-Sign and Vibration Detection](https://doi.org/10.1109/tmtt.2013.2247620)|M02/M05|fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量|
|25|R0424|2024|[A Laboratory test aimed at demostrating the potential of an Interferometric Radar to estimate the Seismic Risk of damaged buildings](https://doi.org/10.58286/29772)|M16|phase|相位/解缠|
|26|R0061|2022|[Fast Displacement Estimation of Multiple Close Targets with MIMO Radar and MUSICAPES Method](https://doi.org/10.3390/rs14092005)|M11/M12/M09|array,fusion,phase|融合/辅助传感器；相位/解缠；阵列或质量|
|27|R0952|2020|[Design and Validation of Android Smartphone Based Wireless Structural Vibration Monitoring System](https://doi.org/10.3390/s20174799)|M19/M20|fusion,phase|融合/辅助传感器；相位/解缠|
|28|R0301|2026|[MRGF: A robust SLAM Framework based on Millimeter wave Radar and GNSS Fusion in Harsh Environments](https://doi.org/10.5194/isprs-archives-xlix-b1-2026-647-2026)|M19/M18|fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量|
|29|R1372|2024|[Sensor Fusion and Virtual Sensor Design for Enhanced Multi-Sensor Data Accuracy in Autonomous Systems](https://doi.org/10.63503/j.ijssic.2024.31)|M19/M20|fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量|
|30|R0601|2019|[A Comparison of Strain-Based Methods for the Evaluation of the Relative Displacement of Beam-Like Structures](https://doi.org/10.3389/fbuil.2019.00118)|M19/M20|fusion|融合/辅助传感器|
|31|R1399|2017|[A Framework for Occupancy Tracking in a Building via Structural Dynamics Sensing of Footstep Vibrations](https://doi.org/10.3389/fbuil.2017.00065)|M17|fusion|融合/辅助传感器|
|32|R1256|2022|[GB-RAR Deformation Information Estimation of High-Speed Railway Bridge in Consideration of the Effects of Colored Noise](https://doi.org/10.3390/app122010504)|M08/M20|fusion,quality|融合/辅助传感器；阵列或质量|
|33|R0427|2024|[Displacement prediction for long-span bridges via limited remote sensing images: An adaptive ensemble regression method](https://doi.org/10.1016/j.measurement.2024.116567)|M17|fusion|融合/辅助传感器|
|34|R0510|2024|[Thermal deformation monitoring of a highway bridge: combined analysis of geodetic and satellite-based InSAR measurements with structural simulations](https://doi.org/10.1007/s13349-024-00779-9)|M06/M20|fusion|融合/辅助传感器|
|35|R0970|2024|[A Review on the Latest Advancements and Innovation Trends in Vibration-Based Structural Health Monitoring (SHM) Techniques for Improved Maintenance of Steel Slit Damper (SSD)](https://doi.org/10.1109/access.2024.3381625)|M16|phase|相位/解缠|
|36|R0027|2024|[Millimeter-Wave Radar-Based Identity Recognition Algorithm Built on Multimodal Fusion](https://doi.org/10.3390/s24134051)|M19|cross-domain,fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量；跨域可迁移|
|37|R0511|2026|[Dynamic Displacement Monitoring of Bridges Using Dual Monostatic Ground-Based MIMO Radar Interferometry](https://doi.org/10.1109/access.2026.3667140)|M11/M14/M08|array,phase|相位/解缠；阵列或质量|
|38|R1174|2026|[Simulation Of Radar-Based Object Detection For Railway Safety In Foggy Conditions Using MATLAB](https://doi.org/10.29284/ijasis.12.1s.2026.496-511)|M10|fusion,phase|融合/辅助传感器；相位/解缠|
|39|R1585|2026|[Sounding of the deforming solid earth surface: new opportunities for spaceborne Differential SAR Interferometry techniques to detect and monitor displacements affecting the ground and the built-up environment](https://doi.org/10.1007/s12210-026-01452-7)|M08/M15|fusion,phase|融合/辅助传感器；相位/解缠|
|40|R1207|2025|[Discontinuous InSAR Monitoring of Infrastructure Using W-band Ground-Based MIMO Radar](https://doi.org/10.1109/jstars.2025.3620959)|M08/M15|array,phase|相位/解缠；阵列或质量|
|41|R0353|2022|[A Novel GB-SAR System Based on TD-MIMO for High-Precision Bridge Vibration Monitoring](https://doi.org/10.3390/rs14246383)|M11/M20|array,phase|相位/解缠；阵列或质量|
|42|R1069|2022|[Methodology for the determination of human respiration rate by using Doppler radar and Empirical Modal Decomposition](https://doi.org/10.1038/s41598-022-12726-z)|M17|fusion,phase|融合/辅助传感器；相位/解缠|
|43|R0373|2020|[Dynamic Modal Identification of Telecommunication Towers Using Ground Based Radar Interferometry](https://doi.org/10.3390/rs12071211)|M01/M05/M16|phase|相位/解缠|
|44|R1486|2018|[Microwave Radar Interferometry as a Cost-Efficient Method of Monitoring the Structural Health of Bridges in New Zealand](https://doi.org/10.1080/10168664.2018.1461538)|M01/M05/M16|phase|相位/解缠|
|45|R0381|2026|[Long-Term Dynamic Monitoring for Structural Health Assessment of Bisantis Bridge](https://doi.org/10.1016/j.prostr.2026.06.054)|M16/M19|fusion,quality|融合/辅助传感器；阵列或质量|
|46|R0508|2026|[Experimental Accuracy Evaluation of UAV-Based Homography for Static and Dynamic Displacement Monitoring of Structures](https://doi.org/10.3390/s26051593)|M17/M20|cross-domain,phase,quality|相位/解缠；阵列或质量；跨域可迁移|
|47|R0482|2025|[Real-Time Bridge Dynamic Deflection Monitoring Using 5G-Integrated Sensing and Communication](https://doi.org/10.5194/isprs-archives-xlviii-g-2025-987-2025)|M08/M19|fusion|融合/辅助传感器|
|48|R1396|2025|[Rail Maintenance, Sensor Systems and Digitalization: A Comprehensive Review](https://doi.org/10.3390/futuretransp5030083)|M16|fusion|融合/辅助传感器|
|49|R1144|2024|[Displacement Evaluation by mmWave FMCW Radars: Method and Performance Metrics](https://doi.org/10.1109/tim.2024.3421440)|M01/M05/M20|cross-domain,phase|相位/解缠；跨域可迁移|
|50|R0457|2020|[GB-SAR in the Diagnosis of Critical City Infrastructure—A Case Study of a Load Test on the Long Tram Extradosed Bridge](https://doi.org/10.3390/rs12203361)|M01/M05/M16|||
|51|R1326|2016|[Deck and Cable Dynamic Testing of a Single-span Bridge Using Radar Interferometry and Videometry Measurements](https://doi.org/10.1515/jag-2015-0030)|M15/M16/M19|fusion,phase|融合/辅助传感器；相位/解缠|
|52|R0324|2025|[A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring](https://doi.org/10.1016/j.ymssp.2025.112777)|M02/M06|array,phase|相位/解缠；阵列或质量|
|53|R0461|2024|[A Three-Dimensional Deformation Monitoring Method: Combining Optical Deformation Monitoring Based on Regression Models and GB-SAR Interferometry](https://doi.org/10.3390/s24061754)|M14/M19|fusion,phase|融合/辅助传感器；相位/解缠|
|54|R1300|2021|[A Simplified Methodology for Condition Assessment of Bridge Bearings Using Vibration Based Structural Health Monitoring Techniques](https://doi.org/10.1142/s0219455421501339)|M16|phase|相位/解缠|
|55|R1303|2019|[Research and Implementations of Structural Monitoring for Bridges and Buildings in Japan](https://doi.org/10.1016/j.eng.2019.09.006)|M16|phase|相位/解缠|
|56|R0358|2016|[Application of Interferometry Method for Dynamic Continuous Testing of Bridges](https://doi.org/10.3311/ppci.8679)|M01/M05/M16|phase|相位/解缠|
|57|R1663|2012|[An interferometric radar for displacement measurement and its application in civil engineering structures](https://doi.org/10.1117/12.917292)|M01/M05|phase|相位/解缠|
|58|R1297|2010|Innovations in Bridge Superstructure Condition Assessment with Sonic and Radar Methods|M16|phase|相位/解缠|
|59|R0029|2026|[Acoustic Source Fusion-Based Passive Eavesdropping System Using Millimeter-Wave Radar](https://doi.org/10.3390/app16084009)|M08/M19|fusion,quality|融合/辅助传感器；阵列或质量|
|60|R0171|2026|[Experimental validation of spaceborne SAR for measurement of structural vibrations](https://doi.org/10.58286/33941)|M02/M16|cross-domain,phase,quality|相位/解缠；阵列或质量；跨域可迁移|
|61|R0208|2026|[Adaptive MTI-Enhanced Range–Phase NHA for Robust FMCW Radar Micro-Displacement Sensing in Dynamic Environments](https://doi.org/10.1109/access.2026.3710261)|M08/M01/M05|phase,quality|相位/解缠；阵列或质量|
|62|R0802|2025|[Phase Noise Model Construction and Denoising Method for Dynamic Infrastructure Measurement in 5G Base Station](https://doi.org/10.5194/isprs-archives-xlviii-g-2025-1523-2025)|M08/M20|phase,quality|相位/解缠；阵列或质量|
|63|R0055|2026|[Low-Cost FMCW Radar for Full-Field Vibration Monitoring of Bridges](https://doi.org/10.58286/33939)|M01/M11/M15|phase|相位/解缠|
|64|R0433|2026|[Interpreting satellite radar for bridges: integrating MT-InSAR with physics-based and data-driven models for scalable structural health monitoring](https://doi.org/10.1093/iti/liag013)|M08/M17|phase|相位/解缠|
|65|R1654|2026|[Analysis of Flow‐Induced Vibrations in an Air Compressor Piping System](https://doi.org/10.1155/vib/3015801)|M16|fusion|融合/辅助传感器|
|66|R0016|2025|[Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring](https://doi.org/10.1038/s41598-025-31631-9)|M01/M05/M20|phase|相位/解缠|
|67|R1014|2025|[GBSAR Geocoding Based on Bayes Theorem](https://doi.org/10.4018/ijitsa.380648)|M14/M20|fusion|融合/辅助传感器|
|68|R1420|2025|[VoiceFormer: Fusing Non-Acoustic Motion Sensors for High-Fidelity Voice Synthesis in Mobile Devices](https://doi.org/10.1145/3779062)|M19|cross-domain,fusion|融合/辅助传感器；跨域可迁移|
|69|R0730|2024|[On the fusion between interferometric satellite data and in situ measurements for the monitoring of built heritage](https://doi.org/10.58286/29789)|M19/M20|fusion,phase|融合/辅助传感器；相位/解缠|
|70|R0475|2023|[Elimination of Thermal Effects from Limited Structural Displacements Based on Remote Sensing by Machine Learning Techniques](https://doi.org/10.3390/rs15123095)|M20|phase|相位/解缠|
|71|R1510|2023|[An Influence of Snow Covers on the Radar Interferometry Observations of Industrial Infrastructure: Norilsk Thermal Power Plant Case](https://doi.org/10.3390/rs15030654)|M20|phase|相位/解缠|
|72|R1639|2023|[Experimental Investigation of Vibration Isolator for Large Aperture Electromagnetic MEMS Micromirror](https://doi.org/10.3390/mi14081490)|M20|fusion|融合/辅助传感器|
|73|R0049|2022|[Structural displacement monitoring using ground-based synthetic aperture radar](https://doi.org/10.1016/j.jag.2022.103144)|M01/M11/M14|phase|相位/解缠|
|74|R0460|2022|[Synchronisation of Contactless Vibration Monitoring Methods](https://doi.org/10.2507/ijsimm21-1-594)|M01/M20|fusion|融合/辅助传感器|
|75|R1307|2026|[Integrated Radar and Data-Driven Framework for Modal Analysis and Operational Assessment of High-Speed Railway Bridges](https://doi.org/10.1142/s0219455427503342)|M16/M17/M08|quality|阵列或质量|
|76|R0421|2024|[An Innovative Gradual De-Noising Method for Ground-Based Synthetic Aperture Radar Bridge Deflection Measurement](https://doi.org/10.3390/app142411871)|M08/M17|quality|阵列或质量|
|77|R1339|2024|[Lessons from Bridge Structural Health Monitoring (SHM) and Their Implications for the Development of Cyber-Physical Systems](https://doi.org/10.3390/infrastructures9020030)|M20|quality|阵列或质量|
|78|R0355|2025|[Dynamic Displacement Estimation of Bridge Using MIMO Radar Interferometry From an Oscillating Platform](https://doi.org/10.1109/tgrs.2025.3594286)|M08/M11/M14|array,phase|相位/解缠；阵列或质量|
|79|R0184|2023|[INTERFEROMETRIC PROCESSING OF A DEVELOPED MIMO GBSAR FOR DISPLACEMENT MONITORING](https://doi.org/10.5194/isprs-annals-x-4-w1-2022-301-2023)|M09/M11/M15|array,phase|相位/解缠；阵列或质量|
|80|R0158|2022|[Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar](https://doi.org/10.1109/jerm.2022.3143431)|M10/M11/M14|array,cross-domain,fusion,phase|融合/辅助传感器；相位/解缠；阵列或质量；跨域可迁移|
|81|R0931|2020|[Adaptive Displacement Calibration Strategies for Field Structural Health Monitoring Based on Doppler Radars](https://doi.org/10.1109/tim.2020.2982233)|M05/M06/M20|phase|相位/解缠|
|82|R1394|2019|[FMCW radar and inertial sensing synergy for assisted living](https://doi.org/10.1049/joe.2019.0558)|M19/M05|fusion|融合/辅助传感器|
|83|R0790|2017|[Software Defined Doppler Radar as a Contactless Multipurpose Microwave Sensor for Vibrations Monitoring](https://doi.org/10.3390/s17010115)|M02/M05|fusion|融合/辅助传感器|
|84|R1402|2015|[Multi-Sensor Data Fusion Identification for Shearer Cutting Conditions Based on Parallel Quasi-Newton Neural Networks and the Dempster-Shafer Theory](https://doi.org/10.3390/s151128772)|M19/M17|fusion|融合/辅助传感器|
|85|R0736|2010|[Decision Fusion for Structural Damage Detection: Numerical and Experimental Studies](https://doi.org/10.1155/2010/820762)|M17/M19|fusion|融合/辅助传感器|
|86|R1087|2026|[Robust Estimation of Noncontact Vital Sign Sensing Data under Multi-source Dynamic Interference Scenarios](https://doi.org/10.18494/sam5993)|M08/M20|cross-domain,fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量；跨域可迁移|
|87|R1160|2026|[Radar-Enhanced Multimodal Speech Recognition Under Occlusion and Noise: Methodology and Experimental Analysis](https://doi.org/10.1109/jsen.2026.3707509)|M08/M19|cross-domain,fusion,quality|融合/辅助传感器；阵列或质量；跨域可迁移|
|88|R0739|2025|[Multimodal Fall Detection Using Spatial–Temporal Attention and Bi-LSTM-Based Feature Fusion](https://doi.org/10.3390/fi17040173)|M17/M19|fusion,quality|融合/辅助传感器；阵列或质量|
|89|R1480|2024|[Noise Reduction Techniques in Adas Sensor Data Management: Methods and Comparative Analysis](https://doi.org/10.14569/ijacsa.2024.0150868)|M08|fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量|
|90|R0070|2016|[Time-Varying Vocal Folds Vibration Detection Using a 24 GHz Portable Auditory Radar](https://doi.org/10.3390/s16081181)|M02/M05|array,cross-domain,phase,quality|相位/解缠；阵列或质量；跨域可迁移|
|91|R0514|2026|[Ground-based interferometric radar for bridge dynamic system identification: A multi-domain operational modal analysis and integrated method selection framework](https://doi.org/10.1016/j.ndteint.2026.103649)|M16/M20|phase|相位/解缠|
|92|R0974|2026|[GaRLILEO: Gravity-aligned radar-leg-inertial enhanced odometry](https://doi.org/10.1177/02783649261457941)|M18/M19|fusion|融合/辅助传感器|
|93|R1048|2026|[JuRa: The Juventas Radar on Hera Mission to Probe Internal Structure of Didymos and Dimorphos Asteroids](https://doi.org/10.1007/s11214-026-01324-4)|M15|fusion|融合/辅助传感器|
|94|R1439|2026|[Evidence-theoretic multi-sensor fusion with spatial semantic coupling for real-time hazard assessment in dynamic construction environments](https://doi.org/10.1038/s41598-026-69867-8)|M19/M20|fusion|融合/辅助传感器|
|95|R0269|2025|[Loosely coupled 4D-Radar-Inertial Odometry for Ground Robots](https://doi.org/10.1007/s10846-025-02301-9)|M18/M19/M20|fusion|融合/辅助传感器|
|96|R0299|2025|[MotionLeaf: Fine-grained Multi-leaf Damped Vibration Monitoring for Plant Water Stress Using Cost-effective mmWave Sensors](https://doi.org/10.1145/3749547)|M05/M17|phase|相位/解缠|
|97|R0469|2025|[Monitoring of a multi‐span prestressed concrete bridge using satellite interferometric data and comparison with on‐site sensor results](https://doi.org/10.1002/suco.202400881)|M14/M16|phase|相位/解缠|
|98|R0513|2024|[Measurement Refinements of Ground-Based Radar Interferometry in Bridge Load Test Monitoring: Comprehensive Analysis on a Multi-Span Cable-Stayed Bridge](https://doi.org/10.3390/rs16111882)|M06/M14/M20|phase|相位/解缠|
|99|R1173|2024|[A Fusion Localization System for Security Robots Based on Millimeter Wave Radar and Inertial Sensors](https://doi.org/10.3390/s24237551)|M18/M19|fusion|融合/辅助传感器|
|100|R1198|2024|[Quantitative Assessment of Fall Risk in the Elderly Through Fusion of Millimeter-Wave Radar Imaging and Trajectory Features](https://doi.org/10.1109/access.2024.3355927)|M17/M19|fusion|融合/辅助传感器|
|101|R1393|2024|[Advanced Fall Detection System for Elderly Individuals Using Deep Learning and Multi-Sensor Fusion](https://doi.org/10.17148/iarjset.2024.11737)|M17/M19|fusion|融合/辅助传感器|
|102|R0504|2023|[Monitoring Displacements and Damage Detection through Satellite MT-InSAR Techniques: A New Methodology and Application to a Case Study in Rome (Italy)](https://doi.org/10.3390/rs15051177)|M06/M20|phase|相位/解缠|
|103|R1089|2023|[PmTrack](https://doi.org/10.1145/3631433)|M10/M18/M19|fusion|融合/辅助传感器|
|104|R0649|2022|[Multi-Sensor Data Fusion Approach for Kinematic Quantities](https://doi.org/10.3390/en15082916)|M19/M20|fusion|融合/辅助传感器|
|105|R0757|2022|[Structure Strength Dynamic Strain Measurement Acquisition System Based on Data Fusion](https://doi.org/10.1155/2022/9689404)|M19|fusion|融合/辅助传感器|
|106|R1600|2022|[Micro-Doppler Feature Extraction of Rotating Structures of Aircraft Targets with Terahertz Radar](https://doi.org/10.3390/rs14163856)|M02/M17|cross-domain,fusion|融合/辅助传感器；跨域可迁移|
|107|R0234|2021|[Advancing Ground-Based Radar Processing for Bridge Infrastructure Monitoring](https://doi.org/10.3390/s21062172)|M08/M14/M20|||
|108|R0367|2020|[Bridge Monitoring by a Monostatic/Bistatic Interferometric Radar Able to Retrieve the Dynamic 3D Displacement Vector](https://doi.org/10.1109/access.2020.3039381)|M11/M14|array,phase|相位/解缠；阵列或质量|
|109|R0025|2015|[Dynamic and static structural displacement measurement using backscattering DC coupled radar](https://doi.org/10.12989/sss.2015.16.3.521)|M01/M05/M14|||
|110|R0781|2021|[A Non-Contact Vital Signs Detection in a Multi-Channel 77GHz LFMCW Radar System](https://doi.org/10.1109/access.2021.3068480)|M05/M08|cross-domain,fusion,phase,quality|融合/辅助传感器；相位/解缠；阵列或质量；跨域可迁移|
|111|R0438|2020|[A Morphology Filter-Assisted Extreme-Point Symmetric Mode Decomposition (MF-ESMD) Denoising Method for Bridge Dynamic Deflection Based on Ground-Based Microwave Interferometry](https://doi.org/10.1155/2020/8430986)|M08/M17|phase,quality|相位/解缠；阵列或质量|
|112|R0272|2023|[Evaluation of Atmospheric Phase Correction Performance in 79 GHz Ground-Based Radar Interferometry: A Comparison with 17 GHz Ground-Based SAR Data](https://doi.org/10.3390/rs15163931)|M08/M20|array,phase|相位/解缠；阵列或质量|
|113|R1357|2023|[Some Considerations about the Incorporation of Dynamic Parameters in the Structural Health Monitoring Systems of Bridges](https://doi.org/10.3390/app14010033)|M16|||
|114|R1261|2022|[Building 3D reconstruction of TomoSAR using multiple bounce scattering model](https://doi.org/10.1049/ell2.12462)|M15|array,phase|相位/解缠；阵列或质量|
|115|R0359|2021|[The Integration of Two Interferometric Radars for Measuring Dynamic Displacement of Bridges](https://doi.org/10.3390/rs13183668)|M14/M16|phase|相位/解缠|
|116|R0406|2021|[CONVOLUTIONAL NEURAL NETWORKS FOR DETECTING BRIDGE CROSSING EVENTS WITH GROUND-BASED INTERFEROMETRIC RADAR DATA](https://doi.org/10.5194/isprs-annals-v-1-2021-31-2021)|M16|phase|相位/解缠|
|117|R0531|2021|[Time-Series Analysis on Persistent Scatter-Interferometric Synthetic Aperture Radar (PS-InSAR) Derived Displacements of the Hong Kong–Zhuhai–Macao Bridge (HZMB) from Sentinel-1A Observations](https://doi.org/10.3390/rs13040546)|M06/M20|phase|相位/解缠|
|118|R1525|2021|[Structural health monitoring (SHM) and Nondestructive testing (NDT) of slender masonry structures: A practical review](https://doi.org/10.1016/j.conbuildmat.2021.123768)|M16|phase|相位/解缠|
|119|R0617|2020|[Sensor Fusion for Identification of Freezing of Gait Episodes Using Wi-Fi and Radar Imaging](https://doi.org/10.1109/jsen.2020.3004767)|M17/M19|cross-domain,fusion|融合/辅助传感器；跨域可迁移|
|120|R0677|2020|[Multi-Instance Inertial Navigation System for Radar Terrain Imaging](https://doi.org/10.3390/rs12213639)|M18/M19|fusion|融合/辅助传感器|
