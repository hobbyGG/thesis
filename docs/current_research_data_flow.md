# Base 数据流与实验边界

本文档与 [Base 方法说明](current_method_specification.md) 配套，说明从硬件采集或
A20 参数仿真到结构位移输出的唯一数据路径。

## 1. 三层边界

```text
system/capture_program/
  IWR1843 + DCA1000 + ADXL355 + 时间轴
          ↓ capture_root
paper_bridge_simulation/
  A20 q(t)、a(t) 和同格式观测包
          ↓ capture_root
system/algorithm/
  Range FFT → DBF → IQ 圆 → beta → ADXL 预积分 → Kalman
```

算法只读取输入包，不读取 PCAP、不控制设备、不生成场景。仿真 `truth/` 只用于
末端评价。

## 2. 实测采集链

IWR1843BOOST 产生 TX0/TX2 TDM-MIMO chirp，DCA1000 接收 LVDS 数据；树莓派负责
雷达 UART、DCA 数据、ADXL355 SPI/DRDY 和同步时间轴。采集程序先完成硬件生命周期、
包完整性和文件完整性检查，再导出：

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

雷达使用 77 GHz、256 ADC 点、5.209 MS/s、70 MHz/μs 斜率、4 个 MIMO loop、
500 Hz 帧周期。每帧的 4 个 loop 保留在无损 `chirp_cube`，并沿 loop 做复数平均，
得到 base 使用的 `adc_cube`。ADXL355 使用 500 Hz ODR，算法保留其原生时间戳，
不把两个时钟伪造为同一采样流。

## 3. A20 参数仿真

`response.py` 根据 A20 公开的梁长、车速、六阶频率和阻尼生成共同的结构位移
(q(t)) 与加速度 (a(t))。每次响应为 0.8 s，响应间隔 5 s，总记录 13 s；总位移
峰值缩放到 1.712 mm。

`package_builder.py` 按同一硬件时间参数生成每个 ADC 快时间点：

\[
f_b=2SR/c,
\qquad
\phi_R=4\pi R/\lambda.
\]

模型包含目标 LOS 投影、传播相位、TDM 阵列相位、距离衰减、弱多径、静态散射、
RX 幅相误差、简化公共相噪、接收噪声和 ADC 量化。雷达数据按 32 帧分块写入
memmap，固定散射相位贯穿整段记录，避免分块边界产生非物理跳变。

## 4. Base 算法

### 4.1 读包和时间轴

`io.load_capture_package()` 读取帧级 `adc_cube`、雷达参考时间、ADXL 原生加速度
和时间戳。算法使用 ADC 孔径中心对应的雷达时间，随后以每两个雷达时间戳之间的
区间作为预积分边界。

### 4.2 Range FFT 和 Angle DBF

每帧 ADC 沿快时间乘 Hamming 窗后做普通 FFT。对 8 个虚拟阵元使用半波长 steering
vector 做 DBF，得到距离—角度复数图。首个观测的幅值图通过局部峰值、MAD 阈值、
近邻峰合并和动态范围筛选出最多 5 个候选。

### 4.3 目标 IQ

后续所有帧只从冻结的目标 range/angle bin 读取复数 DBF 输出，得到目标级
(z_{i,k}=I_{i,k}+jQ_{i,k})。目标角度由 DBF bin 给出，
(\betaeta_i=1/|\cos\theta_i|) 并在记录内冻结。

### 4.4 因果 IQ 圆和相位

每个目标独立递推代数圆拟合。当前点及此前点估计圆心后，计算：

\[
\Delta\phi_{i,k}=\arg[(z_{i,k}-c_{i,k})(z_{i,k-1}-c_{i,k})^*].
\]

累积相位取包裹值，Kalman 输入阶段以目标上一时刻相位做最近 (2\pi) 分支连续。
ADXL 不参与圆拟合和解缠分支选择。

### 4.5 ADXL 预积分

对每个雷达区间使用原生 ADXL 样本做梯形积分，得到：

\[
\Delta v_k=\int_{t_k}^{t_{k+1}}a(t)dt,
\qquad
\Delta q_k=\int_{t_k}^{t_{k+1}}v(t)dt.
\]

### 4.6 共享结构相位 Kalman

状态为结构主相位和相位变化率。ADXL 预积分进入状态预测；每个目标的 LOS 相位乘
冻结 (\betaeta_i) 后形成同一结构状态的观测。当前有效目标先按 (R_i^{-1}) 做一次
加权合并，再执行一次 Kalman 更新。(R_i) 根据每个目标后验残差递推，输出
(q=\lambda\Theta/(4\pi))。

## 5. 评价边界

仿真结果可报告统一输入包、目标提取、相位圆拟合、ADXL 预积分和共享 Kalman 的
链路 RMSE。它不能替代真实激光对照；真实数据还需要独立确认阵列幅相、安装角、
雷达有效载频、雷达时间延迟和 ADXL 轴向/延迟校准。

完整入口：

```bash
python3 -m system.algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/base-result.npz
```
