# 毫米波雷达与加速度计结构位移测量 Phase 1 方法与仿真汇报

> 2026-06-21 同步说明：本文档已按当前代码主方法口径刷新。论文主方法使用 `proposed_full_pipeline_calibrated`，即 calibrated `Q` + SNR-informed initial `R` + confidence-aware target-wise effective `R` + online kappa bootstrap。`proposed_full_pipeline` 仅作为未标定 `Q` 的 full-pipeline 消融结果保留。

> 本材料面向组会/阶段汇报，目标是说明当前倒挂式毫米波雷达 + 加速度计结构位移估计方案、算法链路、Phase 1 仿真验证设计和当前边界。本文档中的数值来自当前代码重新运行得到的 validation/extended validation；标准 validation gates 为 `23/23` 通过。若后续调整参数，应重新运行 `simulation.phase1.run_validation` 和 `simulation.phase1.run_extended_validation` 后再刷新表格。

## 1. 研究背景与问题定义

本章说明为什么“雷达安装在结构上”会使传统相位位移测量问题发生变化，以及本文 Phase 1 需要验证的核心问题。

桥梁、梁体和轨道结构的动态位移能够直接反映结构刚度、车辆荷载响应和服役状态。激光测振仪、激光位移计、LVDT 等高精度位移测量手段通常需要稳定基准或静态参考系，现场布设受桥下空间、视线遮挡、安装安全和长期维护条件限制。毫米波雷达具备非接触、高相位灵敏度和芯片化部署优势，但当雷达倒挂安装在结构测点并随结构一起振动时，雷达本身不再是静止参考点。

在倒挂式布置中，雷达朝向桥下或周围静止散射体。结构位移使雷达相位中心相对这些静止散射体运动，因此回波相位仍携带结构位移信息，但它不再是“固定雷达测振动目标”的简单场景。直接使用单目标、单 range-bin 相位法会遇到以下问题：

- 同一个 range bin 内可能包含多个角度不同的散射体，复数相量混合后相位不再代表单一物理 target。
- target 选择常依赖经验或最强反射，遇到低 SNR、遮挡、移动干扰或多径时不稳定。
- 原始相位被限制在 `(-pi, pi]`，毫米级位移就可能产生 phase wrapping。
- LoS 相位到结构主振动方向位移之间需要投影/转换系数，角度误差会直接放大位移误差。
- 加速度二次积分可作为动力学约束，但低频漂移、同步误差和标定误差也会影响直接位移参考。

本文 Phase 1 的目标是：利用结构上共址安装的毫米波雷达和加速度传感器，在没有外部静态参考系的条件下，估计结构单点竖向或主振动方向的相对位移。

## 2. 总体方案概述

本章给出方法主线。当前方案不是机械沿用单 range-bin 追踪，而是把参考目标定义提升到 range-angle 维度，并在结构主相位层进行多目标融合。

总体链路为：

```text
ADC 原始数据
-> Range-Angle Map
-> 2D peak detection
-> 同 rangeBin 近角度合并 / 远角度分离
-> 滑动窗口稳定性筛选
-> 频带一致性筛选
-> AoA cold start 得到 kappa 初值
-> 多 target 结构主相位 Kalman 融合
-> prediction-aided phase correction
-> confidence-aware target-wise R
-> online kappa bootstrap
-> 相对位移输出
```

本文与 Ma-family 方法的核心差异在状态定义。Ma-family baseline 的状态变量是单 target 的 LoS phase：

```text
x_k^Ma = [phi_k, dot_phi_k]^T
```

本文把状态变量改为结构振动方向主相位：

```text
x_k = [Theta_k, dotTheta_k]^T
Theta_k = 4*pi*delta_q_k/lambda
```

这样，加速度可以直接进入结构主相位系统模型；不同 target 的几何差异不再进入状态预测，而是进入观测矩阵。第 `i` 个 target 的观测写成：

```text
z_i,k = kappa_i * Theta_k + b_i + v_i,k
H_i = [kappa_i, 0]
```

因此，多 target 不再是“多个目标各自估计位移后再平均”，而是在结构主相位状态层进行统一融合。本文的 Ma-family baseline 是“基于公开论文公式与流程实现的 Ma-family baseline”，英文可表述为 “Ma-family baseline based on public formulas/procedures”；它不是 Ma 官方源码复现，也不是 Ma 原始实测数据 replay。

## 3. 完整算法流程图

本章给出两个图：一个用于解释完整数据流，一个用于汇报页快速展示模块关系。图中 `z_corr` 同时进入 Kalman update 和 online kappa bootstrap，这是当前闭环设计的关键。

### 3.1 完整数据流图

