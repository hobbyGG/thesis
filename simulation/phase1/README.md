# Phase 1 Simulation Validation

This package implements the first-stage synthetic validation for the thesis method:

- Structural truth is a multi-frequency displacement signal sampled at a slow-time frame/Kalman rate of 100 Hz. The default synthetic components are near 2 Hz, 5 Hz, and 12 Hz, keeping them below the slow-time Nyquist limit.
- Radar timing explicitly separates slow time from ADC fast time: the default Phase-1 timing profile uses 100 Hz slow-time frames, 6 MHz ADC fast-time sampling, 256 ADC samples per chirp, 60 us chirps, and 4 chirps per frame/time step.
- The truth generator can optionally scale synthetic scenarios by the final displacement peak, prepend a physically quiet calibration segment, and generate nonstationary responses by applying smooth event envelopes to the same modal components.
- Radar observations include both target-wise ablation IQ signals and a physics-shaped synthetic frontend in `frontend.py` that generates an ADC cube, applies range FFT and spatial-frequency angle FFT, and extracts frontend slow-time target observations from Range-Angle peaks.
- The proposed algorithm receives only an algorithm-visible radar input view: wrapped phase, measured/AoA-derived initial `kappa`, and availability masks. Truth fields such as `q_m`, true `kappa`, and unwrapped LoS phase are kept outside the proposed estimator and are used only for simulation generation or evaluation.
- Evaluation is performed on displacement relative to the cold-start reference:

```text
delta_q(t) = q(t) - mean(q over cold_start_window)
delta_Theta(t) = 4*pi*delta_q(t)/lambda
```

- Validation compares baselines and the proposed multi-target structural-main-phase Kalman method.

## Package Structure

- `algorithm.py`: proposed structural-main-phase Kalman estimator, prediction-aided phase correction, calibrated `Q`, SNR-informed initial `R`, posterior-residual / quality-gated confidence-aware target-wise effective `R`, and online `kappa` bootstrap.
- `baselines.py`: oracle, Itoh-LS, single-target Ma-style, fixed-kappa, range-bin-only, and Ma-style iterative-beta baselines.
- `ma2026/`: dedicated reproduction package for the formal Ma 2026 baseline. It separates the paper target-specific LoS-phase Kalman method from the simulation-only range-bin candidate adapter.
- `scenario_inputs.py`: the unified scenario input builder. It turns one `Phase1Config` into named data views: truth, accelerometer, target-level radar, frontend/range-angle outputs, selected frontend radar input, range-bin-only input, and Ma2026 range-bin input.
- `method_registry.py`: the central method list. Add comparison methods here instead of hard-coding calls inside the pipeline.
- `pipeline.py`: thin orchestration only: build scenario inputs, run registered methods, convert results to metric rows, and return artifacts.
- `evaluation.py` and `gates.py`: metric row construction and feasibility gate definitions.
- `scenarios/`: one module per synthetic validation scenario. `scenarios.build_phase1_scenarios()` returns the clean paper scenario set, while `scenarios.build_all_phase1_scenarios()` returns sanity, appendix, robustness, and diagnostic scenarios as well.
- `inputs.py`: backward-compatible re-export layer for older scenario-input imports.
- `methods.py`: backward-compatible re-export layer for older imports.

## Extension Points

The Phase-1 flow is intentionally organized so new experiments can be added without editing hidden internals:

- Add a new test situation or target layout by creating `simulation/phase1/scenarios/<name>.py` with a `build(base)` function that returns `replace(base, ...)`, then register it in `scenarios/__init__.py`.
- Change radar target geometry, SNR, range bins, dropout/degradation windows, ADC settings, or slow-time rate through `Phase1Config` fields in the scenario builder.
- Change how radar observations are exposed to methods in `scenario_inputs.py`. The main public object is `ScenarioInputs`, which contains `RadarViews` and `FrontendViews`.
- Add a new method or baseline by implementing the estimator in `algorithm.py`, `baselines.py`, or a focused package, then adding one `MethodSpec` in `method_registry.py`.
- Keep `pipeline.py` as orchestration glue. It should not directly simulate ADC data, pick targets, or manually construct method-specific radar inputs.

