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

在倒挂式布置中，LoS 距离变化与结构振动方向之间可能存在符号差异。为使后续表达简洁，本文将符号约定并入 $\beta_i$ 或相位偏置 $b_i$ 的定义中。因此，下文重点关注不同 target 之间转换比例的差异，而不单独展开符号约定。

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

## 4. Kalman 前独立转换系数预校准与在线相位校正

经过 range-angle target 选择后，算法首先保留各 target 的原始 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k),
\qquad
\psi_{i,k}\in(-\pi,\pi].
$$

本文沿用 Ma 等人的方向定义，将 $\beta_i$ 定义为 LoS 位移/相位到结构真实振动方向位移/主相位的转换系数：

$$
q_k=\beta_i d_{\mathrm{LOS},i,k},
\qquad
\Theta_k=\beta_i\phi_{i,k}^{\mathrm{LOS}}.
$$

本文首先利用 range-angle bin 的 AoA 几何关系给出原始初值。若第 $i$ 个 target 的 AoA 与结构振动方向夹角为 $\theta_i$，先计算结构方向到 LoS 的投影初值 $p_i$，再取其倒数作为 LoS 到结构方向的转换系数初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

AoA 之后、正式 Kalman 之前执行一次独立批量预校准。公共角度偏差 $\delta$ 仍可作为安装偏差的辅助候选：

$$
p_i(\delta)=\cos(\hat{\theta}_i-\delta),
\qquad
\beta_i(\delta)=\frac{1}{|p_i(\delta)|}.
$$

给定 $\delta$ 时，每个时刻用加权最小二乘估计所有 target 共享的 $\Theta_k$，再最小化跨 target 残差得到公共角候选。该参数只能修正公共安装偏差，不能表示各 target 由 angle-bin 量化、旁瓣或多径造成的不同 AoA 误差，因此不再承担最终的逐目标校准。

逐目标相对投影来自原始多 target 相位的共同运动结构。对训练折内每个 target 的连续相位去除低阶 nuisance 后，记相位矩阵为 $\mathbf{Y}$。当环境 target 静止且雷达安装点作同一结构方向运动时：

$$
\mathbf{Y}\approx\mathbf{p}\mathbf{s}^{\mathsf T},
$$

其中 $\mathbf{p}=[p_1,\ldots,p_M]^{\mathsf T}$ 为各 target 投影，$\mathbf{s}$ 为共同振动相位。算法先按 target 质量加权，通过第一奇异向量提取 rank-1 分量；再以 AoA 初值的稳健中位尺度消除 $\mathbf{p}\to c\mathbf{p},\ \mathbf{s}\to\mathbf{s}/c$ 的固有尺度歧义。低跨 target 相干的行不进入参考集合，但仍可被单独检验。这样得到的 $p_i^{\mathrm{rel}}$ 可以表达每个 target 各不相同的角度量化误差。

相对候选采用双向时间折和 leave-one-target-out 验证。在 holdout 中估计第 $i$ 个 target 时，只由其余通过训练相干门的 target 重建共同分量，再分别用 $p_i^{\mathrm{rel}}$ 与原始 $p_{i,0}$ 预测第 $i$ 行；候选必须在两次互换折中都改善且保持相干。Kalman posterior、prediction-corrected phase 和真值均不参与这一过程。

第二阶段默认使用 native-timestamp ADXL 进行独立尺度与时延校准。物理关系为

$$
-\omega^2\Phi_i(\omega)
=
\frac{4\pi}{\lambda}p_i e^{-j\omega\tau}A(\omega).
$$

实现采用等价的时域积分型回归：在 ADXL 原生时间轴上对加速度梯形双积分得到强迫响应参考 $r(t)$，搜索公共残余时延 $\tau$，并用常数到三次的 nuisance 项吸收积分初值、加速度偏置与缓慢漂移。校准记录同样划分为不重叠的 train 和 holdout；train 估计绝对 $p_i^{\mathrm{abs}}$ 与公共时延，holdout 只重新拟合 nuisance 并检查预测改善，随后交换两半再次验证。

