from dataclasses import replace


def build(base):
    return replace(base, scenario_name="nominal_multifrequency")
