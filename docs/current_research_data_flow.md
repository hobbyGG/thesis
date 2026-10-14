# 本文算法数据流与实验边界

本文档与 [本文算法方法说明](current_method_specification.md) 配套，说明从硬件采集或
A20 参数化仿真到结构位移输出的唯一数据路径。

## 1. 三层边界

```text
system/capture_program/
  IWR1843 + DCA1000 + ADXL355 + 时间轴
          ↓ capture_root
paper_bridge_simulation/
  A20 q(t)、a(t) 与同格式采集包
          ↓ capture_root
system/algorithm/
  Range FFT → DBF → IQ 圆心补偿 → β_i → ADXL 预积分 → Kalman
```

算法只读取采集包，不读取 PCAP、不控制设备、不生成仿真场景。仿真 `truth/` 仅用于
末端评估。

## 2. 实测采集链

IWR1843BOOST 产生 TX0/TX2 TDM-MIMO chirp，DCA1000 接收 LVDS 数据；树莓派负责
雷达 UART、DCA 数据、ADXL355 SPI/DRDY 及同步时间轴。采集程序先完成硬件生命周期、
数据包完整性与文件完整性检查，再导出：

```text
radar/algorithm_input/adc_cube.npy
radar/algorithm_input/chirp_cube.npy
radar/algorithm_input/frame_times_s.npy
radar/algorithm_input/manifest.json
adxl355/algorithm_input/acceleration_mps2.npy
adxl355/algorithm_input/estimated_sample_monotonic_ns.npy
adxl355/algorithm_input/manifest.json
sync/timeline.json
sync/radar_adc_sample_monotonic_ns.npy
```

雷达参数为：起始载频 77 GHz，256 个 ADC 采样点，采样率 5.209 MS/s，调频斜率
70 MHz/μs，每帧 4 个 MIMO loop，帧周期 2 ms（500 Hz）。每帧的 4 个 loop 保留在无损
`chirp_cube` 中，并沿 loop 维做复数相干平均，得到算法使用的 `adc_cube`。ADXL355
输出数据率为 500 Hz，算法保留其原生时间戳，不将两个独立时钟的数据重采样为同一
采样流。

## 3. A20 参数化仿真

`response.py` 依据 A20 文献公开的梁长、车速、六阶模态频率与阻尼，生成共同的结构
位移 $q(t)$ 与加速度 $a(t)$。每次车辆通过响应持续 0.8 s，响应间隔 5 s，总记录 13 s；
总位移峰值缩放至 1.712 mm。

`package_builder.py` 按与实测一致的硬件时序参数逐 ADC 快时间采样点生成信号。
目标差拍频率与相位为

$$
f_b = \frac{2SR}{c},
\qquad
\phi_R = \frac{4\pi R}{\lambda}.
$$

模型包含目标 LOS 投影、传播相位、TDM 阵列相位、距离衰减、弱多径、静态散射体、
接收通道幅相失配、简化的公共相位噪声、接收机噪声与 ADC 量化。雷达数据按每块 32 帧
写入内存映射文件，静态散射体的相位在整段记录内保持连续，避免分块边界处出现非物理
的相位跳变。

ADXL355 的每个 DRDY 样本取 $a(t_k-\tau_g)$，$\tau_g=3.26$ ms 为 500 Hz ODR 下的
数字滤波群延迟；导出的 `estimated_sample_monotonic_ns` 与采集程序在配置了
`group_delay_ns` 时的规则相同，为 DRDY 时刻减去 $\tau_g$。可选的 `Impairments`
参数（默认不启用）用于鲁棒性实验：雷达 SNR 偏移与 IQ 偏置、目标晃动、雷达缺帧、ADXL
静态偏置（含重力投影）、零偏随机游走、噪声倍率、比例误差、倾斜耦合、时间偏移与抖动、
DRDY 时钟相位与 ODR 误差；`Scenario` 参数化结构响应与雷达场景，`ensemble.draw_case(seed)`
给出随机场景（取值范围见 `paper_bridge_simulation/README.md`）。

