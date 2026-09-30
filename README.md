# 论文实验工作区

当前代码只保留一条论文实验链路：采集程序输出统一输入包，A20 论文参数仿真程序也输出同样的输入包，算法目录读取输入包并输出位移结果。

```text
capture_program/                  实测硬件采集与标准化导出
paper_bridge_simulation/       A20 论文参数响应驱动的仿真包生成
algorithm/                        Range-Angle + AoA + 固定 beta + Kalman
```

两种输入包都使用同一组目录：

```text
capture_root/
├── radar/algorithm_input/        adc_cube.npy、frame_times_s.npy、manifest.json
├── adxl355/algorithm_input/      acceleration_mps2.npy、时间轴、manifest.json
├── sync/                         timeline.json、manifest.json、雷达时间轴
├── status.json                    采集完成状态（实测包）
└── truth/                         仿真评价真值，可选，算法不读取
```

`capture_program/` 保留 IWR1843、DCA1000、ADXL355、GPIO 时间轴和算法输入导出。它不调用论文算法。实测包交给算法时，算法只读取 `radar/algorithm_input`、`adxl355/algorithm_input` 和 `sync`。

代码性质已经按用途分开：`algorithm/` 和 `paper_bridge_simulation/` 是离线学术实验代码，保持直接的数组处理和公式实现，不加入服务化、重试或泛化防御框架；`capture_program/` 是硬件采集边界，保留设备生命周期、数据完整性和输出契约检查，因为它负责把真实设备数据变成可用的实验输入。

仿真场景使用 A20 论文中 24.768 m 梁、300 km/h 工况和六阶识别模态（10.35、13.41、27.10、43.84、52.93、84.44 Hz）。`response.py` 以 3 kHz、4 s 生成响应，准静态挠度与阻尼模态共同构成位移，并把总位移峰值整体缩放到 1.712 mm。雷达慢时间采样按 IWR1843 硬件触发配置为 100 Hz，保留每帧 16 个 MIMO loop；ADXL355 为 1 kHz。模态加速度的 0.45 m/s² 是按论文图量级设置的仿真假设，不是额外实测标定。

```bash
python3 -m paper_bridge_simulation \
  --output /tmp/paper_bridge_capture \
  --duration 4.0 \
  --seed 2026
```

算法只有一个入口，没有 method、scenario、Ma 或 baseline 参数：

```bash
python3 -m algorithm.run \
  --input /tmp/paper_bridge_capture \
  --output /tmp/paper_bridge_result.npz
```

算法实际链路是：

```text
统一 capture_root
→ Range FFT + Angle DBF
→ 记录级距离—角度峰值检测
→ 局部 MUSIC/ML 连续 AoA
→ beta = 1 / |cos(theta)|，整段冻结
→ ADXL 原生时间轴区间预积分
→ 加速度预测的结构主相位 Kalman
→ 后验残差更新每个目标 R
→ q_hat_m 与诊断结果
```

`algorithm/` 不生成场景、不读真值、不包含硬件控制。仿真包里的 `truth/` 只用于最终 RMSE 评价，不能进入候选检测、AoA、beta 或 Kalman。

主要文件：

- [`algorithm/io.py`](/Users/umep/thesis/algorithm/io.py)：读取两种来源共有的输入包并构造算法输入。
- [`algorithm/frontend.py`](/Users/umep/thesis/algorithm/frontend.py)：距离—角度处理和目标 slow-time 提取。
- [`algorithm/angle_estimation.py`](/Users/umep/thesis/algorithm/angle_estimation.py)：局部 MUSIC/ML AoA。
- [`algorithm/selection.py`](/Users/umep/thesis/algorithm/selection.py)：记录级候选峰和目标保留。
- [`algorithm/kalman.py`](/Users/umep/thesis/algorithm/kalman.py)：固定几何 beta 的结构主相位 Kalman。
- [`paper_bridge_simulation/package_builder.py`](/Users/umep/thesis/paper_bridge_simulation/package_builder.py)：仿真包生成。
- [`capture_program/README.md`](/Users/umep/thesis/capture_program/README.md)：实测采集输入契约。
- [`thesis_idea_overview.md`](/Users/umep/thesis/thesis_idea_overview.md)：主要研究思路。
- [`innovation_points/`](/Users/umep/thesis/innovation_points/)：创新点说明。
- [`docs/algorithm_chain_review.md`](/Users/umep/thesis/docs/algorithm_chain_review.md)：当前代码链路审查。
- [`docs/current_research_data_flow.md`](/Users/umep/thesis/docs/current_research_data_flow.md)：从雷达发射、树莓派采集到最终位移结果的完整数据流和公式。

检查代码和运行链路：

```bash
python3 -m compileall -q algorithm paper_bridge_simulation
python3 -m unittest discover capture_program/tests -v
python3 -m algorithm.run --input /tmp/paper_bridge_capture --output /tmp/paper_bridge_result.npz
```

历史多场景仿真、Ma 复现、扩展实验和旧报告输出已从当前代码树删除；需要追溯时看 `archive/`，不要把其中内容当作当前实现。

每个代码区的局部约束见对应的 [`AGENTS.md`](/Users/umep/thesis/AGENTS.md)、[`algorithm/AGENTS.md`](/Users/umep/thesis/algorithm/AGENTS.md)、[`paper_bridge_simulation/AGENTS.md`](/Users/umep/thesis/paper_bridge_simulation/AGENTS.md) 和 [`capture_program/AGENTS.md`](/Users/umep/thesis/capture_program/AGENTS.md)。
