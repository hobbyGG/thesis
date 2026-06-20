# Range-Angle Target 的转换系数估计与等效性

## 1. 核心变化

倒挂式毫米波雷达中，雷达随结构共同运动，环境中的静止散射体会因为雷达自身位移产生相位变化。传统处理通常先选定一个 rangeBin，再追踪该 rangeBin 的复数慢时间相位，并利用方向转换系数将雷达视线方向位移转换为结构振动方向位移 [Ma2023, Ma2024]。这一思路在单一散射体主导时有效，但自然反射环境中的一个 rangeBin 可能同时包含多个角度差异较大的强散射体。此时，rangeBin 总相位是多个反射相量的叠加，相位轨迹可能发生畸变，导致用最小二乘拟合得到的转换系数不稳定。

参考 mmWBat 的 range-angle joint phase evolution tracking 思想 [Xiong2021]，本文将参考 target 从 rangeBin 升级为 range-angle target：

$$
T=(b,\mathcal{C}).
$$

其中，$T$ 表示一个参考 target，$b$ 表示 rangeBin 索引，$\mathcal{C}$ 表示同一 rangeBin 内被视为一个 target 的 angleBin 集合。当 $\mathcal{C}$ 只包含一个 angleBin 时，$T$ 是单个 range-angle bin；当 $\mathcal{C}$ 包含多个角度接近的 angleBins 时，$T$ 是一个等效 angle cluster。

这个变化使转换系数问题变得更清楚：

1. 若同一 rangeBin 内多个散射体角度分得开，则它们被拆成多个 range-angle targets，并分别估计转换系数。
2. 若多个散射体角度很近，受天线角分辨率限制落在同一个 angleBin 或 angle cluster 内，则它们可以作为一个等效 target，并估计一个等效转换系数。
3. 若角度差异很大的散射体仍无法被分开，则其相位质量会在频带一致性、相位连续性或转换系数稳定性检查中表现较差，可被剔除或降权。

因此，转换系数估计不再直接作用于整个 rangeBin，而是作用于通过筛选后的 range-angle target。

## 2. 与已有方向转换系数方法的关系

已有雷达-加速度融合结构位移监测研究通常使用如下方向转换关系：

$$
q(k)=\beta d_{\mathrm{LOS}}(k).
$$

其中，$q(k)$ 表示第 $k$ 个 slow-time 采样处的结构振动方向位移，$d_{\mathrm{LOS}}(k)$ 表示毫米波雷达由相位得到的视线方向位移，$\beta$ 表示 direction conversion factor。Ma 等人通常通过初始标定窗口，将雷达相位或雷达位移与加速度参考位移进行拟合，从而得到一个固定转换系数 [Ma2023, Ma2024]。

本文保留这一物理关系，但将 $d_{\mathrm{LOS}}(k)$ 的来源从 rangeBin 相位改为 range-angle target 相位。对于 target $T$，转换关系写为：

$$
q(k)=\beta_T d_T(k).
$$

其中，$d_T(k)$ 表示 target $T$ 的雷达视线方向位移，$\beta_T$ 表示 target $T$ 对应的转换系数。若 target $T$ 是角度接近的散射簇，则 $\beta_T$ 是该散射簇的等效转换系数，而不是某一个单一物理反射点的几何转换系数。

## 3. 由 Range-Angle 相位得到 LoS 位移

目标选择完成后，每个有效 target $T$ 都有一个复数 slow-time 序列：

$$
z_T(k).
$$

其中，$z_T(k)$ 表示 target $T$ 在第 $k$ 个 slow-time 采样处的复数 range-angle phasor。该序列可以来自单个 range-angle bin：

$$
z_T(k)=Y_k(b,p_T),
$$

也可以来自 angle cluster 的固定权重复数合成：

$$
z_T(k)=\sum_{p\in\mathcal{C}}w_pY_k(b,p).
$$

