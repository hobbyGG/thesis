# Thesis Workspace README

这个文件夹是一个论文工作区，主题是“基于毫米波雷达与 MEMS 加速度计融合的结构位移测量方法研究”。它不是单纯代码仓库，而是同时包含论文正文、理论笔记、文献 PDF、仿真代码、实测数据、验证输出、图表资产和 Obsidian 画图配置。

## 先看这里：已有做图和报告工具

后续 AI 或人工需要画图、出报告、生成结果图时，先查下面这些位置，避免重复造工具。

| 需求 | 已有位置 | 功能 |
|---|---|---|
| 生成基础 SVG 折线图 | `simulation/phase1/reporting.py` 的 `write_basic_svg(...)` | 纯 Python/NumPy/标准库写 SVG，不依赖 matplotlib。验证报告和诊断图都用它。 |
| 生成验证报告和关键诊断图 | `simulation/phase1/reporting.py` 的 `write_validation_report(...)` | 写 `metrics.csv`、`feasibility_gates.json`、`summary.md` 和 `plots/*.svg`。 |
| 生成场景真值时域/频域图 | `simulation/phase1/scenario_diagnostics.py` | 写 `scenario_parameters.csv`、`summary.md` 和每个场景的位移/加速度 SVG 图。 |
| 论文汇报可直接引用的图 | `reports/numerical_simulation_assets/` 和 `reports/numerical_simulation_assets_png/` | SVG 源图和 PNG 版本，已包含 range-angle、target selection、phase correction、adaptive R、kappa bootstrap、激光实测分析图。 |
| 仿真验证输出图 | `simulation/outputs/phase1_validation/plots/`、`simulation/outputs/phase1_report_validation/plots/` | 由验证脚本生成的 SVG 图。 |
| 场景诊断输出图 | `simulation/outputs/phase1_scenario_diagnostics/plots/` | 每个场景的 time/frequency displacement/acceleration SVG。 |
| 实测激光数据分析图 | `datafile/analysis/*.svg` | 激光通道时域、频谱、动态相关性、配对分数等图表。 |
| Markdown 流程图/公式图 | `idea/overall_processing_architecture.md`、`idea/kalman_flowchart_preview.md`、`idea/mehrmaid_formula_test.md` | 使用 `mehrmaid` 代码块组织 Mermaid + Markdown/公式流程图。 |
| Obsidian 手绘/流程图插件 | `.obsidian/plugins/obsidian-excalidraw-plugin/` 和 `.obsidian/plugins/mehrmaid/` | 已启用 Excalidraw 和 Mehrmaid。不要误以为没有画图环境。 |
| 主论文 Markdown 转 HTML/PDF 草稿 | `tmp/pdfs/render_report_pdf.py` | 针对主论文 Markdown 的临时渲染脚本，支持表格、图片、公式、Mermaid fallback。 |

常用出图命令：

```bash
python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
python3 -m simulation.phase1.run_scenario_diagnostics --output-dir simulation/outputs/phase1_scenario_diagnostics
python3 -m simulation.phase1.run_extended_validation --output-dir simulation/outputs/phase1_extended_validation
```

## 一句话概览

当前已实现的是 Phase 1 算法级验证链路：生成结构位移真值，合成毫米波雷达多目标 wrapped phase 和 synthetic ADC/range-angle frontend，生成加速度观测，执行 target selection、结构主相位 Kalman 融合、Ma-family baseline 对比、指标/gate 评估，并输出 CSV/Markdown/SVG 报告。

当前未实现的是完整真实毫米波雷达实测链路：真实 IWR1843 ADC 文件解析、真实天线幅相标定、真实 TDM-MIMO 相位补偿、真实雷达与 TDMS 同步采集验证、现场多径长期稳定性验证。

## 重要入口

