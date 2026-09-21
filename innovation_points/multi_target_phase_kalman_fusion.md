# 创新点三：异步加速度辅助的多目标结构主相位 Kalman

## 核心问题

雷达相位对位移敏感，却存在 wrapped phase 和 LoS 投影；加速度能提供运动预测，却不能直接通过双积分得到稳定位移。多个环境目标又对应不同 LoS 方向。本文把各目标观测统一到结构主相位状态后进行联合滤波。

## 状态和观测

状态为：

$$
\mathbf{x}_k=[\Theta_k,\dot\Theta_k]^T,
\qquad \Theta_k=4\pi q_k/\lambda .
$$

第 (i) 个目标的冻结几何因子为 (eta_i)，目标偏置为 (b_i)：

$$
\phi_{i,k}^{LOS}=\Theta_k/\beta_i+b_i.
$$

算法用预测结构相位选择 wrapped phase 的最近 (2\pi) 分支，再得到：

$$
z_{i,k}=\beta_i(\phi_{i,k}^{corr}-b_i),
\quad H_i=[1,0].
$$

所有当前可用目标共同更新同一个结构状态，而不是先分别估计位移再做结果平均。

## 异步加速度预测

雷达帧和 ADXL355 样本保留各自的 native `CLOCK_MONOTONIC` 时间轴。`algorithm/acceleration.py` 对每个雷达区间计算：

$$
\Delta v_k=\int_{t_k}^{t_{k+1}}a(t)dt,
\qquad
\Delta q_k=\int_{t_k}^{t_{k+1}}(t_{k+1}-t)a(t)dt .
$$

Kalman 预测直接使用 (Delta v_k,Delta q_k)，不把两个传感器强行配成同一采样率的伪样本。

## 当前代码入口

- `algorithm/io.py:build_algorithm_inputs`：读取结构轴并构造预积分；
- `algorithm/kalman.py:run_fixed_beta_kalman`：固定 beta、多目标更新、后验残差 (R_i)；
- `algorithm/run.py`：写 `npz` 结果和 JSON 摘要。

## 准确的创新表述

本文的增量是：针对倒挂式自然参考场景，把不同角度目标的 LoS wrapped phase 通过冻结几何因子统一到结构主相位坐标，并将 native-rate 加速度区间预积分接入共享结构状态的 Kalman 预测。它不宣称首次提出 Kalman 解缠、加速度融合或多目标滤波。