## 4. 本文算法

### 4.1 采集包读取与时间轴

`io.load_capture_package()` 读取帧级 `adc_cube`、雷达参考时间、ADXL 原生加速度及其
时间戳。算法采用与 ADC 孔径中心对应的雷达时间，并以相邻雷达时间戳之间的区间作为
预积分边界。`build_algorithm_inputs()` 由 `extract_targets`（前端与目标检测）、
`build_radar_input`（圆拟合与目标选择）和 `build_acceleration_input`（零偏扣除与预积分）
组成，实验代码直接复用这三个函数。

### 4.2 Range FFT 与 DBF

每帧 ADC 数据沿快时间乘 Hamming 窗后做 FFT。对 8 个虚拟阵元，采用半波长间距的
导向矢量做 DBF，得到距离—角度复数图。首帧幅值图经局部峰值检测、MAD 阈值、近邻
峰合并与动态范围筛选，至多保留 5 个候选目标。

### 4.3 目标慢时间 IQ 与转换系数

其后各帧仅在固定的目标 range/angle 单元处读取复数 DBF 输出，得到目标级慢时间序列
$z_{i,k}=I_{i,k}+jQ_{i,k}$。目标角度 $\theta_i$ 由 DBF 角度单元给出，转换系数
$\beta_i = 1/|\cos\theta_i|$ 在整段记录内保持固定。

### 4.4 IQ 圆心补偿与相位提取

对每个目标独立递推地做代数（Kåsa 型）圆拟合，第 $k$ 帧的圆心 $c_{i,k}$ 仅由
$0,\dots,k$ 时刻的样本估计。相位增量以当前圆心作为相邻两个样本的共同参考：

$$
\Delta\phi_{i,k} = \arg\!\left[(z_{i,k}-c_{i,k})\,(z_{i,k-1}-c_{i,k})^{*}\right].
$$

累积相位取主值包裹，随后以目标上一时刻的展开相位为参考做最近邻 $2\pi$ 展开。
ADXL 不参与圆拟合与相位展开。

### 4.5 ADXL 预积分

结构主轴加速度先扣除记录起始 0.2 s 静止窗内的均值（重力投影与器件零偏），再对每个
雷达区间以区间内的 ADXL 原生采样为节点做分段线性积分，区间端点取不晚于端点的最近
ADXL 样本，得到

$$
\Delta v_k = \int_{t_{k-1}}^{t_k} a(t)\,\mathrm{d}t,
\qquad
\Delta q_k = \int_{t_{k-1}}^{t_k}\!\!\int_{t_{k-1}}^{s} a(\tau)\,\mathrm{d}\tau\,\mathrm{d}s .
$$

### 4.6 共享结构相位 Kalman 滤波

状态为结构主相位及其变化率。ADXL 预积分量作为控制输入进入状态预测；各目标 LOS
相位乘以固定转换系数 $\beta_i$ 后，构成对同一结构状态的观测。当前有效目标按
$R_i^{-1}$ 加权合并后执行一次 Kalman 更新；$R_i$ 由各目标的后验残差递推更新。
位移输出为 $q=\lambda\Theta/(4\pi)$。

## 5. 评估边界

仿真结果可用于评估统一采集包、目标提取、IQ 圆心补偿、ADXL 预积分与共享 Kalman
滤波整条处理链的误差（RMSE）。评估协议（保留种子、对比方法、统计）见
`docs/current_method_specification.md` §9，结果见 `experiments/results/summary.md`。
其结论不能替代与激光位移计的实测对比；实测数据还须
独立标定阵列幅相、安装角、雷达等效载频、雷达时间延迟，以及 ADXL 的轴向与延迟。

完整入口：

```bash
python3 -m system.algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/algorithm-result.npz
```
