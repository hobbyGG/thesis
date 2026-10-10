# 优先全文核验：可迁移到 IWR + ADXL355 的雷达方法模块

本表从 `review_2026_10_08/MODULE_INDEX.md` 的 659 条 module 记录中，优先挑出对“毫米波雷达测梁体振动、并与 ADXL355 加速度融合”最有用的链路。条目分为两类：

* **本地全文**：PDF 已保存在 `ref_papers/radar_method_modules/_web_supplements/`，页码是 PDF 页码；
* **开放全文/公开入口**：DOI 指向出版社或仓储的公开页面；部分为开放 HTML/PDF，部分目前只能稳定访问摘要。证据位置给出摘要、方法节或文章节号。仅有摘要证据的条目仍需在正式写作前补充正文页码。

“论文增量”描述的是该论文在现有方法链上增加的工程模块或组合方式，不把已有基本算子（FFT、atan2、圆/椭圆拟合、MUSIC、EMD 等）误写成首创。**已有先例**的意思是该模块在更早雷达文献中已经出现；**组合增量**表示论文把已有算子组合成适合某一体制/场景的胶水链；**算法增量**表示作者对算子本身作了明确修改。

## 1. IQ 几何、圆/椭圆拟合和多弧模块

| ID | 方法模块 | 原始雷达体制/场景 | 输入 → 输出 | 论文增量 | 已有先例 | 迁移到 IWR + ADXL355 的条件 | 证据 |
|---|---|---|---|---|---|---|---|
| T01 | QFG 多频分组 + IQ 中心估计 | 24 GHz/QFG 正交连续波，微小人体振动 | 多频 I/Q 弧 → 圆心、IQ 失配参数、位移 | 用一组频率在同一小位移下增加轨迹样本，改善小弧段拟合；QFG 是体制/采样组织增量 | 圆拟合、椭圆拟合和 DC/IQ 校准已有先例 | IWR 不能直接改变射频频率；可用相邻 chirp、多个稳定 range-bin 或多帧构造“虚拟多弧”，必须验证 chirp 间相位连续和散射点稳定 | [DOI](https://doi.org/10.1038/s41598-019-43205-7)；本地全文 [`kim2019_qfg.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/kim2019_qfg.pdf)，PDF pp.1–5, 9 |
| T02 | Phase-shifter 多弧圆拟合 | 2.4 GHz 正交 CW Doppler，3 mm 运动 | 多个相移 I/Q 弧 → 融合圆心/位移 | 通过相移器人为生成多个弧，再逐弧拟合并融合；改进的是数据覆盖和融合策略 | 单弧 circle fitting、相位解调已有先例 | IWR 中可将多 chirp/多频/多散射点作为多弧，但必须处理不同 chirp 的幅相漂移；ADXL355 可用于选择有效弧段和验证幅值 | [公开 PDF](https://music-sustech.github.io/publication/sjbi2018.pdf)；本地全文 [`bi2018_multi_arc.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/bi2018_multi_arc.pdf)，PDF p.1（摘要与误差实验） |
| T03 | 椭圆拟合 + affine normalization | 微波 CW 生理雷达，I/Q 失配校准 | 原始 I/Q 椭圆 → 圆化 I/Q、幅相失配参数 | 系统比较椭圆参数估计和圆化流程，并讨论运动覆盖不足时的失效条件 | 椭圆拟合、IQ imbalance compensation 早于该论文 | IWR 每个 range-bin 都要单独估计静态偏置和椭圆参数；ADXL355 不参与几何校准，只用于验证相位位移和检测失配漂移 | [DOI](https://doi.org/10.1109/TMTT.2014.2321738)；本地博士论文 [`zakrzewski2014_ellipse_thesis.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/zakrzewski2014_ellipse_thesis.pdf)，PDF pp.42–54（第4章） |
| T04 | Polynomial detrending → circle fitting | 5.8 GHz CW，DC drift/热漂移下的微动测量 | 基带 I/Q → 去趋势 → 圆拟合、位移 | 将慢变化 DC drift 从圆拟合前剥离，使原有 circle fit 在加热和环境振动下稳定；误差由约 1.34 mm 降到约 0.62 mm（摘要报告） | polynomial detrend 与 circle fit 均已有先例 | 对 IWR 需在选定 range-bin 的慢时间 I/Q 上建模低频漂移，不能直接把 CW 的 DC 项等同 FMCW 静态 range-bin 偏置；ADXL355 可提供低频趋势参考 | [DOI](https://doi.org/10.3390/s21196376)；本地全文 [`lee2021_cw_detrending.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/lee2021_cw_detrending.pdf)，PDF pp.1–4, 8–13 |
| T05 | 动态圆心跟踪 + DACM + CS-OMP + RA-DWT | 77 GHz FMCW，生命体征微位移 | IF 相位 I/Q → 动态圆心校正 → DACM 解缠 → 稀疏分离/小波降噪 → 呼吸/心跳频率 | 论文的核心是把多种已有算子组织成一条可运行的低 SNR 管线；动态圆心、DACM、CS-OMP、RA-DWT 的顺序是组合增量 | 圆心估计、DACM、压缩感知和小波去噪均有更早先例 | IWR 可保留“range-bin 复数慢时间→校正→解缠→分解”的框架；需将 CS 观测矩阵、RA-DWT 频带和质量门限按 10–100 Hz 梁模态重设；ADXL355 适合作为稀疏分离和频率输出的参考 | [开放全文](https://doi.org/10.3390/s20102999)，Abstract、Secs. 2–4；本地副本 [`R0041.pdf`](pdfs/R0041.pdf)，PDF pp.1, 3, 5–12, 15–21 |
| T06 | Modified DACM（MDACM）大位移解缠 | 120 GHz 毫米波干涉雷达，机械振动/手势大位移 | 连续 I/Q → 差分交叉相乘 → 积分相位/位移，并校正 AC 耦合、I/Q 失配和 DC 偏置 | 在 DACM 上增加非理想干涉器补偿，实验同时覆盖约 1 μm 微动和超过 40 个波长的大位移；基础 DACM 不是首创 | extended DACM 及其抗幅值变化版本已有先例 | 对 2 mm、100 Hz 梁振动，需要核验相邻采样相位增量、采样率和相位噪声；ADXL355 用来约束解缠突跳和校核大位移幅值 | [DOI](https://doi.org/10.1109/TMTT.2021.3103576)，Abstract、Secs. II–IV |
| T07 | 椭圆近似相位校正 + FMCW beat FFT | ISM-band FMCW，高精度运动检测 | beat 信号 → FFT/range → 椭圆近似校正与 DC 抑制 → 位移 | 将 I/Q 几何校正嵌入 FMCW 的 range-bin 管线，是体制迁移型组合 | 椭圆/圆校准和 beat FFT 均已有先例 | IWR 需区分 fast-time range FFT 与 slow-time vibration phase；校正参数要随 range-bin 和温漂更新，ADXL355 可作为相位质量判据 | [DOI](https://doi.org/10.3390/rs14010058)，Abstract、Secs. 2–4；本地副本 [`R0174.pdf`](pdfs/R0174.pdf)，PDF pp.1–6, 8–12, 14–17 |

## 2. FMCW 距离门控、MUSIC 和多目标/波束模块

| ID | 方法模块 | 原始雷达体制/场景 | 输入 → 输出 | 论文增量 | 已有先例 | 迁移到 IWR + ADXL355 的条件 | 证据 |
|---|---|---|---|---|---|---|---|
| T08 | FFT 粗估 + reduced-search MUSIC | FMCW 汽车雷达，多目标 range/angle | 2D FFT 粗峰 → 缩小伪谱搜索区 → MUSIC 高分辨 range/DOA | “先粗后精”的搜索区裁剪降低 MUSIC 计算量；MUSIC 本身已有先例 | FFT、MUSIC、协方差矩阵处理均已有先例 | IWR 可用 range FFT 锁定梁散射点，再用局部 MUSIC 分离近邻散射点；要保持复数相位，不要只输出检测峰；ADXL355 可帮助选择结构频带和判断伪峰 | [DOI](https://doi.org/10.3390/s22031202)；本地全文 [`kim2022_fmcw_reduced_search_music.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/kim2022_fmcw_reduced_search_music.pdf)，PDF pp.1–3, 6–15 |
| T09 | FFT 自适应采样裁剪 + MUSIC 超分辨 | FMCW 参数估计，目标距离明显小于最大量程 | FFT 粗距离 → 自适应减少 fast-time 样本 → MUSIC 参数估计 | 以距离估计决定输入长度，平均降低约 88% 计算量；是实时实现胶水 | FFT 粗估、MUSIC、样本裁剪都有先例 | IWR 实时处理可采用同样的近距离裁剪，但必须保证裁剪后慢时间相位参考不变；ADXL355 不参与距离估计，可用于判断裁剪后振动频谱是否保持 | [DOI](https://doi.org/10.3390/s21124018)；本地全文 [`high_efficiency_superresolution_fmcw.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/high_efficiency_superresolution_fmcw.pdf)，PDF pp.1–3, 6–12 |
| T10 | MUSIC-APES 同距近目标位移估计 | MIMO FMCW，同距离近目标 | MIMO 复数快/慢时间数据 → MUSIC-APES 分离 → 各目标位移 | 将子空间谱 MUSIC 和 APES 频谱估计串联，面向同距近目标快速位移估计 | MUSIC、APES 和阵列分离均已有先例 | IWR 需检验天线孔径、通道相位同步和同距散射点可观测性；ADXL355 可用于将分离出的目标振动频率与梁模态对齐 | [DOI](https://doi.org/10.3390/rs14092005)，开放全文 Abstract、Secs. 2–4 |
| T11 | Spatially resolved fast-time vibrometry | 超宽带 FMCW，多目标结构振动 | ADC/IF → fast-time range bin + 瞬时相位 → 误差模型/标定 → 多目标位移 | 将距离分辨与振动相位联合建模，并给出空间分辨振动测量/标定流程 | range FFT、相位干涉和误差标定均有先例 | IWR 要保持每 chirp 的快时间 range bin 一致；对 10–20 m 桥梁需评估 SNR、角反射器和相位噪声；ADXL355 用于频率/幅值独立验证 | [DOI](https://doi.org/10.1109/TMTT.2020.3038080)，Abstract、Secs. II–IV |
| T12 | FMCW range-bin + IQ 相位多目标位移 | FMCW 结构健康监测 | beat/range FFT → 选目标 range-bin → I/Q 相位 → 多目标位移 | 把 FMCW 距离门控与 CW 式 I/Q 相位解调组合到结构监测；贡献主要是完整实验链 | 各单步均已有先例 | IWR 可直接复用；需补充 range-bin 漂移跟踪、静态散射偏置和 ADXL355 时间同步 | [DOI](https://doi.org/10.3390/s150407412)，开放全文 Abstract、Secs. 2–4 |
| T13 | MIMO GBSAR 角度分离 + 干涉位移 | W-band MIMO GBSAR，结构形变 | MIMO 复回波 → range-angle/干涉处理 → 同距多目标形变 | 通过阵列维度把同距目标分开，再比较 MIMO 与 GBSAR 干涉结果；系统组合增量 | MIMO 成像、SAR 干涉、range-angle 分离均已有先例 | IWR 阵列较小，需验证角分辨率和通道相位一致性；ADXL355 可作为少量外部参考，不能替代阵列几何标定 | [DOI](https://doi.org/10.5194/isprs-annals-X-4-W1-2022-301-2023)；本地全文 [`hosseiny2023_mimo_gbsar.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/hosseiny2023_mimo_gbsar.pdf)，PDF pp.1–3, 5–6 |

## 3. 解调、杂波、跳变和时频分解模块

| ID | 方法模块 | 原始雷达体制/场景 | 输入 → 输出 | 论文增量 | 已有先例 | 迁移到 IWR + ADXL355 的条件 | 证据 |
|---|---|---|---|---|---|---|---|
| T14 | HAF + time-resampling 扫频线性化 | X-band 短距宽带 FMCW，毫米级位移 | 宽带 beat → 异频接收 → HAF 估计 VCO 非线性 → 时间重采样 → range/干涉相位 | 将 VCO 非线性校正放在 FMCW 位移链前端，降低距离和相位偏差 | 异频、HAF 和重采样在雷达校准中已有先例 | IWR 芯片 chirp 斜率通常已校准，但温漂/帧间残差仍可能影响 10 μm 级相位；需用静态目标和 ADXL355 估计残差 | [DOI](https://doi.org/10.1109/TGRS.2013.2291573)；本地全文 [`anghel2014_short_range_fmcw.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/anghel2014_short_range_fmcw.pdf)，PDF pp.2–10 |
| T15 | Haar-MODWT 跳变/短时失真修复 | Doppler 雷达结构健康监测，低 SNR 长期测量 | 相位解调位移序列 → MODWT 多分辨率系数 → 跳变检测/修复 → 连续位移 | 针对低 SNR 导致的相位突跳提出自动检测和修复方案；MODWT 本身是已有小波工具 | 小波/MODWT、阈值去噪已有先例；结构雷达跳变修复是场景增量 | IWR 需先区分真实高阶模态和失真；ADXL355 可作为“是否真实振动”的旁路判据，避免把 60–100 Hz 模态修成跳变 | [DOI](https://doi.org/10.3390/iot3010003)；本地全文 [`rodrigues2022_modwt_jump_removal.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/rodrigues2022_modwt_jump_removal.pdf)，PDF pp.1–8；开放 HTML 的摘要/方法见 DOI 页面 |
| T16 | EEMD + ESMD + SCBSS 盲源去噪 | GBSAR 桥梁动态挠度 | 多点位移时间序列 → EEMD/ESMD 分解 → 盲源分离 → 去噪位移 | 将两种自适应分解和结构约束盲源分离串成一条去噪链，是主要组合增量 | EEMD、ESMD、BSS 各自已有先例 | 单 IWR 点不足以稳定做 BSS；可用多个 range-bin/天线通道加 ADXL355 组成观测矩阵，并检查端点效应和模态混叠 | [DOI](https://doi.org/10.1109/JSTARS.2021.3061543)，Abstract、Secs. II–IV |
| T17 | SOBI + FFT 噪声分量识别 | GBSAR 桥梁动态挠度，多邻近点观测 | 多点位移 → 白化/SOBI 联合对角化 → FFT 识别噪声分量 → 置零/逆变换 | 将二阶盲辨识与频谱选择结合用于结构雷达去噪 | SOBI、FFT 和盲源分离已有先例 | 至少需要多个相邻散射点或多通道；ADXL355 可作为一个独立观测，但要检查其与雷达位移的量纲、相位和噪声协方差 | [DOI](https://doi.org/10.3390/app9173561)，开放全文 Abstract、Secs. 2–4 |
| T18 | 周期滤波 + 差分相位稳健估计 | 低 SNR 结构振动雷达 | 差分相位/位移 → 周期性滤波 → 抑制相位跳变和杂波误差 | 针对低 SNR 振动信号把周期先验引入滤波；周期滤波是场景化胶水，不是通用基础算子 | 低通、带通、周期平均和差分相位处理已有先例 | 你的梁前六阶分布在十几到六十几 Hz，周期滤波必须做多带并行或自适应，避免削弱非平稳模态；ADXL355 可提供周期先验和质量分数 | [DOI](https://doi.org/10.3390/rs15143461)，开放全文 Abstract、Secs. 2–5 |
| T19 | 彩色噪声建模 + MLE/滤波 | GB-RAR 高速铁路桥 | 形变序列 → 识别白/有色噪声 → MLE/滤波估计 → 校正形变 | 把噪声颜色纳入形变估计，而不是假设独立白噪声；贡献是噪声模型与估计器组合 | MLE、功率谱和有色噪声滤波已有先例 | IWR+ADXL355 融合时应估计两传感器的交叉协方差和频率相关噪声；不能直接把加速度白噪声积分成位移 | [DOI](https://doi.org/10.3390/app122010504)；本地全文 [`wang2022_gbrar_colored_noise.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/wang2022_gbrar_colored_noise.pdf)，PDF pp.1–4, 8–12 |
| T25 | 静态目标回波模板 + 主动回波抵消 | SFCW/GPR/TWIR，强静态目标和天线耦合 | 各频点复回波 → 静态背景/相位校准 → 生成相消回波 → 杂波抑制 | 将静态回波建模和主动抵消放到接收链，实测最高约 38 dB 抑制；核心增量是背景抵消架构 | 静态杂波估计、背景相减和自动增益控制已有先例 | 磁浮梁的固定支座、地面和雷达支架可能形成强静态散射；IWR 通常不能注入相消波形，可迁移为数字背景模板/复数偏置估计；ADXL355 可帮助区分静态背景与真实梁振动 | [DOI](https://doi.org/10.3390/s21175829)；本地全文 [`sipos2021_sfcw_static_echo_cancellation.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/sipos2021_sfcw_static_echo_cancellation.pdf)，PDF pp.1–8, 15 |

## 4. 模态、几何和质量/不确定度模块

| ID | 方法模块 | 原始雷达体制/场景 | 输入 → 输出 | 论文增量 | 已有先例 | 迁移到 IWR + ADXL355 的条件 | 证据 |
|---|---|---|---|---|---|---|---|
| T20 | 衰减正弦最小二乘 + FDD + 温度回归 | GBIR 桥梁自然频率 | 雷达位移衰减段 → LS 阻尼正弦拟合、FDD 交叉验证 → 固有频率；温度回归校正 | 把时域参数拟合、频域分解和温度补偿串成自然频率稳定估计链 | LS、FDD、温度回归均已有先例 | 适合你前六阶频率目标；ADXL355 可作为频率和阻尼的独立参考，雷达负责非接触位移；需保证自由衰减段或可辨识激励 | [DOI](https://doi.org/10.3390/app12115354)；本地全文 [`michel2022_natural_frequency_gbr.pdf`](../../../ref_papers/radar_method_modules/_web_supplements/michel2022_natural_frequency_gbr.pdf)，PDF pp.1–7, 9–15 |
| T21 | 多雷达 LOS → 3D 位移 + 不确定度预算 | Ku-band GB radar 桥梁监测 | 多视线位移、几何和环境指标 → LOS 分解/投影 → 三维位移与不确定度 | 将扰动/静态杂波/大气剔除、LOS 投影和误差预算放进统一工程链；胶水价值高于单一算子 | LOS 投影、最小二乘和不确定度传播已有先例 | IWR 单站通常只给 LOS；要获得竖向/横向需多视线、斜置传感器或结构先验；ADXL355 可提供一个高频加速度方向约束，但不能凭一轴加速度恢复全部 3D 位移 | [DOI](https://doi.org/10.3390/s21062172)；开放全文 [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8003812/)，Abstract、Secs. 2–5 |
| T22 | 79 GHz APS 评估/补偿 | 79 GHz GB radar interferometry 与 17 GHz GB-SAR 对照 | 多散射点相位时间序列 + 气象/参考点 → APS 估计/补偿 → 稳定形变 | 量化高频雷达大气相位屏对形变的影响，并验证补偿策略；补偿而非相位解调本身是增量 | APS、空间插值和时间序列校正已有先例 | 10–20 m 桥梁场景通常大气影响小于远距离 GB-SAR，但仍需现场验证；可用静态散射点估计公共相位，ADXL355 作为局部真实振动参考 | [DOI](https://doi.org/10.3390/rs15163931)，开放全文 Abstract、Secs. 2–5 |
| T23 | 多 LOS → 3D 位移的最小二乘调整 | MIMO-SAR/多视线结构监测 | 多个 LOS 位移 + 视线方向 → 空间/时间 LS 调整 → 3D 位移向量 | 给出从观测几何到三维位移的显式估计和可观测性条件；是可复用的几何胶水 | 最小二乘投影和多视线反演已有先例 | 至少需要两个以上非共线 LOS 或明确结构约束；ADXL355 可作为一个方向的动力学先验，但应在状态空间中处理，不宜简单相加 | [DOI](https://doi.org/10.1515/jag-2022-0035)，开放全文 Abstract、Secs. 2–4 |
| T24 | Persistent-scatterer 时间序列 + MIMO 横向分辨 | 毫米波 MIMO 管线微振动 | range-angle 复回波 → 稳定散射点选择/PSI 时间序列 → 管线微振动 | 把 PSI 的长期稳定散射点管理迁移到毫米波 MIMO 微振动，解决多散射点长期跟踪 | PSI、相干性和 MIMO 空间分辨已有先例 | IWR 必须保持通道相干、帧间时钟稳定和散射点不变；磁浮梁可布置角反射器/高反射贴片；ADXL355 可用于散射点质量打分 | [DOI](https://doi.org/10.1080/2150704x.2023.2291424)，Abstract、Secs. 2–4 |

## 5. 对本课题最值得组合的“胶水”候选

从上述 25 篇来看，真正适合写成你论文主创新的不是把每个基础算子都宣称为新方法，而是围绕一个明确失效问题组织模块。当前最有希望的三条链是：

1. **小位移低 SNR 链**：T01/T02 的多弧样本扩充 + T03/T04 的 IQ 几何校准 + T05/T06 的 DACM 解缠 + T15/T18 的跳变/周期质量控制。主胶水可以定义为“基于 ADXL355 先验的多弧相位质量门控与自适应解缠”。
2. **多散射点/近距离目标链**：T08/T09 的粗到精 MUSIC + T10/T11 的 MIMO/空间分离 + T12/T13 的 range-bin 相位位移。主胶水可以定义为“结构模态先验约束的 range-angle-IQ 联合跟踪”。
3. **工程精度与可解释性链**：T19 的有色噪声 + T20 的 LS/FDD 交叉验证 + T21–T23 的 LOS/3D/不确定度 + T24 的稳定散射点管理。主胶水可以定义为“雷达位移—加速度状态空间融合和质量分数传播”。

其中，T01–T07、T14–T19 的基础算子大多已有先例；可以被包装成小创新的是顺序、触发条件、质量门限、参数自适应和与 ADXL355 的耦合。主创新应落在一个可量化的失效问题上，例如 10 μm 级小位移、低 SNR、range-bin 漂移、相位跳变或多散射点混叠，而不是简单地把 FFT、圆拟合和 Kalman 滤波串起来。
