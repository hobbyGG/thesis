# 基于距离-角度联合维度的在线参考目标选取方法

## 1. 方法目的

倒挂式毫米波雷达固定在结构测点上，并随结构共同振动。雷达视场内的地面、桥下构件、支架和其他静止环境反射物会因为雷达自身运动而产生相位变化，因此可以作为结构位移恢复的参考目标。已有毫米波雷达结构位移监测研究通常先从 range spectrum 中选择一个或多个强反射 target，再估计方向转换系数并恢复结构位移 [Ma2023, Ma2024]。这种做法在目标确实由单一散射体主导时有效，但在自然反射环境中，一个 rangeBin 往往包含多个不同角度的散射体，直接追踪该 rangeBin 的总相位可能导致相位畸变和转换系数不稳定。

本文参考 Xiong 等人提出的 mmWBat 思想，将传统 rangeBin phase tracking 扩展为 range-angle bin phase tracking [Xiong2021]。mmWBat 已经证明，微动目标的 interferometric phase evolution 可以在 range-angle joint dimension 中被保留和提取，并用于 full-field mechanical vibration measurement 和 scaled bridge dynamic monitoring。受此启发，本文不再把一个 target 定义为单一 rangeBin，而是定义为同一 rangeBin 内的一个 angleBin 或一个角度相近的 angleBin cluster：

$$
T=(b,\mathcal{C}).
$$

其中，$T$ 表示一个候选参考 target，$b$ 表示 rangeBin 索引，$\mathcal{C}$ 表示该 rangeBin 内被合并为同一目标的 angleBin 集合。当目标只由一个 angleBin 表示时，有 $\mathcal{C}=\{p\}$，其中 $p$ 为 angleBin 索引。由此，目标选择问题由：

$$
\text{从所有 rangeBins 中选出稳定参考 bins}
$$

改写为：

$$
\text{从所有 range-angle bins 或 angle clusters 中选出稳定参考 targets。}
$$

本文在卡尔曼滤波之前采用如下数据流：

$$
\text{复数 range-angle map 构造}
\rightarrow
\text{距离-角度候选发现}
\rightarrow
\text{同 rangeBin 内角度合并}
\rightarrow
\text{滑动窗口出现确认}
\rightarrow
\text{结构频带一致性筛选}
\rightarrow
\text{相位提取与转换系数估计。}
$$

本文件主要描述目标选取和相位序列提取；转换系数估计在 `equivalent_conversion_factor_stability.md` 中单独说明。

## 2. 复数 Range-Angle Map 构造

设第 $k$ 个 slow-time 采样或雷达帧的多通道基带数据为：

$$
S_k(n,m),\qquad n=0,1,\ldots,N-1,\quad m=0,1,\ldots,M-1.
$$

其中，$S_k(n,m)$ 表示第 $k$ 帧、第 $m$ 个虚拟天线通道在 fast-time 采样点 $n$ 处的复数基带信号；$N$ 表示每个 chirp 或 sweep 的 fast-time 采样点数；$M$ 表示用于角度处理的虚拟天线通道数。对 $S_k(n,m)$ 先沿 fast-time 维做 Range FFT，再沿虚拟天线维做 Angle FFT 或等效数字波束形成，可得到复数距离-角度矩阵：

$$
Y_k(b,p)
=
\sum_{m=0}^{M-1}
\sum_{n=0}^{N-1}
S_k(n,m)
\exp\left(-j\frac{2\pi nb}{N_z}\right)
\exp\left(-j\frac{2\pi mp}{M_z}\right).
$$

其中，$Y_k(b,p)$ 表示第 $k$ 帧在第 $b$ 个 rangeBin 和第 $p$ 个 angleBin 处的复数 range-angle phasor；$b=0,1,\ldots,B-1$ 为 rangeBin 索引；$p=0,1,\ldots,P-1$ 为 angleBin 索引；$N_z$ 和 $M_z$ 分别表示 Range FFT 和 Angle FFT 的点数；$B$ 和 $P$ 分别表示有效 range bins 和 angle bins 的数量；$j$ 为虚数单位。

对应的幅值矩阵定义为：

$$
A_k(b,p)=|Y_k(b,p)|.
$$

