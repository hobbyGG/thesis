# 新对话接续 Prompt：倒挂式毫米波雷达论文思路

下面内容用于在新对话框中接续当前论文讨论。请新对话中的 agent 先完整阅读本文件，再根据需要阅读相关草稿文件。

## 可直接复制到新对话框的 Prompt

你是我的论文协作助手，工作目录是 `/Users/umep/thesis`。请用中文和我讨论，公式必须使用 Obsidian 支持的 `$...$` 和 `$$...$$`，不要使用 math fenced code block。

我正在写一篇关于**倒挂式毫米波雷达结构位移监测**的论文。雷达安装在桥梁/结构测点上，随结构一起运动，向下或斜向观测周围静止参考物。当前实验雷达是 **TI IWR1843**，属于 76-81 GHz FMCW mmWave radar，3TX/4RX MIMO，虚拟阵列规模有限。后续 AoA / range-angle 方法必须考虑 IWR1843 的实际能力，不能推荐需要大规模阵列、大量 snapshots 或复杂离线优化的方法作为主方案。

请优先阅读以下文件：

1. `/Users/umep/thesis/thesis_idea_overview.md`
   - 这是当前论文整体思路说明，已经同步到最新版转换系数方案。
   - 包含数学模型、关键结论、Ma 等人的转换因子方法、AoA 初始化与独立转换系数预校准、IWR1843 硬件约束。
2. `/Users/umep/thesis/idea/overall_processing_architecture.md`
   - 这是整体架构参考文档。
   - 其中若仍出现 Kalman posterior 或 LoS corrected phase 在线反哺 $\beta_i$ 的段落，均是尚待同步的历史方案；转换系数部分以本 Prompt 和 `thesis_idea_overview.md` 的当前口径为准。
3. `/Users/umep/thesis/innovation_points/multi_target_phase_kalman_fusion.md`
   - 这是结构主相位多 target Kalman 融合创新点的参考说明。
   - 其中在线自举表述已弃用；当前区别是状态变量由单 target LoS 相位改为结构主相位，$\beta_i$ 在 Kalman 前经独立原始数据预校准或精确回退 AoA，并在完整滤波期间冻结。
4. `/Users/umep/thesis/draft_inverted_radar_theory_model.md`
   - 这是更完整的倒挂式毫米波雷达理论章节草稿。
   - 包含 mmVib 相位模型、倒挂几何模型、FMCW 回波模型、IQ 模型、多 target、角度门控等内容。
5. `/Users/umep/thesis/ref_papers/00_primary_references/README.md`
   - 这是主参考文献说明。
   - 重点文献包括 mmVib 论文和 Ma/Zhanxiong 系列雷达 + 加速度/应变/相位解缠论文。

当前讨论的核心不是重新发明毫米波雷达测距理论，而是：

> 基于 mmVib 的相位测量理论，建立倒挂式毫米波雷达的结构位移估计框架：前端从 range-angle map 中在线筛选多个可用静止参考 target；后端参考 Ma 等人的 acceleration-aided Kalman filtering 思想，但将状态变量从单 target LoS 相位改为结构振动方向主相位。滤波前先以 AoA 给出 $\beta_i$ 初值，再由原始多 target phase 的双折 rank-1 共同运动估计逐目标相对投影，并用 native-timestamp ADXL 提供独立动力学门控、绝对候选和公共时延。未验证记录固定走 AoA 锚定相对模式，`validated` 记录固定走 ADXL 绝对模式；全局门失败整组回退，逐目标门失败只回退该 target。随后冻结整组 $\beta_i$，从第 0 帧运行完整 Kalman，绝不使用 Kalman posterior 或 LoS corrected phase 反哺 $\beta_i$。

## 当前最新版方法流程

### 0.1 前端 target selection 不依赖相位解缠

ADC 数据经过 Range FFT 和 Angle FFT / DBF 得到复数 range-angle map。二维峰值检测得到 $M$ 个候选 target；同一 rangeBin 内 AoA 差异小于 $15^\circ$ 的 target 可视为等效 target；随后通过滑动窗口稳定性和结构频带一致性筛选，输出 $m$ 个可用 target，$m\le M$。

该阶段只输出 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k),
\qquad
\psi_{i,k}\in(-\pi,\pi],
$$

不做最终意义上的相位解缠，也不预先估计精确转换系数。

### 0.2 AoA 初值与独立 beta 预校准

