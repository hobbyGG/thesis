# 无记忆 agent 交接 Prompt v2

核对日期：2026-09-08。工作目录：`/Users/umep/thesis`。
本文件可整份作为新 agent 的初始 prompt；也可要求它先完整阅读本文件，再读取下述代码与证据。

## 1. 你的任务和证据规则

你接手的是毫米波雷达与 MEMS 加速度计融合测量结构位移的论文及工程项目。请用中文协作，目标是把现有采集程序、离线融合算法和磁浮轨道梁实验流程做成可复现、可解释的成品。

用户的位移精度目标为 RMSE < 0.01 mm，即 1e-5 m。这是待验证的目标，不是现有实机性能结论。不能通过真值泄漏、重复处理真值、挑选随机种子、事后调整评价区间或一律回退来制造达标结论。

本文件记录交接时已核对的状态，不是永远正确的快照。用户最新要求决定任务方向；当前代码决定实际行为；带配置和来源的实验产物决定已验证到哪一步。代码不等于理论正确，测试通过不等于实机精度达标。发现文档、实现、产物冲突时，明确指出冲突并核实，不要静默选一个有利版本。

工作区有大量未提交、未跟踪的实现，HEAD 为 `7d51c6f`（2026-08-23），不能只看提交历史判断进度。先运行 `git status --short`，保护现有改动和实验产物，不擅自回退、清理或提交。

本轮交接只做了文件与代码只读核对，没有重新运行测试、仿真或实机采集。下面引用的旧产物必须标记为历史证据，不能表述成你本轮刚验证通过。

## 2. 用户已确定的约束

- 真实采集主机只有 Raspberry Pi 4。电脑经 Wi-Fi/SSH 控制，采集结束后可下载数据、离线运行算法；电脑不参与传感器采集计时。
- 采用 Pi GPIO 控制雷达 `SYNC_IN`。用户接受该方式的工程同步，不要求额外接 GPIO24 回环，不把追求电信号级时间戳证明设为一切工作的前置条件。
- 雷达帧率当前为 100 Hz，ADXL355 ODR 为 1000 Hz。不能擅自改成 200 Hz，也不能把雷达 MHz ADC 采样率当位移序列帧率。
- 采集格式仿真全流程只做磁浮轨道梁实测波形驱动场景；旧多场景仿真保留作对照，但不是本任务的默认范围。
- 随机传感器误差由采集模拟端统一注入一次。离线读取、预积分和融合不再人为增加一层误差。
- 用户需要修正每个 target 各不相同的 AoA/β 偏差，不能用“只校准公共角偏差”替代，也不能把所有例子都安全回退当成需求已经完成。
- 只跑与改动相关的聚焦测试，避免全量测试、全场景验证或大型 Monte Carlo。最终是否扩大验证由实际风险与当前任务决定。
- 方案讨论和实现考虑 subagent。遵循当前 AGENTS 约束：实际涉及的前端、后端、测试实现分别由对应专家承担；代码实现 agent 与主 agent 同模型同 effort。这里的 `frontend.py` 是雷达信号处理前端，不是网页 UI；不要为满足分工新增无关界面。不要默认使用 Spark。
- 做图优先复用 `/Users/umep/thesis/simulation/phase1/reporting.py` 及现有绘图工具。论文公式用 `$...$`、`$$...$$`。

## 3. 物理场景与数学定义

这是倒挂式雷达方案：雷达和 ADXL 安装在被测结构上，随结构运动；雷达观测地面坐标系中静止的多个参考散射体。不要误写成固定雷达观测运动桥梁的普通布置。安装位置、运动轴、正负号和刚体运动假设都需要在实测中核对。

设结构方向位移为 q，主相位 Θ = (4π/λ)q。当前代码使用的几何转换系数满足：

    q = β_i · d_LOS,i
    Θ = β_i · (φ_LOS,i - b_i)
    p_i = 1/β_i，AoA 初值 p_i ≈ |cos θ_i|

正负号按安装轴和相位约定处理。β 是 LOS 到结构方向的转换系数，不能写成 cos θ。

