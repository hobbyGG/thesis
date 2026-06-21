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

其中，target 提取阶段不依赖相位解缠；AoA 几何初始化为每个 target 给出可启动的转换系数初值；冷启动和初始微振阶段通过固定过程噪声 $Q$ 与自适应测量噪声 $R$ 使滤波器优先依赖加速度预测，并在短窗口内递推修正转换系数。wrapped phase 的在线分支校正、降噪和多 target 融合统一在结构主相位 Kalman 框架内部完成。

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
    AOA("AoA 冷启动<br/>$\hat{\kappa}_{i,0}=\cos\theta_i$<br/>$\hat{\beta}_{i,0}=1/\hat{\kappa}_{i,0}$")
    H("观测矩阵构造<br/>$\mathbf{h}_{i,k}=[1/\hat{\beta}_{i,k},0]$<br/>$\mathbf{H}_{k}=[\mathbf{h}_{1,k};\ldots;\mathbf{h}_{m,k}]$")

    ACC("加速度传感器<br/>$a_{k-1}$")
    XPREV("上一时刻后验<br/>$\mathbf{x}_{k-1},\mathbf{P}_{k-1}$")
    PRED("预测模型 / 系统模型<br/>$\mathbf{x}_{k}^{-}=\mathbf{A}\mathbf{x}_{k-1}+\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}$")

    CORR("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{-}=\mathbf{h}_{i,k}\mathbf{x}_{k}^{-}+b_i$<br/>$z_{i,k}^{\mathrm{corr}}=\psi_{i,k}+2\pi\operatorname{round}\left(\frac{\hat{\phi}_{i,k}^{-}-\psi_{i,k}}{2\pi}\right)$")
    ZC("统一校正相位<br/>$z_{i,k}^{\mathrm{corr}}$")
    OBS("观测模型<br/>$\mathbf{z}_{k}^{\mathrm{corr}}=\mathbf{H}_{k}\mathbf{x}_{k}+\mathbf{b}_{k}+\mathbf{v}_{k}$")

    KF("Kalman 更新<br/>$\mathbf{x}_{k}=\mathbf{x}_{k}^{-}+\mathbf{K}_{k}(\mathbf{z}_{k}^{\mathrm{corr}}-\mathbf{H}_{k}\mathbf{x}_{k}^{-}-\mathbf{b}_{k})$")
    OUT("结构主相位与位移输出<br/>$\mathbf{x}_{k}=[\hat{\Theta}_{k},\dot{\hat{\Theta}}_{k}]^T$<br/>$\hat{q}_{k}=\frac{\lambda}{4\pi}\hat{\Theta}_{k}$")

    subgraph UPD["在线参数更新"]
        LS("转换系数中心化正则 LS 更新<br/>$\hat{\kappa}_{i,k+1}=\frac{\sum_{\tau\in\mathcal{W}_{\beta}}\tilde{\Theta}_{\tau}\tilde{z}_{i,\tau}+\lambda_{\kappa}\hat{\kappa}_{i,0}}{\sum_{\tau\in\mathcal{W}_{\beta}}\tilde{\Theta}_{\tau}^{2}+\lambda_{\kappa}}$<br/>$\hat{\beta}_{i,k+1}=1/\hat{\kappa}_{i,k+1}$")
        RUP("target-wise adaptive $R$<br/>$e_{i,k}^{-}=z_{i,k}^{\mathrm{corr}}-(\mathbf{h}_{i,k}\mathbf{x}_{k}^{-}+b_i)$<br/>$e_{i,k}^{-}\rightarrow r_{i,k+1}$")
    end

    AB --> MT
    AB --> AOA
    MT --> H
    AOA --> H
    H --> CORR
    H --> OBS
    MT -- "wrapped phase $\psi_{i,k}$" --> CORR

    ACC --> PRED
    XPREV --> PRED
    PRED -- "LoS 相位先验 $\hat{\phi}_{i,k}^{-}$" --> CORR

    CORR --> ZC
    ZC --> OBS
    OBS --> KF --> OUT
    OUT -- "进入下一时刻" --> XPREV

    ZC -- "同一 $z_{i,k}^{\mathrm{corr}}$" --> LS
    OUT -- "$\hat{\Theta}_{k}$" --> LS
    LS -- "$\hat{\beta}_{i,k+1}$" --> H

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
    KF("结构主相位 Kalman 融合<br/>系统模型 + 多目标观测模型")
    UNW("预测辅助相位校正<br/>$\hat{\phi}_{i,k}^{-}\rightarrow z_{i,k}^{\mathrm{corr}}$")
    ADAPT("在线自举与权重更新<br/>$\hat{\beta}_{i,k+1},\ r_{i,k+1}$")
    OUT("结构振动方向位移<br/>$\hat{q}_{k}=\lambda\hat{\Theta}_{k}/(4\pi)$")

    S --> RA --> FS --> INIT --> KF --> UNW --> KF --> OUT
    UNW --> ADAPT
    KF --> ADAPT
    ADAPT --> KF
