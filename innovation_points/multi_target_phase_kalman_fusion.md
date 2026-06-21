# 创新点：面向多静止参考目标的结构主相位 Kalman 融合框架

## 1. 方法背景与问题引入

倒挂式毫米波雷达位移监测中，雷达安装在结构测点上并随结构共同运动，周围环境中的地面、桥下构件、支架或其他静止散射体可作为参考目标。结构运动会引起雷达与这些静止参考目标之间的相对距离变化，从而反映在雷达回波相位中。对于任一稳定参考目标，若其视线方向位移与结构真实振动方向位移之间的转换关系已知，则可由该目标的相位变化恢复结构位移。

毫米波雷达相位测量具有很高的位移灵敏度，但原始相位由复数回波取主值得到，通常被限制在 $(-\pi,\pi]$ 范围内。当结构位移对应的相位变化超过一个相位周期时，原始相位会发生缠绕。因此，实际位移估计需要从 wrapped phase 中恢复连续相位。Ma 等人提出的 acceleration-aided Kalman filtering 框架将相位解缠与降噪统一在 Kalman 滤波递推中，利用加速度预测相位演化，并根据预测相位对雷达 wrapped phase 进行 $2\pi$ 分支校正，从而提高强噪声条件下的相位恢复稳定性。

本文参考 Ma 等人的 Kalman 相位融合思想，但针对倒挂式多目标参考场景对状态变量的物理含义和观测模型进行重新定义。Ma 等人的模型主要面向单一雷达目标，其状态相位表示该目标在雷达视线方向上的连续 LoS 相位；而在多目标倒挂式场景中，不同参考目标具有不同的视线方向和方向转换系数，若仍以某一个目标的 LoS 相位作为统一状态，则无法自然地同时兼容多个目标的相位观测。为解决该问题，本文将 Kalman 状态中的相位由单目标 LoS 相位改写为结构振动方向上的连续主相位，并将各个目标的 wrapped phase 作为该主相位的多通道投影观测。

## 2. Ma 等人单目标 LoS 相位模型的特点与局限

Ma 等人的 Kalman 框架将相位及其变化率作为状态变量。对于单一选定 target，可写为：

$$
\mathbf{x}_k^{\mathrm{Ma}}
=
\begin{bmatrix}
\phi_k\\
\dot{\phi}_k
\end{bmatrix},
$$

其中 $\phi_k$ 表示该 target 的连续 LoS 相位。这里的 $\phi_k$ 不是雷达直接输出的 $(-\pi,\pi]$ 主值相位，而是解缠后的完整相位，可在实数域内连续变化。雷达直接测得的是 wrapped phase：

$$
z_k=\operatorname{wrap}(\phi_k)+v_k.
$$

Kalman 预测得到 $\hat{\phi}_k^-$ 后，Ma 等人利用预测相位对当前 wrapped observation 进行分支校正：

$$
z_k^{\mathrm{corr}}
=
z_k
+
2\pi
\operatorname{round}
\left(
\frac{\hat{\phi}_k^- - z_k}{2\pi}
\right).
$$

随后，校正后的 $z_k^{\mathrm{corr}}$ 作为连续相位观测参与 Kalman 更新。该方法的关键在于：加速度提供了相位状态的动力学预测，预测值又为 wrapped phase 的分支选择提供了物理约束。

然而，该状态定义隐含了一个单目标前提。设结构在目标振动方向上的位移为 $q_k$，第 $i$ 个目标的 LoS 位移为 $d_{\mathrm{LOS},i,k}$，方向转换关系为：

$$
q_k=\beta_i d_{\mathrm{LOS},i,k},
$$

其中 $\beta_i$ 表示第 $i$ 个目标从 LoS 位移到结构振动方向位移的转换系数。则该目标的连续 LoS 相位为：

$$
\phi_{i,k}
=
\frac{4\pi}{\lambda}d_{\mathrm{LOS},i,k}
=
\frac{1}{\beta_i}
\frac{4\pi}{\lambda}q_k.
$$

在倒挂式布置中，LoS 距离变化与结构振动方向之间可能存在符号差异。为使后续表达简洁，本文可将该符号并入 $\beta_i$ 或其倒数 $1/\beta_i$ 中。因此，下文重点关注不同 target 之间转换比例的差异，而不单独展开符号约定。

因此，若状态变量定义为某一目标的 LoS 相位，则加速度 $a_k=\ddot{q}_k$ 必须先通过该目标的转换系数映射到对应的 LoS 相位加速度：

$$
\ddot{\phi}_{i,k}
=
\frac{4\pi}{\lambda}
\frac{1}{\beta_i}
a_k.
$$

