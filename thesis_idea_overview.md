# 论文整体思路说明

> 当前状态：本文档已更新为当前方案的总览说明。[idea/overall_processing_architecture.md](/Users/umep/thesis/idea/overall_processing_architecture.md) 与 [innovation_points/multi_target_phase_kalman_fusion.md](/Users/umep/thesis/innovation_points/multi_target_phase_kalman_fusion.md) 仍是整体数据流和 Kalman 融合创新点的参考；当前转换系数口径以本文档为准，其中若仍出现 Kalman posterior 或 LoS corrected phase 反哺在线更新 $\beta_i$ 的描述，均视为尚待同步的历史方案，不代表当前方法。

本文的核心问题是：在毫米波雷达倒挂安装于结构测点、雷达随结构一起运动的情况下，如何利用周围静止反射目标恢复结构位移，并进一步从多个候选 target 中选择最可靠的观测目标。

本文不重新建立一套全新的毫米波雷达测距理论，而是以 mmVib 的相位测量理论为基础，将传统“固定雷达观测振动目标”的模型改写为“运动雷达观测静止参考目标”的倒挂式模型。两者在距离-相位关系和 FMCW 回波形式上基本一致，真正产生差异的是 IQ 复平面中的散射叠加方式，以及由此引出的 target 选择问题。

## 0. 当前最新版方案摘要

当前论文方法由三条主线组成。

第一，**在线多 target 选择**。雷达 ADC 数据经过 Range FFT 和 Angle FFT/DBF 得到 range-angle map；在选定 angle bin 或 angle cluster 后，对候选 peaks 进行多目标跟踪、同 rangeBin 角度合并、滑动窗口稳定性确认，并利用加速度频谱确定结构振动频带，筛选出与结构运动一致的静止参考 target。该阶段只输出原始 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k),
\qquad
\psi_{i,k}\in(-\pi,\pi],
$$

不做最终意义上的相位解缠，也不依赖已知转换系数。

第二，**AoA 初始化与独立转换系数预校准**。Ma 等人的 direction conversion factor 在本文统一记为 $\beta_i$，其方向为 LoS 位移/相位到结构真实振动方向位移/主相位：

$$
q_k=\beta_i d_{i,k}^{\mathrm{LOS}},
\qquad
\Theta_k=\beta_i\phi_{i,k}^{\mathrm{LOS}}.
$$

当前代码与正文统一使用 $\beta_i$ 作为 LoS 到结构真实振动方向的转换系数。AoA 不被视为最终标定值，而是先由结构方向到 LoS 的几何投影 $p_i=|\cos\theta_i|$ 给出转换系数初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

在任何 Kalman 递推开始之前，先从原始多 target slow-time phase 中搜索公共角偏差候选 $\delta$，并据此得到：

$$
p_i(\delta)=|\cos(\theta_i-\delta)|,
\qquad
\beta_i(\delta)=\frac{1}{\max(p_i(\delta),\epsilon_p)}.
$$

公共 $\delta$ 只描述安装级共同偏差，不能表示各 target 不同的 AoA 量化误差，因此它只作为辅助诊断/消融候选，不进入正式逐目标拟合先验。真正的逐目标校准在两个互不重叠的时间折上，从去趋势后的多 target 原始连续相位矩阵中提取 rank-1 共同振动分量，得到每个 target 独立的相对投影 $p_i$；再用 leave-one-target-out 的 holdout 预测检查该 target 的候选是否优于其原始 AoA 初值。与此同时，native-timestamp ADXL 原始加速度通过双积分回归估计绝对投影尺度和公共残余时延 $\tau$。

当 ADXL 轴向/灵敏度或夹具传递增益未知时，ADXL 公共增益与所有投影的公共缩放不能仅凭同一记录区分；若这些量经过独立验证，ADXL 绝对候选则是可辨识的。因此模式由采集标定来源预先确定，而不使用 holdout 分数临时选支路：未验证或缺失验证标志的记录固定采用原始 AoA 锚定的相对投影修正，`validated` 记录固定采用 ADXL 绝对候选。每一时间折只按本折训练段的 ADXL 相干性选择参考 target，对侧时间折只负责验证，不反向改变训练集合；最终仍要求至少三个参考 target 在训练与 holdout 上都与 ADXL 动力学相干，并要求两折相位矩阵通过 rank-1 共同运动门。时间轴、激励、公共时延或共同运动结构等全局门控失败时整组回退。相位连续性、相干性、跨折稳定性、边界、改变量、方差或 holdout 改善等 target-specific 门控只回退对应 target：

$$
\tilde{\beta}_i
=
\begin{cases}
\beta_i^{\mathrm{cand}}, & g_i=1,\\
\hat{\beta}_{i,0}, & g_i=0.
\end{cases}
$$

这里 $g_i$ 是完全在 Kalman 前确定的逐目标接受标志。所有接受值和精确回退值组成 $\tilde{\boldsymbol{\beta}}$ 后整体冻结，随后从第 0 帧重新运行完整 Kalman；Kalman posterior、结构主相位后验和 LoS corrected phase 均不得返回校准器。

