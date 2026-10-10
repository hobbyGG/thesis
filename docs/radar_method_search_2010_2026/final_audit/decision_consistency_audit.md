# 最终一致性审计：判定与证据

- 输入：`decisions_fulltext_audited_v2.jsonl`，1779 行、1779 个唯一 ID。
- 输出：`decisions_final.jsonl`，module=700、context=566、exclude=508、pending=5。
- 27 条原先标为 module、但理由明确写成综述/平台/背景/无独立算法的记录降为 context：R0127, R0136, R0163, R0223, R0235, R0238, R0253, R0331, R0550, R0556, R0829, R0970, R0973, R0982, R1048, R1165, R1297, R1303, R1321, R1354, R1357, R1396, R1480, R1519, R1525, R1582, R1588。
- 有具体升级证据但保留 module 的记录，其旧阶段理由写入 `original_reason`，最终理由改为以 `upgrade_source`、`upgrade_evidence_type` 和 `method/evidence` 为准。
- R1151、R1737 的本地全文支持具体方法链，保留为 module；性能边界继续写在 `transfer_limit`，不把峰峰值/几何融合指标当作 10 μm 动态波形精度。
- pending 仍只有 R1673、R1721、R1722、R1724、R1768；没有因题名猜测升级。
- v2 文件保留作为历史审阅快照；本 `final` 文件是方法库当前采用的保守口径。