```mermaid
flowchart TD
    A["共址传感系统<br/>倒挂毫米波雷达 + 加速度计"] --> B["同步采集"]
    B --> C["雷达 ADC cube"]
    B --> D["加速度 a(k)"]

    subgraph Frontend["Range-Angle 前端"]
        C --> E["Range FFT"]
        E --> F["Angle FFT / DBF<br/>使用 spatial frequency"]
        F --> G["复数 Range-Angle Map<br/>Y_k(b,p)"]
        G --> H["幅值图 A_k(b,p)"]
        H --> I["2D peak detection"]
        I --> J["M 个 candidate targets"]
        J --> K["同 rangeBin 近角度合并<br/>小于 15 deg 视作等效 target"]
        K --> L["同 rangeBin 远角度分离<br/>保留不同 angle target"]
    end

    subgraph Screening["Target 稳定性与可用性筛选"]
        L --> M["滑动窗口 presence gate"]
        D --> N["加速度频谱<br/>结构振动频带 Omega(t)"]
        M --> O["band consistency gate"]
        N --> O
        O --> P["SNR / geometry / max target gates"]
        P --> Q["N 个 selected targets<br/>psi_i,k, theta_i, b_i, measured kappa_i"]
    end

    subgraph Fusion["结构主相位 Kalman 融合闭环"]
        Q --> R["AoA cold start<br/>kappa_i,0 = cos(theta_i)"]
        R --> S["H matrix<br/>H_i=[kappa_i,0]"]
        D --> T["系统模型预测<br/>x_k^- = A x_k-1 + B a_meas,k-1"]
        S --> U["target-wise LoS phase prediction<br/>phi_i,k^- = kappa_i Theta_k^- + b_i"]
        T --> U
        Q --> V["target-wise wrapped phase<br/>psi_i,k"]
        U --> W["prediction-aided phase correction"]
        V --> W
        W --> X["z_corr_i,k"]
        X --> Y["Kalman update<br/>结构主相位后验 Theta_k"]
        X --> Z["online kappa bootstrap<br/>短窗口 LS 更新 kappa_i"]
        Y --> Z
        Y --> AA["相对位移输出<br/>delta_q_hat = lambda Theta_hat/(4*pi)"]
        Y --> AB["innovation / residual"]
        AB --> AC["confidence-aware target-wise R<br/>base R + kappa uncertainty"]
        Z --> S
        AC --> Y
    end
```

### 3.2 汇报页简化模块图

```mermaid
flowchart LR
    S["Radar frontend<br/>ADC / Range FFT / Angle FFT"]
    T["Target screening<br/>2D peaks / merge / stability / band consistency"]
    K["Structural-main-phase Kalman fusion<br/>Theta state + acceleration prediction"]
    A["Online kappa/R adaptation<br/>bootstrap + confidence-aware R"]
    O["Displacement output<br/>relative delta_q"]

    S --> T --> K --> O
    K --> A --> K
```

## 4. 方法细节

本章说明各模块如何接在一起，以及为什么要在 Kalman 前筛选坏 target。

### 4.1 Range-Angle target 提取

仿真前端从 synthetic ADC cube 出发，经 Range FFT 和 Angle FFT/DBF 得到复数 range-angle map `Y_k(b,p)`。这里的 angle 轴按空间频率 `u=sin(theta)` 建立，而不是简单线性铺成 `linspace(-90,90)`。候选 target 通过二维局部峰检测获得，目标单元定义为：

```text
T = (b, C)
```

其中 `b` 是 range bin，`C` 是 angle bin cluster。同一 range bin 内角度差小于约 `15 deg` 的 peaks 合并为等效 target；同一 range bin 但角度差较大的 peaks 保留为不同 target。这是相对于 range-bin-only 方法的重要优势：当两个强散射体处在同一距离单元但 AoA 相差明显时，本文前端可以在 Kalman 前将它们分开，避免把混合相位当作一个稳定 LoS 相位。

### 4.2 Target 稳定性与可用性筛选

Target selection 阶段不做最终相位解缠，只输出复数 slow-time 序列、wrapped phase、AoA 初值和可用 mask。筛选包括：

- `presence gate`：候选 target 需要在滑动窗口内稳定出现。
- `band consistency gate`：target IQ 的 slow-time 变化要集中在加速度识别出的结构振动频带。
- `SNR gate`：低质量 target 不优先进入融合。
- `geometry gate`：过小投影系数或不可靠角度不会被过度信任。
- `max selected targets`：限制进入 Kalman 的 target 数量，保持观测集合稳定。

这些筛选在 Kalman 前完成，是为了避免坏 target 先进入状态更新再由滤波器“事后补救”。对进入 Kalman 的 target，后续还会由 confidence-aware target-wise `R` 动态调低不可靠观测权重。

### 4.3 结构主相位 Kalman 模型

状态定义为：

```text
x_k = [Theta_k, dotTheta_k]^T
Theta_k = 4*pi*delta_q_k/lambda
```

系统模型由加速度驱动：

```text
x_k^- = A x_{k-1}^+ + B a_meas,k-1
```

观测模型为：

```text
z_i,k = kappa_i Theta_k + b_i + v_i,k
H_i = [kappa_i, 0]
```

