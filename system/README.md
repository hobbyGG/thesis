# 核心代码

该目录包含论文实验的算法和硬件采集边界：

- `system/algorithm/`：离线位移估计主链路；
- `system/capture_program/`：IWR1843、DCA1000、ADXL355 和同步时间轴采集程序。

仿真程序 `paper_bridge_simulation/` 生成与采集程序相同的 capture package，
由 `system.algorithm` 读取并输出位移结果。