需要显式承认一个有条件的不可辨识性：若 ADXL 测量整体乘以未知增益 $g_a$，则雷达/ADXL 回归只能得到 $p_i/g_a$，无法仅靠同一记录判断这是 ADXL 增益还是所有 target 的共同几何缩放；若 ADXL 轴向、灵敏度和夹具传递增益已经独立验证，绝对投影则可辨识。因此模式必须在查看 holdout 结果之前由标定来源确定：未验证记录固定采用 AoA 锚定的相对候选，`validated` 记录固定采用 ADXL 绝对候选，不允许在同一 holdout 上择优切换。

相对候选也不是纯雷达自洽。每个时间折只能用本折训练段的 ADXL 动力学相干性选择 rank-1 参考集合，对侧 holdout 只验证候选，不能反向改变训练集合。最终至少三个 target 必须在训练与 holdout 上都过相干门，并且两个时间折的第一奇异分量占比都必须超过阈值；否则整组相对校准失败。逐目标 holdout 使用其余参考 target 重建同一个潜在运动，再在该固定潜变量下比较 $p_i^{\mathrm{rel}}$ 与 $p_{i,0}$，因此该改善量是“目标系数的条件改善诊断”，不是两个完整模型的独立概率比较。

rank-1 门只能证明多 target 共享主要波形，不能单独证明系数差异必然等于几何投影差异。把该系数解释为 $p_i$ 还要求实验中这些 target 观察同一刚体测点/结构自由度；雷达转动、目标特异散射增益、多径非线性或不同模态参与系数必须由布置与额外诊断排除。

时间轴、激励、公共时延边界和跨折时延一致性属于全局门控，失败时整组回退。相位相干、跨折 $\beta_i$ 一致性、物理边界、相对改变量、不确定度和 holdout 改善属于逐目标门控，只决定对应的 $g_i\in\{0,1\}$：

$$
\beta_i^{\star}
=
\begin{cases}
\beta_i^{\mathrm{cand}}, & g_i=1,\\
\beta_i^{\mathrm{AoA}}, & g_i=0.
\end{cases}
$$

全局门控失败等价于所有 $g_i=0$；未选 target 也始终保持原始 AoA 值。逐目标接受或回退完成后，$\boldsymbol{\beta}^{\star}$ 在整次正式估计中冻结；校准器的临时状态不带入 Kalman，正式滤波重新从第 0 帧读取原始 wrapped phase。由 Kalman 系统模型得到结构主相位先验后，在线仅用冻结 beta 预测 LoS 相位分支：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\beta_i^{\star}}+b_i,
$$

并执行预测辅助相位校正：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}
=
\psi_{i,k}
+2\pi\operatorname{round}
\left(
\frac{\hat{\phi}_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}}{2\pi}
\right).
$$

$\phi_{i,k}^{\mathrm{LOS,corr}}$ 只用于构造当前结构方向观测和诊断；Kalman posterior 与 LoS corrected phase 均不得反哺 beta。早期“用 corrected phase 与 $\Theta_k^+$ 做短窗 LS、逐帧自举 beta”的方案属于 legacy/ablation，可用于历史对照，但不是当前或最终方法。

## 5. 多目标相位观测更新模型

完成预测辅助相位校正后，当前时刻所有可用 target 的 LoS corrected phase 先转换为结构方向主相位观测，再共同参与 Kalman 更新。设当前时刻通过目标选择、相位质量评价和创新检验的可用目标集合为：

$$
\mathcal{A}_k=\{i_1,i_2,\ldots,i_{m_k}\},
$$

其中 $m_k=|\mathcal{A}_k|$ 为可用目标数量。对每个 target 先构造结构方向观测：