主数据流：ADC → Range FFT + Angle FFT/DBF → 多个 range-angle 目标的复数 slow-time / wrapped phase → 目标筛选 → 独立 β 预校准或 AoA 回退 → 冻结 β → 结构主相位 Kalman。

Kalman 状态为 [Θ, Θ̇]。预测辅助相位分支校正在 LOS 空间进行，然后构造结构方向观测 y_i = β_i(φ_LOS,i,corr - b_i)，H_i = [1, 0]。Q 由测量数据上的候选标定选定后固定；在线主要调整 target-wise R。

## 4. β 问题：动机、现实现和未解决边界

用户最初希望用“可靠的 Kalman 结果”反向校正各目标 β。后续讨论识别到循环依赖风险：错误 β 本身参与生成该后验，用同一后验反哺 β 可能形成自我确认。因此，当前已采用 Kalman 之前的独立原始数据预校准；不要仅凭函数名 `adaptive_beta` 恢复旧在线后验反馈。

当前主入口是 `/Users/umep/thesis/simulation/phase1/algorithm.py` 中 `estimate_proposed_full_pipeline_beta_confidence`，具体校准器在 `/Users/umep/thesis/simulation/phase1/beta_calibration.py`：

1. 输入原始多 target 相位、AoA 初值、ADXL 原生时间戳/加速度及质量信息。
2. 在不重叠的两个时间折上拟合和交叉验证；原始多目标相位的 rank-1 共同运动给出逐目标相对投影，ADXL 提供独立动力学检查、绝对候选及公共残余时延。
3. `run_captured.py` 在看验证结果之前，按 `calibration_mode` 选定模式：`validated` 用 `adxl_absolute`；未验证/仿真名义标定用 `aoa_anchored_relative`。不允许按哪一种分数更好临时切模式。
4. relative 模式依靠原始 AoA 锚定公共尺度。主配置要求至少 3 个相干参考、两折共同运动和逐目标门控通过；当前每折 ADXL 校准块最低 120 个雷达样本。10 帧冒烟测试无法检验该机制，约 240 帧也只是长度下限，不保证激励足够。
5. 全局时间轴、激励、参考集合或公共时延门失败时整组回退；单目标门失败只回退该目标至原 AoA β。接受与回退值合成后冻结，从第 0 帧完整运行 Kalman。
6. β 变化后初始结构方向 R 按 β 比值平方变换。β 方差用于门控和诊断，不当作每帧独立白噪声重复注入。

判读结果时同时看 `any_accepted`、`accepted_mask`、`accepted_count` 和逐目标拒绝原因；兼容字段 `beta_calibration_accepted` 表示全部通过，false 不能推出一个都没校准成功。

必须保留这些边界：

- relative 模式能调整逐目标比例，但公共绝对尺度仍由 AoA 提供；不能宣称解决全部公共尺度误差。未标定 ADXL 增益与 β 公共尺度可能混淆。
- rank-1 仅说明共享波形；把它解释为几何投影还依赖相同运动自由度等物理假设。雷达转动、多径、散射变化或不同模态不能凭 rank-1 自动排除。
- 双折条件 holdout 是内部接受判据，不是独立实测真值，也不等于整组模型在全新实验上的优越性证明。
- 利用整段记录预校准后从头重跑是离线批处理，不能宣传成因果在线 β 收敛。
- 低位移 RMSE 不等于 β 估计正确。必须分别报告 β/投影误差（有真值时）、接受率、回退原因和位移指标。
- 旧 online bootstrap 代码、图、`beta_history` 和旧表格仅属历史/消融。科学证据不足时可以重新讨论理论，但要交代改变的假设和代价，不能悄悄换问题。

估计主路径不得使用真实位移、真实 β、真实目标标签来选点、拟合、选 Q 或调参数；β 校准也不得使用 Kalman posterior / corrected phase。truth 只可用于生成模拟观测和估计结束后的独立评价。对 legacy/oracle baseline 要单独标明其输入权限。

## 5. 采集程序、同步和就绪标志

固定拓扑：

    电脑 ──Wi-Fi / SSH──→ Pi 4
                            ├──SPI + DRDY──→ ADXL355
                            ├──USB─────────→ IWR1843BOOST
                            ├──GPIO18──────→ IWR SYNC_IN
                            ├──GND─────────→ IWR GND
                            └──Ethernet────→ DCA1000EVM
    IWR1843BOOST ←──60-pin HD / LVDS──→ DCA1000EVM