## Current Method Under Test

The proposed method estimates structural main phase:

```text
x_k = [Theta_k, dotTheta_k]^T
Theta_k = 4*pi*delta_q_k/lambda
```

The noise-parameter policy used for the thesis method is:

- `Q` is treated as a global calibrated process-noise parameter for the structural-main-phase state. It is selected from an offline or initial calibration segment and then kept fixed during the online estimation interval.
- Each target receives an SNR-informed initial measurement noise value `R_i,0`. The initial value expresses the expected phase quality of that target before sufficient residual and target-quality statistics have accumulated.
- During online filtering, only the measurement noise is adapted target-wise as `R_i,k`. The thesis-method target behavior is to update the base measurement noise from posterior residuals, modulated by a target-quality gate, and bounded by robust clipping limits. The gate prevents a large prediction innovation during strong structural response from being interpreted automatically as radar measurement noise. Because the full pipeline starts from AoA-derived conversion coefficients, the effective observation noise also includes a small `kappa`-confidence term that propagates current conversion-coefficient uncertainty into `R_i,k`.

This means the current algorithmic direction is calibrated `Q` + SNR-informed initial `R` + posterior-residual / quality-gated confidence-aware target-wise online `R_i,k`. It should not be described as simultaneous online adaptation of both `Q` and `R`. Sliding-window `q` selection or adaptive `Q_k` is reserved for future work and is not part of the present main method.

The adaptive-`R` policy is literature-guided but not copied verbatim. Akhlaghi, Zhou, and Huang's adaptive noise covariance work motivates the split in which prediction innovation is associated with process/model uncertainty while posterior residual is more appropriate for measurement-noise estimation. Mehra's adaptive filtering taxonomy motivates the covariance-matching view, and Li et al.'s redundant measurement-noise covariance estimation motivates per-channel measurement weighting. The Phase-1 thesis method adapts these ideas to mmWave radar by making `R_i,k` target-wise, gating upward `R` changes by radar target quality, and adding the `kappa`-confidence term required by AoA cold start and online conversion-coefficient bootstrap.

In code, `proposed_full_pipeline_kappa_confidence` implements the `Q` calibration as a candidate-grid selection over `calibrated_q_candidates`. Each candidate runs the same structural-main-phase Kalman filter, and the selected `q^\star` minimizes target-level innovation energy. This calibration uses only algorithm-visible measurements and not truth RMSE; the selected `Q=q^\star Q_0` is then fixed for the reported online filtering result. If `calibrated_process_noise_intensity` is set explicitly in `Phase1Config`, that manual value is used directly.

For the AoA cold-start problem, the main full-pipeline method keeps the same calibrated `Q`, online `kappa` bootstrap, and target-wise adaptive base `R`, but adds an observation-model uncertainty term propagated from the current `kappa_i` variance:

```text
R_eff_i,k = R_base_i,k + (Theta_pred^2 + P_ThetaTheta_pred) * sigma_kappa_i,k^2
```

The extra term is large when the AoA-derived conversion coefficient is still uncertain and naturally decays as the short-window `kappa_i` bootstrap becomes confident. Its diagnostics are reported as `base_r_history`, `base_r_update_gate_history`, `target_quality_history`, `kappa_variance_history`, and `kappa_uncertainty_r_history`. This is an implementation support for the AoA cold-start and online bootstrap loop, not a separate thesis contribution.

Each target contributes:

```text
z_corr_i,k = psi_i,k + 2*pi*round((kappa_hat_i*Theta_pred + b_i - psi_i,k)/(2*pi))
```

The same corrected phase is used for Kalman update and online `kappa_i` bootstrap.

