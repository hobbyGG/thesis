# Mehrmaid 公式流程图测试

> 说明：该文件仅用于测试 Obsidian Mehrmaid 插件的公式渲染能力，不是当前正式方法文档。当前正式流程图以 [overall_processing_architecture.md](/Users/umep/thesis/idea/overall_processing_architecture.md) 为准。

这个文件用于测试 Obsidian 的 Mehrmaid 插件是否能在流程图节点中正常渲染公式。注意代码块语言是 `mehrmaid`，不是 `mermaid`。

## 1. 最小公式测试

```mehrmaid
flowchart LR
    A("普通 Mermaid 文本<br/>$x_{k-1}$")
    B("上标与下标<br/>$\mathbf{x}_{k}^{-}$")
    C("校正相位<br/>$z_{i,k}^{\mathrm{corr}}$")
    D("观测行<br/>$\mathbf{h}_{i,k}=[1/\hat{\beta}_{i,k},0]$")

    A --> B --> C --> D
```

## 2. Kalman 后半段公式版

```mehrmaid
flowchart TD
    ACC("同步加速度<br/>$a_{k-1}$")
    XPREV("上一时刻后验状态<br/>$\mathbf{x}_{k-1},\ \mathbf{P}_{k-1}$")
    INIT("AoA 冷启动<br/>$\hat{\beta}_{i,0},\ b_i,\ r_{i,0}$")

    PRED("系统模型预测<br/>$\mathbf{x}_{k}^{-}=\mathbf{A}\mathbf{x}_{k-1}+\mathbf{B}\frac{4\pi}{\lambda}a_{k-1}$<br/>$\mathbf{P}_{k}^{-}=\mathbf{A}\mathbf{P}_{k-1}\mathbf{A}^{T}+\mathbf{Q}$")

    T1("Target 1<br/>$\psi_{1,k},\ \hat{\beta}_{1,k},\ b_1$")
    T2("Target 2<br/>$\psi_{2,k},\ \hat{\beta}_{2,k},\ b_2$")
    Tm("Target m<br/>$\psi_{m,k},\ \hat{\beta}_{m,k},\ b_m$")

    U1("Target 1 预测辅助相位校正<br/>$\hat{\phi}_{1,k}^{-}=\mathbf{h}_{1,k}\mathbf{x}_{k}^{-}+b_1$<br/>$z_{1,k}^{\mathrm{corr}}=\psi_{1,k}+2\pi\operatorname{round}((\hat{\phi}_{1,k}^{-}-\psi_{1,k})/2\pi)$")
    U2("Target 2 预测辅助相位校正<br/>$\hat{\phi}_{2,k}^{-}=\mathbf{h}_{2,k}\mathbf{x}_{k}^{-}+b_2$<br/>$z_{2,k}^{\mathrm{corr}}=\psi_{2,k}+2\pi\operatorname{round}((\hat{\phi}_{2,k}^{-}-\psi_{2,k})/2\pi)$")
    Um("Target m 预测辅助相位校正<br/>$\hat{\phi}_{m,k}^{-}=\mathbf{h}_{m,k}\mathbf{x}_{k}^{-}+b_m$<br/>$z_{m,k}^{\mathrm{corr}}=\psi_{m,k}+2\pi\operatorname{round}((\hat{\phi}_{m,k}^{-}-\psi_{m,k})/2\pi)$")

    OBS("多目标观测模型<br/>$\mathbf{z}_{k}^{\mathrm{corr}}=\mathbf{H}_{k}\mathbf{x}_{k}+\mathbf{b}_{k}+\mathbf{v}_{k}$<br/>$\mathbf{h}_{i,k}=[1/\hat{\beta}_{i,k},0]$")

    KF("Kalman 更新<br/>$\mathbf{x}_{k}=\mathbf{x}_{k}^{-}+\mathbf{K}_{k}(\mathbf{z}_{k}^{\mathrm{corr}}-\mathbf{H}_{k}\mathbf{x}_{k}^{-}-\mathbf{b}_{k})$")

    XEST("结构主相位后验估计<br/>$\hat{\Theta}_{k},\ \dot{\hat{\Theta}}_{k}$")
    DISP("结构振动方向位移<br/>$\hat{q}_{k}=\frac{\lambda}{4\pi}\hat{\Theta}_{k}$")

    BETA("转换系数短窗口自举<br/>$\hat{\kappa}_{i}=\frac{\sum \hat{\Theta}_{k}(z_{i,k}^{\mathrm{corr}}-b_i)}{\sum \hat{\Theta}_{k}^{2}}$<br/>$\hat{\beta}_{i}=1/\hat{\kappa}_{i}$")

    RADAPT("target-wise adaptive $R$<br/>$s_{i,k}=z_{i,k}^{\mathrm{corr}}-(\mathbf{h}_{i,k}\mathbf{x}_{k}+b_i)$<br/>$r_{i,k+1}=\operatorname{clip}(\alpha r_{i,k}+(1-\alpha)\tilde r_{i,k})$")

    ACC --> PRED
    XPREV --> PRED
    INIT --> PRED

    PRED --> U1
    PRED --> U2
    PRED --> Um

    T1 --> U1
    T2 --> U2
    Tm --> Um

    U1 -- "$\mathbf{h}_{1,k},\ z_{1,k}^{\mathrm{corr}}$" --> OBS
    U2 -- "$\mathbf{h}_{2,k},\ z_{2,k}^{\mathrm{corr}}$" --> OBS
    Um -- "$\mathbf{h}_{m,k},\ z_{m,k}^{\mathrm{corr}}$" --> OBS

    OBS --> KF --> XEST --> DISP

    U1 -- "$z_{1,k}^{\mathrm{corr}}$" --> BETA
    U2 -- "$z_{2,k}^{\mathrm{corr}}$" --> BETA
    Um -- "$z_{m,k}^{\mathrm{corr}}$" --> BETA
    XEST -- "$\hat{\Theta}_{k}$" --> BETA
    BETA -- "$\hat{\beta}_{i,k+1}$" --> OBS
    BETA --> U1
    BETA --> U2
    BETA --> Um

    KF --> RADAPT
    RADAPT -- "$r_{i,k+1}$" --> OBS
    XEST -- "next $k$" --> XPREV
```