当前记录的连接：Pi 物理 12/GPIO18 → IWR J6-9 SYNC_IN；Pi 物理 14/GND → IWR J6-4 GND；ADXL DRDY → Pi 物理 22/GPIO25；SPI0 CE0。实际照片可能有遮挡，不能按线色或历史描述保证实物接线绝对正确；需核对时看板卡方向、丝印与接线文档。

ADXL 与雷达保持两条原生 CLOCK_MONOTONIC 时间轴。算法按真实雷达时间区间预积分 ADXL，不要求样本一一配对或时间戳完全相同。GPIO SET 完成时间是触发参考，PCAP 是网络到达记录，都不等于真实 ADC 时刻；整数纳秒单位也不意味着纳秒测量精度。固定延迟、滤波延迟、抖动与漂移需分别处理。

这些状态是项目自定义契约，不是厂家自检结果或外部计量认证：

- `hardware_validated=false`：尚未声明完成项目要求的硬件/时间标定；不表示器件故障或接线错误。
- `algorithm_ready=true`：真实包满足当前算法运行所需的完整性、硬件触发及时间覆盖条件，仍可能有名义参数和标定警告。
- `fusion_ready=true`：满足更严格的时间、数值和几何标定契约；仅改一个布尔值不能得到可信标定。
- `simulation_ready=true`：明确合成包通过模拟契约。模拟仍保持其他实机就绪标志 false，通过显式 `--allow-simulation` 进入算法。

当前例程 `/Users/umep/thesis/capture_program/examples/capture_synchronized_hardware.toml`：`use_loopback=false`，GPIO18 100 Hz，`capture_frames=10`、`count=10`，ADXL 1000 Hz。CFG 的 9 ms 是雷达最小周期；外部触发实际 10 ms/100 Hz，不能依据嵌套 nominal frame rate 误报成 111.11 Hz。延长实测时同时核对采集帧数、触发数、覆盖和存储。

## 6. 磁浮轨道梁采集格式仿真

只使用 `/Users/umep/thesis/simulation/phase1/run_maglev_capture_simulation.py` 的专用流程进行本任务全链路仿真，核心在 `maglev_capture_simulator.py` 和 `capture_error_models.py`。

- 输入：`/Users/umep/thesis/datafile/20250320test12.tdms`，`卡3激光位移/3-4`，15.33–19.33 s，最多 4 s。
- 唯一实测输入是激光原始电压。`1 V = 1 mm` 为未验证换算；位移先限带 0.2–40 Hz，加速度由该位移 FFT 二阶导数形成。它不是一套实测雷达 + 实测 ADXL 联合记录。
- 雷达 100 Hz、ADXL 1000 Hz；4 s 对应 400 帧和 4000 样本。雷达模板用 TX0/TX2、4 RX、16 loops/32 physical chirps、8 虚拟通道、256 ADC 点，快时间采样率 5.209 MHz。
- 各 loop 按模型时刻生成，随后相干平均。有效观测中心为触发后 1.9071 ms，这是模型计算量；全部时间戳为理想合成。没有验证真实 GPIO/DRDY 抖动与设备时钟漂移；TX0→TX2 的帧内偏移没有建模/补偿。
- writer 是唯一随机传感器误差注入层。ADXL 当前为 25℃、假设已校准的 typical 噪声档：22.5 µg/√Hz、250 Hz 矩形 ENBW 工程近似、20bit 量化。偏置、尺度容差、交叉轴、非线性、温漂和 1.78 ms 滤波延迟未注入，不能说覆盖了厂商全部误差或最坏情况。
- 雷达注入一次复 AWGN 与 12bit I/Q 量化；SNR/目标几何属于场景假设，不能当厂家保证或由噪声系数单独推出。通道失配默认关闭，量化满量程按整包峰值归一化，尚不等于真实模拟增益链。DCA 不加模拟噪声，真实丢包另作完整性失败。
- 输出稳定的 radar/adxl `algorithm_input` 数组和 manifest，再用与真实包共用的离线算法。仿真不制造假的 PCAP、真实电边沿或 DRDY 证据。
- RMSE 的双方使用相同 0.20 s cold-start 均值作为相对零点；报告单位、评价频带、窗口和参考来源。不要把该动态相对指标外推成准静态或绝对位移精度。