```

上述详细图组将数据流处理过程拆分为 target 提取筛选和 Kalman 融合闭环两个子过程，简图则突出各模块之间的主线关系。Kalman 后半段的核心是：系统模型先由加速度给出结构主相位先验 $\mathbf{x}_k^-$，再通过各 target 当前转换系数形成 target-wise LoS 相位预测 $\hat{\phi}_{i,k}^-$，用于选择 wrapped phase 的 $2\pi$ 分支。得到的 $z_{i,k}^{\mathrm{corr}}$ 具有双重作用：一方面堆叠为 $\mathbf{z}_k^{\mathrm{corr}}$ 进入多目标观测模型，修正结构主相位状态；另一方面与后验主相位 $\hat{\Theta}_k$ 一起进入短窗口 $\mathcal{W}_{\beta}$，递推修正每个 target 的转换系数 $\beta_i$。因此，转换系数计算所需的局部连续相位并不是预先独立完成的全时程解缠结果，而是 Kalman 预测辅助分支校正后的在线局部相位。

这一点也使本文方法相对于 Doppler-based phase unwrapping 形成更进一步的状态空间化表达。后者主要利用同一帧内多个 chirp 估计 LoS 相位变化率，并以该相位变化率预测下一时刻相位分支；本文则在 Ma 等人的 acceleration-aided Kalman 框架上，将状态定义为结构振动方向主相位，使滤波器在每个时刻同时具有 $\hat{\Theta}_k^-$、$\dot{\hat{\Theta}}_k^-$ 以及加速度输入带来的动力学约束。通过 $\mathbf{h}_{i,k}$ 映射后，这一共享状态可分别给出多个 target 的 LoS 相位和相位变化趋势预测：

$$
\hat{\phi}_{i,k}^-
=
\hat{\kappa}_{i,k}\hat{\Theta}_k^-+b_i,
\qquad
\dot{\hat{\phi}}_{i,k}^-
=
\hat{\kappa}_{i,k}\dot{\hat{\Theta}}_k^-.
$$

因而，本文不是单纯依赖 chirp 间相位差估计分支，而是利用更丰富的结构主相位状态先验约束多 target 的相位分支校正；最终精度提升仍需通过实验验证，但从模型信息来源看，其分支选择约束比单一 Doppler 预测更完整。

该流程中需要特别区分两类相位：

1. target selection 阶段输出的是 wrapped phase：

$$
\psi_i(k)=\angle z_i(k),\qquad \psi_i(k)\in(-\pi,\pi].
$$

2. Kalman 输出的结构主相位是连续相位：

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

该转换系数用于后续 Kalman 观测矩阵构造。传统处理通常需要先获得一段连续雷达相位，再与加速度参考位移拟合 $\beta_i$。这会带来潜在循环依赖：Kalman 相位解缠需要 $\beta_i$，而 $\beta_i$ 标定又可能需要解缠后的相位。本文采用 AoA 几何初始化与自举更新的方式避免该问题。

若第 $i$ 个 target 的 AoA 与结构振动方向之间的夹角为 $\theta_i$，则其 LoS 投影系数可由几何关系给出初值：

$$
\kappa_i^{(0)}=\cos\theta_i,
\qquad
\beta_i^{(0)}=\frac{1}{\kappa_i^{(0)}}.
$$

其中 $\kappa_i=1/\beta_i$。当本文只选取或合并角度较小的 target 时，AoA 初值通常不会偏离真实转换关系过远。冷启动阶段假设结构近似静止，用于确定每个 target 的初始相位偏置 $b_i$，并将滤波状态初始化为：

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

这意味着在刚进入 Kalman 框架时，滤波器主要依赖加速度驱动的结构主相位预测，而不是完全相信由 AoA 初值构造的雷达观测模型。

当车辆或其他荷载从远处接近时，桥梁通常会先出现小幅可辨识振动。该阶段相位分支选择相对容易，同时又具有足够动态信息用于估计转换系数。由 Kalman 预测得到结构主相位 $\hat{\Theta}_k^-$ 后，第 $i$ 个 target 的 LoS 相位预测为：

$$
\hat{\phi}_{i,k}^-
=
\hat{\kappa}_{i,k}\hat{\Theta}_k^-+b_i.
$$

利用该预测值对原始 wrapped phase 进行分支校正：

$$
z_{i,k}^{\mathrm{corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{
\hat{\phi}_{i,k}^- - \psi_{i,k}
}{2\pi}
\right).
$$

在短窗口 $\mathcal{W}_{\beta}$ 内，可用校正后的连续相位与结构主相位估计递推修正 $\kappa_i$。文档早期版本采用未中心化 plain LS；当前暂定主方法改为中心化并加入 AoA 先验正则项，以降低冷启动偏置、微小振动均值漂移和局部相位偏置对斜率估计的影响。令：

$$
\tilde{\Theta}_k
=
\hat{\Theta}_k-\bar{\Theta},
\qquad
\tilde{z}_{i,k}
=
z_{i,k}^{\mathrm{corr}}-b_i-\bar{z}_i .
$$

则窗口更新写为：

$$
\hat{\kappa}_{i}
=
\frac{
\sum_{k\in\mathcal{W}_{\beta}}
\tilde{\Theta}_k\tilde{z}_{i,k}
+
\lambda_\kappa\hat{\kappa}_{i,0}
}{
\sum_{k\in\mathcal{W}_{\beta}}
\tilde{\Theta}_k^2
+
\lambda_\kappa
},
\qquad
\hat{\beta}_i=\frac{1}{\hat{\kappa}_i}.
$$

该估计只在窗口内结构主相位具有足够可辨识能量时更新；若振动过弱，则保持 AoA 初值或上一时刻估计值。随着前几次分支校正成功，$\hat{\beta}_i$ 会在短时间内从几何初值收敛到该 target 的等效转换系数。该过程不是先验完整解缠，而是由 AoA 初值、加速度预测和自适应测量噪声共同支撑的在线自举。

可定义窗口内转换系数拟合残差：

$$
e_{\beta,i}
=
\frac{
\left\|
\mathbf{z}_{i,\mathcal{W}}^{\mathrm{corr}}
-
b_i\mathbf{1}
-
\hat{\kappa}_i\hat{\boldsymbol{\Theta}}_{\mathcal{W}}
\right\|_2
}{
\left\|
\mathbf{z}_{i,\mathcal{W}}^{\mathrm{corr}}
-
b_i\mathbf{1}
\right\|_2
}.
$$

在第一版方法中，该残差主要用于描述和实验分析；滤波过程中的 target 权重由后文的自适应 $R_i$ 自动调节。即当 $\beta_i$ 尚未收敛或 target 相位质量较差时，其残差会增大，进而使对应观测噪声增大；当 $\beta_i$ 收敛后，对应 target 的观测权重自动恢复。

这一设计避免了“转换系数必须先由完整解缠相位标定”的死锁，同时保留了 Ma 等人预测辅助相位校正思想和 Doppler-based phase unwrapping 文献中的相位速度辅助分支选择思想。若雷达帧内包含多个 chirps，还可用同一 range-angle target 的 chirp 间相位差估计 LoS 相位变化率，作为 $\hat{\phi}_{i,k}^-$ 的辅助先验，但这不是闭环成立的必要条件。

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

由当前转换系数估计得到第 $i$ 个 target 的观测行：

$$
\mathbf{h}_{i,k}
=
\begin{bmatrix}
1/\hat{\beta}_{i,k} & 0
\end{bmatrix}.
$$

由预测主相位得到第 $i$ 个 target 的 LoS 相位预测：

$$
\hat{\phi}_{i,k}^-
=
\mathbf{h}_{i,k}\mathbf{x}_k^-+b_i.
$$

利用该预测值对 wrapped phase 进行分支校正：

$$
z_{i,k}^{\mathrm{corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{
\hat{\phi}_{i,k}^- - \psi_{i,k}
}{2\pi}
\right).
$$

将所有可用 target 的校正相位堆叠为观测向量：

$$
\mathbf{z}_k^{\mathrm{corr}}
=
\begin{bmatrix}
z_{1,k}^{\mathrm{corr}}\\
z_{2,k}^{\mathrm{corr}}\\
\vdots\\
z_{m,k}^{\mathrm{corr}}
\end{bmatrix}.
$$

观测矩阵为：

$$
\mathbf{H}_k=
\begin{bmatrix}
1/\hat{\beta}_{1,k} & 0\\
1/\hat{\beta}_{2,k} & 0\\
\vdots & \vdots\\
1/\hat{\beta}_{m,k} & 0
\end{bmatrix}.
$$

观测噪声协方差采用 target-wise 对角形式：

$$
\mathbf{R}_k
=
\operatorname{diag}
\left(
r_{1,k},r_{2,k},\ldots,r_{m,k}
\right).
$$

然后执行标准 Kalman 更新：

$$
\mathbf{K}_k
=
\mathbf{P}_k^-
\mathbf{H}_k^\mathrm{T}
\left(
\mathbf{H}_k\mathbf{P}_k^-\mathbf{H}_k^\mathrm{T}
+
\mathbf{R}_k
\right)^{-1},
$$

$$
\mathbf{x}_k
=
\mathbf{x}_k^-
+
\mathbf{K}_k
\left(
\mathbf{z}_k^{\mathrm{corr}}
-
\mathbf{H}_k\mathbf{x}_k^-
-
\mathbf{b}_k
\right).
$$

Kalman 更新后，当前主方法使用第 $i$ 个 target 的预测创新来更新基础测量噪声，而不是默认使用后验残差：

$$
e_{i,k}^-
=
z_{i,k}^{\mathrm{corr}}
-
\left(
\mathbf{h}_{i,k}\mathbf{x}_k^-+b_i
\right).
$$

参考 residual-based adaptive Kalman filtering，可用遗忘因子更新该 target 的测量噪声：

$$
\tilde{r}_{i,k}
=
{e_{i,k}^{-}}^2
+
\mathbf{h}_{i,k}\mathbf{P}_k\mathbf{h}_{i,k}^{\mathrm{T}},
$$

$$
r_{i,k+1}
=
\operatorname{clip}
\left[
\alpha r_{i,k}
+
(1-\alpha)\tilde{r}_{i,k},
\ r_{\min},
\ r_{\max}
\right],
$$

其中 $0<\alpha<1$ 为遗忘因子。初始阶段 $r_{i,0}$ 由 target 初始质量、SNR、presence 和几何投影等信息给出；低质量 target 会得到较大的初始测量噪声，高质量 target 可更早参与更新。随着转换系数和分支校正稳定，prediction innovation 减小，$r_{i,k}$ 自动下降，多 target 相位观测逐步恢复正常权重。针对 AoA cold start 阶段转换系数尚未收敛的问题，当前主方法将 $((\hat{\Theta}_k^-)^2+P_{\Theta\Theta,k}^-)\sigma_{\kappa_i,k}^2$ 作为观测模型不确定性加入有效测量噪声，从而使“转换系数越不确定，越降低观测权重”与在线 bootstrap 收敛过程对应起来。posterior residual 形式保留为代码消融候选，不作为论文主线展开。

## 8. 关键接口关系

为避免方法链条出现循环依赖，各模块接口应明确如下。

| 模块 | 输入 | 输出 | 是否依赖 Kalman 内部相位校正 |
|---|---|---|---|
| Range-Angle Map | ADC 原始数据 | 复数 range-angle map | 否 |
| target 选择 | range-angle map、加速度频带 | 可用 target 集合、wrapped phase | 否 |
| AoA 与冷启动初始化 | target AoA、静止初始相位 | $\beta_i^{(0)}$、$b_i$、较大的 $r_{i,0}$ | 否 |
| 转换系数自举更新 | Kalman 预测辅助校正相位、结构主相位估计 | $\hat{\beta}_{i,k}$、$e_{\beta,i}$、$S_{\beta,i}$ | 依赖已启动的 Kalman 递推，但不依赖预先完整解缠 |
| Kalman 融合 | wrapped phase、$\hat{\beta}_{i,k}$、加速度、confidence-aware effective $\mathbf{R}_k$ | 连续主相位、结构位移 | 是，在框架内部完成 |

因此，本文流程中不存在一套独立于 Kalman 的预处理式完整相位解缠。wrapped phase 的 $2\pi$ 分支选择在 Kalman 预测辅助相位校正步骤中在线完成，校正后的 $z_{i,k}^{\mathrm{corr}}$ 同时服务于观测更新和转换系数自举。转换系数不再要求由一段预先完整解缠的雷达相位单独标定，而是以 AoA 几何值启动，并在初始微振阶段借助加速度预测、基础测量噪声更新和转换系数置信度传播逐步收敛。这样，转换系数需要连续相位、连续相位校正又需要转换系数的循环依赖被打断。

## 9. 与三个创新点的对应关系

整体架构中的三个核心创新点对应关系如下：

1. **在线多 target 选择**：对应 Range-Angle Map、角度合并、滑动窗口稳定性确认和结构频带一致性筛选，解决“哪些环境散射体可作为参考 target”的问题。
2. **复合 target 等效转换系数稳定性**：对应 AoA 几何初始化、短窗口自举更新和稳定性评价，解释 angle cluster 或复合散射 target 何时可用一个稳定 $\beta_i$ 表示。
3. **结构主相位多 target Kalman 融合**：对应最终在线融合框架，将 Ma 等人的单目标 LoS 相位状态改写为结构振动方向主相位状态，并把多个 target wrapped phase 作为多通道观测共同更新；固定/标定 $Q$ 与 confidence-aware target-wise $R$ 共同完成初始自举和稳定融合。

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
