# 当前研究的数据流与算法处理链

本文档只描述当前代码真正保留的一条实验链路：

```text
IWR1843BOOST + DCA1000EVM + ADXL355
        ↓
树莓派采集、时间记录、原始数据解码
        ↓
统一 capture_root 输入包
        ↓
距离—角度目标构造与目标级复数观测
        ↓
固定几何 beta 的相位统一
        ↓
ADXL355 区间预积分与结构主相位 Kalman
        ↓
结构位移 q_hat_m
```

`capture_program/` 是硬件采集边界，`measured_bridge_simulation/` 是用实测激光位移驱动的半实测输入包生成器，`algorithm/` 是离线论文算法。后两者都不做服务化运行；算法不直接接触 PCAP、LVDS、串口或 GPIO。

## 1. 研究对象和当前实验边界

当前保留的实验目标是：利用毫米波雷达的多目标慢时间相位和 ADXL355 加速度，估计结构沿主方向的动态位移。

当前代码真正跑通并用于回归测试的是“实测桥梁位移驱动的半实测场景”：

1. 从 `datafile/20250320test12.tdms` 的 `卡3激光位移/3-4` 通道取一段实测桥梁位移。
2. 用这段位移合成雷达复数 ADC/IQ、目标角度和噪声。
3. 用位移的频域二阶导数合成 ADXL355 结构轴加速度，并加入采集噪声。
4. 把合成结果写成与真实采集相同的 `capture_root`。
5. 让 `algorithm/` 对这个输入包执行与真实采集完全相同的算法。

因此，当前半实测实验验证的是“实测运动输入 + 统一采集格式 + 论文算法”这条链。雷达 ADC 和 ADXL355 数值在该场景中是合成的，不能把半实测结果直接表述为真实硬件精度验收。

## 2. 实测硬件链路

### 2.1 雷达发射和接收

IWR1843BOOST 的射频前端按 `radar.cfg` 工作。当前配置是 77 GHz FMCW 雷达：雷达发射线性调频连续波，目标反射回波后由接收通道下变频并进行片上 ADC 采样。代码不实现射频混频和 ADC，它通过配置文件设置这些硬件工作参数。

当前配置的关键字段是：

```text
channelCfg 15 5 0
profileCfg ... 77 ... 57.14 ... 256 5209 ...
chirpCfg 0 0 ... 1
chirpCfg 1 1 ... 4
frameCfg 0 1 16 0 10 1 0    # 软件触发
frameCfg 0 1 16 0  9 2 0    # 硬件触发
```

它们在当前代码中的含义是：

- RX mask `15` 表示启用 4 个接收天线。
- TX mask `5` 表示启用 TX0 和 TX2 两个发射天线。
- 两个 `chirpCfg` 让不同 chirp 使用不同 TX，形成 TDM-MIMO。
- 每帧有 16 个 chirp loop，每个 loop 含 2 个 TX chirp，所以每帧有 32 个物理 chirp。
- 4 个 RX 与 2 个 TX 形成 `2 × 4 = 8` 个虚拟阵元。
- 每个 chirp 采集 256 个 ADC 点，采样率为 5.209 MS/s。
- 起始载频为 77 GHz，调频斜率字段为 70 MHz/us，代码据此写出距离分辨率。
- 软件触发配置的名义帧周期为 10 ms；硬件触发配置的雷达最小帧周期为 9 ms，树莓派示例触发频率为 100 Hz。

FMCW 的拍频与距离关系为：

$$
f_b \approx \frac{2SR}{c},\qquad
R=\frac{cf_b}{2S}.
$$

当前代码不单独计算每个拍频，而是先做距离 FFT，再用采集清单写入的距离分辨率把 FFT bin 映射到距离轴。采集侧使用：

$$
\Delta R=\frac{cF_s}{2SN},
$$

其中 $F_s$ 是 ADC 采样率，$S$ 是调频斜率，$N$ 是每 chirp 的 ADC 点数。

### 2.2 IWR1843BOOST 到 DCA1000EVM

IWR1843 片上 ADC 输出的是两路 LVDS 原始数据，经 60-pin HD 连接器送入 DCA1000EVM。DCA1000EVM 负责接收 LVDS、FPGA 侧整理和 UDP 封包；它不是论文算法，也不在树莓派 Python 中做距离或角度估计。