The default validation now uses a clean paper method set. Diagnostic and deprecated methods remain implemented and can be run with `--method-set all`, but they are not emitted by default into the main `metrics.csv` / `summary.md`.

Default paper/reference methods:

- `oracle`: relative truth upper reference.
- `range_bin_itoh`: conventional range-bin phase baseline. It selects the strongest range bin from the ADC range FFT profile, extracts the strongest virtual-RX slow-time complex value at that range bin, applies Itoh unwrapping, and converts phase to displacement with the measured/equivalent geometry coefficient. It does not use target-level oracle phase or true `kappa`.
- `ma2026_reproduction`: formal staged Ma-family baseline. The simulation wrapper first runs an offline calibration stage on the available test/calibration segment: range-bin candidates are enumerated, each candidate is acceleration-aided unwrapped over the beta grid, and the target/beta pair with the minimum band-limited displacement mismatch is selected. The selected single target then enters the Ma 2026 LoS-phase Kalman stage, whose state is `[phi, dot phi]`, acceleration input is `4*pi*a/(beta*lambda)`, continuous `R=1` is discretized as `R_d=R/T_a`, `Q=10^j` is selected by estimated continuous-phase energy minimization, and the Section 3.3 minimum convergence-time diagnostic is reported. The range-bin enumeration remains a simulation adapter, but the target/beta calibration now precedes Kalman instead of being replaced by an automatic R2 target selector.
- `selected_aoa_fixed_kappa`: frontend-selected targets with AoA initial `kappa` fixed, used as the selected-target fixed-geometry baseline.
- `proposed_full_pipeline_kappa_confidence`: the full pipeline with innovation-energy-selected global `Q`, SNR-informed initial `R_i,0`, posterior-residual / quality-gated confidence-aware target-wise effective `R_i,k`, and online `kappa` bootstrap. This is the current Phase 1 main synthetic method.

Explicit diagnostic/ablation methods:

- `itoh_ls`: ideal target-level single-target Itoh unwrap reference retained for diagnostics only. It bypasses the range-bin/frontend path and should not be reported as the conventional radar baseline.
- `range_bin_only_mixed_phase`: range-bin-only mixed phase Kalman ablation that uses the same range-FFT range-bin observation as a single pseudo-target. It is retained for same-range far-angle mechanism analysis, but is not part of the default paper method set.
- `ma_style_iterative_beta_range_bin`: range-bin iterative-beta mechanism ablation. It is retained for same-range mixing analysis and is not the formal Ma reproduction.
- `multitarget_true_kappa_fixed_r`: known-geometry ablation with true fixed `kappa`; it intentionally uses information unavailable to the real algorithm and is not a paper baseline.
- `multitarget_aoa_fixed_kappa`: all-target AoA-fixed ablation without frontend selection.
- `proposed_full_pipeline_posterior_r`: calibrated-`Q` full pipeline with posterior-residual adaptive `R`, retained as an adaptive-R residual-definition ablation.

Deprecated compatibility methods:

- `single_target_ma_style`: early single-target acceleration-aided Kalman baseline, superseded by `ma2026_reproduction`.
- `proposed`: all-target early version without the complete frontend selection chain.
- `proposed_full_pipeline`: old full-pipeline variant before the final kappa-confidence `R` policy.
- `proposed_full_pipeline_doc_strict`: strict historical comparison variant using the older plain-window LS and conservative initial-R rule.

The default paper scenario set is deliberately small. It contains six scenarios: `literature_maglev_modal_response`, `strong_wrapping`, `same_range_far_angles`, `aoa_error_bootstrap`, `target_snr_drop`, and `vehicle_event_nonstationary`. The full diagnostic set additionally contains `nominal_multifrequency`, `ma2023_balanced_good_targets`, `target_dropout`, `mixed_scatterer_rangebin`, and `low_snr_multitarget`; run validation with `--scenario-set all` when these appendix/sensitivity cases are needed.

