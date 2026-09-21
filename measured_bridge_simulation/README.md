# 实测桥梁半实测场景

这里是一个直接的、可复现的研究数据生成器，不是多场景仿真框架。它只把实测 TDMS 位移记录转换成算法可读的标准输入包。

该目录只保留一个场景：读取 `datafile/20250320test12.tdms` 中的 `卡3激光位移/3-4`，截取 15.33–19.33 s，生成标准 capture package。

```bash
python3 -m measured_bridge_simulation \
  --output /tmp/measured_bridge_capture \
  --duration 4.0 \
  --seed 2026
```

输出包括：

- `radar/algorithm_input/`：合成 ADC/IQ 和 chirp cube；
- `adxl355/algorithm_input/`：激光二阶导数驱动的结构轴加速度和三轴数组；
- `sync/`：雷达时间轴和同步清单；
- `truth/`：评价使用的激光位移、时间轴和加速度。

它与 `capture_program/` 的输入包共享雷达、ADXL 和同步目录。算法不需要知道数据来自 TDMS 还是实测硬件。
