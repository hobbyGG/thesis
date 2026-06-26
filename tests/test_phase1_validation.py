import unittest
import tempfile
import inspect
from pathlib import Path

from simulation.phase1.evaluate import evaluate_all_scenarios, evaluate_scenario
from simulation.phase1.method_registry import all_method_specs, default_method_specs
from simulation.phase1.reporting import write_validation_report
from simulation.phase1.scenario_inputs import frontend_candidate_bins
from simulation.phase1.scenarios import build_all_phase1_scenarios, build_phase1_scenarios


class Phase1ScenarioTest(unittest.TestCase):
    def test_phase1_scenarios_cover_required_innovation_cases(self):
        scenarios = build_phase1_scenarios()
        names = [scenario.scenario_name for scenario in scenarios]

        self.assertEqual(
            names,
            [
                "literature_maglev_modal_response",
                "strong_wrapping",
                "same_range_far_angles",
                "aoa_error_bootstrap",
                "target_snr_drop",
                "vehicle_event_nonstationary",
            ],
        )
        self.assertNotIn("nominal_multifrequency", names)
        self.assertNotIn("measured_bridge_point4_transverse", names)
        self.assertEqual(len(names), len(set(names)))

        all_names = [scenario.scenario_name for scenario in build_all_phase1_scenarios()]
        self.assertIn("nominal_multifrequency", all_names)
        self.assertIn("target_dropout", all_names)
        self.assertIn("mixed_scatterer_rangebin", all_names)
        self.assertIn("low_snr_multitarget", all_names)
        self.assertIn("ma2023_balanced_good_targets", all_names)
        self.assertEqual(len(all_names), len(set(all_names)))