其中，$A_k(b,p)$ 表示第 $k$ 帧第 $(b,p)$ 个距离-角度单元的幅值，$|\cdot|$ 表示复数模长。后续候选发现使用 $A_k(b,p)$，而相位追踪必须使用复数值 $Y_k(b,p)$。因此，数据处理时不能只保存 range-angle heatmap magnitude，而应保留复数 range-angle map。

2D FFT 结果矩阵天然保留 rangeBin 信息：矩阵的同一行对应同一个 rangeBin，不同列对应该 rangeBin 内的不同 angleBins。因此，若两个候选峰分别位于 $(b,p_1)$ 和 $(b,p_2)$，它们就属于同一个 rangeBin 内的两个角度方向；若候选峰位于 $(b_1,p)$ 和 $(b_2,p)$，则表示不同 rangeBins 上的相近角度方向。

## 3. 距离-角度候选发现

对每一帧的幅值矩阵 $A_k(b,p)$ 进行局部峰检测。定义第 $k$ 帧的最大幅值为：

$$
A_{\max}(k)=\max_{0\le b<B,\ 0\le p<P}A_k(b,p).
$$

其中，$A_{\max}(k)$ 表示第 $k$ 帧所有 range-angle bins 中的最大幅值。设 $\mathcal{N}(b,p)$ 表示 $(b,p)$ 周围的二维邻域，本文可取 8 邻域或根据实现取相邻 range-angle cells。第 $k$ 帧的候选距离-角度峰集合定义为：

$$
\mathcal{P}_k
=
\left\{
(b,p)
\ \middle|\
A_k(b,p)>A_k(b',p'),\ \forall(b',p')\in\mathcal{N}(b,p),
\ A_k(b,p)\ge \rho A_{\max}(k)
\right\}.
$$

其中，$\mathcal{P}_k$ 表示第 $k$ 帧检测到的候选 range-angle peaks，$\rho$ 为相对幅值阈值。为保持实现简单，本文可取 $\rho=0.1$，即保留幅值不低于当前帧最大反射强度 10% 的局部峰。Ma 等人在 target selection 中也使用反射强度阈值减少候选 target 数量，并指出候选阶段包含部分错误峰是可以接受的，后续筛选会进一步确认目标可靠性 [Ma2024]。

该步骤只负责发现候选 range-angle peaks，不在单帧内判断其是否最终可用。瞬时噪声峰、旁瓣峰或短时动态干扰可能进入 $\mathcal{P}_k$，后续通过角度合并、滑动窗口出现确认和结构频带一致性筛选剔除。

## 4. 同 RangeBin 内角度合并

由于 IWR1843 等低通道 MIMO 雷达的角分辨率受虚拟阵列孔径限制，Angle FFT 的 zero-padding 只能细化显示网格，不能真正提高物理角分辨率。因此，同一个 rangeBin 内相互很近的 angle peaks 不应被强行解释为多个独立物理目标。本文对同一 rangeBin 内的候选角度峰进行分组，将角度接近的 peaks 合并为一个等效 target。

对任一候选 peak $(b,p)$，设其对应角度为 $\theta_p$，或对应空间频率为：

$$
u_p=\sin\theta_p.
$$

其中，$\theta_p$ 表示第 $p$ 个 angleBin 对应的物理角度，$u_p$ 表示该角度的空间频率。若同一 rangeBin 内两个候选峰 $(b,p_i)$ 和 $(b,p_j)$ 满足：

$$
|\theta_{p_i}-\theta_{p_j}|\le \Delta\theta_{\mathrm{merge}},
$$

或等价地：

$$
|u_{p_i}-u_{p_j}|\le \Delta u_{\mathrm{merge}},
$$

则将它们归入同一个 angle cluster。其中，$\Delta\theta_{\mathrm{merge}}$ 表示角度合并阈值，$\Delta u_{\mathrm{merge}}$ 表示空间频率合并阈值。对于 8 个有效方位虚拟阵元的 IWR1843，主瓣角分辨率通常约为 15 度量级，因此 $\Delta\theta_{\mathrm{merge}}$ 可按该物理分辨率设置，而不应按 zero-padding 后的 angleBin 间隔设置。