树莓派通过 USB 连接 IWR1843BOOST 的 XDS110，通常有两个串口：

- 配置 UART：发送 `sensorStop`、`flushCfg`、`profileCfg`、`chirpCfg`、`frameCfg`、`sensorStart` 等毫米波 SDK 命令。
- 数据 UART：按工程配置打开，但当前原始 ADC 数据路径是 IWR1843 → LVDS → DCA1000 → Ethernet，不是从 Python 数据 UART 逐样本读取。

树莓派通过 UDP 控制 DCA1000：

```text
DCA IP       192.168.33.180
树莓派 DCA 网口 192.168.33.30
控制端口     UDP 4096
数据端口     UDP 4098
```

采集初始化阶段实际调用 DCA1000 的系统连接检查、雷达复位、FPGA 复位、FPGA 配置和 packet delay 配置；正式采集前发送 `RECORD_START`，结束时发送 `RECORD_STOP`。

### 2.3 DCA1000 到树莓派

树莓派的 `eth0` 直连 DCA1000EVM。`RadarDCA` 启动 `tcpdump`，过滤 DCA1000 的 UDP 流并保存为 `dca.pcap`。一次有限帧采集的实际顺序是：

1. 树莓派初始化 DCA1000 和 IWR1843。
2. 启动 `tcpdump`。
3. 发送 DCA `RECORD_START`。
4. 通过雷达配置 UART 发送 `sensorStart`。
5. IWR1843 发射 chirp、接收回波、ADC 采样并通过 LVDS 输出。
6. DCA1000 将 LVDS 数据封装为 UDP 包发送到树莓派。
7. 树莓派将 UDP 包原样写入 `dca.pcap`。
8. 有限帧结束后停止雷达、停止 DCA 记录并结束 `tcpdump`。

DCA UDP 数据包的有效载荷在当前解析器中按以下结构解释：

```text
4 bytes：sequence_id
6 bytes：累计 byte_count
剩余部分：LVDS payload
```

算法输入导出器先按 `byte_count` 重建连续字节流，再检查包序号、字节连续性、重叠和冲突重复。PCAP 时间戳只表示 UDP 包到达树莓派的时间，包含 LVDS 传输、DCA 缓冲、以太网和主机接收延迟，不能当作雷达 ADC 采样时刻。

### 2.4 ADXL355 到树莓派

ADXL355 与雷达采集并行，但走另一条链路：

```text
ADXL355
 ├─ SPI0 CE0：/dev/spidev0.0
 └─ DRDY：GPIO25
       ↓
native/adxl355_capture
       ↓
adxl355.raw + summary.json
       ↓
adxl355_input.py
       ↓
adxl355/algorithm_input/*.npy
```

当前默认配置为 1 kHz、±2 g、SPI 5 MHz。每次 DRDY 上升沿由 Linux GPIO character-device uAPI v2 提供 `CLOCK_MONOTONIC` 时间戳，native 采集程序随后：

1. 读取 `STATUS` 和 `FIFO_ENTRIES`；
2. 读取温度；
3. 从 `FIFO_DATA` 读取一个 XYZ 样本；
4. 再次检查 FIFO，确认本次样本处理完成；
5. 将样本、序号、DRDY 时间和 SPI 完成时间写入二进制记录。

Python 导出器把原始整数换算为物理加速度：

$$
a_{\mathrm{m/s^2}}=a_{\mathrm{raw}}
\frac{9.80665}{\mathrm{LSB/g}}.
$$

当前 ±2 g 设置的灵敏度为 256000 LSB/g，因此：

$$
a_{\mathrm{m/s^2}}=a_{\mathrm{raw}}\frac{9.80665}{256000}.
$$

导出包中同时保留原始整数、物理加速度、DRDY 时间、估计样本时间、样本序号、温度和状态等字段。若没有经过测量的数字滤波群延迟，`group_delay_ns = 0` 只表示“未标定”，不表示真实物理延迟为零。

### 2.5 树莓派的同步组织

同步协调器 `SynchronizedRadarAdxl` 的执行顺序是：

```text
启动 ADXL355
→ 预采集 pre-roll（示例 2 s）
→ 启动 tcpdump 和 DCA RECORD_START
→ sensorStart
→ （硬件模式）GPIO18 触发雷达帧
→ 等待雷达采集结束
→ 后采集 post-roll（示例 2 s）
→ 停止 ADXL355
→ 导出雷达、ADXL 和同步时间轴
```

