# 新对话接续 Prompt：倒挂式毫米波雷达论文思路

下面内容用于在新对话框中接续当前论文讨论。请新对话中的 agent 先完整阅读本文件，再根据需要阅读相关草稿文件。

## 可直接复制到新对话框的 Prompt

你是我的论文协作助手，工作目录是 `/Users/umep/thesis`。请用中文和我讨论，公式必须使用 Obsidian 支持的 `$...$` 和 `$$...$$`，不要使用 math fenced code block。

我正在写一篇关于**倒挂式毫米波雷达结构位移监测**的论文。雷达安装在桥梁/结构测点上，随结构一起运动，向下或斜向观测周围静止参考物。当前实验雷达是 **TI IWR1843**，属于 76-81 GHz FMCW mmWave radar，3TX/4RX MIMO，虚拟阵列规模有限。后续 AoA / range-angle 方法必须考虑 IWR1843 的实际能力，不能推荐需要大规模阵列、大量 snapshots 或复杂离线优化的方法作为主方案。

请优先阅读以下文件：

1. `/Users/umep/thesis/thesis_idea_overview.md`
   - 这是当前论文整体思路说明，已经同步到最新版闭环方案。
   - 包含数学模型、关键结论、Ma 等人的转换因子方法、AoA 冷启动与转换系数自举、IWR1843 硬件约束。
2. `/Users/umep/thesis/idea/overall_processing_architecture.md`
   - 这是当前最重要的整体架构文档。
   - 包含最新版完整数据流、两个 Mehrmaid 流程图、target 提取、AoA 冷启动、预测辅助相位校正、转换系数自举、固定 $Q$ 与自适应 $R$ 的接口关系。
3. `/Users/umep/thesis/innovation_points/multi_target_phase_kalman_fusion.md`
   - 这是结构主相位多 target Kalman 融合创新点的正式说明。
   - 包含与 Ma 等人框架的区别：状态变量由单 target LoS 相位改为结构主相位，转换系数由离线标定改为 AoA 冷启动与在线自举，多个 target 共同构造观测模型。
4. `/Users/umep/thesis/draft_inverted_radar_theory_model.md`
   - 这是更完整的倒挂式毫米波雷达理论章节草稿。
   - 包含 mmVib 相位模型、倒挂几何模型、FMCW 回波模型、IQ 模型、多 target、角度门控等内容。
5. `/Users/umep/thesis/ref_papers/00_primary_references/README.md`
   - 这是主参考文献说明。
   - 重点文献包括 mmVib 论文和 Ma/Zhanxiong 系列雷达 + 加速度/应变/相位解缠论文。

当前讨论的核心不是重新发明毫米波雷达测距理论，而是：

> 基于 mmVib 的相位测量理论，建立倒挂式毫米波雷达的结构位移估计框架：前端从 range-angle map 中在线筛选多个可用静止参考 target；后端参考 Ma 等人的 acceleration-aided Kalman filtering 思想，但将状态变量从单 target LoS 相位改为结构振动方向主相位，并用 AoA 冷启动、预测辅助相位校正和短窗口最小二乘自举打通转换系数与相位连续性的循环依赖。

## 当前最新版方法闭环

### 0.1 前端 target selection 不依赖相位解缠

ADC 数据经过 Range FFT 和 Angle FFT / DBF 得到复数 range-angle map。二维峰值检测得到 $M$ 个候选 target；同一 rangeBin 内 AoA 差异小于 $15^\circ$ 的 target 可视为等效 target；随后通过滑动窗口稳定性和结构频带一致性筛选，输出 $m$ 个可用 target，$m\le M$。

该阶段只输出 wrapped phase：

$$
\psi_{i,k}=\angle z_i(k),
\qquad
\psi_{i,k}\in(-\pi,\pi],
$$

不做最终意义上的相位解缠，也不预先估计精确转换系数。

### 0.2 AoA 冷启动用于打破转换系数与相位校正死锁

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

AoA 初值不是最终精确转换系数，只用于启动 Kalman 闭环。冷启动阶段结构近似静止，用于估计相位偏置 $b_i$，并初始化较大的 target-wise 测量噪声 $r_{i,0}$。

### 0.3 Kalman 状态是结构主相位，不是 Ma 的单 target LoS 相位

状态变量定义为：

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

### 0.4 预测辅助相位校正同时服务观测更新和转换系数自举

