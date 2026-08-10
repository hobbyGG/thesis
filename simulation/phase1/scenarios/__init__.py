from . import (
    aoa_error_bootstrap,
    literature_maglev_modal_response,
    literature_mmshm_adjacent_range_clutter,
    literature_mmwbats_same_range_aliasing,
    low_snr_multitarget,
    mixed_scatterer_rangebin,
    measured_bridge_point4_transverse,
    same_range_far_angles,
    strong_wrapping,
    target_snr_drop,
)
from ..config import Phase1Config


_ALL_SYNTHETIC_BUILDERS = (
    literature_maglev_modal_response.build,
    strong_wrapping.build,
    aoa_error_bootstrap.build,
    target_snr_drop.build,
    same_range_far_angles.build,
    literature_mmwbats_same_range_aliasing.build,
    literature_mmshm_adjacent_range_clutter.build,
    mixed_scatterer_rangebin.build,
    low_snr_multitarget.build,
)

_PAPER_SYNTHETIC_BUILDERS = (
    literature_maglev_modal_response.build,
    strong_wrapping.build,
    same_range_far_angles.build,
    aoa_error_bootstrap.build,
    target_snr_drop.build,
)


_MEASURED_BRIDGE_BUILDERS = (
    measured_bridge_point4_transverse.build,
)

_DEFAULT_SYNTHETIC_PEAK_DISPLACEMENT_MM = 1.5


def _build_from_builders(builders, include_measured_bridge=False):
    base = Phase1Config(
        motion_profile="cold_start_ramp",
        truth_peak_displacement_mm=_DEFAULT_SYNTHETIC_PEAK_DISPLACEMENT_MM,
    )
    selected_builders = list(builders)
    if include_measured_bridge:
        selected_builders.extend(_MEASURED_BRIDGE_BUILDERS)
    return [builder(base) for builder in selected_builders]


def build_phase1_scenarios(include_measured_bridge=False):
    return _build_from_builders(_PAPER_SYNTHETIC_BUILDERS, include_measured_bridge=include_measured_bridge)


def build_paper_phase1_scenarios(include_measured_bridge=False):
    return build_phase1_scenarios(include_measured_bridge=include_measured_bridge)


def build_all_phase1_scenarios(include_measured_bridge=False):
    return _build_from_builders(_ALL_SYNTHETIC_BUILDERS, include_measured_bridge=include_measured_bridge)


def build_measured_bridge_scenarios():
    base = Phase1Config()
    return [builder(base) for builder in _MEASURED_BRIDGE_BUILDERS]