这在单目标场景中是可行的，因为只有一个 $\beta_i$。但在多目标场景中，每个目标都有不同的 $\beta_i$。如果仍将状态定义为某一个目标的 LoS 相位，则其他目标的相位观测都需要再通过额外比例关系映射到该状态，不仅物理含义不直观，也会使相位解缠分支选择依赖某个特定目标。当该目标噪声较大、遮挡或临时失效时，整个滤波状态会受到不必要的约束。

因此，Ma 等人的 LoS 相位状态适合单目标相位解缠与降噪，但不天然适用于多参考目标的联合相位融合。多目标场景需要一个不依附于任何单一目标、同时能够被所有目标观测到的共享状态量。

## 3. 结构振动方向主相位的状态定义

为建立多目标统一融合模型，本文将状态变量中的相位重新定义为结构振动方向上的主相位。设结构测点沿目标振动方向的位移为 $q_k$，雷达波长为 $\lambda$，定义：

$$
\Theta_k
=
\frac{4\pi}{\lambda}q_k.
$$

其中 $\Theta_k$ 表示结构真实位移在相位域中的表达。与雷达原始相位不同，$\Theta_k$ 是解缠后的连续状态量，其取值范围为整个实数域。若结构振动方向为竖直方向，则 $\Theta_k$ 即为结构竖向位移对应的连续主相位。它不表示雷达到某一 target 的斜距相位，而表示结构振动方向位移 $q_k$ 的相位单位化表达：

$$
q_k
=
\frac{\lambda}{4\pi}\Theta_k.
$$

基于该定义，本文的 Kalman 状态向量写为：

$$
\mathbf{x}_k
=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix}.
$$

由于加速度计测得的加速度已位于结构振动方向上，因此它可直接用于主相位状态预测，而无需针对任何具体 target 进行方向转换。离散状态预测模型为：

$$
\mathbf{x}_k^-
=
\mathbf{A}\mathbf{x}_{k-1}
+
\mathbf{B}
\frac{4\pi}{\lambda}a_{k-1}
+
\mathbf{w}_{k-1},
$$

其中：

$$
\mathbf{A}
=
\begin{bmatrix}
1&T\\
0&1
\end{bmatrix},
\qquad
\mathbf{B}
=
\begin{bmatrix}
T^2/2\\
T
\end{bmatrix}.
$$

过程噪声 $\mathbf{w}_{k-1}$ 用于描述主相位动力学预测的不确定性。由于本文状态相位定义在结构振动方向，而不是某一 target 的 LoS 方向，因此过程噪声也应表示结构主相位预测误差，而不应随具体 target 改变。第一版方法中采用固定过程噪声协方差：

$$
\mathbf{w}_{k-1}\sim\mathcal{N}(\mathbf{0},\mathbf{Q}),
$$

$$
\mathbf{Q}
=
q
\begin{bmatrix}
T^3/3 & T^2/2\\
T^2/2 & T
\end{bmatrix},
$$

其中 $q$ 为主相位动力学噪声强度，$T$ 为采样间隔。该形式与常加速度状态模型相对应，表示未建模高阶运动、加速度测量噪声、传感器同步误差和模型预测误差对主相位及其变化率的影响。与 Ma 等人单目标 LoS 相位模型不同，本文的 $\mathbf{Q}$ 不包含 target 方向转换系数；不同 target 的转换关系和观测质量由后续观测矩阵 $\mathbf{H}_k$ 与观测噪声协方差 $\mathbf{R}_k$ 表达。

这一点是本文与 Ma 等人模型的第一个关键差异。Ma 等人的状态相位为单目标 LoS 相位，因此加速度输入需要通过目标转换系数进入状态预测；本文的状态相位为结构振动方向主相位，因此加速度可直接转换为主相位加速度。这一改写消除了状态预测对特定 target 的依赖，使滤波状态在多目标条件下具有统一物理意义。

## 4. 预测辅助相位校正与转换系数自举

本文不将转换系数估计建立在预先完成的全时程相位解缠之上。经过 range-angle target 选择后，进入 Kalman 框架的仍是各 target 的原始 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k),
\qquad
\psi_{i,k}\in(-\pi,\pi].
$$

因此，转换系数计算所需的连续相位不能直接由 $\psi_{i,k}$ 给出，而必须由当前滤波预测进行分支校正。本文首先利用 range-angle bin 的 AoA 几何关系给出可启动初值：

$$
\hat{\kappa}_{i,0}=\cos\theta_i,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\hat{\kappa}_{i,0}},
\qquad
\kappa_i=\frac{1}{\beta_i}.
$$