其中，$Y_k(b,p)$ 表示第 $k$ 帧第 $b$ 个 rangeBin、第 $p$ 个 angleBin 处的复数 range-angle phasor；$p_T$ 表示 target $T$ 的代表 angleBin；$w_p$ 表示 angleBin $p$ 的固定合成权重。为避免权重变化引入伪相位，$w_p$ 应在标定或确认窗口内确定，并在该窗口内保持不变。

由 $z_T(k)$ 得到主值相位：

$$
\psi_T(k)=\angle z_T(k).
$$

其中，$\psi_T(k)$ 表示 target $T$ 在第 $k$ 个采样处的 wrapped phase，$\angle(\cdot)$ 表示复数取相角。由于 $\psi_T(k)$ 被限制在 $[-\pi,\pi]$，若直接用于线性拟合，$2\pi$ 分支跳变会污染转换系数估计。因此，转换系数估计需要局部连续相位或预测辅助校正相位，但不要求预先获得全时程完整解缠相位。记该局部连续相位为：

$$
\phi_T^{\mathrm{loc}}(k).
$$

其中，$\phi_T^{\mathrm{loc}}(k)$ 可以来自初始小位移无绕转窗口、短窗口 Itoh 局部解缠，也可以来自 AoA 几何初值启动后的 Kalman/Doppler 预测辅助分支校正。这里需要强调，$\phi_T^{\mathrm{loc}}(k)$ 不是预先完成的最终全时程解缠相位，而是用于转换系数自举或局部拟合的连续相位片段。然后可将该局部相位转换为雷达视线方向位移：

$$
d_T^{\mathrm{loc}}(k)=\frac{\lambda}{4\pi}\left[\phi_T^{\mathrm{loc}}(k)-\bar{\phi}_T^{\mathrm{loc}}\right].
$$

其中，$d_T^{\mathrm{loc}}(k)$ 表示 target $T$ 在局部窗口内的中心化 LoS 位移，$\lambda$ 表示雷达载波波长，$\bar{\phi}_T^{\mathrm{loc}}$ 表示该窗口内 $\phi_T^{\mathrm{loc}}(k)$ 的均值。

需要特别说明：目标选择阶段不依赖相位解缠；转换系数自举阶段只需要短窗口内的相位分支正确，而不需要在 Kalman 之前完成最终意义上的在线相位解缠。本文最终框架采用 range-angle 几何关系给出 $\beta_T^{(0)}$，并在冷启动后由加速度预测和较大的初始测量噪声支撑 Kalman 递推启动；随后，预测辅助校正后的局部连续相位用于修正 $\beta_T$。若直接使用 wrapped phase，一旦相位跨越 $\pm\pi$，相位序列会出现人为跳变，最小二乘估计的转换系数会被严重污染。只有当工作位移很小、相位从未发生 wrapping 时，wrapped phase 才可能在中心化后近似可用。对于 77 GHz 雷达，$2\pi$ 相位约对应 $\lambda/2\approx1.95\text{ mm}$ 的 LoS 位移，因此毫米级结构振动已经可能出现相位绕转。

## 4. 最小二乘转换系数

设加速度传感器在同一标定窗口内给出的结构参考位移为：

$$
q_a(k).
$$

其中，$q_a(k)$ 表示第 $k$ 个 slow-time 采样处由加速度信号得到的结构振动方向参考位移。实际计算时，可先对 $q_a(k)$ 和 $d_T^{\mathrm{loc}}(k)$ 进行窗口均值去除：

$$
\tilde{q}_a(k)=q_a(k)-\bar{q}_a,
$$

$$
\tilde{d}_T(k)=d_T^{\mathrm{loc}}(k)-\bar{d}_T.
$$