第三，**结构主相位多 target Kalman 融合**。状态变量不再定义为 Ma 等人单 target 的 LoS 相位，而定义为结构振动方向主相位：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix},
\qquad
\Theta_k=\frac{4\pi}{\lambda}q_k.
$$

加速度直接进入系统模型预测主相位。多 target 融合的正文主叙事采用结构方向观测模型：独立预校准已接受或精确回退后的 $\tilde{\beta}_i$ 在在线阶段保持冻结。每个 target 的 LoS 校正相位乘以 $\tilde{\beta}_i$，得到结构主相位观测

$$
y_{i,k}
=
\tilde{\beta}_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right),
\qquad
y_{i,k}=\Theta_k+e_{i,k}.
$$

因此结构方向观测行可写为：

$$
H_i=
\begin{bmatrix}
1&0
\end{bmatrix}.
$$

只有在 prediction-aided phase correction 中需要回到 LoS 相位空间，因为雷达缠绕发生在 LoS 相位上。预测模型先给出第 $i$ 个 target 的 LoS 相位先验：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\tilde{\beta}_i}+b_i.
$$

再对 wrapped phase 进行统一校正，得到 LoS corrected phase：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{\hat{\phi}_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}}{2\pi}
\right).
$$

该 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 只进入结构方向观测构造，不得再作为转换系数校准输入。当前流程为：

$$
\text{AoA 初值}
\rightarrow
\text{原始多 target phase 的 rank-1 相对投影}
\rightarrow
\text{native-timestamp ADXL 绝对尺度/公共时延候选}
\rightarrow
\text{双折 holdout 逐 target 接受或精确回退 AoA}
\rightarrow
\text{冻结 }\tilde{\boldsymbol{\beta}}
\rightarrow
\text{从第 0 帧完整 Kalman}.
$$

因此，当前方案在 Kalman 外部先完成转换系数决策，再以冻结参数运行滤波。曾讨论的“用 Kalman posterior 或 LoS corrected phase 在线反哺 $\beta_i$”存在循环自证风险，已弃用，仅可作为历史方案说明。

当前主方法采用 fixed/calibrated $\mathbf{Q}$ 与 quality-gated target-wise $\mathbf{R}_k$ 的分工：过程噪声强度 $q^\star$ 通过候选集和无真值 prediction innovation energy 标定后在在线估计阶段保持固定；每个 target 的 $R_{i,0}$ 由 SNR、presence、geometry 等初始质量给出。若观测写在结构方向，则第 $i$ 个 target 的等效观测噪声应写为：

$$
R_{i,k}^{\Theta}
\approx
\tilde{\beta}_i^2R_{i,k}^{\mathrm{LOS}}.
$$

这说明 LoS 相位噪声会被冻结转换系数的平方放大。转换系数不确定性由 Kalman 前的独立校准与 holdout 接受/回退门控处理，不在在线阶段以“逐步收敛的 beta 方差”重复计入。当前代码与正文保持同一坐标系：先构造结构方向观测 $y_{i,k}$，再以 $H_i=[1,0]$ 进入 Kalman 更新。

## 1. 数学模型说明

### 1.1 mmVib 的基本相位模型

mmVib 将微振测量建模为目标与雷达之间距离的微小变化。若雷达固定，目标沿雷达视线方向发生微小振动，则目标到雷达的距离可写为：

$$
D(t)=D_0+x(t),
$$

其中 $D_0$ 为初始距离，$x(t)$ 为目标沿雷达视线方向的振动位移。毫米波雷达解调后的复反射信号可表示为：

$$
S(t)=A\exp\left(j\frac{4\pi f_c}{c}D(t)\right),
$$

因此相位变化与距离变化满足：

$$
\Delta\phi(t)=\frac{4\pi f_c}{c}x(t)
=\frac{4\pi}{\lambda}x(t).
$$

位移可以由连续相位恢复：

$$
x(t)=\frac{\lambda}{4\pi}
\operatorname{unwrap}\left(\Delta\phi(t)\right).
$$

这个关系说明，毫米波雷达本质上测量的是相对传播路径变化，而不是直接测量目标本体位移。

### 1.2 倒挂式距离模型

倒挂式安装时，雷达固定在结构测点上，并随结构一起运动；环境中的地面、桥下构件、固定支架等反射体在地面坐标系中可近似静止。设雷达初始位置为 $\mathbf{p}_r^0$，结构位移为 $\mathbf{u}(t)$，则雷达相位中心位置为：

$$
\mathbf{p}_r(t)=\mathbf{p}_r^0+\mathbf{u}(t).
$$

第 $i$ 个静止反射目标位置为 $\mathbf{p}_i$，其与雷达之间的瞬时距离为：

$$
D_i(t)=\left\|\mathbf{p}_i-\mathbf{p}_r^0-\mathbf{u}(t)\right\|.
$$

令

$$
\mathbf{r}_i^0=\mathbf{p}_i-\mathbf{p}_r^0,\qquad
D_i^0=\left\|\mathbf{r}_i^0\right\|,\qquad
\mathbf{n}_i=\frac{\mathbf{r}_i^0}{D_i^0},
$$

其中 $\mathbf{n}_i$ 是雷达初始位置指向第 $i$ 个静止目标的单位视线向量。当结构位移远小于雷达-目标距离时，一阶近似为：

