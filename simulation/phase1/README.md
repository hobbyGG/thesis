# Phase 1 Simulation Validation

This package implements the first-stage synthetic validation for the thesis method:

- Structural truth is a multi-frequency displacement signal sampled at a slow-time frame/Kalman rate of 100 Hz. The default synthetic components are near 2 Hz, 5 Hz, and 12 Hz, keeping them below the slow-time Nyquist limit.
- Radar timing explicitly separates slow time from ADC fast time: the default Phase-1 timing profile uses 100 Hz slow-time frames, 6 MHz ADC fast-time sampling, 256 ADC samples per chirp, 60 us chirps, and 4 chirps per frame/time step.
- The truth generator can optionally scale synthetic scenarios by the final displacement peak, prepend a physically quiet calibration segment, and generate nonstationary responses by applying smooth event envelopes to the same modal components.
- Radar observations include both target-wise ablation IQ signals and a physics-shaped synthetic frontend in `frontend.py` that generates an ADC cube, applies range FFT and spatial-frequency angle FFT, and extracts frontend slow-time target observations from Range-Angle peaks.
- The proposed algorithm receives only an algorithm-visible radar input view: wrapped phase, measured/AoA-derived initial `beta`, and availability masks. Truth fields such as `q_m`, true `beta`, and unwrapped LoS phase are kept outside the proposed estimator and are used only for simulation generation or evaluation.
- Evaluation is performed on displacement relative to the cold-start reference:

```text
delta_q(t) = q(t) - mean(q over cold_start_window)
delta_Theta(t) = 4*pi*delta_q(t)/lambda
```

- Validation compares baselines and the proposed multi-target structural-main-phase Kalman method.

## Package Structure

- `algorithm.py`: proposed structural-main-phase Kalman estimator, prediction-aided phase correction, calibrated `Q`, SNR-informed initial `R`, posterior-residual / quality-gated confidence-aware target-wise effective `R`, and online `beta` bootstrap.
- `baselines.py`: oracle, range-bin Itoh, selected-target fixed-beta, all-target AoA fixed-beta, and range-bin-only mixed-phase baselines.
- `ma2026/`: dedicated reproduction package for the formal Ma 2026 baseline. It separates the paper target-specific LoS-phase Kalman method from the simulation-only range-bin candidate adapter.
- `scenario_inputs.py`: the unified scenario input builder. It turns one `Phase1Config` into named data views: truth, accelerometer, target-level radar, frontend/range-angle outputs, selected frontend radar input, range-bin-only input, and Ma2026 range-bin input.
- `method_registry.py`: the central method list. Add comparison methods here instead of hard-coding calls inside the pipeline.
- `pipeline.py`: thin orchestration only: build scenario inputs, run registered methods, convert results to metric rows, and return artifacts.
- `evaluation.py` and `gates.py`: metric row construction and feasibility gate definitions.
- `scenarios/`: one module per synthetic validation scenario. `scenarios.build_phase1_scenarios()` returns the clean paper scenario set, while `scenarios.build_all_phase1_scenarios()` returns sanity, appendix, robustness, and diagnostic scenarios as well.
- `inputs.py`: backward-compatible re-export layer for older scenario-input imports.
- `capture_reader.py`: loads the acquisition program's stable algorithm-input
  schema into `ADCCubeObservation` and `FrontendConfig`; it does not parse raw
  PCAP, LVDS, or radar configuration data.
- `methods.py`: compatibility re-export layer used by low-level tests and older notebooks; paper method selection is controlled by `method_registry.py`.

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
- During online filtering, only the measurement noise is adapted target-wise as `R_i,k^Theta`. The thesis-method target behavior is to update the base structural-direction measurement noise from posterior residuals, modulated by a target-quality gate, and bounded by robust clipping limits. The gate prevents a large prediction innovation during strong structural response from being interpreted automatically as radar measurement noise. Because the full pipeline starts from AoA-derived conversion coefficients, the effective observation noise also includes a small `beta`-confidence term that propagates current conversion-coefficient uncertainty into `R_i,k^Theta`.

This means the current algorithmic direction is calibrated `Q` + SNR-informed initial `R` + posterior-residual / quality-gated confidence-aware target-wise online `R_i,k`. It should not be described as simultaneous online adaptation of both `Q` and `R`. Sliding-window `q` selection or adaptive `Q_k` is reserved for future work and is not part of the present main method.