Default synthetic scenarios are normalized by the generated truth peak displacement rather than by component amplitudes alone. Regular synthetic cases now use a cold-start ramp profile: 0-0.2 s is quiet, 0.2-0.8 s is a weak bootstrap vibration of roughly 0.05-0.20 mm, 0.8-1.4 s smoothly grows toward the main response, and the later interval reaches the scenario peak of about `1.5 mm`. `strong_wrapping` keeps a stronger cold-start/micro-vibration/ramp/strong-response/decay profile and targets about `5.0 mm` peak displacement. This makes the wrapping scenario cross multiple radar phase periods for a 77 GHz carrier while keeping the other scenarios in a realistic millimeter-level response range.

`sample_rate_hz` is always the slow-time phase/frame/Kalman sampling rate. It is not the ADC sampling rate. ADC fast-time parameters are represented separately by `adc_sample_rate_hz`, `adc_samples_per_chirp`, `chirp_duration_s`, and `chirps_per_frame`. The synthetic ADC cube is therefore suitable for algorithm-level frontend validation, but it is not a parser or replay of real IWR1843 raw ADC files.

In the synthetic frontend, `target_snr_db` is calibrated at the target observation level: each scatterer's slow-time complex IQ is perturbed before ADC cube synthesis, so range/angle FFT processing does not artificially convert a configured target SNR into a much higher post-FFT SNR. ADC background noise is still added to keep the Range-Angle Map background non-degenerate, but it is not the primary definition of target quality.

The `ma2023_balanced_good_targets` scenario is a parameterized synthetic case motivated by the long-range experiment in Ma et al. (MSSP 2023), where targets around 31 m, 33 m, 35 m, 42 m, and the selected best target around 48 m produced nearly identical target-wise displacement RMSEs after conversion-factor fitting. The scenario uses low-frequency components at 0.3 Hz, 0.5 Hz, and 1.0 Hz, five balanced high-SNR targets, and range bins `(31, 33, 35, 42, 48)` to emulate the reported multi-good-target condition. It is an informed appendix/extended-validation simulation of the reported condition, not a replay of Ma et al.'s raw IQ/phase data.

The `literature_maglev_modal_response` scenario replaces the local TDMS-driven bridge case in default validation. It uses reported maglev concrete girder vertical modal frequencies `7.7737 Hz`, `11.5742 Hz`, and `26.5642 Hz`, a quiet-start vehicle-event envelope, a `200 Hz` slow-time rate, and a normalized peak displacement of about `1.8 mm`. Finite-window nonstationarity gives broadened modal bands and spectral leakage rather than ideal single-line sinusoids. The scenario is intended as the formal literature-driven bridge-response simulation when measured radar ADC is unavailable.

The `same_range_far_angles` scenario is the formal angle-bin motivation case: all main scatterers are placed in the same range bin but with substantially different AoA values. The default paper comparison uses `range_bin_itoh` and `ma2026_reproduction` as the range-bin / single-target baselines. `range_bin_only_mixed_phase` and `ma_style_iterative_beta_range_bin` remain available under diagnostic/extended validation for mechanism analysis of mixed range-bin phases. The ADC/range-angle frontend must split the targets before selection and Kalman fusion.

## Measured Bridge Driven Scenario

`measured_bridge_point4_transverse` is an optional semi-measured diagnostic scenario, not part of default validation. It uses TDMS laser displacement from `卡3激光位移/3-4` as a provisional structural displacement reference. The raw TDMS/laser record may have a higher sampling rate, but the scenario resamples the displacement truth to the radar slow-time rate; the default radar phase/Kalman update rate is `100 Hz`, not `1000 Hz`. The laser truth is minimally processed by event-window extraction, resampling, unit conversion, and cold-start relative zeroing; it is not band-limited or power-line-notched by default. The default acceleration input is derived from a separate 0.2-30 Hz filtered copy of the laser displacement and then adds seeded accelerometer noise. Because the local TDMS channels show unresolved low-frequency/quasi-static and power-line contamination issues, this case is retained for debugging and boundary checks rather than for formal paper accuracy claims. Radar ADC/IQ/wrapped phase observations are still synthesized from the physical phase model because no measured mmWave radar ADC is available for this dataset.