$$
D_i(t)\approx D_i^0-\mathbf{n}_i^\mathrm{T}\mathbf{u}(t).
$$

因此距离变化为：

$$
\Delta D_i(t)\approx -\mathbf{n}_i^\mathrm{T}\mathbf{u}(t).
$$

若结构主要沿单位方向 $\mathbf{e}$ 运动，令 $\mathbf{u}(t)=\mathbf{e}q(t)$，则：

$$
\Delta D_i(t)\approx -\eta_i q(t),
\qquad
\eta_i=\mathbf{n}_i^\mathrm{T}\mathbf{e}.
$$

对应的相位变化为：

$$
\Delta\phi_i(t)
\approx
-\frac{4\pi}{\lambda}\eta_i q(t).
$$

因此，若第 $i$ 个目标稳定可见且 $\eta_i\neq 0$，结构位移可由该目标相位恢复：

$$
q(t)\approx
-\frac{\lambda}{4\pi\eta_i}
\operatorname{unwrap}\left(\Delta\phi_i(t)\right).
$$

从距离模型看，倒挂式模型与普通固定雷达模型的主要差别是符号和投影系数。普通模型中目标运动导致距离变化，倒挂模型中雷达自身运动导致相对距离变化；但二者都是通过相对距离变化引起回波相位变化。

### 1.3 回波模型的一致性

倒挂式安装并不改变 FMCW 雷达的回波生成与解调形式。对于第 $i$ 个静止反射目标，其目标反射分量仍可写为：

$$
Z_i(k)=A_i(k)\exp\left(j\frac{4\pi f_c}{c}D_i(k)\right).
$$

代入倒挂式距离近似：

$$
D_i(k)\approx D_i^0-\eta_i q(k),
$$

可得：

$$
Z_i(k)\approx
A_i(k)
\exp\left[
j\left(
\phi_i^0-\frac{4\pi}{\lambda}\eta_i q(k)
\right)
\right],
$$

其中 $\phi_i^0=4\pi D_i^0/\lambda$。这说明倒挂式回波模型可以理解为将 mmVib 中的目标振动位移 $x(k)$ 替换为等效相对位移：

$$
x_{\mathrm{equiv},i}(k)=-\eta_i q(k).
$$

因此，距离模型和回波模型本身并不是倒挂式方法的主要创新点。真正重要的问题是：倒挂式场景中，选定 range bin 或 range-angle bin 内的 IQ 复信号由哪些散射体组成，以及这些散射体是否能够形成稳定、规则、可用于相位恢复的圆弧。

### 1.4 IQ 模型的关键差异

mmVib 的 IQ 分析是在选定目标所在的 range bin 或 range-angle bin 后，对该单元的 slow-time 复数序列进行分析。在固定雷达场景中，实测 IQ 信号可表示为：

$$
S'(t)=S(t)+S_B+w(t),
$$

其中 $S(t)$ 是真实振动目标反射，$S_B$ 是静态背景和杂波合成的复向量，$w(t)$ 是噪声。由于雷达固定、背景也固定，$S_B$ 在短时间内可近似为常量：

$$
S_B=C_I+jC_Q.
$$

因此，实测 IQ 点绕固定圆心 $(C_I,C_Q)$ 形成圆弧。mmVib 通过圆拟合估计背景中心，再将圆心平移回原点，从而提取真实振动反射分量的相位。

倒挂式安装中，这一解释不能直接照搬。因为雷达自身随结构运动，环境中原本静止的反射体也会相对于雷达发生距离变化。也就是说，地面、桥下构件、固定支架等静止反射体不再天然构成一个固定背景中心，它们也会随结构位移产生相位旋转。

对于某个选定的距离/角度单元 $b$，更一般的倒挂式 IQ 信号应写为：

$$
Y_b(k)=
\sum_{m\in\mathcal{B}_b}
A_m(k)
\exp\left[
j\left(
\phi_m^0-\frac{4\pi}{\lambda}\eta_m q(k)
\right)
\right]
+D_b+w_b(k),
$$

其中 $\mathcal{B}_b$ 为该 bin 内的散射体集合，$\eta_m$ 为第 $m$ 个散射体的视线投影系数，$D_b$ 为硬件直流偏置、泄漏或近似不随结构运动变化的残余常量项。

因此，倒挂式 IQ 模型的核心不再是简单估计一个固定背景中心，而是判断选定 bin 内的散射叠加能否近似为一个稳定的主导反射圆弧。

## 2. 由模型引出的关键结论

### 2.1 距离模型与回波模型基本相同

倒挂式雷达与普通固定雷达在相位测距机理上是一致的。二者都满足：

$$
\Delta\phi(t)=\frac{4\pi}{\lambda}\Delta D(t).
$$

普通模型中，距离变化来自目标自身运动；倒挂模型中，距离变化来自雷达随结构运动后与静止参考目标之间的相对运动。两者在数学形式上主要表现为符号和投影系数的差异。

### 2.2 倒挂式真正不同的是 IQ 散射叠加

