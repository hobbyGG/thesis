# 倒挂式毫米波雷达结构位移测量：直接 AoA 主线数据流

> 版本：Direct-AoA Phase 1，2026-09-14
>
> 当前主方案已经撤掉 Kalman 后的动态 beta 修正和 Kalman 前独立 beta 预校准。系统先从雷达阵列空间相位直接估计 target 角度，再按几何关系得到固定 beta，最后进行结构主相位位移估计。旧 beta 反馈方案保存在 [overall_processing_architecture_legacy_beta.md](</Users/umep/thesis/archive/2026-09-14-pre-direct-aoa/legacy_docs/idea/overall_processing_architecture_legacy_beta.md>)，只用于历史复现和消融。

## 1. 研究对象与主线定义

雷达和加速度计共址安装在结构测点处。雷达观测周围相对静止的环境散射体；结构运动改变雷达与散射体之间的传播距离，因此回波 LoS 相位包含结构位移信息。对第 (i) 个 target：

$$
\Theta(k)=\frac{4\pi}{\lambda}q(k),
\qquad
\phi_i^{\mathrm{LOS}}(k)=\frac{\Theta(k)}{\beta_i}+b_i.
$$

其中：

- \(q(k)\)：结构测点沿目标方向的结构主位移；
- \(\Theta(k)\)：结构主相位；
- \(\phi_i^{\mathrm{LOS}}(k)\)：第 (i) 个 target 的 LoS 相位；
- \(b_i\)：target 固定相位偏置；
- (\beta_i)：LoS 相位到结构主相位的几何转换系数；
- \(\lambda\)：雷达波长。

当前直接 AoA 主线的关键变换是：

$$
\hat\theta_i
\longrightarrow
\hat\beta_i=\frac{1}{|\cos\hat\theta_i|}
\longrightarrow
\text{固定 }\hat\beta_i\text{ 的结构位移估计}.
$$

\(\hat\beta_i\) 只由前端直接测得的 target 角度产生，不由位移结果反向更新。

## 2. 总体数据流图

```mehrmaid
flowchart TD
    CFG["Phase1Config / 采集配置<br/>采样率、载频、ADC参数、target场景、随机种子"]
    CFG --> SIM["仿真数据生成层"]
    CFG --> ALGCFG["算法参数层<br/>角度方法、搜索区、Q/R、门限"]

    subgraph TRUTH["A. 结构真值分支：只用于生成和最终评价"]
        Q["结构位移真值 q(k)"]
        V["速度 v(k)"]
        ACC_T["加速度真值 a_true(k)"]
        ANG_T["target真实角度 θ_i"]
        BETA_T["真实 beta_i"]
        Q --> V
        V --> ACC_T
    end
    SIM --> TRUTH

    subgraph MEAS["B. 观测仿真分支"]
        RADAR_IDEAL["理想 target-level 雷达观测<br/>true LoS phase / wrapped phase / beta<br/>仅作 oracle、基线和评价参考"]
        ADC["合成 ADC cube<br/>frame × virtual antenna × ADC sample"]
        ACC_M["加速度计观测<br/>a_meas(k)=a_true(k)+noise/bias/drift"]
        TRUTH --> RADAR_IDEAL
        TRUTH --> ADC
        ACC_T --> ACC_M
    end

    subgraph RF["C. 雷达前端"]
        RFFT["Range FFT<br/>沿快时间提取距离单元"]
        AFFT["Angle-FFT / 几何 DBF<br/>生成粗略 Range-Angle Map"]
        MAP["复数 Range-Angle Map<br/>Y(k,b,p)"]
        SNAP["目标距离单元多通道复快拍<br/>X_b ∈ C^(M×N)"]
        ADC --> RFFT
        RFFT --> AFFT --> MAP
        RFFT --> SNAP
    end

    subgraph DET["D. 候选 target 检测与质量筛选"]
        PEAK["2D幅值峰检测<br/>candidate (range bin, angle bin)"]
        MERGE["同距离近角峰合并<br/>远角峰保留为不同候选"]
        QUALITY["目标质量筛选<br/>IQ有效性、SNR、可用mask、加速度相关性"]
        MAP --> PEAK --> MERGE --> QUALITY
        ACC_M --> QUALITY
    end

    subgraph AOA["E. 直接 target AoA 估计：粗—精—精修"]
        COARSE["粗筛：FFT候选角度<br/>只确定局部搜索中心"]
        MUSIC["精筛：局部 MUSIC<br/>协方差 + 噪声子空间 + 局部谱峰"]
        ML["精修：局部 ML/NLS<br/>联合变量投影，连续优化 θ"]
        STEER["固定最终导向矢量<br/>重建完整 target slow-time IQ"]
        SNAP --> MUSIC
        MERGE --> COARSE
        COARSE --> MUSIC --> ML --> STEER
        QUALITY --> ML
    end

    subgraph GEO["F. 几何转换：只由直接角度决定"]
        THETA["直接角度输出 θ_hat_i"]
        BETA["beta_hat_i = 1 / |cos(theta_hat_i)|<br/>冻结，不接受Kalman反馈"]
        ML --> THETA --> BETA
    end

    subgraph FUSION["G. 固定 beta 的结构主相位估计"]
        INPUT["RadarAlgorithmInput<br/>wrapped phase、fixed beta、available mask、selected indices"]
        BIAS["冷启动偏置估计 b_i"]
        PRED["加速度驱动状态预测<br/>x_k^- = A x_(k-1)^+ + B a_meas(k-1)"]
        CORR["预测辅助相位分支校正<br/>LoS预测与wrapped phase对齐"]
        OBS["结构方向观测<br/>y_i,k = beta_hat_i(phi_i,k^LOS,corr - b_i)"]
        KF["结构主相位 Kalman update<br/>x_k=[Theta_k, Theta_dot_k]^T"]
        QR["Q批量选择 + target-wise R更新<br/>不更新 beta"]
        OUT["结构主相位 / 相对位移<br/>q_hat = lambda Theta_hat/(4 pi)"]
        STEER --> INPUT
        BETA --> INPUT
        QUALITY --> INPUT
        INPUT --> BIAS --> CORR
        INPUT --> CORR
        ACC_M --> PRED
        KF --> PRED
        PRED --> CORR --> OBS --> KF --> OUT
        KF --> QR
        QR --> KF
    end

    subgraph EVAL["H. 评价与报告：真值只在这里进入"]
        ANG_E["AoA角度误差<br/>theta_hat - theta_true"]
        BETA_E["beta相对误差"]
        DISP_E["位移RMSE / MAE / 最大误差"]
        WRAP_E["相位分支错误率"]
        TRUTH --> ANG_E
        TRUTH --> BETA_E
        TRUTH --> DISP_E
        TRUTH --> WRAP_E
        THETA --> ANG_E
        BETA --> BETA_E
        OUT --> DISP_E
        CORR --> WRAP_E
    end

    RADAR_IDEAL -. "evaluation/reference only" .-> EVAL
```