冷启动阶段结构近似静止，用于确定每个 target 的初始相位偏置 $b_i$，并将对应 target 的测量噪声初始化为较大值，使滤波器在初始阶段主要依赖加速度预测模型。该 AoA 初值不要求精确等于真实转换系数，只需为初始微振阶段提供可用的相位分支预测。

在第 $k$ 个时刻，先由当前转换系数估计构造观测行：

$$
\mathbf{h}_{i,k}
=
\begin{bmatrix}
1/\hat{\beta}_{i,k} & 0
\end{bmatrix}
=
\begin{bmatrix}
\hat{\kappa}_{i,k} & 0
\end{bmatrix}.
$$

由 Kalman 系统模型得到结构主相位先验状态 $\mathbf{x}_k^-$ 后，可先预测第 $i$ 个 target 的 LoS 相位分支：

$$
\hat{\phi}_{i,k}^-
=
\mathbf{h}_{i,k}\mathbf{x}_k^-+b_i.
$$

随后，对原始 wrapped phase 进行预测辅助相位校正：

$$
z_{i,k}^{\mathrm{corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{\hat{\phi}_{i,k}^- - \psi_{i,k}}{2\pi}
\right).
$$

这里的 $z_{i,k}^{\mathrm{corr}}$ 是由 Kalman 预测模型给出的局部连续相位观测。它不是进入 Kalman 前预先完成的全局解缠结果，也不是转换系数模块额外执行的一套独立解缠流程，而是在每个时刻由同一预测模型生成、并被后续模块共同使用的校正相位。

因此，本文将相位校正步骤前置到观测更新和转换系数更新之前。得到 $z_{i,k}^{\mathrm{corr}}$ 后，它同时进入两条路径。第一条路径是作为 Kalman 观测更新的连续相位观测；第二条路径是在短窗口 $\mathcal{W}_{\beta}$ 内用于转换系数自举。文档早期版本可写成未中心化的 plain LS；当前暂定主方法采用中心化并带 AoA 先验约束的窗口 LS。令：

$$
\tilde{\Theta}_{\tau}
=
\hat{\Theta}_{\tau}-\bar{\Theta},
\qquad
\tilde{z}_{i,\tau}
=
z_{i,\tau}^{\mathrm{corr}}-b_i-\bar{z}_i,
$$

则：

$$
\hat{\kappa}_{i,k+1}
=
\frac{
\sum_{\tau\in\mathcal{W}_{\beta}}
\tilde{\Theta}_{\tau}\tilde{z}_{i,\tau}
+
\lambda_\kappa \hat{\kappa}_{i,0}
}{
\sum_{\tau\in\mathcal{W}_{\beta}}
\tilde{\Theta}_{\tau}^{2}
+
\lambda_\kappa
},
\qquad
\hat{\beta}_{i,k+1}
=
\frac{1}{\hat{\kappa}_{i,k+1}}.
$$

该设计避免了“先完整解缠相位才能估计转换系数、而 Kalman 解缠又需要转换系数”的循环依赖。实际运行时，AoA 初值使滤波器能够在冷启动后开始工作；初始微小振动到来时，预测辅助相位校正产生局部连续的 $z_{i,k}^{\mathrm{corr}}$；随着短窗口最小二乘逐步修正 $\hat{\beta}_{i,k}$，观测矩阵 $\mathbf{H}_k$ 和 LoS 相位预测同步改善，进一步增强后续分支选择的稳定性。

该步骤继承了 Ma 等人利用预测相位辅助解缠的思想，但预测相位的来源和作用范围发生了变化。Ma 等人使用单目标自身 LoS 相位预测来校正同一目标的 wrapped phase；本文则使用共享结构主相位预测，并通过各目标的转换系数映射到对应 LoS 相位分支，从而分别辅助多个 target 的 wrapped phase 校正。这样，任一 target 的分支选择都受到同一结构运动状态约束，而不依赖某个单一 target 的相位历史。

## 5. 多目标相位观测更新模型

完成预测辅助相位校正后，当前时刻所有可用 target 的校正相位观测可共同参与 Kalman 更新。设当前时刻通过目标选择、相位质量评价和创新检验的可用目标集合为：

$$
\mathcal{A}_k=\{i_1,i_2,\ldots,i_{m_k}\},
$$

其中 $m_k=|\mathcal{A}_k|$ 为可用目标数量。将各目标的校正相位组成观测向量：

$$
\mathbf{z}_k^{\mathrm{corr}}
=
\begin{bmatrix}
z_{i_1,k}^{\mathrm{corr}}\\
z_{i_2,k}^{\mathrm{corr}}\\
\vdots\\
z_{i_{m_k},k}^{\mathrm{corr}}
\end{bmatrix}.
$$

对应的线性观测模型为：

$$
\mathbf{z}_k^{\mathrm{corr}}
=
\mathbf{H}_k\mathbf{x}_k
+
\mathbf{b}_k
+
\mathbf{v}_k,
$$

其中：

$$
\mathbf{H}_k
=
\begin{bmatrix}
1/\hat{\beta}_{i_1,k} & 0\\
1/\hat{\beta}_{i_2,k} & 0\\
\vdots & \vdots\\
1/\hat{\beta}_{i_{m_k},k} & 0
\end{bmatrix},
\qquad
\mathbf{b}_k
=
\begin{bmatrix}
b_{i_1}\\
b_{i_2}\\
\vdots\\
b_{i_{m_k}}
\end{bmatrix}.
$$

若使用相对相位，则 $\mathbf{b}_k$ 可省略。Kalman 更新为：

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
\right),
$$