在固定雷达场景中，静态背景近似为固定圆心偏移；在倒挂场景中，环境静止散射体也会因为雷达运动而产生相位旋转。因此，倒挂式 IQ 轨迹是否规则，取决于选定 bin 内是否存在一个主导散射体，或多个散射体是否具有相近的角度和投影系数。

### 2.3 单主导静止 target 是最理想情况

如果选定 bin 内只有一个主导静止 target，则：

$$
Y_b(k)\approx
A_i(k)
\exp\left[
j\left(
\phi_i^0-\frac{4\pi}{\lambda}\eta_i q(k)
\right)
\right]
+D_b+w_b(k).
$$

若 $D_b$ 很小，IQ 轨迹近似绕原点形成圆弧；若存在常量偏置，IQ 轨迹则绕固定偏移点形成圆弧。这种情况下相位提取最稳定，最适合作为主 target。

### 2.4 多个角度相近的强散射体也可接受

如果同一 bin 内存在多个强静止散射体，但它们的角度相近、视线投影系数 $\eta_m$ 接近，则这些散射体的相位旋转趋势相近，复数叠加后仍可能形成比较规则的等效圆弧。此时虽然不是严格单一 target，但仍可作为稳定参考目标使用。

这也是后续角度过滤的理论基础：通过雷达已有的角度估计或波束形成方法，尽量保留角度相近的散射分量，过滤角度差异较大的散射体。

### 2.5 多个角度不同的强散射体形成复合 target

如果同一 range bin 内存在多个强散射体，且它们角度不同、投影系数 $\eta_m$ 差异明显，则该 bin 不再严格对应一个单一物理 target，而是多个静止散射体共同形成的复合 target。其观测信号可写为：

$$
Y_b(k)=
\sum_m
A_m
\exp\left[
j\left(
\phi_m^0-\frac{4\pi}{\lambda}\eta_m q(k)
\right)
\right]
+D_b+w_b(k).
$$

这些散射体虽然具有不同的投影系数，但它们仍然由同一个结构位移 $q(k)$ 驱动，因此总 IQ 信号不是随机噪声，而是一个确定的复合相位观测。若在当前工作位移范围内，其总相位可以近似表示为：

$$
\arg Y_b(k)\approx
\phi_b^0-\frac{4\pi}{\lambda}\eta_{\mathrm{eq}}q(k),
$$

则该 range bin 可以作为一个等效 target 使用。此时 $\eta_{\mathrm{eq}}$ 不再对应某一个单一反射点的几何角度，而是整个复合散射簇的等效 LOS 投影系数。

因此，多个角度不同的强散射体并不必然导致 IQ 圆弧不可用。相反，若复合回波幅值高、相位连续、等效转换因子稳定，它可能比单个弱散射体具有更高的信噪比。真正需要警惕的是：当多个散射体贡献接近、$\eta_m$ 差异较大、并且结构位移幅值足以使不同分量产生明显相对相位变化时，总相位与 $q(k)$ 之间可能出现非线性关系，表现为圆弧厚化、弯曲、幅值凹陷、相位跳变或转换因子随窗口变化。此时才需要考虑角度拆分或剔除。

### 2.6 移动物体会造成更明显的异常

如果车辆、行人或其他移动物体进入选定 bin，它们会引入独立于结构位移 $q(k)$ 的距离变化和幅值变化。此时 IQ 轨迹可能出现突变、断裂、漂移或非周期扰动。这样的 target 应被识别为遮挡、动态干扰或异常目标，而不是用于连续位移恢复。

### 2.7 多 target 的本质是多个投影观测

倒挂式场景中，多个静止 target 并不是多个独立位移源，而是同一个结构测点位移 $q(k)$ 在不同视线方向上的投影观测：

$$
\Delta\phi_i(k)\approx
-\frac{4\pi}{\lambda}\eta_i q(k).
$$

因此，不同 target 经投影修正后，应恢复出一致的结构位移。这个一致性可以用于 target 筛选、异常剔除、遮挡检测和备用目标切换。

## 3. 多 target 在线选择方案

由前述模型可知，倒挂式雷达中的多个静止反射目标可以作为同一结构位移 $q(k)$ 的多个 LOS 投影观测。因此，本文的核心工程方案不是只寻找单个最优 target，而是在线维护一组可用静态参考 target：

$$
\mathcal{B}_{\mathrm{valid}}(t)
=
\{b_1,b_2,\ldots,b_N\}.
$$

需要强调的是，本文的多 target 选择与常规毫米波雷达多目标检测在目标定义上相反。常规雷达多目标检测通常从静态背景中寻找车辆、行人或振动物体等运动目标；本文则需要从可能包含动态干扰的自然反射环境中寻找稳定静态参考目标。这个理念反转本身不是算法创新，但它会导致已有目标检测与目标管理模块在判据和输出上发生实际改造。

### 3.1 从已有模块到改造模块

若将参考文献中的方法模块记为 $A,B,C,\ldots$，则本文目前的真实关系可概括为：

$$
A' + B' + C' + E' + F',
$$

其中 Ma 等人的相位解缠、转换因子遍历和 RMSE 目标选择模块 $D$ 暂不用于 target selection 阶段。

具体而言：