The adaptive-`R` policy is literature-guided but not copied verbatim. Akhlaghi, Zhou, and Huang's adaptive noise covariance work motivates the split in which prediction innovation is associated with process/model uncertainty while posterior residual is more appropriate for measurement-noise estimation. Mehra's adaptive filtering taxonomy motivates the covariance-matching view, and Li et al.'s redundant measurement-noise covariance estimation motivates per-channel measurement weighting. The Phase-1 thesis method adapts these ideas to mmWave radar by making `R_i,k^Theta` target-wise, gating upward `R` changes by radar target quality, and adding the `beta`-confidence term required by AoA cold start and online conversion-coefficient bootstrap.

In code, `proposed_full_pipeline_aoa_fixed_beta` and `proposed_full_pipeline_beta_confidence` both implement the `Q` calibration as a candidate-grid selection over `calibrated_q_candidates`. Each candidate runs the corresponding structural-main-phase Kalman filter, and the selected `q^\star` minimizes target-level innovation energy. This calibration uses only algorithm-visible measurements and not truth RMSE; the selected `Q=q^\star Q_0` is then fixed for the reported online filtering result. If `calibrated_process_noise_intensity` is set explicitly in `Phase1Config`, that manual value is used directly.

For the AoA cold-start problem, the fixed-beta full-pipeline method keeps `beta_i` equal to the AoA-derived initial value and disables online `beta` updates. The beta-bootstrap full-pipeline method starts from the same AoA value and enables online `beta` bootstrap. Both methods keep the same calibrated `Q`, selected frontend targets, target-wise adaptive base `R^Theta`, and an observation-model uncertainty term propagated from the current `beta_i` variance:

```text
R_i,k^Theta = R_base_i,k^Theta + (phi_i,k^LOS,corr - b_i)^2 * sigma_beta_i,k^2
```

The extra term is large when the AoA-derived conversion coefficient is still uncertain. In `proposed_full_pipeline_aoa_fixed_beta`, `beta_i` remains fixed, so this uncertainty is not reduced by an online fit. In `proposed_full_pipeline_beta_confidence`, the uncertainty can decay as the short-window `beta_i` bootstrap becomes confident. Its diagnostics are reported as `base_r_theta_history`, `base_r_update_gate_history`, `target_quality_history`, `beta_variance_history`, and `beta_uncertainty_r_theta_history`. This is an implementation support for the AoA cold-start and online bootstrap loop, not a separate thesis contribution.

Each target contributes:

```text
phi_i,k^LOS,corr = psi_i,k + 2*pi*round((Theta_pred/beta_hat_i + b_i - psi_i,k)/(2*pi))
```

The same LoS corrected phase is first converted to a structural-direction observation and is also used for online `beta_i` bootstrap.

The default validation uses a clean paper method set. Only current paper methods and necessary ablations are registered in `method_registry.py`; old target-level or pre-beta-confidence variants are no longer part of the reportable method set.

Default paper/reference methods:

- `oracle`: relative truth upper reference.
- `range_bin_itoh`: conventional range-bin phase baseline. It selects the strongest range bin from the ADC range FFT profile, extracts the strongest virtual-RX slow-time complex value at that range bin, applies Itoh unwrapping, and converts LoS phase to structural displacement with the measured/equivalent `beta`. It does not use target-level oracle phase or true `beta`.
- `ma2026_reproduction`: Ma 2026 paper-equation baseline. The simulation wrapper uses a Range FFT range-bin candidate adapter and passes the first distance-spectrum candidate into the target-specific paper method, then runs the Ma 2026 LoS-phase Kalman stage: state `[phi, dot phi]`, acceleration input `4*pi*a/(beta*lambda)`, continuous `R=1` discretized as `R_d=R/T_a`, `Q=10^j` selected by the corrected/unwrapped measurement phase `z_corr` energy in Eq. (16), band-pass alpha fitting with `[0.5 Hz, 3 Hz]` as the paper experiment default, and Section 3.3 minimum convergence-time diagnostics. In synthetic scenarios, the alpha fit uses the available true continuous LoS phase as the corrected/unwrapped radar phase input; if that oracle calibration phase cannot be uniquely attached to a range-bin candidate, the wrapper falls back to ordinary wrapped-phase unwrapping as an input adapter. It does not run beta-grid target selection. The scenario adapter may raise the alpha-fit upper cutoff to cover configured structural frequencies, following the paper's cutoff rule. It does not use the Range-Angle frontend or angle-bin target selection.
- `selected_aoa_fixed_beta`: frontend-selected targets with AoA initial `beta` fixed, used as the selected-target fixed-geometry baseline.
- `proposed_full_pipeline_aoa_fixed_beta`: the full pipeline with innovation-energy-selected global `Q`, SNR-informed initial `R_i,0^Theta`, posterior-residual / quality-gated confidence-aware target-wise effective `R_i,k^Theta`, and fixed AoA-derived `beta_i`. This isolates the effect of removing the online beta closed loop while keeping the rest of the full pipeline.
- `proposed_full_pipeline_beta_confidence`: the full pipeline with innovation-energy-selected global `Q`, SNR-informed initial `R_i,0^Theta`, posterior-residual / quality-gated confidence-aware target-wise effective `R_i,k^Theta`, and online `beta` bootstrap. This is the current Phase 1 beta-bootstrap method.

Explicit ablation methods:

- `range_bin_only_mixed_phase`: range-bin-only mixed phase Kalman ablation that uses the same range-FFT range-bin observation as a single pseudo-target. It is retained for same-range far-angle mechanism analysis, but is not part of the default paper method set.
- `multitarget_aoa_fixed_beta`: all-target AoA-fixed ablation without frontend selection.

The default paper scenario set is deliberately small. It contains five scenarios: `literature_maglev_modal_response`, `strong_wrapping`, `same_range_far_angles`, `aoa_error_bootstrap`, and `target_snr_drop`. The registered diagnostic set additionally contains literature/angle-resolution and robustness checks: `literature_mmwbats_same_range_aliasing`, `literature_mmshm_adjacent_range_clutter`, `mixed_scatterer_rangebin`, and `low_snr_multitarget`.

Default synthetic scenarios are normalized by the generated truth peak displacement rather than by component amplitudes alone. Regular synthetic cases now use a cold-start ramp profile: 0-0.2 s is quiet, 0.2-0.8 s is a weak bootstrap vibration of roughly 0.05-0.20 mm, 0.8-1.4 s smoothly grows toward the main response, and the later interval reaches the scenario peak of about `1.5 mm`. `strong_wrapping` keeps a stronger cold-start/micro-vibration/ramp/strong-response/decay profile and targets about `5.0 mm` peak displacement. This makes the wrapping scenario cross multiple radar phase periods for a 77 GHz carrier while keeping the other scenarios in a realistic millimeter-level response range.

`sample_rate_hz` is always the slow-time phase/frame/Kalman sampling rate. It is not the ADC sampling rate. ADC fast-time parameters are represented separately by `adc_sample_rate_hz`, `adc_samples_per_chirp`, `chirp_duration_s`, and `chirps_per_frame`. The synthetic ADC cube is therefore suitable for algorithm-level frontend validation, but it is not a parser or replay of real IWR1843 raw ADC files.

In the synthetic frontend, `target_snr_db` is calibrated at the target observation level: each scatterer's slow-time complex IQ is perturbed before ADC cube synthesis, so range/angle FFT processing does not artificially convert a configured target SNR into a much higher post-FFT SNR. ADC background noise is still added to keep the Range-Angle Map background non-degenerate, but it is not the primary definition of target quality.

The `literature_maglev_modal_response` scenario replaces the local TDMS-driven bridge case in default validation. It uses reported maglev concrete girder vertical modal frequencies `7.7737 Hz`, `11.5742 Hz`, and `26.5642 Hz`, a quiet-start vehicle-event envelope, a `200 Hz` slow-time rate, and a normalized peak displacement of about `1.8 mm`. Finite-window nonstationarity gives broadened modal bands and spectral leakage rather than ideal single-line sinusoids. The scenario is intended as the formal literature-driven bridge-response simulation when measured radar ADC is unavailable.

