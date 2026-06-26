import csv
import tempfile
import unittest
from pathlib import Path

from simulation.phase1.scenario_diagnostics import write_scenario_diagnostics
from simulation.phase1.scenarios import build_all_phase1_scenarios


class Phase1ScenarioDiagnosticsTest(unittest.TestCase):
    def test_write_scenario_diagnostics_creates_parameter_table_and_plots(self):
        scenarios = build_all_phase1_scenarios()[:2]

        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_scenario_diagnostics(scenarios, Path(tmpdir))

            self.assertTrue(written["parameters_csv"].exists())
            self.assertTrue(written["summary_md"].exists())
            self.assertTrue(written["plots_dir"].exists())

            with written["parameters_csv"].open() as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 2)
            for field in (
                "scenario",
                "scenario_label_zh",
                "validation_purpose_zh",
                "validation_focus_zh",
                "duration_s",
                "sample_rate_hz",
                "motion_profile",
                "peak_displacement_mm",
                "quiet_peak_mm",
                "micro_peak_mm",
                "ramp_peak_mm",
                "main_response_peak_mm",
                "dominant_displacement_frequencies_hz",
            ):
                self.assertIn(field, rows[0])

            for scenario in scenarios:
                stem = scenario.scenario_name
                for suffix in (
                    "time_displacement",
                    "time_acceleration",
                    "frequency_displacement",
                    "frequency_acceleration",
                ):
                    svg = written["plots_dir"] / f"{stem}_{suffix}.svg"
                    self.assertTrue(svg.exists())
                    self.assertIn("<polyline", svg.read_text())

            time_svg = (written["plots_dir"] / "nominal_multifrequency_time_displacement.svg").read_text()
            self.assertIn("Time (s)", time_svg)
            self.assertIn("Relative displacement (mm)", time_svg)
            self.assertIn("legend", time_svg)

            frequency_svg = (
                written["plots_dir"] / "nominal_multifrequency_frequency_displacement.svg"
            ).read_text()
            self.assertIn("Frequency (Hz)", frequency_svg)
            self.assertIn("Amplitude (mm)", frequency_svg)

            literature_frequency_svg = (
                written["plots_dir"] / "literature_maglev_modal_response_frequency_displacement.svg"
            ).read_text()
            self.assertIn("Frequency (Hz)", literature_frequency_svg)
            self.assertIn("Amplitude (mm)", literature_frequency_svg)
            self.assertIn(">40.0<", literature_frequency_svg)
            self.assertNotIn(">120<", literature_frequency_svg)

            summary = written["summary_md"].read_text()
            self.assertIn("Scenario Diagnostics", summary)
            self.assertIn("标准多频振动", summary)
            self.assertIn("文献主频驱动磁浮轨道梁响应", summary)
            self.assertIn("验证基础多目标结构主相位融合在常规多频响应下的位移恢复精度", summary)
            self.assertIn("nominal_multifrequency_time_displacement.svg", summary)


if __name__ == "__main__":
    unittest.main()
