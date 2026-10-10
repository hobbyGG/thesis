# 本地 PDF 逐篇方法描述审计（2026-10-08）

本表对应 `ref_papers/radar_method_modules/README.md` 的完整本地 PDF 索引。每个 PDF 路径都有一行具体的雷达方法描述；描述按 `模块标签 → 归属判断 → 方法用途` 写入 README，并在机器可读表中保留全文状态和证据定位。

| 项目 | 数量 | 口径 |
|---|---:|---|
| PDF 路径 | 114 | 递归扫描 `ref_papers/radar_method_modules/` |
| README 方法行 | 114 | 与 PDF 路径一一对应，无缺失、无悬空、无重复路径 |
| 机器可读方法行 | 114 | [`local_pdf_method_rows.jsonl`](local_pdf_method_rows.jsonl) |
| 逐篇具体方法 | 114 | 已消除“按所属目录归入/打开原文核对”占位描述 |
| 可提取本地正文逐篇核对 | 87 | 前端、阵列、全场、GBSAR、融合和校准目录；含页码/章节定位 |
| 网络补充全文 | 15 | `_web_supplements/`，含方法论文与 GBIR 综述索引 |
| 优先全文记录 | 12 | `_web_priority_fulltext/`；扫描版或外部作者稿明确标注证据边界 |

来源归属使用 `R/T/G/A`：雷达原生、跨雷达迁移、通用算法迁移、场景胶水/应用适配。综述或技术应用报告也保留在文件索引中，但用途明确标成“索引/导航”或“技术报告”，不把它们冒充新的单一算法。

本审计只保证“本地文件逐篇有可追溯方法描述”。它不等于 1,779 条候选全部取得本地全文；候选池的最终证据计数仍以 [`decisions_final.jsonl`](decisions_final.jsonl) 和 [`decision_consistency_audit.md`](decision_consistency_audit.md) 为准。
