# 旧版本归档：2026-09-14 Direct-AoA

本目录保存切换到当前 Direct-AoA 主线之前的文档、实验产物、汇报幻灯片和历史图表。归档内容未删除，可按 manifest.json 中的原始路径和 SHA-256 校验恢复。

## 当前保留在工作区的兼容代码

simulation/phase1/beta_calibration.py、beta_bootstrap_diagnostics.py 等模块仍保留在原位置，因为显式 legacy/ablation 方法、报告生成器和回归测试仍会导入它们。它们不是当前默认主线；删除或移动需要同步修改方法注册、报告生成器和测试。

这部分代码的“归档”通过当前入口和本说明完成：默认入口不会调用它们，只有显式选择 legacy 方法时才使用。为避免把可复现的历史实现变成断裂的导入路径，本次没有复制一份容易造成版本混淆的代码副本。

## 归档范围

- legacy_docs/：旧 β 主线架构、旧 Phase 1 报告和历史 implementation plans。
- legacy_evidence_docs/：2026-09-08 预实验交接和磁浮历史复核文档。
- legacy_outputs/：旧报告验证输出、旧 extended 输出、旧单次 multifrequency/场景诊断输出、磁浮历史采集包及 fixed/adaptive 比较产物。
- legacy_presentations/：thesis_progress_v1* 历史汇报及 inspect 文件。
- legacy_assets/：旧 beta-bootstrap 和 adaptive-R 图表。

docs/data_processing_flow_2026-09-14.md 是当前数据流程入口；当前默认采集算法为 direct_aoa_fixed_beta。
