# 倒挂式毫米波雷达结构位移估计整体处理架构

## 1. 系统目标

本文研究的传感系统由毫米波雷达和加速度传感器共址安装在梁体测点处，雷达朝向正下方。与激光测振仪、LVDT 等需要静态参考系或固定安装基准的位移传感器不同，倒挂式毫米波雷达随结构共同运动，并利用周围近似静止的环境散射体作为参考目标，从而在不额外布设外部静态参考点的条件下估计结构振动方向位移。

系统的核心任务可以表述为：

$$
\text{从雷达观测到的多个环境静止散射 target 中，恢复梁体测点在结构振动方向上的连续位移。}
$$

由于自然环境中的参考 target 数量多、角度和反射强度不同、同一 rangeBin 内可能存在多个散射体，并且雷达原始相位存在 $2\pi$ 缠绕，本文将整体处理流程拆分为三个层级：

$$
\text{参考 target 提取}
\rightarrow
\text{AoA 几何初始化与独立预校准}
\rightarrow
\text{结构主相位 Kalman 融合}.
$$

其中，target 提取阶段不依赖 Kalman 后验；AoA 几何关系先给出每个 target 的转换系数初值。随后在 Kalman 启动前，仅用原始雷达相位、AoA 和原生 ADXL 数据进行一次独立静态预校准：双时间折从多 target 相位的 rank-1 结构估计逐目标相对投影，ADXL 回归给出动力学相干、绝对尺度与公共时延候选。未验证或缺失验证标志的记录固定采用原始 AoA 锚定相对模式，`validated` 记录固定采用 ADXL 绝对模式，不依据 holdout 临时选支路；每折只用本折训练段选择 ADXL 相干参考，对侧折仅验证。时间轴、激励、公共时延、参考数量或 rank-1 共同运动门失败时整组回退；相位连续性、相干性、跨折稳定性、边界和条件 holdout 等逐目标门只回退对应 target。接受值与回退值一起冻结，再从第 0 帧运行正式 Kalman。在线仅保留 prediction-aided phase correction 与 target-wise $R_i$ 更新，不从 Kalman 后验反向更新 $\beta_i$。rank-1 仅验证共同波形；投影解释仍要求所有参考 target 观察同一刚体测点/结构自由度。

## 2. 总体数据流

### 2.1 详细数据流图组

#### 2.1.1 Target 提取与筛选流程

```mehrmaid
flowchart TD
    A("梁上共址安装<br/>毫米波雷达 + 加速度计<br/>雷达朝向正下方") --> B("同步采集")
    B --> C("毫米波雷达 ADC 原始数据")
    B --> D("同步加速度<br/>$a(k)$")

    C --> E("Range FFT + Angle FFT / DBF<br/>复数 range-angle map: $Y_k(b,p)$")
    E --> F("幅值图<br/>$A_k(b,p)=|Y_k(b,p)|$")
    F --> G("二维峰值检测<br/>候选 range-angle peaks<br/>候选数量 $M$")

    G --> G1("候选 peak / target 1")
    G --> G2("候选 peak / target 2")
    G --> GM("候选 peak / target $M$")

    G1 --> H("同 rangeBin 角度合并<br/>$|\theta_i-\theta_j|\lt15^\circ$ 视为等效 target")
    G2 --> H
    GM --> H
    H --> I("target 跟踪与滑动窗口维护<br/>$\mathcal{W}_t=[t-W+1,t]$")
    I --> J("出现率稳定性确认<br/>$R_T(t)\ge \tau_R$")

    D --> K("加速度频谱分析<br/>结构振动频带 $\Omega(t)$")
    J --> L("target 频带一致性筛选<br/>$G_T(t)\ge \tau_G$")
    K --> L

    L --> ASET("筛选后可用参考 target 集合<br/>$\mathcal{A}_k=\{T_1,T_2,\ldots,T_m\}$<br/>$m\le M$")
    ASET --> T1("Target 1<br/>$z_1(k),\ \psi_{1,k},\ \theta_1,\ b_1$")
    ASET --> T2("Target 2<br/>$z_2(k),\ \psi_{2,k},\ \theta_2,\ b_2$")
    ASET --> Tm("Target $m$<br/>$z_m(k),\ \psi_{m,k},\ \theta_m,\ b_m$")
```

#### 2.1.2 独立预校准后的结构主相位 Kalman 融合