class Phase1EvaluationTest(unittest.TestCase):
    def test_evaluate_scenario_returns_metrics_for_paper_methods_by_default(self):
        scenario = build_phase1_scenarios()[0]
        rows, artifacts = evaluate_scenario(scenario)
        method_names = {row["method"] for row in rows}

        self.assertIn("oracle", method_names)
        self.assertIn("range_bin_itoh", method_names)
        self.assertIn("ma2026_reproduction", method_names)
        self.assertIn("selected_aoa_fixed_kappa", method_names)
        self.assertIn("proposed_full_pipeline_kappa_confidence", method_names)
        self.assertNotIn("range_bin_only_mixed_phase", method_names)
        self.assertNotIn("itoh_ls", method_names)
        self.assertNotIn("single_target_ma_style", method_names)
        self.assertNotIn("ma_style_iterative_beta_range_bin", method_names)
        self.assertNotIn("multitarget_true_kappa_fixed_r", method_names)
        self.assertNotIn("multitarget_aoa_fixed_kappa", method_names)
        self.assertNotIn("proposed", method_names)
        self.assertNotIn("proposed_full_pipeline", method_names)
        self.assertNotIn("proposed_full_pipeline_posterior_r", method_names)
        self.assertNotIn("proposed_full_pipeline_doc_strict", method_names)
        self.assertIn("truth", artifacts)
        self.assertIn("radar", artifacts)
        self.assertIn("selected_targets", artifacts)
        self.assertIn("selection_diagnostics", artifacts)
        self.assertIn("ma2026_rangebin_input", artifacts)
        self.assertIn("results", artifacts)

    def test_validation_rows_include_full_pipeline_selection_metrics(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "vehicle_event_nonstationary"][0]
        rows, _ = evaluate_scenario(scenario)
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertIn("selected_target_count", full)
        self.assertIn("selected_indices", full)
        self.assertIn("corrected_observation_count", full)
        self.assertIn("unwrap_error_rate", full)
        self.assertGreaterEqual(full["selected_target_count"], 1)
        self.assertNotIn(4, full["selected_indices"])

    def test_clean_full_pipeline_selection_reports_matched_targets(self):
        scenario = [item for item in build_all_phase1_scenarios() if item.scenario_name == "nominal_multifrequency"][0]
        rows, _ = evaluate_scenario(scenario)
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertNotIn(-1, full["selected_indices"])
        self.assertGreaterEqual(full["selected_target_count"], 1)

    def test_full_pipeline_dropout_target_is_rejected_before_kalman(self):
        scenario = [item for item in build_all_phase1_scenarios() if item.scenario_name == "target_dropout"][0]
        rows, artifacts = evaluate_scenario(scenario)
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertNotIn(0, full["selected_indices"])
        self.assertIn("low_presence", artifacts["selection_diagnostics"].rejected_reasons[0])

    def test_same_range_far_angles_full_pipeline_separates_targets_before_kalman(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "same_range_far_angles"][0]
        rows, artifacts = evaluate_scenario(scenario)
        diagnostic_rows, _ = evaluate_scenario(scenario, method_specs=all_method_specs())
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")
        selected_frontend = artifacts["selected_frontend_targets"]

        self.assertGreaterEqual(full["selected_target_count"], 2)
        self.assertLessEqual(full["rmse_mm"], 0.10)
        range_only = next(row for row in diagnostic_rows if row["method"] == "range_bin_only_mixed_phase")
        self.assertGreater(range_only["rmse_mm"], full["rmse_mm"])
        self.assertGreater(range_only["rmse_mm"], 1.25 * full["rmse_mm"])
        ma2026 = next(row for row in rows if row["method"] == "ma2026_reproduction")
        self.assertGreater(ma2026["rmse_mm"], full["rmse_mm"])
        ma2026_result = next(result for result in artifacts["results"] if result.method_name == "ma2026_reproduction")
        self.assertIn("selected_beta", ma2026_result.extra)
        self.assertIn("selected_alpha", ma2026_result.extra)
        self.assertIn("selected_q", ma2026_result.extra)
        self.assertIn("alpha_calibration", ma2026_result.extra)
        self.assertIn("convergence_time_s", ma2026_result.extra)
        same_range_far_angle_pair_found = False
        for left in range(selected_frontend.range_bins.size):
            for right in range(left + 1, selected_frontend.range_bins.size):
                if (
                    selected_frontend.range_bins[left] == selected_frontend.range_bins[right]
                    and abs(selected_frontend.angle_deg[left] - selected_frontend.angle_deg[right]) > 15.0
                ):
                    same_range_far_angle_pair_found = True
        self.assertTrue(same_range_far_angle_pair_found)

    def test_ma2023_balanced_good_targets_fuses_multiple_reported_good_targets(self):
        scenario = [
            item for item in build_all_phase1_scenarios() if item.scenario_name == "ma2023_balanced_good_targets"
        ][0]
        rows, _ = evaluate_scenario(scenario)
        basic_range_bin = next(row for row in rows if row["method"] == "range_bin_itoh")
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertEqual(tuple(scenario.target_range_bins), (31, 33, 35, 42, 48))
        self.assertEqual(tuple(scenario.nominal_frequencies_hz), (0.3, 0.5, 1.0))
        self.assertLess(max(scenario.target_snr_db) - min(scenario.target_snr_db), 1.0e-9)
        self.assertGreaterEqual(full["selected_target_count"], 1)
        self.assertLess(full["rmse_mm"], basic_range_bin["rmse_mm"])

    def test_low_snr_full_pipeline_does_not_diverge_from_noisy_initial_slope(self):
        scenario = [item for item in build_all_phase1_scenarios() if item.scenario_name == "low_snr_multitarget"][0]
        rows, _ = evaluate_scenario(scenario)
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertLess(full["rmse_mm"], 0.1)
        self.assertLessEqual(full["unwrap_error_rate"], 0.001)

    def test_strong_wrapping_challenges_traditional_unwrap(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "strong_wrapping"][0]
        rows, _ = evaluate_scenario(scenario)
        itoh = next(row for row in rows if row["method"] == "range_bin_itoh")
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")

        self.assertGreater(itoh["rmse_mm"], full["rmse_mm"])
        self.assertGreater(itoh["rmse_mm"], 2.0 * full["rmse_mm"])

    def test_full_pipeline_kalman_input_comes_from_frontend_targets(self):
        scenario = build_phase1_scenarios()[0]
        _, artifacts = evaluate_scenario(scenario)
        frontend_targets = artifacts["frontend_targets"]
        radar_input = artifacts["radar_input"]

        self.assertEqual(radar_input.wrapped_phase_rad.shape, frontend_targets.wrapped_phase_rad.shape)
        self.assertEqual(radar_input.available_mask.shape, frontend_targets.available_mask.shape)
        self.assertEqual(radar_input.measured_kappa.shape, frontend_targets.measured_kappa.shape)
        self.assertEqual(radar_input.initial_r.shape, frontend_targets.measured_kappa.shape)
        self.assertFalse(hasattr(radar_input, "target_reference_indices"))

        self.assertTrue((radar_input.wrapped_phase_rad == frontend_targets.wrapped_phase_rad).all())
        self.assertTrue((radar_input.available_mask == frontend_targets.available_mask).all())
        self.assertTrue((radar_input.measured_kappa == frontend_targets.measured_kappa).all())

    def test_frontend_candidate_bins_do_not_accept_truth_metadata(self):
        params = set(inspect.signature(frontend_candidate_bins).parameters)

        self.assertTrue({"merged_peaks", "range_angle"}.issubset(params))
        self.assertTrue(params.isdisjoint({"adc", "scatterers", "truth", "radar", "kappa"}))

    def test_default_method_specs_use_clean_paper_method_set(self):
        method_names = [spec.name for spec in default_method_specs()]

        self.assertEqual(
            method_names,
            [
                "oracle",
                "range_bin_itoh",
                "ma2026_reproduction",
                "selected_aoa_fixed_kappa",
                "proposed_full_pipeline_kappa_confidence",
            ],
        )

    def test_basic_phase_baseline_uses_range_bin_input_not_target_truth(self):
        from simulation.phase1.baselines import estimate_range_bin_itoh

        params = set(inspect.signature(estimate_range_bin_itoh).parameters)

        self.assertIn("radar_input", params)
        self.assertIn("config", params)
        self.assertNotIn("truth", params)
        self.assertNotIn("radar", params)

    def test_basic_range_bin_baseline_selects_strongest_adc_range_bin(self):
        from simulation.phase1.scenario_inputs import build_scenario_inputs

        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "target_snr_drop"][0]
        inputs = build_scenario_inputs(scenario)

        self.assertEqual(int(inputs.radar.range_bin_only.extra["range_bin"]), 4)

    def test_paper_scenarios_keep_targets_inside_frontend_range_fft(self):
        from simulation.phase1.scenario_inputs import build_scenario_inputs

        for scenario in build_phase1_scenarios():
            inputs = build_scenario_inputs(scenario)
            num_range_bins = inputs.frontend.frontend_config.num_range_bins
            self.assertTrue(
                all(0 <= int(bin_idx) < num_range_bins for bin_idx in scenario.target_range_bins),
                scenario.scenario_name,
            )

    def test_posterior_r_full_pipeline_is_same_range_far_angles_ablation_candidate(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "same_range_far_angles"][0]
        rows, artifacts = evaluate_scenario(scenario, method_specs=all_method_specs())
        kappa_confidence = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")
        posterior = next(row for row in rows if row["method"] == "proposed_full_pipeline_posterior_r")
        result = next(
            result for result in artifacts["results"] if result.method_name == "proposed_full_pipeline_posterior_r"
        )

        self.assertLessEqual(posterior["rmse_mm"], kappa_confidence["rmse_mm"])
        self.assertEqual(posterior["selected_indices"], kappa_confidence["selected_indices"])
        self.assertEqual(result.extra["adaptive_r_mode"], "posterior_residual")
        self.assertEqual(result.extra["kappa_update_mode"], "centered_regularized_ls")

    def test_doc_strict_full_pipeline_uses_same_target_selection_as_full_pipeline(self):
        scenario = [item for item in build_all_phase1_scenarios() if item.scenario_name == "nominal_multifrequency"][0]
        rows, _ = evaluate_scenario(scenario, method_specs=all_method_specs())
        full = next(row for row in rows if row["method"] == "proposed_full_pipeline")
        strict = next(row for row in rows if row["method"] == "proposed_full_pipeline_doc_strict")

        self.assertEqual(strict["selected_target_count"], full["selected_target_count"])
        self.assertEqual(strict["selected_indices"], full["selected_indices"])
        self.assertGreater(strict["corrected_observation_count"], 0)

    def test_kappa_confidence_full_pipeline_selects_q_that_does_not_break_strong_wrapping(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "strong_wrapping"][0]
        rows, artifacts = evaluate_scenario(scenario)
        kappa_confidence = next(row for row in rows if row["method"] == "proposed_full_pipeline_kappa_confidence")
        result = next(
            result for result in artifacts["results"] if result.method_name == "proposed_full_pipeline_kappa_confidence"
        )

        self.assertLess(kappa_confidence["rmse_mm"], 0.20)
        self.assertEqual(kappa_confidence["unwrap_error_rate"], 0.0)
        self.assertIn("calibrated_q_candidates", result.extra)
        self.assertIn("calibrated_q_metric_values", result.extra)