## Run Tests

```bash
python3 -m unittest discover tests -v
```

## Run Full Phase-1 Validation

```bash
python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
```

This command writes the paper scenario set and paper method set. To run all appendix/diagnostic scenarios, use:

```bash
python3 -m simulation.phase1.run_validation --scenario-set all --output-dir /tmp/phase1_validation_all_scenarios
```

The local TDMS-driven semi-measured bridge scenario is excluded by default. To include it for optional diagnostics, use:

```bash
python3 -m simulation.phase1.run_validation --include-measured-bridge --output-dir /tmp/phase1_validation_with_measured_bridge
```

## Run Extended Paper Experiments

```bash
python3 -m simulation.phase1.run_extended_validation --output-dir simulation/outputs/phase1_extended_validation
```

This generates Monte Carlo, ablation, AoA sensitivity, and SNR sensitivity tables for the thesis experiment chapter.

## Inspect Scenario Parameters And Truth Signals

```bash
python3 -m simulation.phase1.run_scenario_diagnostics --output-dir simulation/outputs/phase1_scenario_diagnostics
```

This writes `scenario_parameters.csv`, `summary.md`, and per-scenario SVG plots for time-domain displacement, time-domain acceleration, displacement spectrum, and acceleration spectrum. Use `--include-measured-bridge` only when you want the optional local TDMS diagnostic set.

## Main Outputs

- `metrics.csv`: method-by-scenario RMSE/MAE/max error/phase RMSE/unwrap errors plus `selected_target_count`, `selected_indices`, `corrected_observation_count`, `unwrap_error_rate`, and `kappa_median_relative_error`.
- `feasibility_gates.json`: pass/fail feasibility checks.
- `summary.md`: readable validation summary with full-pipeline selection metrics.
- `plots/*.svg`: basic displacement plots and diagnostic figures generated without matplotlib, including vehicle-event range-angle/selection/full-pipeline comparisons.
- `phase1_extended_validation/*.csv`: paper-ready Monte Carlo, ablation, AoA sensitivity, and SNR sensitivity tables.

The single-run `.npz` output keeps the absolute synthetic truth (`q_m`, `main_phase_rad`) and also writes the cold-start relative quantities (`q_ref_m`, `delta_q_m`, `delta_main_phase_rad`) used by formal evaluation.

## Interpretation

Passing data-generation tests only means the synthetic observations are reproducible and physically shaped. Passing validation gates means the proposed method meets the current synthetic feasibility criteria. If any gate fails, report the failure and inspect the scenario instead of hiding it by tuning parameters.

This phase is intentionally algorithm-level validation with a synthetic ADC/range-angle frontend. It does not claim to parse real IWR1843 ADC files, simulate a complete bridge or maglev finite-element model, include real antenna amplitude/phase calibration, or validate field multipath. Its purpose is to check whether known displacement, independently generated radar wrapped phase/frontend slow-time observations, and independently generated accelerometer measurements can be fused by the proposed estimator.

The tests include two independence checks intended to avoid algorithm-dependent simulation:

- Radar wrapped phase is checked against the independent LoS phase equation `phi_i = kappa_i * 4*pi*q/lambda + b_i` in a near-noiseless case.
- Accelerometer synchronization error is checked against an explicit time-shift interpolation of the true acceleration.
- Quiet-start and vehicle-event tests check that the truth generator can create a stationary calibration segment followed by a nonstationary response without using any estimator output.

The proposed estimator is also tested through an algorithm-visible radar view that intentionally does not expose true `kappa`, `true_main_phase_rad`, or `true_los_phase_rad`.
