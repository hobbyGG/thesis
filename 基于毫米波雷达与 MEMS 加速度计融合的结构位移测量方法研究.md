
## 1. 研究背景与问题提出

### 1.1 研究意义

桥梁和土木结构的位移响应能够直接反映结构在车辆荷载、风荷载、温度效应或局部损伤影响下的整体变形状态，是结构健康监测中的关键物理量。相较于加速度，位移对低频和准静态响应更敏感，也更接近挠度、线形和服役性能评价指标；相较于应变，单点位移更容易服务于跨中挠度、振型变化和结构整体刚度评估。已有结构位移测量综述和结构健康监测数据融合综述均指出，位移观测在精度、参考基准、长期稳定性、布设成本和现场环境适应性之间存在明显权衡[1-2]。

传统位移测量方法主要包括 LVDT、拉线位移计、激光位移计、全站仪和视觉测量等。接触式方法精度较高，但通常需要固定参考基座，现场长期布设困难；光学方法可以实现非接触测量，但容易受视线遮挡、光照、雨雾、支架稳定性和参考点布设影响[1]。加速度计布设方便、采样率高，但由加速度双积分恢复位移时，低频噪声、初值误差和传感器偏置会持续放大，因此常需要状态空间或多源融合方法抑制漂移[3-4]。在桥梁长期监测场景中，如何在不依赖外部静止参考基座的情况下获得结构测点位移，是当前方案希望解决的核心问题。

毫米波雷达具有全天候、非接触、相位灵敏度高和硬件小型化等优点。已有 FMCW 雷达结构位移测量和毫米波微振感知研究表明，目标复数回波相位可用于毫米级乃至微米级位移估计[5-7]。对于 77 GHz 雷达，波长约为毫米量级，复数回波相位对亚毫米级距离变化十分敏感，因此毫米波雷达具备用于结构微位移测量的潜力。

### 1.2 现有毫米波雷达位移测量方法的基本思路

已有毫米波雷达位移测量研究通常默认雷达固定在地面、桥侧或稳定支架上，雷达观测结构上的运动目标。FMCW 雷达经 Range FFT 后得到不同 range-bin 的复数回波，目标所在距离单元的相位变化可用于恢复视线方向位移[5-6]。

在这一类问题中，典型流程是：固定雷达、选择强反射 range-bin、提取 slow-time 相位、进行相位解缠，再由相位变化换算 LoS 位移。围绕相位缠绕问题，已有研究提出了基于相位模糊消除、多 chirp 预测和加速度辅助 Kalman 滤波的解缠方法[8-10]。这些工作为“相位测位移”和“加速度辅助解缠”提供了基础，但其几何关系仍然以固定雷达为前提。

### 1.3 倒挂式安装场景带来的新问题

本文考虑的是雷达与 MEMS 加速度计共址安装在结构测点处，雷达随结构共同运动并朝向桥下或周围环境。此时问题从“固定雷达观测运动目标”变为“运动雷达观测环境静止散射体”。环境中的地面、桥下构件、支架、护栏或其他近似静止散射体，反而成为相对位移参考。Ma 等的倒挂式毫米波雷达与加速度计融合研究已经验证了这种利用环境静止 target 进行结构位移估计的可行性[11-14]。

倒挂式安装带来了几个新问题。

第一，同一 range-bin 内可能存在多个不同角度散射体。若仍按传统 range-bin-only 方法把这些散射体合成一个复数相量，其相位不再对应单一 LoS 目标，容易产生混合相位。已有 range-angle 微动感知和全场毫米波振动测量研究表明，距离-角度联合维度中的复数 component 可以承载可跟踪的 slow-time 相位信息[15-16]。

第二，最强反射目标不一定最稳定。自然环境中的散射体会受到 SNR 波动、遮挡、多径、旁瓣和移动干扰影响，单 target 方法对目标失效较敏感。

第三，毫米级结构响应下相位缠绕明显。wrapped phase 的跳变会影响直接 Itoh unwrap 和单目标相位跟踪，相位分支选择需要引入预测信息或额外观测约束[8-10]。

第四，从 LoS 位移恢复结构主振动方向位移需要转换系数。既有倒挂式雷达研究通常通过初始标定窗口估计 direction conversion factor[11-14]；而在自然散射环境中，AoA、雷达安装姿态、阵列误差和目标几何关系都会影响转换系数，固定系数会带来系统误差。

第五，加速度可以提供短时动力学预测，但直接二次积分容易出现漂移、偏置积累和同步误差，因此不适合作为长期位移真值直接使用[3-4]。

### 1.4 本阶段研究目标与技术路线概述

本阶段研究目标是在无外部静态参考系条件下，利用倒挂式毫米波雷达与共址 MEMS 加速度计估计结构测点主振动方向相对位移。具体包括：

- 构建运动雷达观测环境静止散射体的相位观测模型。
- 从 Range-Angle Map 中提取并维护多个候选 target，缓解单 range-bin 混合相位问题。
- 建立多目标 wrapped phase 与加速度预测融合框架。
- 将加速度作为 Kalman 状态预测输入，而不是直接积分为位移。
- 通过数值仿真和实测位移驱动半实测仿真验证方法链路可行性。

为解决上述问题，本文方法路线可以概括为：把传统“固定雷达观测运动结构目标”的问题，转化为“运动雷达观测环境静止散射体”的问题；把多个环境静止 target 看作同一结构位移在不同 LoS 方向上的投影观测；再通过加速度辅助预测和多目标相位融合恢复结构主振动方向相对位移。这里先给出方法模块，第 3 章补充基本原理，第 4 章再展开具体模型和算法。

- Range-Angle 多目标提取：把同 range-bin 但远角度的散射体拆分为不同 target，降低混合相位风险[15-17]。
- AoA 冷启动：利用目标角度为转换系数提供初始几何先验，使算法可以在线启动。
- 结构主相位 Kalman 融合：状态变量定义为结构主振动方向位移对应的连续相位，而不是某个 target 的 LoS 相位，该递推估计框架以经典 Kalman 滤波为基础[18]。
- prediction-aided phase correction：用加速度辅助的状态预测推断各 target 所在的相位分支，校正 wrapped phase[10]。
- online beta bootstrap：用 LoS corrected phase 和结构主相位估计在线修正 $\beta_i$。
- adaptive R：根据 target 质量动态调整观测噪声，对 SNR drop、dropout 或异常相位 target 降权，其思想与自适应滤波中根据创新或观测质量调节测量噪声统计量的做法一致[19-20]。

