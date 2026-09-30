# 纯算法目录

这里是离线学术实验算法，不承担硬件控制、数据采集或服务运行。代码直接读取统一 `capture_root`，执行当前论文链路并写出结果；数值稳定处理只保留在对应公式附近。

算法入口只接受一个统一的 `capture_root`：

```bash
python3 -m algorithm.run --input /path/to/capture_root --output /tmp/result.npz
```

The default `frame` mode reads the frame-level coherent mean.  To run the
experimental chirp-loop path on a package that contains `chirp_cube.npy`, use:

```bash
python3 -m algorithm.run \
  --input /path/to/capture_root \
  --output /tmp/chirp-result.npz \
  --radar-mode chirp
```

In this mode each saved MIMO loop becomes one slow-time sample.  The loop
timestamps are formed from `loop_start_interval_s` in the radar manifest, and
the ADXL355 preintegration, Kalman update, truth alignment, and output time
axis all use that expanded timeline.  The default frame path remains unchanged.
This is a chirp-level experiment: it does not add TDM motion compensation,
and its timestamps are burst-like rather than a uniform 3.9 kHz stream.
Cold-start statistics use elapsed time; measurement-noise forgetting is scaled
by each interval relative to the frame period so both modes use the same
physical adaptation time.

模块顺序固定为：

1. `io.py` 读取雷达 ADC、ADXL 结构轴和同步时间轴。
2. `frontend.py` 做 Range FFT、Angle DBF、记录级候选提取和 slow-time 目标观测。
3. `angle_estimation.py` 用局部 MUSIC/ML 将角度从 FFT 粗网格精修为连续值。
4. `selection.py` 合并近邻峰并保留记录级有效目标。
5. `acceleration.py` 将 native ADXL 样本预积分到雷达相邻帧区间。
6. `kalman.py` 冻结 `beta=1/|cos(theta)|`，用加速度预测结构主相位并做多目标 Kalman 更新。

算法不生成数据，也不读取 `truth/` 参与估计。`truth/` 只在 `run.py` 写结果摘要时计算仿真 RMSE。