$$
\mathbf{P}_k
=
\left(
\mathbf{I}
-
\mathbf{K}_k\mathbf{H}_k
\right)
\mathbf{P}_k^-.
$$

这一更新模型是本文与 Ma 等人模型的第二个关键差异。Ma 等人的观测矩阵为单行矩阵 $[1,0]$，表示单个 target 的校正 LoS 相位直接观测状态相位；本文的观测矩阵由多个 target 的转换系数组成，每个 target 只观测结构主相位在其 LoS 方向上的投影。由此，多个 target 不再是独立估计位移后再进行平均，而是在相位域内作为同一结构状态的多通道观测共同参与滤波更新。

该处理具有三个直接优势。第一，滤波状态不依赖任何单一目标，当某个 target 噪声升高或临时失效时，只需从 $\mathcal{A}_k$ 中移除该观测，状态仍可由其他 target 和加速度维持。第二，不同 target 的方向转换系数被显式保留在观测矩阵中，避免了先将各目标相位转换为位移再平均时对转换误差和相位分支误差的掩盖。第三，多目标观测共同约束同一主相位状态，可在相位解缠阶段利用目标间冗余性抑制单目标误判造成的分支跳变。

## 6. 目标可靠性与观测噪声建模

在多目标融合中，不同 target 的相位质量通常并不相同。目标幅值、信噪比、IQ 轨迹规则性、同 rangeBin 复合散射稳定性、转换系数标定误差和短时遮挡都会影响其观测可信度。因此，本文可将观测噪声协方差写为随时间变化的矩阵：

$$
\mathbf{R}_k
=
\operatorname{cov}(\mathbf{v}_k).
$$

最简单情形下，可令 $\mathbf{R}_k$ 为对角矩阵：

$$
\mathbf{R}_k
=
\operatorname{diag}
\left(
R_{1,k},R_{2,k},\ldots,R_{m_k,k}
\right),
$$

其中 $R_{i,k}$ 表示第 $i$ 个 target 当前相位观测的不确定度。

本文主方法采用固定/标定 $\mathbf{Q}$ 与 confidence-aware target-wise effective $\mathbf{R}_k$ 的分工。也就是说，$\mathbf{Q}$ 表示结构主相位动力学预测误差，主要由加速度传感器噪声、同步误差和状态模型未建模项决定，属于全局标定参数；$\mathbf{R}_k$ 表示 radar target 相位观测误差与转换系数不确定性共同形成的等效观测噪声，受目标 SNR、遮挡、复合散射、AoA/转换系数误差和短时观测条件影响，更适合作为在线估计对象。桥梁 acceleration+strain displacement estimation 的相关工作也采用类似分工：过程噪声可依据传感器或模型误差预先给定，而测量噪声随观测条件变化进行自适应估计。

在当前仿真实现中，$\mathbf{Q}$ 的标定采用候选网格而不是单个硬编码常数。具体地，对候选 $q \in \mathcal{Q}$ 分别运行相同的结构主相位 Kalman 滤波器，并以目标级 prediction innovation energy 作为无真值标定准则：

$$
q^\star
=\arg\min_{q\in\mathcal{Q}}
\frac{1}{|\Omega|}
\sum_{(i,k)\in\Omega}
{e_{i,k}^{-}}^2,
\qquad
\mathbf{Q}=q^\star\mathbf{Q}_0.
$$

该过程只使用算法可见的 wrapped phase、measured acceleration、selected targets、初始 $\hat{\beta}_i$ 和自适应 $\mathbf{R}_k$，不使用真实位移或真值 RMSE。选定 $q^\star$ 后，在线滤波过程中 $\mathbf{Q}$ 保持不变；因此它仍属于固定/标定 $\mathbf{Q}$ 策略，而不是逐时刻 adaptive $\mathbf{Q}_k$。

