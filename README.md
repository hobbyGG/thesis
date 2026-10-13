# 论文实验工作区

本工作区只保留一条可复现的论文实验链：真实采集和论文参数仿真输出同一种
`capture_root`，唯一的算法入口读取该输入包并输出结构位移。

```text
system/capture_program/       IWR1843/DCA1000、ADXL355 和同步时间轴采集
paper_bridge_simulation/      A20 参数化磁浮轨道梁响应与观测包仿真
system/algorithm/             唯一 base 位移算法
```

统一输入包：

```text
capture_root/
├── radar/algorithm_input/
│   ├── adc_cube.npy          # 500 Hz，4-loop 复数相干平均
│   ├── chirp_cube.npy        # 无损原始 chirp，供采集追溯
│   ├── frame_times_s.npy
│   └── manifest.json
├── adxl355/algorithm_input/
│   ├── acceleration_mps2.npy
│   ├── estimated_sample_monotonic_ns.npy
│   └── manifest.json
├── sync/
│   ├── timeline.json
│   └── radar_adc_sample_monotonic_ns.npy
└── truth/                    # 仿真评价旁路，可选
```

## Base 算法

```text
adc_cube
→ Hamming 普通 Range FFT
→ 8 虚拟阵元 Angle DBF
→ 首个观测的距离—角度候选峰
→ 冻结目标 bin 的 slow-time IQ
→ 因果 IQ 圆拟合与圆心校正
→ 普通最近 2π 相位连续
→ 冻结 AoA beta = 1 / |cos(theta)|
→ ADXL 原生时间轴区间预积分
→ 共享结构主相位 Kalman
→ 后验残差更新目标测量方差
→ 结构位移 q_hat
```

算法入口：

```bash
python3 -m system.algorithm.run \
  --input /tmp/paper_bridge_capture \
  --output /tmp/paper_bridge_result.npz
```

论文参数仿真：

```bash
python3 -m paper_bridge_simulation \
  --output /tmp/paper_bridge_capture \
  --duration 13.0 \
  --seed 2026
```

仿真响应采用 A20 公开参数：24.768 m 梁、300 km/h 工况、六阶模态
10.35、13.41、27.10、43.84、52.93、84.44 Hz。每次响应持续 0.8 s，间隔 5 s，
总位移峰值缩放到 1.712 mm。雷达使用 77 GHz、500 Hz 帧率、每帧 4 个 TX0+TX2
MIMO loop、256 个 ADC 点和 8 个虚拟阵元；ADXL355 使用 500 Hz 原生时间轴。

算法和仿真代码保持直接的数组处理。仿真真值只在输出摘要中计算 RMSE，不进入
候选检测、角度处理、beta 或 Kalman。

主要说明：

- [当前方法说明](docs/current_method_specification.md)
- [完整数据流](docs/current_research_data_flow.md)
- [算法目录说明](system/algorithm/README.md)
- [采集程序说明](system/capture_program/README.md)
- [仿真说明](paper_bridge_simulation/README.md)
- [方法文献库](docs/radar_method_search_2010_2026/README.md)