## 2. 本阶段主要贡献与方法依据

### 2.1 倒挂式毫米波雷达数学模型与问题定义

本文首先建立倒挂式安装场景下的毫米波雷达相位观测模型。传统雷达测振通常是“固定雷达观测运动目标”，而本文场景是“雷达随结构测点运动，观测环境中的静止散射体”。这一变化使得环境散射体从背景反射变成相对位移参考 target。

设结构测点主振动方向相对位移为 $\delta q$，第 $i$ 个环境静止 target 的 LoS 位移为 $d_{i}^{\mathrm{LOS}}$。沿用 Ma 等人的 direction conversion factor 定义，本文用 $\beta_i$ 表示 LoS 位移到结构真实振动方向位移的转换系数：

$$
\delta q(t)=\beta_i d_i^{\mathrm{LOS}}(t).
$$

相位层面定义结构主相位 $\Theta(t)=4\pi\delta q(t)/\lambda$，则有：

$$
\Theta(t)=\beta_i\phi_i^{\mathrm{LOS}}(t),
\qquad
\phi_i^{\mathrm{LOS}}(t)=\frac{1}{\beta_i}\Theta(t)+b_i.
$$

其中 $b_i$ 为初始相位偏置。该模型说明了倒挂式场景下多目标观测的可能性：多个环境静止 target 观测的是同一个结构主位移，只是各自具有不同 LoS 投影关系。已有倒挂式雷达与加速度融合研究已经验证环境静止 target 可用于结构位移估计[11-14]，本文进一步关注多个自然散射 target 在相位域内如何共同建模和融合。

这一数学模型也暴露出一个关键问题：如果仍以 range-bin 为基本 target 单元，那么同一个 range-bin 内可能包含多个角度差很大的散射体。此时该 range-bin 的复数回波是多个 phasor 的叠加，其相位不再对应单一 LoS 几何方向。若直接对该混合相位拟合转换系数 beta，拟合得到的 beta 只是一个混合等效量，可能随散射体幅值、相对相位和运动幅值变化而漂移。

因此，本文提出的第一个贡献不是简单增加目标数量，而是先明确：倒挂式雷达中“target 的定义尺度”会直接影响转换系数拟合质量。当同 range-bin 内目标角度差较大时，range-bin 级 beta 拟合效果会变差，必须把 target 从 range-bin 层面进一步细化到 angle-bin 或 angle cluster 层面。

### 2.2 基于 angle-bin 的多目标方案

基于上述问题，本文提出基于 angle-bin 的多目标 reference target 方案。具体来说，前端不再只在 range profile 上选择一个最强反射点，而是在 Range-Angle Map 上提取候选散射体。对于同一 range-bin 内角度接近的 peaks，可以合并成一个等效 angle cluster；对于同一 range-bin 内角度差较大的 peaks，则保留为不同 target。

候选 target 可定义为：

$$
T_i=(r_i,\mathcal{C}_i)
$$

其中 r_i 为 range-bin，C_i 为 angle-bin 或 angle cluster。这样做的意义有三点。

第一，它直接解决前一节指出的同 range-bin 多角度散射体混合问题。角度差大的散射体不再被强行合成为一个 pseudo target，因此后续每个 target 的相位和转换系数具有更清晰的几何含义。range-angle 微动感知、全场毫米波振动测量和 MIMO-FMCW 角度处理研究为这种 range-angle component 级相位跟踪提供了依据[15-17]。

第二，它天然提高了 target 丢失时的鲁棒性。倒挂场景中的自然散射体可能受遮挡、SNR 波动、多径或车辆干扰影响，单一 target 一旦失效，传统单目标方法容易中断；而 angle-bin 多目标方案保留多个可用环境 target，当某个 target 退化或短时丢失时，其他 target 仍可维持结构主相位估计。

第三，当多个 target 信号质量都较好时，该方案可以最大程度利用冗余观测。多个 target 不是简单取平均，而是在统一结构主相位状态下形成多行观测，从而同时利用不同 LoS 方向提供的相位信息。

### 2.3 基于最小二乘的转换系数拟合

在获得 angle-bin 级 target 后，本文进一步提出用最小二乘拟合转换系数，而不是依赖迭代式 beta 搜索。其原因在于，前一步已经把几何方向相差较大的散射体拆分开，使每个 target 的相位序列更接近单一 LoS 投影模型。此时 $\beta_i$ 可以在短窗口内由 LoS corrected phase 和结构主相位估计直接拟合。

对于第 $i$ 个 target，先由预测辅助相位校正得到 LoS corrected phase $\phi_{i,k}^{\mathrm{LOS,corr}}$。结构方向观测构造为：

$$
y_{i,k}
=
\beta_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

若令 $x_k=\phi_{i,k}^{\mathrm{LOS,corr}}-b_i$，$y_k=\hat{\Theta}_k^+$，则 $\beta_i$ 可由短窗口最小二乘估计：

$$
\hat{\beta}_{i}
=
\frac{\sum_k x_k y_k}
{\sum_k x_k^2}
$$

该处理成立的前提正是上一节的 angle-bin target 拆分。如果仍在 range-bin 层面对多个角度差很大的散射体做 beta 拟合，输入相位本身就是混合相位，最小二乘也只能拟合出不稳定的等效 beta。因此，本文的转换系数拟合不是孤立改进，而是依赖于前一贡献：先把 target 定义从 range-bin 细化到 angle-bin，再进行 target-wise $\beta_i$ 最小二乘估计。

与迭代式 beta 搜索相比，最小二乘拟合的优点是物理含义更直接、计算更简单，也更适合放入在线闭环。AoA 只用于提供 $\beta_i$ 的冷启动初值，后续正文以 $\beta_i$ 作为 LoS 到结构方向转换系数持续修正。

### 2.4 基于相位的闭环 Kalman 融合框架