## 3. 如果第 2 张太挤

如果上面的公式都能正常渲染，但节点太宽，可以采用这一版：节点里只放短公式，长公式放图下。

```mehrmaid
flowchart TD
    PRED("系统模型预测<br/>$\mathbf{x}_{k}^{-},\mathbf{P}_{k}^{-}$")
    U1("Target 1 解缠<br/>$z_{1,k}^{\mathrm{corr}}$")
    U2("Target 2 解缠<br/>$z_{2,k}^{\mathrm{corr}}$")
    Um("Target m 解缠<br/>$z_{m,k}^{\mathrm{corr}}$")
    OBS("多目标观测模型<br/>$\mathbf{z}_{k}^{\mathrm{corr}},\mathbf{H}_{k},\mathbf{R}_{k}$")
    KF("Kalman 更新<br/>$\hat{\Theta}_{k},\dot{\hat{\Theta}}_{k}$")
    BETA("转换系数自举<br/>$\hat{\beta}_{i,k+1}$")
    RADAPT("自适应测量噪声<br/>$r_{i,k+1}$")

    PRED --> U1
    PRED --> U2
    PRED --> Um
    U1 -- "$\mathbf{h}_{1,k}$" --> OBS
    U2 -- "$\mathbf{h}_{2,k}$" --> OBS
    Um -- "$\mathbf{h}_{m,k}$" --> OBS
    OBS --> KF
    U1 --> BETA
    U2 --> BETA
    Um --> BETA
    KF --> BETA
    BETA --> OBS
    KF --> RADAPT --> OBS
    KF --> PRED
```
