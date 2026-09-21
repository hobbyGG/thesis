# 主要研究思路

## 研究问题

桥梁结构位移变化会同时反映在毫米波雷达的传播相位和 MEMS 加速度计的动力学响应中。雷达相位灵敏但存在 (2\pi) 缠绕、目标角度投影和瞬时噪声问题；加速度能约束结构运动趋势，却需要两次积分并容易漂移。本文把两者放到同一个结构主相位状态空间中估计位移。

## 数据组织

研究代码分成三个边界：

1. `capture_program/` 负责真实 IWR1843/DCA1000 与 ADXL355 采集，并导出统一 `capture_root`。
2. `measured_bridge_simulation/` 读取实测 TDMS 激光位移，生成雷达 ADC/IQ、ADXL355 和同步时间轴，也导出同一 `capture_root`。
3. `algorithm/` 只读取 `capture_root`，不生成场景、不读取真值参与估计、不控制硬件。

共同输入格式是：

```text
radar/algorithm_input/adc_cube.npy
adxl355/algorithm_input/acceleration_mps2.npy
adxl355/algorithm_input/estimated_sample_monotonic_ns.npy
sync/radar_frame_monotonic_ns.npy
```

半实测包额外保存 `truth/`，仅用于评价。

## 算法主链

```text
ADC cube
→ Range FFT
→ Angle DBF / range-angle map
→ 整段记录级峰值检测与近邻峰合并
→ 局部 MUSIC/ML 连续 AoA
→ slow-time IQ 与 wrapped LoS phase
→ beta_i = 1 / |cos(theta_i)|，整段冻结
→ ADXL 原生时间轴区间预积分
→ 加速度预测结构主相位
→ 多目标 Kalman 更新
→ 后验残差更新测量噪声 R_i
→ 结构位移 q_hat
```

### 1. 距离—角度观测

对每帧 ADC cube 做距离 FFT，在虚拟阵元方向做角度 DBF，得到 (Z_k(r,\theta))。整段记录的中位数幅值图用于检测候选距离和角度。候选只来自 ADC，不使用目标真值。

### 2. 连续 AoA 与等效转换因子

角度 FFT 只提供粗候选。对每个候选距离的阵元快拍做局部 MUSIC/ML 精修，得到连续角度 (hat\theta_i)。倒挂雷达的结构位移与视线位移关系写为：

\[
\beta_i = \frac{1}{|\cos\hat\theta_i|},\qquad
\Theta_k = \frac{4\pi}{\lambda}q_k .
\]

本研究把 (\beta_i) 在整段记录内冻结，避免把结构运动误当成角度或比例因子变化。

### 3. 异步加速度约束

雷达帧与 ADXL355 样本保留各自的单调时钟。对每个雷达区间 ([t_k,t_{k+1}]) 计算：

\[
\Delta v_k=\int_{t_k}^{t_{k+1}}a(t)dt,\qquad
\Delta q_k=\int_{t_k}^{t_{k+1}}(t_{k+1}-t)a(t)dt.
\]

这样加速度只作为状态预测输入，不先重采样成伪配对序列。

### 4. 结构主相位 Kalman

状态为：

\[
\mathbf{x}_k=[\Theta_k,\dot\Theta_k]^T .
\]

常加速度预测使用 (Delta q_k,Delta v_k)。对第 (i) 个目标，预测的视线相位为：

\[
\phi_{i,k}^{pred}=\Theta_k/\beta_i+b_i .
\]

用最近的 (2\pi) 分支校正观测 wrapped phase，再转换回结构主相位：

\[
z_{i,k}=\beta_i(\phi_{i,k}^{corr}-b_i),
\quad H_i=[1,0].
\]

所有当前可用目标共同更新同一个结构状态。每个目标的测量噪声 (R_i) 根据后验残差递推，低质量目标的权重会自动下降。

## 实验设计

当前实验只保留实测桥梁位移驱动的半实测场景：激光通道提供真实结构运动波形，雷达和 ADXL 观测按固定硬件参数合成，然后经过与实测采集相同的输入目录进入算法。实验重点是验证：

- 实测运动输入能否通过统一采集包进入算法；
- Range-Angle 与连续 AoA 是否能给出稳定的 (\beta_i)；
- 异步 ADXL 预测和多目标相位融合是否能恢复结构位移；
- 输出结果是否可直接对照激光位移真值。

## 论文贡献口径

论文只保留三点：

1. **记录级多目标参考构造**：从距离—角度图提取多个参考目标，并结合有效性保留稳定目标集合。
2. **连续 AoA 驱动的固定转换因子**：用局部 MUSIC/ML 替代角度 FFT 离散格点，得到连续角度和冻结几何 (\beta_i)。
3. **异步加速度辅助的多目标结构主相位 Kalman**：原生时间轴预积分提供预测，多目标观测共同更新主相位，并用后验残差调整 (R_i)。

Ma、旧多场景、online beta、自适应 beta 和扩展 baseline 不属于当前论文主链。