合并后，一个候选 target 表示为：

$$
T=(b,\mathcal{C}),
$$

其中，$\mathcal{C}=\{p_1,p_2,\ldots,p_L\}$ 表示同一 rangeBin $b$ 内被合并为一个 target 的 $L$ 个 angleBins。若 $L=1$，则该 target 是单个 range-angle bin；若 $L>1$，则该 target 是一个角度相近的等效 angle cluster。

为了保持主方法简单，本文将确认窗口内平均幅值最大的 angleBin 作为该 cluster 的代表 bin。设当前窗口为 $\mathcal{W}_t$，则 cluster 内第 $p$ 个 angleBin 的窗口平均幅值为：

$$
\bar{A}_{b,p,\mathcal{W}}
=
\frac{1}{|\mathcal{W}_t|}
\sum_{k\in\mathcal{W}_t}
A_k(b,p).
$$

其中，$\bar{A}_{b,p,\mathcal{W}}$ 表示第 $b$ 个 rangeBin、第 $p$ 个 angleBin 在窗口 $\mathcal{W}_t$ 内的平均幅值，$|\mathcal{W}_t|$ 表示窗口内采样数量。cluster 的代表 angleBin 定义为：

$$
p_T
=
\arg\max_{p\in\mathcal{C}}
\bar{A}_{b,p,\mathcal{W}}.
$$

其中，$p_T$ 表示 target $T$ 的代表 angleBin。该 target 的复数 slow-time 序列定义为：

$$
z_T(k)=Y_k(b,p_T).
$$

其中，$z_T(k)$ 表示 target $T$ 在第 $k$ 个 slow-time 采样处的复数 phasor。若后续实验需要保留整个 angle cluster 的能量，也可以使用固定权重进行复数加权：

$$
z_T(k)=\sum_{p\in\mathcal{C}}w_pY_k(b,p),
$$

其中，$w_p$ 表示 angleBin $p$ 的固定权重。为了避免权重变化引入伪相位，$w_p$ 应在确认窗口内确定，并在该窗口内保持不变。

## 5. 滑动窗口出现确认

单帧候选峰不能直接作为可用参考 target。一个可靠的静态参考 target 应在连续一段时间内反复出现。FMCW 多目标跟踪中常使用 M-out-of-N logic 对 candidate track 进行确认 [Kim2013]。本文不引入完整跟踪滤波器，只保留这一最简单的窗口确认思想。

设滑动窗口为：

$$
\mathcal{W}_t=[t-W+1,t].
$$

其中，$\mathcal{W}_t$ 表示以当前时刻 $t$ 结束的滑动窗口，$W$ 表示窗口长度，窗口内包含从 $t-W+1$ 到 $t$ 的连续 slow-time 采样或雷达帧。

对任一候选 target $T$，定义其在第 $\tau$ 帧是否被检测到：

$$
I_T(\tau)
=
\begin{cases}
1, & T\ \text{在第}\ \tau\ \text{帧被匹配到},\\
0, & T\ \text{在第}\ \tau\ \text{帧未被匹配到}.
\end{cases}
$$

其中，$I_T(\tau)$ 表示 target $T$ 在第 $\tau$ 帧的出现指示变量。匹配时要求候选峰具有相同或相邻的 rangeBin，并且其 angleBin 落入 target $T$ 对应的 angle cluster 或合并阈值范围内。

target $T$ 在窗口内的出现率定义为：

$$
R_T(t)
=
\frac{1}{W}
\sum_{\tau=t-W+1}^{t}
I_T(\tau).
$$

其中，$R_T(t)$ 表示 target $T$ 在窗口 $\mathcal{W}_t$ 内被检测到的比例。若：

$$
R_T(t)\ge \tau_R,
$$

则认为 target $T$ 通过窗口出现确认，其中 $\tau_R$ 为出现率阈值。为保持实现简单，本文可取 $\tau_R=0.7$，即候选 target 在最近窗口中至少约 70% 的帧内出现，才进入下一步频谱筛选。

通过窗口确认的稳定候选集合定义为：

$$
\mathcal{T}_{\mathrm{stable}}(t)
=
\left\{
T
\mid
R_T(t)\ge \tau_R
\right\}.
$$