| 想做什么 | 先看哪里 |
|---|---|
| 理解整体论文思路 | `thesis_idea_overview.md`、`next_chat_memory_prompt.md` |
| 理解最终阶段性论文正文 | `基于毫米波雷达与 MEMS 加速度计融合的结构位移测量方法研究.md` |
| 理解方法和代码对应关系 | `docs/algorithm_chain_review.md` |
| 理解 Phase 1 仿真包 | `simulation/phase1/README.md` |
| 运行完整单元测试 | `python3 -m unittest discover tests -v` |
| 运行 Phase 1 标准验证 | `python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation` |
| 运行含 TDMS 半实测桥梁场景的验证 | `python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation`，当前默认包含半实测场景 |
| 只跑纯合成验证 | `python3 -m simulation.phase1.run_validation --exclude-measured-bridge --output-dir /tmp/phase1_validation_synthetic_only` |
| 生成论文实验章节表格 | `python3 -m simulation.phase1.run_extended_validation --output-dir simulation/outputs/phase1_extended_validation` |
| 生成场景参数和真值图 | `python3 -m simulation.phase1.run_scenario_diagnostics --output-dir simulation/outputs/phase1_scenario_diagnostics` |
| 生成单次 `.npz` 仿真数据 | `python3 -m simulation.phase1.run_phase1 --output simulation/outputs/phase1_multifrequency.npz` |

## 顶层目录地图

| 路径 | 内容 |
|---|---|
| `simulation/` | Python 仿真和验证代码，核心在 `simulation/phase1/`。 |
| `tests/` | `unittest` 测试，覆盖仿真、前端、目标选择、Kalman、baseline、报告、半实测场景。 |
| `reports/` | 已整理的 Phase 1 方法与仿真汇报，以及可直接引用的 SVG/PNG 图表资产。 |
| `datafile/` | 实测数据：`20250320test12.tdms`、CSV、metadata，以及激光/加速度分析结果。 |
| `docs/` | 方法链审查和历史 implementation plan。 |
| `idea/` | 总体处理架构、Kalman 流程图、Mehrmaid 测试图。 |
| `innovation_points/` | 三个创新点的理论说明：多目标选择、转换系数稳定性、结构主相位 Kalman 融合。 |
| `ref_papers/` | 文献 PDF 库，共约 232 个 PDF，含主要参考、AoA/range-angle、无关文献分类。 |
| `tmp/` | 临时文件：PDF 文本抽取、HTML/PDF 渲染草稿、渲染页图片。 |
| `.obsidian/` | Obsidian vault 配置和插件，包括 Excalidraw、Mehrmaid。 |

## 顶层 Markdown 文件

| 文件 | 用途 |
|---|---|
| `基于毫米波雷达与 MEMS 加速度计融合的结构位移测量方法研究.md` | 当前阶段性论文/报告正文，旁边有同名 PDF。 |
| `thesis_idea_overview.md` | 论文整体思路、数学模型、多 target 选择、转换因子和硬件约束总览。 |
| `next_chat_memory_prompt.md` | 给新对话续接用的上下文 prompt，包含最新版方法闭环和待讨论问题。 |
| `draft_inverted_radar_theory_model.md` | 倒挂式毫米波雷达位移测量理论模型草稿。 |
| `integrated_literature_review.md` | 第二章文献综述整合稿。 |
| `innovation_1_literature_review.md`、`innovation_2_range_angle_target_literature_review.md`、`innovation_3_range_angle_target_literature_review.md` | 三个创新点对应的综述正文。 |
| `innovation_1_literature_review_prompt.md`、`innovation_2_literature_review_prompt.md`、`innovation_3_literature_review_prompt.md` | 用于生成/改写综述的详细 prompt。 |
| `literature_reference_assessment.md` | 大量文献相关性评估。 |
| `kalman_data_fusion_reference_check.md` | Kalman / 数据融合参考文献补查。 |
| `simulation_design_literature_review.md` | 仿真设计相关文献综述。 |

## `simulation/phase1` 功能地图

