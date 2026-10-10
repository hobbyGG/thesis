# 2010+ 雷达结构振动文献聚焦检索：8 条 OpenAlex 查询的独立粗筛

更新时间：2026-10-08（Asia/Shanghai）。

## 这份记录回答什么问题

这是一次独立的聚焦检索，用于检验“2010 年以后雷达—结构振动/位移/加速度融合文献是否只有几十篇”。结果表明原始召回达到数百至数千量级，40 条不能作为筛选前数量。本文档只记录检索和题名级粗筛，**不把 180 条视为最终全文纳入文献**。最终纳入仍需逐条检查摘要、全文、发表类型、DOI 重复和与毫米波/GBIR/结构振动的实际相关性。

## 检索参数

- 数据源：OpenAlex Works API（`https://api.openalex.org/works`）。
- 时间过滤：`from_publication_date:2010-01-01,to_publication_date:2026-10-08`。
- 每个查询取前 100 条（`per-page=100`），记录 API 返回的 `meta.count` 作为该查询的原始命中量。
- 8 个查询之间有大量重叠；原始命中量不能相加当作唯一论文数。
- 本轮抓取行数：538（来自 8×100 结果，扣除标题格式无法解析的 4 行）；按题名大小写合并后 534 个唯一题名。

| # | 查询式 | OpenAlex 原始命中量 | 本轮抓取上限 |
|---:|---|---:|---:|
| 1 | `millimeter wave radar bridge displacement` | 1,779 | 100 |
| 2 | `FMCW radar structural vibration displacement` | 339 | 100 |
| 3 | `ground based radar bridge interferometry` | 4,282 | 100 |
| 4 | `radar accelerometer displacement fusion bridge` | 973 | 100 |
| 5 | `radar vibration measurement structural health monitoring` | 7,828 | 100 |
| 6 | `millimeter wave radar bridge vibration` | 1,667 | 100 |
| 7 | `interferometric radar bridge dynamic monitoring` | 3,254 | 100 |
| 8 | `radar displacement accelerometer structure` | 4,661 | 100 |

## 题名级粗筛规则与结果

在 534 个题名中，先要求题名同时命中两组词：

1. 结构对象/响应词：`bridge`, `railway/rail`, `structure`, `tower`, `building`, `pipeline`, `cable`, `infrastructure`, `vibration`, `displacement`, `vibromet`, `modal`, `viaduct`。
2. 雷达词：`radar`, `microwave`, `mmwave`, `millimeter`, `FMCW`, `interfer`。

得到 207 条题名级结构雷达候选。再按题名明显排除卫星 InSAR/GPR、通信/天线、人体生命体征、海洋/地质/地震、植物/材料缺陷等 27 条，保留 180 条“候选题名”。这个排除只根据题名，可能漏掉边界论文，不能替代全文筛选。

| 阶段 | 数量 | 说明 |
|---|---:|---|
| 8 条查询的 API 原始命中（各自计数，不能求和） | 1,779 / 339 / 4,282 / 973 / 7,828 / 1,667 / 3,254 / 4,661 | 有查询重叠 |
| 抓取结果行 | 538 | 8×100，去掉 4 条无法解析的标题行 |
| 题名去重后 | 534 | 仅按题名大小写合并，尚未 DOI 去重 |
| 结构词 + 雷达词题名粗筛 | 207 | 题名级宽口径 |
| 明显无关题名排除 | 27 | 卫星/GPR/通信/人体等题名规则 |
| 粗筛候选 | 180 | 待摘要、全文、DOI 和文献类型筛选 |

## 粗筛候选的题名场景分层（仍非最终纳入）

在180条候选中，按题名做一个便于后续人工复核的场景分层：93条含 `bridge/rail/viaduct`，43条含 `tower/building/pipeline/cable/infrastructure/structure` 但没有桥梁/铁路词，44条只有通用 `vibration/displacement/vibrometry` 雷达词。该分层只用于安排全文复核，不能当作相关性最终判定。

| 题名场景 | 数量 | 含义 |
|---|---:|---|
| 桥梁/铁路/高架桥 | 93 | 直接优先复核 |
| 其他结构（塔、楼、管线、索、基础设施等） | 43 | 跨场景方法迁移候选 |
| 未指明结构的通用雷达振动/位移 | 44 | 方法模块候选，需查实验对象 |

## 粗筛候选的年份分布

| 年份 | 候选题名数 | 年份 | 候选题名数 |
|---:|---:|---:|---:|
| 2010 | 4 | 2011 | 3 |
| 2012 | 3 | 2013 | 11 |
| 2014 | 9 | 2015 | 7 |
| 2016 | 7 | 2017 | 6 |
| 2018 | 11 | 2019 | 14 |
| 2020 | 16 | 2021 | 14 |
| 2022 | 11 | 2023 | 18 |
| 2024 | 14 | 2025 | 20 |
| 2026 | 12 |  |  |

## JSONL 附件

`focused_pass_candidates.jsonl` 包含 180 条题名级粗筛候选，每行记录 `year`, `title`, `doi`, `source_query/source_queries`, `coarse_screen`, `screen_scope` 和 `source`。DOI 为空表示 OpenAlex 该条记录没有 DOI 字段；并不表示论文不存在 DOI。

## 限制

- 这是检索式和题名级粗筛审计，不是 PRISMA 意义上的最终系统综述。
- OpenAlex `meta.count` 会随索引更新而变化；本文件保存的是本次运行的返回值。
- 每式只抓前 100 条，因此 534 个唯一题名不是整个 OpenAlex 结果集的唯一总数，而是本次可复核的聚焦抽样池。
- 180 条中还含会议论文、综述、跨场景结构雷达和可能重复 DOI；必须继续做摘要/全文筛选后才能得到正式纳入数。