1. $A'$：range spectrum 候选峰检测。底层仍使用 Range FFT 和 local maxima，但候选峰的含义从“雷达检测目标”改为“潜在静态参考 rangeBin 或峰簇”。
2. $B'$：滑动窗口确认。借用 M-out-of-N 或 track management 的“候选先观察再确认”思想，但确认含义从“运动目标轨迹稳定存在”改为“该 rangeBin 可作为长期静态参考”。
3. $C'$：加速度结构频带先验。Ma 等人用加速度频谱确定带通频带后进行位移 RMSE 比较；本文将其改为 target 细过滤的频带先验，用于判断候选 IQ 是否主要由结构运动驱动。
4. $E'$：IQ 几何异常指标。mmVib 的 IQ 圆弧分析用于振动恢复；本文只借用 IQ 轨迹形态，作为遮挡、动态干扰或不稳定复合 target 的辅助异常指标。
5. $F'$：输出 target 集合和权重。已有方法常选择 best target 或在遮挡时切换 target；本文输出的是 $\mathcal{B}_{\mathrm{valid}}(t)$ 及其可靠性权重，为后续多 target 融合提供输入。

### 3.2 unwrap-free 的 target selection

本文的 target selection 阶段不进行相位解缠。这里的边界需要明确：不需要解缠的是“目标选择模块”，而不是后续完整位移恢复模块。

target selection 的任务是判断某个 rangeBin 是否适合作为稳定静态参考，而不是直接恢复结构位移 $q(k)$。因此，该模块只使用以下不依赖连续相位的量：

$$
A_b(k)=|Y_b(k)|,
\qquad
\hat{b}(k),
\qquad
Z_b(k)=Y_b(k)-\bar{Y}_{b,\mathcal{W}},
\qquad
P_b(f),
\qquad
G_b(t),
\qquad
H_b(t).
$$

其中 $A_b(k)$ 用于幅值和持续性判断，$\hat{b}(k)$ 用于 range 位置稳定性判断，$Z_b(k)$ 为中心化 IQ 序列，$P_b(f)$ 为 IQ 频谱，$G_b(t)$ 为结构频带能量占比，$H_b(t)$ 为 IQ 轨迹厚度指标。上述指标均可在幅值域或复数 IQ 域计算，不需要：

$$
\operatorname{unwrap}(\angle Y_b(k)).
$$

这种设计避免了循环依赖：如果先对尚未确认可靠性的 target 进行相位解缠，再用解缠后的位移误差判断 target 是否可靠，那么不可靠 target 本身可能导致错误解缠，并进一步误导 target selection。尤其在毫米级位移和 20 Hz 以上结构响应下，77 GHz 雷达的相邻帧相位变化可能接近或超过 $\pi$，因此不宜在目标选择阶段依赖相位增量或解缠结果。

### 3.3 在线 target 选择流程

当前确定的在线 target 选择流程如下。

第一，每帧进行 Range FFT，得到 range profile 和每个 rangeBin 的复数 IQ：

$$
Y_b(t),\qquad A_b(t)=|Y_b(t)|.
$$

第二，使用稳健阈值和局部峰检测获得候选 rangeBin，并对相邻候选 bin 进行峰簇合并，避免将同一个强反射峰附近的泄漏 bin 重复计为多个 target。

第三，在滑动窗口 $\mathcal{W}_t$ 内评价候选 target 的持续性、幅值稳定性和 range 位置稳定性：

$$
R_b(t)
=
\frac{1}{W}
\sum_{\tau\in\mathcal{W}_t}
\mathbf{1}[A_b(\tau)>\tau_A],
$$

$$
CV_b(t)
=
\frac{
\operatorname{std}_{\tau\in\mathcal{W}_t}(A_b(\tau))
}{
\operatorname{mean}_{\tau\in\mathcal{W}_t}(A_b(\tau))+\epsilon
},
$$

$$
M_b(t)
=
\operatorname{std}_{\tau\in\mathcal{W}_t}
\left(\hat{b}(\tau)\right).
$$

第四，根据加速度频谱确定结构振动频带 $\Omega$。若存在多个结构模态，则取多个主频带的并集：

$$
\Omega
=
\bigcup_{r=1}^{R}
\left[
f_{a,r}-\Delta f_r,
f_{a,r}+\Delta f_r
\right].
$$

第五，对通过初筛的候选 target 计算中心化 IQ 频谱：

$$
Z_b(k)=Y_b(k)-\bar{Y}_{b,\mathcal{W}},
$$

$$
P_b(f)
=
\left|
\mathcal{F}\{Z_b(k)\}
\right|^2.
$$

定义结构频带能量占比：

$$
G_b(t)
=
\frac{
\sum_{f\in\Omega}P_b(f)
}{
\sum_{f\in\Omega_{\mathrm{valid}}}P_b(f)+\epsilon
}.
$$

若 $G_b(t)$ 较高，说明该 target 的 IQ 变化主要由结构振动频带驱动；若 $G_b(t)$ 较低，则说明其可能混入独立运动物体或非结构扰动。

第六，为每个 target 维护 `candidate`、`valid`、`active`、`suspect`、`lost` 等状态，并输出当前可用 target 集合及可靠性权重：

$$
\mathcal{B}_{\mathrm{valid}}(t)
=
\{b\mid r_b(t)>\tau_{\mathrm{valid}}\},
$$