其中，$\mathcal{T}_{\mathrm{stable}}(t)$ 表示时刻 $t$ 通过窗口出现确认的稳定候选 target 集合。

## 6. 结构频带一致性筛选

通过窗口确认只能说明 target 稳定存在，尚不能说明其 slow-time IQ 变化由结构振动驱动。倒挂式雷达的有效静态参考 target 应满足：其复数 slow-time 序列的主要变化应集中在结构振动频带内。Ma 等人在自动校准中先由加速度频谱识别结构主频，并据此确定带通滤波频带 [Ma2024]。本文保留这一思想，但只将加速度频带作为 target selection 的频谱先验，不在目标选择阶段计算相位解缠结果或转换系数。

设与雷达同测点安装的加速度信号为 $a(k)$，其中 $a(k)$ 表示第 $k$ 个 slow-time 采样处的加速度。在窗口 $\mathcal{W}_t$ 内计算加速度功率谱：

$$
P_a(f)
=
\left|
\mathcal{F}\{a(k),k\in\mathcal{W}_t\}
\right|^2.
$$

其中，$P_a(f)$ 表示加速度信号在频率 $f$ 处的功率谱，$f$ 表示频率变量，$\mathcal{F}\{\cdot\}$ 表示傅里叶变换。设结构主频为加速度谱中幅值最大的频率：

$$
f_a(t)
=
\arg\max_{f\in\Omega_a}P_a(f).
$$

其中，$f_a(t)$ 表示当前窗口内识别到的结构主频，$\Omega_a$ 表示允许搜索结构主频的频率范围。以该主频为中心，定义结构振动频带：

$$
\Omega(t)
=
\left[
f_a(t)-\Delta f,\,
f_a(t)+\Delta f
\right].
$$

其中，$\Omega(t)$ 表示当前窗口内的结构振动频带，$\Delta f$ 表示频带半宽。

对任一稳定候选 target $T\in\mathcal{T}_{\mathrm{stable}}(t)$，取其复数 slow-time 序列 $z_T(k)$，并进行窗口均值去除：

$$
\tilde{z}_T(k)
=
z_T(k)-\bar{z}_{T,\mathcal{W}},
$$

其中，$\tilde{z}_T(k)$ 表示 target $T$ 的中心化复数 slow-time 序列，$\bar{z}_{T,\mathcal{W}}$ 表示该 target 在窗口 $\mathcal{W}_t$ 内的复数均值，定义为：

$$
\bar{z}_{T,\mathcal{W}}
=
\frac{1}{W}
\sum_{k\in\mathcal{W}_t}
z_T(k).
$$

计算中心化序列的功率谱：

$$
P_T(f)
=
\left|
\mathcal{F}\{\tilde{z}_T(k),k\in\mathcal{W}_t\}
\right|^2.
$$

其中，$P_T(f)$ 表示 target $T$ 的中心化复数 slow-time 序列在频率 $f$ 处的功率谱。定义结构频带能量占比：

$$
G_T(t)
=
\frac{
\sum_{f\in\Omega(t)}P_T(f)
}{
\sum_{f\in\Omega_{\mathrm{valid}}}P_T(f)+\epsilon
}.
$$

其中，$G_T(t)$ 表示 target $T$ 在时刻 $t$ 的结构频带能量占比，分子为该 target 的 IQ 频谱在结构频带 $\Omega(t)$ 内的能量，分母为其在有效分析频带 $\Omega_{\mathrm{valid}}$ 内的总能量，$\epsilon$ 为防止分母为零的小常数。

若：

$$
G_T(t)\ge \tau_G,
$$

则认为 target $T$ 的 IQ 变化主要集中在结构振动频带内，该 target 通过结构频带一致性筛选。其中，$\tau_G$ 为频带一致性阈值。为保持阈值简单，本文可取 $\tau_G=0.5$，即 target IQ 频谱至少一半能量位于结构振动频带内。

最终可用 target 集合定义为：

$$
\mathcal{T}_{\mathrm{valid}}(t)
=
\left\{
T
\mid
R_T(t)\ge \tau_R,\,
G_T(t)\ge \tau_G
\right\}.
$$

