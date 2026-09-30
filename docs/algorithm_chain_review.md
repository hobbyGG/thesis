# 当前代码链路审查

这份审查只描述当前保留的三层代码，不再记录已删除的多场景仿真、Ma 复现和旧 baseline。

## 三层边界

| 层 | 目录 | 输入 | 输出 |
|---|---|---|---|
| 实测采集 | `capture_program/` | IWR1843/DCA1000、ADXL355、GPIO 时间轴 | `capture_root/radar/algorithm_input`、`adxl355/algorithm_input`、`sync` |
| 论文参数仿真 | `paper_bridge_simulation/` | A20 论文参数响应 | 与采集程序相同的 `capture_root`，另附 `truth/` |
| 论文算法 | `algorithm/` | 统一 `capture_root` | `algorithm_result.npz`、同名 JSON 摘要 |

算法入口不再接收场景名、方法名或 baseline 开关。这样可以保证两种数据源只在“输入包生成”处有差异，后面的处理链完全相同。

## 实际主链

```text
capture_root
  ├─ radar/algorithm_input/adc_cube.npy
  ├─ adxl355/algorithm_input/acceleration_mps2.npy
  └─ sync/radar_frame_monotonic_ns.npy
        ↓
algorithm.io.load_capture_package
        ↓
Range FFT + Angle DBF
        ↓
整段中位数幅值图 → 2D 峰值 → 近距离近角峰合并 → 动态范围保留
        ↓
局部 MUSIC/ML AoA → slow-time IQ → wrapped LoS phase
        ↓
beta = 1 / |cos(theta)|，整段冻结
        ↓
ADXL native timeline → 每个雷达区间的 Δv、Δq
        ↓
加速度预测 [Theta, Theta_dot] 的结构主相位 Kalman
        ↓
后验残差更新各目标 R → q_hat_m
```

## 代码对应

| 步骤 | 入口 |
|---|---|
| 统一包读取 | `algorithm/io.py:load_capture_package` |
| 算法输入构造 | `algorithm/io.py:build_algorithm_inputs` |
| Range-Angle | `algorithm/frontend.py:range_angle_process` |
| 局部 AoA | `algorithm/angle_estimation.py:estimate_local_music_ml` |
| 峰值与目标保留 | `algorithm/selection.py` |
| ADXL 预积分 | `algorithm/acceleration.py:preintegrate_acceleration_to_radar` |
| 固定 beta Kalman | `algorithm/kalman.py:run_fixed_beta_kalman` |
| CLI 和结果文件 | `algorithm/run.py:run` |
| 仿真包生成 | `paper_bridge_simulation/package_builder.py:generate` |

## 输入边界

算法实际使用：

```text
adc_cube[F, V, S]
frame_times_s[F]
radar_frame_monotonic_ns[F]
acceleration_mps2[N, 3] 的 x 轴
estimated_sample_monotonic_ns[N]
```

算法不使用：

```text
truth/displacement_m.npy
truth/acceleration_mps2.npy
场景标签、目标真值角度、真值 beta
```

仿真真值只在输出摘要中与估计结果对齐计算 RMSE。真实采集没有 `truth/` 时，算法仍可正常输出位移，只是不计算 RMSE。

## 当前实验边界

当前保留的是一个 A20 论文参数驱动的仿真场景。`response.py` 以 3 kHz、4 s 生成 24.768 m 梁、300 km/h 工况的共同 `q(t), a(t)`，包含准静态通车挠度和六阶阻尼模态；随后按 IWR1843 的 100 Hz、16-loop TDM 配置生成物理一致的 chirp/ADC，并生成 1 kHz ADXL355 及噪声。该实验用于验证“论文参数响应 + 雷达链路 + 统一采集格式 + 论文算法”这条链，不能直接替代真实雷达精度验收。

真实采集使用同一算法入口，仍需后续补充阵列幅相标定、安装姿态标定、雷达到 ADC 延迟标定和 ADXL 轴向/群延迟标定。
