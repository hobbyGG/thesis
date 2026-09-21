# 总体处理架构

```text
真实硬件采集 ───────────────┐
                            ├─ capture_root ─→ algorithm/ ─→ 位移结果
TDMS 激光位移驱动半实测 ────┘
```

两个数据源必须输出同一套目录：

```text
capture_root/
├── radar/algorithm_input/
│   ├── adc_cube.npy
│   ├── frame_times_s.npy
│   └── manifest.json
├── adxl355/algorithm_input/
│   ├── acceleration_mps2.npy
│   ├── estimated_sample_monotonic_ns.npy
│   └── manifest.json
├── sync/
│   ├── radar_frame_monotonic_ns.npy
│   ├── timeline.json
│   └── manifest.json
└── truth/                       # 半实测评价旁路，可选
```

算法只读前三个目录。真值不进入估计器。

## 处理流程

```text
adc_cube
  ↓ Range FFT
range-angle magnitude map
  ↓ 记录级峰值检测、近邻峰合并
candidate range/angle bins
  ↓ local MUSIC/ML
continuous target angle
  ↓ geometry
frozen beta_i = 1 / |cos(theta_i)|
  ↓ phase extraction
wrapped LoS phase
  ↓ ADXL native-time preintegration
state prediction
  ↓ multi-target Kalman + posterior residual R
structural phase → displacement
```

状态定义为：

\[
\mathbf{x}_k=[\Theta_k,\dot\Theta_k]^T,
\qquad \Theta_k=4\pi q_k/\lambda .
\]

加速度预积分提供：

\[
\Delta v_k=\int a(t)dt,
\qquad
\Delta q_k=\int(t_{k+1}-t)a(t)dt .
\]

每个参考目标先做相位分支校正，再按冻结 (\beta_i) 转成结构主相位观测。多目标共享一个结构状态，(R_i) 根据各目标后验残差更新。

## 目录职责

| 目录 | 只负责什么 |
|---|---|
| `capture_program/` | 硬件控制、原始数据解码、标准输入导出 |
| `measured_bridge_simulation/` | TDMS 读取、雷达/ADXL 合成、标准输入导出 |
| `algorithm/` | 标准输入读取、前端、AoA、目标保留、预积分、Kalman |

旧的多场景仿真、Ma、baseline 和扩展报告不再属于当前架构。
