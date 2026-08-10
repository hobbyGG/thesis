import unittest

import numpy as np

from simulation.phase1.accelerometer import build_accelerometer_observation
from simulation.phase1.scenario_inputs import build_frontend_views
from simulation.phase1.scenarios import build_all_phase1_scenarios
from simulation.phase1.truth import generate_truth_signal


def _scenario_by_name(name):
    return next(scenario for scenario in build_all_phase1_scenarios() if scenario.scenario_name == name)


class Phase1LiteratureScenarioTest(unittest.TestCase):
    def test_literature_scenarios_are_registered_as_diagnostic_cases(self):
        names = [scenario.scenario_name for scenario in build_all_phase1_scenarios()]

        self.assertIn("literature_mmwbats_same_range_aliasing", names)
        self.assertIn("literature_mmshm_adjacent_range_clutter", names)
        self.assertNotIn("literature_vitals_same_radial_distance", names)

    def test_mmwbats_same_range_aliasing_matches_range_angle_mechanism(self):
        scenario = _scenario_by_name("literature_mmwbats_same_range_aliasing")

        self.assertEqual(tuple(scenario.target_range_bins), (18, 18))
        self.assertEqual(tuple(scenario.target_angles_deg), (15.0, 30.0))
        self.assertEqual(scenario.frontend_num_virtual_rx, 8)
        self.assertGreaterEqual(scenario.frontend_num_angle_bins, 64)

        frontend = _build_frontend(scenario)
        references = set(frontend.target_reference_indices.tolist())

        self.assertTrue({0, 1}.issubset(references))
        self.assertTrue(_has_same_range_far_angle_pair(frontend.frontend_targets.range_bins, frontend.frontend_targets.angle_deg))

    def test_mmshm_adjacent_range_clutter_matches_paper_mechanism(self):
        scenario = _scenario_by_name("literature_mmshm_adjacent_range_clutter")

        self.assertEqual(tuple(scenario.target_range_bins), (18, 19))
        self.assertEqual(tuple(scenario.target_angles_deg), (15.0, 30.0))

        frontend = _build_frontend(scenario)
        references = set(frontend.target_reference_indices.tolist())
        detected_ranges = set(frontend.frontend_targets.range_bins.tolist())

        self.assertTrue({0, 1}.issubset(references))
        self.assertTrue({18, 19}.issubset(detected_ranges))

def _build_frontend(scenario):
    truth = generate_truth_signal(scenario)
    accelerometer = build_accelerometer_observation(truth, scenario)
    return build_frontend_views(truth, accelerometer, scenario)


def _has_same_range_far_angle_pair(range_bins, angle_deg, min_angle_sep_deg=10.0):
    ranges = np.asarray(range_bins, dtype=int)
    angles = np.asarray(angle_deg, dtype=float)
    for left in range(ranges.size):
        for right in range(left + 1, ranges.size):
            if ranges[left] == ranges[right] and abs(angles[left] - angles[right]) >= min_angle_sep_deg:
                return True
    return False


if __name__ == "__main__":
    unittest.main()
