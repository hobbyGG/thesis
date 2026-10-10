# 最终 pending 审计与补证据

本目录保存 2010+ 联合候选池中原先 93 条 pending 的最后三批审计，以及最后对剩余 7 条的补证据结果。

- `pending_01.jsonl`、`pending_02.jsonl`、`pending_03.jsonl` 覆盖原先 81 条 pending，合计升级为 53 条 module、16 条 context、5 条 exclude、7 条仍 pending。
- `remaining_pending_resolution.jsonl` 记录最后 7 条：R1691（地基雷达桥梁振动）和 R1727（InSAR 桥梁异常检测）取得公开全文，升级为 module；R1673、R1721、R1722、R1724、R1768 仍因没有可核实算法证据而保留 pending。
- `web_fulltext/` 保存 R1691 作者机构稿和抽取文本；R1727 的公开会议全文保存于 `ref_papers/radar_method_modules/_web_supplements/`，并保留本地方法库入口。

因此历史审计索引 [MODULE_INDEX_FULLTEXT_AUDITED_V2.md](../review_2026_10_08/MODULE_INDEX_FULLTEXT_AUDITED_V2.md) 的计数为 **727 module、539 context、508 exclude、5 pending**。最终一致性审计随后将仅综述/平台/案例背景的 27 条记录降为 context，当前采用 [MODULE_INDEX_FINAL.md](../review_2026_10_08/MODULE_INDEX_FINAL.md)：**700 module、566 context、508 exclude、5 pending**。这表示候选池审计已完成到可取得证据的范围，不表示全世界 2010+ 雷达论文已完成全文穷尽。