最后，本文提出一套闭环 Kalman 融合框架，将上述创新点串联起来。该框架不是先分阶段完成 target 选择、相位解缠、转换系数标定，再离线融合位移；而是在同一个在线递推过程中完成 AoA 冷启动、预测辅助相位校正、结构主相位更新、$\beta_i$ 自举和 target-wise adaptive R 调整。

该闭环的核心状态不是某一个 target 的 LoS 相位，而是结构主振动方向的连续相位：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix}
$$

加速度进入状态预测，用于提供短时动力学先验；多个 angle-bin target 的 wrapped phase 经预测辅助校正后，先转换为结构方向主相位观测再进入 Kalman update；LoS corrected phase 同时用于 $\beta_i$ 最小二乘更新；滤波创新和 target 质量指标进一步用于 adaptive R，动态降低退化 target 的权重。

因此，本文的第四个贡献是把前面三个模块组成全流程一体化方法：AoA 负责冷启动，angle-bin 多目标负责明确 target 几何尺度，最小二乘 $\beta_i$ 拟合负责在线修正转换系数，adaptive R 负责处理 target 质量变化，结构主相位 Kalman 则把这些环节闭合到同一个递推估计框架中。这样既避免了分阶段误差传递，也能在 target 丢失、SNR 下降、AoA 初值误差和相位缠绕同时存在时保持位移估计连续性。

## 3. 基本原理

### 3.1 FMCW 毫米波雷达相位测距原理

FMCW 毫米波雷达发射频率随时间线性变化的 chirp 信号，目标回波与发射信号混频后得到差频信号。对快时间维做 Range FFT，可以在距离维上分离不同 range-bin 的复数回波。

![[Pasted image 20260510160557.png]]

Range FFT 的距离分辨率主要由带宽决定，通常为厘米量级；但复数回波相位对距离变化非常敏感，可以用于亚毫米级微位移估计。因此，毫米波雷达测振的核心不是直接读取 range-bin 位置变化，而是追踪目标所在距离单元的复数相位变化[5-7]。

![[Pasted image 20260510161032.png]]

设雷达波长为 λ，目标与雷达之间 LoS 距离变化为 ΔR，对应回波相位变化为 Δφ，则有：

$$
\Delta R(t)=\frac{\lambda}{4\pi}\Delta\phi(t)
$$

这里的 4π 来自往返传播路径。对于 77 GHz 毫米波雷达，波长约为 3.9 mm，半波长约为 1.95 mm，因此相位对毫米级位移十分敏感。

### 3.2 相位缠绕与解缠问题

雷达复数相位通常由 `atan2` 得到，取值范围为负 π 到正 π。当真实连续相位跨越边界时，观测相位会发生 2π 跳变，这就是相位缠绕。位移振幅增大、噪声升高、目标 SNR 降低或多目标相位混合时，传统 unwrap 可能选错相位分支。

传统 Itoh unwrap 假设相邻采样点相位变化不超过 π，并用相邻差分进行补偿。该假设在结构强响应、采样不足、目标遮挡、相位跳变或同 range-bin 多散射体混合时不一定成立。已有相位模糊消除、Doppler-based unwrap、多 chirp adaptive unwrap 和加速度辅助 Kalman 方法都说明，相位解缠需要利用额外预测或运动约束来减少分支错误[8-10]。因此，本文把相位解缠写成“预测辅助相位分支校正”问题：先预测当前 target 应落在哪个相位分支，再将 wrapped phase 校正到连续分支。

### 3.3 倒挂式场景下的相位观测模型

倒挂式安装时，雷达随结构测点运动，环境静止散射体提供相对参考。设结构主振动方向相对位移为 $\delta q$，第 $i$ 个 target 的 LoS 位移与结构主振动方向位移之间的转换系数为 $\beta_i$，则有：

$$
\Theta(t)=\beta_i\phi_i^{\mathrm{LOS}}(t),
\qquad
\phi_i^{\mathrm{LOS}}(t)=\frac{1}{\beta_i}\Theta(t)+b_i.
$$

其中 $b_i$ 为 target 的初始相位偏置。$\beta_i$ 表示 LoS 到结构主振动方向的 direction conversion factor，既与 AoA 几何有关，也受安装姿态、阵列误差和实际散射几何影响。既有倒挂式雷达研究已经把方向转换系数作为 LoS 位移到结构振动方向位移换算的关键标定量[11-14]；本文进一步将 $\beta_i$ 作为可在线修正的 target-wise 参数，而不只作为固定常数使用。

### 3.4 加速度辅助预测原理

加速度计与雷达共址安装，可以提供结构测点的短时动力学信息。直接对加速度二次积分虽然理论上可以得到位移，但在实际场景中会受到零偏、比例因子、重力分量、低频漂移和时间同步误差影响，长期积分结果容易失真。

本文不把加速度直接积分结果作为位移输出，而是把加速度作为 Kalman 状态预测输入。这样，加速度负责提供短时相位分支预测和动力学约束，雷达相位负责提供长期观测校正，两者在滤波框架中互补[3-4,10]。

## 4. 多目标结构主相位融合方法

### 4.1 方法总体框架

本文方法总体框架对齐 `idea/overall_processing_architecture.md`。完整链路不是简单的“雷达前端 -> Kalman -> 位移输出”，而是由两个闭合子流程组成：第一部分是不依赖相位解缠的 range-angle target 提取与筛选；第二部分是结构主相位 Kalman 融合闭环。流程图使用 Obsidian `Mehrmaid` 插件，代码块语言为 `mehrmaid`。

第一部分是 target 提取与筛选。该阶段只使用 ADC 前端、range-angle 幅值/复数信息和加速度频带先验，不使用结构位移真值，也不依赖完整相位解缠或已知转换系数。