Ma 论文里的 direction conversion factor 本文统一记为 $\beta_i$，方向是：

$$
q_k=\beta_i d_{i,k}^{\mathrm{LOS}},
\qquad
\Theta_k=\beta_i\phi_{i,k}^{\mathrm{LOS}}.
$$

对第 $i$ 个 target，用 AoA 先给出结构方向到 LoS 的几何投影初值，再取其倒数作为 $\beta_i$ 初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|,
\qquad
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}.
$$

AoA 初值不是最终精确转换系数。任何 Kalman 递推开始前，先仅从原始多 target slow-time phase 搜索公共角偏差候选 $\delta$：

$$
p_i(\delta)=|\cos(\theta_i-\delta)|,
\qquad
\beta_i(\delta)=\frac{1}{\max(p_i(\delta),\epsilon_p)}.
$$

该候选不得使用 Kalman posterior、结构主相位后验或 LoS corrected phase。公共角偏差仅作辅助诊断/消融，不进入正式逐目标拟合先验；真正的逐目标候选由原始相位的双折 rank-1 共同运动结构得到，并用 ADXL native timestamps 上的原始加速度做独立动力学/绝对时域校准。相对模式至少需要三个训练/holdout 均与 ADXL 相干的参考 target，且两折 rank-1 占比均过门。时间轴、激励、公共时延、参考数量或共同运动门失败时整组回退；单个 target 的连续性、相干性、物理边界、跨折一致性或条件 holdout 改善失败时只回退该 target。不得复用公共偏差结果或历史缓存。接受值与回退值合成 $\tilde{\boldsymbol{\beta}}$ 后冻结，再从第 0 帧运行完整 Kalman。初始近静止段仍可用于估计相位偏置 $b_i$ 和 target-wise 测量噪声初值 $r_{i,0}$，但不构成在线 beta 自举。

### 0.3 Kalman 状态是结构主相位，不是 Ma 的单 target LoS 相位

本阶段只在独立校准接受或 AoA 精确回退、并冻结 $\tilde{\boldsymbol{\beta}}$ 后启动。状态变量定义为：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix},
\qquad
\Theta_k=\frac{4\pi}{\lambda}q_k.
$$

加速度直接进入系统模型预测结构主相位：

$$
\mathbf{x}_k^-=
\mathbf{A}\mathbf{x}_{k-1}
+
\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}.
$$

第一版方法中 $Q$ 固定，可采用常加速度模型形式：

$$
\mathbf{Q}
=
q
\begin{bmatrix}
T^3/3 & T^2/2\\
T^2/2 & T
\end{bmatrix}.
$$

### 0.4 冻结 beta 后的预测辅助相位校正只服务 Kalman 观测

雷达 phase wrapping 发生在 LoS 相位空间，因此分支选择时需要先把结构主相位预测投影回 LoS：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\tilde{\beta}_i}+b_i.
$$

然后对原始 wrapped phase 执行预测辅助相位校正：

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

注意：$\phi_{i,k}^{\mathrm{LOS,corr}}$ 仍是第 $i$ 个 target 的 LoS 连续相位，不是结构主相位 $\Theta_k$。

该 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 只用于构造结构方向主相位观测：

$$
y_{i,k}
=
\tilde{\beta}_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

Kalman 观测模型写在结构方向：

$$
y_{i,k}=\Theta_k+e_{i,k},
\qquad
H_i=[1,0].
$$

LoS corrected phase 不进入任何转换系数拟合，也不反馈更新 $\tilde{\beta}_i$。当前数据流固定为：

$$
\text{原始 target phase + AoA + native-timestamp ADXL}
\rightarrow
\text{独立预校准 + holdout}
\rightarrow
\text{接受冻结 beta 或精确回退 AoA}
\rightarrow
\text{从第 0 帧完整 Kalman}.
$$

旧的“LoS corrected phase 或 Kalman posterior $\rightarrow\beta_{i,k+1}$”方案已弃用，仅保留为历史讨论。当前代码与正文统一采用结构方向观测模型 $H_i=[1,0]$。

### 0.5 当前噪声策略

第一版采用固定 $Q$、自适应 target-wise $R^\Theta$。结构方向残差可写为：

$$
s_{i,k}=y_{i,k}-H_i\mathbf{x}_k
$$

调节：