$$
\omega_b(t)
=
\frac{
r_b(t)
}{
\sum_{j\in\mathcal{B}_{\mathrm{valid}}(t)}r_j(t)+\epsilon
}.
$$

### 3.4 与后续位移恢复的关系

多 target selection 只负责输出“哪些 target 当前适合进入位移恢复”，不直接完成位移恢复。后续阶段仍然需要讨论相位解缠、转换因子估计、单 target 位移恢复和多 target 加权融合：

$$
\text{unwrap-free target selection}
\rightarrow
\text{phase unwrapping}
\rightarrow
\text{conversion factor estimation}
\rightarrow
\text{multi-target displacement fusion}.
$$

因此，本文可以把 target selection 和 displacement recovery 明确拆开。前者要求稳定、在线、无需解缠；后者才处理相位连续性、$\beta$、$\eta$ 和位移融合。

## 4. 转换因子与角度问题

### 4.1 Ma 等人的转换因子标定方法

Ma 等人在毫米波雷达与加速度融合的结构位移监测研究中，已经提出过利用加速度标定雷达 LOS 方向转换关系的方法。其出发点是：毫米波雷达相位直接得到的是 line-of-sight 方向上的位移，而加速度计安装在结构测点处，测量的是实际结构振动方向上的加速度。因此，需要一个方向转换因子，将雷达 LOS 位移转换为实际振动方向位移。

设雷达相位得到的 LOS 位移为：

$$
d_r(k)=\frac{\lambda}{4\pi}
\operatorname{unwrap}\left(\Delta\phi(k)\right),
$$

加速度经双积分和带通滤波后得到的参考位移为：

$$
q_a(k).
$$

Ma 等人的早期做法可以概括为：遍历一组转换因子 $\beta$，将雷达 LOS 位移转换为结构振动方向位移：

$$
q_{r,\beta}(k)=\beta d_r(k),
$$

然后计算其与加速度参考位移之间的误差：

$$
E(\beta)=
\sqrt{
\frac{1}{N}
\sum_k
\left[
\beta d_r(k)-q_a(k)
\right]^2
}.
$$

使误差最小的 $\beta$ 被选为方向转换因子：

$$
\hat{\beta}=
\arg\min_{\beta}E(\beta).
$$

当存在多个候选 target 时，对每个 target 都执行该过程，最终选择误差最小的 target 及其转换因子。后续论文中也出现了线性拟合相位的写法：先将加速度位移转换为 acceleration-based phase，再将其与 radar-derived unwrapped phase 进行带通滤波和线性拟合，拟合斜率即为 direction conversion factor。

### 4.2 该方法的本质

Ma 等人的方法本质上不是直接拟合雷达 AoA，而是拟合雷达 LOS 测量与真实结构运动之间的比例关系。若结构主要沿方向 $\mathbf{e}$ 运动，第 $i$ 个目标视线方向为 $\mathbf{n}_i$，则：

$$
d_i(k)\approx \eta_i q(k),
\qquad
\eta_i=\mathbf{n}_i^\mathrm{T}\mathbf{e}.
$$

若采用转换因子写法：

$$
q(k)\approx \beta_i d_i(k),
$$

则有：

$$
\beta_i\approx \frac{1}{|\eta_i|}.
$$

在二维几何简化下，若 $\eta_i=\cos\alpha_i$，则可进一步写成：

$$
\alpha_i\approx
\arccos\left(\frac{1}{\beta_i}\right).
$$

因此，转换因子可以进一步解释为等效 LOS 投影角，但它不是雷达阵列直接估计的 AoA。后续如果要用它进行角度过滤，需要将“由加速度-雷达相位拟合得到的等效投影角”和“雷达 range-angle 元数据中的空间角度”区分开来。

### 4.3 可替代的转换因子估计办法

普通最小二乘或遍历 RMSE 方法虽然直接，但在倒挂场景下可能不够稳健。原因包括：加速度双积分存在低频漂移，雷达相位可能存在解缠错误，同一 bin 内可能存在多散射叠加，车辆或行人会造成短时异常，并且雷达与加速度可能存在微小时延。因此，本节保留若干转换因子估计思路，作为方法演进记录和对照候选。凡是依赖 Kalman posterior 或 LoS corrected phase 在线反哺 $\beta_i$ 的方案均已弃用，不代表本文当前方法。

可选方案包括以下几类。

第一，使用 Ma 式 RMSE 遍历法。该方法实现简单，便于复现已有文献。对候选 $\beta$ 逐个计算雷达转换位移与加速度参考位移的 RMSE，选择最小者。它适合作为 baseline，但对异常点、相位解缠错误和双积分漂移较敏感。

第二，使用普通最小二乘闭式估计。若采用

$$
q_a(k)\approx \beta d_r(k),
$$

则有：

$$
\hat{\beta}
=
\frac{\sum_k d_r(k)q_a(k)}
     {\sum_k d_r^2(k)}.
$$

如果按倒挂投影系数估计，也可写为：

$$
\hat{\eta}
=
-\frac{\sum_k q_a(k)d_r(k)}
       {\sum_k q_a^2(k)}.
$$