| 模块 | 功能 |
|---|---|
| `config.py` | `Phase1Config`，集中定义采样率、ADC 参数、目标几何/SNR、Kalman 参数、半实测桥梁数据配置。注意 `sample_rate_hz` 是 100 Hz slow-time/frame/Kalman 率，不是 MHz ADC 快时间采样率。 |
| `truth.py` | 生成结构位移真值：多频振动、quiet start、vehicle event、strong wrapping 等 profile。 |
| `radar.py` | 生成目标级雷达观测：true/measured kappa、LoS phase、wrapped phase、IQ、dropout/degradation。 |
| `accelerometer.py` | 生成或封装加速度观测，含噪声、偏置、同步误差。 |
| `frontend.py` | synthetic ADC cube、Range FFT、Angle FFT/DBF、range-angle map、frontend target slow-time 提取。 |
| `selection.py` | 2D peak detection、同 range 近角度合并、presence/SNR/结构频带一致性评分、selected target 输出。 |
| `inputs.py` | 统一场景输入构建层：一个 `Phase1Config` 生成 truth、accelerometer、target-level radar、frontend/range-angle、selected frontend、range-bin-only、Ma2026 等命名视图。 |
| `method_registry.py` | 方法/基线注册表：集中声明要跑哪些方法、每个方法吃哪个输入视图、评估时如何映射 target reference。 |
| `algorithm.py` | proposed 方法：结构主相位 Kalman、prediction-aided phase correction、online kappa bootstrap、target-wise adaptive R。 |
| `baselines.py` | oracle、Itoh-LS、single-target Ma-style、range-bin-only mixed phase、Ma-style iterative beta、固定 kappa 等 baseline。 |
| `ma2026/` | 正式 Ma-family baseline 复现：Ma 2023 range-bin beta 标定 + Ma 2026 acceleration-aided LoS phase Kalman。 |
| `pipeline.py` | 薄编排层：构建统一输入、运行 `method_registry`、生成指标和 artifacts；不再直接拼雷达输入。 |
| `evaluation.py` | method result 转指标行。 |
| `metrics.py` | RMSE/MAE/max error、phase RMSE、convergence 等指标工具。 |
| `gates.py` | feasibility gate 定义，例如 strong wrapping、same-range far-angle、vehicle event 等验收条件。 |
| `reporting.py` | CSV/JSON/Markdown/SVG 报告输出，也是主要做图工具。 |
| `scenario_diagnostics.py` | 场景参数表和每个场景 truth 的时域/频域 SVG 图。 |
| `extended_experiments.py` | Monte Carlo、ablation、AoA sensitivity、SNR sensitivity 表格生成。 |
| `measured_bridge.py` | TDMS 半实测桥梁数据读取、事件窗口截取、频域滤波、激光位移到加速度反演。 |
| `methods.py` | 兼容旧导入路径的 re-export 层。 |
| `run_phase1.py` | 单次仿真写 `.npz`。 |
| `run_validation.py` | 标准 validation CLI。 |
| `run_extended_validation.py` | extended paper experiments CLI。 |
| `run_scenario_diagnostics.py` | 场景参数和 truth 图 CLI。 |

## Phase 1 场景

场景定义在 `simulation/phase1/scenarios/`，由 `build_phase1_scenarios()` 汇总。

| 场景 | 验证重点 |
|---|---|
| `nominal_multifrequency` | 标准多频结构振动。 |
| `ma2023_balanced_good_targets` | 模拟 Ma 2023 多个优质目标条件。 |
| `strong_wrapping` | 强相位缠绕，检验 prediction-aided phase correction。 |
| `aoa_error_bootstrap` | AoA 初值误差下的 online kappa bootstrap。 |
| `target_snr_drop` | 目标 SNR 退化下的 target-wise adaptive R。 |
| `target_dropout` | 单 target 缺失/遮挡。 |
| `mixed_scatterer_rangebin` | 同 rangeBin 复合散射相位混合。 |
| `same_range_far_angles` | 同 rangeBin 但远角度目标分离，是 range-angle 前端的关键动机场景。 |
| `low_snr_multitarget` | 低 SNR 多目标融合。 |
| `vehicle_event_nonstationary` | quiet start 后非平稳车辆事件，检验 target selection 和全流程鲁棒性。 |
| `measured_bridge_point4_transverse` | 可选半实测场景，用 TDMS 激光位移驱动真值，雷达仍为物理相位模型合成。 |

## 输出目录怎么读

