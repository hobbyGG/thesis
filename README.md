# 论文实验工作区

本工作区只保留一条可复现的论文实验链：真实采集和论文参数仿真输出同一种
`capture_root`，唯一的算法入口读取该输入包并输出结构位移。

```text
system/capture_program/       IWR1843/DCA1000、ADXL355 和同步时间轴采集
paper_bridge_simulation/      A20 参数化磁浮轨道梁响应与观测包仿真
system/algorithm/             唯一的结构位移估计算法
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

## 本文算法

```text
adc_cube
→ Hamming 窗 Range FFT
→ 8 虚拟阵元 DBF
→ 首帧距离—角度候选峰检测
→ 固定目标 range/angle 单元的慢时间 IQ
→ 递推代数圆拟合与 IQ 圆心补偿
→ 最近邻 2π 相位展开
→ 固定转换系数 β_i = 1 / |cos θ_i|
→ ADXL 原生时间轴区间预积分
→ 共享结构相位 Kalman 滤波
→ 由后验残差更新目标测量方差
→ 结构位移估计 q̂
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

算法和仿真代码保持直接的数组处理。仿真真值仅在输出摘要中用于计算 RMSE，不进入
目标检测、角度估计、转换系数 β_i 计算或 Kalman 滤波。

主要说明：

- [本文算法方法说明](docs/current_method_specification.md)
- [数据流与实验边界](docs/current_research_data_flow.md)
- [算法目录说明](system/algorithm/README.md)
- [采集程序说明](system/capture_program/README.md)
- [仿真说明](paper_bridge_simulation/README.md)
- [雷达位移测量方法文献调研](docs/radar_method_search_2010_2026/README.md)