$$
y_{i,k}
=
\beta_i^{\star}
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

将各目标的结构方向观测组成观测向量：

$$
\mathbf{y}_k
=
\begin{bmatrix}
y_{i_1,k}\\
y_{i_2,k}\\
\vdots\\
y_{i_{m_k},k}
\end{bmatrix}.
$$

对应的线性观测模型为：

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

也即每个 target 的观测行均为 $H_i=[1,0]$。Kalman 更新为：

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
\right),
$$

$$
\mathbf{P}_k
=
\left(
\mathbf{I}
-
\mathbf{K}_k\mathbf{H}
\right)
\mathbf{P}_k^-.
$$

这一更新模型是本文与 Ma 等人模型的第二个关键差异。Ma 等人的观测矩阵为单行矩阵 $[1,0]$，表示单个 target 的校正 LoS 相位直接观测其 LoS 相位状态；本文的状态已经定义在结构真实振动方向，因此各 target 的 LoS corrected phase 需先经冻结的 $\beta_i^\star$ 转为结构方向主相位观测，随后以相同的 $H_i=[1,0]$ 共同观测同一个 $\Theta_k$。由此，多个 target 不再是独立估计位移后再进行平均，而是在结构方向相位域内作为同一结构状态的多通道观测共同参与滤波更新。

该处理具有三个直接优势。第一，滤波状态不依赖任何单一目标，当某个 target 噪声升高或临时失效时，只需从 $\mathcal{A}_k$ 中移除该观测，状态仍可由其他 target 和加速度维持。第二，不同 target 的冻结方向转换系数通过 $y_{i,k}=\beta_i^\star(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)$ 显式进入观测构造，避免了先将各目标位移粗略平均时对转换误差和相位分支误差的掩盖。第三，多目标观测共同约束同一主相位状态，可在相位解缠阶段利用目标间冗余性抑制单目标误判造成的分支跳变。

同一物理关系在相位校正阶段只用于预测 LoS 分支：

$$
\phi_{i,k}^{\mathrm{LOS}}
=
\frac{\Theta_k}{\beta_i^\star}+b_i.
$$

当前正文统一采用结构方向观测模型：先构造 $y_{i,k}=\beta_i^\star(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)$，再写 $y_{i,k}=\Theta_k+e_{i,k}$，对应 $H_i=[1,0]$。整个在线递推中 $\beta_i^\star$ 不变。

## 6. 目标可靠性与观测噪声建模

在多目标融合中，不同 target 的相位质量通常并不相同。目标幅值、信噪比、IQ 轨迹规则性、同 rangeBin 复合散射稳定性、转换系数标定误差和短时遮挡都会影响其观测可信度。由于本文正文主观测写在结构方向，观测噪声也应写为结构主相位坐标下的协方差：

$$
\mathbf{R}_k^{\Theta}
=
\operatorname{cov}(\mathbf{e}_k).
$$

最简单情形下，可令 $\mathbf{R}_k^{\Theta}$ 为对角矩阵：

$$
\mathbf{R}_k^{\Theta}
=
\operatorname{diag}
\left(
R_{1,k}^{\Theta},R_{2,k}^{\Theta},\ldots,R_{m_k,k}^{\Theta}
\right),
$$

其中 $R_{i,k}^{\Theta}$ 表示第 $i$ 个 target 转换到结构主相位坐标后的观测不确定度。

本文主方法采用固定/标定 $\mathbf{Q}$ 与 posterior-residual / quality-gated target-wise $\mathbf{R}_k^{\Theta}$ 的分工。$\mathbf{Q}$ 表示结构主相位动力学预测误差，属于全局标定参数；在线 $\mathbf{R}_k^{\Theta}$ 只描述各 radar target 当前相位观测质量，由 posterior residual 和 target quality gate 更新。beta 预校准方差是逐目标接受/拒绝门控和离线诊断量，不作为逐帧独立白噪声注入 $\mathbf{R}_k^{\Theta}$。

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