## 7. 已有证据与当前缺口

真实硬件历史记录：`/Users/umep/thesis/capture_program/PI4_VALIDATION_2026-08-30.md`。

- ADXL 1 kHz、100/100 样本短采集通过。
- 软件时间戳联合采集 10 个雷达帧/8300 个 ADXL 样本通过；这不等于硬件触发门已通过。
- `use_loopback=false` 的 SYNC_IN 诊断采集 10 帧/9275 样本，包和时间覆盖完整。
- 开 GPIO24 回环时曾出现 10 脉冲/0 观测边沿，失败包没有发布为有效同步包。GPIO24 当前是可选诊断，不是普通算法运行硬条件。

已有磁浮示例：`/Users/umep/thesis/simulation/outputs/maglev_capture_demo/algorithm/phase1_result.json`。
它记录 `fixed_beta`、400 帧、4000 样本、5 个选中目标，RMSE 约 0.0005016 mm。它是既有仿真产物，部分字段早于当前实现；不能用来证明最新版测试已通过、adaptive β 校准成功或实机达到目标精度。任何聊天中提到但找不到配置/产物的其他数字先视为未复核。

当前具备安装后试采与离线处理的基础；尚无完整真实磁浮“ADC → 自动选点 → β → Kalman → 独立参考 RMSE”成功证据。还需核对安装轴、ADXL 偏置/尺度、传感器时间偏差、雷达距离/通道/阵列参数、真实目标质量、帧内运动效应，以及正式记录时长下的收包/存储稳定性。按目标误差预算评估各项影响，允许先做预实验，不把未验证硬说成已坏或已准。

旧文档有冲突：`next_chat_memory_prompt.md` 尾部称只做无硬件测试；顶层 README 称 GPIO24 必需；`docs/algorithm_chain_review.md` 仍有真实 ADC 解析未实现的旧文案。当前采集解析链已经存在。阅读这些文件时按具体代码和上述 bench 记录核对，不整份照搬旧结论。

## 8. 阅读顺序与代码入口

先读本文件，再按任务读取：

1. 论文设计：`/Users/umep/thesis/thesis_idea_overview.md`、`/Users/umep/thesis/innovation_points/multi_target_phase_kalman_fusion.md`、`/Users/umep/thesis/innovation_points/equivalent_conversion_factor_stability.md`。
2. 算法：`/Users/umep/thesis/simulation/phase1/README.md`、`beta_calibration.py`、`algorithm.py`、`config.py`（后三个均在该 phase1 目录）。
3. 独立处理入口：`/Users/umep/thesis/simulation/phase1/run_captured.py`、`capture_reader.py`、`fusion_adapter.py`。
4. 模拟入口：`/Users/umep/thesis/simulation/phase1/run_maglev_capture_simulation.py`、`maglev_capture_simulator.py`、`capture_error_models.py`、`measured_bridge.py`。
5. 采集部署：`/Users/umep/thesis/capture_program/PI4_CAPTURE.md`、`README.md`、`PI4_VALIDATION_2026-08-30.md` 及硬件 TOML。
6. 采集契约：`/Users/umep/thesis/capture_program/src/mmwavecapture/fusion_input.py`、`synchronized_input.py`、`fusion_calibration.py`、`algorithm_input.py`；编排在其 `capture/synchronized.py`。
7. 聚焦测试：`/Users/umep/thesis/tests/test_phase1_beta_calibration.py`、`test_phase1_capture_fusion_reader.py`、`test_phase1_run_captured.py`、`test_phase1_maglev_capture_simulator.py`；采集测试在 `/Users/umep/thesis/capture_program/tests/`。

涉及论文依据时再按 `/Users/umep/thesis/ref_papers/00_primary_references/README.md` 定位原文，不开局遍历全部 PDF。旧 `next_chat_memory_prompt.md` 用于追溯，不作为启动时必须重读的 754 行现行规格。

## 9. 最小复现命令