$$
r_{i,k+1}
=
\operatorname{clip}
\left[
\alpha r_{i,k}
+
(1-\alpha)
\left(
s_{i,k}^{2}
+
H_i\mathbf{P}_kH_i^{T}
\right),
r_{\min},
r_{\max}
\right].
$$

转换系数不确定性在 Kalman 前通过独立校准的接受/精确回退门控消化；$\tilde{\beta}_i$ 在线保持冻结。$R$ 的自适应只反映 target phase 质量、结构方向残差和观测一致性，不得再解释为在线 beta 收敛过程，也不得以 $R$ 回落反证 beta 校准成功。

## 已形成的关键理论结论

### 1. 距离模型：倒挂和普通模型基本一致

普通 mmVib / 固定雷达模型中，雷达固定，目标振动：

$$
D(t)=D_0+x(t)
$$

相位变化为：

$$
\Delta\phi(t)=\frac{4\pi}{\lambda}x(t)
$$

倒挂式场景中，雷达随结构运动，环境目标静止。设雷达初始位置为 $\mathbf{p}_r^0$，结构位移为 $\mathbf{u}(t)$，第 $i$ 个静止反射目标位置为 $\mathbf{p}_i$：

$$
D_i(t)=\left\|\mathbf{p}_i-\mathbf{p}_r^0-\mathbf{u}(t)\right\|
$$

令：

$$
\mathbf{r}_i^0=\mathbf{p}_i-\mathbf{p}_r^0,\qquad
D_i^0=\left\|\mathbf{r}_i^0\right\|,\qquad
\mathbf{n}_i=\frac{\mathbf{r}_i^0}{D_i^0}
$$

小位移一阶近似：

$$
\Delta D_i(t)\approx -\mathbf{n}_i^\mathrm{T}\mathbf{u}(t)
$$

若结构主要沿方向 $\mathbf{e}$ 运动，$\mathbf{u}(t)=\mathbf{e}q(t)$：

$$
\Delta D_i(t)\approx -\eta_i q(t),\qquad
\eta_i=\mathbf{n}_i^\mathrm{T}\mathbf{e}
$$

相位变化：

$$
\Delta\phi_i(t)\approx -\frac{4\pi}{\lambda}\eta_i q(t)
$$

结构位移恢复：

$$
q(t)\approx -\frac{\lambda}{4\pi\eta_i}
\operatorname{unwrap}\left(\Delta\phi_i(t)\right)
$$

结论：从距离-相位模型看，倒挂和普通安装本质上差别不大，主要是正负号和 LOS 投影系数 $\eta_i$。正负号受坐标定义和混频共轭约定影响，不是关键；关键是 $|\eta_i|$。

### 2. 回波模型也基本一致

FMCW 回波相位模型本身不变。普通模型中可以理解为：

$$
S(t)=A\exp\left[j\left(\phi_0+\frac{4\pi}{\lambda}x(t)\right)\right]
$$

倒挂式第 $i$ 个静止目标：

$$
Z_i(k)=A_i(k)\exp\left(j\frac{4\pi}{\lambda}D_i(k)\right)
$$

代入：

$$
D_i(k)\approx D_i^0-\eta_i q(k)
$$

得到：

$$
Z_i(k)\approx
A_i(k)
\exp\left[
j\left(
\phi_i^0-\frac{4\pi}{\lambda}\eta_i q(k)
\right)
\right]
$$

因此倒挂式回波模型可以看成将 mmVib 中的目标振动位移 $x(k)$ 替换为：

$$
x_{\mathrm{equiv},i}(k)=-\eta_i q(k)
$$

结论：距离模型和回波模型不是本文最主要的差异点。真正关键的是 IQ 模型和 target 选择。

### 3. mmVib 的 IQ 模型：固定雷达下的背景中心偏移

mmVib 的 IQ 分析是在选定目标所在 range bin 或 range-angle bin 后，对该单元 slow-time 复数序列进行分析。

固定雷达场景中，实测 IQ 信号写成：

$$
S'(t)=S(t)+S_B+w(t)
$$

其中：

- $S(t)$ 是真实振动目标反射；
- $S_B$ 是静态背景/杂波合成的复向量；
- $w(t)$ 是噪声。

因为雷达固定、背景固定，所以：

$$
S_B=C_I+jC_Q
$$

在 IQ 平面中，$S_B$ 表现为圆心偏移，真实振动分量 $S(t)$ 围绕该偏移中心旋转。mmVib 通过圆拟合估计中心，再将圆心平移回原点，提取真实振动相位。

