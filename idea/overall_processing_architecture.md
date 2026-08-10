# 倒挂式毫米波雷达结构位移估计整体处理架构

## 1. 系统目标

本文研究的传感系统由毫米波雷达和加速度传感器共址安装在梁体测点处，雷达朝向正下方。与激光测振仪、LVDT 等需要静态参考系或固定安装基准的位移传感器不同，倒挂式毫米波雷达随结构共同运动，并利用周围近似静止的环境散射体作为参考目标，从而在不额外布设外部静态参考点的条件下估计结构振动方向位移。

系统的核心任务可以表述为：

$$
\text{从雷达观测到的多个环境静止散射 target 中，恢复梁体测点在结构振动方向上的连续位移。}
$$

由于自然环境中的参考 target 数量多、角度和反射强度不同、同一 rangeBin 内可能存在多个散射体，并且雷达原始相位存在 $2\pi$ 缠绕，本文将整体处理流程拆分为四个层级：

$$
\text{参考 target 提取}
\rightarrow
\text{AoA 几何初始化与冷启动}
\rightarrow
\text{转换系数自举更新}
\rightarrow
\text{结构主相位 Kalman 融合}.
$$

其中，target 提取阶段不依赖相位解缠；AoA 几何初始化为每个 target 给出可启动的转换系数初值；冷启动和初始微振阶段通过固定/标定过程噪声 $Q$ 与 posterior-residual、target-quality-gated 自适应测量噪声 $R$ 使滤波器优先依赖加速度预测，并在短窗口内递推修正转换系数。wrapped phase 的在线分支校正、降噪和多 target 融合统一在结构主相位 Kalman 框架内部完成。

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

#### 2.1.2 结构主相位 Kalman 融合闭环

该图承接 2.1.1 的输出。经过多目标选取与筛选后，当前时刻有 $m$ 个可用 target 进入 Kalman 框架。需要注意，这些 target 输入的是原始 wrapped phase $\psi_{i,k}$，而不是已经完整解缠的连续相位。

```mehrmaid
flowchart TD
    AB("选定 angle bin<br/>复数 slow-time 序列")
    MT("多目标选取模块<br/>输出 $m$ 个可用 target<br/>$\{\psi_{i,k},\theta_i,b_i\}_{i=1}^{m}$")
    AOA("AoA 冷启动<br/>$\hat{p}_{i,0}=|\cos\theta_i|$<br/>$\hat{\beta}_{i,0}=1/\max(\hat{p}_{i,0},\epsilon_p)$")
    BETA("转换系数预测<br/>$\hat{\beta}_{i,k}^{-}=\hat{\beta}_{i,k-1}^{+}$")

    ACC("加速度传感器<br/>$a_{k-1}$")
    XPREV("上一时刻后验<br/>$\mathbf{x}_{k-1},\mathbf{P}_{k-1}$")
    PRED("预测模型 / 系统模型<br/>$\mathbf{x}_{k}^{-}=\mathbf{A}\mathbf{x}_{k-1}+\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}$")

    CORR("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{\mathrm{LOS},-}=\hat{\Theta}_{k}^{-}/\hat{\beta}_{i,k}^{-}+b_i$<br/>$\phi_{i,k}^{\mathrm{LOS,corr}}=\psi_{i,k}+2\pi\operatorname{round}\left(\frac{\hat{\phi}_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}}{2\pi}\right)$")
    ZC("LOS corrected phase<br/>$\phi_{i,k}^{\mathrm{LOS,corr}}$")
    YOBS("结构方向观测构造<br/>$y_{i,k}=\hat{\beta}_{i,k}^{-}(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)$")
    OBS("结构方向观测模型<br/>$\mathbf{y}_{k}=\mathbf{H}\mathbf{x}_{k}+\mathbf{e}_{k}$<br/>$H_i=[1,0]$")

    KF("Kalman 更新<br/>$\mathbf{x}_{k}^{+}=\mathbf{x}_{k}^{-}+\mathbf{K}_{k}(\mathbf{y}_{k}-\mathbf{H}\mathbf{x}_{k}^{-})$")
    OUT("结构主相位与位移输出<br/>$\mathbf{x}_{k}=[\hat{\Theta}_{k},\dot{\hat{\Theta}}_{k}]^T$<br/>$\hat{q}_{k}=\frac{\lambda}{4\pi}\hat{\Theta}_{k}$")

    subgraph UPD["在线参数更新"]
        LS("转换系数中心化 LS 更新<br/>$x_\tau=\phi_{i,\tau}^{\mathrm{LOS,corr}}-b_i,\ y_\tau=\hat{\Theta}_{\tau}^{+}$<br/>$\hat{\beta}_{i,k+1}=\frac{\sum x_{\tau,c}y_{\tau,c}+\lambda_{\beta}\hat{\beta}_{i,0}}{\sum x_{\tau,c}^{2}+\lambda_{\beta}}$")
        RUP("target-wise adaptive $R^\Theta$<br/>$R_{i,k}^{\Theta}\approx(\hat{\beta}_{i,k}^{-})^2R_{i,k}^{\mathrm{LOS}}+(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)^2\sigma_{\beta_i,k}^2$")
    end

    AB --> MT
    AB --> AOA
    MT --> BETA
    AOA --> BETA
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

    ZC -- "同一 $\phi_{i,k}^{\mathrm{LOS,corr}}$" --> LS
    OUT -- "$\hat{\Theta}_{k}$" --> LS
    LS -- "$\hat{\beta}_{i,k+1}$" --> BETA

    KF --> RUP
    RUP -- "$r_{i,k+1}$ updates $\mathbf{R}_{k+1}$" --> OBS
```

