import csv
import tempfile
import unittest
from pathlib import Path

from simulation.phase1.extended_experiments import (
    run_extended_experiments,
    write_extended_experiment_report,
)


class Phase1ExtendedExperimentsTest(unittest.TestCase):
    def test_extended_experiments_return_monte_carlo_ablation_and_sensitivity_tables(self):
        summary = run_extended_experiments(
            seeds=(2026,),
            monte_carlo_scenarios=("same_range_far_angles",),
            aoa_errors_deg=(0.0, 8.0),
            snr_floors_db=(6.0, 10.0),
        )

        self.assertIn("monte_carlo_rows", summary)
        self.assertIn("monte_carlo_summary_rows", summary)
        self.assertIn("ablation_rows", summary)
        self.assertIn("sensitivity_aoa_rows", summary)
        self.assertIn("sensitivity_snr_rows", summary)

        mc_summary = summary["monte_carlo_summary_rows"]
        self.assertTrue(any(row["method"] == "ma2026_reproduction" for row in mc_summary))
        self.assertTrue(any(row["method"] == "proposed_full_pipeline" for row in mc_summary))
        self.assertTrue(any(row["method"] == "proposed_full_pipeline_kappa_confidence" for row in mc_summary))
        full_mc = next(row for row in mc_summary if row["method"] == "proposed_full_pipeline_kappa_confidence")
        self.assertEqual(full_mc["scenario_label_zh"], "同 rangeBin 远角度多目标")
        self.assertIn("angle-bin 分离", full_mc["validation_purpose_zh"])
        self.assertIn("rmse_mean_mm", full_mc)
        self.assertIn("rmse_std_mm", full_mc)
        self.assertEqual(full_mc["n"], 1)

        ablation_methods = {row["method"] for row in summary["ablation_rows"]}
        self.assertIn("ma_style_iterative_beta_range_bin", ablation_methods)
        self.assertIn("ma2026_reproduction", ablation_methods)
        self.assertIn("proposed_full_pipeline", ablation_methods)
        self.assertIn("proposed_full_pipeline_kappa_confidence", ablation_methods)

        self.assertEqual({row["aoa_error_deg"] for row in summary["sensitivity_aoa_rows"]}, {0.0, 8.0})
        self.assertEqual({row["snr_floor_db"] for row in summary["sensitivity_snr_rows"]}, {6.0, 10.0})
        self.assertIn(
            "proposed_full_pipeline_kappa_confidence",
            {row["method"] for row in summary["sensitivity_aoa_rows"]},
        )
        self.assertIn(
            "proposed_full_pipeline_kappa_confidence",
            {row["method"] for row in summary["sensitivity_snr_rows"]},
        )

    def test_write_extended_experiment_report_creates_paper_ready_tables(self):
        summary = run_extended_experiments(
            seeds=(2026,),
            monte_carlo_scenarios=("same_range_far_angles",),
            aoa_errors_deg=(0.0,),
            snr_floors_db=(8.0,),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_extended_experiment_report(summary, Path(tmpdir))

            self.assertTrue(written["monte_carlo_csv"].exists())
            self.assertTrue(written["monte_carlo_summary_csv"].exists())
            self.assertTrue(written["ablation_csv"].exists())
            self.assertTrue(written["sensitivity_aoa_csv"].exists())
            self.assertTrue(written["sensitivity_snr_csv"].exists())
            self.assertTrue(written["summary_md"].exists())

            header = written["monte_carlo_summary_csv"].read_text().splitlines()[0].split(",")
            self.assertIn("scenario_label_zh", header)
            self.assertIn("validation_purpose_zh", header)
            self.assertIn("rmse_mean_mm", header)
            self.assertIn("rmse_std_mm", header)

            with written["ablation_csv"].open() as f:
                rows = list(csv.DictReader(f))
            self.assertTrue(any(row["method"] == "proposed_full_pipeline_kappa_confidence" for row in rows))
            self.assertIn("Monte Carlo", written["summary_md"].read_text())


if __name__ == "__main__":
    unittest.main()
