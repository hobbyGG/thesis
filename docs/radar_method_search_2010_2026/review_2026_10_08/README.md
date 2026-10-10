# 2010+ 雷达候选逐条审阅包

本目录是对检索候选进行人工/摘要证据筛选的工作区。`union_candidates.jsonl` 是合并后的候选池；`packet_1.jsonl`–`packet_3.jsonl` 将其按稳定的 `R` 编号分成三个包，每包 593 条。

每条输入必须在对应 `decisions_N.jsonl` 中有且仅有一条结果，字段如下：

`id`, `decision`, `reason`, `evidence_level`, `modules`, `method`, `transfer_limit`, `evidence`。

`decision` 取值：

- `module`：题名/摘要/全文已经给出可复用的雷达处理方法；
- `context`：雷达结构应用、综述或实验背景有价值，但没有足够证据认定为独立方法模块；
- `exclude`：非雷达、纯通信/器件、与位移/振动/可迁移处理无关，或重复且无新增内容；
- `pending`：题名提示可能相关，但当前证据不足，必须补全文或出版社页面。

模块编号沿用雷达方法库 README 的 M01–M20。仅凭题名不能确定算法；没有摘要/全文证据时应使用 `pending`，不得把推测写成方法事实。

完成后用脚本校验：输入与输出 ID 一一对应、无重复 ID、decision 合法、每个 `module` 至少有一个 M 编号，最后再按 DOI 合并并更新主 README。


## 最新审计快照

`decisions_fulltext_audited_v2.jsonl` 是历史全文审计快照，覆盖 1,779 条候选，统计为 `module=727`、`context=539`、`exclude=508`、`pending=5`。最终一致性审计将 27 条仅综述/平台/案例背景降为 context；当前逐论文方法索引为 [`MODULE_INDEX_FINAL.md`](MODULE_INDEX_FINAL.md)，机器可读决策为 [`decisions_final.jsonl`](decisions_final.jsonl)，统计文件为 [`review_counts_final.json`](review_counts_final.json)，口径为 `module=700`、`context=566`、`exclude=508`、`pending=5`。变更说明见 [`decision_consistency_audit.md`](../final_audit/decision_consistency_audit.md)。
