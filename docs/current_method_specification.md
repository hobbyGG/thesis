# Base 论文方法说明

本文档只描述当前唯一算法路径。对比方法、临时分支和未采用的 ADXL IQ 圆约束
不属于代码或论文主方法。

## 1. 研究目标和边界

目标是用安装在磁浮轨道梁上的 IWR1843BOOST 毫米波雷达和 ADXL355，测量结构沿
主振动方向的动态位移。雷达从静止参考散射体得到 LOS 相位，ADXL 提供结构加速度
动态先验；多个距离—角度目标共同观测一个结构状态。

当前验证使用 A20 参数化响应仿真和统一采集包。`truth/` 只在末端计算 RMSE，
不进入目标检测、角度、beta、相位或 Kalman。

## 2. 唯一数据流

```text
500 Hz 帧级 adc_cube（4-loop 复数平均）
→ Hamming 窗普通 Range FFT
→ 8 虚拟阵元 Angle DBF
→ 首个观测的距离—角度候选峰
→ 冻结目标 range/angle bin 的 slow-time IQ
→ 因果 IQ 圆拟合与圆心校正
→ 普通最近 2π 相位连续
→ 冻结 AoA beta
→ ADXL 原生时间轴区间预积分
→ 共享结构主相位 Kalman
→ 结构位移
```

真实采集和仿真必须先生成同一个 `capture_root`。算法不接触 PCAP、LVDS、串口、
GPIO 或硬件生命周期。

## 3. 雷达和 ADXL 参数

| 项目 | 当前值 |
|---|---:|
| 起始载频 | 77 GHz |
| ADC | 256 点，5.209 MS/s |
| 调频斜率 | 70 MHz/μs |
| 快时间窗 | Hamming |
| 阵列 | 4 RX、TX0+TX2 TDM，8 虚拟阵元 |
| 帧内 loop | 4 个 MIMO loop，复数相干平均 |
| 雷达慢时间 | 500 Hz，2 ms 帧周期 |
| ADXL355 | 500 Hz 原生 ODR，使用结构垂向轴 |

有效载频取 ADC 快时间孔径中心：

\[
f_{eff}=f_0+S\left(t_{start}+\frac{N-1}{2F_s}\right),
\qquad \lambda=c/f_{eff}.
\]

这是相位参考修正，不增加新的测量信息。

## 4. 距离—角度目标

对每个帧和虚拟阵元做 Hamming 窗普通 FFT：

\[
X_f[r,v]=FFT\{w_H[n]x_f[v,n]\}.
\]

对半波长虚拟阵列构造 steering vector：

\[
a_v(u)=e^{-j2\pi p_vu},\qquad p_v=0.5v,
\]

并执行 DBF：

\[
Y_f[r,a]=\sum_v X_f[r,v]w_va_v(u_a).
\]

候选检测只使用第一个观测：中位数幅值和 MAD 形成阈值，保留二维局部峰，合并
距离相差不超过 1 个 bin 且角度差小于 15° 的峰，在最强目标 20 dB 动态范围内
最多保留 5 个目标。后续帧只提取这些冻结目标的复数 IQ。

## 5. IQ 圆和相位

每个目标每个观测得到：

\[
z_k=I_k+jQ_k.
\]

代码按时间递推代数圆拟合，只使用当前及过去点，得到圆心 (c_k) 和半径 (R_k)：

\[
\tilde z_k=z_k-c_k,
\qquad
\bar z_k=\tilde z_k/R_k.
\]

归一化 IQ 仅用于诊断；当前相位由圆心校正后的相邻复数点得到：

\[
\Delta\phi_k=\arg\left[(z_k-c_k)(z_{k-1}-c_k)^*\right].
\]

累计相位在输出给 Kalman 前取包裹值，再由上一时刻目标相位执行普通最近 (2\pi)
分支连续。解缠不依赖 ADXL。

## 6. AoA 几何校正

DBF 角度 bin 给出目标角度 (\thetaheta_i)。结构主方向和 LOS 的转换系数为：

\[
\beta_i=1/|\cos\theta_i|.
\]

第 (i) 个目标的观测为：

\[
y_{i,k}=\beta_i\phi_{i,k}.
\]

(\betaeta_i) 在记录开始时计算并在整段记录内冻结，不由 Kalman 后验反向修改。
角度误差属于独立的几何误差源，不能由当前滤波器自动消除。

## 7. ADXL 预积分和共享 Kalman

ADXL 保留原生时间戳。对每个相邻雷达时间区间计算：

\[
\Delta v_k=\int a(t)dt,
\qquad
\Delta q_k=\int v(t)dt.
\]

Kalman 状态为：

\[
x_k=[\Theta_k,\dot\Theta_k]^T,
\qquad \Theta_k=4\pi q_k/\lambda.
\]

预测为：

\[
x_k^-=
\begin{bmatrix}1&\Delta t_k\\0&1\end{bmatrix}x_{k-1}^+
+\frac{4\pi}{\lambda}
\begin{bmatrix}\Delta q_k\\\Delta v_k\end{bmatrix}.
\]

同一时刻的所有有效目标共同观测这个结构状态。先按目标测量方差倒数进行加权：

\[
z_k=\frac{\sum_iR_i^{-1}y_{i,k}}{\sum_iR_i^{-1}},
\qquad
R_k=\left(\sum_iR_i^{-1}\right)^{-1},
\]

再执行一次共享状态更新。目标测量方差根据后验残差递推更新，弱目标的权重会
自然降低。最终位移为：

\[
\hat q_k=\lambda\hat\Theta_k/(4\pi).
\]

## 8. 当前代码分工

| 文件 | 作用 |
|---|---|
| `system/algorithm/io.py` | 读取输入包并构造算法输入 |
| `system/algorithm/frontend.py` | Range FFT、DBF 和目标 IQ |
| `system/algorithm/selection.py` | 候选目标检测和冻结选择 |
| `system/algorithm/phase.py` | 因果 IQ 圆拟合和相位连续 |
| `system/algorithm/acceleration.py` | ADXL 时间区间预积分 |
| `system/algorithm/kalman.py` | 固定 AoA beta 的共享结构 Kalman |
| `system/algorithm/run.py` | 唯一命令行入口和结果导出 |
| `paper_bridge_simulation/` | A20 参数化输入包生成 |
| `system/capture_program/` | 实测硬件采集和输入包导出 |
