# A20 论文参数响应仿真

该目录生成与真实采集一致的 `capture_root`，供算法直接读取。它不读取
激光 TDMS，也不复现未公开的完整车辆—梁耦合模型；`response.py` 使用 A20 公开
参数合成可重复的结构响应。

```bash
python3 -m paper_bridge_simulation \
  --output /tmp/paper_bridge_capture \
  --duration 13.0 \
  --seed 2026
python3 -m system.algorithm.run \
  --input /tmp/paper_bridge_capture \
  --output /tmp/paper_bridge_result.npz
```

仿真响应采用 24.768 m 梁、300 km/h 和六阶模态（10.35、13.41、27.10、43.84、
52.93、84.44 Hz）。每次事件持续 0.8 s，事件之间静止 5 s，共生成三次响应；
总位移峰值缩放到 1.712 mm。准静态通车挠度和阻尼模态共同构成位移，ADXL 加速度
由同一结构响应计算后加入传感器噪声、偏置、比例误差和 3.26 ms 数字滤波群延迟。
ADXL 的 `acceleration_mps2.npy` 由 ±2 g、20 bit、256000 LSB/g 的量化码反算得到，
因此算法输入中包含量化误差；RMSE 只在算法输出位移与 `truth/displacement_m.npy`
对齐后计算，不把 ADXL 加速度与加速度真值单独作为性能指标。
真值 `truth/acceleration_mps2.npy` 对应的是传感器实际采样的内容时刻
`truth/adxl_time_ns.npy = DRDY - group_delay`；它不再错误地标成 DRDY 时刻。
`truth/adxl_published_time_ns.npy` 保存含残余偏移与抖动、并经过严格递增修复的算法时间轴。
算法输入中的 `estimated_sample_monotonic_ns` 与采集程序配置 `group_delay_ns` 时的规则
相同：DRDY 时刻减去标定群延迟。

`Scenario`（`scenario.py`，默认值是上述 A20 参数化参考响应）描述观测对象：结构响应参数（车速、
峰值挠度、通过时长、事件时刻、模态激励权重与相位、环境微振）与雷达场景（安装高度、
5 个目标的角度/幅度/SNR、静态散射体）。`Impairments`（默认采用参考传感器参数）描述
传感器与环境相对参考模型的偏离：

| 参数 | 含义 |
|---|---|
| `snr_offset_db` | 每个目标散射系数的 SNR 偏移，相位噪声按 $10^{-\mathrm{SNR}/20}$ 缩放；热噪声与量化噪声在 DBF 输出中可忽略 |
| `radar_mount_angle_error_deg` | 物理阵列视角相对算法标称视角的误差；只作用于前向信号，算法仍读取标称角度 |
| `radar_array_spacing_error` | 物理虚拟阵元间距的相对误差；DBF 仍使用标称阵元位置 |
| `radar_chirp_slope_error` | 物理 chirp 斜率相对标称 profile 的误差；算法仍使用标称距离标定 |
| `iq_offset_ratio` | 每个目标距离—角度单元内不随结构运动的常值复数项（直流偏置、串扰与静态杂波的集总）占目标幅度的比例，使该目标的 IQ 圆心偏离原点 |
| `target_sway_*` | 指定目标的独立低通视线运动（非刚性散射体） |
| `radar_dropout_*` | 全部目标同时丢失的连续帧（ADC 数据置 NaN） |
| `adxl_bias_x_mps2`、`adxl_bias_walk_mps2_per_sqrt_s`、`adxl_noise_scale`、`adxl_scale_error`、`adxl_tilt_gain_mps2_per_m` | ADXL 静态偏置（含重力投影）、零偏随机游走、噪声倍率、比例误差、随局部变形同步的倾斜耦合 |
| `adxl_timestamp_offset_s`、`adxl_timestamp_jitter_std_s` | 群延迟标定残差与时间戳抖动，只改时间戳，不改采样时刻 |
| `adxl_clock_phase_s`、`adxl_odr_error` | ADXL DRDY 栅格相对雷达帧栅格的相位与 ODR 相对误差，同时改变采样时刻与时间戳 |

`ensemble.draw_case(seed)` 由一个种子给出完整的 `(Scenario, Impairments)`。全部范围都是
仿真假设，未用实测静态采集标定；其中 IQ 偏置比例对雷达链误差影响最大，实验报告按它分层。