| 路径 | 来源 | 内容 |
|---|---|---|
| `simulation/outputs/phase1_validation/` | `run_validation` | 当前标准验证输出：`metrics.csv`、`feasibility_gates.json`、`summary.md`、`plots/*.svg`。 |
| `simulation/outputs/phase1_report_validation/` | 报告用验证输出副本 | 与报告/论文图表更贴近的 validation 输出。 |
| `simulation/outputs/phase1_extended_validation/` | `run_extended_validation` | Monte Carlo、ablation、AoA/SNR sensitivity CSV 和 `extended_summary.md`。 |
| `simulation/outputs/phase1_report_extended_validation/` | 报告用 extended 输出副本 | 论文汇报使用的 extended 表格。 |
| `simulation/outputs/phase1_scenario_diagnostics/` | `run_scenario_diagnostics` | 场景参数表、summary、每场景时域/频域 SVG。 |
| `simulation/outputs/phase1_multifrequency.npz` | `run_phase1` | 单次 synthetic multifrequency 仿真数据。 |

## `reports` 目录

| 路径 | 内容 |
|---|---|
| `reports/phase1_method_and_simulation_report.md` | Phase 1 方法与仿真汇报，包含流程图、实验设计、关键图、结果表和后续工作。 |
| `reports/numerical_simulation_assets/` | 汇报/论文用 SVG 源图。 |
| `reports/numerical_simulation_assets_png/` | 同一批图的 PNG 版本，适合插入 Markdown/PDF/Word。 |

已有关键图包括：

- `vehicle_event_nonstationary_range_angle_frame`
- `vehicle_event_nonstationary_target_selection_timeline`
- `vehicle_event_nonstationary_selected_vs_all_targets_displacement`
- `strong_wrapping_phase_correction`
- `target_snr_drop_adaptive_r`
- `aoa_error_bootstrap_kappa_bootstrap`
- `laser_time_channels`
- `laser_spectrum_channels`
- `laser_dynamic_correlation`

## `datafile` 目录

| 路径 | 内容 |
|---|---|
| `datafile/20250320test12.tdms` | 原始 TDMS 实测数据。 |
| `datafile/20250320test12.csv` | 对应 CSV 数据。 |
| `datafile/20250320test12.metadata.json` | 数据元信息。 |
| `datafile/analysis/` | 激光/加速度预分析结果，包括 SVG、CSV、JSON。 |

半实测场景默认使用：

- 激光组：`卡3激光位移`
- 激光通道：`3-4`
- 事件窗口：`15.33s` 到 `19.33s`
- 分析频带：`0.2-10 Hz`
- 工频陷波：`50/100/150 Hz`
- 默认加速度来源：`laser_derived`

## `ref_papers` 文献库

`ref_papers/` 约 1.2 GB，共约 232 个 PDF。重点不是逐个打开，而是先读分类 README：

| 路径 | 内容 |
|---|---|
| `ref_papers/00_primary_references/README.md` | 主要参考文献速读说明，结构位移、雷达相位、加速度融合、Kalman 等核心文献。 |
| `ref_papers/01_AoA/README.md` | AoA / Range-Angle / MIMO-FMCW 方法论文速读说明。 |
| `ref_papers/99_irrelevant_literature/README.md` | 已判断偏离当前主题或较低优先级的文献。 |

`tmp/pdf_text/` 中有部分 PDF 抽取出的文本，可用于快速检索文献内容。

## `docs`、`idea`、`innovation_points`

| 路径 | 内容 |
|---|---|
| `docs/algorithm_chain_review.md` | 最重要的追踪表：理论模块、代码入口、测试证据、输出证据、状态和缺口。 |
| `docs/superpowers/plans/` | 历史 implementation plan，能看出 Phase 1 和半实测场景是如何拆解实现的。 |
| `idea/overall_processing_architecture.md` | 总体处理架构，含 Mehrmaid 流程图。 |
| `idea/kalman_flowchart_preview.md` | Kalman 融合流程图预览。 |
| `innovation_points/online_multi_target_selection.md` | 创新点：距离-角度联合维度在线参考目标选取。 |
| `innovation_points/equivalent_conversion_factor_stability.md` | 创新点：range-angle target 转换系数估计与等效稳定性。 |
| `innovation_points/multi_target_phase_kalman_fusion.md` | 创新点：多静止参考目标结构主相位 Kalman 融合。 |

