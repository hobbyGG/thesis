# 创新点 2 收尾：calibration-only AoA/几何误差诊断与边界分析

日期：2026-10-07（UTC）
范围：profile-LS、AoA 和几何换算的隔离诊断；不修改算法代码和实验数据。
状态：可作为论文结果/限制段落的本地交接稿。

## 结论先行

当前证据支持一个有边界的结论：在八阵元半波长 ULA、单源、固定噪声和固定
合成位移的 calibration/test 协议中，校准段 profile-LS 能把 Bartlett 的角度
量化误差压低，但这没有转化成一致的位移 RMSE 改善。4101--4103 的三组 paired
test 窗口中，profile-LS 的位移 RMSE 差（profile-LS − Bartlett）分别为
`+0.000139953`、`+0.000260402` 和 `+0.000323884 mm`，三组均为正；中位数
为 `+0.000260402 mm`。因此可以写“角度误差下降但位移 RMSE 未改善”，不能写成
“更精确的 AoA 提升了位移精度”。

4201--4203 的 matched factorial 给出了更强的因素诊断。三个因素的 profile-LS
角度绝对误差都低于 Bartlett，但三个因素的 paired RMSE 中位差仍全部为正：
`offgrid_only +0.000284063 mm`、`offgrid_beta +0.000561574 mm`、
`offgrid_array +0.000230262 mm`。这组结果把结论限定为“在当前小样本合成模型
和下游换算中未观察到一致的位移收益”，而不是“profile-LS 无效”。

## 可直接写入论文的结果段落

> 在 calibration-only 的合成诊断中，profile-LS 只使用帧 0--127 的阵列 IQ，
> 在 Bartlett 角度附近的有限区间内进行 off-grid 细化，并在帧 128--255 冻结
> 角度后完成测试段相位提取。对 4101--4103 三个独立种子，Bartlett 的角度绝对
> 误差为 0.12°、0.08° 和 0.04°，profile-LS 降为 0°、0.03° 和 0.03°；然而
> 共享帧 148--255 的 paired displacement RMSE 并未下降，profile-LS 相对
> Bartlett 的差值为 +0.000140、+0.000260 和 +0.000324 mm。为分离误差来源，
> 4201--4203 matched factorial 在复用同一 motion/noise realization 的条件下
> 改变 beta 或阵元位置失配。profile-LS 在 offgrid-only、offgrid-beta 和
> offgrid-array 条件下的角度绝对误差由 0.12° 分别降至 0°、0° 和 0.02°，
> 但 RMSE 中位差仍为 +0.000284、+0.000562 和 +0.000230 mm。因此，角度量化误差
> 不是当前位移误差的唯一主导项，AoA 细化本身不能作为位移精度改善的充分证据。

如果论文需要英文结果段落，可使用：

> In the bounded calibration-only synthetic diagnostic, profile-LS used only the
> calibration IQ and reduced the absolute Bartlett angle error from 0.12°, 0.08°,
> and 0.04° to 0°, 0.03°, and 0.03° for seeds 4101--4103. This angular
> improvement did not yield a displacement-RMSE
> reduction on the shared frames 148--255: the paired profile-LS minus Bartlett
> differences were +0.000140, +0.000260, and +0.000324 mm. In a three-block
> common-random-number factorial diagnostic, the profile-LS angle error was lower
> in all factors, whereas the median RMSE differences remained positive
> (+0.000284, +0.000562, and +0.000230 mm for offgrid-only, offgrid-beta, and
> offgrid-array). The evidence therefore supports an angle-diagnostic observation,
> not a general displacement-accuracy gain.

The exact seed values are listed in the table below; the 4103 value is 0.03° after
rounding. Prefer the table when exact reporting is needed.

## 数值证据

RMSE 单位为 mm；角度误差是绝对值。所有 4101--4103 的 12 个 route rows
以及 4201--4203 的 36 个 factorial rows 都通过 finite/amplitude guard。

### 4101--4103 独立校准/测试记录