当前主方法采用 calibrated `Q`，即在候选过程噪声强度中用无真值 prediction innovation energy 选出 `q^\star`，在线阶段固定使用 `Q=q^\star Q_0`。每个 target 的基础 `R_i,k` 由 SNR-informed 初值、prediction innovation 和状态不确定性递推；同时将当前 `kappa_i` 的估计方差传播为有效观测噪声：

```text
R_eff_i,k = R_base_i,k + (Theta_pred^2 + P_ThetaTheta_pred) * sigma_kappa_i,k^2
```

这个 confidence-aware 项只用于支撑 AoA cold start 和 online kappa bootstrap：当转换系数尚未收敛时降低对应 target 的观测权重，bootstrap 收敛后该项自然回落。它不是本文单独包装的创新点。

原始相位是 wrapped phase：

```text
psi_i,k = angle(z_i(k)), psi_i,k in (-pi, pi]
```

Kalman 预测主相位后，先映射到 target LoS phase：

```text
phi_i,k^- = kappa_i Theta_k^- + b_i
```

再执行 prediction-aided phase correction：

```text
z_corr_i,k = psi_i,k + 2*pi*round((phi_i,k^- - psi_i,k)/(2*pi))
```

同一个 `z_corr_i,k` 同时用于 Kalman update 和 kappa bootstrap，这样避免了“先估转换系数需要连续相位，而连续相位又需要转换系数”的循环依赖。

### 4.4 与 Ma-family baseline 的对比

Ma-family baseline 的优势在于把加速度预测、相位分支校正和 Kalman 降噪统一在状态空间框架中。本文保留这一思想，但改变状态物理含义和观测组织方式：

| 对比项 | Ma-family baseline | 本文方法 |
|---|---|---|
| 状态相位 | 单 target LoS phase | 结构主相位 `Theta` |
| 加速度进入方式 | 需经转换系数映射到 LoS phase | 直接预测结构主相位 |
| 目标组织 | 单 target 或 range-bin 级候选 | range-angle target / angle cluster |
| 同 range 远角度目标 | 容易相干混合为一个 pseudo target | 在前端分离为不同 target |
| 转换系数 | 常依赖离线 beta 标定或 range-bin 拟合 | AoA cold start + online kappa bootstrap |
| 观测噪声 | 公开流程中以固定设置为主 | confidence-aware target-wise `R_eff` |

需要强调：`ma2026_reproduction` 是根据公开论文公式与流程实现的 Ma-family baseline，不是 Ma 官方源码复现；`ma_style_iterative_beta_range_bin` 是机制消融 baseline，不应写成 Ma 官方完整方法。

## 5. 仿真实验设计

本章说明数据从哪里来、仿真怎样构造、评价对象是什么。Phase 1 主要验证算法闭环可行性，不声称完成真实桥梁毫米波雷达实测。

### 5.1 仿真总体逻辑

仿真逻辑为：

```text
不同 scenario 生成 q_true(t)
-> 雷达物理相位模型生成 IQ / wrapped phase / synthetic ADC cube
-> 加速度观测生成 a_meas(t)
-> 各方法统一处理同一组观测
-> 与相对位移真值 delta_q(t) 比较
```

评价目标是相对位移：

```text
delta_q(t) = q(t) - mean(q over cold_start_window)
```

因此，Phase 1 关注动态相对位移恢复，不讨论绝对静态零位。

### 5.2 雷达观测仿真

每个 target 的结构主相位和 LoS 相位关系为：

```text
Theta(t) = 4*pi*q(t)/lambda
phi_i(t) = kappa_i*Theta(t) + b_i
IQ_i(t) = A_i exp(j phi_i(t)) + complex_noise
wrapped_phase_i(t) = angle(IQ_i(t))
```

full pipeline 进一步生成 synthetic ADC cube，并通过 Range FFT、Angle FFT/DBF 和 Range-Angle Map 前端提取候选 target。这样可以检查“ADC -> range-angle -> target selection -> Kalman”完整链路，而不是只在理想 target phase 上做后端滤波。

### 5.3 加速度观测仿真

普通合成场景使用真值位移求得 `a_true(t)`，再叠加噪声、偏置、漂移和同步误差，得到 `a_meas(t)`。

实桥半实测场景使用 TDMS 激光位移 `卡3激光位移/3-4` 作为真实桥梁波形来源：

```text
TDMS 激光位移 3-4
-> 事件窗口截取
-> 重采样到 100 Hz radar slow-time
-> 单位换算与 cold-start 相对零位
-> q_true(t)
-> 对另一份 0.2-30 Hz 滤波副本做二阶微分
-> 加 seeded accelerometer noise 得到 a_meas(t)
```

该场景是“实测位移驱动的半实测仿真”；激光位移 truth 默认不做带通或工频陷波，雷达观测仍由物理相位模型合成；原始 TDMS 加速度通道当前仅作为诊断与后续标定方向，不作为主验证输入。这不是完整实测毫米波雷达验证。