## 测试覆盖

测试都在 `tests/`，使用标准库 `unittest`：

```bash
python3 -m unittest discover tests -v
```

主要覆盖面：

- `test_phase1_simulation.py`：真值、雷达、加速度合成。
- `test_phase1_frontend.py`：ADC cube、range/angle FFT、frontend target 提取。
- `test_phase1_target_selection.py`：峰值检测、角度合并、presence/SNR/频带筛选。
- `test_phase1_methods.py`：proposed Kalman、kappa bootstrap、adaptive R、算法可见输入边界。
- `test_phase1_ma2026_reproduction.py`：Ma-family baseline 复现。
- `test_phase1_validation.py`：场景、指标、gates、报告和 SVG 输出。
- `test_phase1_extended_experiments.py`：Monte Carlo / ablation / sensitivity 表格。
- `test_phase1_measured_bridge.py` 和 `test_phase1_measured_bridge_integration.py`：TDMS 半实测桥梁数据与场景集成。
- `test_phase1_scenario_diagnostics.py`：场景诊断表和图生成。
- `test_phase1_architecture.py`：模块拆分和兼容 API。

## 依赖和注意事项

- 仓库没有看到 `requirements.txt` 或 `pyproject.toml`。
- 核心仿真依赖 `numpy`。
- 半实测 TDMS 读取依赖 `nptdms`。
- 代码刻意使用 `simulation/phase1/reporting.py` 生成 SVG，不要求 matplotlib/pandas。
- `.DS_Store`、`__pycache__`、`.pytest_cache`、`simulation/outputs/` 多数是本地或生成文件，改动前要分清是不是用户已有工作成果。

## 后续 AI 协作建议

1. 需要理解方法时，先读 `docs/algorithm_chain_review.md` 和 `simulation/phase1/README.md`。
2. 需要画图时，先查本 README 的“已有做图和报告工具”，尤其是 `reporting.py`、`scenario_diagnostics.py`、`reports/numerical_simulation_assets_png/` 和 Obsidian 插件。
3. 需要新增场景/测试情况时，在 `simulation/phase1/scenarios/` 新增一个 `build(base)` 模块，通过 `Phase1Config` 设置 target 数量、角度、SNR、range bin、dropout/degradation、ADC 参数等，并在 `scenarios/__init__.py` 注册。
4. 需要改变雷达信息如何供算法使用时，优先看 `simulation/phase1/inputs.py` 的 `ScenarioInputs`、`RadarViews`、`FrontendViews`，不要在 `pipeline.py` 内临时拼输入。
5. 需要新增方法时，先在 `algorithm.py`、`baselines.py` 或独立包里实现，再到 `method_registry.py` 增加一个 `MethodSpec`；`pipeline.py` 不应硬编码新方法。
6. 需要新增指标或验收条件时，看 `metrics.py` 和 `gates.py`。
7. 需要证明改动正确时，优先补 `tests/` 里的对应测试，再运行 `python3 -m unittest discover tests -v`。
8. 需要写论文段落时，先查 `thesis_idea_overview.md`、`innovation_points/`、`integrated_literature_review.md` 和相关 `*_prompt.md`。

## 当前边界结论

已实现：

- synthetic ADC cube、Range FFT、Angle FFT/DBF、range-angle map。
- 2D peak detection、同 rangeBin 近角度合并、同 rangeBin 远角度分离。
- target presence、SNR、结构频带一致性筛选。
- AoA cold start、prediction-aided phase correction、online kappa bootstrap。
- 多目标结构主相位 Kalman、target-wise adaptive R。
- Ma 2023 + Ma 2026 family baseline 复现。
- 标准合成验证、extended validation、场景诊断、SVG/CSV/Markdown 报告输出。
- TDMS 激光位移驱动的半实测桥梁场景。

未实现：

- 真实 IWR1843 ADC 文件解析。
- 真实天线幅相标定和 TDM-MIMO 相位补偿。
- 实测毫米波雷达 ADC 与 TDMS 同步采集验证。
- 真实桥梁现场多径环境建模与长期稳定性验证。
- 完整现场安装姿态标定流程。