| seed | true angle | Bartlett / profile-LS 角度绝对误差 | paired RMSE Bartlett / profile-LS | profile − Bartlett |
|---:|---:|---:|---:|---:|
| 4101 | 17.37° | 0.12° / 0.00° | 0.002364527 / 0.002504480 | +0.000139953 |
| 4102 | 17.83° | 0.08° / 0.03° | 0.012621832 / 0.012882234 | +0.000260402 |
| 4103 | 18.21° | 0.04° / 0.03° | 0.011936250 / 0.012260134 | +0.000323884 |

这里的 paired 窗口统一为测试帧 148--255（108 帧）；4101--4103 的 cold 与
warm 在该窗口重基准后给出相同的确定性指标，因此不能从这组记录宣称 warm
initialization 带来收益。

### 4201--4203 matched factorial

| factor | 角度绝对误差 Bartlett / profile-LS | conversion ratio Bartlett / profile-LS | RMSE 中位数 Bartlett / profile-LS | Δ RMSE（profile − Bartlett） | profile 改善 seeds |
|---|---:|---:|---:|---:|---:|
| offgrid_only | 0.12° / 0.00° | 0.999347 / 1.000000 | 0.002335557 / 0.002619620 | +0.000284063 | 1/3 |
| offgrid_beta | 0.12° / 0.00° | 1.014338 / 1.015000 | 0.014185214 / 0.014746788 | +0.000561574 | 0/3 |
| offgrid_array | 0.12° / 0.02° | 0.999347 / 0.999891 | 0.002334989 / 0.002565251 | +0.000230262 | 1/3 |

`conversion ratio = beta_scale * cos(theta_true) / cos(theta_hat)`。在
offgrid-beta 条件下，profile-LS 消除了角度网格误差，但仍保留约 +1.5% 的
尺度残差；这说明角度细化没有估计或校正 beta 失配。该比值是诊断量，不是
beta 校准结果。

## 代码和校准边界核对

隔离实验的 calibration-only 逻辑在源码中是明确的：

- [run_experiment.py](../../experiments/profile_ls_synthetic_heldout_2026-10-06/run_experiment.py)
  先取 `cal = iq[:CAL_FRAMES]`，用该数组调用 `bartlett_angle` 或
  `profile_angle`，随后才进入 `estimate_test`；profile 搜索范围是
  Bartlett ±1.5°、步长 0.01°。
- [run_factorial.py](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/run_factorial.py)
  每个 seed 先生成一次 q/noise，再让三个 factor 复用同一 realization，
  支持 factor 内的 paired 差分。当前 JSON 没有保存实现后 q/noise 数组 hash，
  所以这是代码层 common-random-number 证据，而不是完整的数组身份审计。
- [frontend.py](../../algorithm/frontend.py) 以
  `beta = 1 / abs(cos(angle))` 形成目标级几何换算；这是假设阵列、安装
  方向、结构运动方向和角度符号约定均适用的直接映射，不是独立实测 beta。
- 隔离 profile-LS 结果不能直接改写为“当前生产前端已实现 calibration-only”。
  [io.py](../../algorithm/io.py) 的 `build_algorithm_inputs` 对完整
  `capture.adc_cube` 做 Range--Angle 处理、目标检测和角度细化；已有
  [ra_fence_audit.json](../../spatial_recovery_rebuilt/ra_fence_audit/ra_fence_audit.json)
  的 test-only 扰动保持帧 0--199 不变，却改变了候选、range、angle、beta 和
  selected indices。当前生产路径因此仍是“全记录构建几何”的状态。论文应把
  4101--4203 称为 calibration-only 诊断路线；若要宣称端到端 calibration-only
  部署，必须先把生产前端改成显式的校准前缀/冻结接口并重新验证。

## 为什么角度误差下降仍可能没有位移收益

隔离 runner 的下游位移估计为

$$
\hat q(t)=\operatorname{unwrap}(\angle(\mathbf a(\hat\theta)^H
\mathbf z(t)))\frac{\lambda}{4\pi\cos(\hat\theta)}.
$$

生成器的相位则含有未建模的尺度项：

$$
\phi(t)=\frac{4\pi}{\lambda}q(t)\,
\mathrm{beta\_scale}\cos(\theta_{true}).
$$

因此，profile-LS 只优化校准段的单源空间残差，不优化测试段 displacement
RMSE，也没有自由度去估计阵元位置或 beta scale。即使 `theta_hat` 更接近
`theta_true`，以下误差仍会保留或变化：