### 5.4 场景设计表

| scenario | 真实位移来源/波形 | target 数 | target angles | target SNR | 特殊退化条件 | 设计目的 |
|---|---|---:|---|---|---|---|
| `nominal_multifrequency` | 2/5/12 Hz 附近多频，普通合成场景峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | cold-start ramp：quiet -> 微振 -> 主响应 | 基准多目标多频振动 |
| `ma2023_balanced_good_targets` | 0.3/0.5/1.0 Hz，0.5/0.3/0.2 mm | 5 | 5/12/19/26/33 deg | 全 35 dB | range bins 31/33/35/42/48；quiet start 0.10 s | 模拟多个高质量 target 都可用的 Ma 2023 启发场景 |
| `strong_wrapping` | 2/5/12 Hz，强 wrapping profile，峰值约 5.0 mm | 5 | 10/25/40/55/70 deg | 30/25/20/15/10 dB | quiet -> 微振 -> ramp -> strong wrapping -> decay | 压测 prediction-aided phase correction |
| `aoa_error_bootstrap` | 默认多频峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | AoA 初值误差 10 deg | 验证 online kappa bootstrap |
| `target_snr_drop` | 默认多频峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0/1 在 1.6-3.4 s 降 25 dB | 验证 confidence-aware target-wise R |
| `target_dropout` | 默认多频峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0 在 1.6-3.4 s dropout | 验证目标缺失与多目标冗余 |
| `mixed_scatterer_rangebin` | 默认多频峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0 混合两散射体，kappa 0.95/0.35 | 验证同 range-bin 复合散射风险 |
| `same_range_far_angles` | 2/5/12 Hz，0.32/0.15/0.075 mm 分量，普通峰值约 1.5 mm | 4 | 0/45/25/65 deg | 36/36/32/32 dB | 4 个 target 均在 range bin 12，角度相差明显 | 验证 range-angle frontend 分离同 range 远角度目标 |
| `low_snr_multitarget` | 默认多频峰值约 1.5 mm | 5 | 10/25/40/55/70 deg | 12/10/8/6/4 dB | 整体低 SNR | 验证低 SNR 多目标融合 |
| `vehicle_event_nonstationary` | 非平稳车辆事件包络，quiet start 0.10 s | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | center 2.2 s，width 0.35 s | 验证非平稳事件与 target selection |
| `measured_bridge_point4_transverse` | TDMS 激光位移 3-4，15.33-19.33 s 事件窗 | 5 | 5/15/25/35/45 deg | 26/24/22/20/18 dB | laser truth 不滤波；derived acceleration 使用 0.2-30 Hz 滤波副本 | 验证真实桥梁位移波形下完整链路可运行 |

### 5.5 关键中间结果图

以下图均为 Markdown 绝对路径引用。图像已改用报告专用 PNG 版本，避免 SVG 在深色模式或部分 Markdown 环境中出现空白、白块或坐标轴缺失。

![车辆非平稳事件 Range-Angle 前端响应](/Users/umep/thesis/reports/numerical_simulation_assets_png/vehicle_event_nonstationary_range_angle_frame.png)

图 1 展示车辆非平稳事件场景中某帧二维 Range-Angle Map 的幅值热力图，并标注 full pipeline 选中的候选 target，用于说明 full pipeline 从 synthetic ADC / Range-Angle Map 中提取候选目标，而不是直接使用理想 target 相位。

![车辆非平稳事件 target selection 时间线](/Users/umep/thesis/reports/numerical_simulation_assets_png/vehicle_event_nonstationary_target_selection_timeline.png)

图 2 展示车辆事件中候选 target 的在线选择状态。fresh summary 显示该场景 full pipeline 选中 4 个 target，并排除了不可靠 target。

![车辆非平稳事件 selected vs all targets 位移对比](/Users/umep/thesis/reports/numerical_simulation_assets_png/vehicle_event_nonstationary_selected_vs_all_targets_displacement.png)

图 3 对比 all-target proposed 与 full pipeline 目标筛选后的位移结果。该图用于说明 target screening 不是装饰步骤，而是能降低坏 target 对状态的影响。

![强缠绕场景相位校正](/Users/umep/thesis/reports/numerical_simulation_assets_png/strong_wrapping_phase_correction.png)

图 4 展示 strong wrapping 场景中 wrapped phase、prediction-aided corrected phase 与真实 LoS phase 的关系，说明预测辅助分支选择如何在相位绕转时维持局部连续观测。

![target SNR drop 场景 confidence-aware R](/Users/umep/thesis/reports/numerical_simulation_assets_png/target_snr_drop_adaptive_r.png)

图 5 展示目标质量退化时 confidence-aware target-wise `R` 的变化。低质量 target 的基础观测噪声会随 innovation 增大；AoA cold start 阶段的 `kappa` 不确定性也会进入有效观测噪声，从而在 Kalman update 中降低不可靠 target 的权重。