软件时间戳模式下，树莓派记录 `sensorStart` 发送前后两个 `CLOCK_MONOTONIC` 时间，取中点作为第一个帧参考，再加上解码得到的名义帧周期：

$$
t_k=t_{\mathrm{mid}}+kT_{\mathrm{frame}}.
$$

这是一条估计时间轴，不是实测 ADC 起始时间。

硬件触发模式下，GPIO18 接 IWR1843BOOST 的 `SYNC_IN`，可选 GPIO24 观察回环上升沿。时间轴使用 GPIO 回环时间戳或 GPIO set 完成时间戳，但仍不是经过雷达触发延迟标定的 ADC 采样时间，也不会让雷达 ADC 和 ADXL355 共用采样时钟。

## 3. 统一输入包

真实采集和半实测生成器最终都要产生同一类目录：

```text
capture_root/
├── radar/algorithm_input/
│   ├── adc_cube.npy
│   ├── chirp_cube.npy
│   ├── frame_times_s.npy
│   ├── frame_receive_times_epoch_ns.npy   # 真实采集可有
│   └── manifest.json
├── adxl355/algorithm_input/
│   ├── acceleration_mps2.npy
│   ├── estimated_sample_monotonic_ns.npy
│   ├── sample_times_s.npy
│   └── manifest.json
├── sync/
│   ├── radar_frame_monotonic_ns.npy
│   ├── radar_adc_sample_monotonic_ns.npy
│   └── timeline.json
├── status.json                              # 实测采集包
└── truth/                                   # 半实测评价用，可选
```

雷达算法输入导出器 `capture_program/src/mmwavecapture/algorithm_input.py` 将两路 LVDS 的 little-endian `int16` 组成复数：当前 `quadrature_in_lsb=true` 时，8 字节一组解释为 `[Q0,Q1,I0,I1]`，再组成 `I+jQ`。

按雷达配置重排后：

```text
chirp_cube.shape = (frame, chirp_loop, virtual_antenna, adc_sample)
```

当前配置对应：

```text
chirp_cube.shape = (frame, 16, 8, 256)
```

默认的帧级输入沿 chirp loop 做复数平均：

$$
adc\_cube[f,v,n]
=\frac{1}{L}\sum_{\ell=0}^{L-1}
chirp\_cube[f,\ell,v,n].
$$

输出：

```text
adc_cube.shape = (frame, virtual_antenna, adc_sample)
```

当前 `algorithm/` 主要使用 `adc_cube.npy`、ADXL 的 `acceleration_mps2.npy` 与 `estimated_sample_monotonic_ns.npy`，以及 `sync/timeline.json` 指向的雷达时间轴。`chirp_cube.npy` 和 `frame_receive_times_epoch_ns.npy` 被保留用于追溯，但当前位移算法不直接使用它们。

## 4. 算法从输入包到位移结果

入口为：

```bash
python3 -m algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/algorithm_result.npz
```

### 4.1 读取输入

`algorithm/io.py` 读取：

```text
adc_cube[F,V,S]                         雷达帧级复数 ADC
estimated_sample_monotonic_ns[N]       ADXL 原生时间轴
acceleration_mps2[N,3]                 ADXL 三轴物理加速度
sync radar time[F]                     雷达帧参考时间
```

算法当前只使用 ADXL 第 0 轴：

```python
structural_accel = acceleration_mps2[:, 0]
```

`truth/displacement_m.npy` 不参与任何候选检测、角度估计、beta 计算或 Kalman 更新；它只在最后的半实测 RMSE 统计中使用。

### 4.2 距离 FFT

对每帧、每个虚拟阵元沿 ADC 快时间做 FFT：

$$
X[f,v,r]=\operatorname{FFT}_n\{adc\_cube[f,v,n]\}.
$$

代码是：

```python
range_fft = np.fft.fft(adc, n=num_range_bins, axis=2)
```

当前 `num_range_bins = adc_samples_per_chirp`，因此 256 个 ADC 点对应 256 个距离 bin。距离轴为：

$$
R_r=r\Delta R.
$$

### 4.3 角度 DBF

