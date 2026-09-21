# 当前工作区记忆

当前研究代码只保留三层：

- `capture_program/`：实测 IWR1843/DCA1000 + ADXL355 采集，输出标准 `capture_root`；
- `measured_bridge_simulation/`：读取 TDMS 激光桥梁位移，生成同样的 `capture_root`；
- `algorithm/`：只读取 `capture_root`，运行 Range-Angle、局部 MUSIC/ML、冻结几何 beta、异步加速度预积分和多目标结构主相位 Kalman。

主算法入口：

```bash
python3 -m algorithm.run --input /path/to/capture_root --output /tmp/result.npz
```

半实测包入口：

```bash
python3 -m measured_bridge_simulation --output /tmp/capture --duration 4 --seed 2026 --overwrite
```

当前论文文档：

- 主要研究思路：`thesis_idea_overview.md`
- 创新点：`innovation_points/`
- 代码链路审查：`docs/algorithm_chain_review.md`
- 目录和数据流图：`idea/overall_processing_architecture.md`

已删除的内容包括旧多场景仿真、Ma 复现、baseline 注册表、online beta 和扩展验证脚本。不要从 `archive/` 推断当前代码入口。