```mehrmaid
flowchart TD
    SYS("共址安装<br/>倒挂毫米波雷达 + 加速度计") --> SYNC("同步采集")
    SYNC --> ADC("雷达 ADC")
    SYNC --> ACC("同步加速度")

    ADC --> RA("Range FFT + Angle FFT 或 DBF")
    RA --> MAP("复数距离角度图")
    MAP --> AMP("幅值图")
    AMP --> PEAK("二维峰值检测")

    PEAK --> MERGE("同 range 近角合并")
    MERGE --> SEP("同 range 远角保留")
    SEP --> TRACK("滑动窗口维护")
    TRACK --> PRES("出现率稳定性确认")

    ACC --> SPEC("加速度频谱分析")
    PRES --> BAND("频带一致性筛选")
    SPEC --> BAND

    BAND --> SET("可用 target 集合")
    SET --> T1("Target 1<br/>复数序列 / 包裹相位 / AoA / 偏置")
    SET --> T2("Target 2<br/>复数序列 / 包裹相位 / AoA / 偏置")
    SET --> TM("Target m<br/>复数序列 / 包裹相位 / AoA / 偏置")
```

第二部分是结构主相位 Kalman 融合闭环。该阶段的关键不是先离线解缠每个 target，再分别恢复位移，而是用结构主相位预测为每个 target 选择 wrapped phase 分支；同一个校正相位同时进入 Kalman update 和转换系数最小二乘自举。

```mehrmaid
flowchart TD
    MT("可用 target 集合<br/>包裹相位 / AoA / 偏置") --> AOA("AoA 冷启动")
    AOA --> H("观测矩阵构造")
    MT --> H

    ACC("同步加速度") --> PRED("状态预测")
    XPREV("上一时刻后验") --> PRED
    PRED --> BRANCH("LoS 分支预测")
    H --> BRANCH
    MT --> WRAP("包裹相位")
    WRAP --> CORR("预测辅助相位校正")
    BRANCH --> CORR

    CORR --> ZC("校正相位")
    ZC --> OBS("多目标观测模型")
    H --> OBS
    OBS --> KF("Kalman 更新")
    KF --> OUT("结构主相位与位移")
    OUT --> XPREV

    ZC --> LS("转换系数最小二乘自举")
    OUT --> LS
    LS --> H
    LS --> BRANCH

    KF --> RADAPT("target-wise adaptive R")
    RADAPT --> OBS
```

压缩到汇报页时，可以保留下面的模块图：

```mehrmaid
flowchart LR
    S("共址传感") --> RA("Range-Angle target 提取")
    RA --> FS("稳定性与频带筛选")
    FS --> INIT("AoA 冷启动")
    INIT --> KF("结构主相位 Kalman")
    KF --> PC("预测辅助相位校正")
    PC --> KF
    KF --> OUT("相对位移输出")
    PC --> ADAPT("系数自举与 adaptive R")
    ADAPT --> KF
```

因此，4.1 的框架应理解为“target 提取筛选 + Kalman 融合闭环”两级结构。前者解决哪些环境散射体可以作为 reference target；后者解决这些 target 的 wrapped phase 如何在结构主相位状态中完成相位校正、转换系数更新、噪声自适应和位移输出。

### 4.2 Range-Angle 候选目标提取

前端输入为多帧 ADC cube。经过 Range FFT 后得到距离维复数响应，再通过 Angle FFT 或 DBF 得到 Range-Angle Map：

$$
Y_k(b,p)
$$

其中 b 表示 range-bin，p 表示 angle-bin，k 表示 slow-time 帧序号。二维峰值检测在 Range-Angle Map 上寻找候选散射体，而不是只选择某个 range-bin 的最大幅值点。range-angle component 用于 slow-time 相位跟踪的依据，可见于 mmWBat、mmSHM 和 MIMO-FMCW 多目标分离相关研究[15-17]。

![[Pasted image 20260510165842.png]]

候选 target 定义为：

$$
T_i=(r_i,\mathcal{C}_i)
$$

其中 C_i 表示同一 range-bin 内的一个 angle-bin 或角度相近的 angle-bin cluster。同一 range-bin 内角度差小于约 15° 的 peaks 合并为一个等效 target；同一 range-bin 内角度差较大的 peaks 保留为不同 target。这样可以避免把同 range 但远角度的散射体强行混合成一个 pseudo target。

### 4.3 目标稳定性与频带一致性筛选

候选 target 需要经过动态筛选后才进入融合。筛选依据包括：

- presence gate：目标在滑动窗口内需要持续出现，避免短时噪声峰进入滤波。
- SNR 或幅值稳定性：低 SNR、幅值剧烈波动或短时遮挡 target 应降低权重或剔除。
- 几何约束：AoA 对应的投影方向不能退化到不可用状态。
- 频带一致性：target 相位中的主要频带应与加速度观测的结构响应频带一致。
- 数量约束：进入 Kalman 的 target 数量保持在有限范围内，避免低质量 target 过多稀释稳定观测。

频带一致性中，加速度并不提供最终位移真值，而是提供结构响应的频域先验。既有雷达-加速度融合系统通常利用加速度辅助校准、频带选择或相位预测[11,14]；若某个 target 的相位主要能量与加速度响应频带明显不一致，则更可能来自噪声、多径或移动干扰。

### 4.4 结构主相位状态建模

传统 Ma-family 单 target Kalman 方法通常把状态定义为某个 target 的 LoS 连续相位[10]。本文把状态改为结构主振动方向的连续相位：

$$
\mathbf{x}_k=
\begin{bmatrix}
\Theta_k\\
\dot{\Theta}_k
\end{bmatrix}
$$

结构主相位与结构相对位移之间满足：

$$
\Theta_k=\frac{4\pi}{\lambda}\delta q_k
$$

加速度进入状态预测模型：

$$
\mathbf{x}_k^-=\mathbf{A}\mathbf{x}_{k-1}^+ + \mathbf{B}a_{\mathrm{meas},k-1}
$$

这使得滤波器预测的是结构主相位，而不是某个 target 的局部 LoS 相位。多个 target 只是对同一结构主相位的不同投影观测。

### 4.5 多目标 wrapped phase 观测模型

雷达原始观测是第 $i$ 个 target 的 wrapped LoS phase：

$$
\psi_{i,k}=\angle IQ_i(k),\qquad \psi_{i,k}\in(-\pi,\pi].
$$

经过预测辅助相位校正后，得到 LoS corrected phase $\phi_{i,k}^{\mathrm{LOS,corr}}$。由于本文状态定义为结构主相位，因此 Kalman 更新前先构造结构方向观测：

