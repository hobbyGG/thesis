# Kalman 融合流程图预览

> 说明：该文件仅保留为流程图草稿预览，不是当前正式方法文档。当前最新版整体流程以 [overall_processing_architecture.md](/Users/umep/thesis/idea/overall_processing_architecture.md) 为准。

下面是“去公式化节点 + 图下公式”的版本。图中只保留模块关系和变量流向，不在 Mermaid 节点中写下标、上标或长公式；完整数学表达放在图后，由 Obsidian 原生 LaTeX 渲染。

```mermaid
flowchart TD
    A["Range-Angle Map"] --> B["二维峰值检测"]
    B --> C1["Target 1"]
    B --> C2["Target 2"]
    B --> Cm["Target m"]

    C1 --> D["角度合并与滑动窗口稳定性确认"]
    C2 --> D
    Cm --> D

    D --> E["结构频带一致性筛选"]
    ACC["同步加速度"] --> E

    E --> F1["Target 1<br/>wrapped phase / AoA / phase offset"]
    E --> F2["Target 2<br/>wrapped phase / AoA / phase offset"]
    E --> Fm["Target m<br/>wrapped phase / AoA / phase offset"]

    F1 --> INIT["AoA 冷启动<br/>转换系数初值 / 偏置 / 初始测量噪声"]
    F2 --> INIT
    Fm --> INIT

    ACC --> PRED["系统模型预测<br/>结构主相位先验"]
    INIT --> PRED
    XOUT["上一时刻后验状态"] --> PRED

    PRED --> U1["Target 1<br/>预测辅助相位校正"]
    PRED --> U2["Target 2<br/>预测辅助相位校正"]
    PRED --> Um["Target m<br/>预测辅助相位校正"]

    F1 --> U1
    F2 --> U2
    Fm --> Um

    U1 -- "观测行 + 校正相位" --> OBS["多目标观测模型<br/>校正相位 / 观测矩阵 / 测量噪声"]
    U2 -- "观测行 + 校正相位" --> OBS
    Um -- "观测行 + 校正相位" --> OBS

    OBS --> KF["Kalman 更新<br/>phase estimation / denoise"]
    KF --> XEST["结构主相位后验估计<br/>相位 + 相位变化率"]
    XEST --> DISP["结构振动方向位移"]

    U1 -- "校正相位" --> BETA["转换系数短窗口自举<br/>更新各 target 转换系数"]
    U2 -- "校正相位" --> BETA
    Um -- "校正相位" --> BETA
    XEST -- "结构主相位" --> BETA
    BETA -- "更新 H 与下一步解缠预测" --> OBS
    BETA --> U1
    BETA --> U2
    BETA --> Um

    KF --> RADAPT["target-wise adaptive R"]
    RADAPT -- "更新测量噪声" --> OBS
    XEST -- "进入下一时刻" --> XOUT
```

## 图中关键公式

结构主相位状态定义为：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix},
\qquad
\Theta_k=\frac{4\pi}{\lambda}q_k.
$$

系统模型由加速度直接预测结构主相位：

$$
\mathbf{x}_k^-=
\mathbf{A}\mathbf{x}_{k-1}
+
\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}.
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

第 $i$ 个 target 的观测行和 LoS 相位预测为：

$$
\mathbf{h}_{i,k}
=
\begin{bmatrix}
1/\hat{\beta}_{i,k}&0
\end{bmatrix},
\qquad
\hat{\phi}_{i,k}^-
=
\mathbf{h}_{i,k}\mathbf{x}_k^-+b_i.
$$

利用预测 LoS 相位对 wrapped phase 进行分支校正：

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

多目标校正相位堆叠为观测向量：

$$
\mathbf{z}_k^{\mathrm{corr}}
=
\begin{bmatrix}
z_{1,k}^{\mathrm{corr}}\\
z_{2,k}^{\mathrm{corr}}\\
\vdots\\
z_{m,k}^{\mathrm{corr}}
\end{bmatrix},
\qquad
\mathbf{H}_k
=
\begin{bmatrix}
1/\hat{\beta}_{1,k}&0\\
1/\hat{\beta}_{2,k}&0\\
\vdots&\vdots\\
1/\hat{\beta}_{m,k}&0
\end{bmatrix}.
$$

因此观测模型为：

$$
\mathbf{z}_k^{\mathrm{corr}}
=
\mathbf{H}_k\mathbf{x}_k
+
\mathbf{b}_k
+
\mathbf{v}_k.
$$

校正相位同时用于转换系数短窗口自举：

$$
\hat{\kappa}_{i}
=
\frac{
\sum_{k\in\mathcal{W}_{\beta}}
\hat{\Theta}_k
\left(
z_{i,k}^{\mathrm{corr}}-b_i
\right)
}{
\sum_{k\in\mathcal{W}_{\beta}}
\hat{\Theta}_k^2
},
\qquad
\hat{\beta}_i=\frac{1}{\hat{\kappa}_i}.
$$

target-wise 测量噪声由后验残差和 target quality gate 自适应更新：

$$
s_{i,k}
=
z_{i,k}^{\mathrm{corr}}
-
\left(
\mathbf{h}_{i,k}\mathbf{x}_k+b_i
\right),
$$

$$
\Delta r_{i,k}
=
\left(
s_{i,k}^2
+
\mathbf{h}_{i,k}\mathbf{P}_k^+\mathbf{h}_{i,k}^{\mathrm{T}}
\right)
-
r_{i,k},
\qquad
g_{i,k}
=
\begin{cases}
1-\rho_{i,k}, & \Delta r_{i,k}>0,\\
1, & \Delta r_{i,k}\le 0.
\end{cases}
$$

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
\right].
$$

最终位移由结构主相位恢复：

$$
\hat{q}_k
=
\frac{\lambda}{4\pi}\hat{\Theta}_k.
$$
