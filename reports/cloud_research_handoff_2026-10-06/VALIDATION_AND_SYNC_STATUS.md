# 验证与同步状态：本地研究交接

日期：2026-10-06（UTC）
来源：主线程 `01a0f052-59cf-7234-8860-2a971aaf403e` 传递的文本恢复，
加上本地现有报告、JSON、源码和 manifest 的只读核对。
保存性质：新增本地文档，不覆盖旧文档；没有复制云端原文件字节。

## 跨端同步状态

本轮已把收到的分析修订与研究状态保存到本地交接目录。
云端执行器及云端原文件当前尚不可读，因此无法核对文件清单、版本或逐文件字节。
**全量云端到本地同步尚未完成；本地已保存本次收到的文本更新。**
Git 分支/工作树对比只反映本地仓库状态，不能证明跨端文件同步完成。
本轮不调用 Library、不修改权限或凭据、不 commit/push、不运行新实验。

## 严格 paired 验证要求

- 每个 semantic block 预先生成同一 motion/noise realization，各几何条件及
  比较路由共享该 realization；保存 motion/noise 数组 hash 与请求/实际检测几何。
  同一个 seed 名称不能替代共享实际数组及其身份记录。
- 估计器只读 IQ、声明的 metadata 和合法 causal prefix；truth 仅在估计、
  路由与接受/拒识决策完成后用于 scoring。
- 预先冻结全部路由、阈值、评分窗口、warmup 策略和失败判定；不能根据测试
  truth 改阈值、选择路由或进行符号/偏移拟合。
- 比较路由统一评分窗口及物理参考，单列 warmup 延迟。报告 coverage、
  accepted 失败率、successful yield，以及拒识样本的独立路由反事实误差。
  对没有可用反事实输出的 guard failure 保留缺失/失败标记。
- 若描述阈值为 `RMSE > 0.01 mm`，明确 accepted 失败率分母是接受数，
  successful yield 分母是总样本数；该描述阈值不能自动成为部署精度承诺。

## P1：旧失败记录与配对缺口

本地原报告及 JSON 重新核对得到：

| 记录 | 本地报告 | 经核对的状态 |
|---|---|---|
| 几何邻域旧记录 | [REPORT.md](../../experiments/innovation1_geometry_neighborhood_2026-10-05/REPORT.md)；[neighborhood_results.json](../../experiments/innovation1_geometry_neighborhood_2026-10-05/neighborhood_results.json) | 37 个 semantic rows，13 个接受，5 个接受输出 `RMSE > 0.01 mm`；coverage `13/37`，accepted 失败率 `5/13 = 38.46%`，该描述阈值下 successful yield `8/37 = 21.62%`。 |
| seed213 | [CONSERVATIVE_REPORT.md](../../experiments/innovation1_selector_check_2026-10-04/CONSERVATIVE_REPORT.md) | 单 seed、六场景 smoke；接受 `3/6`，接受中的描述高误差 `0/3`，不能扩展为边界验证完成。 |
| 严格配对设计 | [PROTOCOL.md](../../experiments/innovation1_boundary_pairing_protocol_2026-10-05/PROTOCOL.md)；[BLOCKER.json](../../experiments/innovation1_boundary_pairing_protocol_2026-10-05/BLOCKER.json) | `blocked_strict_pairing`：旧 geometry cells 各自重新抽 motion phase/noise，未共享 common random numbers。 |

旧记录未严格配对会限制几何差异的因果解释，但不会消除已经观察到的接受失败。
一个峰不自动保证 merge 安全；小 projection gap 不自动构成应拒识的充分理由。
新的分析修订与候选门控见 [ANALYTICAL_REVISION.md](ANALYTICAL_REVISION.md)，
它们尚未验证，不能追溯性地替换旧结果。

## P2：新增本地证据与已有报告的数值口径

### 新增 4101–4103 合成 calibration/test 记录

目录：[profile_ls_synthetic_heldout_2026-10-06](../../experiments/profile_ls_synthetic_heldout_2026-10-06/)。
已只读核对 [REPORT.md](../../experiments/profile_ls_synthetic_heldout_2026-10-06/REPORT.md)、
[results.json](../../experiments/profile_ls_synthetic_heldout_2026-10-06/results.json)、
[PROTOCOL.md](../../experiments/profile_ls_synthetic_heldout_2026-10-06/PROTOCOL.md)、
源码和 manifest。