![AoA error 场景 kappa bootstrap](/Users/umep/thesis/reports/numerical_simulation_assets_png/aoa_error_bootstrap_kappa_bootstrap.png)

图 6 展示 AoA 初值误差场景下 `kappa` 在线估计与真实参考值的关系。fresh gate 中 `aoa_bootstrap_kappa_median_relative_error_le_0p05` 通过，说明 bootstrap 能缓解 AoA 初值偏差。

![实测激光位移通道时域图](/Users/umep/thesis/reports/numerical_simulation_assets_png/laser_time_channels.png)

图 7 展示 TDMS 激光位移多通道时域响应，本文半实测场景选用 `卡3激光位移/3-4` 的事件窗口作为位移波形来源。

![实测激光位移通道频谱图](/Users/umep/thesis/reports/numerical_simulation_assets_png/laser_spectrum_channels.png)

图 8 展示激光通道频谱特性，用于支撑分析频带和工频陷波设置。

![实测激光位移通道动态相关性](/Users/umep/thesis/reports/numerical_simulation_assets_png/laser_dynamic_correlation.png)

图 9 展示激光通道动态成分相关性，说明所选桥梁响应波形具有通道一致性基础。

## 6. 实验结果与分析

本章使用 fresh validation 的 `metrics.csv`。报告中的 `ma2026_reproduction` 和 `measured_bridge_point4_transverse` 均来自新生成的 `/Users/umep/thesis/simulation/outputs/phase1_report_validation/metrics.csv`，不是旧 `phase1_validation/metrics.csv`。

### 6.1 方法对比表

| 方法 | 输入/假设 | 主要用途 | 解释边界 |
|---|---|---|---|
| `itoh_ls` | 单 target Itoh unwrap + LS/kappa 换算 | 传统相位解缠 baseline | 对噪声、dropout 和强异常相位敏感 |
| `single_target_ma_style` | 单 target acceleration-aided Kalman | Ma-style 单目标思想对比 | 状态为 LoS phase，不自然支持多 target |
| `ma2026_reproduction` | range-bin target/beta calibration + Ma2026 LoS Kalman | 正式 Ma-family baseline 对比 | 基于公开论文公式与流程实现，不是 Ma 官方源码复现 |
| `selected_aoa_fixed_kappa` | 前端筛选 target + AoA fixed kappa | 检查只筛选、不 bootstrap 的效果 | AoA 误差不能在线修正 |
| `proposed` | 所有 target + target-wise R + kappa bootstrap | 后端机制验证 | 不包含完整前端筛选、calibrated Q 和前端 target selection |
| `proposed_full_pipeline` | ADC/Range-Angle 前端 + target selection + proposed Kalman | 未标定 `Q` 的 full-pipeline 消融 | 不作为论文主结果 |
| `proposed_full_pipeline_calibrated` | ADC/Range-Angle 前端 + target selection + calibrated `Q` + confidence-aware `R_eff` + kappa bootstrap | Phase 1 主方法 | 当前仍是合成/半实测仿真链路 |

### 6.2 总体 RMSE 对比表

单位为 mm。数值越小表示相对位移估计误差越低。

| 场景 | `itoh_ls` | `single_target_ma_style` | `ma2026_reproduction` | `selected_aoa_fixed_kappa` | `proposed` | `proposed_full_pipeline` | `proposed_full_pipeline_calibrated` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `nominal_multifrequency` | 0.013564 | 0.086122 | 0.831404 | 0.053955 | 0.069999 | 0.068810 | 0.023270 |
| `measured_bridge_point4_transverse` | 0.011603 | 0.179898 | 0.211293 | 0.126551 | 0.151354 | 71.427434 | 0.142800 |
| `ma2023_balanced_good_targets` | 0.004245 | 0.037021 | 0.299403 | 0.002788 | 0.014885 | 0.003905 | 0.003032 |
| `strong_wrapping` | 8.514168 | 11.780095 | 0.375219 | 12.386050 | 0.393007 | 0.388011 | 0.090761 |
| `aoa_error_bootstrap` | 0.013564 | 0.086122 | 0.831404 | 0.053955 | 0.124290 | 0.068810 | 0.023215 |
| `target_snr_drop` | 3.570984 | 0.146961 | 0.831404 | 0.077267 | 0.074686 | 0.075821 | 0.069571 |
| `target_dropout` | 1.391564 | 5.235099 | 0.831404 | 0.061973 | 0.070474 | 0.071782 | 0.042468 |
| `mixed_scatterer_rangebin` | 1.124392 | 0.207994 | 0.242059 | 0.061924 | 0.071960 | 0.070455 | 0.024966 |
| `same_range_far_angles` | 0.003447 | 0.080351 | 0.343026 | 0.051385 | 0.067095 | 0.064288 | 0.019840 |
| `low_snr_multitarget` | 0.059941 | 0.102452 | 0.180231 | 0.073490 | 0.080155 | 0.077537 | 0.062440 |
| `vehicle_event_nonstationary` | 0.013183 | 0.056232 | 0.632018 | 0.029504 | 0.040004 | 0.036729 | 0.020384 |