class Phase1FeasibilityTest(unittest.TestCase):
    def test_evaluate_all_scenarios_reports_feasibility_gates(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:2])

        self.assertIn("rows", summary)
        self.assertIn("gates", summary)
        self.assertGreater(len(summary["rows"]), 0)
        self.assertGreater(len(summary["gates"]), 0)
        self.assertTrue(all("passed" in gate for gate in summary["gates"]))

    def test_evaluate_all_scenarios_reports_full_pipeline_gates(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios())
        gate_names = {gate["name"] for gate in summary["gates"]}

        self.assertIn("vehicle_event_full_pipeline_selected_count_ge_1", gate_names)
        self.assertIn("vehicle_event_full_pipeline_excludes_target4", gate_names)
        self.assertIn("same_range_far_angles_full_pipeline_selects_two_same_range_targets", gate_names)
        self.assertIn("same_range_far_angles_full_pipeline_rmse_le_0p10mm", gate_names)
        self.assertIn("same_range_far_angles_full_pipeline_beats_ma2026_reproduction", gate_names)
        self.assertIn("strong_wrapping_full_pipeline_beats_range_bin_itoh", gate_names)
        self.assertIn("strong_wrapping_range_bin_itoh_rmse_ge_2x_full_pipeline", gate_names)
        self.assertIn("strong_wrapping_full_pipeline_rmse_le_reasonable_threshold", gate_names)
        self.assertIn("target_snr_drop_full_pipeline_beats_selected_fixed_r", gate_names)
        self.assertIn("aoa_bootstrap_kappa_median_relative_error_le_0p05", gate_names)
        full_pipeline_failures = [
            gate["name"]
            for gate in summary["gates"]
            if (
                gate["name"].startswith("vehicle_event_full_pipeline")
                or gate["name"].startswith("target_snr_drop_full_pipeline")
                or gate["name"].startswith("aoa_bootstrap")
                or gate["name"].startswith("same_range_far_angles_full_pipeline")
            )
            and not gate["passed"]
        ]
        self.assertEqual(full_pipeline_failures, [])

    def test_full_pipeline_gates_use_kappa_confidence_method_when_available(self):
        scenario = [item for item in build_phase1_scenarios() if item.scenario_name == "strong_wrapping"][0]
        summary = evaluate_all_scenarios([scenario])
        kappa_confidence = next(
            row for row in summary["rows"] if row["method"] == "proposed_full_pipeline_kappa_confidence"
        )
        gate = next(
            gate for gate in summary["gates"] if gate["name"] == "strong_wrapping_full_pipeline_rmse_le_reasonable_threshold"
        )

        self.assertAlmostEqual(gate["value"], kappa_confidence["rmse_mm"])


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

    def test_write_validation_report_removes_stale_svg_plots(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            stale_dir = output_dir / "plots"
            stale_dir.mkdir()
            stale_plot = stale_dir / "vehicle_event_nonstationary_selected_vs_all_targets_displacement.svg"
            stale_plot.write_text("<svg></svg>")

            write_validation_report(summary, output_dir)

            self.assertFalse(stale_plot.exists())

    def test_write_validation_report_creates_diagnostic_svg_plots(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios())

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)
            plots_dir = written["plots_dir"]

            self.assertTrue((plots_dir / "aoa_error_bootstrap_kappa_bootstrap.svg").exists())
            self.assertTrue((plots_dir / "target_snr_drop_adaptive_r.svg").exists())
            self.assertTrue((plots_dir / "strong_wrapping_phase_correction.svg").exists())
            self.assertTrue((plots_dir / "vehicle_event_nonstationary_range_angle_frame.svg").exists())
            self.assertTrue((plots_dir / "vehicle_event_nonstationary_target_selection_timeline.svg").exists())
            self.assertTrue((plots_dir / "vehicle_event_nonstationary_paper_methods_displacement.svg").exists())

    def test_reporting_csv_keeps_new_metric_headers(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)
            header = written["metrics_csv"].read_text().splitlines()[0].split(",")

            self.assertIn("scenario_label_zh", header)
            self.assertIn("validation_purpose_zh", header)
            self.assertIn("validation_focus_zh", header)
            self.assertIn("selected_target_count", header)
            self.assertIn("selected_indices", header)
            self.assertIn("corrected_observation_count", header)
            self.assertIn("unwrap_error_rate", header)

    def test_summary_markdown_includes_full_pipeline_selection_columns(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)
            text = written["summary_md"].read_text()

            self.assertIn("文献主频驱动磁浮轨道梁响应", text)
            self.assertIn("基于实桥文献给出的轨道梁主频构造可解释的非平稳车辆响应仿真", text)
            self.assertIn("Selected Indices", text)
            self.assertIn("Corrected Obs", text)
            self.assertIn("Kappa Rel Err", text)

    def test_displacement_plot_includes_selected_fixed_baseline(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios()[:1])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)
            svg = (written["plots_dir"] / "literature_maglev_modal_response_displacement.svg").read_text()

            self.assertGreaterEqual(svg.count("<polyline"), 5)

    def test_validation_report_plots_include_axis_labels(self):
        summary = evaluate_all_scenarios(build_phase1_scenarios())

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            written = write_validation_report(summary, output_dir)
            plots_dir = written["plots_dir"]

            displacement = (plots_dir / "aoa_error_bootstrap_displacement.svg").read_text()
            self.assertIn("Time (s)", displacement)
            self.assertIn("Relative displacement (mm)", displacement)

            kappa = (plots_dir / "aoa_error_bootstrap_kappa_bootstrap.svg").read_text()
            self.assertIn("Time (s)", kappa)
            self.assertIn("Projection coefficient kappa", kappa)
            self.assertIn("proposed_full_pipeline_kappa_confidence", kappa)

            adaptive_r = (plots_dir / "target_snr_drop_adaptive_r.svg").read_text()
            self.assertIn("Time (s)", adaptive_r)
            self.assertIn("Measurement variance R (rad^2)", adaptive_r)
            self.assertIn("proposed_full_pipeline_kappa_confidence", adaptive_r)

            phase = (plots_dir / "strong_wrapping_phase_correction.svg").read_text()
            self.assertIn("Time (s)", phase)
            self.assertIn("LoS phase (rad)", phase)
            self.assertIn("proposed_full_pipeline_kappa_confidence", phase)

            range_angle = (plots_dir / "vehicle_event_nonstationary_range_angle_frame.svg").read_text()
            self.assertIn("Range bin", range_angle)
            self.assertIn("Peak range-angle magnitude", range_angle)

            selection = (plots_dir / "vehicle_event_nonstationary_target_selection_timeline.svg").read_text()
            self.assertIn("Time (s)", selection)
            self.assertIn("Presence / selected gate", selection)

            paper_methods = (
                plots_dir / "vehicle_event_nonstationary_paper_methods_displacement.svg"
            ).read_text()
            self.assertIn("Time (s)", paper_methods)
            self.assertIn("Relative displacement (mm)", paper_methods)
            self.assertIn("proposed_full_pipeline_kappa_confidence", paper_methods)