The `same_range_far_angles` scenario is the formal angle-bin motivation case: all main scatterers are placed in the same range bin but with substantially different AoA values. The default paper comparison uses `range_bin_itoh` and `ma2026_reproduction` as the range-bin / single-target baselines. `range_bin_only_mixed_phase` remains available under diagnostic/extended validation for mechanism analysis of mixed range-bin phases. The ADC/range-angle frontend must split the targets before selection and Kalman fusion.

## Measured Bridge Driven Scenario

`measured_bridge_point4_transverse` is an optional semi-measured diagnostic scenario, not part of default validation. It uses TDMS laser displacement from `卡3激光位移/3-4` as a provisional structural displacement reference. The raw TDMS/laser record may have a higher sampling rate, but the scenario resamples the displacement truth to the radar slow-time rate; the default radar phase/Kalman update rate is `100 Hz`, not `1000 Hz`. The laser truth is minimally processed by event-window extraction, resampling, unit conversion, and cold-start relative zeroing; it is not band-limited or power-line-notched by default. The default acceleration input is derived from a separate 0.2-30 Hz filtered copy of the laser displacement and then adds seeded accelerometer noise. Because the local TDMS channels show unresolved low-frequency/quasi-static and power-line contamination issues, this case is retained for debugging and boundary checks rather than for formal paper accuracy claims. Radar ADC/IQ/wrapped phase observations are still synthesized from the physical phase model because no measured mmWave radar ADC is available for this dataset.

## Load a Real Radar Capture

The capture program publishes the exact three-dimensional ADC cube expected by
the Phase-1 frontend. The algorithm-side reader only consumes that stable
schema:

```python
from simulation.phase1.capture_reader import load_captured_frontend_input
from simulation.phase1.frontend import range_angle_process

captured = load_captured_frontend_input(
    "example_dataset/capture_00000/iwr1843"
)
range_angle = range_angle_process(captured.adc, captured.frontend_config)
```

The returned `frame_times_s` and frontend configuration come from the captured
radar timing. They must be used instead of assuming the synthetic scenario's
default slow-time sample rate.

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

- `metrics.csv`: method-by-scenario RMSE/MAE/max error/phase RMSE/unwrap errors plus `selected_target_count`, `selected_indices`, `corrected_observation_count`, `unwrap_error_rate`, and `beta_median_relative_error`.
- `feasibility_gates.json`: pass/fail feasibility checks.
- `summary.md`: readable validation summary with full-pipeline selection metrics.
- `plots/*.svg`: basic displacement plots and diagnostic figures generated without matplotlib, including vehicle-event range-angle/selection/full-pipeline comparisons.
- `phase1_extended_validation/*.csv`: paper-ready Monte Carlo, ablation, AoA sensitivity, and SNR sensitivity tables.

The single-run `.npz` output keeps the absolute synthetic truth (`q_m`, `main_phase_rad`) and also writes the cold-start relative quantities (`q_ref_m`, `delta_q_m`, `delta_main_phase_rad`) used by formal evaluation.

## Interpretation

Passing data-generation tests only means the synthetic observations are reproducible and physically shaped. Passing validation gates means the proposed method meets the current synthetic feasibility criteria. If any gate fails, report the failure and inspect the scenario instead of hiding it by tuning parameters.

This phase remains algorithm-level validation with a synthetic ADC/range-angle frontend. The separate `capture_program` package now parses and standardizes real IWR1843/DCA1000 ADC captures, and `capture_reader.py` can load that stable schema, but the synthetic validation results do not by themselves claim real antenna amplitude/phase calibration, a complete bridge or maglev finite-element model, or field-multipath validation. Their purpose is to check whether known displacement, independently generated radar wrapped phase/frontend slow-time observations, and independently generated accelerometer measurements can be fused by the proposed estimator.

The tests include two independence checks intended to avoid algorithm-dependent simulation:

- Radar wrapped phase is checked against the independent LoS phase equation `phi_i^LOS = (4*pi*q/lambda)/beta_i + b_i` in a near-noiseless case.
- Accelerometer synchronization error is checked against an explicit time-shift interpolation of the true acceleration.
- Quiet-start and vehicle-event tests check that the truth generator can create a stationary calibration segment followed by a nonstationary response without using any estimator output.

The proposed estimator is also tested through an algorithm-visible radar view that intentionally does not expose true `beta`, `true_main_phase_rad`, or `true_los_phase_rad`.