该图承接 2.1.1 的输出。预校准在正式 Kalman 之前完成，且不读取 Kalman corrected phase 或 posterior。预校准只使用原始数据片段；最终冻结的 $\beta_i^\star$ 随后用于从第 0 帧重新处理原始 wrapped phase $\psi_{i,k}$。

```mehrmaid
flowchart TD
    AB("选定 angle bin<br/>复数 slow-time 序列")
    MT("多目标选取模块<br/>输出 $m$ 个可用 target<br/>$\{\psi_{i,k},\theta_i,b_i\}_{i=1}^{m}$")
    AOA("AoA 初值<br/>$\hat{p}_{i,0}=|\cos\theta_i|$<br/>$\hat{\beta}_{i,0}=1/\max(\hat{p}_{i,0},\epsilon_p)$")
    PRECAL("Kalman 前逐目标预校准<br/>phase rank-1 相对投影 + native ADXL 绝对候选<br/>双折 / leave-one-target-out 门控")
    BETA("逐目标接受或回退后冻结<br/>$\beta_i^\star=\beta_i^{cand}$ 或 $\beta_{i,0}$")

    ACC("加速度传感器<br/>预校准 native $a(t)$<br/>在线输入 $a_{k-1}$")
    XPREV("上一时刻后验<br/>$\mathbf{x}_{k-1},\mathbf{P}_{k-1}$")
    PRED("预测模型 / 系统模型<br/>$\mathbf{x}_{k}^{-}=\mathbf{A}\mathbf{x}_{k-1}+\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}$")

    CORR("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{\mathrm{LOS},-}=\hat{\Theta}_{k}^{-}/\beta_i^\star+b_i$<br/>$\phi_{i,k}^{\mathrm{LOS,corr}}=\psi_{i,k}+2\pi\operatorname{round}\left(\frac{\hat{\phi}_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}}{2\pi}\right)$")
    ZC("LOS corrected phase<br/>$\phi_{i,k}^{\mathrm{LOS,corr}}$")
    YOBS("结构方向观测构造<br/>$y_{i,k}=\beta_i^\star(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)$")
    OBS("结构方向观测模型<br/>$\mathbf{y}_{k}=\mathbf{H}\mathbf{x}_{k}+\mathbf{e}_{k}$<br/>$H_i=[1,0]$")

    KF("Kalman 更新<br/>$\mathbf{x}_{k}^{+}=\mathbf{x}_{k}^{-}+\mathbf{K}_{k}(\mathbf{y}_{k}-\mathbf{H}\mathbf{x}_{k}^{-})$")
    OUT("结构主相位与位移输出<br/>$\mathbf{x}_{k}=[\hat{\Theta}_{k},\dot{\hat{\Theta}}_{k}]^T$<br/>$\hat{q}_{k}=\frac{\lambda}{4\pi}\hat{\Theta}_{k}$")

    subgraph UPD["在线参数更新（不更新 beta）"]
        RUP("target-wise adaptive $R^\Theta$<br/>初始坐标缩放 $R_{i,0}^{\Theta}\propto(\beta_i^\star)^2$<br/>在线由 posterior residual + quality gate 更新")
    end

    AB --> MT
    AB --> AOA
    MT --> PRECAL
    AOA --> PRECAL
    ACC --> PRECAL
    PRECAL -- "per-target accepted 或 AoA fallback" --> BETA
    BETA --> CORR
    BETA --> YOBS
    MT -- "wrapped phase $\psi_{i,k}$" --> CORR

    ACC --> PRED
    XPREV --> PRED
    PRED -- "结构主相位先验 $\hat{\Theta}_{k}^{-}$" --> CORR

    CORR --> ZC
    ZC --> YOBS
    YOBS --> OBS
    OBS --> KF --> OUT
    OUT -- "进入下一时刻" --> XPREV

    KF --> RUP
    RUP -- "$r_{i,k+1}$ updates $\mathbf{R}_{k+1}$" --> OBS
```

### 2.2 模块流向简图