### 2.2 模块流向简图

```mehrmaid
flowchart LR
    S("共址传感系统<br/>倒挂毫米波雷达 + 加速度计")
    RA("Range-Angle target 提取<br/>二维峰值 / 角度合并 / 滑动窗口稳定性<br/>候选 target 数 $M$")
    FS("结构频带一致性筛选<br/>由加速度谱确认可用参考 target<br/>可用 target 数 $m\le M$")
    INIT("AoA 冷启动<br/>$\hat{\beta}_{i,0},\ b_i,\ r_{i,0}$")
    KF("结构主相位 Kalman 融合<br/>系统模型 + 结构方向多目标观测")
    UNW("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{\mathrm{LOS},-}\rightarrow \phi_{i,k}^{\mathrm{LOS,corr}}$")
    ADAPT("在线自举与权重更新<br/>$\hat{\beta}_{i,k+1},\ r_{i,k+1}$")
    OUT("结构振动方向位移<br/>$\hat{q}_{k}=\lambda\hat{\Theta}_{k}/(4\pi)$")

    S --> RA --> FS --> INIT --> KF --> UNW --> KF --> OUT
    UNW --> ADAPT
    KF --> ADAPT
    ADAPT --> KF
```

上述详细图组将数据流处理过程拆分为 target 提取筛选和 Kalman 融合闭环两个子过程，简图则突出各模块之间的主线关系。Kalman 后半段的核心是：系统模型先由加速度给出结构主相位先验 $\mathbf{x}_k^-$，再通过各 target 当前转换系数 $\beta_i$ 投影回 target-wise LoS 相位预测 $\hat{\phi}_{i,k}^{\mathrm{LOS},-}$，用于选择 wrapped phase 的 $2\pi$ 分支。得到的 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 是第 $i$ 个 target 的 LoS 连续校正相位；它先乘以 $\beta_i$ 转为结构方向主相位观测 $y_{i,k}$，再进入多目标 Kalman 更新。与此同时，$\phi_{i,k}^{\mathrm{LOS,corr}}$ 与后验主相位 $\hat{\Theta}_k^+$ 一起进入短窗口 $\mathcal{W}_{\beta}$，递推修正每个 target 的转换系数 $\beta_i$。因此，转换系数计算所需的局部连续相位并不是预先独立完成的全时程解缠结果，而是 Kalman 预测辅助分支校正后的在线 LoS 局部相位。

