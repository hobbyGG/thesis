# 本文算法方法说明

本文档描述当前唯一的算法路径。对比方法、临时分支和未采用的 ADXL 辅助相位约束
不属于代码实现或论文主方法。

## 1. 研究目标与边界

研究目标是利用安装于磁浮轨道梁的 IWR1843BOOST 毫米波雷达与 ADXL355 加速度计，
测量结构沿主振动方向的动态位移。雷达从静止参考散射体的回波中提取视线（line of
sight, LOS）方向相位，加速度计提供结构加速度形式的动力学先验，多个距离—角度
目标共同观测同一个结构状态。

当前验证使用 A20 参数化响应仿真与统一采集包。真值（`truth/`）仅在评估阶段用于
计算 RMSE，不参与目标检测、角度估计、转换系数 $\beta_i$ 计算、相位提取与 Kalman
滤波。

## 2. 算法流程

```text
500 Hz 帧级 adc_cube（4 个 MIMO loop 复数相干平均）
→ Hamming 窗 Range FFT
→ 8 虚拟阵元 DBF（数字波束形成）
→ 首帧距离—角度候选峰检测
→ 固定目标 range/angle bin 的慢时间 IQ 序列
→ 递推代数圆拟合与 IQ 圆心补偿
→ 最近邻 2π 相位展开
→ 由首帧 DBF 角度确定固定转换系数 β_i
→ ADXL 原生时间轴区间预积分
→ 共享结构相位 Kalman 滤波
→ 结构位移
```

实测采集与仿真须先生成同一格式的采集包（`capture_root`）。算法不接触 PCAP、LVDS、
串口、GPIO 或硬件生命周期。

## 3. 雷达与加速度计参数

| 项目 | 当前值 |
|---|---:|
| 起始载频 | 77 GHz |
| ADC | 256 点，5.209 MS/s |
| 调频斜率 | 70 MHz/μs |
| 快时间窗 | Hamming |
| 阵列 | 4 RX，TX0+TX2 TDM，8 虚拟阵元 |
| 帧内 loop | 4 个 MIMO loop，复数相干平均 |
| 雷达慢时间采样 | 500 Hz，帧周期 2 ms |
| ADXL355 | 500 Hz 原生输出数据率，使用结构垂向轴 |

等效载频取 ADC 快时间孔径中心处的瞬时频率：

$$
f_{\mathrm{eff}} = f_0 + S\left(t_{\mathrm{start}} + \frac{N-1}{2F_s}\right),
\qquad \lambda = \frac{c}{f_{\mathrm{eff}}},
$$

其中 $f_0$ 为起始载频，$S$ 为调频斜率，$t_{\mathrm{start}}$ 为 ADC 起始时刻，
$N$ 为每个 chirp 的采样点数，$F_s$ 为 ADC 采样率。该修正仅用于相位—位移换算的
参考波长，不引入新的测量信息。

## 4. 距离—角度目标检测

对每帧、每个虚拟阵元的快时间信号 $x_f[v,n]$ 加 Hamming 窗并做 FFT：

$$
X_f[r,v] = \mathrm{FFT}_n\{w_H[n]\,x_f[v,n]\}.
$$

对半波长间距虚拟阵列，阵元位置 $p_v = 0.5v$（单位：波长），导向矢量为

$$
a_v(u) = e^{-j2\pi p_v u},
$$

其中 $u=\sin\theta$。采用加窗 DBF：

$$
Y_f[r,a] = \sum_{v} X_f[r,v]\,w_v\,a_v(u_a).
$$

候选目标仅由首帧的距离—角度幅值图确定：以幅值的中位数加 6 倍 MAD（median
absolute deviation）作为阈值，保留 $3\times3$ 邻域内的二维局部极大值，合并距离
相差不超过 1 个距离单元且角度差小于 $15^\circ$ 的峰值，并在最强目标 20 dB 动态范围内
至多保留 5 个目标。其后各帧仅提取这些固定目标位置处的复数 DBF 输出。

## 5. IQ 圆心补偿与相位提取

对每个目标，各帧得到慢时间 IQ 序列：

$$
z_k = I_k + jQ_k .
$$

静止参考目标的 IQ 点理想情况下位于以 $c$ 为圆心的圆弧上，圆心偏移由直流偏置及
静态杂波叠加引起。本文采用递推的代数（Kåsa 型）最小二乘圆拟合估计圆心 $c_k$
与半径 $R_k$：法方程的充分统计量按时间顺序累加，第 $k$ 帧的估计仅使用 $0,\dots,k$
时刻的样本。当累积样本少于 3 个，或法方程条件数不小于 $10^{4}$ 时，保持上一次圆参数
不变（初始为零圆心）。

在首次接受圆拟合之前，相位以原点为参考；该阶段产生的相位误差作为常值偏移保留在累积相位中，
后续步骤不予修正，因此拟合收敛所需的弧长（取决于位移幅度与噪声）决定了冷启动误差。

圆心补偿后的 IQ 与半径归一化 IQ 分别为

$$
\tilde z_k = z_k - c_k,
\qquad
\bar z_k = \tilde z_k / R_k ,
$$

其中 $\bar z_k$ 仅用于诊断。相位增量以当前圆心 $c_k$ 同时作为相邻两个样本的参考，
以避免圆心更新引入虚假相位跳变：