```mehrmaid
flowchart LR
    S("共址传感系统<br/>倒挂毫米波雷达 + 加速度计")
    RA("Range-Angle target 提取<br/>二维峰值 / 角度合并 / 滑动窗口稳定性<br/>候选 target 数 $M$")
    FS("结构频带一致性筛选<br/>由加速度谱确认可用参考 target<br/>可用 target 数 $m\le M$")
    INIT("AoA 初值<br/>$\hat{\beta}_{i,0},\ b_i$")
    CAL("Kalman 前逐目标预校准<br/>rank-1 相对投影 + ADXL 绝对候选<br/>双折验收 / 逐目标回退")
    FREEZE("冻结 $\beta_i^\star$<br/>从第 0 帧运行")
    KF("结构主相位 Kalman 融合<br/>系统模型 + 结构方向多目标观测")
    UNW("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{\mathrm{LOS},-}\rightarrow \phi_{i,k}^{\mathrm{LOS,corr}}$")
    ADAPT("在线 target-wise 权重更新<br/>$r_{i,k+1}$")
    OUT("结构振动方向位移<br/>$\hat{q}_{k}=\lambda\hat{\Theta}_{k}/(4\pi)$")

    S --> RA --> FS --> INIT --> CAL --> FREEZE --> KF --> UNW --> KF --> OUT
    UNW --> ADAPT
    KF --> ADAPT
    ADAPT --> KF
```

上述图组把流程明确分成 Kalman 前预校准和正式在线估计。预校准先从原始数据得到候选静态 $\beta_i$，并由独立双折 holdout 为每个 target 决定采用候选还是精确回退其 AoA 初值；随后统一冻结为 $\beta_i^\star$。正式 Kalman 从第 0 帧开始，系统模型由加速度给出结构主相位先验，再通过冻结的 $\beta_i^\star$ 投影到各 target 的 LoS 相位，用于选择 wrapped phase 的 $2\pi$ 分支。校正相位转换为结构方向观测后进入多目标更新。Kalman posterior 不返回预校准器，因而不存在“同一后验既生成又证明 beta”的循环估计。

这一点也使本文方法相对于 Doppler-based phase unwrapping 形成更进一步的状态空间化表达。后者主要利用同一帧内多个 chirp 估计 LoS 相位变化率，并以该相位变化率预测下一时刻相位分支；本文则在 Ma 等人的 acceleration-aided Kalman 框架上，将状态定义为结构振动方向主相位，使滤波器在每个时刻同时具有 $\hat{\Theta}_k^-$、$\dot{\hat{\Theta}}_k^-$ 以及加速度输入带来的动力学约束。通过除以冻结的 $\beta_i^\star$ 投影后，这一共享状态可分别给出多个 target 的 LoS 相位和相位变化趋势预测：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\beta_i^\star}+b_i,
\qquad
\dot{\hat{\phi}}_{i,k}^{\mathrm{LOS},-}
=
\frac{\dot{\hat{\Theta}}_k^-}{\beta_i^\star}.
$$

因而，本文不是单纯依赖 chirp 间相位差估计分支，而是利用更丰富的结构主相位状态先验约束多 target 的相位分支校正；最终精度提升仍需通过实验验证，但从模型信息来源看，其分支选择约束比单一 Doppler 预测更完整。

该流程中需要特别区分三类相位：

1. target selection 阶段输出的是 wrapped phase：

$$
\psi_i(k)=\angle z_i(k),\qquad \psi_i(k)\in(-\pi,\pi].
$$

2. prediction-aided phase correction 后得到的是 LoS corrected phase：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}\in\mathbb{R}.
$$

它属于第 $i$ 个 target 的 LoS 相位空间，不能直接等同于结构主相位。

3. Kalman 输出的结构主相位是连续相位：

$$
\Theta_k=\frac{4\pi}{\lambda}q_k,\qquad \Theta_k\in\mathbb{R}.
$$

其中，$q_k$ 表示梁体测点在结构振动方向上的真实位移。最终位移由结构主相位恢复：

$$
\hat{q}_k=\frac{\lambda}{4\pi}\hat{\Theta}_k.
$$

## 3. 模块一：Range-Angle Map 与参考 Target 提取

毫米波雷达 ADC 原始数据首先经过 Range FFT 和 Angle FFT/DBF 处理，得到每一帧的复数 range-angle map：

$$
Y_k(b,p),
$$

其中 $b$ 表示 rangeBin，$p$ 表示 angleBin，$k$ 表示 slow-time 采样索引。其幅值图为：

$$
A_k(b,p)=|Y_k(b,p)|.
$$

对每一帧幅值图进行二维局部峰检测，得到候选 range-angle peaks。对于同一 rangeBin 内角度相近的 peaks，若其角度差小于设定阈值，例如 $15^\circ$，则将其合并为一个等效 target：

