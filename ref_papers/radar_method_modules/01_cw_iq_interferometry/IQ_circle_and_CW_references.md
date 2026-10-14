# IQ 圆拟合与 CW 雷达补偿参考文献

本索引把通用圆拟合、CW 雷达 IQ 圆心/DC offset 补偿、I/Q 椭圆校正和
FMCW/mmWave 迁移分开记录。`本地全文`表示 PDF 已在仓库中；`在线入口`
表示保留 DOI 或开放网页，尚未复制出版社 PDF。

## 1. 数学基础

| 文献 | 模块 | 状态 |
|---|---|---|
| I. Kåsa, “A Curve Fitting Procedure and Its Error Analysis,” *IEEE Transactions on Instrumentation and Measurement*, 25(1), 8–14, 1976. DOI: [10.1109/TIM.1976.6312298](https://doi.org/10.1109/TIM.1976.6312298) | Kåsa 代数圆拟合：将圆参数估计化为线性最小二乘 | 在线入口 |
| W. Gander, G. H. Golub, and R. Strebel, “Least Squares Fitting of Circles and Ellipses,” *BIT Numerical Mathematics*, 34, 558–578, 1994. DOI: [10.1007/BF01934268](https://doi.org/10.1007/BF01934268) | 圆/椭圆最小二乘方法比较 | 在线入口 |

## 2. CW 雷达 IQ 圆心与 DC offset

| 文献 | 模块 | 状态 |
|---|---|---|
| M. Park et al., “Arctangent Demodulation With DC Offset Compensation in Quadrature Doppler Radar Receiver Systems,” *IEEE Transactions on Microwave Theory and Techniques*, 55(5), 1073–1079, 2007. DOI: [10.1109/TMTT.2007.895653](https://doi.org/10.1109/TMTT.2007.895653) | 正交 CW 的 DC offset 补偿与 atan2 解调 | 在线入口 |
| M. Zakrzewski, H. Raittinen, and J. Vanhala, “Comparison of Center Estimation Algorithms for Heart and Respiration Monitoring With Microwave Doppler Radar,” *IEEE Sensors Journal*, 12(3), 627–634, 2012. DOI: [10.1109/JSEN.2011.2119299](https://doi.org/10.1109/JSEN.2011.2119299) | CW IQ 圆心估计方法比较 | 在线入口 |
| S. Guan, J. A. Rice, C. Li, and C. Gu, “Automated DC Offset Calibration Strategy for Structural Health Monitoring Based on Portable CW Radar Sensor,” *IEEE Transactions on Instrumentation and Measurement*, 63(12), 3111–3118, 2014. DOI: [10.1109/TIM.2014.2317298](https://doi.org/10.1109/TIM.2014.2317298) | 面向结构位移的 CW DC offset 自动校准 | 在线入口 |
| M. Mercuri et al., “Analysis of Signal Processing Methods to Reject the DC Offset Contribution of Static Reflectors in FMCW Radar-Based Vital Signs Monitoring,” *Sensors*, 22(24), 9697, 2022. DOI: [10.3390/s22249697](https://doi.org/10.3390/s22249697)，[开放全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9781610/) | 在 FMCW/mmWave range-bin IQ 上比较 AC coupling、代数圆拟合和几何圆拟合 | 在线入口（开放全文） |

## 3. I/Q 不平衡：椭圆到圆的校正

| 文献 | 模块 | 状态 |
|---|---|---|
| A. Singh et al., “Data-Based Quadrature Imbalance Compensation for a CW Doppler Radar System,” *IEEE Transactions on Microwave Theory and Techniques*, 61(4), 1718–1724, 2013. DOI: [10.1109/TMTT.2013.2249525](https://doi.org/10.1109/TMTT.2013.2249525) | 基于椭圆拟合的数据驱动幅度/相位不平衡校正 | 在线入口 |
| M. Zakrzewski et al., “Quadrature Imbalance Compensation With Ellipse-Fitting Methods for Microwave Radar Physiological Sensing,” *IEEE Transactions on Microwave Theory and Techniques*, 62(6), 1400–1408, 2014. DOI: [10.1109/TMTT.2014.2321738](https://doi.org/10.1109/TMTT.2014.2321738) | 椭圆拟合、仿射归一化和 LM 几何拟合；本地补充全文见 [`_web_supplements/zakrzewski2014_ellipse_thesis.pdf`](../_web_supplements/zakrzewski2014_ellipse_thesis.pdf) | 本地全文（作者版本） |
| Lee et al., “Detrending Technique for Denoising in CW Radar,” *Sensors*, 21(19), 6376, 2021. DOI: [10.3390/s21196376](https://doi.org/10.3390/s21196376) | 先去除时变 DC drift，再做 I/Q 校准和圆拟合 | 本地补充全文：[`_web_supplements/lee2021_cw_detrending.pdf`](../_web_supplements/lee2021_cw_detrending.pdf) |

## 4. 短弧、多弧和小位移

| 文献 | 模块 | 状态 |
|---|---|---|
| X. Gao et al., “Arc Shifting Method for Small Displacement Measurement With Quadrature CW Doppler Radar,” *2017 IEEE MTT-S International Microwave Symposium*. DOI: [10.1109/MWSYM.2017.8058760](https://doi.org/10.1109/MWSYM.2017.8058760) | 通过 arc shifting 增加有效拟合弧段，改善短弧圆心估计 | 在线入口 |
| Bi et al., “A Multi-Arc Method for Improving Doppler Radar Motion Measurement Accuracy,” 2018. [公开 PDF](https://music-sustech.github.io/publication/sjbi2018.pdf) | 多弧、逐弧拟合与融合 | 本地补充全文：[`_web_supplements/bi2018_multi_arc.pdf`](../_web_supplements/bi2018_multi_arc.pdf) |
| D. K. Kim and Y. Kim, “Quadrature Frequency-Group Radar and Its Center Estimation Algorithms for Small Vibrational Displacement,” *Scientific Reports*, 9, 6763, 2019. DOI: [10.1038/s41598-019-43205-7](https://doi.org/10.1038/s41598-019-43205-7) | 用多频率 QFG 增加 IQ 拟合点，改善小振动条件 | 本地补充全文：[`_web_supplements/kim2019_qfg.pdf`](../_web_supplements/kim2019_qfg.pdf) |

## 与当前代码的对应关系

当前 [`system/algorithm/phase.py`](../../../system/algorithm/phase.py) 使用的是递推的
Kåsa 型代数圆拟合：估计每个目标的圆心和半径，执行圆心平移与半径归一化，再计算
相邻 IQ 点的相位增量。它**没有**实现 Singh/Zakrzewski 论文中的完整椭圆到圆仿射校正。

因此论文中应分别引用：Kåsa 作为拟合数学基础，Zakrzewski/Guan/Mercuri 作为雷达
IQ 圆心和 DC offset 补偿依据；只有真正加入 I/Q 椭圆校正时，才把 Singh 和
Zakrzewski 2014 作为该模块的直接依据。