- seeds `4101,4102,4103`，12 route rows；JSON 中 `12/12` finite/amplitude guard 通过。
- calibration `0–127`，test `128–255`；共享 paired scoring `148–255`（108 帧），
  warm prefix `128–147`（20 帧）；角度在 calibration 后冻结。
- Bartlett `0.25°` 网格；profile-LS 在 Bartlett ±`1.5°` 范围以 `0.01°`
  候选步长搜索，属于有界细网格 profile residual refinement。
- 原报告的 `+0.000324 mm`（舍入）是**两路 RMSE 中位数之差**：
  `median(profile)-median(Bartlett)`。从 JSON 逐 seed 重算，
  cold paired RMSE 差（profile − Bartlett）分别为
  `+0.000139953368,+0.000260402347,+0.000323883915 mm`；
  **逐 seed 配对差的中位数**是 `+0.000260402347 mm`。
  两种汇总不是同一统计量，严格 paired 报告必须区分；本轮没有改原报告。
- 这组结果只显示有界 off-grid 角度变化；未显示一致的位移 RMSE 改善。
  不同 seed 的角度/beta/array 条件也不同，不能以跨 seed 差异单独识别某个因素效应。

### 新增 4201–4203 matched factorial 记录

目录：[profile_ls_factorial_diagnostic_2026-10-06](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/)。
已只读核对 [REPORT.md](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/REPORT.md)、
[results.json](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/results.json)、
[PROTOCOL.md](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/PROTOCOL.md)、
源码和 manifest。

- 三个 matched seeds，三个 factors、两 estimator、两 initialization，共 36 rows；
  JSON 中 `36/36` guard 通过，全部使用 `148–255` 评分窗口。
- 源码每个 seed 先生成 `q/noise`，再跨三个 factors 复用同一数组。
  这支持代码层面的 common-random-number 配对；结果仍没有保存实现后
  motion/noise 数组的 hash，严格配对身份审计还应补全。
- JSON 逐 seed 差重新汇总的中位数（profile − Bartlett，cold paired）为：

| factor | 配对 RMSE 差中位数（mm） | profile 改善的 seeds |
|---|---:|---:|
| offgrid_only | +0.000284062919 | 1/3 |
| offgrid_beta | +0.000561573932 | 0/3 |
| offgrid_array | +0.000230262349 | 1/3 |

这些数值与原 factorial 报告一致。更精确的 AoA 在当前小样本单源阵列模型中
尚未证明位移 RMSE 提升。不得扩展为同距离多源可辨识、LVDT 精度、现场性能或
完整 covariance/GLS 验证。

### 初始化和因果性边界

两组新实验的 cold/warm 在共同评分帧重基准后指标相同，不能据此声称存在
状态初始化获益。它们使用离线相位解缠，源码 amplitude guard 读取完整 test
段的最小幅度；这尚未完成逐前缀因果接受/拒识或持续在线状态估计验证。
源码的几何估计仅读 calibration IQ、truth 位于 scoring 部分，支持所声明的
calibration fence；文档字段本身仍不能替代运行时隔离验证。

持续在线自校准尚未完成；calibration 后冻结属于初始化策略。
本交接统一 `beta = 1/cos(theta)` 为几何位移换算因子，将相位增益另记
`g = 4*pi*cos(theta)/lambda`。该记号需适用几何与符号明确，避免此前同符号混用。

## 原始归档仍缺失

截至本次本地检查，目录
`experiments/same_range_geometry_reference_diagnostic/heldout_20261003/` 仍不存在。
历史 seeds400–402 的原始 runner、manifest、输入、冻结协议和结果尚未恢复。
4101–4103 与 factorial 均在 manifest 中声明 `historical_400_402_recovery=false`，
不能描述成历史 400–402 复现。

[RECOVERY_SEARCH_2026-10-05.md](../../experiments/profile_ls_init_pairing_2026-10-04/RECOVERY_SEARCH_2026-10-05.md)
保留先前本地恢复搜索记录。v22 线索仅用于定位：大小 `3723687` 字节，
预期 SHA-256 `f692ad87a6258b680ad8d5873ac7d653c45bf64e42adb9df557118c55d545c1b`；
它不是已经保存到本地的归档 hash。

## 本地最新实验目录索引

