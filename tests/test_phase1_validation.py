import unittest
import tempfile
from pathlib import Path

from simulation.phase1.evaluate import evaluate_all_scenarios, evaluate_scenario
from simulation.phase1.reporting import write_validation_report
from simulation.phase1.scenarios import build_phase1_scenarios


class Phase1ScenarioTest(unittest.TestCase):
    def test_phase1_scenarios_cover_required_innovation_cases(self):
        scenarios = build_phase1_scenarios()
        names = [scenario.scenario_name for scenario in scenarios]

        self.assertIn("nominal_multifrequency", names)
        self.assertIn("strong_wrapping", names)
        self.assertIn("aoa_error_bootstrap", names)
        self.assertIn("target_snr_drop", names)
        self.assertIn("target_dropout", names)
        self.assertIn("mixed_scatterer_rangebin", names)
        self.assertIn("low_snr_multitarget", names)
        self.assertEqual(len(names), len(set(names)))


class Phase1EvaluationTest(unittest.TestCase):
    def test_evaluate_scenario_returns_metrics_for_all_core_methods(self):
        scenario = build_phase1_scenarios()[0]
        rows, artifacts = evaluate_scenario(scenario)
        method_names = {row["method"] for row in rows}

        self.assertIn("oracle", method_names)
        self.assertIn("itoh_ls", method_names)
        self.assertIn("single_target_ma_style", method_names)
        self.assertIn("multitarget_fixed", method_names)
        self.assertIn("proposed", method_names)
        self.assertIn("truth", artifacts)
        self.assertIn("radar", artifacts)
        self.assertIn("results", artifacts)


class Phase1FeasibilityTest(unittest.TestCase):
    def test_evaluate_all_scenarios_reports_feasibility_gates(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:2])

        self.assertIn("rows", summary)
        self.assertIn("gates", summary)
        self.assertGreater(len(summary["rows"]), 0)
        self.assertGreater(len(summary["gates"]), 0)
        self.assertTrue(all("passed" in gate for gate in summary["gates"]))


class Phase1ReportingTest(unittest.TestCase):
    def test_write_validation_report_creates_csv_json_and_markdown(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)

            self.assertTrue(written["metrics_csv"].exists())
            self.assertTrue(written["gates_json"].exists())
            self.assertTrue(written["summary_md"].exists())

    def test_write_validation_report_creates_svg_directory(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)

            self.assertTrue(written["plots_dir"].exists())
            self.assertGreaterEqual(len(list(written["plots_dir"].glob("*.svg"))), 1)


if __name__ == "__main__":
    unittest.main()