其中，$\mathcal{T}_{\mathrm{valid}}(t)$ 表示时刻 $t$ 的可用 range-angle reference targets 集合。目标选择阶段不依赖相位解缠，也不依赖转换系数估计。

## 7. 相位序列输出

对于每个 $T\in\mathcal{T}_{\mathrm{valid}}(t)$，本文输出其复数 slow-time 序列 $z_T(k)$。在目标选取完成之后，可对该复数序列提取相位：

$$
\psi_T(k)=\angle z_T(k).
$$

其中，$\psi_T(k)$ 表示 target $T$ 在第 $k$ 个 slow-time 采样处的 wrapped phase，$\angle(\cdot)$ 表示复数取相角。需要强调的是，相位解缠不参与前面的目标选择判别；目标选择模块只输出复数 slow-time 序列和 wrapped phase。后续转换系数估计阶段如需连续相位，应采用独立的标定阶段粗解缠或小位移无绕转窗口；最终相位分支校正则在结构主相位 Kalman 融合框架内部完成。

## 8. 算法流程

**算法 1：基于距离-角度联合维度的在线参考目标选取**

输入：多通道雷达复数基带数据 $S_k(n,m)$、同步加速度信号 $a(k)$、窗口长度 $W$、候选峰相对幅值阈值 $\rho$、角度合并阈值 $\Delta\theta_{\mathrm{merge}}$ 或 $\Delta u_{\mathrm{merge}}$、窗口出现率阈值 $\tau_R$、频带一致性阈值 $\tau_G$。

输出：当前可用参考 target 集合 $\mathcal{T}_{\mathrm{valid}}(t)$，以及每个 target 的复数 slow-time 序列 $z_T(k)$。

1. 对第 $k$ 帧多通道雷达数据 $S_k(n,m)$ 进行 Range FFT 和 Angle FFT/DBF，得到复数 range-angle map $Y_k(b,p)$。
2. 计算幅值矩阵 $A_k(b,p)=|Y_k(b,p)|$。
3. 根据二维局部峰条件和相对幅值阈值 $\rho A_{\max}(k)$ 得到候选峰集合 $\mathcal{P}_k$。
4. 对 $\mathcal{P}_k$ 中候选峰按 rangeBin $b$ 分组，并对同一 rangeBin 内角度相近的 peaks 进行合并，得到候选 targets $T=(b,\mathcal{C})$。
5. 对每个候选 target $T$，在滑动窗口 $\mathcal{W}_t$ 内计算出现率 $R_T(t)$。
6. 保留满足 $R_T(t)\ge\tau_R$ 的稳定候选集合 $\mathcal{T}_{\mathrm{stable}}(t)$。
7. 由加速度功率谱 $P_a(f)$ 识别结构主频 $f_a(t)$，并确定结构频带 $\Omega(t)$。
8. 对每个 $T\in\mathcal{T}_{\mathrm{stable}}(t)$，计算中心化复数 slow-time 序列 $\tilde{z}_T(k)$ 及其功率谱 $P_T(f)$。
9. 计算结构频带能量占比 $G_T(t)$。
10. 保留满足 $G_T(t)\ge\tau_G$ 的 targets，得到 $\mathcal{T}_{\mathrm{valid}}(t)$。
11. 对每个有效 target 输出 $z_T(k)$ 及其 wrapped phase $\psi_T(k)$。后续转换系数估计阶段可计算标定用连续相位，最终相位解缠在 Kalman 融合框架内部完成。

## 9. 方法支撑与本文改造关系

本文方法不是重新发明毫米波雷达多目标检测，而是将已有工作中可靠的 range-angle phase tracking 思想改造为倒挂式结构位移监测的前置 target extraction 模块。

1. **range-angle phase tracking 来自 mmWBat。** Xiong 等人提出 mmWBat，并证明微动目标的相位演化可以从 range-angle joint dimension 中提取，用于多人生命体征、full-field mechanical vibration measurement 和 scaled bridge dynamic monitoring [Xiong2021]。本文直接继承其核心思想：选定 range-angle component 后，沿 slow-time 追踪该复数单元的相位。