其中，$\tilde{q}_a(k)$ 表示中心化后的加速度参考位移，$\bar{q}_a$ 表示局部窗口内 $q_a(k)$ 的均值，$\tilde{d}_T(k)$ 表示中心化后的 target LoS 位移，$\bar{d}_T$ 表示局部窗口内 $d_T^{\mathrm{loc}}(k)$ 的均值。若 $d_T^{\mathrm{loc}}(k)$ 已按上一节由相位均值中心化，则通常有 $\bar{d}_T\approx0$。

本文采用过原点的一维最小二乘估计 target $T$ 的转换系数：

$$
\hat{\beta}_T
=
\arg\min_{\beta}
\sum_{k\in\mathcal{W}_{\mathrm{cal}}}
\left[
\beta\tilde{d}_T(k)-\tilde{q}_a(k)
\right]^2.
$$

其中，$\hat{\beta}_T$ 表示 target $T$ 的转换系数估计值，$\beta$ 表示待估计的标量转换系数，$\mathcal{W}_{\mathrm{cal}}$ 表示用于标定的采样窗口。该问题的闭式解为：

$$
\hat{\beta}_T
=
\frac{
\sum_{k\in\mathcal{W}_{\mathrm{cal}}}
\tilde{d}_T(k)\tilde{q}_a(k)
}{
\sum_{k\in\mathcal{W}_{\mathrm{cal}}}
\tilde{d}_T^2(k)
}.
$$

其中，分子表示 target LoS 位移与加速度参考位移的内积，分母表示 target LoS 位移的能量。若 $d_T(k)$ 和 $q_a(k)$ 已经在预处理阶段完成去均值，则上式可简写为：

$$
\hat{\beta}_T
=
\frac{
\sum_{k}d_T(k)q_a(k)
}{
\sum_{k}d_T^2(k)
}.
$$

该闭式解是标准的一维线性最小二乘解，本质上是在标定窗口内寻找一个标量，使雷达 LoS 位移经比例缩放后最接近加速度参考位移。

## 5. Range-Angle Target 内的等效转换系数

一个 range-angle target $T=(b,\mathcal{C})$ 仍可能包含不止一个物理散射体。区别在于，angleBin 或 angle cluster 已经限制了散射体的入射方向范围，因此 target 内部散射体的投影系数通常比整个 rangeBin 内更接近。

设 target $T$ 内有 $L$ 个静止散射体，并忽略噪声和固定直流项，其复数回波可写为：

$$
z_T(q)
=
\sum_{\ell=1}^{L}
c_\ell
\exp\left(-j\gamma\eta_\ell q\right).
$$

其中，$z_T(q)$ 表示结构位移为 $q$ 时 target $T$ 的复数回波，$q$ 表示结构真实振动方向位移，$c_\ell=A_\ell e^{j\phi_\ell^0}$ 表示第 $\ell$ 个散射体的复幅值，$A_\ell$ 表示该散射体幅值，$\phi_\ell^0$ 表示其初始相位，$\eta_\ell$ 表示该散射体 LoS 方向与结构运动方向之间的投影系数，$\gamma=4\pi/\lambda$ 表示相位-位移比例系数。

若 target 内所有主要散射体的投影系数接近：

$$
\eta_1\approx\eta_2\approx\cdots\approx\eta_L\approx\eta_{\mathrm{eq}},
$$

则：

$$
z_T(q)
\approx
\left(\sum_{\ell=1}^{L}c_\ell\right)
\exp\left(-j\gamma\eta_{\mathrm{eq}}q\right).
$$

其中，$\eta_{\mathrm{eq}}$ 表示该 angle cluster 的等效 LoS 投影系数。此时，多个角度相近的散射体可以作为一个等效 target 使用，其等效转换系数为：

$$
\beta_{\mathrm{eq}}\approx\frac{1}{\eta_{\mathrm{eq}}}.
$$

这说明，角度接近的散射体不需要被强行拆开；如果它们在 IWR1843 的角分辨能力内本来就不可可靠分离，则将其合并为一个等效 range-angle target 反而更符合物理和硬件能力。