该过程只使用算法可见的 wrapped phase、measured acceleration、selected targets、冻结的 $\beta_i^\star$ 和 target-wise $\mathbf{R}_k^{\Theta}$，不使用真实位移或真值 RMSE。选定 $q^\star$ 后，在线滤波过程中 $\mathbf{Q}$ 保持不变；因此它仍属于固定/标定 $\mathbf{Q}$ 策略，而不是逐时刻 adaptive $\mathbf{Q}_k$。

各 target 的初始结构方向测量噪声只按冻结 beta 带来的坐标变化缩放。设 $R_{i,0}^{\Theta,\mathrm{AoA}}$ 为按原始 AoA 转换系数 $\beta_i^{\mathrm{AoA}}$ 构造的初始噪声，则预校准后使用：

$$
R_{i,0}^{\Theta,\star}
=
\operatorname{clip}
\left[
R_{i,0}^{\Theta,\mathrm{AoA}}
\left(
\frac{\beta_i^\star}{\beta_i^{\mathrm{AoA}}}
\right)^2,
\ R_{\min},
\ R_{\max}
\right],
$$

该平方比仅完成 LoS/结构方向坐标变换，不把 beta 校准方差解释成每帧重新采样的测量白噪声。SNR、presence 和 range-angle 稳定性进入后续 target quality gate，而不再额外改变这一 beta 坐标缩放规则。

Kalman 更新后，本文不再直接将预测创新作为第 $i$ 个 target 的测量噪声更新量。预测创新定义为：

$$
e_{i,k}^{-}
=
y_{i,k}
-
H_i\mathbf{x}_k^-,
\qquad
H_i=
\begin{bmatrix}
1&0
\end{bmatrix}.
$$

该量同时包含状态预测误差、加速度输入误差、过程噪声尺度不足和 radar 相位观测误差。Akhlaghi 等人关于 dynamic state estimation 的自适应噪声协方差研究进一步指出，prediction innovation 更适合用于反映过程模型或 $\mathbf{Q}$ 的不确定性，而 posterior residual 更适合用于估计测量噪声 $\mathbf{R}$。因此，在强结构响应阶段，若 target 的 SNR、presence 和 IQ 稳定性正常，较大的 $e_{i,k}^{-}$ 不应被直接解释为 radar measurement noise 增大。

本文据此采用后验残差作为基础测量噪声的主要统计量：

$$
\varepsilon_{i,k}
=
y_{i,k}
-
H_i\mathbf{x}_k^+.
$$

参考 residual-based adaptive Kalman filtering，当前主方法以第 $i$ 个 target 的后验残差能量加后验状态协方差投影，形成瞬时基础测量噪声估计：

$$
\tilde{R}_{i,k}
=
\varepsilon_{i,k}^{2}
+
H_i\mathbf{P}_k^+H_i^{\mathrm{T}}.
$$

后验残差统计仍可能在复合散射或污染观测被 Kalman 更新吸收时低估测量噪声。为避免测量噪声更新只由单一残差量驱动，本文进一步引入 target quality gate。令

$$
\rho_{i,k}\in[0,1]
$$

表示第 $i$ 个 target 的瞬时观测质量，可由 SNR、presence、range-angle 位置稳定性和 IQ 幅值稳定性等算法可见量构造。beta 已冻结，其校准方差不作为逐帧 quality 随机量。$\rho_{i,k}$ 越大，说明该 target 当前越可信。定义

$$
\Delta R_{i,k}
=
\tilde{R}_{i,k}
-
R_{i,k}.
$$

当 $\Delta R_{i,k}>0$ 时，测量噪声有上涨趋势，此时需要判断 target 质量是否确实下降；当 $\Delta R_{i,k}\le 0$ 时，测量噪声下降不会降低鲁棒性，可允许其正常恢复。由此定义门控因子：

