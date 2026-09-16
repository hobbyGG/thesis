# 磁浮采集包复核与预实验准备（2026-09-08）

本轮完成同包 fixed/adaptive 离线比较、逐目标 β 诊断、公共时延门控修复和独立 400 帧采集配置。保护了原有 dirty worktree 和历史产物，未提交、未连接 Pi、未采集硬件数据。

## 证据层级与复现

输入复用 `simulation/outputs/maglev_capture_demo`，为历史生成的完整模拟包，seed=2026。本轮没有重新生成 writer：现有虚拟环境缺少 nptdms，安装请求未获批准。nptdms 仅用于读取 TDMS 生成模拟输入；已有稳定采集包的离线融合不需要它。

两种方法均由本轮代码运行，结果位于 `simulation/outputs/maglev_review_2026-09-08/{fixed_beta,adaptive_beta}.{npz,json}`；逐目标表为 `target_beta_diagnostics.csv`，来源及代码 SHA256 和同输入检查为 `evidence.json`。核对两方法的原始相位、AoA β、两条时间轴、ADXL 加速度和选点完全相同；adaptive 的 β 在全部帧保持冻结。

在项目根目录运行（输出使用新目录以避免覆盖）：

```bash
PYTHONPATH=capture_program/src capture_program/.venv/bin/python -m simulation.phase1.run_captured simulation/outputs/maglev_capture_demo --allow-simulation --method fixed_beta --output /tmp/maglev-review-new/fixed_beta.npz
PYTHONPATH=capture_program/src capture_program/.venv/bin/python -m simulation.phase1.run_captured simulation/outputs/maglev_capture_demo --allow-simulation --method adaptive_beta --output /tmp/maglev-review-new/adaptive_beta.npz
```

输入来源为 `datafile/20250320test12.tdms` 的 `卡3激光位移/3-4` 电压，源窗口 15.33–19.33 s，1 V=1 mm 换算未经验证，生成位移限带 0.2–40 Hz。雷达/加速度是合成数据，时间轴理想；100 Hz/1000 Hz，400 帧/4000 样本。评价使用全部400个雷达时刻（相对首观测中心0–3.99 s），以首0.20 s均值定义相对零点；不另选有利区间、不对估计误差事后滤波。雷达观测中心为模型触发后1.9071 ms。

## 本轮结果

|方法|位移 RMSE (mm)|逐目标接受|
|---|---:|---|
|fixed_beta|0.000501587560|不执行预校准|
|adaptive_beta|0.000326560363|4/5，非全部通过|

标定模式是 `simulation_nominal_unvalidated` → `aoa_anchored_relative`。7个候选中选中5个；另外2个未选中，不计入校准失败。两折各195帧，rank-1占比分别0.99999115和0.99980236；公共残余时延估计0.5 ms。该时延是模型数据上的拟合结果，不可直接写进硬件标定。

|target / range bin|AoA β|冻结 β|β相对误差：初始→最终 (%)|holdout改善|决定|
|---|---:|---:|---:|---:|---|
|0 / 8|1.004424|1.004424|+0.06016 → +0.06016|0.00%|回退：holdout_residual_not_improved|
|1 / 24|1.032796|1.035602|-0.23961 → +0.03148|5.35%|接受|
|2 / 40|1.112077|1.102611|+0.78839 → -0.06951|22.53%|接受|
|3 / 56|1.209486|1.220020|-0.92468 → -0.06182|14.85%|接受|
|4 / 72|1.438293|1.414688|+1.70268 → +0.03353|28.25%|接受|

β几何真值仅在估计完成后按选中目标唯一 range bin 与模拟 manifest 的5/15/25/35/45度匹配，使用 β=1/cosθ；没有用于选点、拟合、选Q或修改门限。四个接受目标的模型 β 误差均下降，提供了不同于位移RMSE的模拟评价证据。holdout仍为同一记录的内部条件检验，不是独立实测验证。target 0 两折ADXL相干性均约0.9999，但报告holdout改善为0，未过2%改善门；不是整组激励不足，也无需为它放宽门限。

relative 模式公共绝对尺度仍由 AoA 锚定；绝对ADXL候选的内部holdout改善为负，本轮没有因此临时切换模式。低RMSE和很高rank-1都不能验证实际增益、刚体运动假设、多径、转动或绝对β。

## 本轮修复

`simulation/phase1/beta_calibration.py` 的 raw静态拟合可能先返回坏目标 `non_positive_projection_candidate`，遮蔽公共时延边界/跨折不一致。原targetwise仅匹配首个reason，曾在真实模拟delay为17.5 ms、搜索边界±10 ms且第5目标反号时接受前4目标，尽管两折delay均卡在10 ms。

现对两折delay直接检查形状、有限性、搜索边界和跨折差，全局失败整组精确回退；保留单目标失败时其余目标可接受的行为。未放宽参数、未恢复Kalman后验反馈。实现与回归测试由独立专家分别负责。

## 进入真实预实验的最小缺口

新增 `capture_program/examples/capture_synchronized_preexperiment.toml`，与10帧冒烟模板分开，capture_frames=count=400，雷达100 Hz、ADXL1000 Hz、pre/post roll各2 s、GPIO18、use_loopback=false、hardware_validated=false。约4 s只是第一包的工程起点，两折都必须有足够激励且至少3个相干静止参考；240帧不是充分条件。已使用现有TOML parser核对其他参数未变。

400帧原始DCA载荷约50 MiB，lossless complex64 chirp cube另100 MiB，mean ADC cube约6.25 MiB，另有PCAP头和ADXL；当前preflight的3倍原始数据加1 GiB预留对应1174 MiB。采集编排已随触发数自动延长超时。Pi持续收包、存储和ADXL backlog仍需实际验证。

现场首包应记录：雷达和ADXL固定在梁上并随梁运动、参考物静止；安装朝向、结构轴、ADXL轴和正负号、参考物位置、激励起止与独立参考来源。先确认真实包完整及algorithm_ready，随后同包跑fixed/adaptive（不加--allow-simulation，按安装填写--adxl-axis/--adxl-sign），保留所有接受与回退结果。

本轮未执行现场命令。可从capture_program目录使用既有采集CLI和新配置；串口路径、接口、供电与存储在实际Pi上复核后执行。独立参考电压—位移换算、安装轴、ADXL偏置/尺度、雷达阵列/通道/距离以及时间偏差均需独立验证。GPIO24不作为普通预实验前置条件；hardware_validated=false不表示硬件损坏。严格fusion_ready及<0.01 mm计量验收仍未完成。

历史硬件证据仅为 `capture_program/PI4_VALIDATION_2026-08-30.md` 的短采集记录，本轮没有访问原Pi数据重验。

## 本轮实际验证

- `PYTHONPATH=capture_program/src capture_program/.venv/bin/python -m pytest -q tests/test_phase1_beta_calibration.py`：24 passed（含两种尺度模式×两种公共delay失败共4个新增回归子用例）。运行时移除新增门控模拟旧逻辑时，4个子用例均因错误接受目标而失败；磁盘源码未回退。
- `PYTHONPATH=capture_program/src capture_program/.venv/bin/python -m pytest -q tests/test_phase1_capture_fusion_reader.py tests/test_phase1_run_captured.py`：6 passed。
- 本轮完成已有包的两次真实算法调用及数组一致性/β冻结检查。未运行需要nptdms重新生成包的writer测试，也未跑全量测试或Monte Carlo。