### 6.3 关键场景 RMSE 表

| 场景 | 主要验证点 | `ma2026_reproduction` | `selected_aoa_fixed_kappa` | `proposed_full_pipeline_calibrated` | selected count | unwrap rate | 结论 |
|---|---|---:|---:|---:|---:|---:|---|
| `strong_wrapping` | prediction-aided phase correction | 0.375219 | 12.386050 | 0.090761 | 4 | 0.000000 | 预测辅助校正和 calibrated full pipeline 降低强 wrapping 下的相位分支风险 |
| `same_range_far_angles` | 同 range bin 远角度分离 | 0.343026 | 0.051385 | 0.019840 | 3 | 0.000000 | Range-Angle 前端将同 range 远角度目标分离，避免 range-bin-only 混合相位 |
| `target_snr_drop` | confidence-aware target-wise R | 0.831404 | 0.077267 | 0.069571 | 3 | 0.000000 | 退化 target 被动态降权，主状态不被坏观测长期污染 |
| `aoa_error_bootstrap` | online kappa bootstrap | 0.831404 | 0.053955 | 0.023215 | 4 | 0.000000 | AoA 初值只作为启动先验，bootstrap 后主方法误差更低 |
| `vehicle_event_nonstationary` | 非平稳车辆事件 + target selection | 0.632018 | 0.029504 | 0.020384 | 4 | 0.000000 | 冷启动、筛选和多目标 Kalman 在非平稳事件中保持可运行 |
| `measured_bridge_point4_transverse` | 实测位移驱动的半实测仿真 | 0.211293 | 0.126551 | 0.142800 | 5 | 0.000000 | 真实桥梁位移波形下完整算法链路可运行；该场景更适合作为可运行性和边界验证 |

### 6.4 关键场景分析

**strong_wrapping。** 该场景将真实位移峰值提高到约 5 mm，使 wrapped phase 多次跨越 `+-pi`。`proposed_full_pipeline_calibrated` 的 RMSE 为 0.090761 mm，unwrap error rate 为 0，低于 `ma2026_reproduction`、`single_target_ma_style` 和固定 AoA 多目标基线。该场景主要展示 prediction-aided phase correction 和 calibrated confidence-aware Kalman 在强 wrapping 下维持连续观测分支的能力。

**same_range_far_angles。** 该场景中 4 个主要 target 均位于同一 range bin，但 AoA 差异明显。range-bin-only 或 Ma-family 单 range-bin 思路会把不同 AoA 的相位混成一个 pseudo target；本文 Range-Angle frontend 在 Kalman 前保留不同 angle target。fresh gate 中 `same_range_far_angles_full_pipeline_beats_ma2026_reproduction` 通过，`proposed_full_pipeline_calibrated` RMSE 为 0.019840 mm。

**target_snr_drop。** target 0/1 在 1.6-3.4 s SNR 降低 25 dB。`itoh_ls` 出现大误差，`selected_aoa_fixed_kappa` 为 0.077267 mm，`proposed_full_pipeline_calibrated` 为 0.069571 mm。confidence-aware `R_eff` 使退化 target 和转换系数尚不稳定的 target 获得较低观测权重，降低坏观测对结构主相位状态的污染。

**aoa_error_bootstrap。** AoA 初值加入 10 deg 误差，用于检验转换系数自举。`selected_aoa_fixed_kappa` 固定几何初值，RMSE 为 0.053955 mm；`proposed_full_pipeline_calibrated` 通过 online kappa bootstrap 后为 0.023215 mm。该结果说明 AoA 更适合作为 cold start，而不是作为最终固定转换系数。

**vehicle_event_nonstationary。** 该场景包含 quiet start 和车辆事件非平稳响应。fresh summary 中 calibrated full pipeline selected count 为 4，unwrap error rate 为 0，RMSE 为 0.020384 mm。它验证了目标筛选、冷启动和多目标 Kalman 在非平稳事件下的闭环可运行性。

**measured_bridge_point4_transverse。** 该场景使用 TDMS 激光位移 3-4 作为真实桥梁响应波形，经过事件窗口、重采样和 cold-start 相对零位后得到 `q_true(t)`；加速度输入由滤波后的激光位移副本二阶微分并叠加 seeded noise 得到。`proposed_full_pipeline_calibrated` RMSE 为 0.142800 mm，unwrap error rate 为 0。该结果应被解释为真实桥梁位移波形驱动下的链路可运行性和边界检查；雷达观测仍由物理相位模型合成，不是完整实测毫米波雷达验证，也不应写成最终精度结论。

### 6.5 Extended validation 摘要

