from dataclasses import replace


def build(base):
    return replace(
        base,
        scenario_name="target_dropout",
        dropout_target_indices=(0,),
        dropout_start_s=1.6,
        dropout_end_s=3.4,
    )