class Phase1ReadmeTest(unittest.TestCase):
    def test_readme_describes_frontend_full_pipeline_outputs(self):
        text = Path("simulation/phase1/README.md").read_text()

        self.assertIn("frontend.py", text)
        self.assertIn("selected_aoa_fixed_kappa", text)
        self.assertIn("range_bin_only_mixed_phase", text)
        self.assertIn("ma_style_iterative_beta_range_bin", text)
        self.assertIn("ma2026_reproduction", text)
        self.assertIn("ma2026/", text)
        self.assertIn("proposed_full_pipeline", text)
        self.assertNotIn("proposed_full_pipeline_kappa_confidence_r", text)
        self.assertIn("selected_target_count", text)
        self.assertIn("ADC/range-angle", text)


class Phase1AlgorithmChainReviewTest(unittest.TestCase):
    def test_algorithm_chain_review_mentions_every_method_module(self):
        review = Path("docs/algorithm_chain_review.md")

        self.assertTrue(review.exists())
        text = review.read_text()
        required = [
            "ADC 到 range-angle map",
            "2D peak detection",
            "同 rangeBin 近角度合并",
            "滑动窗口稳定性",
            "结构频带一致性筛选",
            "AoA cold start",
            "prediction-aided phase correction",
            "multi-target observation model",
            "same rangeBin far-angle separation",
            "range-bin-only mixed phase baseline",
            "Ma 2026 reproduction baseline",
            "Ma-style iterative beta baseline",
            "confidence-aware target-wise R",
            "online kappa bootstrap",
            "真实 IWR1843 ADC 文件解析",
        ]
        for item in required:
            self.assertIn(item, text)


if __name__ == "__main__":
    unittest.main()