这一点也使本文方法相对于 Doppler-based phase unwrapping 形成更进一步的状态空间化表达。后者主要利用同一帧内多个 chirp 估计 LoS 相位变化率，并以该相位变化率预测下一时刻相位分支；本文则在 Ma 等人的 acceleration-aided Kalman 框架上，将状态定义为结构振动方向主相位，使滤波器在每个时刻同时具有 $\hat{\Theta}_k^-$、$\dot{\hat{\Theta}}_k^-$ 以及加速度输入带来的动力学约束。通过除以 $\beta_i$ 投影后，这一共享状态可分别给出多个 target 的 LoS 相位和相位变化趋势预测：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\hat{\beta}_{i,k}^{-}}+b_i,
\qquad
\dot{\hat{\phi}}_{i,k}^{\mathrm{LOS},-}
=
\frac{\dot{\hat{\Theta}}_k^-}{\hat{\beta}_{i,k}^{-}}.
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

## 6. 模块四：AoA 初始化与转换系数自举更新

对于每个可用 target $T_i$，需要估计其 LoS 位移到结构振动方向位移的转换系数：

$$
q(k)=\beta_i d_{\mathrm{LOS},i}(k).
$$

该转换系数用于将 LoS corrected phase 转换为结构方向主相位观测。传统处理通常需要先获得一段连续雷达相位，再与加速度参考位移拟合 $\beta_i$。这会带来潜在循环依赖：Kalman 相位解缠需要 $\beta_i$，而 $\beta_i$ 标定又可能需要解缠后的相位。本文采用 AoA 几何初始化与自举更新的方式避免该问题。

若第 $i$ 个 target 的 AoA 与结构振动方向之间的夹角为 $\theta_i$，则先由几何关系得到结构方向到 LoS 的投影初值 $p_i$，再取其倒数作为 LoS 到结构方向的转换系数初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

当本文只选取或合并角度较小的 target 时，AoA 初值通常不会偏离真实转换关系过远。冷启动阶段假设结构近似静止，用于确定每个 target 的初始相位偏置 $b_i$，并将滤波状态初始化为：

$$
\mathbf{x}_0\approx
\begin{bmatrix}
0\\
0
\end{bmatrix}.
$$

同时，将每个 target 的测量噪声初始化为较大值：

$$
r_{i,0}=r_{\max}.
$$

这意味着在刚进入 Kalman 框架时，滤波器主要依赖加速度驱动的结构主相位预测，而不是完全相信由 AoA 初值构造的雷达观测。

当车辆或其他荷载从远处接近时，桥梁通常会先出现小幅可辨识振动。该阶段相位分支选择相对容易，同时又具有足够动态信息用于估计转换系数。由 Kalman 预测得到结构主相位 $\hat{\Theta}_k^-$ 后，第 $i$ 个 target 的 LoS 相位预测为：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\hat{\beta}_{i,k}^{-}}+b_i.
$$

利用该预测值对原始 wrapped phase 进行分支校正：

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

这里的 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 仍然是 LoS 连续相位。在短窗口 $\mathcal{W}_{\beta}$ 内，可用校正后的 LoS 连续相位与结构主相位估计递推修正 $\beta_i$。文档早期版本采用未中心化 plain LS；当前正文统一表述为估计 LoS corrected phase 到结构主相位的斜率。令：

$$
x_k
=
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i,
\qquad
y_k
=
\hat{\Theta}_k^+.
$$

中心化后窗口更新写为：

$$
\hat{\beta}_{i}
=
\frac{
\sum_{k\in\mathcal{W}_{\beta}}
x_{k,c}y_{k,c}
+
\lambda_\beta\hat{\beta}_{i,0}
}{
\sum_{k\in\mathcal{W}_{\beta}}
x_{k,c}^2
+
\lambda_\beta
}.
$$

