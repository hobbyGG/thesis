# 创新点一：距离—角度参考目标构造

## 问题

倒挂式雷达的环境散射体提供结构运动参考。同一个 range-bin 内若混有多个角度散射体，直接对整个 range-bin 求复数相位会产生混合相位，转换因子也失去明确几何意义。因此，后端观测单元应是距离—角度目标。

## 当前代码链

`algorithm/selection.py` 对整段 range-angle 幅值取中位数，检测二维局部峰，再合并距离接近且角度接近的峰，按动态范围保留候选。`algorithm/frontend.py` 从候选提取每个目标的 slow-time IQ、wrapped phase、角度和 `beta`。

```text
ADC cube
→ range-angle cube
→ record median magnitude
→ 2D peaks
→ close-peak merge
→ candidate range/angle bins
→ target slow-time IQ
```

目标候选不使用 truth。当前场景保留 5 个有效参考目标，逐帧只通过 `available_mask` 表示该目标是否可用。

## 研究贡献

本文把 range-angle target 作为结构主相位融合的基本观测通道：同距离近角散射体合并为等效目标，同距离远角散射体保持独立，从而避免单一 range-bin 混合相位直接进入 Kalman。

## 边界

当前实现是记录级候选构造，不是动态新增、删除和重关联的在线 tracker。目标集合确定后，某帧没有有效目标时算法只做状态预测；实时重关联属于后续工作。
