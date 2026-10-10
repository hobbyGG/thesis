# 雷达方法库收集清单

更新时间：2026-10-08。这里定义当前方法库已经收集到什么程度，以及哪些工作仍未完成；“全部”指方法族覆盖和每条记录可追溯，而不是宣称检索了全世界所有雷达论文。

## 已完成的收集层

| 层 | 当前结果 | 证据文件 |
|---|---|---|
| 宽检索召回 | 14 个 OpenAlex 查询，命中数合计 24,584；每式导出前 200 条，去重后 1,663 条 | `search_log.json`、`raw_openalex_records.jsonl` |
| 聚焦结构检索 | 538 条解析结果，题名合并后 534 条，明显边界排除后 180 条粗筛候选 | `focused_pass_8queries.md`、`focused_pass_candidates.jsonl` |
| 联合候选池 | 宽检索、聚焦检索、Crossref 清单和人工扩展去重后 1,779 条 | `review_2026_10_08/union_candidates.jsonl` |
| 最终方法判定 | **700 module、566 context、508 exclude、5 pending**；历史摘要阶段 659/524/503/93 保留作快照 | `review_2026_10_08/review_counts_final.json`、`final_audit/decision_consistency_audit.md` |
| 模块分类 | M01–M20 全部已有记录，覆盖距离、Doppler、IQ、相位、解缠、多弧、杂波、多目标、阵列、几何、模态、分解、跟踪、融合和不确定度 | `ref_papers/radar_method_modules/README.md`、`MODULE_INDEX.md` |
| 来源矩阵 | 659 条 module、1,287 个论文–模块归属，按结构雷达、其他雷达迁移、通用算法和场景胶水拆分 | `module_provenance_matrix.md` |
| 本地全文库 | 114 个 PDF 条目，按内容去重 109 篇；包含 15 个网络补充全文和 12 个优先全文硬链接；README 已逐篇写入具体方法 | `ref_papers/radar_method_modules/README.md`、`final_audit/local_pdf_method_audit.md` |
| 重点全文核验 | 22 张结构直接证据卡、25 张可迁移模块卡、雷达–加速度融合证据卡 | `priority_fulltext/structural_direct.md`、`transferable_modules.md`、`radar_accel_fusion.md` |
| 机制级归并 | 64 张机制卡：IQ/相位 21、距离/波形/阵列 25、融合/质量/模态 18；按机制合并多篇论文并记录迁移边界 | `ref_papers/radar_method_modules/catalog/README.md`、`iq_phase.md`、`array_range.md`、`fusion_quality_modal.md` |
| pending 补证据 | 首批 13 条高价值 pending 加上三批 81 条 pending 审计，并对最后 7 条逐一复核；R1691、R1727 取得公开全文，最终剩 5 条 pending；随后完成判定一致性审计 | `final_audit/README.md`、`final_audit/pending_01.jsonl`、`pending_02.jsonl`、`pending_03.jsonl`、`remaining_pending_resolution.jsonl`、`final_audit/decision_consistency_audit.md` |

## 方法来源口径

- **R：雷达原生**：FMCW beat/range、slow-time Doppler、CFAR、MIMO 虚拟阵列、波束形成等。
- **T：跨雷达迁移**：CW/微波/GBSAR/QFG 中的 IQ 圆拟合、椭圆校准、DACM、多弧、相位解缠等，迁移到 IWR 的 range-bin 复数慢时间。
- **G：通用算法迁移**：最小二乘、MLE、KF/EKF/FIR、STFT、EMD/VMD、MUSIC、SOBI、DBSCAN 等。
- **A：场景胶水**：把多目标、多视线、雷达和 ADXL355 观测统一成结构位移状态，并处理质量门控、遮挡和失锁恢复。

基础模块不自动等于论文创新。是否“新”必须继续检查论文的相关工作、引用链、观测方程和触发/切换规则。

## 最终审计快照

| 判定 | 数量 | 说明 |
|---|---:|---|
| module | **700** | 摘要、公开记录或全文支持可复用方法模块；最终一致性审计排除了仅综述/平台/案例背景 |
| context | **566** | 有关但不足以单列模块 |
| exclude | **508** | 排除或边界记录 |
| pending | **5** | R1673、R1721、R1722、R1724、R1768，当前仍无可核实算法证据 |

该快照由 `decisions_final.jsonl` 和 `review_counts_final.json` 生成；历史 `decisions_fulltext_audited_v2.jsonl` 的 727/539/508/5 口径仍保留作可追溯快照。它是联合候选池在当前证据边界内的审计终点，不是全球文献穷尽声明。

## 尚未完成的项目

1. 5 条 `pending` 仍缺可核实算法证据，不能计入 `module`；其余原 93 条已完成摘要/公开记录/全文审计。
2. 700 条 `module` 的证据等级不同，只有一部分补齐了本地全文页码；不能把摘要证据等同于逐篇全文精读。历史 727/539 快照仍保留在 `MODULE_INDEX_FULLTEXT_AUDITED_V2.md`，最终 700/566 口径及 27 条降级原因见 `final_audit/decision_consistency_audit.md`。
3. 跨论文的 DOI、版本和重复关系已经部分处理，但仍需完成统一 DOI/题名去重审计。
4. 还需要在全文证据基础上选出面向 IWR+ADXL355 的最终 20–40 篇核心论文，再讨论毕业论文的三项创新。

因此当前方法库已经完成“广泛收集 + 模块化整理 + 候选池逐条证据审计”；尚未完成“700 条全部全文精读 + 创新性查重 + 面向 IWR+ADXL355 的 20–40 篇核心论文定稿”。
