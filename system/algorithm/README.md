# Base 位移算法

这是唯一保留的离线算法入口。它读取采集程序或论文参数仿真程序生成的统一
`capture_root`，输出结构位移结果；不生成场景、不控制硬件、不读取真值参与估计。

```bash
python3 -m system.algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/base-result.npz
```

当前固定数据流为：

```text
500 Hz 帧级 adc_cube（4 个 MIMO loop 的复数平均）
→ Hamming 窗普通 Range FFT
→ 8 虚拟阵元 Angle DBF
→ 首个观测的距离—角度峰值检测与近邻合并
→ 冻结的目标 range/angle bin slow-time IQ
→ 每个目标因果代数 IQ 圆拟合
→ 圆心校正、普通最近 2π 相位连续
→ beta = 1 / |cos(theta)|，记录内冻结
→ ADXL355 原生时间轴区间预积分
→ 加速度预测的共享结构相位 Kalman
→ 目标测量方差按后验残差更新
→ 结构位移 q_hat
```

算法只依赖以下输入：

```text
radar/algorithm_input/adc_cube.npy
radar/algorithm_input/manifest.json
adxl355/algorithm_input/acceleration_mps2.npy
adxl355/algorithm_input/estimated_sample_monotonic_ns.npy
sync/timeline.json
```

仿真包中的 `truth/` 只用于 `run.py` 生成末端 RMSE 摘要。`chirp_cube.npy` 保留在
采集包中作为无损原始数据和采集契约的一部分，但 base 算法只使用导出的帧级
`adc_cube.npy`。

代码职责：

- `io.py`：读取统一输入包，构造雷达、ADXL 和目标输入。
- `frontend.py`：Hamming Range FFT、Angle DBF 和目标 IQ 提取。
- `selection.py`：首个观测的候选峰合并与目标保留。
- `phase.py`：因果 IQ 圆拟合和相位连续化。
- `acceleration.py`：ADXL 原生时间轴预积分。
- `kalman.py`：固定 AoA 几何 beta 的多目标共享结构相位 Kalman。
- `run.py`：单一命令行入口和结果输出。
