from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioDescription:
    label_zh: str
    validation_purpose_zh: str
    validation_focus_zh: str
    paper_section_zh: str


_SCENARIO_DESCRIPTIONS = {
    "measured_bridge_point4_transverse": ScenarioDescription(
        label_zh="实测桥梁位移驱动",
        validation_purpose_zh="验证算法在真实桥梁单点非平稳位移波形上的可用性",
        validation_focus_zh="半实测波形、真实车辆响应形态、雷达相位合成",
        paper_section_zh="主实验",
    ),
    "literature_maglev_modal_response": ScenarioDescription(
        label_zh="文献主频驱动磁浮轨道梁响应",
        validation_purpose_zh="基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真",
        validation_focus_zh="文献主频、车辆事件包络、频谱泄漏、半实测替代场景",
        paper_section_zh="主实验",
    ),
    "strong_wrapping": ScenarioDescription(
        label_zh="强相位缠绕",
        validation_purpose_zh="验证预测辅助相位校正能否处理毫米级大振幅导致的多次相位缠绕",
        validation_focus_zh="强缠绕、解缠失败风险、Kalman 预测辅助校正",
        paper_section_zh="主实验",
    ),
    "aoa_error_bootstrap": ScenarioDescription(
        label_zh="FFT AoA 初值误差与 beta 预校准",
        validation_purpose_zh="验证 angle FFT 前端 AoA 量化/分辨率误差存在时，独立 beta 预校准能否安全修正或回退",
        validation_focus_zh="FFT 前端 AoA 初值误差、beta 独立预校准、冻结参数多目标融合",
        paper_section_zh="消融实验",
    ),
    "target_snr_drop": ScenarioDescription(
        label_zh="目标 SNR 退化",
        validation_purpose_zh="验证 confidence-aware target-wise R 能否降低退化目标对融合状态的污染",
        validation_focus_zh="SNR 下降、目标级有效 R、坏目标降权",
        paper_section_zh="主实验",
    ),
    "mixed_scatterer_rangebin": ScenarioDescription(
        label_zh="同 rangeBin 复合散射",
        validation_purpose_zh="验证同一距离单元内复合散射造成相位畸变时，前端筛选与 confidence-aware R 的鲁棒性",
        validation_focus_zh="复合散射、混合相位、目标质量退化",
        paper_section_zh="鲁棒性附录",
    ),
    "same_range_far_angles": ScenarioDescription(
        label_zh="同 rangeBin 远角度多目标",
        validation_purpose_zh="验证 angle-bin 分离能解决同距离单元内不同角度目标被 range-bin 方法混合的问题",
        validation_focus_zh="同 rangeBin、多角度分离、Ma-style range-bin baseline 对比",
        paper_section_zh="主实验",
    ),
    "literature_mmwbats_same_range_aliasing": ScenarioDescription(
        label_zh="mmWBat 同 rangeBin 角度混叠复刻",
        validation_purpose_zh="复刻 mmWBat/mmSHM 中两个目标位于同一 rangeBin、依靠第二次 Angle FFT 分离的机制场景",
        validation_focus_zh="同 rangeBin、约一个角分辨单元、range-angle component 相位提取",
        paper_section_zh="文献机制复刻/附录",
    ),
    "literature_mmshm_adjacent_range_clutter": ScenarioDescription(
        label_zh="mmSHM 相邻 rangeBin 干扰复刻",
        validation_purpose_zh="复刻 mmSHM 中相邻距离单元目标互扰、需要 range-angle 联合定位后提取相位的机制场景",
        validation_focus_zh="相邻 rangeBin、角度分离、clutter/coupling 机制",
        paper_section_zh="文献机制复刻/附录",
    ),
    "low_snr_multitarget": ScenarioDescription(
        label_zh="低 SNR 多目标",
        validation_purpose_zh="验证低信噪比条件下多目标融合与目标筛选是否仍能保持可用精度",
        validation_focus_zh="低 SNR、多目标融合、SNR sensitivity",
        paper_section_zh="敏感性/附录",
    ),
}


def describe_scenario(scenario_name):
    return _SCENARIO_DESCRIPTIONS.get(
        str(scenario_name),
        ScenarioDescription(
            label_zh=str(scenario_name),
            validation_purpose_zh="未登记的仿真场景",
            validation_focus_zh="未登记",
            paper_section_zh="未分类",
        ),
    )


def scenario_metadata_fields(scenario_name):
    description = describe_scenario(scenario_name)
    return {
        "scenario_label_zh": description.label_zh,
        "validation_purpose_zh": description.validation_purpose_zh,
        "validation_focus_zh": description.validation_focus_zh,
        "paper_section_zh": description.paper_section_zh,
    }