为使初始阶段的 AoA 转换系数误差和低 SNR target 不会被滤波器过度信任，本文令每个 target 的测量噪声初值由目标初始质量给出。若可获得初始 SNR 或 range-angle peak quality，可写为：

$$
R_{i,0}
=
\operatorname{clip}
\left[
g(\mathrm{SNR}_{i,0}),
\ R_{\min},
\ R_{\max}
\right],
$$

其中 $g(\cdot)$ 为随 SNR 增大而下降的单调映射。若缺少可靠 SNR 估计，则可退化为保守的大初值：

$$
R_{i,0}=R_{\max}.
$$

Kalman 更新后，主方法先采用预测创新更新第 $i$ 个 target 的基础测量噪声：

$$
e_{i,k}^{-}
=
z_{i,k}^{\mathrm{corr}}
-
\left(
\mathbf{h}_{i,k}\mathbf{x}_k^-+b_i
\right),
\qquad
\mathbf{h}_{i,k}=
\begin{bmatrix}
1/\hat{\beta}_{i,k}&0
\end{bmatrix}.
$$

参考 Mehra 的 innovation/covariance matching 思想、Mohamed-Schwarz 的 measurement noise covariance estimation、Li 等人在 INS-GNSS 多观测通道中的自适应测量噪声处理，以及 Sage-Husa radar tracking 中对噪声协方差在线估计和鲁棒约束的使用，可得到该 target 的瞬时测量噪声估计：

$$
\tilde{R}_{i,k}
=
{e_{i,k}^{-}}^2
+
\mathbf{h}_{i,k}\mathbf{P}_k\mathbf{h}_{i,k}^{\mathrm{T}}.
$$

然后用遗忘因子平滑并进行上下限约束：

$$
R_{i,k+1}
=
\operatorname{clip}
\left[
\alpha R_{i,k}
+
(1-\alpha)\tilde{R}_{i,k},
\ R_{\min},
\ R_{\max}
\right],
\qquad
0<\alpha<1.
$$

该基础更新机制使滤波器在 target SNR 下降或相位残差异常时自动降低对应 target 的观测权重；随着预测辅助相位校正稳定，prediction innovation 减小，$R_{i,k}$ 随之下降，radar 相位观测以正常权重参与多目标融合。上下限 clipping 的作用不是人为修饰结果，而是防止单帧异常残差导致测量噪声估计发散或退化为零，从而维持 Kalman 增益的数值稳定性和鲁棒性。

需要说明的是，posterior residual

$$
e_{i,k}^{+}
=
z_{i,k}^{\mathrm{corr}}
-
\left(
\mathbf{h}_{i,k}\mathbf{x}_k+b_i
\right)
$$

也可用于构造 adaptive $R$。当前仿真消融表明，posterior residual 在 strong wrapping、vehicle event 和 same range far angles 等预测误差主导场景中可降低 RMSE；但在 mixed scatterer 和半实测桥梁场景中，它可能由于 Kalman 更新已吸收污染观测而低估测量噪声，并进一步影响 $q^\star$ 的选择。因此，本文采用 prediction-innovation 作为基础 $R$ 的更新残差口径，posterior-residual adaptive $R$ 仅作为代码消融候选和后续 R 机制讨论对象。

由于本文的完整链路以 AoA 结果作为转换系数初值，冷启动阶段 $\kappa_i$ 尚未完全由相位数据自举收敛。为避免此时过度信任观测模型，主方法将转换系数不确定性传播到等效观测噪声中：

$$
R_{i,k}^{\mathrm{eff}}
=
\sigma_{\phi_i,k}^2
+
\left[
(\hat{\Theta}_k^-)^2
+
P_{\Theta\Theta,k}^-
\right]
\sigma_{\kappa_i,k}^2,
\qquad
\kappa_i=\frac{1}{\beta_i}.
$$

其中 $\sigma_{\phi_i,k}^2$ 表示第 $i$ 个 target 的基础相位测量噪声，$\sigma_{\kappa_i,k}^2$ 表示转换系数倒数的不确定度，$P_{\Theta\Theta,k}^-$ 为预测主相位方差。该式说明，转换系数误差会随结构主相位幅值及状态不确定度放大，并最终表现为观测模型误差。这一点与本文前述复合 target 等效转换系数稳定性分析一致。实现上，基础 $R_{i,k}$ 仍由 target 质量和 prediction innovation 更新，额外的 $\kappa_i$ 置信度项只用于描述 AoA cold start 至短窗口自举收敛过程中的观测方程不确定性。该处理是为了支撑本文的 AoA cold start 与在线转换系数自举，并不作为独立创新点展开。