该方法计算方便，但假设数据噪声较温和，不适合直接处理遮挡、移动目标或强相位噪声。

第三，使用频域幅值比。若标定窗口中结构响应主要集中在主频 $f_0$，可利用加速度与位移的频域关系：

$$
A(f)=-(2\pi f)^2Q(f).
$$

若 $Q(f)=\beta D_r(f)$，则：

$$
\hat{\beta}
\approx
\frac{|A(f_0)|}
     {(2\pi f_0)^2|D_r(f_0)|}.
$$

该方法避免完整双积分，低频漂移影响较小，但依赖清晰主频。

第四，使用相干加权的频域拟合。在一个可靠频带 $\Omega$ 内，令：

$$
X(f)=-(2\pi f)^2D_r(f),
$$

并拟合：

$$
A(f)\approx \beta X(f).
$$

可用 coherence 作为权重 $w(f)$：

$$
\hat{\beta}
=
\frac{
\sum_{f\in\Omega} w(f)\operatorname{Re}\{X^*(f)A(f)\}
}{
\sum_{f\in\Omega} w(f)|X(f)|^2
}.
$$

该方法可以自动降低低相干频点的影响，更适合判断 radar phase 与 acceleration 是否来自同一个结构运动。

第五，使用鲁棒回归。若存在短时遮挡、车辆经过或相位突变，可将普通最小二乘替换为 Huber loss、Tukey loss 或 RANSAC：

$$
\hat{\beta}
=
\arg\min_\beta
\sum_k
\rho\left(\beta d_r(k)-q_a(k)\right).
$$

该方法可以避免少量异常点将转换因子严重带偏。

第六，使用总最小二乘或 Deming 回归。普通最小二乘默认自变量 $d_r(k)$ 没有误差，但实际中雷达相位和加速度参考位移都有噪声。因此，可以考虑同时建模两侧误差的总最小二乘或 Deming 回归，使拟合更符合双传感器噪声场景。

第七，使用几何/AoA 先验再微调。如果雷达能够给出 AoA 或 range-angle bin，且雷达安装姿态大致已知，可先由几何关系得到初始投影系数：

$$
\eta_0=\mathbf{n}^\mathrm{T}\mathbf{e},
$$

再在其附近进行小范围搜索或拟合：

$$
\beta_0\approx \frac{1}{|\eta_0|}.
$$

这种方法可以把雷达空间角度元数据和加速度拟合得到的投影关系结合起来。本文当前方法以该思想为起点，但校准完全位于 Kalman 之前：先由 AoA 给出初值，再从原始多 target phase 提出公共角偏差和逐目标相对投影候选，并必须通过 native-timestamp ADXL 动力学相干、rank-1 共同运动与不重叠 holdout 门控。全局门失败时整组回退；逐目标门失败时只精确回退对应 target。最后统一冻结 $\beta_i$。

### 4.4 当前结论：AoA 初始化与独立转换系数预校准

本文沿用 Ma 等人的方向定义，将 $\beta_i$ 作为 LoS 位移/相位到结构真实振动方向位移/主相位的转换系数：

$$
q(k)=\beta_i d_{\mathrm{LOS},i}(k),
\qquad
\Theta_k=\beta_i\phi_{i,k}^{\mathrm{LOS}}.
$$

当前方案中，AoA 不被视为最终精确转换系数，而是独立预校准的几何初值。若第 $i$ 个 target 的 AoA 与结构振动方向夹角为 $\theta_i$，则先得到结构主相位到 LoS 相位的几何投影 $p_i$，再取其倒数作为 LoS 到结构方向的转换系数初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

随后在任何 Kalman 递推之前，先使用原始多 target slow-time phase 搜索一个共享角偏差 $\delta$。该偏差作用在 AoA 投影上：

$$
p_i(\delta)=|\cos(\theta_i-\delta)|,
\qquad
\beta_i(\delta)=\frac{1}{\max(p_i(\delta),\epsilon_p)}.
$$

公共角偏差候选只负责描述多个静止 target 共同的几何偏差，不能由 Kalman posterior、$\Theta_k^+$ 或 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 构造。真正的逐目标候选由原始相位矩阵的 rank-1 共同运动结构给出，并进一步使用 ADXL 的 native timestamps 和原始加速度做独立动力学门控/绝对时域校准。拟合段和 holdout 段不重叠且双向交换；相对模式要求至少三个 ADXL 相干参考 target，且两折第一奇异分量占比均通过阈值。

模式由标定来源预先决定：未验证的轴向、灵敏度或夹具传递增益采用 AoA 锚定相对候选，`validated` 记录采用 ADXL 绝对候选，不得在同一 holdout 上择优。时间轴、激励、公共时延、参考数量或 rank-1 共同运动门失败时，整组精确回退到本次 AoA 初值；单个 target 的相位连续性、相干性、跨折参数一致性、物理边界、改变量、不确定度或条件 holdout 改善失败时，只令该 target 回退：

$$
\tilde{\beta}_i
=
\begin{cases}
\beta_i^{\mathrm{cand}}, & g_i=1,\\
\hat{\beta}_{i,0}, & g_i=0.
\end{cases}
$$

任何失败都不得复用上一次运行的缓存值；通过的其他 target 不因单个坏 target 被丢弃。