把距离 FFT 的轴整理为 `(frame, range_bin, virtual_antenna)`，再用默认半波长虚拟阵列和 Hann 阵元窗做角度方向变换。阵元位置以波长为单位：

$$
p_v=0.5v.
$$

角度搜索变量是空间频率，导向矢量为：

$$
a_v(u)=e^{-j2\pi p_v u}.
$$

波束形成输出为：

$$
Y[f,r,a]=
\sum_v X[f,r,v]w_v a_v(u_a),
$$

并按 ADC 点数和窗函数总和归一化。空间频率再映射到角度：

$$
\theta=\arcsin\left(\frac{u}{d/\lambda}\right),
\qquad d/\lambda=0.5.
$$

这一步只建立距离—角度复数数据立方体，不使用加速度和真值。

### 4.4 记录级候选目标检测

`selection.py` 对整段帧做中位数幅值聚合：

$$
M[r,a]=\operatorname{median}_f|Y[f,r,a]|.
$$

阈值由全局中位数和 MAD 构成：

$$
m=\operatorname{median}(M),\qquad
T=m+6\operatorname{median}(|M-m|).
$$

超过阈值且在一格距离/角度邻域内为局部峰的点成为候选。随后：

- 距离 bin 相差不超过 1 且角度差小于 15° 的峰合并；
- 以最强峰为基准保留 20 dB 动态范围内的峰；
- 最多保留 5 个候选（当前 `build_algorithm_inputs()` 显式传入 `max_candidates=5`）。

这一阶段得到每个候选的距离 bin 和粗角度 bin。

### 4.5 局部 MUSIC/最小二乘角度精修

对于同一距离 bin 的候选，取该距离上的虚拟阵元复数快拍：

$$
X\in\mathbb{C}^{V\times K}.
$$

代码对快拍做有限值筛选、最多保留 512 个快拍并按最大幅值归一化，然后计算：

$$
R_{xx}=\frac{1}{K}XX^H.
$$

对协方差矩阵特征分解，取小特征值对应的噪声子空间 $E_n$。在粗角度对应的局部空间频率区间内搜索 MUSIC 谱：

$$
P_{\mathrm{MUSIC}}(u)=
\frac{1}{\|E_n^Ha(u)\|^2}.
$$

当前局部搜索半宽为 0.12，网格为 129 点。得到初值后，代码用阵列导向矩阵做复数最小二乘拟合：

$$
X\approx A(u)S,\qquad S=A(u)^\dagger X,
$$

并以投影残差：

$$
J(u)=\|X-A(u)A(u)^\dagger X\|_F^2
$$

进行三轮局部细化。最终得到连续角度和目标的慢时间复数观测 $s_i[f]$。

### 4.6 慢时间相位和固定 beta

每个目标的慢时间复数观测取包裹相位：

$$
\phi_i[f]=\arg(s_i[f])\in[-\pi,\pi].
$$

零幅值或非有限观测标记为不可用，存入 `available_mask`。

当前一维方位、倒挂安装约定下，由精修角度直接生成目标级几何系数：

$$
\beta_i=\frac{1}{|\cos\theta_i|}.
$$

这个 beta 在整段实验中冻结，不由 Kalman 后验反向更新。它是当前简化几何模型下的投影系数；真实系统仍需要确认安装方向、主振动方向、角度定义和阵列幅相标定。

### 4.7 有效目标保留

对第 $i$ 个候选计算有效观测比例：

$$
\rho_i=\frac{\text{available samples}}{\text{total frames}}.
$$

只保留 $\rho_i>0.5$ 的目标。初始每个目标的测量方差设为：

$$
R_i=9.
$$

当前代码没有动态新增、删除和重关联目标的在线 tracker；目标集合在这一轮记录级检测后固定，某帧没有有效目标时只执行 Kalman 预测。

### 4.8 ADXL355 区间预积分

雷达帧和 ADXL355 样本保留各自的原生单调时间轴。对相邻雷达时间 $[t_k,t_{k+1}]$，代码找出区间内的 ADXL 样本，并在线性插值后按分段线性加速度积分：

$$
\Delta v_k=\int_{t_k}^{t_{k+1}}a(t)\,dt,
$$

$$
\Delta q_k=\int_{t_k}^{t_{k+1}}
\left(\int_{t_k}^{t}a(\tau)d\tau\right)dt.
$$

