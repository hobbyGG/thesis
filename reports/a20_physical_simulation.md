# A20 户外轨道梁物理一致仿真

本次仿真保留 A20 论文参数化结构响应，并把雷达安装在约 10 m 高的轨道梁下方，地面沙土和树丛作为固定世界散射体。雷达随轨道梁运动，散射体的距离按结构位移在 LOS 上的投影变化。

雷达链路按仓库中的 IWR1843 配置生成：77 GHz、70 µs idle、7 µs ADC start、57.14 µs ramp、70 MHz/µs slope、256 ADC 点、5.209 MS/s、100 Hz frame、16 个 loop/frame、TX0/TX2 TDM 和 4 RX。每个 ADC 点经过 FMCW 拍频、传播相位、虚拟阵列相位、距离衰减、弱多径、RX 幅相误差、简化 PLL 公共相噪、接收机噪声和有效 12 bit I/Q 量化。ADXL355 使用 1 kHz 采样、22.5 µg/√Hz 噪声密度、1.78 ms 数字滤波延迟、偏置和比例误差。

结构响应仍由 [response.py](/Users/umep/thesis/paper_bridge_simulation/response.py) 生成；雷达和传感器输入由 [package_builder.py](/Users/umep/thesis/paper_bridge_simulation/package_builder.py) 生成；算法入口没有改动。

固定 seed=2026 的 4 s 运行结果如下，单位为 µm：

五个目标的注入散射系数 SNR 为 30、27.5、25、22.5、20 dB；经过距离 FFT 后，manifest 估计的实际目标 bin SNR 约为 52.3、50.1、47.9、49.5、47.9 dB。两者不同是因为 256 点相干距离处理带来了处理增益。

| 模式 | Radar samples | RMSE | Frame-grid RMSE | 选中目标数 |
|---|---:|---:|---:|---:|
| Frame | 400 | 29.38 | 29.38 | 5 |
| Chirp/Loop | 6400 | 29.32 | 29.47 | 5 |

10 个 seed 的目标数量消融中，冷启动后 passage RMSE 为：

| 目标数 | Frame | Chirp/Loop |
|---:|---:|---:|
| 1 | 31.38 ± 0.83 | 31.01 ± 0.44 |
| 2 | 31.25 ± 1.03 | 31.21 ± 0.77 |
| 3 | 30.95 ± 0.91 | 31.07 ± 0.79 |
| 4 | 31.06 ± 0.72 | 31.11 ± 0.73 |
| 5 | 31.11 ± 0.78 | 31.14 ± 0.74 |

在这组户外场景误差模型下，多目标没有明显改善，说明当前误差主要由 ADXL 延迟、相位/幅度失配、弱多径和结构响应模型误差决定。此前理想目标域 IQ 实验中的多目标增益仍可作为算法信息上限；本次物理一致仿真更接近现场条件，适合评估这些误差源对增益的削弱。

结果文件：

- [Frame 结果](/Users/umep/thesis/reports/a20_physical_frame.json)
- [Chirp/Loop 结果](/Users/umep/thesis/reports/a20_physical_chirp.json)
- [目标数量消融](/Users/umep/thesis/reports/a20_physical_target_count_monte_carlo.json)

这仍是基带/ADC 级仿真，不是全波电磁仿真。IWR1843 的配置依据 [TI 数据手册](https://www.ti.com/lit/ds/symlink/iwr1843.pdf)，ADXL355 噪声和 1 kHz 滤波延迟依据 [ADI 数据手册](https://www.analog.com/media/en/technical-documentation/data-sheets/adxl354_adxl355.pdf)；绝对接收增益、现场 RCS、连续植被散射和多径参数还需要用户外静态采集校准。