## 6. 等效转换系数的稳定性

等效转换系数是否可靠，取决于 target 内部多个散射体的复数叠加相位是否可以近似表示为单一线性相位。对 $z_T(q)$ 的总相位：

$$
\Psi_T(q)=\arg z_T(q)
$$

求导，可得到局部等效投影系数：

$$
\eta_{\mathrm{loc}}(q)
=
-\frac{1}{\gamma}
\frac{d\Psi_T(q)}{dq}
=
\operatorname{Re}
\left\{
\frac{
\sum_{\ell=1}^{L}
\eta_\ell c_\ell e^{-j\gamma\eta_\ell q}
}{
\sum_{\ell=1}^{L}
c_\ell e^{-j\gamma\eta_\ell q}
}
\right\}.
$$

其中，$\Psi_T(q)$ 表示 target $T$ 的总相位，$\eta_{\mathrm{loc}}(q)$ 表示结构位移为 $q$ 时的局部等效投影系数，$\operatorname{Re}\{\cdot\}$ 表示取复数实部。该式说明：

1. 若所有 $\eta_\ell$ 接近，$\eta_{\mathrm{loc}}(q)$ 近似为常数，固定转换系数有效。
2. 若一个散射体幅值明显占主导，$\eta_{\mathrm{loc}}(q)$ 近似等于主导散射体的投影系数，固定转换系数仍然有效。
3. 若多个散射体幅值接近、投影系数差异较大，并且结构位移幅值足以造成明显相对相位变化，则 $\eta_{\mathrm{loc}}(q)$ 会随 $q$ 改变，固定转换系数只能作为标定窗口内的最佳线性近似。

这也是本文先做 range-angle target extraction 的原因：相比整个 rangeBin，range-angle target 显著缩小了可参与叠加的角度范围，从源头上降低了 $\eta_\ell$ 差异。

## 7. 两个散射体的直观分析

考虑 target $T$ 内只有两个主要散射体：

$$
z_T(q)
=
A_1e^{j\phi_1}e^{-j\gamma\eta_1q}
+
A_2e^{j\phi_2}e^{-j\gamma\eta_2q}.
$$

其中，$A_1$ 和 $A_2$ 分别表示两个散射体的幅值，$\phi_1$ 和 $\phi_2$ 分别表示两个散射体的初始相位，$\eta_1$ 和 $\eta_2$ 分别表示两个散射体的 LoS 投影系数。定义幅值比：

$$
\rho=\frac{A_2}{A_1},
$$

以及两个散射体之间的相对相位：

$$
\Theta(q)=\phi_2-\phi_1-\gamma(\eta_2-\eta_1)q.
$$

其中，$\rho$ 表示第二个散射体相对第一个散射体的幅值比，$\Theta(q)$ 表示结构位移为 $q$ 时两个散射体之间的相对相位。此时局部等效投影系数可写为：

$$
\eta_{\mathrm{loc}}(q)
=
\eta_1
+
(\eta_2-\eta_1)
\frac{
\rho\cos\Theta(q)+\rho^2
}{
1+2\rho\cos\Theta(q)+\rho^2
}.
$$

由此可以得到三个结论。第一，若 $\eta_1=\eta_2$，则 $\eta_{\mathrm{loc}}(q)$ 恒定，两个散射体可以完美等效为一个 target。第二，若 $\rho\ll1$，即第一个散射体显著占主导，则 $\eta_{\mathrm{loc}}(q)\approx\eta_1$，固定转换系数仍然有效。第三，只有当 $\rho$ 不小、$\eta_1$ 与 $\eta_2$ 差异明显，并且 $\Theta(q)$ 在工作位移范围内发生明显变化时，固定转换系数才会出现幅值相关或窗口相关误差。

## 8. 角度接近时为何可以合并

