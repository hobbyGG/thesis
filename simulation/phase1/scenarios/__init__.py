from . import (
    aoa_error_bootstrap,
    low_snr_multitarget,
    ma2023_balanced_good_targets,
    mixed_scatterer_rangebin,
    measured_bridge_point4_transverse,
    nominal_multifrequency,
    same_range_far_angles,
    strong_wrapping,
    target_dropout,
    target_snr_drop,
    vehicle_event_nonstationary,
)
from ..config import Phase1Config


_SYNTHETIC_BUILDERS = (
    nominal_multifrequency.build,
    ma2023_balanced_good_targets.build,
    strong_wrapping.build,
    aoa_error_bootstrap.build,
    target_snr_drop.build,
    target_dropout.build,
    mixed_scatterer_rangebin.build,
    same_range_far_angles.build,
    low_snr_multitarget.build,
    vehicle_event_nonstationary.build,
)


_MEASURED_BRIDGE_BUILDERS = (
    measured_bridge_point4_transverse.build,
)

_DEFAULT_SYNTHETIC_PEAK_DISPLACEMENT_MM = 1.5


def build_phase1_scenarios(include_measured_bridge=True):
    base = Phase1Config(
        motion_profile="cold_start_ramp",
        truth_peak_displacement_mm=_DEFAULT_SYNTHETIC_PEAK_DISPLACEMENT_MM,
    )
    builders = [nominal_multifrequency.build]
    if include_measured_bridge:
        builders.extend(_MEASURED_BRIDGE_BUILDERS)
    builders.extend(_SYNTHETIC_BUILDERS[1:])
    return [builder(base) for builder in builders]


def build_measured_bridge_scenarios():
    base = Phase1Config()
    return [builder(base) for builder in _MEASURED_BRIDGE_BUILDERS]