$$
T=(b,\mathcal{C}),
$$

其中 $\mathcal{C}$ 表示被合并的 angleBin 集合。这样处理的物理含义是：角度相近的散射体具有接近的 LoS 投影系数，其复数相位变化可近似等效为一个稳定 target；而角度差异较大的散射体应尽量分开，以降低同一 rangeBin 内多散射体叠加造成的相位畸变和转换系数漂移。

## 4. 模块二：滑动窗口稳定性确认

单帧出现的峰值不能直接视为可用参考 target。本文为每个候选 target 维护滑动窗口：

$$
\mathcal{W}_t=[t-W+1,t].
$$

在窗口内统计 target 出现率：

$$
R_T(t)=
\frac{1}{W}
\sum_{\tau=t-W+1}^{t}I_T(\tau),
$$

其中：

$$
I_T(\tau)=
\begin{cases}
1,& T\text{ 在第 }\tau\text{ 帧被检测到},\\
0,& T\text{ 在第 }\tau\text{ 帧未被检测到}.
\end{cases}
$$

当：

$$
R_T(t)\ge\tau_R
$$

时，认为该 target 在时间上稳定存在。该步骤只判断 target 是否稳定出现，不进行相位解缠，也不估计转换系数。

## 5. 模块三：结构频带一致性筛选

通过滑动窗口确认只能说明 target 稳定存在，尚不能说明其相位变化由结构振动驱动。因此，本文进一步引入加速度数据确定结构振动频带。设同步加速度信号为 $a(k)$，在滑动窗口内计算其功率谱：

$$
P_a(f)=
\left|
\mathcal{F}\{a(k),k\in\mathcal{W}_t\}
\right|^2.
$$

由加速度谱确定结构主频 $f_a(t)$ 及结构振动频带：

$$
\Omega(t)=
[f_a(t)-\Delta f,\ f_a(t)+\Delta f].
$$

对于每个通过稳定性确认的 target $T$，取其复数 slow-time 序列：

$$
z_T(k),\qquad k\in\mathcal{W}_t.
$$

去除窗口均值后得到：

$$
\tilde{z}_T(k)=z_T(k)-\bar{z}_{T,\mathcal{W}},
$$

并计算其功率谱：

$$
P_T(f)=
\left|
\mathcal{F}\{\tilde{z}_T(k),k\in\mathcal{W}_t\}
\right|^2.
$$

定义结构频带能量占比：

$$
G_T(t)=
\frac{
\sum_{f\in\Omega(t)}P_T(f)
}{
\sum_{f\in\Omega_{\mathrm{valid}}}P_T(f)+\epsilon
}.
$$

若：

$$
G_T(t)\ge\tau_G,
$$

则认为该 target 的 slow-time 变化主要由结构运动驱动，可作为参考 target。该模块输出可用参考 target 集合：

$$
\mathcal{A}_k=\{T_1,T_2,\ldots,T_m\},
\qquad
m\le M.
$$

## 6. 模块四：AoA 初始化与 Kalman 前独立转换系数预校准

对于每个可用 target $T_i$，需要估计其 LoS 位移到结构振动方向位移的转换系数：

$$
q(k)=\beta_i d_{\mathrm{LOS},i}(k).
$$

该转换系数用于将 LoS corrected phase 转换为结构方向主相位观测。为避免循环依赖，当前主方法禁止使用同一 target 参与生成的 Kalman 后验反向标定 $\beta_i$。转换系数只在正式 Kalman 之前，由算法可见的原始雷达相位、AoA 和原生 ADXL 数据批量预校准。

若第 $i$ 个 target 的 AoA 与结构振动方向之间的夹角为 $\theta_i$，则先由几何关系得到结构方向到 LoS 的投影初值 $p_i$，再取其倒数作为 LoS 到结构方向的转换系数初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

预校准包含三层互补约束。公共 AoA 安装偏差 $\delta$ 只作为辅助候选：

$$
p_i(\delta)=\cos(\hat{\theta}_i-\delta),
\qquad
\beta_i(\delta)=\frac{1}{|p_i(\delta)|}.
$$

给定 $\delta$ 后，每个时刻通过加权最小二乘估计所有 target 共享的结构主相位 $\Theta_k$，再以跨 target 残差选择候选 $\delta$。该步骤只修正公共安装偏差，不能表达各 target 不同的 angle-bin 量化误差。