1. **尺度失配：** offgrid-beta 的 +1.5% beta scale 直接进入 displacement
   比例；角度修正不能消除它。
2. **阵列模型失配：** offgrid-array 使用真实阵元位置生成 IQ，但估计仍使用
   nominal positions；角度的剩余偏差、波束投影和相位噪声会共同影响 RMSE。
3. **有限快拍和噪声：** profile 目标是校准快拍上的复残差；更接近真实角度
   不等于测试段相位噪声、幅度起伏或解缠误差必然更小。offgrid-only 的
   profile angle 已为 0°，但三 seed 中仍只有 1/3 的 RMSE 改善，正是该边界
   的直接反例。
4. **观测模型范围：** 该实验是单源、单 range-cell、静态阵列和固定目标集合；
   它没有测试同距离多源、相干散射、旁瓣/距离泄漏、range migration、多径、
   目标重关联或时间变化安装姿态。

因此，正确的因果表述是“profile-LS 诊断了并降低了有限角度网格误差，但在本
下游模型中尚未证明位移 RMSE 获益”，而不是“角度误差是位移误差的唯一来源”。

## 可保留和应删除的论文表述

可保留：

- “在固定八阵元 ULA 的 bounded synthetic protocol 中，calibration-only
  profile-LS 降低了 off-grid AoA 的量化误差。”
- “在 3-seed matched factorial 中，角度误差改善没有带来一致的 displacement
  RMSE 改善；因此 AoA refinement 与位移精度之间存在受几何尺度和阵列失配
  影响的边界。”
- “结果是有限机制诊断，不是现场精度或 LVDT 等价性验证。”

应删除或改写：

- “profile-LS 提高了位移精度”“更小 AoA 误差必然降低 RMSE”；
- “在线校准已在生产前端完成”或“完整流程严格 calibration-only”；
- “beta 已由 AoA 准确标定”“可推广到任意阵列/安装方向”；
- “已恢复/复现历史 400--402 profile-LS 记录”。当前目录
  `experiments/same_range_geometry_reference_diagnostic/heldout_20261003/`
  仍不存在，4101--4103 和 4201--4203 是独立的新合成记录；
- “现场、LVDT、0.01 mm 或普适角度阈值”结论。

## 数据、范围和复核入口

主要证据：

- [4101--4103 报告](../../experiments/profile_ls_synthetic_heldout_2026-10-06/REPORT.md)、
  [协议](../../experiments/profile_ls_synthetic_heldout_2026-10-06/PROTOCOL.md)、
  [结果 JSON](../../experiments/profile_ls_synthetic_heldout_2026-10-06/results.json)；
- [4201--4203 factorial 报告](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/REPORT.md)、
  [协议](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/PROTOCOL.md)、
  [结果 JSON](../../experiments/profile_ls_factorial_diagnostic_2026-10-06/results.json)；
- [本地验证与同步状态](VALIDATION_AND_SYNC_STATUS.md)；
- [生产前端 fence audit](../../spatial_recovery_rebuilt/ra_fence_audit/ra_fence_audit.json)。

关键 source/protocol/result SHA-256 已在对应 manifest 中记录；本次复核的摘要为：

| record | protocol | source | results |
|---|---|---|---|
| 4101--4103 | `c301bc68572b7434489e2cca8b2dc03ee78b9a7d6bb50379142e0d970069f424` | `0b48a1f335f3802ac6e5cd69e3b0530e2f34328c1d8babfe4056891b1fddd940` | `bf946085b385a42e56997eb13c445fbc29a1f60be649d1247d6c19cb755573ff` |
| 4201--4203 | `16256e744db5aaec88216f79b7972955cb59babd621fceed4767896d6a56ce32` | `58912266c6929c6a36ff721accf45643522f1899d87eee7d2aa9e87007c45162` | `c802ef4caa6a97af99713d294fa6b3ac0e6017b7a294306ab2bb12d9f440e1f6` |

本报告只新增这一份 Markdown 交接文件；没有重跑会覆写 `results.json` 的实验，
没有改动生产算法，也没有 push。