$$
y_{i,k}
=
\beta_i
\left(
\phi_{i,k}^{\mathrm{LOS,corr}}-b_i
\right).
$$

对应结构方向观测模型为：

$$
y_{i,k}
=
\Theta_k+e_{i,k},
\qquad
H_i=
\begin{bmatrix}
1&0
\end{bmatrix}.
$$

多个 target 同时进入滤波时，可将 $y_{i,k}$ 按行堆叠，形成结构方向多通道观测模型。这样，目标数量增加不是简单取平均，而是在同一个结构主相位状态下进行带权融合。该处理吸收了既有多 target 倒挂式雷达研究对目标遮挡和多 good targets 的认识[12-13]，但把多目标关系前移到相位观测模型内部。

当前代码与正文统一采用结构方向观测模型；LoS 相位只在预测辅助相位校正阶段使用

$$
\phi_{i,k}^{\mathrm{LOS}}
=
\frac{\Theta_k}{\beta_i}+b_i.
$$

进入 Kalman 更新前，LoS corrected phase 先乘以 $\beta_i$ 转为结构方向主相位观测，因此观测行保持 $H_i=[1,0]$。

### 4.6 预测辅助相位校正

Kalman 预测先给出结构主相位预测值，再映射到每个 target 的 LoS 相位预测：

$$
\hat{\phi}_{i,k}^{\mathrm{LOS},-}
=
\frac{\hat{\Theta}_k^-}{\hat{\beta}_{i,k}^{-}}+b_i
$$

根据该预测值，对 wrapped phase 选择最接近的 2π 分支：

$$
\phi^{\mathrm{LOS,corr}}_{i,k}
=
\psi_{i,k}
+2\pi\operatorname{round}
\left(
\frac{\hat{\phi}_{i,k}^{\mathrm{LOS},-} - \psi_{i,k}}{2\pi}
\right)
$$

校正后的 $\phi^{\mathrm{LOS,corr}}_{i,k}$ 仍是 LoS 连续相位，需乘以 $\beta_i$ 后才成为结构方向主相位观测。相比直接 Itoh unwrap，这一处理利用了加速度辅助的结构主相位预测，因此更适合强 wrapping、噪声和目标质量波动场景[8-10]。

### 4.7 转换系数在线自举

AoA 可为 $\beta_i$ 提供冷启动初值。若第 $i$ 个 target 的 AoA 与结构振动方向夹角为 $\theta_i$，先计算结构方向到 LoS 的投影初值：

$$
\hat{p}_{i,0}=|\cos\theta_i|
$$

再取其倒数作为 LoS 到结构方向的转换系数初值：

$$
\hat{\beta}_{i,0}=\frac{1}{\max(\hat{p}_{i,0},\epsilon_p)}
$$

但 AoA 只能提供几何先验，不能完全覆盖安装姿态、阵列误差和实际散射点偏差。MIMO 雷达角度估计依赖虚拟阵列孔径、通道幅相一致性和角度处理流程[17]，因此本文只把 AoA 作为冷启动先验，并使用短窗口内的 $\phi_{i,k}^{\mathrm{LOS,corr}}$ 与结构主相位估计 $\hat{\Theta}_k^+$ 做局部最小二乘，在线更新 $\beta_i$。

这一做法解决了一个循环依赖：相位校正需要 $\beta_i$，$\beta_i$ 自举又需要连续 LoS 相位。AoA 冷启动提供初值，prediction-aided correction 生成局部 LoS corrected phase，online beta bootstrap 再逐步修正 $\beta_i$。

### 4.8 自适应观测噪声调整

不同 target 的质量会随时间变化。若某个 target 出现 SNR drop、dropout、幅值突变、相位残差变大或频带不一致，则应降低其对 Kalman update 的影响。本文通过 target-wise adaptive R 调整观测噪声。这一设计借鉴自适应滤波中根据观测统计特性更新测量噪声协方差的思想[19-20]：

- target 稳定且残差小，则保持较小观测噪声，赋予较高权重。
- target 质量下降或残差异常，则增大观测噪声，降低其更新权重。
- target 长时间缺失或不满足筛选条件，则从当前目标集合中移除。

因此，多目标融合不是把所有 target 无差别地平均，而是让稳定 target 主导更新，让退化 target 自动降权。

## 5. 数值仿真设计

### 5.1 仿真目标

数值仿真的目标是验证算法链路是否闭环可行，并分析各关键模块对典型失效问题的作用。重点验证以下问题：

- Range-Angle target 定义是否能缓解同 range-bin 多散射体混合。
- prediction-aided phase correction 是否能改善强相位缠绕场景。
- adaptive R 和 target screening 是否能处理目标质量退化和缺失。
- online beta bootstrap 是否能修正 AoA 初值误差，并观察 $\beta_i$ 的收敛情况。
- 实测桥梁位移波形驱动下，完整链路是否仍可运行。

需要强调，当前结果属于合成数值仿真与实测位移驱动的半实测仿真，不等同于真实 IWR1843 ADC 端到端实测验证。

### 5.2 仿真数据生成流程

仿真流程按统一链路组织：先构造结构位移真值，再由位移真值生成 target LoS 相位，并合成 IQ、wrapped phase 和 synthetic ADC cube；同时生成带噪声、偏置、漂移和同步误差的加速度观测；最后让各方法处理同一组观测，并与相对位移真值比较。

评价对象为相对位移：

$$
\delta q(t)=q(t)-\operatorname{mean}\left(q(t)\ \mathrm{over\ cold\ start\ window}\right)
$$

雷达相位仿真模型为：

$$
\Theta(t)=\frac{4\pi}{\lambda}q(t)
$$

$$
\Theta(t)=\beta_i\phi_i^{\mathrm{LOS}}(t)
$$

$$
\phi_i^{\mathrm{LOS}}(t)=\frac{\Theta(t)}{\beta_i}+b_i
$$

$$
IQ_i(t)=A_i\exp\left(j\phi_i^{\mathrm{LOS}}(t)\right)+n_i(t)
$$

$$
\psi_i(t)=\angle IQ_i(t)
$$

当前代码与正文采用同一物理相位模型：$\beta_i$ 始终表示 LoS 到结构真实振动方向的转换系数；预测回 LoS 空间时使用 $\Theta(t)/\beta_i$。