交接时 `/Users/umep/thesis/capture_program/.venv/bin/python` 存在，`.venv-sim/bin/python` 不存在。先检查现有解释器依赖，不要重复建环境。以下命令已经对照 CLI 参数，交接本轮未执行。

只生成一包数据，用同一包比较 fixed/adaptive；输出到新的临时目录，避免覆盖旧证据：

```bash
cd /Users/umep/thesis
task_run_dir="$(mktemp -d /tmp/thesis-handoff-XXXXXX)"

PYTHONPATH=/Users/umep/thesis/capture_program/src \
  /Users/umep/thesis/capture_program/.venv/bin/python \
  -m simulation.phase1.run_maglev_capture_simulation \
  --output "$task_run_dir/capture" --duration 4 --seed 2026 \
  --run-algorithm --method fixed_beta

PYTHONPATH=/Users/umep/thesis/capture_program/src \
  /Users/umep/thesis/capture_program/.venv/bin/python \
  -m simulation.phase1.run_captured "$task_run_dir/capture" \
  --allow-simulation --method adaptive_beta \
  --output "$task_run_dir/adaptive_beta.npz"
```

固定方法结果在 `$task_run_dir/capture/algorithm/phase1_result.npz` 与同名 JSON；adaptive 在指定 NPZ 和同名 JSON。CLI 默认 `fixed_beta`，要测试校准必须显式 `--method adaptive_beta`。上述 4 s 是当前固定磁浮波形的支持范围，不能直接把 `--duration` 改为任意长记录。

真实包使用相同 `run_captured`，路径换成真实 `synchronized` 目录，不加 `--allow-simulation`，按实际安装给出 `--adxl-axis` 和 `--adxl-sign`。`mmwavecapture-fusion-check` 可诊断真实包；`--require-calibrated` 要求严格标定契约，不要推测它也接受仿真的 opt-in 参数。

只核验 β / 捕获适配时，可选针对性测试：

```bash
cd /Users/umep/thesis
PYTHONPATH=/Users/umep/thesis/capture_program/src \
  /Users/umep/thesis/capture_program/.venv/bin/python -m pytest -q \
  /Users/umep/thesis/tests/test_phase1_beta_calibration.py \
  /Users/umep/thesis/tests/test_phase1_capture_fusion_reader.py \
  /Users/umep/thesis/tests/test_phase1_run_captured.py
```

模拟 writer 改动再选磁浮模拟测试；采集生命周期/契约改动再选相应 capture tests。不把以上示例测试集当作每次讨论都必须执行的动作。

## 10. 接手后的首轮行为与完成标准

先确认当前请求，再按上述阅读顺序核对工作区。若用户没有另给具体任务，默认围绕“磁浮轨道梁的可复现预实验与 β 有效性”继续：

1. 给出简短、带路径证据的现状：实现到了哪、历史验证到了哪、此刻最小缺口是什么。
2. 优先完成可离线复现的部分：同一磁浮包的 fixed/adaptive 比较、逐目标校准诊断和适用的聚焦测试。已有新鲜等价结果时复用，不无意义重复。
3. 对接受的目标检查独立证据，对拒绝的目标解释门控；若全部回退，区分激励不足、尺度不可辨识、实现错误或门限问题。不要为使“accepted”变真而放松判据。
4. 报告方法名、场景、输入来源、采样率、评价窗口/零点、标定模式、逐目标接受/回退、位移 RMSE、配置/seed 和产物路径。把内部 holdout 与独立实测验证分开表述。
5. 实机任务按用户请求执行。连接前读 `/Users/umep/thesis/.agents/skills/connect-pi4/SKILL.md`，按 MAC `88:a2:9e:d5:8f:89` 找当前 IP，用户为 `umep`，凭据按 skill 使用；不要硬编码历史 `10.81.201.181`。上次就绪审查未在当前 LAN 找到该 MAC，这只是当时状态，不能据此判断现在仍离线。本交接自身不要求你通电、启动采集或改变设备配置。
6. 交付代码时说明改了什么、为何这样改、实际跑了哪些聚焦测试、证据路径和剩余限制。每次宣称“完成”都限定到真实完成的层级，不把仿真闭环等同于实机计量验收。
