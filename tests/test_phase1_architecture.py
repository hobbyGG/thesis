import importlib
import inspect
import unittest


class Phase1ArchitectureTest(unittest.TestCase):
    def test_algorithm_and_baseline_modules_export_expected_public_api(self):
        algorithm = importlib.import_module("simulation.phase1.algorithm")
        baselines = importlib.import_module("simulation.phase1.baselines")
        ma2026 = importlib.import_module("simulation.phase1.ma2026")

        for name in (
            "MethodResult",
            "cold_start_reference_mean",
            "estimate_proposed",
            "estimate_proposed_full_pipeline",
            "estimate_proposed_full_pipeline_kappa_confidence",
            "estimate_proposed_full_pipeline_calibrated",
            "estimate_proposed_full_pipeline_kappa_confidence_r",
            "estimate_proposed_full_pipeline_posterior_r",
            "estimate_proposed_full_pipeline_doc_strict",
            "run_structural_phase_kalman",
        ):
            self.assertTrue(hasattr(algorithm, name), name)

        for name in (
            "estimate_oracle",
            "estimate_itoh_ls",
            "estimate_range_bin_itoh",
            "estimate_single_target_ma_style",
            "estimate_multitarget_true_kappa_fixed_r",
            "estimate_multitarget_aoa_fixed_kappa",
            "estimate_selected_aoa_fixed_kappa",
            "estimate_range_bin_only_mixed_phase",
            "estimate_ma_style_iterative_beta_range_bin",
        ):
            self.assertTrue(hasattr(baselines, name), name)

        for name in (
            "Ma2026Config",
            "Ma2026RangeBinInput",
            "beta_grid",
            "calibrate_best_target",
            "estimate_ma2026_reproduction",
            "estimate_ma2026_target",
            "rangebin_input_from_range_angle",
            "run_ma2026_los_kalman",
            "select_q_by_energy",
        ):
            self.assertTrue(hasattr(ma2026, name), name)

    def test_methods_keeps_backward_compatible_exports(self):
        methods = importlib.import_module("simulation.phase1.methods")

        for name in (
            "MethodResult",
            "cold_start_reference_mean",
            "estimate_oracle",
            "estimate_itoh_ls",
            "estimate_range_bin_itoh",
            "estimate_single_target_ma_style",
            "estimate_multitarget_true_kappa_fixed_r",
            "estimate_multitarget_aoa_fixed_kappa",
            "estimate_selected_aoa_fixed_kappa",
            "estimate_range_bin_only_mixed_phase",
            "estimate_ma_style_iterative_beta_range_bin",
            "estimate_ma2026_reproduction",
            "estimate_ma2026_target",
            "estimate_proposed",
            "estimate_proposed_full_pipeline",
            "estimate_proposed_full_pipeline_kappa_confidence",
            "estimate_proposed_full_pipeline_calibrated",
            "estimate_proposed_full_pipeline_kappa_confidence_r",
            "estimate_proposed_full_pipeline_posterior_r",
            "estimate_proposed_full_pipeline_doc_strict",
        ):
            self.assertTrue(hasattr(methods, name), name)

    def test_scenarios_are_split_into_package_modules(self):
        scenarios = importlib.import_module("simulation.phase1.scenarios")

        self.assertTrue(hasattr(scenarios, "__path__"))
        expected_modules = (
            "nominal_multifrequency",
            "literature_maglev_modal_response",
            "ma2023_balanced_good_targets",
            "strong_wrapping",
            "aoa_error_bootstrap",
            "target_snr_drop",
            "target_dropout",
            "mixed_scatterer_rangebin",
            "same_range_far_angles",
            "low_snr_multitarget",
            "vehicle_event_nonstationary",
        )
        for module_name in expected_modules:
            module = importlib.import_module(f"simulation.phase1.scenarios.{module_name}")
            self.assertTrue(hasattr(module, "build"), module_name)

        scenario_names = [item.scenario_name for item in scenarios.build_phase1_scenarios()]
        self.assertEqual(
            scenario_names,
            [
                "literature_maglev_modal_response",
                "strong_wrapping",
                "same_range_far_angles",
                "aoa_error_bootstrap",
                "target_snr_drop",
                "vehicle_event_nonstationary",
            ],
        )

        all_scenario_names = [item.scenario_name for item in scenarios.build_all_phase1_scenarios()]
        self.assertEqual(all_scenario_names, list(expected_modules))

        measured_names = [item.scenario_name for item in scenarios.build_phase1_scenarios(include_measured_bridge=True)]
        self.assertIn("measured_bridge_point4_transverse", measured_names)

    def test_pipeline_uses_unified_scenario_inputs_and_method_registry(self):
        inputs = importlib.import_module("simulation.phase1.scenario_inputs")
        registry = importlib.import_module("simulation.phase1.method_registry")
        pipeline = importlib.import_module("simulation.phase1.pipeline")

        for name in (
            "FrontendViews",
            "RadarViews",
            "ScenarioInputs",
            "build_scenario_inputs",
        ):
            self.assertTrue(hasattr(inputs, name), name)

        for name in (
            "MethodSpec",
            "default_method_specs",
            "run_method_specs",
            "target_reference_by_method",
        ):
            self.assertTrue(hasattr(registry, name), name)

        source = inspect.getsource(pipeline.evaluate_scenario)
        self.assertIn("build_scenario_inputs", source)
        self.assertIn("run_method_specs", source)
        self.assertNotIn("simulate_adc_cube", source)
        self.assertNotIn("range_angle_process", source)
        self.assertNotIn("RadarAlgorithmInput(", source)
        self.assertNotIn("estimate_proposed(", source)

    def test_legacy_inputs_module_reexports_scenario_inputs(self):
        scenario_inputs = importlib.import_module("simulation.phase1.scenario_inputs")
        legacy_inputs = importlib.import_module("simulation.phase1.inputs")

        self.assertIs(legacy_inputs.ScenarioInputs, scenario_inputs.ScenarioInputs)
        self.assertIs(legacy_inputs.FrontendViews, scenario_inputs.FrontendViews)
        self.assertIs(legacy_inputs.RadarViews, scenario_inputs.RadarViews)
        self.assertIs(legacy_inputs.build_scenario_inputs, scenario_inputs.build_scenario_inputs)

    def test_evaluate_facade_exports_only_public_evaluation_api(self):
        evaluate = importlib.import_module("simulation.phase1.evaluate")
        gates = importlib.import_module("simulation.phase1.gates")

        self.assertEqual(
            tuple(evaluate.__all__),
            (
                "build_gate_results",
                "evaluate_all_scenarios",
                "evaluate_scenario",
            ),
        )
        self.assertFalse(hasattr(evaluate, "_frontend_candidate_bins"))
        self.assertFalse(hasattr(evaluate, "_build_gate_results"))
        self.assertFalse(hasattr(gates, "_build_gate_results"))
        self.assertFalse(hasattr(gates, "_row_lookup"))
        self.assertFalse(hasattr(gates, "_same_range_far_angle_pair_count"))

    def test_pipeline_no_longer_reexports_scenario_input_helpers(self):
        pipeline = importlib.import_module("simulation.phase1.pipeline")

        for name in (
            "_frontend_candidate_bins",
            "_frontend_available_threshold",
            "_range_bin_only_mixed_input",
            "_selected_frontend_algorithm_input",
        ):
            self.assertFalse(hasattr(pipeline, name), name)

    def test_scenario_inputs_expose_named_radar_views_for_new_cases(self):
        inputs = importlib.import_module("simulation.phase1.scenario_inputs")
        scenarios = importlib.import_module("simulation.phase1.scenarios")
        radar_module = importlib.import_module("simulation.phase1.radar")

        scenario_inputs = inputs.build_scenario_inputs(scenarios.build_phase1_scenarios()[0])

        self.assertIsInstance(scenario_inputs, inputs.ScenarioInputs)
        self.assertIsInstance(scenario_inputs.radar, inputs.RadarViews)
        self.assertIsInstance(scenario_inputs.frontend, inputs.FrontendViews)
        self.assertIsInstance(scenario_inputs.radar.target_algorithm, radar_module.RadarAlgorithmInput)
        self.assertIsInstance(scenario_inputs.radar.selected_frontend, radar_module.RadarAlgorithmInput)
        self.assertIsInstance(scenario_inputs.radar.range_bin_only, radar_module.RadarAlgorithmInput)
        self.assertEqual(
            scenario_inputs.radar.selected_frontend.wrapped_phase_rad.shape,
            scenario_inputs.frontend.frontend_targets.wrapped_phase_rad.shape,
        )
        self.assertEqual(
            scenario_inputs.frontend.target_reference_indices.shape[0],
            scenario_inputs.frontend.frontend_targets.measured_kappa.shape[0],
        )

    def test_method_registry_separates_paper_and_diagnostic_methods(self):
        registry = importlib.import_module("simulation.phase1.method_registry")

        method_names = [spec.name for spec in registry.default_method_specs()]

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
        self.assertTrue(all(spec.role in {"reference", "paper"} for spec in registry.default_method_specs()))
        self.assertTrue(all(spec.status == "active" for spec in registry.default_method_specs()))

        all_method_names = [spec.name for spec in registry.all_method_specs()]
        self.assertIn("single_target_ma_style", all_method_names)
        self.assertIn("ma_style_iterative_beta_range_bin", all_method_names)
        self.assertIn("proposed_full_pipeline_posterior_r", all_method_names)
        self.assertIn("proposed_full_pipeline_doc_strict", all_method_names)

        spec_by_name = {spec.name: spec for spec in registry.all_method_specs()}
        self.assertEqual(spec_by_name["single_target_ma_style"].status, "deprecated")
        self.assertEqual(spec_by_name["proposed_full_pipeline"].status, "deprecated")
        self.assertEqual(spec_by_name["proposed_full_pipeline_posterior_r"].role, "ablation")
        self.assertEqual(spec_by_name["ma_style_iterative_beta_range_bin"].role, "diagnostic")


if __name__ == "__main__":
    unittest.main()