普通合成场景由位移真值生成加速度真值，再叠加噪声、偏置、漂移和同步误差得到加速度观测。实测位移驱动半实测场景使用 TDMS 激光位移通道 `卡3激光位移/3-4` 作为真实桥梁响应波形，经事件窗口、滤波和陷波后得到位移真值，再由位移二阶微分得到加速度并叠加 seeded noise。雷达观测仍由上述物理相位模型合成。

### 5.3 场景设置

| scenario | 位移来源/波形 | target 数 | target angles | target SNR | 退化条件 | 设计目的 |
|---|---|---:|---|---|---|---|
| `nominal_multifrequency` | 20/40/60 Hz 多频，0.08/0.04/0.02 mm | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | 无 | 基准多目标多频振动 |
| `ma2023_balanced_good_targets` | 0.3/0.5/1.0 Hz，0.5/0.3/0.2 mm | 5 | 5/12/19/26/33 deg | 全 35 dB | 多个高质量 target | 文献友好条件对照 |
| `strong_wrapping` | 振幅增至 0.45/0.25/0.12 mm | 5 | 10/25/40/55/70 deg | 30/25/20/15/10 dB | 强相位缠绕 | 压测相位分支校正 |
| `aoa_error_bootstrap` | 默认多频 | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | AoA 初值误差 10 deg | 验证 online beta bootstrap，代码诊断为 beta 收敛 |
| `target_snr_drop` | 默认多频 | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0/1 在中段降 25 dB | 验证 adaptive R |
| `target_dropout` | 默认多频 | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0 中段 dropout | 验证目标缺失鲁棒性 |
| `mixed_scatterer_rangebin` | 默认多频 | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | target 0 内含两散射体 | 验证 range-bin 混合散射风险 |
| `same_range_far_angles` | 0.32/0.15/0.075 mm | 4 | 5/45/25/35 deg | 32/32/24/22 dB | 前两个 target 同 range 远角度 | 验证 Range-Angle 分离 |
| `low_snr_multitarget` | 默认多频 | 5 | 10/25/40/55/70 deg | 12/10/8/6/4 dB | 整体低 SNR | 验证低信噪比融合 |
| `vehicle_event_nonstationary` | 非平稳车辆事件包络 | 5 | 10/25/40/55/70 deg | 25/20/15/10/5 dB | 静止启动后非平稳事件 | 验证非平稳响应 |
| `measured_bridge_point4_transverse` | TDMS 激光位移 3-4 | 5 | 5/15/25/35/45 deg | 26/24/22/20/18 dB | 激光位移驱动、雷达相位合成 | 验证真实桥梁波形下链路可运行 |

### 5.4 对比方法与评价指标

| 方法                         | 基本思路                                            | 作用                   |
| -------------------------- | ----------------------------------------------- | -------------------- |
| `itoh_ls`                  | 对多 target 相位做 Itoh unwrap 后进行最小二乘换算             | 传统相位解缠 baseline      |
| `single_target_ma_style`   | 单 target Ma-style Kalman，相位状态为 target LoS phase | 对比单目标加速度辅助方法         |
| `ma2026_reproduction`      | 基于公开论文公式与流程实现的 Ma-family baseline               | 文献方法族对照，不是 Ma 官方源码复现 |
| `selected_aoa_fixed_beta` | 使用筛选 target 和 AoA 固定 $\beta$，但不做 online bootstrap | 验证固定几何先验的局限          |
| `proposed`                 | 多目标结构主相位 Kalman，含相位校正和 $\beta$ 自举 | 验证核心融合框架             |
| `proposed_full_pipeline`   | 在 proposed 基础上加入 Range-Angle 前端、目标筛选和自适应噪声      | 当前主方案                |

主要评价指标包括 RMSE、MAE、最大误差、结构主相位误差、unwrap error、selected target 数量、corrected observation 数量和转换系数相对误差；当前代码输出 $\beta$ 的相对误差诊断。半实测场景还通过激光通道时域、频谱和动态相关性图说明所选桥梁位移波形的有效性。

## 6. 仿真结果与分析

### 6.1 总体误差结果

下表给出各 scenario 下不同方法的 RMSE，对应单位为 mm。表中数值来自重新生成的数值仿真结果。需要注意，结果应理解为不同退化场景下的机制验证，不应写成“所有场景全面最优”。

| 场景 | `itoh_ls` | `single_target_ma_style` | `ma2026_reproduction` | `selected_aoa_fixed_beta` | `proposed` | `proposed_full_pipeline` |
|---|---:|---:|---:|---:|---:|---:|
| `nominal_multifrequency` | 0.013007 | 0.008483 | 0.053692 | 0.022540 | 0.007366 | 0.007265 |
| `ma2023_balanced_good_targets` | 0.004053 | 0.001460 | 0.037064 | 0.016383 | 0.001109 | 0.001205 |
| `strong_wrapping` | 0.007302 | 0.049198 | 0.220250 | 0.055089 | 0.039386 | 0.038741 |
| `aoa_error_bootstrap` | 0.013007 | 0.008483 | 0.053692 | 0.022540 | 0.008644 | 0.007267 |
| `target_snr_drop` | 9.148472 | 0.018043 | 0.299926 | 0.028316 | 0.008539 | 0.009899 |
| `target_dropout` | 0.012921 | 1.274598 | 0.053692 | 0.027775 | 0.007503 | 0.008592 |
| `mixed_scatterer_rangebin` | 0.026781 | 0.016109 | 0.049107 | 0.023389 | 0.009160 | 0.007109 |
| `same_range_far_angles` | 0.005664 | 0.031874 | 0.127338 | 0.036103 | 0.026568 | 0.025306 |
| `low_snr_multitarget` | 0.059297 | 0.016939 | 0.047153 | 0.031592 | 0.011296 | 0.013590 |
| `vehicle_event_nonstationary` | 0.012959 | 0.004710 | 0.016125 | 0.019849 | 0.004721 | 0.004474 |
| `measured_bridge_point4_transverse` | 0.011141 | 0.002967 | 0.616525 | 0.013626 | 0.007445 | 0.003400 |