fresh extended validation 使用 seeds 2026-2030，覆盖 Monte Carlo、消融、AoA sensitivity 和 SNR sensitivity。摘要显示：

- `same_range_far_angles` 的 Monte Carlo 中，`proposed_full_pipeline_calibrated` 平均 RMSE 为 0.016271 mm，低于 `range_bin_only_mixed_phase` 的 0.269230 mm 和 `ma2026_reproduction` 的 0.477647 mm。
- `target_snr_drop` 的 Monte Carlo 中，`proposed_full_pipeline_calibrated` 平均 RMSE 为 0.056421 mm，低于 `selected_aoa_fixed_kappa` 的 0.086099 mm。
- AoA sensitivity 中，AoA 误差从 0 到 15 deg 时，`proposed_full_pipeline_calibrated` 维持约 0.023215 mm 的 RMSE；这反映当前前端选择、confidence-aware R 和 kappa bootstrap 对初值误差具有一定缓冲。
- SNR sensitivity 中，随着 SNR floor 从 4 dB 提升到 12 dB，`proposed_full_pipeline_calibrated` RMSE 从 0.062440 mm 降到 0.029349 mm。

这些结果支持 Phase 1 算法级可行性，但不替代真实 ADC 和现场同步验证。

## 7. 方案比选

本章把旧稿中的方案讨论整理为当前方案比选表。最终采用的是 `Range-Angle frontend + target selection + structural-main-phase Kalman + calibrated Q + confidence-aware R + online kappa bootstrap`。

| 方案 | 优点 | 局限 | 是否采用 | 原因 |
|---|---|---|---|---|
| 单 target Itoh unwrap + kappa 换算 | 实现最简单；物理含义清楚；适合作为传统相位解缠 baseline | 对强 wrapping、噪声、dropout 和相位跳变敏感；不利用加速度预测；固定 kappa 难以处理 AoA/安装误差 | 不作为主方案 | 用作 baseline，说明仅靠单 target unwrap 不足以覆盖退化场景 |
| Ma-style 单 target / range-bin beta 标定 + Kalman | 文献基线清晰；加速度辅助 Kalman 能统一相位预测、解缠和降噪 | 状态是单 target LoS phase；多 target 和同 range 多角度散射体不易自然融合；beta 标定对混合相位和加速度参考敏感 | 作为对比 baseline | 保留 Ma-family 思想对比，但不作为最终框架 |
| 多 target fixed kappa Kalman | 已具备结构主相位 + 多行观测矩阵骨架；可利用多 target 冗余 | 假设 kappa 已知且稳定；无法修正 AoA 和安装误差；坏 target 会长期污染观测 | 部分采用为结构骨架 | 多目标观测模型被采用，但 fixed kappa 不作为最终设置 |
| 多 target AoA fixed kappa Kalman | AoA 元数据能提供 cold start，避免先完整解缠再标定 beta 的死锁 | AoA 只是几何先验；真实阵列误差、旁瓣和安装姿态会影响 kappa；固定后不能收敛修正 | 作为初始化和 baseline | 本文保留 AoA cold start，但后续必须 online bootstrap |
| 本文 calibrated proposed full pipeline | 完整覆盖 ADC/Range-Angle 前端、目标筛选、结构主相位 Kalman 融合、prediction-aided phase correction、calibrated Q、confidence-aware R 和 online kappa bootstrap | 当前仍是 Phase 1 合成仿真与实测位移驱动的半实测仿真；真实 ADC、天线标定、同步和现场多径未完成 | 采用为主方案 | 与当前论文创新主线一致，并能解释同 range 远角度、target 退化和 AoA 初值误差等关键失败模式 |

## 8. 当前结论与后续工作

本章明确当前已经完成什么、还缺什么。结论保持客观，不把 Phase 1 结果扩展为部署级实测结论。

### 8.1 当前结论

- 已完成 Phase 1 算法级合成仿真与实测位移驱动的半实测仿真。
- 当前方法链路完整覆盖 frontend target extraction、selection、结构主相位 Kalman 融合、prediction-aided phase correction、calibrated Q、confidence-aware target-wise R、online kappa bootstrap 和相对位移输出。
- fresh validation 的 23 个 feasibility gates 全部通过。
- 仿真表明，在 same-range far-angle、target SNR drop、AoA 初值误差、多目标低 SNR、target dropout 和车辆非平稳事件等场景中，full pipeline 具有稳定表现。
- 实桥半实测场景表明，真实桥梁位移波形下完整链路可运行；但这不是完整实测毫米波雷达验证。

### 8.2 当前完成/未完成工作表