$$
g_{i,k}
=
\begin{cases}
1-\rho_{i,k}, & \Delta R_{i,k}>0,\\
1, & \Delta R_{i,k}\le 0.
\end{cases}
$$

最终的基础测量噪声更新为：

$$
R_{i,k+1}
=
\operatorname{clip}
\left[
R_{i,k}
+
(1-\alpha)g_{i,k}\Delta R_{i,k},
\ R_{\min},
\ R_{\max}
\right],
\qquad
0<\alpha<1.
$$

该机制的作用是：当 target 质量下降且后验残差增大时，$R_{i,k}$ 上涨并降低该 target 的观测权重；当结构响应突然增强但 target 质量正常时，$R_{i,k}$ 的上涨被抑制，避免将过程预测误差误归因于 radar 测量噪声；当冷启动或低质量阶段结束后，$R_{i,k}$ 仍可随残差下降而恢复较高观测权重。上下限 clipping 用于防止单帧异常残差导致测量噪声估计发散或退化为零，从而维持 Kalman 增益的数值稳定性和鲁棒性。

上述处理的主要参考来源包括 Akhlaghi、Zhou 和 Huang 的 *Adaptive Adjustment of Noise Covariance in Kalman Filter for Dynamic State Estimation*、Mehra 对 adaptive filtering / covariance matching 方法的分类，以及 Li 等人在 INS/GNSS 紧组合中利用多观测通道估计 measurement noise covariance 的工作。已有文献提供的基础思想是：innovation 与 residual 均可用于噪声统计匹配，但 prediction innovation 不能被简单等同于 measurement noise；residual-based 估计更适合更新 $\mathbf{R}$，而多观测通道的 $\mathbf{R}$ 可根据各通道观测质量分别调整。

本文并非直接照搬上述 adaptive Kalman 公式，而是将其改写为多 target 相位观测下的 target-wise 标量噪声更新：每个 radar target 拥有独立的 $R_{i,k}^{\Theta}$，后验残差及后验协方差投影形成瞬时噪声估计，SNR、presence、range-angle 与 IQ 稳定性共同构成 quality gate。在线路径不再加入 beta 方差逐帧项。预校准 beta 方差只保存在 `variance/confidence/accepted_mask/reason_by_target` 等诊断中，用于逐目标接受门控，不能按 $(\phi-b)^2\sigma_\beta^2$ 逐帧叠加到 $R$，因为同一个静态尺度误差不是逐帧独立白噪声。

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

本文的主要改进在于状态相位的物理含义和观测组织方式发生变化。Ma 等人将状态相位定义为单一目标的 LoS 连续相位，因此加速度输入需要根据该目标方向转换系数映射到 LoS 相位域，观测模型也只对应一个 target。本文将状态相位定义为结构振动方向主相位，使加速度可以直接参与状态预测；各 target 的冻结方向转换关系用于两处：相位分支选择时用 $1/\beta_i^\star$ 将结构主相位预测投影回 LoS，相位观测更新时用 $\beta_i^\star$ 将 LoS corrected phase 转换为结构方向主相位观测。这样，多目标差异不再体现在多个互不兼容的状态定义中，而是体现在同一共享状态下的 target-wise 观测构造中。

这种改写解决了 Ma 单目标框架在多目标倒挂式监测中的三个问题。第一，不同 target 具有不同转换系数，单一 LoS 相位状态无法同时作为所有 target 的自然状态；本文通过主相位状态避免了该矛盾。第二，单目标状态对目标遮挡和相位噪声敏感；本文允许观测集合 $\mathcal{A}_k$ 随时间动态变化，使可靠 target 进入更新、不可靠 target 被降权或剔除。第三，单目标模型只能利用一个 wrapped phase 进行分支校正；本文利用共享主相位预测分别校正多个 target 的 wrapped phase，并将得到的 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 仅用于构造结构方向观测。beta 已在 Kalman 前经独立尺度/时延校准和 holdout 门控后冻结。

