import unittest
from pathlib import Path
import os

import numpy as np

from simulation.phase1.accelerometer import build_accelerometer_observation
from simulation.phase1.config import Phase1Config
from simulation.phase1.pipeline import evaluate_scenario
from simulation.phase1.scenarios import build_phase1_scenarios
from simulation.phase1.truth import generate_truth_signal


REPO_ROOT = Path(__file__).resolve().parents[1]
TDMS_PATH = Path(os.environ.get("PHASE1_MEASURED_BRIDGE_TDMS", REPO_ROOT / "datafile" / "20250320test12.tdms"))


def _require_measured_bridge_fixture(testcase):
    if os.environ.get("PHASE1_RUN_MEASURED_BRIDGE_TESTS") != "1":
        testcase.skipTest("set PHASE1_RUN_MEASURED_BRIDGE_TESTS=1 to run local TDMS-backed tests")
    if not TDMS_PATH.exists():
        testcase.skipTest(f"TDMS fixture not found: {TDMS_PATH}")


class TestMeasuredBridgeIntegration(unittest.TestCase):
    def test_default_measured_bridge_config_is_inactive(self):
        config = Phase1Config()

        self.assertNotEqual(config.motion_profile, "measured_bridge")
        self.assertEqual(config.measured_bridge_laser_channel, "3-4")
        self.assertEqual(config.measured_bridge_acceleration_channel, "1-5")

    def test_dispatch_uses_measured_bridge_for_measured_profile(self):
        _require_measured_bridge_fixture(self)
        config = Phase1Config(
            motion_profile="measured_bridge",
            measured_bridge_tdms_path=str(TDMS_PATH),
            sample_rate_hz=1000.0,
            duration_s=4.0,
        )

        truth = generate_truth_signal(config)
        accel = build_accelerometer_observation(truth, config)

        self.assertEqual(truth.t.size, accel.measured_mps2.size)
        self.assertGreater(np.std(truth.q_m), 0.0)
        self.assertGreater(np.std(accel.measured_mps2), 0.0)

    def test_measured_bridge_scenario_is_registered(self):
        scenarios = build_phase1_scenarios(include_measured_bridge=True)
        names = [scenario.scenario_name for scenario in scenarios]

        self.assertIn("measured_bridge_point4_transverse", names)

    def test_default_measured_bridge_scenario_uses_radar_slow_time_rate(self):
        scenario = next(
            scenario
            for scenario in build_phase1_scenarios(include_measured_bridge=True)
            if scenario.scenario_name == "measured_bridge_point4_transverse"
        )

        self.assertEqual(scenario.sample_rate_hz, 100.0)

    def test_measured_bridge_runs_key_methods(self):
        _require_measured_bridge_fixture(self)
        scenario = next(
            scenario
            for scenario in build_phase1_scenarios(include_measured_bridge=True)
            if scenario.scenario_name == "measured_bridge_point4_transverse"
        )

        rows, artifacts = evaluate_scenario(scenario)
        methods = {row["method"] for row in rows}

        self.assertIn("ma2026_reproduction", methods)
        self.assertIn("proposed_full_pipeline_beta_confidence", methods)
        self.assertIn("selected_aoa_fixed_beta", methods)
        self.assertEqual(artifacts["truth"].t.size, int(round(scenario.duration_s * scenario.sample_rate_hz)))

        proposed = next(row for row in rows if row["method"] == "proposed_full_pipeline_beta_confidence")
        self.assertGreaterEqual(proposed["selected_target_count"], 1)
        self.assertNotIn(-1, proposed["selected_indices"])
        self.assertLess(proposed["unwrap_error_rate"], 0.05)