注意：静态背景不是随机噪声。静态背景导致固定圆心偏移；随机噪声导致圆弧变厚、发散和拟合不稳定。

### 4. 倒挂场景下 IQ 模型的真正差异

倒挂式场景中，雷达自身随结构运动。环境中的地面、桥下构件、固定支架等“静止参考物”在地面坐标系中静止，但相对于雷达的距离会随结构位移变化。

所以这些静止反射体不再天然构成 mmVib 意义上的固定背景中心，它们也会产生由 $q(k)$ 驱动的相位旋转。

如果只选一个 rangeBin $b$，则该 bin 是一个等距离反射单元，不是一个物理 target。二维中可理解为以雷达为中心、rangeBin 半径对应的圆弧面；三维中更接近球面壳的一部分。落在该距离单元内且被雷达照到的强散射体都会复数叠加。

一般模型：

$$
Y_b(k)=
\sum_{m\in\mathcal{B}_b}
A_m(k)
\exp\left[
j\left(
\phi_m^0-\frac{4\pi}{\lambda}\eta_m q(k)
\right)
\right]
+D_b+w_b(k)
$$

其中 $\mathcal{B}_b$ 是落入该 rangeBin 或 range-angle bin 的散射体集合，$\eta_m$ 是第 $m$ 个散射体的 LOS 投影系数，$D_b$ 是硬件直流偏置/泄漏/近似常量项。

### 5. 由 IQ 模型得到的三类关键情况

#### 情况 1：单一主导静止 target

如果一个 bin 内实际由一个强反射体主导：

$$
Y_b(k)\approx
A_i(k)
\exp\left[
j\left(
\phi_i^0-\frac{4\pi}{\lambda}\eta_i q(k)
\right)
\right]
+D_b+w_b(k)
$$

若 $D_b$ 很小，IQ 轨迹近似绕原点形成圆弧；若有常量偏置，则绕固定偏移点形成圆弧。此时相位提取最稳定，Ma 式转换因子可直接解释为该反射物 LOS 与结构运动方向之间的投影关系。

如果结构运动方向是绝对竖直方向，拟合得到的等效角度基本就是反射物 LOS 与绝对竖直方向的夹角。

#### 情况 2：多个角度相近的强静止散射体

如果同一 bin 内存在多个强静止散射体，但它们角度相近：

$$
\eta_1\approx \eta_2\approx \cdots \approx \eta_0
$$

则这些散射体的相位旋转趋势接近，复数叠加后仍可能形成规则的等效圆弧：

$$
Y_b(k)
\approx
\left(
\sum_m A_m e^{j\phi_m^0}
\right)
e^{-j\frac{4\pi}{\lambda}\eta_0 q(k)}
$$

此时拟合得到的是一个等效共同 LOS 投影角，可用于 angle gate，但要注意它可能不是某个单一物理点的角度，而是散射簇的等效角度。

#### 情况 3：多个角度不同的强静止散射体形成复合 target

如果同一 rangeBin 内存在多个强散射体，且角度不同、投影系数差异明显：

$$
\eta_1,\eta_2,\eta_3
$$

差异较大，则每个散射体相位旋转速率不同。但这些散射体仍然都由同一个结构位移 $q(k)$ 驱动，因此总 IQ 信号不是随机噪声，而是一个确定的复合相位观测：

$$
Y_b(k)=
\sum_m
A_m
\exp\left[
j\left(
\phi_m^0-\frac{4\pi}{\lambda}\eta_m q(k)
\right)
\right]
+D_b+w_b(k)
$$

若在当前工作位移范围内，总相位可以近似表示为：

$$
\arg Y_b(k)\approx
\phi_b^0-\frac{4\pi}{\lambda}\eta_{\mathrm{eq}}q(k)
$$

则该 rangeBin 可以作为一个复合等效 target 使用。此时 Ma 式方法或其他拟合方法得到的是复合散射簇的等效转换因子，不是某个单一反射点的真实几何角度，但仍可用于位移恢复。

只有当多个散射体贡献接近、$\eta_m$ 差异较大、且结构位移幅值足以造成明显相对相位变化时，总相位与 $q(k)$ 之间才可能出现非线性关系，表现为 IQ 圆弧厚化、弯曲、幅值凹陷、相位跳变或转换因子随窗口漂移。

这类情况有两个出口：