对于竖向结构振动，设第 $\ell$ 个散射体的 LoS 与竖直运动方向夹角为 $\alpha_\ell$，则其投影系数为：

$$
\eta_\ell=\cos\alpha_\ell.
$$

其中，$\alpha_\ell$ 表示第 $\ell$ 个散射体的 LoS 与竖直方向之间的夹角。两个散射体之间的投影系数差为：

$$
\Delta\eta
=
|\cos\alpha_1-\cos\alpha_2|.
$$

其中，$\Delta\eta$ 表示两个散射体 LoS 投影系数的差异。令：

$$
\bar{\alpha}=\frac{\alpha_1+\alpha_2}{2},
$$

$$
\Delta\alpha=|\alpha_1-\alpha_2|.
$$

其中，$\bar{\alpha}$ 表示两个散射体夹角的平均值，$\Delta\alpha$ 表示两个散射体夹角差。则：

$$
\Delta\eta
=
2
|\sin\bar{\alpha}\sin(\Delta\alpha/2)|.
$$

当 $\Delta\alpha$ 较小时，有近似关系：

$$
\Delta\eta\approx|\sin\bar{\alpha}|\Delta\alpha.
$$

若结构振动位移幅值为 $Q$，两个散射体之间的相对相位摆动幅值近似为：

$$
\Delta\Theta
=
\gamma Q\Delta\eta
=
\frac{4\pi}{\lambda}Q
|\cos\alpha_1-\cos\alpha_2|.
$$

其中，$\Delta\Theta$ 表示两个散射体因投影系数不同而产生的相对相位摆动幅值，$Q$ 表示结构振动位移幅值。对于 77 GHz 雷达，$\lambda\approx3.9\text{ mm}$。若 $Q=2\text{ mm}$，则：

$$
\frac{4\pi}{\lambda}Q\approx6.44.
$$

因此：

$$
\Delta\Theta\approx6.44|\cos\alpha_1-\cos\alpha_2|.
$$

这说明，若散射体集中在相近角度，$\Delta\eta$ 较小，相对相位摆动也较小，合并为一个等效 target 是合理的；若同一 target 内同时包含正下方散射体和大斜角散射体，则 $\Delta\eta$ 变大，更容易出现转换系数漂移。这与本文的处理策略一致：角度相近的 angleBins 合并为等效 target，角度差异明显的 peaks 尽量在 range-angle map 中拆开。

## 9. 转换系数稳定性检查

虽然 range-angle target 已经降低了混叠风险，但仍可在标定阶段检查转换系数是否稳定。设标定数据被划分为 $L_w$ 个短窗口，并在第 $r$ 个短窗口内估计得到：

$$
\hat{\beta}_T^{(r)},\qquad r=1,2,\ldots,L_w.
$$

其中，$\hat{\beta}_T^{(r)}$ 表示 target $T$ 在第 $r$ 个短窗口内的转换系数估计值，$L_w$ 表示短窗口数量。定义转换系数稳定性指标：

$$
S_{\beta,T}
=
\frac{
\operatorname{std}\left(\hat{\beta}_T^{(1)},\hat{\beta}_T^{(2)},\ldots,\hat{\beta}_T^{(L_w)}\right)
}{
\left|
\operatorname{mean}\left(\hat{\beta}_T^{(1)},\hat{\beta}_T^{(2)},\ldots,\hat{\beta}_T^{(L_w)}\right)
\right|
}.
$$

其中，$S_{\beta,T}$ 表示 target $T$ 的转换系数相对稳定性指标，$\operatorname{std}(\cdot)$ 表示标准差，$\operatorname{mean}(\cdot)$ 表示均值。$S_{\beta,T}$ 越小，说明该 target 在不同短窗口内的等效转换关系越稳定。该指标可作为卡尔曼滤波前的 target 质量检查或后续多目标融合权重的依据。