每个小区间的实际递推为：

$$
\Delta v\mathrel{+}=\frac{a_0+a_1}{2}\Delta t,
$$

$$
\Delta q\mathrel{+}=v_0\Delta t
+\frac12a_0\Delta t^2
+\frac16(a_1-a_0)\Delta t^2.
$$

得到每个雷达帧间隔的 `duration_s`、`delta_v_mps` 和 `delta_q_m`。代码还构造了区间平均加速度 `delta_v / duration`，但当前 Kalman 只使用 `delta_v` 和 `delta_q`，这个平均量没有进入后端状态更新。

### 4.9 加速度预测的结构主相位 Kalman

结构主相位定义为：

$$
\Theta_k=\frac{4\pi}{\lambda}q_k.
$$

状态为：

$$
\mathbf{x}_k=
\begin{bmatrix}\Theta_k\\\dot\Theta_k\end{bmatrix}.
$$

状态转移为：

$$
A_k=\begin{bmatrix}1&\Delta t_k\\0&1\end{bmatrix}.
$$

加速度预积分直接作为相位预测输入：

$$
\mathbf{x}_{k|k-1}
=A_k\mathbf{x}_{k-1|k-1}
+\frac{4\pi}{\lambda}
\begin{bmatrix}\Delta q_k\\\Delta v_k\end{bmatrix}.
$$

过程噪声使用常加速度模型：

$$
Q_k=\sigma_q^2
\begin{bmatrix}
\Delta t_k^3/3&\Delta t_k^2/2\\
\Delta t_k^2/2&\Delta t_k
\end{bmatrix},
$$

其中当前 `process_noise_intensity = 5e4`。初值为 $[0,0]^T$，初始协方差为 `diag(25, 400)`。

### 4.10 相位分支修正和多目标融合

冷启动时长为 0.2 s。每个目标在冷启动阶段对有效包裹相位做 Itoh 解包并取平均，作为目标相位偏置 $b_i$。

在第 $k$ 帧，使用预测相位选择包裹相位的最近整周：

$$
\phi_{i,k}^{\mathrm{corr}}
=\phi_{i,k}^{\mathrm{wrap}}
+2\pi\operatorname{round}\left(
\frac{\Theta_{k|k-1}/\beta_i+b_i-
\phi_{i,k}^{\mathrm{wrap}}}{2\pi}
\right).
$$

再将目标相位映射到公共结构主相位：

$$
z_{i,k}=\beta_i
\left(\phi_{i,k}^{\mathrm{corr}}-b_i\right).
$$

同一时刻所有有效目标不是先各自输出位移再平均，而是按测量方差的倒数加权成一个公共观测：

$$
z_k=\frac{\sum_iR_i^{-1}z_{i,k}}{\sum_iR_i^{-1}},
\qquad
R_k=\frac{1}{\sum_iR_i^{-1}}.
$$

观测矩阵为 $H=[1,0]$，然后执行标准 Kalman 更新。代码另外为每个目标记录相对预测值的 innovation，并用后验残差更新各自测量方差：

$$
R_i\leftarrow \operatorname{clip}\left[
0.95R_i+0.05\left((z_{i,k}-\Theta_{k|k})^2+P_{00,k|k}\right)
\right].
$$

方差限制为 $10^{-4}\le R_i\le25$。这只是各目标观测权重的自适应更新，不会改写 beta。

### 4.11 相位转位移和输出

Kalman 输出的第一状态量为结构主相位，最终位移为：

$$
\hat q_k=\frac{\lambda}{4\pi}\Theta_k.
$$

`algorithm/run.py` 写出：

```text
algorithm_result.npz
├── time_s
├── radar_time_ns
├── q_hat_m
├── theta_hat_rad
├── theta_dot_hat_radps
├── los_corrected_phase_rad
├── beta_hat
├── r_theta_history
├── innovation_rad
├── radar_wrapped_phase_rad
├── radar_measured_beta
├── selected_target_indices
├── target_angle_deg
└── target_range_m
```

如果输入包有 `truth/`，结果中额外保存真值，并在 JSON 摘要中计算 RMSE。计算前把估计值和真值都以冷启动阶段的真值平均值作为参考零点：