逐目标相对候选来自原始连续相位矩阵的共同运动结构。每个时间折分别去除低阶 nuisance，并拟合

$$
\mathbf{Y}\approx\mathbf{p}\mathbf{s}^{\mathsf T}.
$$

加权第一奇异向量给出各 target 的相对投影 $p_i$；其固有公共尺度由 AoA 初值的稳健中位比例锚定。只有训练/holdout 两折均与 native-timestamp ADXL 动力学相干的 target 才有资格进入参考集合，且两折第一奇异分量占比必须通过共同运动阈值。holdout 中由其余参考 target 重建同一个共同分量，并在该固定潜变量下单独比较该 target 的候选 $p_i$ 与原始 $p_{i,0}$。两折互换后均改善且稳定，才能通过该 target 的相对校准门；该改善量是目标系数的条件诊断，不是完整模型间的独立概率比较。

默认再用 ADXL 提供独立动力学尺度验证。其频域物理关系为：

$$
-\omega^2\Phi_i(\omega)
=
\frac{4\pi}{\lambda}p_i e^{-j\omega\tau}A(\omega).
$$

实现上优先采用等价的时域积分型回归，避免 $-\omega^2$ 放大雷达相位噪声：对原生 ADXL 时间轴进行梯形双积分得到强迫响应参考 $r(t)$，网格搜索公共残余时延 $\tau$，并拟合

$$
\phi_i(t)
=
c_{i,0}+c_{i,1}t+c_{i,2}t^2+c_{i,3}t^3
+
\frac{4\pi}{\lambda}p_i r(t-\tau)+n_i(t).
$$

多项式 nuisance 项吸收积分常数、加速度偏置与缓慢漂移。整个可用记录划分为不重叠的 train 和 holdout：一半拟合绝对 $p_i,\tau$，另一半只重新拟合 nuisance 并验证候选，然后反向再做一次。当 ADXL 轴向/灵敏度或夹具增益未知时，其公共增益与所有 $p_i$ 的公共缩放不可从同一记录唯一分离；这些量经独立验证后绝对投影可辨识。因此，未验证采集预先采用 AoA 锚定相对模式，`validated` 采集预先采用绝对 ADXL 模式。

时间轴、激励和公共时延属于全局门控；相干、跨折一致性、候选边界、改变量、不确定度和 holdout 改善按 target 判断。最终值记为

$$
\beta_i^\star
=
\begin{cases}
\beta_i^{\mathrm{cand}}, & g_i=1,\\
\beta_{i,0}, & g_i=0.
\end{cases}
$$

随后冻结 $\beta_i^\star$，丢弃校准阶段的临时回归状态，并从第 0 帧重新运行正式 Kalman。历史版本中“由 corrected phase 与 Kalman posterior 做短窗中心化 LS、在线递推 $\beta_i$”的方案仅保留为 legacy/ablation 对照，不属于当前主方法。

## 7. 模块五：结构主相位 Kalman 融合

在线 Kalman 融合阶段重新使用每个 target 的原始 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k).
$$

定义结构振动方向主相位：

$$
\Theta_k=\frac{4\pi}{\lambda}q_k,
$$

并构造状态向量：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix}.
$$

由于加速度计测得的是结构振动方向加速度，状态预测可直接写为：

$$
\mathbf{x}_k^-
=
\mathbf{A}\mathbf{x}_{k-1}
+
\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}
+
\mathbf{w}_{k-1},
$$

其中：

$$
\mathbf{A}=
\begin{bmatrix}
1&T\\
0&1
\end{bmatrix},
\qquad
\mathbf{B}=
\begin{bmatrix}
T^2/2\\
T
\end{bmatrix}.
$$

过程噪声采用固定形式：

$$
\mathbf{Q}
=
q
\begin{bmatrix}
T^3/3 & T^2/2\\
T^2/2 & T
\end{bmatrix}.
$$

由预测主相位得到第 $i$ 个 target 的 LoS 相位预测：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\beta_i^\star}+b_i.
$$

利用该预测值对 wrapped phase 进行分支校正：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{
\hat{\phi}_{i,k}^{\mathrm{LOS},-} - \psi_{i,k}
}{2\pi}
\right).
$$

该 corrected phase 仍然是 LoS 连续相位。为了使正文主坐标系与加速度和状态定义一致，将其转换为结构方向主相位观测：