| 本地目录 | 内容/状态 |
|---|---|
| `experiments/innovation1_claim_audit_2026-10-04/` | 旧 same-range 证据与声明边界整理。 |
| `experiments/innovation1_selector_check_2026-10-04/` | seed212/213 routing smoke 与原报告。 |
| `experiments/innovation1_geometry_neighborhood_2026-10-05/` | 旧 37 rows、13 接受、5 接受失败；未严格配对。 |
| `experiments/innovation1_boundary_pairing_protocol_2026-10-05/` | 严格配对设计及 blocker。 |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/` | 新 4101–4103 合成记录。 |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/` | 新 4201–4203 合成 matched-factorial 记录。 |
| `experiments/profile_ls_init_pairing_2026-10-04/` | 历史 400–402 恢复缺口、blocked protocol 与恢复搜索。 |
| `experiments/cross_review_profile_ls_covariance_2026-10-03/` | 文献补充、angle/beta 与 initialization pilots；各自有范围限定。 |
| `experiments/same_range_merge_mechanism_v2/` | 已有 bounded same-range synthetic 机制记录。 |
| `experiments/online_geometry_loop_scratch/` | 已有在线/gauge scratch diagnostics；不代表持续自校准已完成。 |

## 本次本地来源 SHA-256 核验

以下记录在写入交接文档之前从本地现存文件计算。P2 manifest 所列全部 source、
protocol、results 与 dependency hash 均匹配；factorial manifest 另列 report hash，
也匹配。4101–4103 的 manifest 未列 report hash，本次补记实际值；
匹配仅证明本地文件身份一致，不证明云端版本一致或运行期独立性。

| 本地文件 | SHA-256 |
|---|---|
| `experiments/innovation1_geometry_neighborhood_2026-10-05/REPORT.md` | `6c4cf3822b794dd34d03749b0e670b4f471c5482ce16ab545d1fd278482c2ba2` |
| `experiments/innovation1_geometry_neighborhood_2026-10-05/neighborhood_results.json` | `02b608294dbd436493562ff6ba445c582e6a3033615da9466778b382a90a11d4` |
| `experiments/innovation1_selector_check_2026-10-04/CONSERVATIVE_REPORT.md` | `e13891c52704c53eaa56e072bf768162a48817ff5f2610fc6f6e4906e70df152` |
| `experiments/innovation1_boundary_pairing_protocol_2026-10-05/BLOCKER.json` | `21b7cc389810c1fc68d27f80f9e62496a36f9deef0be3212898fadaf138566fc` |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/PROTOCOL.md` | `c301bc68572b7434489e2cca8b2dc03ee78b9a7d6bb50379142e0d970069f424` |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/run_experiment.py` | `0b48a1f335f3802ac6e5cd69e3b0530e2f34328c1d8babfe4056891b1fddd940` |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/results.json` | `bf946085b385a42e56997eb13c445fbc29a1f60be649d1247d6c19cb755573ff` |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/REPORT.md` | `a99f989568439e4abfdf975836583d5d42a884c7aeffa00c8b085adf483fe7d9` |
| `experiments/profile_ls_synthetic_heldout_2026-10-06/MANIFEST.json` | `c82a06fc973f57e34de85967e238388b05592978c63d3bbcebe37ed95e9afa7f` |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/PROTOCOL.md` | `16256e744db5aaec88216f79b7972955cb59babd621fceed4767896d6a56ce32` |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/run_factorial.py` | `58912266c6929c6a36ff721accf45643522f1899d87eee7d2aa9e87007c45162` |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/results.json` | `c802ef4caa6a97af99713d294fa6b3ac0e6017b7a294306ab2bb12d9f440e1f6` |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/REPORT.md` | `230c40e6b1d9a7bff9d3c1a1b293cf5e554caea7da70359813c91c44590f7930` |
| `experiments/profile_ls_factorial_diagnostic_2026-10-06/MANIFEST.json` | `ef2bf271bd46a807cd27ad57f80592a9c7235b5975fb6c0ef937f7dfb1938a4c` |
| `experiments/profile_ls_init_pairing_2026-10-04/RECOVERY_SEARCH_2026-10-05.md` | `8f10fa59cf4d057df7de194eaf890385f0f4ce79c95cbc9088ba2c294928eccf` |

本次仅新增本交接目录中的两份 Markdown 文档，并进行读回/字节一致性/SHA-256
核验。没有改算法、改旧报告或运行实验；本地 Git HEAD 保持
`5de28dbaa7328bfc2b9aef7a1737092906d43b03`。
