# A20 论文参数响应仿真

该目录生成一条直接、可复现的离线实验输入链。它不读取激光 TDMS，也不复现论文未公开的完整车辆—梁耦合模型；`response.py` 使用 A20 论文公开参数合成结构响应，再由 `package_builder.py` 导出算法可读的标准 capture package。

论文参考工况为 24.768 m 梁、300 km/h、3 kHz 原始响应时间轴和六个识别模态（10.35、13.41、27.10、43.84、52.93、84.44 Hz）。准静态通车挠度与小幅阻尼模态叠加，总位移峰值缩放到论文报告的 1.712 mm；5 节编组、入场包络、模态参与和约 0.45 m/s² 动态加速度是明确的仿真假设。

```bash
python3 -m paper_bridge_simulation \
  --output /tmp/paper_bridge_capture \
  --duration 4.0 \
  --seed 2026
python3 -m algorithm.run \
  --input /tmp/paper_bridge_capture \
  --output /tmp/paper_bridge_result.npz
```

输出包含 `radar/algorithm_input/`、`adxl355/algorithm_input/`、`sync/` 和可选的 `truth/`。算法只读取前三者，`truth/` 仅用于末端 RMSE 评价。响应的公开参数、仿真假设和限制写入 `paper_response_metadata.json`。

仿真雷达使用本仓库 IWR1843 采集配置的 77 GHz 起始频率、70 µs idle、7 µs ADC start、57.14 µs ramp end、70 MHz/µs 斜率、256 点、5.209 MS/s、100 Hz 帧率和 16 个 MIMO loop。每个 loop 顺序使用 TX0、TX2 两个 TDM chirp，每个 chirp 同时采集 4 RX；ADXL355 为 1 kHz。每个 ADC 采样点由窄带 FMCW 点散射模型生成：

\[
f_b=2S R/c,\qquad \phi_R=4\pi R/\lambda,
\]

论文响应 `q(t)` 表示离地约 10 m 轨道梁沿主方向的位移，目标使用相对该结构的地面点几何。模型包含传播相位、距离拍频、阵列角度相位、距离衰减、逐 TX/loop 散射系数复扰动、接收白噪声、固定 RX 幅相误差、简化 PLL 公共相噪、12 bit 有效 I/Q 量化和饱和。一条 0.08 m 等效距离增量与 8% 幅度的弱路径表示简化 multipath；沙土地面和树丛用低幅散射点表示。ADXL355 采用 22.5 µg/√Hz 噪声密度、约 1.78 ms 数字滤波延迟、小偏置和比例误差。

`chirp_cube.npy` 的形状是 `[frame, loop, 8 virtual antenna, 256 ADC sample]`：前 4 个通道来自 TX0/RX0–3，后 4 个通道来自稍后发射的 TX2/RX0–3，构成一次 TDM 虚拟快照。它保留各 loop 的物理时间；`adc_cube.npy` 是这 16 个 loop 的复数平均。manifest 同时保存 3.9998 GHz 全 ramp 带宽和约 3.4402 GHz ADC 有效采样带宽；距离 FFT bin 间隔由后者决定，约为 43.57 mm。该复数 ADC 模型的拍频无混叠距离上限约为 11.15 m，散射体与弱路径均限制在这一范围内。

这是“硬件链路一致”的点目标仿真，不是全波电磁仿真：尚未复现 IWR1843 芯片内部 PLL 相噪的具体统计量，也没有建立完整的连续地形和车辆—梁电磁散射模型。因此它适合验证 range-angle 选点、chirp 级融合和噪声敏感性；最终精度仍需用户外静态/动态 IWR1843 数据校准。

当前五个几何目标在 3°、9°、15°、21°、25° 的注入 SNR 分别为
30、27.5、25、22.5、20 dB。该数值定义在每个 TX、每个 loop 的目标域
散射系数上，随后经过阵列投影、距离拍频、传播相位和 16-loop 平均；参数写入
radar manifest 的 `source` 中用于实验追溯，算法不读取它们决定权重。manifest
同时记录按整段 chirp cube 的距离 FFT 估计 `range_fft_snr_db`，用于区分注入
SNR 与接收处理后的实际 bin SNR。

在同一份四秒输入上比较目标数 1–5：

```bash
python3 tests/experiment_target_count.py \
  --input /tmp/paper_bridge_capture \
  --output reports/snr20_30_target_count_seed2026
```

目标按静止冷启动段的结构相位方差排序，依次加入；每种模式只提取一次
前端观测，目标数变化时仅更改选中索引。结果包含共同帧时间点上的 RMSE、
冷启动后的 RMSE，以及进入梁响应后的 RMSE。算法本身的单目标/多目标
冷启动差异保持原样，实验同时记录初始 R 和递推后的 R，便于解释结果。