2. **低通道 MIMO-FMCW 的 range-angle 分离有工程支撑。** Ahmad 等人使用 TI mmWave 传感器，在 range-azimuth plane 中分离同一 rangeBin 内不同角度的目标，并进一步提取相位信号 [Ahmad2018]。Qu 等人则使用 Range FFT、Capon angle estimation、2D-CFAR、DBSCAN 和 LCMV beamforming 得到多目标 slow-time phase signal [Qu2024]。这些工作说明，range-angle target extraction 是 MIMO-FMCW 雷达中的成熟链路。

3. **窗口出现确认来自 M-out-of-N 思想。** FMCW 多目标跟踪中常用 candidate track 和 M-out-of-N logic 判断目标是否稳定存在 [Kim2013]。本文不使用完整跟踪滤波器，只将该思想简化为窗口出现率 $R_T(t)$。

4. **结构频带由加速度提供。** Ma 等人在自动校准中利用加速度频谱确定结构主频和滤波频带 [Ma2024]。本文将该频带用于 target IQ 频谱筛选，而不是用于目标选择阶段的位移 RMSE 比较。

本文的主要改造在于：参考目标的基本单元从 rangeBin 升级为 range-angle bin 或 angle cluster。角度可分的散射体被自然拆成多个 targets；角度接近且无法可靠分开的散射簇则作为一个等效 target 处理。这样，后续转换系数估计不再直接面对整个 rangeBin 内方向差异很大的混合相位，而是面对更接近单源或等效单源的 range-angle phase sequence。

## 10. 可写入论文的简要表述

本文提出一种基于距离-角度联合维度的在线参考目标选取方法。受 mmWBat 中 range-angle joint phase evolution tracking 思想启发，本文将传统的 rangeBin 参考目标扩展为 range-angle reference target。首先，对每帧多通道雷达数据进行 Range FFT 和 Angle FFT/DBF，构造复数 range-angle map；随后，在二维幅值图中进行局部峰检测，并对同一 rangeBin 内角度接近的 peaks 进行合并，形成单个 angleBin 或 angle cluster target；接着，利用滑动窗口出现率确认 target 是否稳定存在；最后，利用加速度识别结构振动频带，并通过 target 的中心化复数 slow-time 频谱能量占比判断其是否主要由结构运动驱动。与直接在 rangeBin 上进行相位追踪的方法相比，本文方法将参考目标提升到距离-角度联合维度，既能自然分离同一 rangeBin 内角度差异较大的反射体，又允许角度接近的散射簇作为等效 target 使用，从而为后续转换系数估计和多目标相位融合提供更稳定的输入。

## 11. 参考文献

[Xiong2021] Xiong, Y., Li, S., Gu, C., Meng, G., Peng, Z. Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View. Research, 2021, Article ID 9787484, 2021. 本地文件：`ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`

[Ahmad2018] Ahmad, A., Roh, J. C., Wang, D., Dubey, A. Vital Signs Monitoring of Multiple People using a FMCW Millimeter-Wave Sensor. IEEE Radar Conference, 2018. 本地文件：`ref_papers/01_AoA/Vital Signs Monitoring of Multiple People Using a FMCW Millimeter-Wave Sensor.pdf`

[Qu2024] Yang, Y., Qu, L., Yang, Y., Hu, Q., Yang, T. Multitarget Vital Signs Detection Based on MIMO-FMCW Radar. PIERS, 2024. 本地文件：`ref_papers/01_AoA/Multitarget_Vital_Signs_Detection_Based_on_MIMO-FMCW_Radar.pdf`

[Kim2013] Kim, D.-B., Hong, S.-M. Multiple-target tracking and track management for an FMCW radar network. EURASIP Journal on Advances in Signal Processing, 2013, 159, 2013. 本地文件：`ref_papers/Multiple-target tracking and track management for an FMCW radar network.pdf`

[Ma2023] Ma, Z., Choi, J., Sohn, H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer. Mechanical Systems and Signal Processing, 197, 110408, 2023. 本地文件：`ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`

[Ma2024] Ma, Z., Han, K., Choi, J., Lee, J., Kwon, O., Sohn, H., et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer. Engineering Structures, 321, 118926, 2024. 本地文件：`ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