图中的实线是算法数据流，虚线是评价参考流。真值分支不能进入 target AoA、target selection 或固定 beta Kalman 的算法输入。

## 3. 仿真数据生成层

### 3.1 结构真值

入口为 [truth.py](/Users/umep/thesis/simulation/phase1/truth.py) 的 `generate_truth_signal()`。输出：

```text
t[N]                 slow-time时间轴
q_m[N]               结构位移真值
v_mps[N]             结构速度真值
a_mps2[N]            结构加速度真值
frequencies_hz      结构频率分量
amplitudes_m        各分量幅值
```

场景可以生成普通多频、强相位缠绕、同距离多目标、AoA 偏差和 SNR 下降等工况。

### 3.2 目标几何和相位真值

`build_default_scatterers()` 为每个散射体建立：

```text
range_m
angle_deg
amplitude
snr_db
phase_bias_rad
beta = 1 / |cos(angle_deg)|
range_bin_index
```

`simulate_adc_cube()` 对第 (i) 个 target 生成：

$$
\begin{aligned}
\Theta(k)&=\frac{4\pi q(k)}{\lambda},\\
\phi_i^{\mathrm{LOS}}(k)&=\frac{\Theta(k)}{\beta_i}+b_i,\\
s_i(k)&=A_i e^{j\phi_i^{\mathrm{LOS}}(k)}+n_i(k),\\
a_i(m)&=e^{j2\pi p_m\sin\theta_i},\\
r_i(n)&=e^{j2\pi f_{r,i}n/N_r}.
\end{aligned}
$$

ADC 中的 target 回波为：

$$
X_i(k,m,n)=s_i(k)a_i(m)r_i(n).
$$

所有 target 的 (X_i) 叠加后得到 ADC cube，并按场景加入噪声、目标退化和 dropout。

### 3.3 两条雷达观测分支

仿真同时生成两类对象：

| 对象 | 用途 | 是否进入当前直接 AoA 主算法 |
|---|---|---|
| `RadarObservation` | 理想 target-level LoS/wrapped phase、真实 beta、oracle 对照 | 否，只有评价和指定基线使用 |
| `ADCCubeObservation` | 物理形状 ADC 数据，包含距离和阵元空间相位 | 是，经前端处理后使用 |