| 量 | 分布 |
|---|---|
| 车速 / 列车长度 | U(250, 350) km/h / U(40, 125) m，通过时长 $=(L+24.768)/v$ |
| 峰值挠度 / 动态加速度峰值 | U(0.6, 2.2) mm / U(0.2, 0.8) m/s² |
| 事件起始 | U(0.5, 1.3) s（4 s 记录内一次通过） |
| 模态激励权重 / 相位 | 参考值 × U(0.5, 1.5) / U(0, 2π) |
| 环境微振加速度 RMS | 对数均匀 0.5–5 mm/s² |
| 安装高度 | U(8, 10) m |
| 目标角度 | $\lvert\theta\rvert\sim$ U(2°, 28°)，随机符号；要求任意两目标距离差 ≥ 2.5 个距离单元或角度差 ≥ 14°，且最大距离 ≤ 10.9 m |
| 目标幅度 / SNR | 参考值 × U(0.6, 1.4) / U(18, 32) dB |
| 静态散射体（2 个） | 距离 U(9, 10.9) m，角度 U(−35°, 35°)，幅度 U(0.01, 0.03) |
| SNR 偏移 | U(−10, 0) dB |
| 雷达安装角 / 阵元间距 / chirp 斜率失配 | N(0, 0.5°) 截断 ±2° / N(0, 1%) 截断 ±3% / N(0, 0.1%) 截断 ±0.3% |
| IQ 偏置比例 | 对数均匀 0.02–0.5（未标定） |
| 目标晃动 | 概率 0.5；随机 1–2 个目标；标准差对数均匀 2–40 µm |
| ADXL 偏置 / 零偏游走 | U(−0.6, 0.6) m/s² / 对数均匀 1e-4–5e-3 m/s²/√s |
| ADXL 噪声倍率 / 比例误差 | U(1, 2) / N(0, 1%) 截断 ±3% |
| ADXL 倾斜增益 | ±U(0, 0.2)·g，单位 (m/s²)/m |
| 时间偏移 / 抖动 | N(0, 0.5 ms) 截断 ±2 ms / U(0, 100 µs) |
| DRDY 时钟相位 / ODR 误差 | U(0, 2 ms) / U(−0.3%, 0.3%) |

`generate(..., fast=True)` 不写无损 `chirp_cube.npy`，但仍按分块计算轻量的有效 SNR
统计量；`adc_cube`、ADXL、时间线与真值不变。它供大批量实验使用。
ADXL 的 DRDY 序列比雷达记录多保留 4 个样本，使时钟相位与群延迟补偿不会让最后一个
雷达区间失去后继样本。

各旋钮在本模块内按硬件量纲和观测模型定义：SNR 偏移对应目标相位噪声的缩放、
零偏游走方差随时间线性增长、抖动标准差、时钟相位/ODR 误差、比例误差与倾斜项的定义、
晃动的平稳标准差与相关性、集合场景的取值范围。`source.effective_snr_db` 同时输出
Range-FFT、DBF 和 IQ 三层有效 SNR。Range-FFT 使用与主算法一致的 Hamming 窗；DBF 使用
标称阵元位置的固定 64 角度栅格；IQ 使用前 0.2 s 静止窗口的复数均值功率与残差方差。
三者只写入 manifest，不参与算法决策。`range_fft_snr_db` 保留为 Range-FFT 层别名。
SNR 偏移 −10 dB 时该指标仍可能受旁瓣与静态杂波支配，因此应按三层指标共同报告，不能只用
散射系数 SNR 替代有效 SNR。
（其底噪应由旁瓣与 ADC 量化噪声支配，未单独验证）。

雷达观测模型使用 IWR1843 参数：77 GHz、70 MHz/µs 斜率、256 ADC 点、5.209 MS/s、
500 Hz 外部触发、每帧 4 个 MIMO loop。每个 loop 包含 TX0 和 TX2 两个 TDM chirp，
每个 chirp 使用 4 RX；4 个 loop 的复数数据平均得到算法使用的 `adc_cube.npy`。
无损 `chirp_cube.npy` 同时保留在输入包中（`fast=True` 除外），用于采集契约和后续数据追溯。

雷达数组按 32 帧分块生成并直接写入 `.npy`，不会把完整记录的 `complex128` 数组
同时留在内存中。模型包含传播相位、距离拍频、阵列角度相位、距离衰减、弱多径、
静态散射、接收噪声、RX 幅相误差、简化 PLL 公共相噪和 ADC 量化。固定散射相位在
整段记录内保持一致，避免分块边界产生人为相位跳变。

这是硬件链路一致的点目标仿真，不是全波电磁仿真。它用于验证输入包、Range-Angle
目标提取、IQ 圆相位、ADXL 预积分和共享 Kalman 的链路；最终精度仍需真实
IWR1843、ADXL355 与激光参考数据验证。已知的保真度缺口：未做链路预算，热噪声与量化
噪声远小于目标散射系数噪声；运动为一维；IQ 偏置、ADXL 误差与晃动幅度的取值范围均
未用实测标定；ADXL 与雷达的真实同步误差尚未标定；仿真与算法共用同一前向模型
（inverse crime）。
