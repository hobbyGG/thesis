# 工作区地图

工作区只保留一条可复现的实验主线。采集和仿真都输出同一种
`capture_root`，算法从该输入包直接生成位移结果。

| 路径 | 职责 |
|---|---|
| `system/capture_program/` | IWR1843/DCA1000、ADXL355、同步时间轴与采集包导出 |
| `paper_bridge_simulation/` | A20 参数化磁浮轨道梁响应与同格式仿真包 |
| `system/algorithm/` | Hamming 窗 Range FFT、DBF、IQ 圆心补偿、固定转换系数 β_i、ADXL 预积分、共享 Kalman 滤波 |
| `tests/` | 采集包契约、仿真响应与算法测试 |
| `tool/` | 结果绘图和 A20 响应辅助脚本 |

当前说明：

- [`current_method_specification.md`](current_method_specification.md)：算法的公式、参数与文件职责。
- [`current_research_data_flow.md`](current_research_data_flow.md)：从采集到结果的数据流与实验边界。
- [`radar_method_search_2010_2026/`](radar_method_search_2010_2026/)：雷达位移测量方法文献调研。
- `ref_papers/`：论文全文、硬件资料和结构健康监测参考文献。
- `hardware_manuals/`、`hardware_schemes/`：设备说明与采集方案。

旧实验结果、比较分支、归档目录和生成图片不属于当前工作区。
