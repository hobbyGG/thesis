# 雷达方法模块文献库

本目录服务于“毫米波雷达 + ADXL355 测量磁浮轨道梁振动”的方法拼接。目标是先把已有雷达链路拆成可复用模块，再讨论论文主创新。这里收集的是**方法模块**，不把论文摘要中的所有贡献都当作新方法。

IQ 圆拟合、CW 圆心/DC offset、I/Q 椭圆校正的集中参考索引见
[`01_cw_iq_interferometry/IQ_circle_and_CW_references.md`](01_cw_iq_interferometry/IQ_circle_and_CW_references.md)。

更新时间：2026-10-08。源目录中的 PDF 通过硬链接汇总到本目录，因此不会额外复制一份大文件；`_web_supplements/` 是本轮从作者、机构仓储或公开出版社入口取得的补充全文。原始目录仍保留。

### 统计口径

- 本目录有 **114 个 PDF 文件条目**，因为部分论文同时归入两个模块目录；按文件内容去重后是 **109 篇本地 PDF**。
- 其中 **82 篇来自仓库已有本地资料**；本轮从公开网络补充并保存了 **27 篇本地 PDF**（15 篇 `_web_supplements` 与 12 篇优先全文），包括多弧、QFG、椭圆拟合、CW 去趋势、MODWT 跳变修复、SFCW 静态回波消除、FMCW 超分辨、X-band FMCW、MIMO GBSAR、GBRAR 彩色噪声、GBIR 综述、SFCW 桥梁振动、InSAR 桥梁异常检测和 12 篇检索优先全文等。
- 另外补充了 **40 条 2010 年以后网络调查记录**，其中 24 条仍是在线入口、16 条已保存为本地全文。它们是人工扩展记录，不是从一个已保存的原始候选池筛选出的“最终 40 篇”；其中 7 条 DOI 已在本 README 前文出现，所以相对前文只新增 32 个 DOI 加 1 个无 DOI 的机构入口。随后为 R1722 的关联方法补充了 1 条在线摘要记录，因此下方表格当前显示 41 行；这 1 行不改变原始 40 条扩展表的统计。
- 因此本 README 暂不把 40 条扩展记录换算成整库唯一论文总数：本地 PDF 的 109 篇已经按文件内容去重，但部分旧 PDF 没有在表中登记 DOI/题名，无法可靠地与在线记录做全量题名去重。可复核的 2010+ 雷达方法检索见 [`docs/radar_method_search_2010_2026/README.md`](../../docs/radar_method_search_2010_2026/README.md)：宽检索命中数之和为 24,584，导出的首轮记录按 DOI/work ID 去重后为 1,663 条；独立聚焦检索经题名粗筛和明显边界排除后还有 180 条候选。旧版 [`docs/literature_inventory_2023_2026.md`](../../docs/literature_inventory_2023_2026.md) 中的约 4,219 只是没有原始日志支撑的历史估计。

### 40 条扩展记录与正式筛选的区别

这两个数字不能混用：

- **40 条**：本目录针对 2010 年以后雷达方法模块做的第一批人工扩展表，24 条只有 DOI/官方入口，16 条已有本地全文；它没有保存检索式、原始命中列表和逐条排除理由，因此不能回答“筛选前多少→筛选后 40”。下方实际表格多出的 Zhao et al. 2022 行是后来补录的在线摘要，不计入这 40 条原始扩展表。
- **24,584 → 1,663 → 首轮 A/B 796**：[`docs/radar_method_search_2010_2026/README.md`](../../docs/radar_method_search_2010_2026/README.md) 保存了本次 OpenAlex 查询式、时间戳、API URL、原始 JSONL 和首轮筛选结果。24,584 是 14 个查询命中数之和，1,663 是每个查询导出前 200 条后按 DOI/work ID 的并集，796 是题名/摘要机器辅助首轮 A/B 记录，仍需人工全文筛选。

所以，若问“筛选前有多少”，现在可以给出可复核的本轮数字：宽检索命中数总和 **24,584**，实际导出的去重首轮候选 **1,663**；若限定为本 README 的 40 条原始扩展表，则它仍然没有原始候选池，不能把 40 假装成筛选后样本。

## 阶段性全量方法卡索引

本 README 的本地 PDF 索引保留了已下载全文；2010 年以后检索得到的逐论文方法卡另存于 [MODULE_INDEX_FINAL.md](../../docs/radar_method_search_2010_2026/review_2026_10_08/MODULE_INDEX_FINAL.md)。该当前索引覆盖 1,779 条去重候选，采用 700 条 `module`、566 条 `context`、508 条 `exclude` 和 5 条 `pending`；摘要阶段的 659 条索引与全文审计 v2 快照仍保留供追溯。最终口径把仅有综述/平台/案例背景、没有单一可复用算法的 27 条记录降为 context；每条方法记录写明论文、模块标签、输入→算法→输出、迁移限制和证据层级；同一论文可以带多个模块标签。

整个收集范围、来源分层和剩余缺口见 [collection_manifest.md](../../docs/radar_method_search_2010_2026/collection_manifest.md)。

### 机制级方法目录

论文索引之外，已把方法归并为机制卡，统一入口见[机制级目录索引](catalog/README.md)。当前已有 IQ/相位链 21 张卡（[Markdown](catalog/iq_phase.md)、[JSONL](catalog/iq_phase.jsonl)）、距离/波形/阵列链 25 张卡（[Markdown](catalog/array_range.md)、[JSONL](catalog/array_range.jsonl)）和雷达—加速度—质量控制—模态后处理 18 张卡（[Markdown](catalog/fusion_quality_modal.md)、[JSONL](catalog/fusion_quality_modal.jsonl)），合计 64 张机制卡。每张卡固定记录问题、输入、步骤、输出、前提、失效模式、已有基础、论文组合增量、证据和迁移边界；卡片按机制合并多篇论文，不把“一篇论文”当成“一个新方法”。

对其中最接近本课题的论文，已进一步建立 [结构测振全文证据卡](../../docs/radar_method_search_2010_2026/priority_fulltext/structural_direct.md)、[可迁移模块全文卡](../../docs/radar_method_search_2010_2026/priority_fulltext/transferable_modules.md) 和 [雷达–加速度融合证据卡](../../docs/radar_method_search_2010_2026/priority_fulltext/radar_accel_fusion.md)。这些全文卡区分作者声称的新组合、已有基础算子和迁移条件，不能用摘要阶段的 `module` 标签替代全文核验结论。

摘要阶段 659 条记录的来源归类见 [module_provenance_matrix.md](../../docs/radar_method_search_2010_2026/module_provenance_matrix.md)；最终 700 条判定与 27 条降级原因见 [decision_consistency_audit.md](../../docs/radar_method_search_2010_2026/final_audit/decision_consistency_audit.md)；高价值 pending 的新增全文/摘要证据见 [pending_upgrade_evidence.md](../../docs/radar_method_search_2010_2026/priority_fulltext/pending_upgrade_evidence.md)。

## 先看结论：雷达方法地图

| ID | 模块 | 典型输入 → 输出 | 来源判断 | 对 IWR1843/IWR1642 + ADXL355 的用途 |
|---|---|---|---|---|
| M01 | 波形/距离 | ADC/IF → beat frequency、Range FFT、range bin | 雷达体制内 | 把 10–20 m 目标分到距离单元；是全部后续相位处理的入口 |
| M02 | 慢时间速度/频率 | range-bin IQ → Doppler FFT/STFT/速度 | 雷达体制内 | 给振动频率、相位变化率和 Doppler 辅助解缠 |
| M03 | IQ 标定 | I/Q → 去 DC、幅相失配校正、ellipse→circle | CW 雷达早期形成，迁移到 FMCW range-bin | 消除 ADXL355 之外的雷达本征相位偏差 |
| M04 | 圆拟合/phasor offset | 复数 IQ 弧 → 圆心、半径、静态背景 | 微波/CW 雷达 + 通用最小二乘 | mmVib 的基础算子；可作为雷达位移观测生成器 |
| M05 | 相位解调 | I/Q → atan2/DACM/连续相位 | CW Doppler/干涉雷达，后迁移 FMCW | 得到 LOS 位移相位 |
| M06 | 相位解缠/降噪 | wrapped phase + prior → unwrapped phase | 雷达特定问题，KF/Doppler 是通用工具 | 最大 2 mm 位移时处理 λ/4 变化、噪声和跳变 |
| M07 | 多弧/多频/多 Chirp | 多个观测弧 → 更稳定圆心/相位 | CW/QFG/微波先有；mmVib 做 virtual Chirp 胶水 | 低 VSNR 和微米振动精度增强 |
| M08 | 杂波/干扰/鲁棒估计 | IQ/phase → 清洁观测、异常段 | 雷达应用问题 + 通用鲁棒估计 | 处理静止参考、动态遮挡、旁瓣和低 SNR |
| M09 | 多目标距离分离 | range profile → 多 range target | FMCW 原生 | 不同距离散射点分别跟踪 |
| M10 | 检测/候选选择 | range-angle/Doppler map → target candidates | CFAR/DBSCAN 等雷达常用模块 | 自动挑选稳定目标，避免手工指定 range bin |
| M11 | 波束形成 | 阵列复数 → DBF/FFT/Capon/MVDR complex beam | MIMO 雷达原生 | 同 range bin 不同角度目标分离并保留相位 |
| M12 | 超分辨 AoA | 阵列复数 → MUSIC/ESPRIT/RELAX 角度 | 通用阵列谱估计迁移到雷达 | 作为离线分离上限或小孔径增强对照 |
| M13 | 稀疏/贝叶斯空间重构 | 阵列 → OMP/SBL/gridless range-angle | 通用优化迁移到雷达 | 处理有限通道/近角目标；相位连续性要单独验证 |
| M14 | LOS→结构坐标 | 多 LOS + 几何 → 2D/3D 位移 | 雷达几何应用 + 通用坐标变换 | 解决雷达只测径向分量的问题 |
| M15 | 扫描/全场 | 波束/相位编码 → 多点振动场 | 微波雷达/扫描雷达迁移 | 用于多测点或模态形状验证 |
| M16 | 频谱/模态 | 位移/加速度 → 频率、模态、ODS | 通用信号处理迁移 | 识别前六阶 <100 Hz 频率和模态参数 |
| M17 | BSS/分解 | 混合响应 → VMD/EMD/ICA 分量 | 通用信号处理迁移 | 在同距混合或多模态场景做辅助分离 |
| M18 | 跟踪/数据关联 | 候选点 → track/state | 通用跟踪迁移到雷达 | 维护 range-angle target 身份和遮挡后的恢复 |
| M19 | 雷达–加速度融合 | radar displacement + accel → state/displacement | 结构监测胶水；FIR/KF 本身已有 | ADXL355 提供高频预测、雷达提供低频/绝对约束 |
| M20 | 质量/置信度/不确定度 | SNR、IQ 几何、innovation → covariance/weight | 雷达质量模型 + 通用自适应滤波 | 让多 target 和多传感器按可靠性加权 |

## 方法来源的三种层级