雷达 phase wrapping 发生在 LoS 相位空间，因此分支选择时需要先把结构主相位预测投影回 LoS：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\hat{\beta}_{i,k}^{-}}+b_i.
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

同一个 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 同时进入两条路径：

1. 乘以 $\beta_i$ 构造结构方向主相位观测：

$$
y_{i,k}
=
\hat{\beta}_{i,k}^{-}
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

2. 作为转换系数短窗口最小二乘自举的 LoS 侧数据。不能把同一 target 参与生成的后验结构相位直接作为该 target 的 $\beta_i$ 收敛证据；为避免自反馈，$\beta_i$ 的在线更新应使用第 $i$ 个 target 的 LoS corrected phase 与不含 target $i$ 的结构方向参考状态进行最小二乘拟合，并用加速度参考或可靠几何 target 做尺度锚定。令 $x_\tau=\phi_{i,\tau}^{\mathrm{LOS,corr}}-b_i$，$y_\tau=\Theta_{\tau}^{\mathrm{ref},-i}$，中心化后：

$$
\hat{\beta}_{i,k+1}
=
\frac{
\sum_{\tau\in\mathcal{W}_{\beta}}
x_{\tau,c}y_{\tau,c}
}{
\sum_{\tau\in\mathcal{W}_{\beta}}
x_{\tau,c}^{2}
}.
$$

因此，本文不是先独立完成一段完整相位解缠再标定 $\beta$，而是在 Kalman 闭环内生成局部 LoS corrected phase，并让该校正相位支撑结构方向观测更新；转换系数更新必须另接不含当前 target 的结构方向参考状态。当前代码与正文统一采用结构方向观测模型 $H_i=[1,0]$。

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

这样在冷启动和初始微振阶段，若某些 target 或转换系数尚未稳定，其测量噪声会保持较大，滤波器更依赖加速度预测；只有在 target-wise beta error、last-window median error 和更新 gate 共同支持时，才能说短窗口自举使 $\hat{\beta}_{i,k}$ 进入可信范围，随后 $R$ 才应回落并恢复多 target 观测权重。

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

## IWR1843 硬件约束

当前雷达为 **TI IWR1843**：

- 76-81 GHz FMCW mmWave radar；
- 3TX / 4RX MIMO；
- 虚拟阵列规模有限；
- 适合常规 Range FFT + Angle FFT / DBF；
- Capon/MVDR 可作为较现实的增强候选；
- MUSIC/ESPRIT/稀疏重构/SBL/atomic norm 等可调研，但不能默认适合低通道数、复杂桥下多径和实时相位跟踪；
- 目标不是单帧角度估计精度最大化，而是得到稳定的 range-angle 复数 slow-time 序列，用于相位跟踪、IQ 圆弧判断和转换因子估计。

## 当前需要继续讨论的问题

当前论文方法论框架已经基本闭环。下一步应围绕“如何写成论文方法章节”和“如何设计实验验证”继续推进，而不是重新回到旧的离线转换因子路线。重点包括：

1. 将整体方法整理成 Method 章节结构：系统模型、target 提取、多 target 观测构造、AoA 冷启动、预测辅助相位校正、转换系数自举、固定 $Q$ 与自适应 $R$。
2. 明确第一版算法的可复现实验参数：滑动窗口长度、角度合并阈值、结构频带阈值、$Q$ 的遍历范围、$R$ 的上下界和遗忘因子。
3. 设计 ablation study：单 target vs 多 target；无 AoA 冷启动 vs AoA 冷启动；固定转换系数 vs 在线自举；固定 $R$ vs 自适应 $R$；是否使用 Doppler/chirp 间相位变化率作为辅助先验。
4. 设计闭环有效性验证：初始微振阶段 target-wise beta error、last-window median error、更新 gate、$R_i$ 的自动回落、$\phi_{i,k}^{\mathrm{LOS,corr}}$ 的分支选择错误率、多 target innovation 一致性。车辆事件等短时非平稳激励只能说明 AoA 初值误差对位移估计影响被降低，不能证明所有 target-wise beta 均收敛到真值。
5. 继续保留 Ma 等人方法作为 baseline：Ma 式单 target LoS phase Kalman + 离线转换因子；本文作为结构主相位多 target Kalman + AoA 冷启动 + 在线转换系数自举。

请在新对话中不要重新推翻上述共识，除非发现明确数学错误。优先在这些共识上继续推进方法章节写作、公式统一和实验方案设计。