这一划分防止算法直接读取 `true_los_phase_rad`、`true beta` 或 `q_true`。

### 3.4 加速度观测

普通仿真中：

$$
a_{\mathrm{meas}}(k)=a_{\mathrm{true}}(k)+n_a(k)+b_a+d_a(k).
$$

加速度观测有两个用途：

1. target quality / selection：辅助判断目标是否与结构振动相关；
2. 固定 beta Kalman：作为结构主相位的动力学输入。

加速度不参与 `estimate_local_music()` 或 `estimate_local_music_ml()` 的阵列角度拟合。

## 4. 雷达前端与候选 target

入口为 [frontend.py](/Users/umep/thesis/simulation/phase1/frontend.py) 和 [scenario_inputs.py](/Users/umep/thesis/simulation/phase1/scenario_inputs.py)。

### 4.1 Range FFT

ADC cube 的快时间轴做距离 FFT：

```text
adc_cube:       [N_frame, M_virtual_rx, N_adc]
range_fft:      [N_frame, M_virtual_rx, N_range]
range_by_rx:    [N_frame, N_range, M_virtual_rx]
```

Phase1 默认参数为 77 GHz、6 MHz ADC、256 samples/chirp、60 us chirp、4 chirps/frame；slow-time/Kalman 采样率单独由 `sample_rate_hz` 定义。

### 4.2 Angle-FFT / 几何 DBF

默认旧前端使用 Angle-FFT 得到粗角度轴。若配置了阵元坐标，则前端使用几何导向矢量进行 DBF。当前 1-D 方位 Phase1 使用 8 个方位虚拟阵元等效模型；真实 IWR1843 ADC 接入时必须核对实际虚拟阵元坐标和方位/俯仰通道映射。

输出：

```text
range_angle_cube[N_frame, N_range, N_angle]
angle_axis_deg[N_angle]
range_snapshots[N_frame, N_range, M_virtual_rx]
array_positions_wavelengths[M_virtual_rx]
```

### 4.3 候选检测、合并和筛选

1. 在冷启动参考帧的 Range-Angle 幅值图上检测二维局部峰；
2. 将候选峰表示为 `(range_bin, angle_bin)`；
3. 同一距离单元内近角峰可合并，明显远角峰保留为不同 target；
4. 对每个候选提取完整 slow-time IQ 和 wrapped phase；
5. 根据 IQ 有效性、SNR、质量分数、可用 mask 以及与加速度观测的相关性选择进入位移算法的 target。

候选 target 的数据结构为：

```text
range_bins[T]
angle_bins[T]
range_m[T]
angle_deg[T]
slow_time[T, N_frame]
wrapped_phase_rad[T, N_frame]
available_mask[T, N_frame]
```

当前 selection 的输出只决定哪些目标进入后端，不改变 target 的阵列空间角度估计模型。

## 5. 直接 AoA：粗筛、精筛、精修

入口为 [angle_estimation.py](/Users/umep/thesis/simulation/phase1/angle_estimation.py) 的 `estimate_local_music()` 或 `estimate_local_music_ml()`。

### 5.1 第一段：FFT 粗筛

Angle-FFT 只提供：

- 目标候选数量；
- 每个候选的初始角度；
- 每个候选的距离单元；
- 后续局部搜索中心。

它不作为最终角度值，也不负责补偿阵元幅相误差。

### 5.2 第二段：局部 MUSIC 精筛

对于同一距离单元的多通道复快拍：

$$
X_b=[x_b(1),x_b(2),\ldots,x_b(L)]
$$

计算样本协方差：

$$
R_b=\frac{1}{L}X_bX_b^H.
$$

对 (R_b) 特征分解，得到噪声子空间 (E_n)，在 FFT 粗角度附近计算：

$$
P_{\mathrm{MUSIC}}(u)=
\frac{1}{a^H(u)E_nE_n^Ha(u)},
\qquad u=\sin\theta.
$$

当前实现只在局部空间频率区间内搜索，并用谱峰邻域二次插值得到连续初值。

### 5.3 第三段：局部 ML/NLS 精修

对于单个或同一距离单元内的多个目标，使用校准导向矢量：

$$
Y=A(\boldsymbol{\theta})C+N,
\qquad
A=[a(\theta_1),\ldots,a(\theta_K)].
$$

给定角度后，先用最小二乘求线性复幅度 (C)，再优化角度：