$$
\Delta\phi_k = \arg\!\left[(z_k - c_k)\,(z_{k-1} - c_k)^{*}\right],
\qquad
\phi_k = \sum_{m\le k}\Delta\phi_m .
$$

累积相位首个有效样本处为零，输出前取主值区间 $(-\pi,\pi]$ 内的包裹相位。随后按
最近邻 $2\pi$ 准则，由该目标上一时刻的展开相位确定当前展开相位：

$$
\phi_k^{\mathrm{u}} = \phi_k^{\mathrm{w}} + 2\pi\,\mathrm{round}\!\left(\frac{\phi_{k-1}^{\mathrm{u}} - \phi_k^{\mathrm{w}}}{2\pi}\right).
$$

相位展开不依赖 ADXL 加速度。

## 6. 视线—主方向转换系数

DBF 角度单元给出目标角度 $\theta_i$（首帧确定）。结构主振动方向与 LOS 方向之间的
几何转换系数取

$$
\beta_i = \frac{1}{|\cos\theta_i|},
$$

第 $i$ 个目标映射到结构主方向的相位观测为

$$
y_{i,k} = \beta_i\,\phi^{\mathrm{u}}_{i,k}.
$$

实现中对 $|\cos\theta_i|$ 设有下限 $10^{-6}$ 以避免除零。$\beta_i$ 由首帧角度一次确定，在整段记录内保持固定，不由 Kalman 后验反向修正。
角度估计误差属于独立的几何误差来源，当前滤波器不对其进行补偿。

## 7. ADXL 预积分与共享状态 Kalman 滤波

ADXL 数据保留其原生时间戳。对相邻雷达观测时刻 $t_{k-1}$ 与 $t_k$ 之间的区间，
以区间内的 ADXL 原生采样时刻为节点，节点间加速度按分段线性处理；区间两端点的
加速度取不晚于该端点的最近一个 ADXL 样本（零阶保持），以避免使用未来样本。
由此计算区间内的速度增量与以区间起点速度为零参考的位移增量：

$$
\Delta v_k = \int_{t_{k-1}}^{t_k} a(t)\,\mathrm{d}t,
\qquad
\Delta q_k = \int_{t_{k-1}}^{t_k}\!\!\int_{t_{k-1}}^{s} a(\tau)\,\mathrm{d}\tau\,\mathrm{d}s .
$$

起点速度对位移的贡献 $\Delta t_k\,\dot q_{k-1}$ 由下述状态转移矩阵体现。

结构相位状态向量及其定义为

$$
x_k = \left[\Theta_k,\ \dot\Theta_k\right]^{\mathsf T},
\qquad
\Theta_k = \frac{4\pi q_k}{\lambda}.
$$

状态预测为

$$
x_k^{-} =
\begin{bmatrix}1 & \Delta t_k\\ 0 & 1\end{bmatrix} x_{k-1}^{+}
+ \frac{4\pi}{\lambda}
\begin{bmatrix}\Delta q_k\\ \Delta v_k\end{bmatrix},
\qquad
P_k^{-} = A_k P_{k-1}^{+} A_k^{\mathsf T} + \sigma_a Q_k,
$$

其中 $Q_k$ 为白噪声加速度模型的过程噪声协方差矩阵，$\sigma_a$ 为过程噪声强度。

同一时刻所有有效目标共同观测该结构状态。按各目标测量方差的倒数进行加权合并：

$$
z_k = \frac{\sum_i R_i^{-1}\,y_{i,k}}{\sum_i R_i^{-1}},
\qquad
R_k = \Big(\sum_i R_i^{-1}\Big)^{-1},
$$

并以 $H=[1,\ 0]$ 对共享状态执行一次标量测量更新。各目标测量方差 $R_i$ 按后验残差
递推更新（带遗忘因子，并限制在 $[10^{-4},\,25]$ 范围内），残差较大的目标权重相应降低：

$$
R_i \leftarrow \rho\,R_i + (1-\rho)\left[(y_{i,k} - \hat\Theta_k^{+})^2 + P^{+}_{k,00}\right].
$$

初始 $R_i$ 由该目标首个样本的归一化幅度给出，幅度较弱的目标获得较大的初始方差。
最终位移估计为

$$
\hat q_k = \frac{\lambda\,\hat\Theta_k}{4\pi}.
$$

## 8. 代码模块

| 文件 | 作用 |
|---|---|
| `system/algorithm/io.py` | 读取采集包并构造算法输入 |
| `system/algorithm/frontend.py` | Range FFT、DBF 与目标 IQ 提取 |
| `system/algorithm/selection.py` | 首帧候选目标检测与目标选择 |
| `system/algorithm/phase.py` | 递推圆拟合、圆心补偿与最近邻相位展开 |
| `system/algorithm/acceleration.py` | ADXL 时间区间预积分 |
| `system/algorithm/kalman.py` | 固定转换系数 $\beta_i$ 的共享结构 Kalman 滤波 |
| `system/algorithm/run.py` | 命令行入口与结果导出 |
| `paper_bridge_simulation/` | A20 参数化采集包生成 |
| `system/capture_program/` | 实测硬件采集与采集包导出 |