进一步地，若多个 target 来自同一 rangeBin 或同一分离过程，其相位误差可能存在相关性。此时不宜简单假设所有 target 观测相互独立，否则会因为观测数量增加而使 Kalman 过度自信。可将 $\mathbf{R}_k$ 写成：

$$
\mathbf{R}_k
=
\operatorname{diag}
\left(
\sigma_{1,k}^2,\ldots,\sigma_{m_k,k}^2
\right)
+
\sigma_{c,k}^2\mathbf{1}\mathbf{1}^{\mathrm{T}},
$$

其中 $\sigma_{c,k}^2$ 表示同源 target 之间的公共误差项。该建模使多目标融合能够利用冗余观测，同时避免将高度相关的相位信息误认为多个完全独立的测量。

## 7. 与 Ma 等人框架的关系和改进点

本文方法并非脱离 Ma 等人框架重新构造一套滤波器，而是在其 acceleration-aided phase denoising and unwrapping 思想上进行多目标化扩展。二者的共同点在于：均将相位及其变化率作为 Kalman 状态，均利用加速度进行相位预测，均通过预测相位对 wrapped phase 进行分支校正，并通过 Kalman 更新实现相位降噪。

本文的主要改进在于状态相位的物理含义和观测组织方式发生变化。Ma 等人将状态相位定义为单一目标的 LoS 连续相位，因此加速度输入需要根据该目标方向转换系数映射到 LoS 相位域，观测模型也只对应一个 target。本文将状态相位定义为结构振动方向主相位，使加速度可以直接参与状态预测；各 target 的方向转换关系则被移入观测模型，通过 $1/\beta_i$ 连接主相位和目标 LoS 相位。这样，多目标差异不再体现在多个互不兼容的状态定义中，而是体现在同一共享状态下的多行观测矩阵中。

这种改写解决了 Ma 单目标框架在多目标倒挂式监测中的三个问题。第一，不同 target 具有不同转换系数，单一 LoS 相位状态无法同时作为所有 target 的自然状态；本文通过主相位状态避免了该矛盾。第二，单目标状态对目标遮挡和相位噪声敏感；本文允许观测集合 $\mathcal{A}_k$ 随时间动态变化，使可靠 target 进入更新、不可靠 target 被降权或剔除。第三，单目标模型只能利用一个 wrapped phase 进行分支校正；本文利用共享主相位预测分别校正多个 target 的 wrapped phase，并将得到的 $z_{i,k}^{\mathrm{corr}}$ 同时用于 Kalman 观测更新和转换系数最小二乘自举，从而提高解缠、降噪和转换系数收敛的闭环稳定性。

因此，本文方法可概括为：以结构振动方向主相位为共享状态，以加速度为状态预测输入，利用当前预测状态提前对多 target wrapped phase 进行分支校正，并将统一得到的 $z_{i,k}^{\mathrm{corr}}$ 同时作为 Kalman 观测更新和转换系数自举更新的输入，在相位域内完成多参考目标的闭环融合。最终，滤波得到的主相位可直接转换为结构位移：

$$
\hat{q}_k
=
\frac{\lambda}{4\pi}
\hat{\Theta}_k.
$$

## 8. 固定过程噪声协方差的第一版实现

在上述框架下，状态定义、预测模型、wrapped phase 校正方式和多目标观测模型已经确定。第一版方法不引入在线自适应过程噪声，而采用固定 $\mathbf{Q}$ 的 Kalman 滤波实现。这样做的原因有两点。

第一，Ma 2026 的参数选择强调 Kalman 滤波效果主要受过程噪声 $Q$ 与测量噪声 $R$ 的相对权重影响；其做法是在固定 $R=1$ 的条件下遍历 $Q=10^j$，并以初始或标定数据段上的指标选择候选值。该过程本质上属于离线/初始段标定，而不是连续运行阶段的在线 adaptive $Q$。因此，采用固定/标定过程噪声协方差与 Ma 等人的实际滤波使用方式一致，并不会改变 acceleration-aided Kalman phase unwrapping 的基本逻辑。

第二，本文的主要创新在于将状态相位由单目标 LoS 相位改为结构振动方向主相位，并将多个 target 的 wrapped phase 组织为同一主相位状态的多通道观测。若同时引入复杂的在线 $\mathbf{Q}_k$ 自适应机制，容易使方法贡献分散。固定 $\mathbf{Q}$ 能够使模型结构更清晰，也便于通过实验单独验证多目标主相位融合相对于单目标 Ma 框架和后处理平均方法的改进。

具体实现时，令：

$$
\mathbf{Q}(q)
=
q\mathbf{Q}_0,
\qquad
\mathbf{Q}_0
=
\begin{bmatrix}
T^3/3 & T^2/2\\
T^2/2 & T
\end{bmatrix}.
$$