该估计只在窗口内结构响应激励足够、target quality 足够好且相位分支稳定时更新；若振动过弱或观测质量不足，则保持 AoA 初值或上一时刻估计值。随着前几次分支校正成功，$\hat{\beta}_i$ 会在短时间内从几何初值收敛到该 target 的等效转换系数。该过程不是先验完整解缠，而是由 AoA 初值、加速度预测和自适应测量噪声共同支撑的在线自举。

可定义窗口内转换系数拟合残差：

$$
e_{\beta,i}
=
\frac{
\left\|
\hat{\boldsymbol{\Theta}}_{\mathcal{W}}^{+}
-
\hat{\beta}_i
\left(
\boldsymbol{\phi}_{i,\mathcal{W}}^{\mathrm{LOS,corr}}
-
b_i\mathbf{1}
\right)
\right\|_2
}{
\left\|
\hat{\boldsymbol{\Theta}}_{\mathcal{W}}^{+}
\right\|_2
}.
$$

在第一版方法中，该残差主要用于描述和实验分析；滤波过程中的 target 权重由后文的自适应 $R_i$ 自动调节。即当 $\beta_i$ 尚未收敛或 target 相位质量较差时，其残差会增大，进而使对应观测噪声增大；当 $\beta_i$ 收敛后，对应 target 的观测权重自动恢复。

这一设计避免了“转换系数必须先由完整解缠相位标定”的死锁，同时保留了 Ma 等人预测辅助相位校正思想和 Doppler-based phase unwrapping 文献中的相位速度辅助分支选择思想。若雷达帧内包含多个 chirps，还可用同一 range-angle target 的 chirp 间相位差估计 LoS 相位变化率，作为 $\hat{\phi}_{i,k}^{\mathrm{LOS},-}$ 的辅助先验，但这不是闭环成立的必要条件。

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
\frac{\hat{\Theta}_k^-}{\hat{\beta}_{i,k}^{-}}+b_i.
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
\hat{\beta}_{i,k}^{-}
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
\left(\hat{\beta}_{i,k}^{-}\right)^2R_{i,k}^{\mathrm{LOS}}
+
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right)^2
\sigma_{\beta_i,k}^{2}.
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

并引入 target quality gate。令 $\rho_{i,k}\in[0,1]$ 表示由 SNR、presence、range-angle 稳定性、IQ 幅值稳定性和转换系数置信度等可见量构造的 target 质量，定义

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

其中 $0<\alpha<1$ 为遗忘因子。初始阶段 $r_{i,0}$ 由 target 初始质量、SNR、presence 和几何投影等信息给出；低质量 target 会得到较大的初始测量噪声，高质量 target 可更早参与更新。该门控机制使 target 质量下降且后验残差增大时自动降低对应 target 的观测权重；当结构响应突然增强但 target 质量正常时，抑制将预测模型误差误归因于 measurement noise 的 $R$ 异常上涨。针对 AoA cold start 阶段转换系数尚未收敛的问题，结构方向有效观测噪声应包含 $\beta_i$ 对 LoS 相位噪声的放大，以及 $\beta_i$ 本身不确定性传播项：

$$
R_{i,k}^{\Theta}
\approx
\left(\hat{\beta}_{i,k}^{-}\right)^2R_{i,k}^{\mathrm{LOS}}
+
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right)^2
\sigma_{\beta_i,k}^{2}.
$$

这使“转换系数越不确定，越降低观测权重”与在线 bootstrap 收敛过程对应起来。当前代码与正文统一在结构方向观测空间表达有效噪声，$\beta_i$ 不确定性直接进入 $R_{i,k}^{\Theta}$，不会再把结构主相位到 LoS 相位的投影参数作为主符号。