1. 若复合 target 的等效转换因子稳定、雷达-加速度残差小、相位连续，则直接作为一个等效 target 使用；
2. 若复合 target 不能稳定等效，且有 AoA / range-angle 信息，则拆成多个 range-angle target，分别估计角度和转换因子；
3. 若不能稳定等效且无法拆分，则识别为混叠并剔除。

### 6. 情况 3 的稳定等效、识别与拆分思路

情况 3 不能直接等同于“不可靠”。应先判断它是否能作为复合等效 target 使用；只有不能稳定等效时，才进入角度拆分或剔除。

可用指标：

1. **range-angle 谱峰值数量**
   - 单一强峰：倾向情况 1；
   - 多个角度接近的强峰：倾向情况 2；
   - 多个角度差异明显且强度接近的峰：倾向复合 target，需要进一步验证是否稳定等效。

2. **IQ 单圆弧拟合残差**

$$
r_{\mathrm{circle}}
=
\frac{
\sqrt{
\frac{1}{N}
\sum_k
\left(
|Y_b(k)-C|-R
\right)^2
}
}{R}
$$

情况 1、2 通常残差小；情况 3 如果能稳定等效，残差也可能较小。圆弧残差大只能说明该复合 target 不适合直接等效，不能单独用来证明“多散射体一定不可用”。

3. **转换因子稳定性**

滑动窗口估计：

$$
\hat{\beta}^{(1)},\hat{\beta}^{(2)},\ldots,\hat{\beta}^{(L)}
$$

如果：

$$
\frac{\operatorname{std}(\hat{\beta})}
     {\operatorname{mean}(\hat{\beta})}
$$

较大，说明转换因子不稳定，可能存在不能稳定等效的角度混叠。

4. **加速度-雷达一致性残差**

用拟合后的转换因子：

$$
q_r(k)=\hat{\beta}d_r(k)
$$

与加速度参考 $q_a(k)$ 比较：

$$
E=
\sqrt{
\frac{1}{N}
\sum_k
\left[
q_r(k)-q_a(k)
\right]^2
}
$$

残差大或 coherence 低，则说明该 bin 不适合作为直接复合 target，需要尝试角度拆分或剔除。

若 IWR1843 的 MIMO 数据可用，处理逻辑不是无条件拆分，而是：

1. 选定 rangeBin $b$；
2. 先把该 bin 作为复合等效 target，拟合转换因子并检查残差、coherence、相位连续性和窗口稳定性；
3. 若通过检查，直接保留该 range target；
4. 若不通过，再计算角度谱 $P_b(\theta)$；
5. 找角度峰 $\theta_1,\theta_2,\ldots,\theta_M$；
6. 对每个角度峰做 angle gate 或 digital beamforming，得到 $Y_{b,\theta_j}(k)$；
7. 对每个 $Y_{b,\theta_j}(k)$ 分别做 IQ 圆弧检查、相位提取、加速度拟合转换因子、残差和稳定性判断；
8. 保留通过检查的 angle target，剔除失败的 angle target。

如果没有角度维数据，情况 3 仍然可以在“稳定复合等效”的前提下使用；只有它不能稳定等效时，才只能识别和剔除。

## Ma 等人的转换因子方法

Ma 系列论文中确实使用加速度来标定雷达 LOS 方向转换关系，但更精确地说不是直接拟合 AoA，而是拟合 **direction conversion factor / LOS conversion factor**。

雷达 LOS 位移：

$$
d_r(k)=\frac{\lambda}{4\pi}
\operatorname{unwrap}\left(\Delta\phi(k)\right)
$$

加速度双积分并带通后的参考位移：

$$
q_a(k)
$$

Ma 的 baseline 方法：

$$
q_{r,\beta}(k)=\beta d_r(k)
$$

计算：

$$
E(\beta)=
\sqrt{
\frac{1}{N}
\sum_k
\left[
\beta d_r(k)-q_a(k)
\right]^2
}
$$

选择：

$$
\hat{\beta}=
\arg\min_{\beta}E(\beta)
$$

也可用普通最小二乘闭式：

$$
\hat{\beta}
=
\frac{\sum_k d_r(k)q_a(k)}
     {\sum_k d_r^2(k)}
$$

如果按倒挂投影系数估计：

$$
\hat{\eta}
=
-\frac{\sum_k q_a(k)d_r(k)}
       {\sum_k q_a^2(k)}
$$

如果：

$$
\eta=\cos\alpha
$$

则：