- **雷达原生模块（R）**：dechirp/beat、Range FFT、slow-time Doppler、CFAR、MIMO 虚拟阵列、波束形成、range-angle map。
- **跨雷达迁移（T）**：CW/24 GHz/94 GHz 的 I/Q atan2、DC offset、circle/ellipse fit、DACM、多弧/QFG；FMCW 先取 range-bin 复数慢时间，再复用这些几何方法。
- **通用算法迁移（G）**：LM/最小二乘、MLE/Nelder–Mead、MUSIC/RELAX、STFT/VMD/EMD、KF/EKF/UKF/FIR、DBSCAN/JPDA 等。论文中应把“雷达观测模型”与“优化器/滤波器”分开写。
- **场景胶水（A）**：把多个观测变成同一结构位移潜变量，例如 mmVib 的 consolidated common-radius + virtual Chirp，或雷达/加速度的共同状态、目标级协方差和遮挡切换。

## 关键论文卡片（优先精读）

| 论文 | 主要模块 | 原始体制/场景 | 与 mmVib 或本课题的关系 | 来源 |
|---|---|---|---|---|
| Kåsa, 1976, A Curve Fitting Procedure and Its Error Analysis | M04：代数圆拟合 | 通用最小二乘/微波测量 | 当前递推 IQ 圆拟合的数学基础；不是雷达专属创新 | [DOI](https://doi.org/10.1109/TIM.1976.6312298) |
| Park et al., 2007, Arctangent Demodulation With DC Offset Compensation in Quadrature Doppler Radar Receiver Systems | M03/M05：DC offset 补偿 + atan2 解调 | 微波正交 CW Doppler，生命体征 | 圆弧 I/Q 解调的早期代表；不是 mmVib 首创 | [DOI](https://doi.org/10.1109/TMTT.2007.895653) |
| Mikhelson et al., 2011, Remote Sensing of Heart Rate and Patterns of Respiration on a Stationary Subject Using 94-GHz Millimeter-Wave Interferometry | M04/M05/M06：I/Q 去均值、圆弧中心、相位解缠 | 94 GHz CW 干涉 | 证明圆弧中心去偏和相位→位移可迁移到毫米波 | [DOI](https://doi.org/10.1109/TBME.2011.2111371) |
| Wang et al., 2014, Noncontact Distance and Amplitude-Independent Vibration Measurement Based on an Extended DACM Algorithm | M05：extended DACM | 微波 CW | 绕开 atan2 值域与零点问题的相位模块 | [DOI](https://doi.org/10.1109/TIM.2013.2277530) |
| Zakrzewski et al., 2014, Quadrature Imbalance Compensation With Ellipse-Fitting Methods | M03：ellipse fit + affine normalization | 微波 CW 生理雷达 | I/Q 椭圆校准来源；mmVib 只使用其几何思想的 FMCW 版本 | [DOI](https://doi.org/10.1109/TMTT.2014.2321738)，补充全文在 `_web_supplements/zakrzewski2014_ellipse_thesis.pdf` |
| Gao et al., 2017, Arc Shifting Method for Small Displacement Measurement | M07：arc shifting + LM circle fit | 2.4 GHz CW Doppler | 多弧提升小位移圆心估计精度；mmVib 的多观测思想前序 | [DOI](https://doi.org/10.1109/MWSYM.2017.8058760) |
| Bi et al., 2018, A Multi-Arc Method for Improving Doppler Radar Motion Measurement Accuracy | M07：phase shifter 多弧、逐弧 LM 拟合、融合 | 2.4 GHz CW Doppler | 多弧不是 mmVib 首创；本地全文在 `_web_supplements/bi2018_multi_arc.pdf` | [公开 PDF](https://music-sustech.github.io/publication/sjbi2018.pdf) |
| Kim & Kim, 2019, Quadrature Frequency-Group Radar and its center estimation algorithms | M07：QFG 真实频率组、多弧圆心估计 | 24 GHz SFCW/QFG | mmVib virtual Chirp 可看作不加额外硬件的多频/多弧迁移 | [DOI](https://doi.org/10.1038/s41598-019-43205-7)，补充全文在 `_web_supplements/kim2019_qfg.pdf` |
| Li et al., 2015, A Noncontact FMCW Radar Sensor for Displacement Measurement in SHM | M01/M09：beat、Range FFT、range-bin 相位、多目标距离分离 | FMCW 结构监测 | FMCW 位移链的基础前序 | [DOI](https://doi.org/10.3390/s150407412) |
| Ding et al., 2016, Vibration Parameter Estimation Using FMCW Radar | M01/M02/M07：FMCW 振动模型、参数估计、CRLB | FMCW | 把振动频率/幅值估计写成参数估计问题 | [DOI](https://doi.org/10.1109/ICASSP.2016.7472072) |
| Xiong et al., 2018, Accurate and Robust Displacement Measurement for FMCW Radar Vibration Monitoring | M01/M05/M06：零填充 FFT + approximate ML 跨 sweep 相位 | FMCW 振动监测 | 复杂相位估计的 FMCW 路线 | [DOI](https://doi.org/10.1109/JSEN.2017.2778294) |
| Mercuri et al., 2022, Analysis of Signal Processing Methods to Reject the DC Offset Contribution of Static Reflectors in FMCW Radar-Based Vital Signs Monitoring | M03/M04：AC coupling、代数/几何圆拟合、圆心相减 | FMCW/mmWave range-bin IQ | 直接验证 IQ 圆心补偿从 CW 迁移到 FMCW/mmWave；开放全文 | [DOI](https://doi.org/10.3390/s22249697)，[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9781610/) |
| mmVib, MobiCom 2020, Measuring Micrometer-Level Vibrations With mmWave Radar | M04/M07/M10/M11/M20：virtual Chirp、consolidated common-radius、IQM、AoA/方向修正 | 77 GHz FMCW IWR1642 | 代表性胶水：已有圆拟合/多弧/阵列模块被统一成共享振动潜变量 | [作者 PDF](https://tns.thss.tsinghua.edu.cn/sun/publications/mmVib_MobiCom2020.pdf)，本地 `03_range_velocity_target_processing/mmVib_MobiCom2020.pdf` |
| Li et al., 2022, Multi-scale and full-field vibration measurement via millimetre-wave sensing | M01/M06/M09/M11/M15：ASPD、range-angle joint phase tracking | LFMCW mmWave | 处理跨 range bin、大位移和同距多目标；是 mmVib 后续重要迁移 | [DOI](https://doi.org/10.1016/j.ymssp.2022.109178) |
| Guerzoni et al., 2025, A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars | M02/M06：Doppler 增量辅助迭代解缠 | mmWave MIMO FMCW | 针对大相位增量的近期 radar-native 解缠模块 | [DOI](https://doi.org/10.1016/j.ymssp.2025.112777) |
| Ma et al., 2023, Structural displacement estimation using accelerometer and FMCW millimeter wave radar | M06/M14/M19：best target、转换因子、acc 辅助解缠、FIR | FMCW mmWave + 加速度 | 与你的雷达+ADXL355 目标最直接的前序；胶水是频带互补和 target 标定 | [DOI](https://doi.org/10.1016/j.ymssp.2022.109582) |
| Michel et al., 2021, Advancing Ground-Based Radar Processing for Bridge Infrastructure Monitoring | M04/M06/M08/M14/M20：扰动/杂波剔除、圆拟合、LOS 投影、不确定度 | GBSAR Ku-band 桥梁 | 跨体制的完整雷达后处理链；开放全文：[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8003812/) |
| Rodrigues & Li, 2021, A Review on Low-Cost Microwave Doppler Radar Systems for SHM | 方法总综述：CW Doppler、解调、时频、结构监测 | 低成本微波 Doppler | 用于扩展模块索引，不作为单一算法创新 | [DOI](https://doi.org/10.3390/s21082612) / [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8068160/) |
| Kim & Hong, 2013, Multiple-target tracking and track management for an FMCW radar network | M10/M18：beat measurement-space association + EKF track management | FMCW radar network | 可迁移到静止散射点/遮挡后的 target identity 管理 | [DOI](https://doi.org/10.1186/1687-6180-2013-159) |
| Piotrowsky et al., 2019/2022, Unambiguous/High-Accuracy Distance Measurements With FMCW Radar | M01/M05/M07/M20：beat 粗距离 + carrier phase 精测距 + 硬件/路径校准 | 80 GHz/126–182 GHz FMCW | 适合作为范围/相位耦合与系统标定来源，不应直接等同 IWR 10–20 m 精度 | [2019 DOI](https://doi.org/10.1109/MWSYM.2019.8700889)，[2019 TMTT DOI](https://doi.org/10.1109/TMTT.2019.2930504)，[2022 DOI](https://doi.org/10.1109/TMTT.2022.3195235) |

## 与 mmVib 的关系：哪些是模块，哪些是胶水

mmVib 的基础算子并非全部新提出。`atan2/DC offset`、I/Q 圆弧中心、ellipse/circle fit、DACM、多弧/多频、Range FFT、AoA 和最小二乘在更早的 CW、微波、QFG、FMCW、阵列雷达文献中已有。mmVib 的主要系统性贡献是：
1. 用目标/背景复数回波模型把多个观测解释为同一振动状态；
2. 通过 fast-time 重排生成 virtual Chirp，把真实多频/多弧思想迁移到商用 FMCW；
3. 用 common intrinsic radius + 每个观测的 translation/scaling 做 consolidated fit；
4. 用多天线 AoA 和方向投影把多观测合并成目标位移。

因此后续论文应把“模块来源”和“胶水位置”分开。只把 FFT、圆拟合、KF、VMD、MUSIC 等已有算子串起来，不能写成单个算子首创；可以把创新放在结构响应的共同潜变量、雷达/ADXL355 观测方程、目标级质量协方差、相位解缠约束和遮挡切换。

## 对本课题的推荐拼接链

`ADC → Range FFT → candidate range bins → IQ ellipse/circle + phasor offset → atan2/DACM → Doppler/加速度辅助 phase unwrap → LOS displacement → AoA/几何投影 → target confidence → ADXL355 状态预测 → radar/accel 共同位移状态（KF/EKF/FIR）→ FFT/SSI 模态识别`。
其中 M01–M18 都可以作为已有模块库；论文的小胶水可集中在 M19/M20：多个 radar target 的共同结构位移潜变量、ADXL355 加速度状态预测、target-wise covariance/quality gate，以及最大 2 mm、<100 Hz 磁浮轨道梁场景下的同步和方向约束。

## 完整本地 PDF 索引

下表覆盖本目录中的每个 PDF，且每行已经写入该文件的具体处理链和用途。目录名给出主模块；同一论文在两个模块目录出现时，表示它可以被两条链路复用，文件使用硬链接避免额外存储。`R`=雷达原生，`T`=跨雷达迁移，`G`=通用算法迁移，`A`=场景胶水/应用适配。 逐篇方法行的字段审计见 [`local_pdf_method_audit.md`](../../docs/radar_method_search_2010_2026/final_audit/local_pdf_method_audit.md)，机器可读记录见 [`local_pdf_method_rows.jsonl`](../../docs/radar_method_search_2010_2026/final_audit/local_pdf_method_rows.jsonl)。

| 文件 | 主模块 | 模块标签 | 归属判断 | 该文件在方法库中的用途 |
|---|---|---|---|---|
| `00_fmcw_phase_displacement/A Doppler aliasing free micro-motion parameter estimation method in the terahertz band.pdf` | 00_fmcw_phase_displacement | M02/M08/M16 | R/G | 把回波变换为 STFT 时频图；针对 THz 微多普勒超过 PRF/2 后发生折叠的问题，在参数空间用 modulo Generalized Hough Transform 匹配折叠曲线，估计微动周期、幅度和初相位。该过程把 Doppler 混叠处理和曲线参数估计放在同一个搜索步骤中。 |
| `00_fmcw_phase_displacement/A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf` | 00_fmcw_phase_displacement | M01/M05/M09 | R/T | 对每个 FMCW beat 信号做 DFT/Range FFT，取峰值 beat-frequency bin 得到粗距离；在目标固定于同一 range bin 时读取 beat 相位变化并换算位移。对多个距离不同的目标分别分析 range bin 的相位，从而实现多目标位移测量。 |
| `00_fmcw_phase_displacement/A Software-Synchronization Based, Flexible, Low-Cost FMCW Radar.pdf` | 00_fmcw_phase_displacement | M01/M02/M10 | R/G | 用周期性间歇斜坡波形产生 beat 信号，并仅从声卡采样的连续信号中检测有效帧起点。提出基于幅度特征的三阈值软件同步算法，再按 beat 频率计算目标距离或速度。 |
| `00_fmcw_phase_displacement/A_130-nm_Fusion-Based_Deconvolution_Kernel_Generator_IC_for_Real-Time_mmWave_Radar_Motion_Compensation.pdf` | 00_fmcw_phase_displacement | M08/M19 | A/G | 在小于 95 ms 的窗口内融合与雷达同步的辅助加速度计数据，生成用于抑制平台振动的解卷积/陷波核。该核随后作用于雷达数据频谱，以实时补偿平台运动；芯片实现采用单陷波核降低硬件开销。 |
| `00_fmcw_phase_displacement/An_Unambiguous_Phase-Based_Algorithm_for_Single-Digit_Micron_Accuracy_Distance_Measurements_using_FMCW_Radar.pdf` | 00_fmcw_phase_displacement | M01/M05/M06 | R/G | 先用无歧义的目标 beat frequency 确定 range cell，再使用歧义但高精度的目标相位细化距离；相位校准补偿 RF/IF 路径的距离相关误差。将粗距离和载波相位结合，得到全局无歧义距离。 |
| `00_fmcw_phase_displacement/B36_Robust_Vibration_Displacement_Extraction_for_FMCW_Radar_by_Incorporating_Optimized_Beat_Frequency_and_Maximum_Likelihood_Estimation.pdf` | 00_fmcw_phase_displacement | M01/M05/M08 | R/G | 用 Nelder–Mead 在噪声 beat 信号上优化目标 beat frequency；再以该频率为条件，在多个 radar sweep 周期上用最大似然估计得到稳健相位时间序列。最终将相位序列转换为振动位移。 |
| `00_fmcw_phase_displacement/B38_Frequency-phase_coupled_parameter_estimation_for_vibration_measurement_with_LFMCW_radar.pdf` | 00_fmcw_phase_displacement | M01/M05/M06/M07 | R/G | 从 LFMCW 离散基带模型显式保留距离信息中的频率–相位耦合；用最大似然联合估计两类信息，并设计顺序启发式求解以避免联合优化随观测数指数增长。该方法直接输出距离/振动参数，性能接近 CRLB。 |
| `00_fmcw_phase_displacement/B45_Accurate_multi-scale_displacement_measurement_with_FMCW_radar_based_on_all-phase_compensation_method.pdf` | 00_fmcw_phase_displacement | M01/M05/M06/M09/M18 | R/A | 将 beat 信号的多个子信号组合为 all-phase beat signal；同时跟踪目标所在的 range unit，并沿慢时间跟踪干涉相位演化。APC 用统一的相位补偿消除目标跨 range unit 时的相位跳变和动态索引相移。 |
| `00_fmcw_phase_displacement/Development of a high-precision nano millimeter-wave radar system for non-contact bridge displacement monitoring.pdf` | 00_fmcw_phase_displacement | M01/M05/M08/M10 | R/G/A | 用均值消除和 Hamming 窗处理目标指示，再以 ap-FFT 相位识别算法从目标回波提取位移。通过实验室滑台和桥梁现场实验，把峰值/相位处理链与相机基准比较。 |
| `00_fmcw_phase_displacement/Distance_Measurement_Using_mmWave_Radar_Micron_Accuracy_at_Medium_Range.pdf` | 00_fmcw_phase_displacement | M01/M05/M06/M08 | R/G | 先对 IF 输入做逆滤波和窗口化，经居中 IFFT、峰值插值同时估计 pulse position 与 pulse phase；上下扫频平均以抑制 Doppler/路径项，再施加近场和空气折射率补偿。利用无歧义 pulse position 为高精度 phase 建立全局解缠距离。 |
| `00_fmcw_phase_displacement/Enabling_High_Accuracy_Distance_Measurements_With_FMCW_Radar_Sensors.pdf` | 00_fmcw_phase_displacement | M01/M05/M06/M08 | R/G | 建立考虑 RF/IF 路径频率响应的 phase evaluation chain，把频率估计提供的粗距离和相位估计提供的细距离联合起来。增强相位评估还显式分析干扰目标和微多普勒引入的误差，以提升 5.2 m 范围内的鲁棒性。 |
| `00_fmcw_phase_displacement/Experimental Analysis of Accuracy and Precision in Displacement Measurement Using Millimeter-Wave FMCW Radar.pdf` | 00_fmcw_phase_displacement | M01/M05 | R/G | 固定目标时以 FMCW beat frequency 确定 range，并以相邻 chirp 间的 beat-signal phase difference 直接换算微小位移。论文用 loopback waveguide 测 MMIC 固有相位精度，再用 vibration shaker 测真实运动。 |
| `00_fmcw_phase_displacement/FMCW_Radar_for_Noncontact_Bridge_Structure_Displacement_Estimation.pdf` | 00_fmcw_phase_displacement | M01/M05/M06/M09/M14/M15 | R/G/A | 对 LPF 后的 FMCW 频谱取峰值 range bin，并读取该 FFT index 的相位得到位移；对相位进行展开。用 MPU6050 测得雷达仰角并做 LOS 几何修正，同时在桥梁跨径上布置多点目标得到位移分布。 |
| `00_fmcw_phase_displacement/Method for Improving Range Resolution of Indoor FMCW Radar Systems Using DNN.pdf` | 00_fmcw_phase_displacement | M01/M09/M10 | R/G | 先由多台低成本 FMCW 雷达的距离测量推断目标所在 sector，再用 grid/DNN 估计位置以超越单雷达带宽的距离分辨率。多目标场景用 Gaussian filter 和 OS-CFAR 进行检测与筛选。 |
| `00_fmcw_phase_displacement/Radar_Sensing_of_Displacement_Motions_With_High_Robustness_Against_Additive_Noise.pdf` | 00_fmcw_phase_displacement | M05/M06/M08 | T/G | 先分析加性高斯噪声对 I/Q 相位解调的影响，再把 I/Q 中的加性噪声变换成相位噪声，从而降低其对位移重建的影响。方法仍以正交 I/Q 相位解调为入口，并配合相位解缠处理包络周期。 |
| `00_fmcw_phase_displacement/Structural displacement measurements using DC coupled radar with active transponder.pdf` | 00_fmcw_phase_displacement | M05/M08 | T/A | 在 CW 雷达的被动后向散射链路中加入主动转发器以提高返回信号功率和 SNR；随后比较两种配置下的正交雷达位移测量结果。方法的核心是通过目标端增益改善 I/Q 相位解调的观测质量。 |
| `01_cw_iq_interferometry/B46_On_Amplitude_Modulation_in_CW_Doppler_Radars_for_Remote_Displacement_Sensing_Using_ENVSIL_Radar.pdf` | 01_cw_iq_interferometry | M05/M08 | T/A | 推导 TX–RX leakage 下目标运动同时产生 AM 和 PM，并用 AM/PM 的互补关系构造 IQ 轨迹。ENVSIL 架构以包络检测结合自注入锁定，实现远程位移解调并缓解单通道 null-point 问题。 |
| `01_cw_iq_interferometry/Miniaturized_Millimeter-Wave_Radar_Sensor_for_High-Accuracy_Applications.pdf` | 01_cw_iq_interferometry | M01/M05 | R/G | 把 FMCW beat frequency 用于粗目标位置/距离估计，再评估同一回波的相位以得到细距离。该两步链路在 121–127 GHz 集成雷达上实现单数字微米级距离测量。 |
| `01_cw_iq_interferometry/Scanning_Microwave_Vibrometer_Full-Field_Vibration_Measurement_via_Microwave_Sensing_With_Phase-Encoded_Beam_Scanning.pdf` | 01_cw_iq_interferometry | M01/M05/M08/M11/M15 | R/A | 以相位编码的合成波束扫描构造扫描微波测振仪，在 LFMCW 回波上沿慢时间跟踪干涉相位演化。论文专门设计耦合杂波消除流程，把扫描得到的各空间点恢复为全场振动位移。 |
| `01_cw_iq_interferometry/Structural displacement measurements using DC coupled radar with active transponder.pdf` | 01_cw_iq_interferometry | M05/M08 | T/A | 在 CW 雷达的被动后向散射链路中加入主动转发器以提高返回信号功率和 SNR；随后比较两种配置下的正交雷达位移测量结果。方法的核心是通过目标端增益改善 I/Q 相位解调的观测质量。 |
| `02_phase_unwrap_denoise/A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars and its application to displacement estimation in structural health monitoring.pdf` | 02_phase_unwrap_denoise | M02/M05/M06 | R/G/A | 从连续 MIMO FMCW 观测估计目标 Doppler，再将 Doppler 增量作为每个采样间隔的相位变化约束。迭代地选择与预测 Doppler 一致的 wrapped-phase 分支，从而在传统 Itoh 解缠失效的快速运动场景恢复径向位移。 |
| `02_phase_unwrap_denoise/Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.pdf` | 02_phase_unwrap_denoise | M05/M06/M19 | A/G | 将雷达相位建模为离散恒加速度状态，把加速度测量用于动态预测和高频噪声抑制；预测相位校正步骤先消除 2π 跳变，再递归 Kalman 更新得到连续、降噪相位。滤波噪声参数自适应优化，并以卷积形式分析解缠收敛时间。 |
| `02_phase_unwrap_denoise/Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping.pdf` | 02_phase_unwrap_denoise | M05/M06/M07 | R/A | 在每个时间步利用多 Chirp 估计相位变化率，预测下一时刻相位并生成参考相位范围；自适应地从 wrapped phase 选择正确分支，无需经验阈值或额外传感器。 |
| `02_phase_unwrap_denoise/Solving_Phase_Ambiguity_in_Interferometric_Displacement_Measurement_With_Millimeter-Wave_FMCW_Radar_Sensors.pdf` | 02_phase_unwrap_denoise | M03/M05/M06 | T/R | 从单通道 FMCW 的慢时间样本合成正交 I/Q 信号，使 CW 雷达已有的 MDACM 线性相位解调可直接复用。合成 I/Q 后可在超过半波长、最高约十倍波长的位移上连续提取相位而不发生歧义。 |
| `03_range_velocity_target_processing/B05_Periodic-Filtering_Method_for_Low-SNR_Vibration_Radar_Signal.pdf` | 03_range_velocity_target_processing | M02/M04/M05/M06/M08 | R/G/A | 先在 Doppler 域提取振动频率，再利用振动周期构造周期滤波器抑制噪声而不提高过采样率；在复平面用最小二乘圆拟合估计静态杂波，最后以差分相位反演变形。该链路针对低 SNR 下差分相位跳变和杂波估计困难。 |
| `03_range_velocity_target_processing/B24_Fully_automated_and_non-contact_force_identification_of_bridge_cables_using_microwave_remote_sensing.pdf` | 03_range_velocity_target_processing | M02/M10/M16 | R/G/A | 对微波雷达位移谱使用线性复杂度 fast sieve 找局部 Fourier 峰，再用 weighted hash voting 判定峰对应的模态阶次。把选出的频率代入考虑索、弯曲刚度和边界的缆索振动模型，自动求索力。 |
| `03_range_velocity_target_processing/B26_Spectral_estimation_model_for_linear_displacement_and_vibration_monitoring_with_GBSAR_system.pdf` | 03_range_velocity_target_processing | M01/M02/M11/M12/M16 | R/G | 在 MIMO/GBSAR 成像中加入谱估计，使目标方位、线位移和振动特征能被联合检测。模型使用 beamforming、Capon、MUSIC 和 CLEAN 等空间谱/旁瓣处理模块，并以干涉相位获得快速位移。 |
| `03_range_velocity_target_processing/Measuring_Micrometer-Level_Vibrations_With_mmWave_Radar.pdf` | 03_range_velocity_target_processing | M01/M04/M07/M08/M10/M11/M20 | A/R/G | mmVib 的 MSC（Multi-Signal Consolidation）模型在 IQ 域统一多频、多天线及背景反射；Range FFT 分离距离，fast-time 重排生成 virtual Chirp，IQM 用 consolidated common-radius 拟合弧/圆并恢复相位。VSNR 指导降误差，MVE/CVE/DVR 完成目标选择、多弧整合和 AoA/方向投影；IQM 是聚合步骤，不是圆拟合算子本身的首创。 |
| `03_range_velocity_target_processing/Multi-Vib_Precise_Multi-point_Vibration_Monitoring_Using_mmWave_Radar.pdf` | 03_range_velocity_target_processing | M01/M05/M08/M09/M10/M11/M15 | A/R/G | 用具有高 RCS 的物理 marker 把各测点反射增强到雷达方向；利用 FMCW range separation、MIMO beamforming/null steering 分离测点回波，再对每个信号并行提取相位。后续信号处理对各点去噪并估计振动频率和位移。 |
| `03_range_velocity_target_processing/mmVib_MobiCom2020.pdf` | 03_range_velocity_target_processing | M01/M04/M07/M08/M10/M11/M20 | A/R/G | 论文提出 MSC（Multi-Signal Consolidation）信号模型，显式描述多 Chirp、多天线与静态背景反射；在 Range FFT 后生成 virtual Chirp，利用 IQM 的 common-radius 几何聚合恢复微振相位。MSC 是整条聚合链的胶水，圆拟合、Range FFT 和 AoA 等基础算子均有前序来源。 |
| `04_aoa_beamforming_mimo/A Decoupling-based Approach for Signature Estimation of Wideband XL MIMO-FMCW Radars.pdf` | 04_aoa_beamforming_mimo | M09/M10/M12/M13 | R/G | Models spatial-wideband range migration, beam squint and range-angle coupling in XL MIMO-FMCW. Uses OMP sparse recovery for range and angle, then performs sequential one-dimensional frequency estimates to decouple the 2-D problem. A low-index detection stage separates overlapping target clusters in the range-angle plane. |
| `04_aoa_beamforming_mimo/A Real-Time Evaluation Algorithm for Noncontact Heart Rate Variability Monitoring.pdf` | 04_aoa_beamforming_mimo | M01/M05/M11/M16 | R/G | Separates people using FMCW range gating and MIMO beamforming. Demodulates the selected chest-motion phase, differentiates it to acceleration, smooths the acceleration, and uses joint optimization to segment individual heartbeats. Computes HRV statistics from the segmented interbeat intervals. |
| `04_aoa_beamforming_mimo/An Implementation Scheme of Range and Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M12/M13 | R/G | Builds a coherent 4-TX/4-RX TDM FMCW virtual array and forms range-angle measurements from its IF data. Applies sparse spectrum fitting (SpSF) to estimate target distance and direction, exploiting spatial sparsity with few snapshots and low SNR. Compares the sparse spectrum estimate with MUSIC and Capon. |
| `04_aoa_beamforming_mimo/Angle of Arrival Estimation with Transformer- A Sparse and Gridless Method with Zero-Shot Capability .pdf` | 04_aoa_beamforming_mimo | M11/M12/M13 | G/R | Introduces AAETR, an encoder-decoder Transformer that maps array signals to sparse angle targets. The decoder uses cross-attention and learnable queries to produce gridless AoA estimates without a predefined angle grid. Trains on simulated data and evaluates zero-shot transfer to real automotive radar, including sidelobe suppression. |
| `04_aoa_beamforming_mimo/Burg-Aided 2D MIMO Array Extrapolation for Improved Spatial Resolution.pdf` | 04_aoa_beamforming_mimo | M11/M12/M13 | G/R | Uses the Burg autoregressive algorithm to extrapolate a 2-D MIMO virtual array beyond the available antenna aperture. Processes 77-GHz 1-D MIMO measurements to obtain 3-D range-azimuth-elevation data and evaluates the extrapolated array experimentally. The extrapolated spatial samples are used to improve angular resolution without adding physical elements. |
| `04_aoa_beamforming_mimo/Enhanced Two-Stage Sparse Bayesian Learning Algorithm for Multi-Vehicle Precise Detection and Localization with MIMO-FMCW Radar.pdf` | 04_aoa_beamforming_mimo | M01/M09/M10/M12/M13 | R/G | Uses a hierarchical two-stage SBL procedure for joint range-angle localization. A coarse search on a sparse grid finds target regions; local high-resolution grids then refine the estimates. A sigmoid local-maximization term suppresses sidelobes and iterative interference cancellation separates mutually interfering vehicles. |
| `04_aoa_beamforming_mimo/Extrapolation-RELAX_Estimator_Based_on_Spectrum_Partitioning_for_DOA_Estimation_of_FMCW_Radar.pdf` | 04_aoa_beamforming_mimo | M11/M12/M13 | R/G | Partitions the spatial spectrum and extrapolates each partition with an autoregressive model to synthesize virtual array samples. Feeds the extrapolated complex spectrum into a RELAX iterative parameter estimator, retaining magnitude and phase information. Uses the estimator as an alternative to low-resolution DBF and compares it with MUSIC/ESPRIT. |
| `04_aoa_beamforming_mimo/FMCW_multiple-input_multiple-output_radar_with_iterative_adaptive_beamforming.pdf` | 04_aoa_beamforming_mimo | M01/M11/M20 | R/G | Adapts the iterative adaptive approach (IAA) beamformer to range-compressed FMCW MIMO data. Uses a 4×4 collocated array and compares IAA with delay-and-sum beamforming for angular sidelobe and resolution performance. Adds a low-frequency clock/trigger distribution and calibration procedure to preserve phase coherence between TX/RX sites. |
| `04_aoa_beamforming_mimo/Fast_and_Accurate_Angle_Estimation_for_MIMO_Radar_With_a_Virtual_Nonrectangular_Array.pdf` | 04_aoa_beamforming_mimo | M11/M12 | R/G | Forms a coarse estimate with amplitude-normalized 2-D FFT on a nonrectangular virtual array. Refines the off-grid angle using a statistically optimized amplitude-comparison monopulse estimator. The two-stage estimator uses the full irregular aperture rather than extracting only a rectangular subarray. |
| `04_aoa_beamforming_mimo/Frequency-Spatial_Adaptive_Digital_Beamforming_Technique_for_Range-Angle_Decoupling_With_High-Resolution_MIMO_Radar.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M12 | R/G | Generates adaptive steering vectors from the frequency-spatial phase of the IF signals. Performs digital beamforming with those vectors so range is estimated within each angular cell instead of using a fixed-wavelength steering vector. This directly reduces wideband range-angle coupling and target spreading at off-boresight angles. |
| `04_aoa_beamforming_mimo/Full-field 3D displacement measurement via microwave sensing.pdf` | 04_aoa_beamforming_mimo | M09/M11/M14/M15 | A/T | Uses three non-collinear microwave transceivers and reference targets to establish device and structural coordinate systems. Automatically matches points across range-angle heatmaps from different transceivers. Reconstructs 3-D displacement in device and structural coordinates from multi-view microwave range-angle measurements. |
| `04_aoa_beamforming_mimo/High-Resolution Localization Using Distributed MIMO FMCW Radars.pdf` | 04_aoa_beamforming_mimo | M09/M11/M12/M14/M20 | R/A | Runs 2-D MUSIC locally at each FMCW MIMO radar to estimate target range and cross-range. Transforms local estimates into one unified coordinate system and fuses them with weighted averaging. Sets weights from the achievable coordinate resolution and local range/angle estimation errors. |
| `04_aoa_beamforming_mimo/High-Resolution and Accurate RV Map Estimation by Spare Bayesian Learning.pdf` | 04_aoa_beamforming_mimo | M01/M02/M09/M13 | R/G | Builds a wideband FMCW signal dictionary directly from the radar model instead of a DFT dictionary. Uses fast marginal-likelihood SBL to reconstruct a sparse range-velocity map with few samples. The method addresses range migration and improves resolution, accuracy, and unambiguous velocity over 2-D DFT. |
| `04_aoa_beamforming_mimo/Joint_Estimation_of_Channel_Range_and_Doppler_for_FMCW_Radar_with_Sparse_Bayesian_Learning.pdf` | 04_aoa_beamforming_mimo | M01/M02/M13/M20 | R/G | Forms a joint channel, range, and Doppler estimation model for FMCW radar. Applies SBL to exploit sparse radar targets and incorporates local estimates from neighboring cooperative sensing nodes as prior information. Uses the resulting channel estimates to improve target sensing reliability and reduce false alarms. |
| `04_aoa_beamforming_mimo/Li_Azimuth_Super-Resolution_for_FMCW_Radar_in_Autonomous_Driving_CVPR_2023_paper.pdf` | 04_aoa_beamforming_mimo | M11/M12/M13 | G/R | Introduces ADC-SR, a lightweight neural model that predicts uncaptured receive-channel ADC signals from raw FMCW MIMO ADC data. Applies ordinary FFT after hallucinating the missing spatial samples, and also combines ADC-SR with a range-azimuth super-resolution model (Hybrid-SR). Trains/evaluates on Pitt-Radar and RADIal and reports downstream object-detection gains. |
| `04_aoa_beamforming_mimo/MIMO FMCW Radar with Doppler-Insensitive Polyphase.pdf` | 04_aoa_beamforming_mimo | M01/M11/M20 | R/G | Designs polyphase codes for successive FMCW chirps so TX waveforms remain low-cross-correlation under Doppler-filter mismatch. Optimizes code phases with a simulated-annealing algorithm. Uses the coded MIMO virtual array for angle estimation and compares angle error with conventional orthogonal codes. |
| `04_aoa_beamforming_mimo/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf` | 04_aoa_beamforming_mimo | M01/M05/M08/M09/M11/M15 | A/T | Tracks interferometric phase evolution jointly in range and angle to quantify micromotion across a full field of view. Combines full-field localization with clutter elimination before extracting phase-based vibration. Demonstrates multi-person vital signs, full-field structural vibration, and sound-source localization using one mmWave system. |
| `04_aoa_beamforming_mimo/Millimeter_Wave_Real-Time_Tracking_and_Imaging_of_Moving_Objects_Based_on_Virtual_MIMO_Array_and_State_Vector_Prediction.pdf` | 04_aoa_beamforming_mimo | M09/M11/M15/M18 | R/G | Forms a 3×4 virtual MIMO array and converts its reflections into a point-cloud image. Uses a target state vector and Kalman prediction to track point-cloud motion between frames. Produces real-time imaging and continuous target trajectories with a 100-ms delay. |
| `04_aoa_beamforming_mimo/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf` | 04_aoa_beamforming_mimo | M01/M05/M06/M08/M09/M11/M15 | A/T | Introduces adaptive segmented phase demodulation (ASPD) to quantify displacement from micrometre to decimetre scales. Tracks interferometric phase jointly in range-angle dimensions to remove adjacent-target coupling and aliasing. Uses LFMCW range-angle processing for synchronous multi-target, full-field structural vibration. |
| `04_aoa_beamforming_mimo/Multi-target Range and Angle detection forMIMO-FMCW radar with limited antennas.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M13 | R/G | Uses DFT-based focusing to obtain target range-delay bins from FMCW IF data. At each detected range, recovers target angles with compressive sensing over a sparse random virtual array. The range-first/angle-second decomposition avoids requiring a dense physical array and is evaluated for multi-target localization. |
| `04_aoa_beamforming_mimo/Multi-target Range, Doppler and Angle estimation in MIMO-FMCW Radar with Limited Measurements .pdf` | 04_aoa_beamforming_mimo | M01/M02/M09/M11/M13 | R/G | Models sparse-random and ULA MIMO-FMCW data as a 3-D spectral estimation problem. Uses DFT focusing or range-OMP for range, then 2-D compressive sensing for joint Doppler-angle estimation. Derives recovery guarantees for structured random measurements and demonstrates similar detection with fewer chirps and antennas than DFT/MUSIC. |
| `04_aoa_beamforming_mimo/Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf` | 04_aoa_beamforming_mimo | M01/M09/M10/M11/M16 | R/G | Forms a range-angle map using range FFT and Capon angle estimation. Applies 2-D CFAR and DBSCAN to detect each person’s range and angle, then uses LCMV digital beamforming to obtain each target slow-time signal. Selects the phase signal by autocorrelation and estimates respiration/heart rates from harmonic discrimination. |
| `04_aoa_beamforming_mimo/Non-Contact_Vital_Signs_Monitoring_for_Multiple_Subjects_Using_a_Millimeter-Wave_FMCW_Automotive_Radar.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M16 | R/A | Uses a 76–81-GHz single-channel FMCW automotive radar and extracts phase from tiny chest motion. Applies beam steering across the receive aperture to isolate subjects with different angles, including subjects at equal range. Demonstrates independent respiratory signatures with about 30° angular discrimination. |
| `04_aoa_beamforming_mimo/Non-uniform virtual array position optimization for MIMOradar and neural network-based radar imagingenhancement.pdf` | 04_aoa_beamforming_mimo | M11/M12/M13 | A/G/R | Optimizes non-uniform TX/RX virtual-array element placement with a genetic algorithm to reduce sidelobes. Trains a convolutional neural network to suppress residual sidelobe artifacts in range-angle images. Generates training radar data by simulation and validates the optimized array and CNN on a TI AWR cascade radar. |
| `04_aoa_beamforming_mimo/Reduced complexity angle-Doppler-range estimation for MIMO radar that employs compressive sensing.pdf` | 04_aoa_beamforming_mimo | M01/M02/M11/M13 | R/G | Introduces step-frequency pulses so target range appears as phase variation across pulses. Uses sparse ℓ1 recovery for MIMO angle-Doppler-range estimation. Decouples angle, velocity, and range into successive estimates to reduce the computational burden of a joint 3-D optimization. |
| `04_aoa_beamforming_mimo/Research on a Super-Resolution and Low-Complexity Positioning Algorithm Using FMCW Radar Based on OMP and FFT in 2D Driving Scene.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M13/M18 | R/G/A | Uses Hamming-windowed FFT for the baseline range-angle estimate and OMP for sparse super-resolution localization. Applies particle swarm optimization to redesign an aging/nonideal antenna placement and recover its angular accuracy. Estimates 2-D target position, trajectory, and velocity from one-frame IF data. |
| `04_aoa_beamforming_mimo/Simultaneous Monitoring of Multiple People’s Vital Sign Leveraging a Single Phased-MIMO Radar.pdf` | 04_aoa_beamforming_mimo | M01/M09/M11/M20 | A/R | Uses a TDM phased-MIMO TI FMCW radar to form a virtual array and steer beams to desired directions. Combines TX/RX virtual-array channels with a Capon beamformer to increase target SNR at equal radial distances. Automatically localizes multiple subjects and extracts their vital signs from separated phase signals. |
| `04_aoa_beamforming_mimo/Subspace-Based Detector For Distributed Mmwave Mimo Radar Sensors.pdf` | 04_aoa_beamforming_mimo | M02/M08/M10/M20 | R/G | Models distributed mmWave MIMO radar interference as a low-rank subspace with angle and Doppler spread. Derives a generalized likelihood-ratio test detector for moving targets in clutter and interference. Chooses the detector threshold to obtain constant false-alarm-rate behavior. |
| `04_aoa_beamforming_mimo/Super-Resolution Angle Estimation Algorithm using Low Complexity MUSIC-Based RELAX for MIMO FMCW Radar .pdf` | 04_aoa_beamforming_mimo | M11/M12 | R/G | Combines RELAX-based CLEAN with a low-complexity MUSIC (LC-MUSIC) estimator for MIMO-FMCW DOA. Uses the first target estimate to cancel reconstructed target components and iteratively estimates remaining angles. Validates the super-resolution angle estimator with simulation and indoor FMCW experiments. |
| `04_aoa_beamforming_mimo/TI MMWAVE-SDK : AoAProc : MIMO Radar app report.pdf` | 04_aoa_beamforming_mimo | M11 | R | Explains the TI virtual-array MIMO principle, including TX/RX multiplexing and the resulting virtual antenna positions. Describes angle estimation using conventional spatial FFT/digital beamforming over the virtual array. Covers TDM-MIMO and BPM-MIMO configuration and implementation on TI mmWave devices. |
| `04_aoa_beamforming_mimo/Variational Signal Separation for Automotive Radar Interference Mitigation .pdf` | 04_aoa_beamforming_mimo | M08/M09/M13/M20 | R/G | Represents coherent echoes and noncoherent interfering FMCW chirps as multipath channels with parametric envelopes. Places hierarchical Gamma-Gaussian priors on channel coefficients and derives iterative variational expectation-maximization inference. Jointly estimates object parameters and successively cancels interference, approaching the no-interference CRLB under the stated model. |
| `04_aoa_beamforming_mimo/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf` | 04_aoa_beamforming_mimo | M01/M05/M09/M11/M16 | R/A | Uses FMCW range gating and multiple receive channels to separate objects in the range-azimuth plane. Applies beamforming to isolate each person’s complex slow-time phase from clutter and neighboring subjects. Extracts breathing and heart rates from phase modulation caused by chest motion. |
| `05_multi_target_full_field/B41_Cross-range_displacement_measurement_using_a_single_MIMO_FMCW_radar.pdf` | 05_multi_target_full_field | M01/M05/M09/M11/M14 | A | 对MIMO-FMCW IF信号形成range-angle热图，并跟踪目标的距离和角度迁移。先补偿横向运动引起的range/angle migration相位，再解耦同时依赖距离和角度的相位项，用剩余相位估计cross-range displacement。 |
| `05_multi_target_full_field/B42_Simultaneous_displacement_and_rotation_estimation_for_flexible_structures_through_millimeter-wave_radar_and_inertial_sensor_fusion.pdf` | 05_multi_target_full_field | M05/M14/M19/M20 | A | 从FMCW雷达相位得到结构LOS位移；用共址IMU加速度估计初始转角，并用雷达测量解耦平移分量。再用转换因子标定把LOS位移换为结构位移，并以误差优化融合初始转角和IMU角速度。 |
| `05_multi_target_full_field/B43_Non-contact_3D_displacement_measurement_of_structure_based_on_the_fusion_of_millimeter_wave_radar_and_digital_image_correlation.pdf` | 05_multi_target_full_field | M05/M14/M19/M15 | A | 用LFMCW雷达相位提取目标out-of-plane位移，用单目2D-DIC得到in-plane位移。根据观测点和目标点的水平/垂直角度做坐标映射，再把雷达与DIC分量标定后融合重建3D位移。 |
| `05_multi_target_full_field/C07_Using_Geometrical_Information_to_Measure_the_Vibration_of_a_Swaying_Millimeter-wave_Radar.pdf` | 05_multi_target_full_field | M14/M15/M20 | A | 把环境中的参考物作为几何基准，利用雷达与参考物在不同时刻形成的面积差估计平面摆动位移。对空间摆动则利用参考物构成的体积差估计自振幅，并由几何变化给出粗略方向。 |
| `05_multi_target_full_field/Full-field 3D displacement measurement via microwave sensing.pdf` | 05_multi_target_full_field | M09/M11/M14/M15/M20 | A | 用三个不共线微波收发机和参考目标建立device/structural coordinate systems。把同一测点自动匹配到各雷达的range-angle热图，取得三个LOS位移，解三元几何方程并变换到结构坐标系得到全场3D位移。 |
| `05_multi_target_full_field/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf` | 05_multi_target_full_field | M08/M09/M11/M15/M16 | A | 用MIMO雷达生成range-angle联合热图，在每个目标位置跟踪慢时间复数相位演化以测量微动。用高通滤波抑制低频运动/温漂，并以目标相位历史的时变稀疏性与空间定位排除静态杂波后逐目标输出振动。 |
| `05_multi_target_full_field/Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf` | 05_multi_target_full_field | M05/M06/M09/M11/M15/M20 | A | 提出adaptive segmented phase demodulation（ASPD），根据位移尺度分段解调以覆盖微米到分米范围。对range-angle联合维度做改进的interferometric phase evolution tracking，分离邻近目标的耦合/混叠并逐目标恢复位移。 |
| `06_gbsar_microwave_interferometry/B10_Measurement_Refinements_of_Ground-Based_Radar_Interferometry_in_Bridge_Load_Test_Monitoring.pdf` | 06_gbsar_microwave_interferometry | M06/M08/M14/M20 | T | 检测桥塔位移序列中的GB-radar phase jumps，删除异常跳变并恢复正确的unwrapped phase。投影计算中使用目标变形后的几何关系而非只使用初始LOS，从而补偿结构变形带来的厘米级投影误差，并保留沉降慢变趋势。 |
| `06_gbsar_microwave_interferometry/B12_Analysis_of_bridge_dynamic_load_test_based_on_millimeter_wave_radar.pdf` | 06_gbsar_microwave_interferometry | M05/M14/M16 | A | 对连续雷达回波相位做相邻采样干涉，得到目标LOS位移；根据雷达视线与桥梁几何关系把LOS分量投影成竖向挠度。再由位移时程和频谱提取一阶模态频率、车辆激励频率和冲击系数。 |
| `06_gbsar_microwave_interferometry/Bridge Monitoring Strategies for Sustainable Development with Microwave Radar Interferometry.pdf` | 06_gbsar_microwave_interferometry | M03/M05/M08/M14/M16 | T | 将极化分析与微波干涉结合，分别在RAR、SFCW线性合成孔径和MIMO阵列上获取桥梁响应。InSAR部分用双差相位去除平地/地形/噪声项，再用LOS投影向量解释变形分量，并从干涉位移时程给出频谱。 |
| `06_gbsar_microwave_interferometry/Ground-based radar interferometry for monitoring the dynamic performance of a multitrack steel truss high-speed railway bridge.pdf` | 06_gbsar_microwave_interferometry | M05/M14/M15/M16 | T | 使用IBIS-S地基微波干涉雷达，在多个距离单元和不同观测方位提取桥梁梁、轨道和附属构件的LOS位移。结合LiDAR点云解释目标空间位置和几何方向，并比较列车/地铁/风荷载时程及频谱以得到动态响应和空间变形图。 |
| `06_gbsar_microwave_interferometry/Radar-based multipoint displacement measurements of a 1200-m-long suspension bridge.pdf` | 06_gbsar_microwave_interferometry | M01/M05/M14/M15/M20 | T | 对每个距离单元的I/Q beat signal做FFT，同时读取频谱峰的相位并按干涉关系换算LOS位移。利用三个参考点估计桥梁/基座几何运动，对梁、塔、缆多点位移作修正，并绘制多点位移影响线。 |
| `07_radar_sensor_fusion/Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf` | 07_radar_sensor_fusion | M06/M18/M19/M20 | A | 初始阶段为多个雷达目标选择good targets并标定各自方向转换因子；目标可见时用加速度辅助相位解缠并在目标间切换。全部目标遮挡时用加速度重构位移，目标恢复后用多目标相位构造绝对解缠结果并消除遮挡造成的漂移。 |
| `07_radar_sensor_fusion/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf` | 07_radar_sensor_fusion | M05/M06/M18/M19/M20 | A | 从FMCW IF做FFT并用选定目标相位得到雷达位移；初始同步段自动选择目标并估计LOS到结构方向转换因子。雷达目标遮挡时以检测器切换到应变计ANN位移与加速度支路，恢复后用边界校正消除漂移并回到雷达—加速度FIR融合。 |
| `07_radar_sensor_fusion/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf` | 07_radar_sensor_fusion | M05/M06/M14/M19/M20 | A | 用同步雷达—ADXL355短时数据自动筛选有效大振幅片段和最佳雷达目标，估计LOS到结构方向比例系数。运行时以加速度预测辅助相位解缠，再将雷达低频位移与加速度高频位移通过FIR互补滤波输出连续位移。 |
| `07_radar_sensor_fusion/Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf` | 07_radar_sensor_fusion | M16/M19/M20 | A | 把FMCW雷达位移转换为低频结构加速度支路，把MEMS加速度作为高频支路。有限冲击响应互补滤波器合并两支路，输出的是结构加速度而不是位移；实验用LDV比较时域/频域并验证抑制MEMS漂移和雷达噪声。 |
| `07_radar_sensor_fusion/Structural Displacement Estimation of Rail Bridges Through Millimeter-Wave Radar, Accelerometers, and Non-Dedicated Multi-Modal Sensing.pdf` | 07_radar_sensor_fusion | M05/M06/M14/M19/M20 | A | 共址60 GHz FMCW雷达与三轴MEMS加速度计采集同步数据，自动按雷达/加速度高频位移RMSE选择反射目标并标定方向转换因子。加速度辅助预测用于每个采样点的2π相位解缠，随后用FIR合并雷达和加速度位移；另以NTP同步的既有通信光纤做分布式应变扩展。 |
| `07_radar_sensor_fusion/Structural displacement estimation using accelerometer and FMCW millimeter wave radar.pdf` | 07_radar_sensor_fusion | M05/M06/M14/M19/M20 | A | 从多个FMCW距离峰分别提取雷达相位，并用同步加速度双积分位移比较各候选目标的高频RMSE，选出best target和LOS转换因子。运行时用加速度辅助相位解缠，再用FIR把雷达低频位移和加速度高频位移合成为结构位移。 |
| `08_radar_calibration_tracking/A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf` | 08_radar_calibration_tracking | M01/M03/M05/M09/M14 | R | FMCW前端正交混频得到I/Q beat signal，DFT/FFT的频率峰给出距离、固定距离bin的相位变化给出高精度位移。通过多个不同距离目标的beat频率分离实现多目标测量，并用参考点几何关系推导3D位移的线性化解。 |
| `08_radar_calibration_tracking/Anchor-Based, Real-Time Motion Compensation for High-Resolution mmWave Radar.pdf` | 08_radar_calibration_tracking | M08/M10/M20 | R | 从场景中选取静态anchor回波，把平台复杂运动映射为复数相位/频率调制项。用anchor估计并反卷积补偿非谐瞬态和多模态谐振造成的谱展宽，再在低延迟约束下恢复目标距离/速度谱。 |
| `08_radar_calibration_tracking/Incoherent Interference Detection and Mitigation for Millimeter-Wave FMCW Radars.pdf` | 08_radar_calibration_tracking | M08/M20 | R | 对接收复信号取幅值并用低通FIR检测干扰包络，把标记干扰区当作缺失数据。将回波恢复写成L1正则最小二乘问题，使用ADMM求解并重建受干扰的FMCW echo。 |
| `08_radar_calibration_tracking/Multiple-target tracking and track management for an FMCW radar network.pdf` | 08_radar_calibration_tracking | M09/M10/M18 | R | 直接在beat-frequency measurement space把每个chirp的测量与已有track关联，避免先计算range/range-rate和多边定位。逐chirp处理把数据关联分解为二维assignment，再用轨迹初始化、更新和删除规则管理杂波中的多目标track。 |
| `08_radar_calibration_tracking/Recent Advances in mmWave-Radar-Based Sensing, Its Applications, and Machine Learning Techniques: A Review.pdf` | 08_radar_calibration_tracking | M01/M09/M10/M11/M17 | G | 综述IF信号到range profile、range–azimuth heatmap和3D scatter plot的解释链，并汇总CFAR、DBSCAN、点云分割、特征/数据级融合和深度学习模块。它是方法索引和来源导航，不应作为单一算法实验依据。 |
| `08_radar_calibration_tracking/Transversal Displacement Detection of an Arched Bridge with a Multimonostatic Multiple-Input Multiple-Output Radar.pdf` | 08_radar_calibration_tracking | M05/M14/M20 | A | 分别对单站和多单站FMCW-MIMO复回波沿快时间FFT取得距离，再用相邻采样相位差换算LOS位移。雷达与同步transponder形成两个不同LOS观测，解2×2几何方程得到桥面水平/竖向分量，并用误差传播预测几何不确定度。 |
| `08_radar_calibration_tracking/多径利用雷达目标探测技术综述与展望.pdf` | 08_radar_calibration_tracking | M08/M09/M10/M14/M17 | G | 综述空中和地面平台的多径利用雷达链路：多径传播建模与回波提取、距离/多普勒/角度检测、镜像几何定位、波束形成/RMA/MSBP成像和多径目标跟踪。文章用于补充NLOS/多径模块来源，不代表本课题的单一测振算法。 |
| `_web_supplements/anghel2014_short_range_fmcw.pdf` | _web_supplements | M01/M05/M06/M08 | R/G | 采用异频 X 波段 FMCW 接收机避开近距离自混频低频噪声；用高阶模糊函数估计 VCO 多项式非线性，再通过时间重采样校正 beat 信号。校正后的 beat 频率给出距离，干涉相位用于毫米级位移。 |
| `_web_supplements/bi2018_multi_arc.pdf` | _web_supplements | M03/M04/M05/M07 | T/G | 在 Doppler CW 雷达接收链中插入数字控制相移器，针对同一运动生成多个相位偏移 IQ 弧；每条弧独立做圆心/半径拟合，再融合多个圆心并进行反正切相位解调。多弧增加有效弧长，降低短弧和 DC 偏置造成的位移误差。 |
| `_web_supplements/high_efficiency_superresolution_fmcw.pdf` | _web_supplements | M01/M09/M12/M13 | R/G | 先用 FFT 粗估目标距离，再按粗距离自适应截取所需采样点数，把缩小后的数据送入 MUSIC 超分辨率估计。该“FFT 粗定位 + ROI 超分辨”链路在保持分辨率的同时减少 MUSIC 运算量。 |
| `_web_supplements/hosseiny2023_mimo_gbsar.pdf` | _web_supplements | M01/M05/M09/M11/M15 | R/G/A | 以 W 波段 MIMO GBSAR 做距离压缩、方位合成孔径处理和干涉相位计算；MIMO 虚拟阵列提供同距多目标的角度分辨，GBSAR 扫描轨道提高横向分辨率。实验把 MIMO GBSAR 与 MIMO 雷达干涉结果对齐，验证位移监测一致性。 |
| `_web_supplements/kim2019_qfg.pdf` | _web_supplements | M03/M04/M07 | R/G | 用一组离散载频构造 QFG 正交雷达，使同一小位移在复平面形成多个离散椭圆弧；比较几何和代数圆/椭圆拟合估计 IQ 中心并完成相位解调。多频弧在无需机械位移台或 RF 相移器的情况下延长有效拟合弧长。 |
| `_web_supplements/kim2022_fmcw_reduced_search_music.pdf` | _web_supplements | M01/M02/M09/M12 | R/G | 先用 FFT 估计 FMCW 目标距离/速度并缩小数据量，再在估计目标附近限制 MUSIC 伪谱搜索区间；用该“FFT 粗估计 + 局部子空间搜索”保持接近 MUSIC 的分辨率，同时降低计算复杂度。 |
| `_web_supplements/lee2021_cw_detrending.pdf` | _web_supplements | M03/M04/M05/M08 | T/G | 对 CW 雷达基带 I/Q 在时间窗口内用多项式拟合估计慢变 DC drift，先从信号中去除漂移，再执行圆拟合的 DC 偏置/失衡校准和相位解调。该前置 detrending 使极低频漂移不再扭曲小振动位移。 |
| `_web_supplements/michel2022_natural_frequency_gbr.pdf` | _web_supplements | M05/M08/M14/M16/M20 | R/G/A | 从 GBR 干涉相位得到多点 LOS 位移，并以最小二乘复频率/频域峰值估计桥梁固有频率；将 GBR 频率与 FDD 和应变传感器结果比较。进一步用线性温度模型解释频率漂移，为频率质量评估和结构状态判别提供校正。 |
| `_web_supplements/rodrigues2022_modwt_jump_removal.pdf` | _web_supplements | M05/M06/M08/M17 | T/G | 先按雷达 I/Q 圆拟合和非线性相位解调得到位移，再对位移时间序列做最大重叠离散小波变换（MODWT）多分辨率分解。利用各尺度系数识别瞬时跳变/短时畸变，重构校正后的位移而不改变正常振动分量。 |
| `_web_supplements/sipos2021_sfcw_static_echo_cancellation.pdf` | _web_supplements | M01/M08/M10 | R/G | 在 SFCW 每个频点估计静态目标回波，并用与静态回波幅相匹配的主动/被动抵消分量进行实时回波消除；通过恒定性判决识别静态目标。该链路降低强静态杂波和接收机饱和，保留动态目标的距离/相位观测。 |
| `_web_supplements/sotoudeh2025_gbir_review.pdf` | _web_supplements | M01/M05/M06/M08/M14/M16 | T/G | 系统综述 104 篇 GBIR 桥梁监测论文，按 GB-RAR/GB-SAR 体制、range-bin 生成、干涉相位位移、相位解缠/噪声处理、LOS 几何解释和模态参数提取归纳方法链。它是方法与应用索引，不提出单一新的雷达估计算法。 |
| `_web_supplements/wang2022_gbrar_colored_noise.pdf` | _web_supplements | M05/M06/M08/M16/M20 | R/G/A | 从 GB-RAR 干涉相位生成桥梁形变时间序列后，先用功率谱分析区分白噪声与有色噪声，再以最大似然估计有色噪声谱指数并修正形变估计。将校正后的沉降速率与水准测量比较，形成面向桥梁监测的不确定度处理链。 |
| `_web_supplements/zakrzewski2014_ellipse_thesis.pdf` | _web_supplements | M03/M04/M05/M17 | T/G | 系统研究正交 CW Doppler 雷达的 IQ 失衡估计、椭圆拟合仿射归一化和非线性相位解调，并比较不同中心估计方法。该工作为后续雷达小位移链路提供 ellipse→circle 校准和低噪声相位提取的可迁移基线。 |

| `_web_supplements/marino2018_ground_based_radar_bridge_vibration.pdf` | 00_fmcw_phase_displacement | M01/M05/M08/M16/M20 | R/A | 5–6 GHz SFCW 地基雷达；iFFT 距离压缩、相邻脉冲相位差、时间相干性检查、3-bin boxcar 和经验三角波匹配滤波，用于桥梁车辆振动峰检测。|
| `_web_supplements/lasri2025_insar_bridge_anomaly.pdf` | 06_gbsar_microwave_interferometry | M05/M08/M14/M16/M20 | T/A | Sentinel-1 MT-DInSAR；分区 LOS 平均、升降轨 East/Up 反演、温度回归、残差和 Hotelling T² 控制图检测桥梁异常。|

## 网络优先全文补充（已汇总至雷达目录）

这些全文原保存在检索审计目录；现通过硬链接汇总，保留检索位置便于复核。按 SHA-256 核实，12 份均为此前雷达目录未收录的不同内容。

| 本地路径 | 论文 | 模块 | 方法模块 |
|---|---|---|---|
| `_web_priority_fulltext/R0038.pdf` | _web_priority_fulltext | M09/M10/M18/M05/M06 | R/A | 双目视觉锁定 FMCW range bin→FFT 峰值选择→相位提取、展开、滤波并分离多目标生命信号。 |
| `_web_priority_fulltext/R0041.pdf` | _web_priority_fulltext | M03/M05/M06/M08/M13/M16 | R/G | FMCW IF 相位→圆心动态跟踪校正 DC→DACM 展开→CS-OMP 与 RA-DWT 分离呼吸/心跳→FFT/自相关估计。 |
| `_web_priority_fulltext/R0146.pdf` | _web_priority_fulltext | M01/M05/M06/M16 | R/G | SAR 回波距离压缩与距离徙动校正后，逐距离单元提取相位历史；用小波变换去除平台/目标慢变项，再估计单/多频振动幅值和频率。 |
| `_web_priority_fulltext/R0162.pdf` | _web_priority_fulltext | M15/M16 | R/A | 干涉雷达多索位移→APES短时高分辨时频→基频/弦振动方程→索力 |
| `_web_priority_fulltext/R0174.pdf` | _web_priority_fulltext | M01/M03/M05/M08 | R/G | FMCW beat FFT→椭圆近似相位校正/DC偏置抑制→位移 |
| `_web_priority_fulltext/R0310.pdf` | _web_priority_fulltext | M19/M20 | G/A | 由加速度等观测进行梁结构动态位移重构，并与不同数据融合重构技术比较 |
| `_web_priority_fulltext/R0328.pdf` | _web_priority_fulltext | M19/M20 | G/A | 低成本多传感器桥梁SHM系统联合振动、准静态与冲刷环境传感 |
| `_web_priority_fulltext/R0418.pdf` | _web_priority_fulltext | M14/M20 | R/A | 双RAR同步测量垂向/纵向响应，降低单雷达解释误差 |
| `_web_priority_fulltext/R0553.pdf` | _web_priority_fulltext | M19 | G/T | 由加速度测量重构浮体动态位移，并比较不同数据重构技术 |
| `_web_priority_fulltext/R0649.pdf` | _web_priority_fulltext | M19/M20 | G | 多传感器运动学量融合，统一位置/速度/加速度观测和不确定度 |
| `_web_priority_fulltext/R0665.pdf` | _web_priority_fulltext | M19/M20 | G/A | 应变模态叠加得到应变位移→与加速度经 Kalman 滤波→实时塔体位移重构。 |
| `_web_priority_fulltext/R0761.pdf` | _web_priority_fulltext | M17/M19 | G/A | 桥梁加速度/倾角模态→独立成分分析提取 surrogate inclination mode shapes→数据融合估计加速度。 |

## 公开入口但未复制到本地的补充论文

以下论文已纳入模块地图，但出版社/仓储下载受限或本轮没有保存本地 PDF；README 中保留 DOI/官方入口，避免把“未下载”误解为“未调查”。
| 论文 | 模块 | 官方入口 |
|---|---|---|
| Singh et al., Data-Based Quadrature Imbalance Compensation for a CW Doppler Radar System | M03 ellipse/IQ imbalance | https://doi.org/10.1109/TMTT.2013.2249525 |
| Zakrzewski et al., Comparison of center estimation algorithms for heart and respiration monitoring with microwave Doppler radar | M03/M04 circle-center estimation | https://doi.org/10.1109/JSEN.2011.2119299 |
| Gao et al., Non-contact Displacement Estimation Using Doppler Radar | M04/M05 CW arc and nonlinear demodulation | https://doi.org/10.1109/EMBC.2012.6346251 |
| Xiong et al., Static clutter elimination for FMCW radar displacement measurement based on phasor offset compensation | M08 static clutter/phasor offset | https://doi.org/10.1049/el.2017.2915 |
| Chen et al., Radar Sensing of Displacement Motions With High Robustness Against Additive Noise | M08 low-SNR phase/noise model | https://doi.org/10.1109/TMTT.2023.3284264 |
| Xiong et al., An Effective Accuracy Evaluation Method for LFMCW Radar Displacement Monitoring With Phasor Statistical Analysis | M20 phasor-based uncertainty/accuracy | https://doi.org/10.1109/JSEN.2019.2938620 |
| Guan et al., Automated DC offset calibration strategy for structural health monitoring based on portable CW radar sensor | M03 automatic DC calibration | https://doi.org/10.1109/TIM.2014.2317298 |
| Zhao et al., Accurate DC offset calibration of Doppler radar via non-convex optimisation | M03 robust circle-center calibration | https://doi.org/10.1049/el.2015.1181 |
| Pieraccini et al., Static and dynamic testing of bridges through microwave interferometry | M06/M14 early bridge microwave interferometry | https://doi.org/10.1016/j.ndteint.2006.10.007 |
| Pieraccini et al., An interferometric MIMO radar for bridge monitoring | M11/M14 MIMO interferometric bridge monitoring | https://doi.org/10.1109/LGRS.2019.2900405 |
| Miccinesi & Pieraccini, Bridge monitoring by a monostatic/bistatic interferometric radar able to retrieve the dynamic 3D displacement vector | M14 monostatic/bistatic 3D LOS inversion | https://doi.org/10.1109/ACCESS.2020.3039381 |
| Farrar et al., Microwave interferometers for noncontact vibration measurements on large structures | M04/M05 early microwave structural vibration baseline | https://doi.org/10.1006/mssp.1998.1216 |
| Su et al., FMCW radar dynamic demodulation: Enabling accurate vibration measurement | M01/M05 dynamic beat demodulation | https://doi.org/10.1016/j.ymssp.2026.114224 |
| Guerzoni et al., A novel Doppler-based phase unwrapping algorithm for mmWave MIMO radars | M02/M06 Doppler-aided unwrap | https://doi.org/10.1016/j.ymssp.2025.112777 |

## 2010 年以后网络扩展清单（第一批人工扩展记录，40 条）

这一节是针对上一轮“网上文献只有 12 篇”的补充调查。这里的“在线入口”表示只登记 DOI/官方页面；“本地补充全文”和“已有本地 PDF”表示网络论文已经落到当前工作区。部分论文同时出现在前面的核心卡片或本地索引中，因此本表是扩展调查记录，不直接等同于新增唯一论文数量。

| 论文 | 年份 | 模块 | 方法模块摘要 | 当前状态 | DOI/入口 |
|---|---:|---|---|---|---|
| Guan et al., 2014, Automated DC Offset Calibration Strategy for SHM Based on Portable CW Radar Sensor | 2014 | M03 | 2.4/24 GHz CW；按信号特征自动选择 DC-offset 校准法。 | 在线入口 | https://doi.org/10.1109/TIM.2014.2317298 |
| Guan et al., 2015, Dynamic and Static Structural Displacement Measurement Using Backscattering DC Coupled Radar | 2015 | M03/M05 | DC-coupled CW + backscatter/transponder，同时测静态和动态位移。 | 在线入口 | https://doi.org/10.12989/sss.2015.16.3.521 |
| Guan et al., 2017, Structural Displacement Measurements Using DC Coupled Radar with Active Transponder | 2017 | M03/M05/M08 | 主动转发器提升 SNR、抑制杂波，输出结构位移。 | 已有本地 PDF | https://doi.org/10.1002/stc.1909 |
| Zhao et al., 2015, Accurate DC Offset Calibration of Doppler Radar via Non-convex Optimisation | 2015 | M03/M08 | IRL1 重加权 L1 估计 DC offset，处理稀疏离群点。 | 在线入口 | https://doi.org/10.1049/el.2015.1181 |
| Gu et al., 2016, High-Precision Motion Detection Using Low-Complexity Doppler Radar With Digital Post-Distortion | 2016 | M03/M05 | 数字后失真恢复 AC 耦合 CW 雷达的慢周期运动。 | 在线入口 | https://doi.org/10.1109/TMTT.2016.2519881 |
| Rodrigues et al., 2020, Adaptive Displacement Calibration Strategies for Field SHM Based on Doppler Radars | 2020 | M05/M08/M20 | ALFA/AJSPA 自适应低通和联合处理，校正反正切解调突跳。 | 在线入口 | https://doi.org/10.1109/TIM.2020.2982233 |
| Rodrigues et al., 2021, Wind-Induced Displacement Analysis for a Traffic Light Structure Based on a Low-Cost Doppler Radar Array | 2021 | M15/M16 | 多 5.8 GHz Doppler 阵列同步测位移、频率和空间模态。 | 在线入口 | https://doi.org/10.1109/TIM.2021.3098380 |
| Rodrigues et al., 2022, A MODWT-Based Algorithm for Identification and Removal of Jumps/Short-Term Distortions | 2022 | M08/M16 | Haar-MODWT 多分辨率检测相位跳变和短时畸变。 | 本地补充全文 | https://doi.org/10.3390/iot3010003 |
| Lee et al., 2021, Detrending Technique for Denoising in CW Radar | 2021 | M03/M08 | 多项式 detrending 去除时变 DC drift，再进行圆拟合。 | 本地补充全文 | https://doi.org/10.3390/s21196376 |
| Jiang et al., 2025, On Amplitude Modulation in CW Doppler Radars Using ENVSIL Radar | 2025 | M05/M08 | 自注入锁定 CW 中利用 AM/PM 互补恢复运动。 | 在线入口 | https://doi.org/10.1109/TMTT.2024.3470819 |
| Wang et al., 2014, Noncontact Distance and Amplitude-Independent Vibration Measurement Based on Extended DACM | 2014 | M05 | extended DACM 从 I/Q 相位导数估计位移，降低对振幅变化和 atan2 的依赖。 | 在线入口 | https://doi.org/10.1109/TIM.2013.2277530 |
| Xiong et al., 2018, Accurate and Robust Displacement Measurement for FMCW Radar Vibration Monitoring | 2018 | M01/M05/M06 | 零填充 FFT 估 beat frequency + 跨 sweep approximate ML 相位 + 解缠。 | 在线入口 | https://doi.org/10.1109/JSEN.2017.2778294 |
| Xiong et al., 2017, Static Clutter Elimination for FMCW Radar Displacement Measurement | 2017 | M04/M08 | phasor offset compensation 去除同 range-bin 静态散射造成的圆心偏置。 | 在线入口 | https://doi.org/10.1049/el.2017.2915 |
| Anghel et al., 2014, Short-Range Wideband FMCW Radar for Millimetric Displacement Measurements | 2014 | M01/M05/M08 | HAF + time-resampling 修正 VCO 扫频非线性，再做 range-gate/干涉相位。 | 本地补充全文 | https://doi.org/10.1109/TGRS.2013.2291573 |
| Ding et al., 2016, Vibration Parameter Estimation Using FMCW Radar | 2016 | M01/M02/M07 | FMCW 振动参数模型、频率/幅值估计和 CRLB。 | 在线入口 | https://doi.org/10.1109/ICASSP.2016.7472072 |
| Šipoš & Gleich, 2021, SFCW Radar with an Integrated Static Target Echo Cancellation System | 2021 | M08 | 静态目标模板/相位校准 + 主动回波抵消，抑制强静态背景。 | 本地补充全文 | https://doi.org/10.3390/s21175829 |
| Kim et al., 2022, FMCW Radar Estimation Algorithm with High Resolution and Low Complexity Based on Reduced Search Area | 2022 | M12/M13 | 2D FFT 粗估 range/DOA，再缩小 MUSIC 搜索区域。 | 本地补充全文 | https://doi.org/10.3390/s22031202 |
| Kim et al., 2021, High-Efficiency Super-Resolution FMCW Radar Algorithm Based on FFT Estimation | 2021 | M12/M13 | FFT 初估 + MUSIC 超分辨，降低搜索范围和计算量。 | 本地补充全文 | https://doi.org/10.3390/s21124018 |
| Zhang et al., 2018, Dynamic Displacement Monitoring of Long-Span Bridges with a Microwave Radar Interferometer | 2018 | M04/M06/M09 | 微波干涉、多 range-bin、两步相位解缠和桥梁动态响应。 | 在线入口 | https://doi.org/10.1016/j.isprsjprs.2018.02.020 |
| Huang et al., 2020, Ground-Based Radar Interferometry for a Multitrack Steel Truss High-Speed Railway Bridge | 2020 | M06/M09/M16 | GB-RAR 多点位移、FFT 频谱和模态频率分析。 | 已有本地 PDF | https://doi.org/10.3390/rs12162594 |
| Li et al., 2020, Radar-Based Multipoint Displacement Measurements of a 1200-m Suspension Bridge | 2020 | M01/M04/M09 | 微波干涉雷达通过 I/Q FFT 相位同时测多点。 | 已有本地 PDF | https://doi.org/10.1016/j.isprsjprs.2020.06.017 |
| Michel & Keller, 2021, Advancing Ground-Based Radar Processing for Bridge Infrastructure Monitoring | 2021 | M04/M06/M08/M14/M20 | 扰动/静态杂波剔除、圆拟合、LOS→三维投影和不确定度。 | 在线入口 | https://doi.org/10.3390/s21062172 |
| Michel & Keller, 2022, Determining and Investigating the Variability of Bridges’ Natural Frequencies with Ground-Based Radar | 2022 | M16/M20 | 衰减振动段最小二乘正弦拟合估频，与 FDD 交叉验证。 | 本地补充全文 | https://doi.org/10.3390/app12115354 |
| Wang et al., 2022, GB-RAR Deformation Information Estimation Considering Colored Noise | 2022 | M08/M20 | GB-RAR 彩色噪声建模和滤波，改善形变估计。 | 本地补充全文 | https://doi.org/10.3390/app122010504 |
| Zou et al., 2024, Strategy for Vertical Deformation of Railway Bridge Monitoring Using Polarimetric GB-RAR | 2024 | M03/M14 | 极化通道/散射点选择 + 相位干涉 + 垂向几何投影。 | 在线入口 | https://doi.org/10.1177/14759217231226128 |
| Measurement Refinements of Ground-Based Radar Interferometry in Bridge Load Test Monitoring | 2024 | M06/M08/M14 | 异常 phase jump 检测、Akima 插值恢复、实时几何投影。 | 已有本地 PDF | https://doi.org/10.3390/rs16111882 |
| Lipták et al., 2013, Monitoring of Bridge Dynamics by Radar Interferometry | 2013 | M06/M16 | GBIR 动态变形和频谱分析。 | 在线入口 | https://doi.org/10.14311/gi.12.2 |
| 3-D Spatial-Temporal Phase Unwrapping Method of GB-InSAR | 2023 | M06/M08 | minimum-cost-flow 初解 + 空间/时间约束修复区域解缠错误。 | 在线入口 | https://doi.org/10.15918/j.tbit1001-0645.2023.067 |
| Michel et al., 2026, Ground-Based Interferometric Radar for Bridge Dynamic System Identification | 2026 | M16/M20 | Cov-SSI、EFDD、时域/频域/时频一致性组成模态识别框架。 | 在线入口 | https://doi.org/10.1016/j.ndteint.2026.103649 |
| Transversal Displacement Detection of an Arched Bridge with a Multimonostatic MIMO Radar | 2024 | M11/M14 | 多单站 MIMO FMCW 多视线几何反演水平/竖向位移。 | 已有本地 PDF | https://doi.org/10.3390/s24061839 |
| Enhanced Beamspace MUSIC for Cost-Effective FMCW Automotive Radar | 2020 | M12 | beamspace 降维 + MUSIC 超分辨 DOA。 | 在线入口 | https://doi.org/10.1049/iet-rsn.2019.0342 |
| A Novel Range Estimation Method Based on MUSIC High-Resolution Profile | 2024 | M01/M12 | 60 GHz FMCW 用 MUSIC 同时精估近邻 range/angle。 | 在线入口 | https://doi.org/10.1109/ACES-China62474.2024.10699781 |
| Accuracy Analysis and Appropriate Strategy for Determining Dynamic and Quasi-Static Bridge Response Using Two Real-Aperture GB Radars | 2023 | M14/M20 | 双 GB radar 同步 LOS 方程反演二维/三维位移，分析时间同步和几何不确定度。 | 在线入口 | https://doi.org/10.3390/rs15030837 |
| Hosseiny et al., 2023, Interferometric Processing of a Developed MIMO GBSAR for Displacement Monitoring | 2023 | M09/M11/M14 | MIMO GBSAR 角度区分同距目标，并比较 MIMO 与 GBSAR 干涉位移。 | 本地补充全文 | https://doi.org/10.5194/isprs-annals-X-4-W1-2022-301-2023 |
| Sotoudeh et al., 2025, A Systematic Review into GBIR for Bridge Monitoring | 2025 | M01–M20 综述 | 统计 104 篇 GBIR 桥梁论文，归纳目标提取、模态参数和加速度融合。 | 本地补充全文 | https://doi.org/10.3390/rs17091541 |
| Zhao et al., 2022, Dynamic Deformation Measurement of Bridge Structure Based on GB-MIMO Radar | 2022 | M08/M10/M16/M20 | 改进杂波抑制、两步像素提取、频域与时域环境激励联合稳定模态识别；用两座悬索桥和一座斜拉桥验证。 | 在线摘要 | https://doi.org/10.1109/TGRS.2022.3197227 |
| Zhang et al., 2026, Radar-Based Bridge Vibration Frequency Estimation under Moving Target Interference | 2026 | M08/M16/M17 | 动态 clutter map + STFT + StOMP，抑制车辆/行人干扰下的频率估计偏差。 | 在线入口 | https://doi.org/10.1049/icp.2026.0555 |
| Rodrigues & Li, 2021, A Review on Low-Cost Microwave Doppler Radar Systems for SHM | 2021 | M01–M08/M15 综述 | 系统归纳 CW Doppler、IQ/arctan、circle fit、时频和结构监测。 | 在线入口 | https://doi.org/10.3390/s21082612 |
| Ma et al., 2023, Structural Displacement Sensing Techniques for Civil Infrastructure: A Review | 2023 | M01/M06/M14/M19 综述 | 梳理 IF→FFT→range→phase→LOS→转换因子及雷达–加速度融合。 | 已有本地 PDF | https://doi.org/10.1016/j.iintel.2023.100041 |
| Ciattaglia et al., 2024, Displacement Evaluation by mmWave FMCW Radars: Method and Performance Metrics | 2024 | M20 | 用 LDV 对比毫米波雷达位移准确度/精度，整理性能指标。 | 在线入口 | https://iris.univpm.it/handle/11566/335992 |
| A Review of Microwave Radar Technology for Monitoring Bridges and Other Civil Structures | 2026 | M01–M20 综述 | 按 FMCW/SFCW/SAR/MIMO 分类整理桥梁监测体制、方法和挑战。 | 在线入口 | https://doi.org/10.1016/j.istruc.2026.112512 |

## 阅读和使用规则

- 先读 `03_range_velocity_target_processing/mmVib_MobiCom2020.pdf`、`02_phase_unwrap_denoise/Accurate structural displacement...pdf`、`07_radar_sensor_fusion/Structural displacement estimation using accelerometer...pdf` 和 `04_aoa_beamforming_mimo/Millimeter-Wave Bat...pdf`，再按 M01–M20 选模块。
- 对每个模块记录四件事：输入复数数据形态、输出变量、成立前提、移植到 IWR + ADXL355 时需要的改动。
- 论文写作时把“已有 primitive / 通用数学 / 场景适配 / 胶水方法”分栏，不能把公开算法换一个传感器或换一个场景就写成算法首创。
- 本地 PDF 仅作个人研究资料，引用时以论文 DOI、出版社页面或作者公开版本为准。
- 2010+ 候选的可复核检索、逐条审阅包和当前筛选状态见 [`docs/radar_method_search_2010_2026/README.md`](../../docs/radar_method_search_2010_2026/README.md)；审阅包位于 `docs/radar_method_search_2010_2026/review_2026_10_08/`，完成一进一出的逐条决策后再把方法卡片并入本 README。
- 当前阶段从 1,779 条联合候选中形成了 700 张经最终一致性审计、能够写出输入→处理→输出的方法卡片；566 条保留为 context，508 条排除，5 条因无可核实算法证据保留 `pending`。逐条当前索引见 [`docs/radar_method_search_2010_2026/review_2026_10_08/MODULE_INDEX_FINAL.md`](../../docs/radar_method_search_2010_2026/review_2026_10_08/MODULE_INDEX_FINAL.md)；历史 727/539 快照仍保留用于追溯。
- 已下载全文的摘要级方法证据和页码索引见 [`docs/radar_method_search_2010_2026/local_fulltext_evidence.md`](../../docs/radar_method_search_2010_2026/local_fulltext_evidence.md)。
