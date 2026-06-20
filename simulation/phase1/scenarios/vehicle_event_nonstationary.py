from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="vehicle_event_nonstationary",
        motion_profile="cold_start_vehicle_event",
        quiet_start_duration_s=0.10,
        vehicle_event_center_s=2.2,
        vehicle_event_width_s=0.35,
        component_amplitudes_mm=(0.12, 0.06, 0.03),
    )