其中 $q$ 是唯一需要选择的过程噪声强度参数。该参数可通过初始标定段或实验验证段进行候选值遍历，选定后在连续估计过程中保持不变：

$$
q^\star
=
\arg\min_{q\in\mathcal{Q}}
J(q),
\qquad
\mathbf{Q}
=
\mathbf{Q}(q^\star).
$$

若存在 LDV、位移台或其他参考位移，可令 $J(q)$ 为估计位移与参考位移之间的 RMSE。若不存在外部参考，则可采用多目标相位一致性、解缠异常次数或 innovation 能量作为选择准则。例如，可将各 target 校正后的 LoS 相位反算为主相位观测：

$$
\tilde{\Theta}_{i,k}
=
\beta_i z_{i,k}^{\mathrm{corr}},
$$

并定义多目标一致性代价：

$$
J(q)
=
\sum_k
\sum_{i\in\mathcal{A}_k}
\rho_{i,k}
\left(
\tilde{\Theta}_{i,k}
-
\hat{\Theta}_k(q)
\right)^2,
$$

其中 $\rho_{i,k}$ 表示第 $i$ 个 target 在时刻 $k$ 的可靠性权重。实际实验中，也可将上述一致性代价与分支跳变异常次数或归一化 innovation 超限次数共同作为 $q$ 的选择依据。

因此，本文第一版采用 fixed/calibrated $\mathbf{Q}$，并将过程噪声选择问题简化为单一标量 $q$ 的离线标定或遍历选择问题。该处理既保持了 Ma 等人 Kalman 框架的可比性，又避免了在主创新之外引入额外复杂度。与之相对，在线阶段的主要自适应量为 target-wise $R_{i,k}$，用于反映不同参考目标观测质量的时间变化。

## 9. Ma 等人过程噪声标定方法与滑动窗口自适应扩展

Ma 等人对过程噪声参数的处理可概括为离线候选遍历。其基本出发点是：Kalman 滤波结果主要由过程噪声 $Q$ 与观测噪声 $R$ 的相对比例决定，因此可固定其中一个参数，只调节另一个参数。Ma 等人固定 $R=1$，将 $Q$ 作为待优化参数。

在其单目标 LoS 相位模型中，$Q$ 过大表示滤波器更相信雷达相位观测。此时高频相位噪声难以被抑制，噪声可能触发错误的 $2\pi$ 分支校正。相反，$Q$ 过小表示滤波器过度相信由加速度给出的预测，无法及时修正模型误差和低频偏差，也可能导致相位解缠失败或长期漂移。由于 Kalman 递推具有时间累积特性，一旦某一时刻发生错误分支选择，误差会继续传播到后续状态。因此，Ma 等人将解缠后相位能量作为相位恢复稳定性的量化指标：

$$
E(Q_i)
=
\frac{1}{N}
\sum_{k=1}^{N}
\left[
z_k^{\mathrm{corr}}(Q_i)
\right]^2,
$$

并通过候选值遍历确定：

$$
Q_{\mathrm{opt}}
=
\arg\min_{Q_i}E(Q_i).
$$

在其实验中，候选值可取 $Q_i=10^j$，并在初始数据段上完成选择。选定后，该 $Q_{\mathrm{opt}}$ 在后续连续监测中保持不变。因此，Ma 等人的方法虽然称为噪声参数优化，但其实质是一次性离线标定，而非在线自适应过程噪声估计。

对于本文的多目标结构主相位模型，Ma 的能量最小化思想可作为固定 $q$ 的基线选择方法，但不宜直接作为在线自适应准则。原因在于，本文状态 $\Theta_k$ 表示结构振动方向主相位，其能量大小不仅受解缠错误影响，也受真实结构振动幅值影响。如果在滑动窗口内直接最小化 $\sum \hat{\Theta}_k^2$ 或 $\sum (z_{i,k}^{\mathrm{corr}})^2$，可能会把真实大幅振动误判为不稳定估计，从而倾向于选择过小或过强约束的过程噪声。另一方面，本文已有多个 target 的相位观测，过程噪声选择不应只依赖单通道相位能量，而应利用多目标之间的一致性和 Kalman innovation 统计量。

因此，若后续希望在第一版固定 $\mathbf{Q}$ 的基础上进一步提高鲁棒性，可将滑动窗口自适应 $q$ 作为展望研究，而不纳入当前主方法。设滑动窗口为 $\mathcal{W}_t$，在窗口内对候选过程噪声强度 $q_j$ 运行或局部重放滤波递推，构造代价函数：