$$
y_{i,k}
=
\beta_i^\star
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

将所有可用 target 的结构方向观测堆叠为：

$$
\mathbf{y}_k
=
\begin{bmatrix}
y_{1,k}\\
y_{2,k}\\
\vdots\\
y_{m,k}
\end{bmatrix}.
$$

结构方向观测模型为：

$$
\mathbf{y}_k
=
\mathbf{H}\mathbf{x}_k+\mathbf{e}_k,
\qquad
\mathbf{H}
=
\begin{bmatrix}
1&0\\
1&0\\
\vdots&\vdots\\
1&0
\end{bmatrix}.
$$

也即每个 target 的观测行均为：

$$
\mathbf{H}_i
=
\begin{bmatrix}
1&0
\end{bmatrix}.
$$

观测噪声协方差采用 target-wise 对角形式，但此时噪声已位于结构主相位坐标：

$$
\mathbf{R}_k^{\Theta}
=
\operatorname{diag}
\left(
R_{1,k}^{\Theta},R_{2,k}^{\Theta},\ldots,R_{m,k}^{\Theta}
\right).
$$

其中第 $i$ 个 target 的结构方向观测噪声近似包含两部分：

$$
R_{i,k}^{\Theta}
\approx
\left(\beta_i^\star\right)^2R_{i,k}^{\mathrm{LOS}}
+
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right)^2
\sigma_{\beta_i,\mathrm{pre}}^{2}.
$$

然后执行标准 Kalman 更新：

$$
\mathbf{K}_k
=
\mathbf{P}_k^-
\mathbf{H}^\mathrm{T}
\left(
\mathbf{H}\mathbf{P}_k^-\mathbf{H}^\mathrm{T}
+
\mathbf{R}_k^{\Theta}
\right)^{-1},
$$

$$
\mathbf{x}_k
=
\mathbf{x}_k^-
+
\mathbf{K}_k
\left(
\mathbf{y}_k
-
\mathbf{H}\mathbf{x}_k^-
\right).
$$

Kalman 更新后，当前主方法不直接使用第 $i$ 个 target 的预测创新来更新基础测量噪声。预测创新为：

$$
e_{i,k}^-
=
y_{i,k}
-
\mathbf{H}_i\mathbf{x}_k^-.
$$

同时包含过程模型误差、加速度输入误差和 radar 观测误差。参考 Akhlaghi 等人关于 adaptive adjustment of noise covariance 的分工，prediction innovation 更适合反映过程模型或 $Q$ 的不确定性，而 posterior residual 更适合用于 measurement noise covariance estimation。因此本文采用后验残差：

$$
\varepsilon_{i,k}
=
y_{i,k}
-
\mathbf{H}_i\mathbf{x}_k^+.
$$

基础测量噪声的瞬时估计写为：

$$
\tilde{r}_{i,k}
=
\varepsilon_{i,k}^{2}
+
\mathbf{H}_i\mathbf{P}_k^+\mathbf{H}_i^{\mathrm{T}},
$$

并引入 target quality gate。令 $\rho_{i,k}\in[0,1]$ 表示由 SNR、presence、range-angle 稳定性和 IQ 幅值稳定性等可见量构造的 target 质量，定义

$$
\Delta r_{i,k}
=
\tilde{r}_{i,k}
-
r_{i,k},
$$

$$
g_{i,k}
=
\begin{cases}
1-\rho_{i,k}, & \Delta r_{i,k}>0,\\
1, & \Delta r_{i,k}\le 0.
\end{cases}
$$

最终用遗忘因子与上下限约束更新该 target 的基础测量噪声：

$$
r_{i,k+1}
=
\operatorname{clip}
\left[
r_{i,k}
+
(1-\alpha)g_{i,k}\Delta r_{i,k},
\ r_{\min},
\ r_{\max}
\right],
$$

其中 $0<\alpha<1$ 为遗忘因子。初始阶段 $r_{i,0}$ 由 target 初始质量、SNR 和 presence 给出；冻结 $\beta_i^\star$ 相对 AoA 初值改变时，实现按两者平方比同步缩放初始结构方向噪声。低质量 target 会得到较大的初始测量噪声。该门控机制使 target 质量下降且后验残差增大时自动降低对应 target 的观测权重；当结构响应突然增强但 target 质量正常时，抑制将预测模型误差误归因于 measurement noise 的 $R$ 异常上涨。当结构方向观测由 LoS 观测变换而来时，对应噪声尺度为：