需要注意，本文的主选择流程仍然保持简单：候选发现、滑动窗口出现确认和结构频带一致性筛选不依赖 $\hat{\beta}_T$。转换系数稳定性检查发生在 target 通过筛选并完成局部连续相位估计或预测辅助相位校正之后，可作为后续自适应观测噪声和实验评价的依据。

## 10. 闭环 Kalman 前后的接口

经过 range-angle target selection 和冷启动初始化后，进入闭环 Kalman 前至少可得到如下 target 集合：

$$
\left\{
T_i,\ z_{T_i}(k),\ \psi_{T_i}(k),\ \theta_{T_i},\ \beta_{T_i}^{(0)},\ b_{T_i}
\right\}_{i=1}^{N_T}.
$$

其中，$N_T$ 表示当前可用 targets 数量，$T_i$ 表示第 $i$ 个有效 range-angle target，$z_{T_i}(k)$ 表示其复数 slow-time 序列，$\psi_{T_i}(k)$ 表示 wrapped phase，$\theta_{T_i}$ 表示该 target 的 AoA 几何角，$\beta_{T_i}^{(0)}$ 表示由 AoA 给出的转换系数初值，$b_{T_i}$ 表示冷启动阶段确定的初始相位偏置。后续在线 Kalman 融合阶段重新使用原始 wrapped phase，并在 Kalman 递推内部完成最终相位分支校正和转换系数自举更新。

在初始微振阶段，预测辅助校正相位可用于更新：

$$
\left\{
\hat{\beta}_{T_i,k},\ e_{\beta,T_i,k},\ S_{\beta,T_i,k}
\right\}_{i=1}^{N_T}.
$$

其中，$\hat{\beta}_{T_i,k}$ 表示递推修正后的转换系数，$e_{\beta,T_i,k}$ 和 $S_{\beta,T_i,k}$ 可用于描述该 target 的转换关系质量。后续卡尔曼滤波或多目标相位融合主要使用原始 wrapped phase、当前转换系数和自适应测量噪声作为输入，而不是依赖单目标标定位移作为最终观测。

## 11. 可写入论文的简要表述

本文在距离-角度联合维度中定义参考 target，并为每个通过筛选的 range-angle target 建立方向转换关系。目标选择阶段仅使用幅值峰、窗口出现率和结构频带一致性，不依赖相位解缠和转换系数。目标通过筛选后，本文首先利用 AoA 几何关系给出转换系数初值，并在冷启动阶段确定初始相位偏置；随后，在结构初始微振阶段，利用加速度驱动的结构主相位 Kalman 预测对 wrapped phase 进行分支校正，并用局部连续相位片段递推修正转换系数。对于角度接近而无法可靠分开的 angleBins，本文将其合并为一个等效 target，并估计等效转换系数。理论分析表明，当合并 target 内主要散射体的 LoS 投影系数接近或由单一散射体主导时，其复数相位可以稳定等效为一个线性 LoS 投影关系；只有当多个强散射体的投影系数差异较大且相对相位随结构位移明显变化时，固定转换系数才会出现漂移。因此，将参考目标从 rangeBin 升级到 range-angle target 可以显著降低转换系数畸变风险，并为后续结构主相位 Kalman 融合提供更稳定的多目标输入。

## 12. 参考文献

[Xiong2021] Xiong, Y., Li, S., Gu, C., Meng, G., Peng, Z. Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View. Research, 2021, Article ID 9787484, 2021. 本地文件：`ref_papers/01_AoA/Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`

[Ma2023] Ma, Z., Choi, J., Sohn, H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer. Mechanical Systems and Signal Processing, 197, 110408, 2023. 本地文件：`ref_papers/00_primary_references/Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer.pdf`

[Ma2024] Ma, Z., Han, K., Choi, J., Lee, J., Kwon, O., Sohn, H., et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer. Engineering Structures, 321, 118926, 2024. 本地文件：`ref_papers/00_primary_references/Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer.pdf`
