# 纯算法目录

这里是离线学术实验算法，不承担硬件控制、数据采集或服务运行。代码直接读取统一 `capture_root`，执行当前论文链路并写出结果；数值稳定处理只保留在对应公式附近。

算法入口只接受一个统一的 `capture_root`：

```bash
python3 -m algorithm.run --input /path/to/capture_root --output /tmp/result.npz
```

The default `frame` mode reads the coherent mean of four saved MIMO loops per
about 884.851 Hz observation.  The `chirp` mode remains available for
loop-level comparison.  To run loop-level processing on a package that
contains `chirp_cube.npy`, use:

```bash
python3 -m algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/chirp-result.npz \
  --radar-mode chirp
```

In chirp mode each saved MIMO loop becomes one slow-time sample; in the default frame mode, the exported `adc_cube` is the four-loop coherent mean.  The loop
timestamps are formed from `loop_start_interval_s` in the radar manifest, and
the ADXL355 preintegration, Kalman update, truth alignment, and output time
axis all use that expanded timeline.  The default frame path remains unchanged.
The chirp mode is a loop-level comparison experiment: it does not add TDM motion compensation,
and its timestamps are burst-like rather than a uniform 3.9 kHz stream.
Cold-start statistics use elapsed time; measurement-noise forgetting is scaled
by each interval relative to the frame period so both modes use the same
physical adaptation time. The `frame` mode remains available for comparison.

模块顺序固定为：

1. `io.py` 读取雷达 ADC、ADXL 结构轴和同步时间轴。
2. `frontend.py` 做 Range FFT、Angle DBF、记录级候选提取和 slow-time 目标观测。
3. `angle_estimation.py` 用局部 MUSIC/ML 将角度从 FFT 粗网格精修为连续值。
4. `selection.py` 合并近邻峰并保留记录级有效目标。
5. `acceleration.py` 将 native ADXL 样本预积分到雷达相邻帧区间。
6. `beta.py` 以 AoA 的 `beta=1/|cos(theta)|` 为默认值；只有测得的距离 FFT SNR 不低于 15 dB、ADXL 匹配位移激励持续至少 0.10 s，且至少两个目标的 AoA–ADXL beta 相对差达到 1% 时，才切换到因果 ADXL 匹配 beta。
7. `kalman.py` 用加速度预测结构主相位，并将通过门控的 beta 送入多目标 Kalman 更新。

算法不生成数据，也不读取 `truth/` 参与估计。`truth/` 只在 `run.py` 写结果摘要时计算仿真 RMSE。