$$
\hat{\boldsymbol{\theta}}
=
\arg\min_{\boldsymbol{\theta}}
\left\|Y-A(\boldsymbol{\theta})\hat C\right\|_F^2.
$$

这一步是连续角度拟合，不是神经网络机器学习。`max_snapshots` 只限制拟合窗口，不截断最终慢时间输出。

### 5.4 最终角度输出与慢时间重建

角度估计输出：

```text
angle_deg[T]
angle_estimation_method
angle_estimation_diagnostics[T]
```

以最终角度构造固定导向矩阵，对全部有效时间快拍做投影，得到：

```text
source_slow_time[T, N_frame]
wrapped_phase_rad[T, N_frame]
available_mask[T, N_frame]
```

固定导向矩阵重建是为了避免逐帧选择不同角度 bin 带来的相位跳变。

### 5.5 AoA 质量门

如果出现以下情况，不能把结果宣传为高精度角度：

- FFT 粗峰落在局部搜索区之外；
- 有效快拍数不足；
- 目标数大于阵元可辨识数量；
- MUSIC 协方差非有限或条件数过差；
- ML/NLS 残差过大；
- 同距离多目标的候选关联不稳定。

这些诊断应在报告中单独统计，不能只报告成功案例的角度 RMSE。

## 6. 直接角度到固定 beta

前端完成角度估计后执行：

$$
\hat\beta_i=\frac{1}{|\cos\hat\theta_i|}.
$$

`FrontendTargetObservation.measured_beta` 和 `RadarAlgorithmInput.measured_beta` 都来自该映射。`direct_aoa_fixed_beta` 的不变量是：

```text
beta_hat(k) = beta_hat(0) = frontend angle-derived beta
beta_update_enabled = False
beta_source = frontend_direct_aoa
```

因此不存在：

```text
Kalman posterior -> beta fit -> beta rewrite -> same Kalman posterior
```

旧 `adaptive_beta`、`proposed_full_pipeline_beta_confidence` 和旧 bootstrap 诊断仍保留为显式 legacy/ablation。

## 7. 固定 beta 的结构主相位 Kalman

### 7.1 算法可见输入

[radar.py](/Users/umep/thesis/simulation/phase1/radar.py) 中的 `RadarAlgorithmInput` 只接收：

```text
measured_beta[T]
wrapped_phase_rad[T, N]
available_mask[T, N]
selected_indices
calibration_indices
initial_r[T]
selection_scores[T]
extra["angle_deg"]
```

不接收：

```text
q_true, true_beta, true_los_phase, a_true, scatterer truth labels
```

### 7.2 冷启动和预测

状态为：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot\Theta_k
\end{bmatrix}.
$$

系统预测为：

$$
\mathbf{x}_k^-=
A\mathbf{x}_{k-1}^+
+B\frac{4\pi}{\lambda}a_{\mathrm{meas}}(k-1).
$$

冷启动阶段仅估计各 target 的固定相位偏置 (b_i) 和初始状态，不估计 beta。

### 7.3 预测辅助相位校正

用固定 beta 将结构主相位预测映射回各 target 的 LoS 相位：

$$
\hat\phi_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat\Theta_k^-}{\hat\beta_i}+b_i.
$$

对于原始 wrapped phase：

$$
\psi_{i,k}=\operatorname{angle}(z_i(k)),
$$

选择与预测最接近的 (2\pi) 分支：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}
=
\psi_{i,k}
+2\pi\operatorname{round}
\left(
\frac{\hat\phi_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}}{2\pi}
\right).
$$

### 7.4 多 target 结构方向观测

每个 target 的 LoS 校正相位转到结构主相位坐标：

$$
y_{i,k}
=
\hat\beta_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

观测模型为：

$$
y_{i,k}=\Theta_k+e_{i,k},
\qquad H_i=[1,0].
$$

多个 target 共享同一结构主相位状态，因此后端融合不是把多个独立位移结果简单平均，而是在共同状态层进行更新。

### 7.5 Q、R 和输出

当前 direct 方法仍然执行：

- 在候选过程噪声 (Q) 中用 innovation energy 选择 (Q^\star)；
- 根据 target SNR 和初始质量设置 (R_{i,0})；
- 根据 posterior residual 和质量门更新 target-wise (R_{i,k})；
- 记录 innovation、相位校正结果、(R) 历史和 target quality。

这些是结构位移滤波参数，不是 beta 后续处理。

输出：

```text
q_hat_m[N]
theta_hat_rad[N]
theta_dot_hat_radps[N]
los_corrected_phase_rad[T, N]
beta_hat[T]
r_theta_history[T, N]
innovation_rad[T, N]
```

位移为：

