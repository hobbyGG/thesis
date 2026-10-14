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
导出的 `estimated_sample_monotonic_ns` 与采集程序配置 `group_delay_ns` 时的规则
相同：DRDY 时刻减去标定群延迟。

`Impairments`（默认全部关闭，默认输出不变）提供鲁棒性实验所需的误差源：雷达 SNR
偏移、位移幅值缩放、ADXL 静态偏置（含重力投影）、零偏随机游走、噪声倍率、残余
时间偏移与抖动、最强目标与外侧目标的非刚性晃动、雷达短时缺帧。蒙特卡洛实验见
`experiments/`（`python3 -m experiments.sweep tune|test|report`）。

雷达观测模型使用 IWR1843 参数：77 GHz、70 MHz/µs 斜率、256 ADC 点、5.209 MS/s、
500 Hz 外部触发、每帧 4 个 MIMO loop。每个 loop 包含 TX0 和 TX2 两个 TDM chirp，
每个 chirp 使用 4 RX；4 个 loop 的复数数据平均得到算法使用的 `adc_cube.npy`。
无损 `chirp_cube.npy` 同时保留在输入包中，用于采集契约和后续数据追溯。

雷达数组按 32 帧分块生成并直接写入 `.npy`，不会把完整记录的 `complex128` 数组
同时留在内存中。模型包含传播相位、距离拍频、阵列角度相位、距离衰减、弱多径、
静态散射、接收噪声、RX 幅相误差、简化 PLL 公共相噪和 ADC 量化。固定散射相位在
整段记录内保持一致，避免分块边界产生人为相位跳变。

这是硬件链路一致的点目标仿真，不是全波电磁仿真。它用于验证输入包、Range-Angle
目标提取、IQ 圆相位、ADXL 预积分和共享 Kalman 的链路；最终精度仍需真实
IWR1843、ADXL355 与激光参考数据验证。