一旦完成接受或回退决策，$\tilde{\boldsymbol{\beta}}$ 即冻结，并从第 0 帧重新运行完整 Kalman。进入 Kalman 的 target 相位仍是 wrapped phase；由加速度驱动的预测模型先给出结构主相位先验，再通过冻结的 $\tilde{\beta}_i$ 投影为各 target 的 LoS 相位先验：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\tilde{\beta}_i}+b_i.
$$

预测辅助相位校正仍用于选择 wrapped phase 分支，但只服务 Kalman 观测：

$$
\phi_{i,k}^{\mathrm{LOS,corr}}
=
\psi_{i,k}
+
2\pi
\operatorname{round}
\left(
\frac{
\hat{\phi}_{i,k}^{\mathrm{LOS},-}-\psi_{i,k}
}{2\pi}
\right),
$$

并构造结构方向主相位观测：

$$
y_{i,k}
=
\tilde{\beta}_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right),
\qquad
y_{i,k}=\Theta_k+e_{i,k}.
$$

相对于 Ma 等人的离线转换因子标定，本文保留了“加速度辅助相位预测”的思想，同时把转换系数决策与状态递推严格隔离。旧的“$\phi_{i,k}^{\mathrm{LOS,corr}}$ 或 $\Theta_k^+$ 反哺 $\beta_{i,k+1}$”在线自举方案已弃用，因为同一滤波闭环容易产生自反馈和循环验证；该方案只能作为历史讨论，不得再写成当前或最终方法。

### 4.5 当前硬件约束：TI IWR1843

当前实验雷达为 TI IWR1843。根据 TI 官方资料，IWR1843 是 76-81 GHz FMCW 毫米波雷达芯片，硬件上集成 3 个发射通道和 4 个接收通道，支持 MIMO 角度估计。这个硬件信息会直接影响后续 AoA 和 range-angle 处理方案选择。

对本文来说，这意味着：

1. 可以考虑利用 IWR1843 的 MIMO 虚拟阵列进行 range-angle 处理，而不是只停留在 range bin。
2. 基线方法应优先选择 IWR1843 常规处理链容易实现的方法，例如 Range FFT + Angle FFT 或数字波束形成。
3. Capon/MVDR 可以作为更高角度分辨率的候选方法，但需要评估快拍数、SNR、协方差矩阵估计稳定性和实时计算量。
4. MUSIC、ESPRIT、稀疏重构、SBL、atomic norm 等超分辨方法可以作为候选调研方向，但由于 IWR1843 通道数有限、桥下多径复杂、目标可能相干，不能默认它们比 Angle FFT 或 MVDR 更稳。
5. 本文真正需要的不是单帧角度估计精度最大化，而是获得稳定的 range-angle 复数 slow-time 序列，用于后续相位跟踪、IQ 圆弧判断和加速度-雷达转换因子估计。

因此，后续文献调研和算法选择应围绕 IWR1843 的实际能力展开：优先考虑能在 3TX/4RX MIMO 数据上稳定输出角度门控复信号的方法，再考虑是否需要超分辨角度估计。

### 4.6 唯一实机采集拓扑：Raspberry Pi 4 本地采集

当前项目只采用单采集主机方案：Raspberry Pi 4 负责传感器控制、原始数据接收和同步事件记录，电脑只通过 Wi-Fi/SSH 控制 Pi，并在采集完成后下载数据进行离线分析。

```text
电脑 ──Wi-Fi / SSH──→ Raspberry Pi 4
                         ├──SPI + DRDY──→ ADXL355
                         ├──USB─────────→ IWR1843BOOST
                         ├──GPIO18──────→ IWR1843BOOST SYNC_IN（硬件触发模式）
                         └──Ethernet────→ DCA1000EVM

IWR1843BOOST ←──60-pin HD / LVDS──→ DCA1000EVM
```

其中，Pi 4 通过 SPI 读取 ADXL355，DRDY 接入 Pi GPIO；IWR1843BOOST 的 USB 接 Pi，用于雷达配置和控制；DCA1000EVM 的网线直连 Pi 有线网口，用于控制和接收 UDP 原始 ADC 数据；IWR1843BOOST 与 DCA1000EVM 通过 60-pin HD 板间接口传输 LVDS 数据。硬件触发模式下，Pi 另以 GPIO18 驱动 IWR1843BOOST J6-9 `SYNC_IN`，并可用 GPIO24 回环记录实际边沿。电脑不直接连接 IWR1843BOOST、DCA1000EVM 或 ADXL355，不承担抓包或传感器时间戳工作。同步设计必须建立在 Pi 4 单机统一时间域上。

目前 `capture_program/` 已实现软件时间戳与 GPIO 硬件触发两种统一采集模式，并输出 ADXL355 DRDY 与雷达帧参考的 `CLOCK_MONOTONIC` 时间轴。该实现已通过无硬件聚焦测试，但真实 SPI 持续采样、DCA 数据完整性、`SYNC_IN` 波形、雷达触发时延、ADXL 数字滤波群延迟和跨传感器漂移仍待上电台架验证，因此现阶段不得将软件输出等同于已完成实机同步精度验证。