从总体结果看，proposed full pipeline 在 target SNR drop、target dropout、same range far angles、AoA 初值误差、车辆非平稳事件和半实测场景中保持较低 RMSE。这说明当前方法对典型退化问题具有可行性，但并不意味着在任意条件下都必然优于所有 baseline。例如文献友好条件下，单 target 方法本身也可能表现较好。

### 6.2 强相位缠绕场景分析

strong wrapping 场景用于检验相位分支校正。该场景中，单 target Ma-family baseline 的 RMSE 为 0.220250 mm，selected AoA fixed beta 为 0.055089 mm，proposed full pipeline 为 0.038741 mm。

![[reports/numerical_simulation_assets_png/strong_wrapping_phase_correction.png]]

图中对比了 wrapped phase、prediction-aided corrected phase 和真实 LoS phase。结果说明，在相位跨越 2π 分支时，仅依赖相邻相位差或单目标趋势容易产生分支错误；引入加速度辅助的结构主相位预测后，可以更稳定地选择相位分支。

### 6.3 同 range 远角度目标场景分析

same range far angles 场景用于验证 Range-Angle target 定义的必要性。两个 target 位于相同 range-bin 但角度差较大，如果采用 range-bin-only 方法，会把多个散射体的复数相量混合在一起，导致相位不再对应单一物理 target。

![[reports/numerical_simulation_assets_png/vehicle_event_nonstationary_range_angle_frame.png]]

该图展示了 Range-Angle 前端能够在二维空间中定位候选散射体。虽然图示来自车辆非平稳事件场景，但其作用是说明当前前端不是只读取单个 range-bin，而是在 range-angle 平面上定义 target。same range far angles 场景的 RMSE 中，ma2026_reproduction 为 0.127338 mm，selected AoA fixed beta 为 0.036103 mm，proposed full pipeline 为 0.025306 mm，说明同 range 远角度散射体应在 Kalman 前被分离。

### 6.4 目标退化与缺失场景分析

target SNR drop 和 target dropout 场景用于检验动态降权和目标筛选能力。target SNR drop 中，target 0 和 target 1 在中段发生明显 SNR 下降。该场景下 ma2026_reproduction 为 0.299926 mm，selected AoA fixed beta 为 0.028316 mm，proposed full pipeline 为 0.009899 mm。

![[reports/numerical_simulation_assets_png/target_snr_drop_adaptive_r.png]]

该图展示目标质量退化时 target-wise adaptive R 的变化。低质量 target 的观测噪声被动态增大，从而降低其 Kalman 更新权重。

![[reports/numerical_simulation_assets_png/vehicle_event_nonstationary_target_selection_timeline.png]]

target selection 时间线展示了候选 target 的在线维护过程。full pipeline 不是固定使用所有 target，而是根据稳定性和频带一致性保留可用 target，从而降低坏 target 对结构主相位估计的影响。

![[reports/numerical_simulation_assets_png/vehicle_event_nonstationary_selected_vs_all_targets_displacement.png]]

该图对比了 all-target proposed 与 full pipeline 目标筛选后的位移估计结果，用于说明目标筛选可以提高复杂事件中的鲁棒性。

### 6.5 AoA 初值误差场景分析

aoa error bootstrap 场景人为引入 AoA 初值误差，用于检验 $\beta_i$ 在线修正能力。该场景下 ma2026_reproduction 为 0.053692 mm，selected AoA fixed beta 为 0.022540 mm，proposed full pipeline 为 0.007267 mm。

![[reports/numerical_simulation_assets_png/aoa_error_bootstrap_beta_bootstrap.png]]

图中可以看到，AoA 更适合作为冷启动先验，而不是最终固定转换系数。online beta bootstrap 利用 LoS corrected phase 与结构主相位估计逐步修正 $\beta_i$，从而反映 AoA 初值误差和安装误差被逐步修正。

### 6.6 非平稳车辆事件场景分析

vehicle event nonstationary 场景模拟 quiet start 后出现的非平稳车辆事件。该场景下，ma2026_reproduction 为 0.016125 mm，selected AoA fixed beta 为 0.019849 mm，proposed full pipeline 为 0.004474 mm。

非平稳响应对方法提出两个要求：一是冷启动阶段需要建立 target、$\beta_i$ 和相位偏置的初始状态；二是事件发生后，目标筛选和 adaptive R 需要持续抑制异常 target。仿真结果说明，当前链路在非平稳车辆事件中可以保持连续位移输出。

### 6.7 实测位移驱动半实测场景分析

measured bridge point4 transverse 场景使用 TDMS 激光位移通道 `卡3激光位移/3-4` 作为真实桥梁响应波形来源。该波形经事件窗口选择、滤波和陷波处理后作为位移真值，再生成加速度观测和雷达相位观测。

![[reports/numerical_simulation_assets_png/laser_time_channels.png]]

该图展示 TDMS 激光位移多通道时域响应，用于说明半实测场景所用真实桥梁位移波形来源。

![[reports/numerical_simulation_assets_png/laser_spectrum_channels.png]]

该图展示激光通道频谱特性，用于支撑分析频带和工频陷波设置。

![[reports/numerical_simulation_assets_png/laser_dynamic_correlation.png]]

该图展示激光通道动态成分相关性，说明所选桥梁响应波形具有一定通道一致性基础。

在该半实测场景中，ma2026_reproduction 为 0.616525 mm，selected AoA fixed beta 为 0.013626 mm，proposed full pipeline 为 0.003400 mm。该结果说明真实桥梁位移波形下当前算法链路可运行。但必须强调：这里雷达观测仍由物理相位模型合成，不是完整毫米波雷达实测，也不能替代真实雷达 ADC 与参考传感器同步采集后的端到端验证。

## 7. 阶段性结论与后续工作

### 7.1 阶段性结论

本阶段已经建立倒挂式毫米波雷达与 MEMS 加速度计融合的结构位移估计框架。方法上，本文将环境静止散射体视为运动雷达的相对参考 target，并通过 Range-Angle 多目标提取、目标稳定性筛选、结构主相位 Kalman 融合、prediction-aided phase correction、adaptive R 和 online beta bootstrap 形成完整算法闭环；代码实现与正文统一采用 $\beta$ 作为 LoS 到结构方向的转换系数。