$$
J_{\mathcal{W}_t}(q_j)
=
J_{\mathrm{innov}}(q_j)
+
\mu J_{\mathrm{cons}}(q_j)
+
\nu J_{\mathrm{wrap}}(q_j).
$$

其中 $J_{\mathrm{innov}}$ 表示窗口内 Kalman innovation 能量，$J_{\mathrm{cons}}$ 表示多目标主相位一致性误差，$J_{\mathrm{wrap}}$ 表示异常分支校正惩罚，$\mu$ 和 $\nu$ 为权重系数。

具体地，令窗口内第 $k$ 帧的 innovation 为：

$$
\mathbf{r}_k
=
\mathbf{z}_k^{\mathrm{corr}}
-
\mathbf{H}_k\mathbf{x}_k^-
-
\mathbf{b}_k,
$$

其理论协方差为：

$$
\mathbf{S}_k
=
\mathbf{H}_k\mathbf{P}_k^-\mathbf{H}_k^\mathrm{T}
+
\mathbf{R}_k.
$$

则可定义归一化 innovation 能量：

$$
J_{\mathrm{innov}}(q_j)
=
\sum_{k\in\mathcal{W}_t}
\mathbf{r}_k^\mathrm{T}
\mathbf{S}_k^{-1}
\mathbf{r}_k.
$$

若 $\mathbf{R}_k$ 设定合理，则该量可反映预测模型与多目标观测之间的统计一致性。当窗口内归一化 innovation 长期偏大时，说明状态预测误差可能被低估，可适当增大 $q$；当其长期偏小时，则说明过程噪声可能偏大或观测噪声被高估，可适当减小 $q$。实际实现中，应先通过 target gating 剔除明显异常观测，避免将遮挡、错误分支或低质量 target 误解释为过程噪声增大。

多目标一致性项可写为：

$$
J_{\mathrm{cons}}(q_j)
=
\sum_{k\in\mathcal{W}_t}
\sum_{i\in\mathcal{A}_k}
\rho_{i,k}
\left(
\beta_i
\left(
z_{i,k}^{\mathrm{corr}}-b_i
\right)
-
\hat{\Theta}_k
\right)^2.
$$

该项利用各 target 经转换系数反算得到的主相位观测，与滤波得到的共享主相位进行比较。如果某个 $q_j$ 导致不同 target 对主相位的解释更一致，则说明该过程噪声强度更适合当前窗口的结构运动和观测质量。

异常分支惩罚项可根据分支校正整数构造。设：

$$
n_{i,k}
=
\operatorname{round}
\left(
\frac{
\hat{\phi}_{i,k}^- - z_{i,k}
}{2\pi}
\right),
$$

则可将窗口内异常大分支跳变或频繁分支变化计入：

$$
J_{\mathrm{wrap}}(q_j)
=
\sum_{k\in\mathcal{W}_t}
\sum_{i\in\mathcal{A}_k}
\mathbb{I}
\left(
|n_{i,k}-n_{i,k-1}|>\tau_n
\right),
$$

其中 $\mathbb{I}(\cdot)$ 为指示函数，$\tau_n$ 为允许的分支变化阈值。该项用于抑制由过大或过小 $q$ 导致的不稳定分支选择。

基于上述窗口代价，可得到半在线自适应过程噪声：

$$
q_t^\star
=
\arg\min_{q_j\in\mathcal{Q}_{\mathrm{local}}}
J_{\mathcal{W}_t}(q_j),
\qquad
\mathbf{Q}_t
=
\mathbf{Q}(q_t^\star).
$$

为避免 $\mathbf{Q}_t$ 在相邻窗口之间剧烈变化，可在对数域进行平滑更新：

$$
\log q_t
=
(1-\eta_q)\log q_{t-1}
+
\eta_q\log q_t^\star,
$$

其中 $\eta_q\in(0,1]$ 为更新步长。这样，$q_t$ 只随窗口统计特性缓慢变化，而不会在单帧异常观测下突然改变。

综上，本文主算法不采用 $Q$ 与 $R$ 同时在线自适应的表述，而采用 calibrated $\mathbf{Q}$ + SNR-informed initial $R_{i,0}$ + confidence-aware target-wise online $R_{i,k}^{\mathrm{eff}}$ 的分工。固定/标定 $\mathbf{Q}$ 保持结构主相位动力学模型的统计尺度，在线 $R_{i,k}^{\mathrm{eff}}$ 则吸收目标观测质量和 AoA cold start 转换系数不确定性随时间变化带来的影响。滑动窗口自适应 $q$ 仅作为进一步提高方案或展望。与 Ma 的单目标相位能量最小化相比，该扩展若在未来引入，也应利用多目标 innovation、一致性和分支稳定性，而不是仅依赖单一相位序列的能量大小。
