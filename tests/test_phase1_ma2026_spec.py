import unittest
from dataclasses import FrozenInstanceError

from simulation.phase1.ma2026.spec import MA2026_COMPLIANCE, Ma2026ComplianceEntry, compliance_by_id


class Ma2026ComplianceSpecTest(unittest.TestCase):
    def test_compliance_spec_includes_ma2026_required_entries(self):
        expected_ids = {
            "ma2026_state_space_model",
            "ma2026_predictive_phase_correction",
            "ma2026_rangebin_candidate_adapter",
            "ma2026_q_energy_selection",
            "ma2026_alpha_linear_fit",
            "ma2026_alpha_calibration_phase_adapter",
            "ma2026_convergence_time",
            "ma2026_target_input_boundary",
        }

        self.assertEqual(set(MA2026_COMPLIANCE), expected_ids)

    def test_compliance_entries_have_required_metadata(self):
        allowed_status = {"implemented", "planned", "adapter"}

        for entry_id, entry in MA2026_COMPLIANCE.items():
            with self.subTest(entry_id=entry_id):
                self.assertIsInstance(entry, Ma2026ComplianceEntry)
                self.assertEqual(entry.entry_id, entry_id)
                self.assertTrue(entry.paper_source)
                self.assertTrue(entry.implementation_files)
                self.assertIn(entry.status, allowed_status)

                with self.assertRaises(FrozenInstanceError):
                    entry.status = "planned"

    def test_alpha_linear_fit_tracks_section_and_equations_without_beta_grid_invariant(self):
        alpha_entry = compliance_by_id("ma2026_alpha_linear_fit")

        self.assertIn("Section 3.2", alpha_entry.paper_source)
        self.assertIn("Eq. (18)", alpha_entry.paper_source)
        self.assertIn("Eq. (19)", alpha_entry.paper_source)
        self.assertNotIn("beta grid", alpha_entry.algorithm_invariant.lower())

    def test_rangebin_candidate_adapter_is_not_paper_algorithm(self):
        adapter_entry = compliance_by_id("ma2026_rangebin_candidate_adapter")

        self.assertEqual(adapter_entry.status, "adapter")
        self.assertIn("not part of the paper", adapter_entry.algorithm_invariant)
        self.assertIn("Range FFT range-bin candidates", adapter_entry.algorithm_invariant)
        self.assertIn("does not use beta-grid target selection", adapter_entry.algorithm_invariant)
        self.assertIn("rangebin.py", " ".join(adapter_entry.implementation_files))
        self.assertNotIn("calibration.py", " ".join(adapter_entry.implementation_files))

    def test_alpha_calibration_phase_source_is_marked_as_adapter_not_paper_algorithm(self):
        entry = compliance_by_id("ma2026_alpha_calibration_phase_adapter")

        self.assertEqual(entry.status, "adapter")
        self.assertIn("supplied corrected LoS phase", entry.algorithm_invariant)
        self.assertIn("Do not generate", entry.algorithm_invariant)

    def test_source_classification_matches_ma2026_reproduction_boundary(self):
        self.assertIn("Section 3.1", compliance_by_id("ma2026_state_space_model").paper_source)
        self.assertIn("Section 3.1", compliance_by_id("ma2026_predictive_phase_correction").paper_source)
        self.assertIn("Section 3.2", compliance_by_id("ma2026_q_energy_selection").paper_source)
        self.assertIn("Section 3.3", compliance_by_id("ma2026_convergence_time").paper_source)
        self.assertEqual(compliance_by_id("ma2026_rangebin_candidate_adapter").status, "adapter")
        self.assertEqual(compliance_by_id("ma2026_target_input_boundary").status, "adapter")
        self.assertIn(
            "target-specific paper method",
            compliance_by_id("ma2026_target_input_boundary").paper_source,
        )
        invariant = compliance_by_id("ma2026_target_input_boundary").algorithm_invariant
        self.assertIn("Range FFT range bins", invariant)
        self.assertIn("not from Range-Angle", invariant)


if __name__ == "__main__":
    unittest.main()