因此，本文方法可概括为：AoA 给出原始 beta 初值，原始多 target phase 的 rank-1 结构给出逐目标相对投影，native-timestamp ADXL 提供绝对尺度/公共时延候选；不重叠双折 holdout 与物理门控决定每个 target 接受候选或精确回退 AoA，随后冻结 $\boldsymbol{\beta}^\star$ 并从第 0 帧运行结构主相位 Kalman。在线阶段用共享预测状态校正多 target wrapped phase，以 $\beta_i^\star(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i)$ 构造结构方向观测，并只用 posterior residual 与 target quality gate 更新 $R_{i,k}^{\Theta}$。LoS corrected phase 和 $\Theta_k^+$ 均无返回 beta 校准器的路径。最终，滤波得到的主相位可直接转换为结构位移：

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

若存在 LDV、位移台或其他参考位移，可令 $J(q)$ 为估计位移与参考位移之间的 RMSE。若不存在外部参考，则可采用多目标相位一致性、解缠异常次数或 innovation 能量作为选择准则。例如，可将各 target 的 LoS corrected phase 转换为结构方向主相位观测：

$$
\tilde{\Theta}_{i,k}
=
\beta_i^\star
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right),
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

对于本文的多目标结构主相位模型，Ma 的能量最小化思想可作为固定 $q$ 的基线选择方法，但不宜直接作为在线自适应准则。原因在于，本文状态 $\Theta_k$ 表示结构振动方向主相位，其能量大小不仅受解缠错误影响，也受真实结构振动幅值影响。如果在滑动窗口内直接最小化 $\sum \hat{\Theta}_k^2$ 或 $\sum (\phi_{i,k}^{\mathrm{LOS,corr}})^2$，可能会把真实大幅振动误判为不稳定估计，从而倾向于选择过小或过强约束的过程噪声。另一方面，本文已有多个 target 的相位观测，过程噪声选择不应只依赖单通道相位能量，而应利用多目标之间的一致性和 Kalman innovation 统计量。

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
\mathbf{y}_k
-
\mathbf{H}\mathbf{x}_k^-,
$$

其理论协方差为：

$$
\mathbf{S}_k
=
\mathbf{H}\mathbf{P}_k^-\mathbf{H}^\mathrm{T}
+
\mathbf{R}_k^{\Theta}.
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

若 $\mathbf{R}_k^{\Theta}$ 设定合理，则该量可反映预测模型与多目标结构方向观测之间的统计一致性。当窗口内归一化 innovation 长期偏大时，说明状态预测误差可能被低估，可适当增大 $q$；当其长期偏小时，则说明过程噪声可能偏大或观测噪声被高估，可适当减小 $q$。实际实现中，应先通过 target gating 剔除明显异常观测，避免将遮挡、错误分支或低质量 target 误解释为过程噪声增大。

多目标一致性项可写为：

$$
J_{\mathrm{cons}}(q_j)
=
\sum_{k\in\mathcal{W}_t}
\sum_{i\in\mathcal{A}_k}
\rho_{i,k}
\left(
y_{i,k}
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
\hat{\phi}_{i,k}^{\mathrm{LOS},-} - \psi_{i,k}
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

综上，本文主算法采用 Kalman 前静态 beta 预校准 + calibrated $\mathbf{Q}$ + 按 beta 坐标平方比缩放的 initial $R_{i,0}^{\Theta}$ + posterior-residual / target-quality-gated online $R_{i,k}^{\Theta}$。固定/标定 $\mathbf{Q}$ 保持结构主相位动力学模型的统计尺度；在线 $R_{i,k}^{\Theta}$ 只响应 posterior residual 与 target 当前质量。beta 校准方差只用于预校准门控和诊断，不作为逐帧白噪声注入。滑动窗口自适应 $q$ 仅作为后续展望。
