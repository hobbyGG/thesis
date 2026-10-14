# 结构位移估计算法

这是唯一保留的离线算法入口。它读取采集程序或论文参数仿真程序生成的统一
`capture_root`，输出结构位移结果；不生成场景、不控制硬件、不读取真值参与估计。

```bash
python3 -m system.algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/algorithm-result.npz
```

算法处理流程为：

```text
500 Hz 帧级 adc_cube（4 个 MIMO loop 的复数平均）
→ Hamming 窗 Range FFT
→ 8 虚拟阵元 DBF
→ 首帧距离—角度峰值检测与近邻峰合并
→ 固定目标 range/angle 单元的慢时间 IQ
→ 每个目标的递推代数圆拟合与圆心补偿
→ 最近邻 2π 相位展开
→ 固定转换系数 β_i = 1 / |cos θ_i|
→ ADXL355 静止窗零偏扣除与原生时间轴区间预积分
→ 以加速度预积分量驱动预测的共享结构相位 Kalman 滤波
→ 目标测量方差按后验残差更新
→ 结构位移估计 q̂
```

算法只依赖以下输入：

```text
radar/algorithm_input/adc_cube.npy
radar/algorithm_input/manifest.json
adxl355/algorithm_input/acceleration_mps2.npy
adxl355/algorithm_input/estimated_sample_monotonic_ns.npy
sync/timeline.json
```

仿真包中的 `truth/` 仅用于 `run.py` 生成末端 RMSE 摘要。`chirp_cube.npy` 保留在
采集包中作为无损原始数据和采集契约的一部分，但算法只使用导出的帧级
`adc_cube.npy`。

代码职责：

- `io.py`：读取统一输入包，构造雷达、ADXL 和目标输入；`extract_targets`（前端与目标检测）、`build_radar_input`（圆拟合与目标选择）、`build_acceleration_input`（零偏扣除与预积分）可单独调用。
- `frontend.py`：Hamming Range FFT、Angle DBF 和目标 IQ 提取。
- `selection.py`：首帧候选峰合并与目标保留。
- `phase.py`：递推圆拟合、圆心补偿与最近邻相位展开。
- `acceleration.py`：ADXL 原生时间轴预积分。
- `kalman.py`：固定转换系数 β_i 的多目标共享结构相位 Kalman 滤波。
- `run.py`：命令行入口与结果输出。