数值仿真表明，该方法在强相位缠绕、target SNR drop、target dropout、AoA 初值误差、同 range 远角度散射体、低 SNR 多目标和非平稳车辆事件等场景下具有可行性。实测位移驱动半实测仿真进一步说明，在真实桥梁位移波形下，当前链路可以完成相对位移估计。

### 7.2 当前研究边界

当前研究仍有明确边界。

- 尚未完成真实 IWR1843 ADC 端到端实测验证。
- 真实阵列幅相误差、TDM-MIMO 相位补偿和角度轴校准尚未纳入实测链路。
- 雷达、加速度计和激光参考传感器的时间同步仍需在真实采集系统中处理。
- 加速度计灵敏度、安装方向、bias、重力分量和测点对应关系仍需标定。
- 现场多径、旁瓣、相干散射体、安装姿态变化和长期稳定性仍需进一步实验验证。
- 当前半实测场景只能说明真实桥梁位移波形下链路可运行，不是完整实测毫米波雷达验证。

### 7.3 下一阶段工作

| 工作项 | 当前状态 | 下一步 |
|---|---|---|
| 真实 IWR1843 ADC 文件解析 | 未完成 | 接入 raw ADC 文件格式、帧结构和通道组织 |
| 天线幅相与角度轴标定 | 未完成 | 建立 RX/TX 通道幅相、阵列误差和角度轴校准流程 |
| TDM-MIMO 相位补偿 | 未完成 | 处理多 TX 时序导致的相位差 |
| 雷达/加速度/参考位移同步 | 未完成 | 建立同步采集流程和时间戳对齐方法 |
| 加速度计标定 | 未完成 | 标定灵敏度、方向、bias、重力分量和测点对应关系 |
| 实验梁或真实桥梁验证 | 未完成 | 开展毫米波雷达、激光位移和加速度同步采集 |
| 多径与长期稳定性分析 | 未完成 | 分析桥下多径、移动干扰、target 生命周期和长期漂移 |
| 论文方法章节整理 | 进行中 | 将模型、算法流程和消融实验固化为论文表述 |

下一阶段应优先完成真实 IWR1843 ADC 解析、天线幅相与角度轴标定、同步采集流程搭建，并在实验梁或真实桥梁上开展毫米波雷达、参考位移传感器和加速度计的端到端同步验证。

## 参考文献

[1] MA Z, CHOI J, SOHN H. Structural displacement sensing techniques for civil infrastructure: A review[J]. Journal of Infrastructure Intelligence and Resilience, 2023, 2: 100041.

[2] WU R T, JAHANSHAHI M R. Data fusion approaches for structural health monitoring and system identification: Past, present, and future[J]. Structural Health Monitoring, 2020, 19(2): 552-586.

[3] GINDY M, VACCARO R, NASSIF H, et al. A state-space approach for deriving bridge displacement from acceleration[J]. Computer-Aided Civil and Infrastructure Engineering, 2008, 23: 281-290.

[4] CHO S, PARK J W, PALANISAMY R P, et al. Reference-free displacement estimation of bridges using Kalman filter-based multimetric data fusion[J]. Journal of Sensors, 2016, 2016: 3791856.

[5] LI C, CHEN W, LIU G, et al. A noncontact FMCW radar sensor for displacement measurement in structural health monitoring[J]. Sensors, 2015, 15(4): 7412-7433.

[6] GUO J, HE Y, JIANG C, et al. Measuring micrometer-level vibrations with mmWave radar[J]. IEEE Transactions on Mobile Computing, 2023, 22(4): 2248-2261.

[7] TAKAMATSU H, HINOHARA N, SUZUKI K, et al. Experimental analysis of accuracy and precision in displacement measurement using millimeter-wave FMCW radar[J]. Applied Sciences, 2025, 15(6): 3316.

[8] LIU J, LI Y, GU C. Solving phase ambiguity in interferometric displacement measurement with millimeter-wave FMCW radar sensors[J]. IEEE Sensors Journal, 2022, 22(9): 8482-8489.

[9] MA Z, HAI L, ZHANG T, et al. Accurate structural displacement measurement via enhanced millimeter-wave radar interferometry using multi-chirp-based adaptive phase unwrapping[J]. Measurement, 2026, 262: 120029.

[10] MA Z, ZHANG T, ZHU Y, et al. Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring[J]. Mechanical Systems and Signal Processing, 2026, 248: 113991.

[11] MA Z, CHOI J, YANG L, et al. Structural displacement estimation using accelerometer and FMCW millimeter wave radar[J]. Mechanical Systems and Signal Processing, 2023, 182: 109582.

[12] MA Z, CHOI J, SOHN H. Continuous bridge displacement estimation using millimeter-wave radar, strain gauge and accelerometer[J]. Mechanical Systems and Signal Processing, 2023, 197: 110408.

[13] MA Z, CHOI J, LEE J, et al. Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion[J]. Mechanical Systems and Signal Processing, 2025, 223: 111888.

[14] MA Z, HAN K, CHOI J, et al. Development and field deployment validation of a low-cost and high-precision displacement sensing system by fusing millimeter-wave radar and accelerometer[J]. Engineering Structures, 2024, 321: 118926.

[15] XIONG Y, LI S, GU C, et al. Millimeter-wave bat for mapping and quantifying micromotions in full field of view[J]. Research, 2021, 2021: 9787484.

[16] LI S, XIONG Y, SHEN X, et al. Multi-scale and full-field vibration measurement via millimetre-wave sensing[J]. Mechanical Systems and Signal Processing, 2022, 177: 109178.

[17] RAO S. MIMO Radar[R]. Dallas: Texas Instruments, 2018.

[18] KALMAN R E. A new approach to linear filtering and prediction problems[J]. Transactions of the ASME-Journal of Basic Engineering, 1960, 82: 35-45.

[19] MEHRA R K. Approaches to adaptive filtering[J]. IEEE Transactions on Automatic Control, 1972, 17(5): 693-698.

[20] LI Z, ZHANG H, ZHOU Q, et al. An adaptive low-cost INS/GNSS tightly-coupled integration architecture based on redundant measurement noise covariance estimation[J]. Sensors, 2017, 17(9): 2032.
