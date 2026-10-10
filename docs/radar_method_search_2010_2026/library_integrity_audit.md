# 雷达方法库完整性审计（2026-10-08）

## 审计范围

审计对象为 `ref_papers/radar_method_modules/` 下的 PDF（含 `_web_supplements/` 与 `_web_priority_fulltext/`）、其 `README.md` 本地 PDF 索引，以及 `docs/radar_method_search_2010_2026/review_2026_10_08/MODULE_INDEX.md` 与 `local_fulltext_evidence.md`。本轮补充全文采用硬链接汇总，不重复占用内容。

## 文件与内容哈希

- 实际 PDF 文件条目：**114**（递归扫描全部子目录、`_web_supplements/` 和 `_web_priority_fulltext/`）。
- SHA-256 唯一内容数：**109**。
- 因而重复内容组为 **5 组**，每组 2 个路径；重复均为跨模块目录的硬链接/同内容复用，并非额外论文：
  - `04_aoa_beamforming_mimo/` ↔ `05_multi_target_full_field/`：`Multi-scale and full-field vibration measurement via millimetre-wave sensing.pdf`、`Full-field 3D displacement measurement via microwave sensing.pdf`、`Millimeter-Wave Bat for Mapping and Quantifying Micromotions in Full Field of View.pdf`。
  - `00_fmcw_phase_displacement/` ↔ `08_radar_calibration_tracking/`：`A Noncontact FMCW Radar Sensor for Displacement Measurement in Structural Health Monitoring.pdf`。
  - `00_fmcw_phase_displacement/` ↔ `01_cw_iq_interferometry/`：`Structural displacement measurements using DC coupled radar with active transponder.pdf`。

README 的统计口径（114 个文件条目、109 篇按内容去重）与实际扫描及 SHA-256 结果一致。README 的 114 行均已补齐具体方法描述；逐篇记录见 [`final_audit/local_pdf_method_audit.md`](final_audit/local_pdf_method_audit.md) 和 [`final_audit/local_pdf_method_rows.jsonl`](final_audit/local_pdf_method_rows.jsonl)。检索审计目录已生成 `docs/radar_method_search_2010_2026/SHA256SUMS.txt`；哈希文件需在本轮文档修改完成后重新生成。PDF 唯一数仍由当前 PDF 字节重新计算得到。

## README 本地 PDF 索引核对

按 README 中形如 ``| `path.pdf` |`` 的本地索引行解析：

- 索引行：**114**；索引路径唯一数：**114**。
- 实际 PDF 中未登记条目：**0**。
- README 登记但文件不存在：**0**。
- README 索引无重复路径；重复内容仅来自上述 5 组跨目录复用。

因此 README 本地索引覆盖当前所有 PDF 条目，且路径拼写与实际目录相符。

## MODULE_INDEX 与本地全文清单

- `review_2026_10_08/MODULE_INDEX_FINAL.md` 对应 1,779 条联合候选的最终口径：`module=700`、`context=566`、`exclude=508`、`pending=5`；历史 `MODULE_INDEX.md` 的 659/524/503/93 仅保留作摘要阶段快照。
- `local_fulltext_evidence.md` 当前列出 **14 条**方法或方法链的带页码/证据定位记录；README 统计中的 15 个 `_web_supplements` PDF 还包括 `sotoudeh2025_gbir_review.pdf`，该文件是 GBIR 综述索引，不作为单一算法方法卡；另有 12 个 `_web_priority_fulltext` PDF，它们对应优先全文审阅队列并已在 README 登记。15 个网络补充全文和 12 个优先全文的文件边界均完整，14 条早期方法证据记录只是其中的一个带页码子集。
- 本地全文证据清单是“首轮题名/摘要页证据”子集，不应与 114 个 PDF 文件索引一一对应；其 14 条记录均指向已存在的补充全文，未发现悬空路径。
- MODULE_INDEX 的 659 张卡片以检索候选（含 DOI/在线入口）为主，不能用卡片数反推本地 PDF 数；两套清单粒度不同，当前不存在可据此判定的缺失或重复卡片。

## 优先全文下载校验

- `priority_fulltext/pdfs/` 当前有 **12 个**可提取 PDF，均通过 PDF 签名和 `pdftotext` 首页校验；校验记录见 `priority_fulltext/final_audit/download_validation.jsonl`。
- 3 个错误下载（2 个 HTML 页面、1 个空文件）已移入 `priority_fulltext/rejected_downloads/`，不计入全文证据。

## 结论与后续核查点

当前方法库的文件边界和逐篇方法描述完整：114 个路径条目、109 个唯一 PDF 内容，README 索引全覆盖，5 组重复均符合跨模块复用说明；新增 12 个优先全文为唯一内容。历史全文审计索引的 727 条 `module` 卡片保留在 v2 快照；当前最终一致性审计索引的 700 条 `module` 计数与 `decisions_final.jsonl` 一致。机制级目录另有 64 张按方法归并的卡片。
