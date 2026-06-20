from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="low_snr_multitarget",
        target_snr_db=(12.0, 10.0, 8.0, 6.0, 4.0),
    )