该设计参考 Akhlaghi、Zhou 和 Huang 的 *Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation* 中“prediction innovation 更适合反映过程模型误差、posterior residual 更适合估计 measurement noise”的 Q/R 归因思想，同时参考 Mehra 的 covariance matching 框架和 Li 等人在 INS/GNSS 多观测通道中的 measurement noise covariance estimation。本文的改进不在于重复已有 adaptive Kalman 公式，而在于把该思想改造为 radar target-wise 观测权重模型：每个 target 拥有独立 $R_{i,k}^{\Theta}$，基础噪声估计使用后验协方差投影 $\mathbf{H}_{i}\mathbf{P}_k^+\mathbf{H}_{i}^{\mathrm{T}}$，$R$ 的上涨受 target quality gate 约束，并额外叠加 AoA cold start 下的 $\beta_i$ 置信度传播项。由此，已有文献提供统计依据，本文解决的是倒挂毫米波雷达多 target 相位融合中的观测质量归因问题。

## 8. 关键接口关系

为避免方法链条出现循环依赖，各模块接口应明确如下。

| 模块 | 输入 | 输出 | 是否依赖 Kalman 内部相位校正 |
|---|---|---|---|
| Range-Angle Map | ADC 原始数据 | 复数 range-angle map | 否 |
| target 选择 | range-angle map、加速度频带 | 可用 target 集合、wrapped phase | 否 |
| AoA 与冷启动初始化 | target AoA、静止初始相位 | $\beta_i^{(0)}$、$b_i$、较大的 $r_{i,0}$ | 否 |
| 转换系数自举更新 | LoS corrected phase $\phi_{i,k}^{\mathrm{LOS,corr}}$、结构主相位后验 $\hat{\Theta}_k^+$ | $\hat{\beta}_{i,k}$、$e_{\beta,i}$、$S_{\beta,i}$ | 依赖已启动的 Kalman 递推，但不依赖预先完整解缠 |
| Kalman 融合 | wrapped phase、$\hat{\beta}_{i,k}$、加速度、结构方向 $R_{i,k}^{\Theta}$ | 连续主相位、结构位移 | 是，在框架内部完成 |

因此，本文流程中不存在一套独立于 Kalman 的预处理式完整相位解缠。wrapped phase 的 $2\pi$ 分支选择在 Kalman 预测辅助相位校正步骤中在线完成，校正后的 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 是 LoS 连续相位；它一方面经 $\beta_i$ 转换为结构方向观测 $y_{i,k}$ 参与 Kalman 更新，另一方面与结构主相位后验一起用于自举 $\beta_i$。转换系数不再要求由一段预先完整解缠的雷达相位单独标定，而是以 AoA 几何值启动，并在初始微振阶段借助加速度预测、基础测量噪声更新和转换系数置信度传播逐步收敛。这样，转换系数需要连续相位、连续相位校正又需要转换系数的循环依赖被打断。

## 9. 与三个创新点的对应关系

整体架构中的三个核心创新点对应关系如下：

1. **在线多 target 选择**：对应 Range-Angle Map、角度合并、滑动窗口稳定性确认和结构频带一致性筛选，解决“哪些环境散射体可作为参考 target”的问题。
2. **复合 target 等效转换系数稳定性**：对应 AoA 几何初始化、短窗口自举更新和稳定性评价，解释 angle cluster 或复合散射 target 何时可用一个稳定 $\beta_i$ 表示。
3. **结构主相位多 target Kalman 融合**：对应最终在线融合框架，将 Ma 等人的单目标 LoS 相位状态改写为结构振动方向主相位状态，并把多个 target 的 LoS corrected phase 先转换为结构方向主相位观测后共同更新；固定/标定 $Q$ 与 posterior-residual、quality-gated、confidence-aware target-wise $R^\Theta$ 共同完成初始自举和稳定融合。

该架构使论文主线形成闭环：

$$
\text{找 target}
\rightarrow
\text{用 AoA 给转换关系初值}
\rightarrow
\text{在 Kalman 中自举收敛转换系数和观测权重}
\rightarrow
\text{用多 target 相位约束同一个结构主相位}
\rightarrow
\text{输出梁体位移}.
$$
