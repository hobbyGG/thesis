# 2010 年以后雷达方法文献检索审计

这份目录记录本轮实际执行的 OpenAlex 检索，不把人工挑选的论文列表冒充筛选结果。检索时间范围是 2010-01-01 至 2026-12-31（检索于 2026-10-08；按出版年份覆盖 2010–2026），文献类型限定为 `article`。完整查询记录见 `search_log.json`，去重后的首轮导出见 `raw_openalex_records.jsonl`；关键文件的 SHA-256 在 `SHA256SUMS.txt`。

收集层级、方法来源口径和未完成项目集中列在 [collection_manifest.md](collection_manifest.md)。

## 目前得到的数量

本轮使用 14 个宽检索词，OpenAlex 返回的各查询命中数之和为 **24,584**。这是各查询命中数的和，包含大量交集，不能直接当作论文数。每个查询最多导出前 200 条相关结果；按 DOI（没有 DOI 时按 OpenAlex work ID）去重后，实际保存了 **1,663 条候选记录**。

对这 1,663 条记录做了题名/摘要的机器辅助首轮筛选：

| 类别 | 数量 | 判定含义 |
|---|---:|---|
| A：直接相关 | 704 | 雷达与结构、桥梁、位移、振动、变形或结构监测语境同时出现，且未被明显生物医学/汽车感知语境主导 |
| B：可迁移方法 | 92 | 雷达方法模块（IQ、相位、解缠、FMCW、MIMO、波束形成、微位移等）可能迁移到结构振动，但题名未直接指向桥梁/结构 |
| C：排除或边界 | 867 | 生理雷达、汽车感知、通信、遥感地学、材料检测或题名/摘要不足以支持本课题迁移 |

A/B 是**首轮筛选**，不是最终纳入数；A 类仍需逐条读摘要/全文，B 类需要判断方法是否真的提供可迁移的复数相位、距离、角度或融合模块。对应记录分别在 `screened_A_direct.jsonl`、`screened_B_transferable.jsonl` 和 `excluded_C.jsonl`。

同时做了一轮更窄的结构/融合检索作为交叉核验：8 个聚焦检索式各取前 100 条，解析 538 条结果，按题名合并为 534 条；题名同时出现结构/桥梁/振动/位移与雷达相关词的有 207 条，排除明显卫星 InSAR、GPR、人体、通信、地质和材料检测等边界项后剩 180 条粗筛候选。该独立结果保存在 `focused_pass_8queries.md` 和 `focused_pass_candidates.jsonl`，仍然不是最终全文纳入数。

## 与原来的 40 条是什么关系

`ref_papers/radar_method_modules/README.md` 中的 40 条只是此前人工补充的第一批模块记录；该 README 后来又补录了 1 条与 R1722 相关的在线摘要行，但它不改变原始 40 条统计。人工表没有保存原始检索结果、检索式和逐条排除原因，因此不能称为“筛选后 40 篇”。本次检索证明 2010 年以后候选远大于 40：仅宽检索去重后就有 1,663 条首轮候选。

