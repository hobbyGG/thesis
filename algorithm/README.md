# 纯算法目录

算法入口只接受一个统一的 `capture_root`：

```bash
python3 -m algorithm.run --input /path/to/capture_root --output /tmp/result.npz
```

模块顺序固定为：

1. `io.py` 读取雷达 ADC、ADXL 结构轴和同步时间轴。
2. `frontend.py` 做 Range FFT、Angle DBF、记录级候选提取和 slow-time 目标观测。
3. `angle_estimation.py` 用局部 MUSIC/ML 将角度从 FFT 粗网格精修为连续值。
4. `selection.py` 合并近邻峰并保留记录级有效目标。
5. `acceleration.py` 将 native ADXL 样本预积分到雷达相邻帧区间。
6. `kalman.py` 冻结 `beta=1/|cos(theta)|`，用加速度预测结构主相位并做多目标 Kalman 更新。

算法不生成数据，也不读取 `truth/` 参与估计。`truth/` 只在 `run.py` 写结果摘要时计算半实测 RMSE。