$$
\alpha\approx \arccos(\eta)
$$

或者若：

$$
\beta\approx \frac{1}{|\eta|}
$$

则：

$$
\alpha\approx \arccos\left(\frac{1}{\beta}\right)
$$

注意：这个角度是等效 LOS 投影角，不是雷达阵列直接估计的 AoA。

## 转换因子估计的候选方法

本节是方法演进记录与对照方法池，不等同于当前主方法。尤其是任何利用 Kalman posterior 或 LoS corrected phase 在线更新 $\beta_i$ 的做法均已弃用。

普通最小二乘可能不够稳健，原因包括：

- 加速度双积分有低频漂移；
- 雷达相位可能解缠错误；
- rangeBin 内可能多散射混叠；
- 车辆/行人会造成短时异常；
- 雷达和加速度可能存在微小时延；
- 普通 LS 默认自变量无误差，但雷达和加速度两侧都有噪声。

候选方法池：

1. **Ma 式 RMSE 遍历法**
   - baseline；
   - 简单可复现；
   - 对异常点敏感。

2. **普通 LS 闭式估计**
   - 计算方便；
   - 可作为 baseline；
   - 可能被异常点和双侧噪声带偏。

3. **频域幅值比**

若主频 $f_0$ 明显：

$$
A(f)=-(2\pi f)^2Q(f)
$$

若：

$$
Q(f)=\beta D_r(f)
$$

则：

$$
\hat{\beta}
\approx
\frac{|A(f_0)|}
     {(2\pi f_0)^2|D_r(f_0)|}
$$

优点是不需要完整双积分，低频漂移影响小。

4. **相干加权频域拟合**

令：

$$
X(f)=-(2\pi f)^2D_r(f)
$$

拟合：

$$
A(f)\approx \beta X(f)
$$

可用 coherence 作为权重：

$$
\hat{\beta}
=
\frac{
\sum_{f\in\Omega} w(f)\operatorname{Re}\{X^*(f)A(f)\}
}{
\sum_{f\in\Omega} w(f)|X(f)|^2
}
$$

适合判断 radar phase 与 acceleration 是否来自同一个结构运动。

5. **鲁棒回归**

$$
\hat{\beta}
=
\arg\min_\beta
\sum_k
\rho\left(\beta d_r(k)-q_a(k)\right)
$$

可用 Huber、Tukey 或 RANSAC，适合抵抗短时遮挡和相位异常。

6. **总最小二乘 / Deming 回归**
   - 同时考虑雷达和加速度两侧噪声；
   - 比普通 LS 更符合双传感器拟合。

7. **几何/AoA 先验再微调**

若雷达 AoA 或 range-angle 元数据可用：

$$
\eta_0=\mathbf{n}^\mathrm{T}\mathbf{e}
$$

$$
\beta_0\approx \frac{1}{|\eta_0|}
$$

再在附近小范围搜索或拟合。

当前主方法只采用如下决策链：AoA 逐目标初值 $\rightarrow$ 公共角偏差仅作诊断/消融 + 原始多 target phase 的双折 rank-1 逐目标相对投影 $\rightarrow$ native-timestamp ADXL 动力学相干/绝对候选/公共时延与不重叠 holdout $\rightarrow$ 按标定来源预选相对或绝对模式 $\rightarrow$ 全局失败整组回退、逐目标失败只回退对应 AoA $\rightarrow$ 冻结 $\beta_i$ $\rightarrow$ 从第 0 帧运行完整 Kalman。上述候选方法可作为 baseline 或预校准内部的比较对象，但不得把 Kalman 输出回接为 beta 标定依据。

## IWR1843 硬件约束

当前雷达为 **TI IWR1843**：

- 76-81 GHz FMCW mmWave radar；
- 3TX / 4RX MIMO；
- 虚拟阵列规模有限；
- 适合常规 Range FFT + Angle FFT / DBF；
- Capon/MVDR 可作为较现实的增强候选；
- MUSIC/ESPRIT/稀疏重构/SBL/atomic norm 等可调研，但不能默认适合低通道数、复杂桥下多径和实时相位跟踪；
- 目标不是单帧角度估计精度最大化，而是得到稳定的 range-angle 复数 slow-time 序列，用于相位跟踪、IQ 圆弧判断和转换因子估计。

## 实机采集拓扑（后续对话必须保持）