此外，Sotoudeh 等人在 2025 年 GBIR 桥梁监测系统综述中给出了可复核的筛选链：Scopus 初始召回 **220 条**，数据库/学科/文献类型/语言筛选后保留 75 篇，再由 Web of Science/Google Scholar 补充 23 篇，并保留 6 篇高相关会议、Letters 或 Workshop 文献，最终数据集 **104 篇**；其中 63 篇还研究了 GBIR 与其他系统的组合。这个单一子领域的已发表筛选集已经超过 40，因此 40 条只能作为模块地图的第一批，不能作为 2010+ 全量筛选结果。见 [Remote Sensing 2025, 17, 1541](https://doi.org/10.3390/rs17091541)。

目前还整理了 63 条经 Crossref/出版社入口逐条核过的 2010+ 雷达候选，其中 61 条属于 2010+、2 条是早期基线；它们按直接结构测量（D）、可迁移雷达模块（T）和背景/边界（B）分类，见 `crossref_curated_63.md`。这份清单是高相关候选集，不声称覆盖全部检索结果。

## 阶段性逐条审阅

为了把“候选记录”和“方法模块”分开，已将 1,779 条去重联合候选拆成三个各 593 条的审阅包。历史摘要阶段曾生成唯一决策行：`module` 659 条、`context` 524 条、`exclude` 503 条、`pending` 93 条；这些文件保留作为过程快照。当前最终一致性审计已更新为：`module` 700 条、`context` 566 条、`exclude` 508 条、`pending` 5 条；最终逐条方法卡片索引见 `review_2026_10_08/MODULE_INDEX_FINAL.md`，机器可读决策见 `review_2026_10_08/decisions_final.jsonl`。

这是摘要阶段过程快照；后续全文补证据、版本去重和判定一致性已写入最终审计文件。当前仍有 5 条 `pending` 因缺少可核实算法证据而保留，不能据题名猜测方法。

为便于进入全文阶段，`priority_fulltext/README.md` 给出了 659 条 `module` 记录的工作队列，按结构直接相关性、雷达–加速度融合、相位/解缠、阵列和质量评估等关键词排序；`priority_candidates.jsonl` 保留了每条记录的排序分数和标签。排序只用于安排阅读顺序，不代表论文质量或最终纳入结论。结构直接相关论文和可迁移模块的首批全文核验分别见 `priority_fulltext/structural_direct.md` 与 `priority_fulltext/transferable_modules.md`。

首批全文核验后建议升级的 13 条记录见 `priority_fulltext/fulltext_upgrade_recommendations.jsonl`；补充证据原表见 `priority_fulltext/pending_upgrade_evidence.md`。应用这 13 条升级后生成了单独的 [MODULE_INDEX_FULLTEXT_UPGRADED.md](review_2026_10_08/MODULE_INDEX_FULLTEXT_UPGRADED.md)：module=672、context=523、exclude=503、pending=81。它与原始 `decisions_merged.jsonl` 分开保存，仍不是最终全文终稿。

## 最新逐条审计结果

对 1,779 条联合候选完成了三批 `pending` 逐条证据审计，并对最后两个能够取得公开全文的条目补证据。历史全文审计快照见 [MODULE_INDEX_FULLTEXT_AUDITED_V2.md](review_2026_10_08/MODULE_INDEX_FULLTEXT_AUDITED_V2.md)；随后又做了判定与证据一致性审计，当前采用 [最终索引](review_2026_10_08/MODULE_INDEX_FINAL.md) 和 [最终机器可读决策](review_2026_10_08/decisions_final.jsonl)：

| 判定 | 数量 | 口径 |
|---|---:|---|
| module | **700** | 有证据能够写出输入→处理→输出的可复用方法模块；最终一致性审计已排除仅综述/平台/案例背景的记录 |
| context | **566** | 雷达结构应用、综述或实验背景有价值，但不足以单独抽成模块 |
| exclude | **508** | 主题边界、重复或与本课题不相关 |
| pending | **5** | 仍只有题名/元数据，不能据题名猜算法 |

新增核实的两条是：R1691 的 5–6 GHz SFCW 地基雷达桥梁振动链（iFFT、相邻脉冲相位差、时间相干性、boxcar 与经验匹配滤波），以及 R1727 的 Sentinel-1 MT-DInSAR 桥梁异常检测链（LOS 分区、升降轨几何、温度回归、残差和 Hotelling T²）。最后 5 条仍 pending：R1673、R1721、R1722、R1724、R1768；逐条原因和检索状态见 [remaining_pending_resolution.jsonl](final_audit/remaining_pending_resolution.jsonl)。

这意味着“候选池审计已做到当前可取得证据的范围”，不意味着对全世界 2010+ 雷达论文做完全文穷尽。下一阶段是在当前 700 条方法卡基础上按 M01–M20 和 R/T/G/A 来源分层，再选 20–40 篇核心论文做创新性查重。最终一致性变更、27 条降为 context 的记录和旧快照之间的差异见 [`final_audit/decision_consistency_audit.md`](final_audit/decision_consistency_audit.md)。

## 当前限制

- OpenAlex 的宽检索结果每个查询只导出前 200 条，因此 24,584 是命中数总和，1,663 是“导出的首轮候选”，不是全库唯一总量。
- A/B 分类是可重复的机器辅助初筛，尚未替代人工全文筛选。
- 下一步应以 A 类、B 类和 GBIR 综述的参考文献为主建立逐条台账，补充 `纳入/排除理由、全文状态、方法模块、证据页码`，再给出最终纳入数量。