| 类别 | 当前状态 | 说明 |
|---|---|---|
| synthetic ADC / Range-Angle frontend | 已完成 | synthetic ADC cube、Range FFT、Angle FFT/DBF、Range-Angle Map 已接入 |
| 2D peak detection 与 target extraction | 已完成 | 包括二维局部峰、阈值筛选、同 rangeBin 近角度合并 |
| same rangeBin far-angle separation | 已完成 | 同 range 远角度 target 在 Kalman 前分离 |
| 滑动窗口稳定性与频带一致性筛选 | 已完成 | 使用 presence 和加速度频谱先验筛选可用 target |
| Ma-style / Ma2026 baseline | 已完成 Phase 1 合成复现 | 包含 Ma-style iterative beta 消融和 `ma2026_reproduction` |
| 结构主相位多 target Kalman | 已完成 | 使用 `H_i=[kappa_i,0]` 多行观测模型 |
| prediction-aided phase correction | 已完成 | 用结构主相位预测辅助 wrapped phase 分支选择 |
| confidence-aware target-wise R | 已完成 | 退化 target 动态降权，并在 AoA cold start 阶段传播 kappa 不确定性 |
| online kappa bootstrap | 已完成 | 同一 `z_corr` 用于 Kalman update 和 kappa 更新 |
| 实桥半实测场景 | 已完成 Phase 1 验证 | 使用 TDMS 激光位移驱动，雷达观测仍由物理相位模型合成 |
| 真实 IWR1843 ADC 文件解析 | 未完成 | 需要接入真实 raw ADC 文件格式、帧结构和通道组织 |
| 真实天线幅相标定 | 未完成 | 包括 RX/TX 通道幅相、阵列误差和角度轴校准 |
| 真实 TDM-MIMO 相位补偿 | 未完成 | 多 TX 时序导致的相位补偿尚未进入实测链路 |
| 雷达/激光/加速度时间同步 | 未完成 | 需要真实采集链路时间戳对齐和同步误差建模 |
| 真实加速度传感器标定 | 未完成 | 包括灵敏度、方向、bias、重力分量和测点对应关系 |
| 现场安装姿态 / geometry adapter 标定 | 未完成 | AoA 到结构主振动方向投影关系需现场标定 |
| 实桥 mmWave + laser + accelerometer 同步实测验证 | 未完成 | 需要真实雷达 ADC 与参考传感器同步采集后的端到端验证 |
| 多径和真实环境鲁棒性 | 未完成 | 包括桥下多径、旁瓣、相干散射体、移动干扰和长期稳定性 |

### 8.3 后续工作

后续应优先推进：

1. 真实 IWR1843 ADC 文件解析，明确 chirp/frame/channel 组织和数据校准流程。
2. 真实天线幅相标定与 TDM-MIMO 相位补偿，建立可信 AoA 轴。
3. 雷达、加速度、激光或位移参考的时间同步方案。
4. 加速度传感器灵敏度、安装方向和测点对应关系标定。
5. 实桥毫米波雷达 + 激光/加速度同步实测验证。
6. 真实桥下多径、遮挡、移动散射体和长期 target 失效/切换鲁棒性验证。

## 9. 本次报告使用的资料与结果文件

关键资料：

- `/Users/umep/thesis/thesis_idea_overview.md`
- `/Users/umep/thesis/idea/overall_processing_architecture.md`
- `/Users/umep/thesis/innovation_points/multi_target_phase_kalman_fusion.md`
- `/Users/umep/thesis/innovation_points/online_multi_target_selection.md`
- `/Users/umep/thesis/innovation_points/equivalent_conversion_factor_stability.md`
- `/Users/umep/thesis/docs/algorithm_chain_review.md`
- `/Users/umep/thesis/simulation/phase1/README.md`
- `/Users/umep/thesis/simulation/phase1/config.py`
- `/Users/umep/thesis/simulation/phase1/scenarios/`
- `/Users/umep/thesis/simulation/phase1/measured_bridge.py`
- `/Users/umep/thesis/simulation/phase1/algorithm.py`
- `/Users/umep/thesis/simulation/phase1/ma2026/`
- `/Users/umep/thesis/datafile/analysis/`

fresh validation 结果：

- `/Users/umep/thesis/simulation/outputs/phase1_report_validation/metrics.csv`
- `/Users/umep/thesis/simulation/outputs/phase1_report_validation/summary.md`
- `/Users/umep/thesis/simulation/outputs/phase1_report_validation/feasibility_gates.json`
- `/Users/umep/thesis/simulation/outputs/phase1_report_extended_validation/extended_summary.md`
- `/Users/umep/thesis/simulation/outputs/phase1_report_extended_validation/monte_carlo_summary.csv`
- `/Users/umep/thesis/simulation/outputs/phase1_report_extended_validation/ablation_summary.csv`
- `/Users/umep/thesis/simulation/outputs/phase1_report_extended_validation/sensitivity_aoa.csv`
- `/Users/umep/thesis/simulation/outputs/phase1_report_extended_validation/sensitivity_snr.csv`

本报告的边界：当前结论来自 Phase 1 合成仿真和实测位移驱动的半实测仿真；不把当前结果写成部署级系统结论，不把半实测结果写成实桥毫米波雷达现场验证，不声称复现 Ma 官方源码。