项目只采用下面这一套采集方案：**Raspberry Pi 4 是唯一采集主机和统一时间戳来源，电脑只负责通过 Wi-Fi/SSH 控制，以及采集结束后的数据下载和离线分析。**

```text
电脑 ──Wi-Fi / SSH──→ Raspberry Pi 4
                         ├──SPI + DRDY──→ ADXL355
                         ├──USB─────────→ IWR1843BOOST
                         ├──GPIO18──────→ IWR1843BOOST SYNC_IN（硬件触发模式）
                         └──Ethernet────→ DCA1000EVM

IWR1843BOOST ←──60-pin HD / LVDS──→ DCA1000EVM
```

- ADXL355 的 SPI 和 DRDY 均接 Pi 4。
- IWR1843BOOST 的 USB 接 Pi 4，用于配置和控制雷达。
- DCA1000EVM 的网线直连 Pi 4 的有线网口，用于控制和接收 UDP 原始 ADC 数据。
- IWR1843BOOST 与 DCA1000EVM 通过 60-pin HD 接口传输 LVDS 数据。
- 电脑不直接连接传感器、不运行实机抓包、不参与采集时序；SSH 只负责控制，命令到达时间不是同步时间戳。
- 后续实现、文档和实验设计必须保持 Pi 4 单机采集，不得让电脑参与采集或传感器计时。

同步采集软件现已落在 `capture_program/`：C 原生 ADXL355 采集器使用 spidev + libgpiod DRDY，C 帧触发器产生有限 GPIO18 脉冲并可由 GPIO24 回环记录内核边沿，`SynchronizedRadarAdxl` 统一协调雷达/DCA 与 ADXL 生命周期。软件时间戳模式输出 `sensorStart` bracket + 标称周期估计；硬件模式输出每帧触发参考；两者均写 `sync/radar_frame_monotonic_ns.npy` 和 `timeline.json`，且不把 PCAP 接收时间或 GPIO 边沿冒充雷达 ADC 采样时刻。当前只完成无硬件聚焦测试，`hardware_validated` 必须保持 `false`，直到真实 Pi 上的 SPI、1 kHz DRDY 积压、DCA 丢包、J6-9 `SYNC_IN`、触发波形、帧对应、时延和漂移全部实测通过。

## 当前需要继续讨论的问题

当前论文方法论框架已经基本闭环。下一步应围绕“如何写成论文方法章节”和“如何设计实验验证”继续推进，不得重新采用已弃用的 Kalman posterior / LoS corrected phase 在线反哺 beta 方案。重点包括：

1. 将整体方法整理成 Method 章节结构：系统模型、target 提取、AoA 初值、原始多 target phase 公共角偏差候选、native-timestamp ADXL 独立时域校准、不重叠 holdout、精确 AoA 回退、冻结 beta、从第 0 帧完整 Kalman、多 target 观测构造、固定 $Q$ 与自适应 $R$。
2. 明确第一版算法的可复现实验参数：公共角偏差搜索范围、ADXL 原生时间戳与公共时延范围、校准/holdout 划分、关键门控、滑动窗口长度、角度合并阈值、结构频带阈值、$Q$ 的遍历范围、$R$ 的上下界和遗忘因子。
3. 设计 ablation study：单 target vs 多 target；原始 AoA 精确回退 vs 仅公共角偏差候选 vs 通过 ADXL holdout 的冻结 beta；固定 $R$ vs 自适应 $R$；是否使用 Doppler/chirp 间相位变化率作为辅助先验。
4. 设计独立校准有效性验证：记录接受/拒绝原因、拟合段与 holdout 残差改善、跨折 beta/时延一致性、全局失败时的整组 AoA 回退与逐目标失败时的单目标 AoA 回退、完整 Kalman 期间 beta history 恒定、$\phi_{i,k}^{\mathrm{LOS,corr}}$ 的分支选择错误率和多 target innovation 一致性。车辆事件等短时非平稳激励不能单独证明转换系数校准到真值。
5. 继续保留 Ma 等人方法作为 baseline：Ma 式单 target LoS phase Kalman + 离线转换因子；本文作为结构主相位多 target Kalman + AoA 初始化 + 独立原始数据预校准/holdout + 精确回退 + 冻结 beta。

请在新对话中以本文件和 `thesis_idea_overview.md` 的上述转换系数口径为准。其他源文档里尚未同步的在线 beta 叙述一律视为已弃用历史方案，除非发现明确数学错误，不得将其恢复为当前方法。