$$
RMSE=\sqrt{\frac1N\sum_k
\left[\hat q_k-(q_k-q_{\mathrm{ref}})\right]^2}.
$$

真实硬件采集没有 `truth/` 时仍然可以输出位移估计，只是不计算该 RMSE。

## 5. 半实测场景如何生成输入

`measured_bridge_simulation/tdms.py` 的实际处理是：

1. 读取 TDMS 中 `卡3激光位移/3-4`。
2. 截取 15.33 s 到 19.33 s 的事件窗口。
3. 按 TDMS 波形时间步长插值到 1 kHz。
4. 减去前 0.2 s 平均值。
5. 以 `voltage × 1e-3` 转为米。
6. 在频域只保留 0.2–40 Hz，再反变换得到处理后的位移。
7. 用

   $$
   a(t)=\mathcal{F}^{-1}\{- (2\pi f)^2\mathcal{F}[q(t)]\}
   $$

   得到结构轴加速度。

`package_builder.py` 再把它写成输入包：

- 雷达帧率 100 Hz，雷达位移取 1 kHz 位移每 10 点抽样。
- 5 个目标角度为 5°、15°、25°、35°、45°，距离 bin 为 8、24、40、56、72。
- 目标慢时间相位使用

  $$
  \phi_i(t)=\frac{4\pi q(t)}{\lambda\beta_i}+b_i,
  \qquad \beta_i=1/|\cos\theta_i|.
  $$

- 每个目标加入设定 SNR 的复高斯噪声，并叠加小幅 ADC 噪声。
- 按目标角度生成虚拟阵元空间导向项，按距离 bin 生成快时间复指数，组成 `adc_cube`。
- 将同一 `adc_cube` 沿 chirp loop 重复 16 次得到 `chirp_cube`。
- ADXL 第 0 轴写入合成加速度加噪声，另外两轴为零。
- 写入 `truth/displacement_m.npy`、`truth/time_ns.npy` 和真值加速度，仅供末端评价。

该生成器的作用是验证算法链路和输入契约；它没有模拟 IWR1843 的模拟射频、电路噪声、LVDS 传输误码或 DCA 网络时延。

## 6. 代码对应关系

| 研究环节 | 当前代码 |
| --- | --- |
| 雷达串口、DCA 控制、tcpdump | `capture_program/src/mmwavecapture/radar.py`、`capture.py`、`capture/radardca.py`、`dca1000.py` |
| ADXL355 原始采集和导出 | `capture_program/native/adxl355_capture/`、`capture_program/src/mmwavecapture/capture/adxl355.py`、`adxl355_input.py` |
| 雷达 PCAP/LVDS 解码和 reshape | `capture_program/src/mmwavecapture/algorithm_input.py` |
| 采集同步和时间轴 | `capture_program/src/mmwavecapture/capture/synchronized.py` |
| 半实测 TDMS 处理 | `measured_bridge_simulation/tdms.py` |
| 半实测输入包生成 | `measured_bridge_simulation/package_builder.py` |
| 输入包读取和预积分入口 | `algorithm/io.py` |
| Range FFT、角度 DBF、目标 slow-time | `algorithm/frontend.py` |
| 局部 MUSIC/最小二乘 AoA | `algorithm/angle_estimation.py` |
| 峰值检测和目标保留 | `algorithm/selection.py` |
| ADXL 区间预积分 | `algorithm/acceleration.py` |
| 相位分支和结构主相位 Kalman | `algorithm/phase.py`、`algorithm/kalman.py` |
| 结果和 RMSE 摘要 | `algorithm/run.py` |

## 7. 当前研究结论和需要如实表述的边界

当前研究链的核心不是“树莓派实时运行一个复杂系统”，而是：

```text
硬件采集得到可复现的复数雷达帧和异步加速度
→ 距离—角度目标级分解
→ 连续 AoA 生成目标几何 beta
→ 各目标 LoS 相位统一到公共结构主相位
→ 加速度区间预积分提供动态预测
→ 多目标 Kalman 输出结构位移
```

目前可以准确宣称的算法增量是：将目标级距离—角度观测、局部 MUSIC/最小二乘 AoA、冻结几何投影和 native-time 加速度预积分接入共享结构主相位 Kalman。不能把当前代码宣称为通用三维几何标定、在线目标跟踪、真实雷达 ADC 延迟校准或已完成实机计量验收。