$$
R_{i,k}^{\Theta}
\approx
\left(\beta_i^\star\right)^2R_{i,k}^{\mathrm{LOS}}.
$$

预校准方差描述的是整段记录共享的静态参数不确定度，当前实现用它做候选接受门控和落盘诊断，不把它当作每帧独立白噪声重复加到 $R_{i,k}^{\Theta}$。在线变化量仅为 phase correction 和 target-wise $R_i$。

该设计参考 Akhlaghi、Zhou 和 Huang 的 *Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation* 中“prediction innovation 更适合反映过程模型误差、posterior residual 更适合估计 measurement noise”的 Q/R 归因思想，同时参考 Mehra 的 covariance matching 框架和 Li 等人在 INS/GNSS 多观测通道中的 measurement noise covariance estimation。本文把该思想改造为 radar target-wise 观测权重模型：每个 target 拥有独立 $R_{i,k}^{\Theta}$，基础噪声估计使用后验协方差投影 $\mathbf{H}_{i}\mathbf{P}_k^+\mathbf{H}_{i}^{\mathrm{T}}$，$R$ 的上涨受 target quality gate 约束。该后验残差只更新 $R_i$，不得回灌 beta。

## 8. 关键接口关系

为避免方法链条出现循环依赖，各模块接口应明确如下。

| 模块 | 输入 | 输出 | 是否依赖 Kalman 内部相位校正 |
|---|---|---|---|
| Range-Angle Map | ADC 原始数据 | 复数 range-angle map | 否 |
| target 选择 | range-angle map、加速度频带 | 可用 target 集合、wrapped phase | 否 |
| AoA 初始化 | target AoA、静止初始相位 | $\beta_i^{(0)}$、$b_i$ | 否 |
| 独立转换系数预校准 | 原始 target phase、AoA、原生 ADXL 时间戳与加速度、train/holdout 划分 | candidate $\beta_i$、公共 $\delta/\tau$、variance/confidence、accepted/reason | 否；明确禁止 Kalman corrected phase 和 posterior |
| 冻结与回退 | 预校准门控结果、AoA 初值 | $\beta_i^\star$；拒绝时严格等于 $\beta_i^{(0)}$ | 否 |
| Kalman 融合 | 第 0 帧起的原始 wrapped phase、冻结 $\beta_i^\star$、加速度、结构方向 $R_{i,k}^{\Theta}$ | 连续主相位、结构位移 | 是，仅在框架内部做 phase correction 与 target-wise $R$ 更新 |

因此，预校准和在线相位校正具有清晰边界。预校准可以在有限、连续且可辨识的原始数据片段上局部 unwrap，但不使用任何 Kalman 生成的相位；正式时程的 $2\pi$ 分支仍在 Kalman prediction-aided phase correction 中从第 0 帧在线选择。冻结的 $\beta_i^\star$ 只作为确定的坐标转换和其静态不确定度来源，posterior residual 只更新 target-wise $R_i$。这从数据依赖上消除了 Kalman 后验到 beta 的闭环。

## 9. 与三个创新点的对应关系

整体架构中的三个核心创新点对应关系如下：

1. **在线多 target 选择**：对应 Range-Angle Map、角度合并、滑动窗口稳定性确认和结构频带一致性筛选，解决“哪些环境散射体可作为参考 target”的问题。
2. **公共几何偏差与独立尺度预校准**：多 target 只修正公共 AoA 偏差，ADXL 提供独立动力学尺度与时延验证；train/holdout 门控决定接受候选或回退 AoA，并输出可审计的不确定度。
3. **结构主相位多 target Kalman 融合**：将 Ma 等人的单目标 LoS 相位状态改写为结构振动方向主相位状态，并把多个 target 的 LoS corrected phase 先转换为结构方向观测后共同更新；在线只执行 phase correction 与 posterior-residual、quality-gated target-wise $R^\Theta$ 更新。

该架构使论文主线形成单向、可审计的处理链：

$$
\text{找 target}
\rightarrow
\text{用 AoA 给转换关系初值}
\rightarrow
\text{用原始雷达/ADXL 数据预校准并经 holdout 验收}
\rightarrow
\text{冻结 beta，从第 0 帧用多 target 相位约束结构主相位}
\rightarrow
\text{输出梁体位移}.
$$
