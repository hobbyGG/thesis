# 列车稀疏事件、轨道梁响应与自由衰减

本目录收集与本文“长时间静止—列车通过—短时响应—模态余振”数据形态直接相关的
文献。它用于论文中说明磁浮轨道梁的列车通过响应、稀疏事件和自由衰减背景，不是雷达相位算法模块库。
文献全文和入口分开记录：能合法取得的公开全文保存在本目录；只有出版社/机构入口的
论文保存为 Markdown 记录，避免把未取得的全文误写成本地证据。

## 本地全文

| 文件 | 文献 | 对本文的用处 |
|---|---|---|
| [`Kaito_2010_Vibration_monitoring_for_railway_bridges_using_passing_train_load.pdf`](Kaito_2010_Vibration_monitoring_for_railway_bridges_using_passing_train_load.pdf) | Kaito et al., *Vibration Monitoring for Railway Bridges Using Passing Train Load*, JSCE 2010, DOI [10.2208/jscejf.66.382](https://doi.org/10.2208/jscejf.66.382) | 证明列车重量近似、通过时刻固定的铁路桥可以按事件重复监测；支持每次响应单独建基线和跨事件比较。论文是日文，但 J-STAGE 提供免费全文：[文章页](https://www.jstage.jst.go.jp/article/jscejf/66/3/66_3_382/_article/-char/en)。 |
| [`Han_2024_Research_on_Environmental_Vibration_Induced_by_High-Speed_Maglev_Transportation.pdf`](Han_2024_Research_on_Environmental_Vibration_Induced_by_High-Speed_Maglev_Transportation.pdf) | Han, Zeng & Ye, *Research on Environmental Vibration Induced by High-Speed Maglev Transportation*, Applied Sciences 2024, 14, 413, DOI [10.3390/app14010413](https://doi.org/10.3390/app14010413) | 现场磁浮导梁测点的持续时间和自由衰减段比柱/地面更长，并存在相邻跨叠加和干涉；文中用 1 s RMS 表征响应持续性。支持事件合并、避免把模态过零误切成多个事件，以及不能用过短的固定上限截断余振。 |
| [`Montenegro_2024_InBridge4EU_Damping_Assessment_preprint.pdf`](Montenegro_2024_InBridge4EU_Damping_Assessment_preprint.pdf) | Montenegro et al., *Damping Assessment on Railway Bridges Based on an Extensive Experimental Database Framed on the InBridge4EU Project*, 2024 conference/preprint | 大规模列车激励记录的阻尼与自由衰减处理依据。与 2026 年正式论文配套使用，提供公开可下载的项目版本。 |
| [`A03_Dynamic_Response_Analysis_of_High-Speed_Maglev-Guideway_System.pdf`](../02_recent_uncollected/A03_Dynamic_Response_Analysis_of_High-Speed_Maglev-Guideway_System.pdf) | *Dynamic Response Analysis of High-Speed Maglev-Guideway System*, 2023, DOI [10.1007/s42417-023-00995-5](https://doi.org/10.1007/s42417-023-00995-5) | 本项目已有的磁浮导梁动力学全文。文中给出约 9.3/12.5 Hz 的低阶频率和约 2.67%/3.51% 阻尼；按指数衰减估算，40 dB 幅值衰减约需 2.95/1.67 s，为当前 3 s 事件上限提供数量级依据。 |

## 入口记录（全文未复制）

| 文件 | 文献 | 相关结论 |
|---|---|---|
| [`Bono_2025_Automated_Operational_Modal_Analysis_free_decay.md`](Bono_2025_Automated_Operational_Modal_Analysis_free_decay.md) | Bono et al., *Automated Operational Modal Analysis of a steel truss railway bridge employing free decay response*, Journal of Infrastructure Intelligence and Resilience 2025, 100145, DOI [10.1016/j.iintel.2025.100145](https://doi.org/10.1016/j.iintel.2025.100145) | 将列车离桥后的自由衰减作为 OMA 输入；自由衰减的模态信号比环境噪声更干净，可在更短窗口、较低性能传感器下识别更多模态。支持事件结束后保留响应段并单独分析，而不是把长静止段混进拟合。机构开放入口：[Politecnico repository PDF](https://re.public.polimi.it/bitstream/11311/1287059/2/1-s2.0-S2772991525000088-main.pdf)。 |
| [`Montenegro_2026_InBridge4EU_final_article.md`](Montenegro_2026_InBridge4EU_final_article.md) | Montenegro et al., *Towards improved normative definitions of damping in railway bridges: Insights from the InBridge4EU European experimental database*, Engineering Structures 2026, 359, 122666, DOI [10.1016/j.engstruct.2026.122666](https://doi.org/10.1016/j.engstruct.2026.122666) | 1150 条列车激励记录、近 90 座桥的数据库。公开摘要和项目材料说明其事件/自由衰减处理使用滚动 RMS、sigma 判据，并可用 40 dB RMS 衰减或 10 个基频周期作为衰减终止参考。出版社页面可访问摘要，全文入口受出版社下载策略限制。 |

## 对论文事件建模的参考

逐条对照文献后，论文中的事件建模参考如下：

1. 磁浮导梁响应存在自由衰减、相邻跨叠加和干涉，事件分析应保留响应余振，避免把模态过零
   或短噪声谷值误判为多个事件。
2. 静止基线、滞回阈值和连续确认适合用于区分列车通过响应与背景噪声；具体阈值必须根据
   500 Hz 采样下的实测数据重新标定。
3. 事件长度应覆盖列车离桥后的自由衰减段。A03 的低阶频率和阻尼给出的 40 dB 衰减时间
   约为 1.67–2.95 s，Bono 的自由衰减 OMA 也要求保留离桥后的余振段。
4. 列车重复通过可以使用事件前静止段建立基线，并在事件后单独分析余振；这些处理属于
   论文实验设计，不属于当前实时主算法代码。

## 来源和证据边界

- 磁浮现场响应、导梁自由衰减和相邻跨干涉：Han 2024。
- 列车重复事件与固定通过时刻：Kaito 2010。
- 列车离桥后的自由衰减用于模态识别：Bono 2025。
- 大样本铁路桥列车激励与阻尼统计：Montenegro/InBridge4EU 2024/2026。
- 本项目具体阈值（6/3 MAD、80 ms、0.50 s、3 s、5%）仍是针对 500 Hz、0.8 s 仿真事件
  的工程参数，不能写成上述论文原样采用的参数。
