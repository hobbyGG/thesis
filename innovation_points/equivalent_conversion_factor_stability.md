# 创新点二：直接 AoA 与固定几何转换系数

> **实现口径：** 当前主方法不估计一个随时间变化的 beta，也不在 Kalman 前执行 rank-1/ADXL 独立 beta 预校准。当前流程是局部 MUSIC/ML AoA → 几何 beta → 全程冻结。旧预校准器只作为 legacy/ablation 保留。

## 1. 为什么需要目标级转换系数

倒挂式雷达中，第 $i$ 个环境目标对应一个 LoS 方向。若结构沿主方向位移 $q_k$，则目标相位可写成

$$
\Theta_k=\frac{4\pi}{\lambda}q_k,
\qquad
\phi_{i,k}^{\mathrm{LOS}}=\frac{\Theta_k}{\beta_i}+b_i.
$$

如果同一 range-bin 内混有不同角度的散射体，直接对 range-bin 总相位使用一个 beta 会得到随幅值和相对相位变化的混合等效量。因此，beta 的基本对象应是经过距离—角度拆分的 target，而不是整个 range-bin。

## 2. 当前 AoA 流程

当前捕获入口强制使用 `local_music_ml`：

1. Range FFT 和 Angle FFT/DBF 给出粗距离—角度候选。
2. 粗角度只定义局部搜索区间。
3. 对同一 range-bin 的多阵元复快拍构造协方差矩阵。
4. 在局部空间频率区间内用 MUSIC 噪声子空间谱取得连续初值。
5. 用联合变量投影最小二乘优化复数阵列残差，得到连续 AoA。
6. 用最终固定导向矩阵重建全时段 slow-time IQ。

代码入口：[`algorithm/angle_estimation.py:15`](/Users/umep/thesis/algorithm/angle_estimation.py:15)，算法入口：[`algorithm/run.py`](/Users/umep/thesis/algorithm/run.py)。

## 3. 从 AoA 到 beta

当前 Phase 1 一维方位、倒挂安装约定下，代码使用：

$$
p_i=|\cos\theta_i|,
\qquad
\hat\beta_i=\frac{1}{\max(p_i,\epsilon_p)}.
$$

对应实现是 `angle_deg_to_measured_beta`。该公式不是任意三维安装姿态下的通用标定公式；真实系统还需要确认：

- 结构主振动方向与雷达坐标轴的关系；
- Angle 轴是方位角还是其他角度定义；
- 安装朝向和符号约定；
- IWR1843 虚拟阵元坐标和通道幅相误差。

因此，当前研究中的“固定 beta”首先表示一个可复现的几何模型输入。它的实机绝对精度需要独立角度/姿态/位移标定。

## 4. beta 冻结是当前主线的不变量

`fixed_geometry_beta_structural_kalman` 中：

```text
beta_source = frontend_direct_aoa
beta_update_enabled = False
beta_hat(k) = beta_hat(0)
```

Kalman posterior、corrected phase、加速度参考和 $R$ 更新都不能返回去改写 beta。这样做的目的不是声称几何 beta 永远准确，而是把几何误差与动态滤波误差分开，避免同一状态估计结果循环证明自身的 beta。

## 5. 目标级等效性

同一 range-bin 内角度很近、阵列无法稳定区分的散射体可以作为一个等效 target；角度明显分离的散射体应拆成不同 target。等效 target 的 beta 是该观测通道在当前阵列和波束形成定义下的有效几何尺度，不能无条件解释为某一个物理点目标的精确几何系数。

这也是本点与目标构造创新的连接：目标定义越接近单一空间方向，

$$
y_{i,k}=\hat\beta_i
\left(\phi_{i,k}^{\mathrm{LOS,corr}}-b_i\right)
$$

越有可能成为公共结构主相位 $\Theta_k$ 的稳定观测。

## 6. 不应宣称的内容

以下方案存在代码实现或历史实验，但不属于当前 Direct-AoA 主线：

- 原始多 target phase 的 rank-1 相对投影 beta 校准；
- native-timestamp ADXL 绝对尺度、公共时延和双折 holdout beta 接受/回退；
- Kalman posterior 或 LoS corrected phase 在线 beta bootstrap；
- 用 beta 方差作为 Direct-AoA 默认 $R$ 的额外不确定度项。

这些内容可在方法演变或消融章节说明，但不能与当前 `frontend_direct_aoa` beta 来源混写。

## 7. 本点的准确贡献表述

本文不是提出新的转换系数估计理论，而是将直接连续 AoA、目标级复数 IQ 重建和冻结几何投影接入倒挂式多目标结构位移链路：角度估计负责空间方向，几何映射负责统一相位尺度，结构主相位 Kalman 负责动态预测与多目标融合。该分工使 AoA 误差、几何标定误差和相位滤波误差能够分别诊断。

AoA 精修带来的位移差异需要谨慎解释。当前 `local_music` 与 `local_music_ml` 对比的后端 $Q$ 也会分别按整段 innovation energy 选择，因此位移 RMSE 差不能完全归因于 ML/NLS 精修，除非固定后端参数进行额外对照。