$$
\hat q_k=\frac{\lambda}{4\pi}\hat\Theta_k.
$$

## 8. 评价与对照分支

### 8.1 评价顺序

在 [evaluation.py](/Users/umep/thesis/simulation/phase1/evaluation.py) 中：

```text
frontend estimated angle vs scatterer true angle
frontend beta vs scatterer true beta
Kalman displacement vs cold-start-relative q_true
corrected phase vs true LoS phase
```

评价阶段可以访问真值，但真值不得回流到算法对象。

### 8.2 当前默认方法

[method_registry.py](/Users/umep/thesis/simulation/phase1/method_registry.py) 当前默认注册：

| 方法 | 作用 |
|---|---|
| `oracle` | 理想参考，不作为工程算法结论 |
| `range_bin_itoh` | 传统距离单元相位基线 |
| `ma2026_reproduction` | 公开公式流程基线 |
| `angle_fft_local_music` | 共同 Angle-FFT 粗筛 + 局部 MUSIC，固定 beta |
| `angle_fft_local_music_ml` | 共同 Angle-FFT 粗筛 + 局部 MUSIC + ML/NLS，固定 beta；当前主方法 |

旧方法：

```text
proposed_full_pipeline_aoa_fixed_beta
proposed_full_pipeline_beta_confidence
adaptive_beta
```

只作为显式 ablation/legacy，不进入默认主结论。

### 8.3 当前成对比较命令

```bash
python3 -m simulation.phase1.run_direct_aoa_comparison
```

输出：

```text
simulation/outputs/direct_aoa_comparison.csv
simulation/outputs/direct_aoa_angle_comparison.csv
```

前者比较两种方法的位移 RMSE 和角度 RMSE，后者比较逐场景、逐 target 的角度误差。两种方法使用完全相同的 Angle-FFT 粗筛；唯一变量是局部 MUSIC 后是否继续进行 ML/NLS 精修。

## 9. 数据边界和当前缺口

| 环节 | 当前 Phase 1 状态 | 实验阶段还需补充 |
|---|---|---|
| 结构真值 | 合成多频/非平稳/强 wrapping | 实测结构响应统计 |
| ADC | 合成 ADC cube | 真实 IWR1843 DCA1000 ADC 解析和同步 |
| 阵列 | 8 方位虚拟阵元等效模型 | IWR1843 真实虚拟阵元坐标、幅相和姿态标定 |
| AoA | 局部 MUSIC + ML/NLS | 角反射器转台标定、阵元误差、多径验证 |
| beta | 直接由 AoA 映射并冻结 | 独立几何测量确认 \(\theta\) 定义和安装姿态 |
| 加速度 | 带噪真值或半实测驱动 | 原生时间戳、轴向、比例因子和同步验证 |
| Kalman | 固定 beta、加速度预测、Q/R处理 | 真实 radar/ADXL 联合采集验证 |
| 评价 | 角度、beta、位移、分支错误 | 激光/LVDT 对照和重复试验 |

最重要的物理限制是：阵列固定通道相位偏差与角度相位斜率存在可辨识性混淆。没有独立幅相/几何标定时，MUSIC 或 ML/NLS 可以有很好的重复性，但不能自动保证绝对 AoA 精度。

## 10. 与旧 beta 动态方案的关系

```mehrmaid
flowchart LR
    OLD["旧方案<br/>AoA beta初值"] --> OLD_KF["LoS phase Kalman"]
    OLD_KF --> OLD_FIT["用位移/加速度结果拟合 beta"]
    OLD_FIT --> OLD_KF

    NEW["新方案<br/>ADC阵列空间快拍"] --> NEW_AOA["直接 AoA<br/>FFT→局部MUSIC→ML/NLS"]
    NEW_AOA --> NEW_BETA["几何 beta 冻结"]
    NEW_BETA --> NEW_KF["结构主相位 Kalman"]

    OLD -. "legacy/ablation" .-> CMP["比较角度误差、beta误差、位移RMSE"]
    NEW -. "main" .-> CMP
```

旧方案试图利用结构运动结果补偿 AoA 引起的 beta 误差，因此 beta 与位移状态存在反馈耦合。新方案先完成空间角度估计，再把 beta 作为固定几何输入，研究重点转为：

1. 直接 AoA 是否比 Angle-FFT 更准确；
2. 角度误差是否满足 beta/REMS 要求；
3. 短时 1.5 s 响应中，局部 MUSIC-ML 是否稳定；
4. 同距离多目标和低 SNR 是否造成角度估计失败。

当前研究不再把“Kalman 在线修正 beta”作为主创新或主结果。
