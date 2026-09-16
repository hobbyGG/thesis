# Phase 1 Simulation Validation

> **Current mainline (2026-09-14):** the default paper-facing method is `direct_aoa_fixed_beta`: local MUSIC/ML angle estimation, geometry-derived frozen beta, and structural-main-phase Kalman. The independent beta pre-calibration and online beta-bootstrap paths remain available only as explicit legacy/ablation methods. Historical outputs are in `archive/2026-09-14-pre-direct-aoa/`; regenerate validation outputs before using them as current results.

This package implements the first-stage synthetic validation for the thesis method:

- Structural truth is a multi-frequency displacement signal sampled at a slow-time frame/Kalman rate of 100 Hz. The default synthetic components are near 2 Hz, 5 Hz, and 12 Hz, keeping them below the slow-time Nyquist limit.
- Radar timing explicitly separates slow time from ADC fast time: the default Phase-1 timing profile uses 100 Hz slow-time frames, 6 MHz ADC fast-time sampling, 256 ADC samples per chirp, 60 us chirps, and 4 chirps per frame/time step.
- The truth generator can optionally scale synthetic scenarios by the final displacement peak, prepend a physically quiet calibration segment, and generate nonstationary responses by applying smooth event envelopes to the same modal components.
- Radar observations include both target-wise ablation IQ signals and a physics-shaped synthetic frontend in `frontend.py` that generates an ADC cube, applies range FFT and spatial-frequency angle processing, and extracts frontend slow-time target observations from Range-Angle peaks. The default frontend now uses `local_music_ml`: Angle-FFT supplies a coarse gate, then a calibrated joint MUSIC/variable-projection fit returns continuous target angles and reconstructs the full slow-time IQ with a fixed steering vector.
- The proposed algorithm receives only an algorithm-visible radar input view: wrapped phase, measured/AoA-derived initial `beta`, and availability masks. Truth fields such as `q_m`, true `beta`, and unwrapped LoS phase are kept outside the proposed estimator and are used only for simulation generation or evaluation.
- Evaluation is performed on displacement relative to the cold-start reference:

```text
delta_q(t) = q(t) - mean(q over cold_start_window)
delta_Theta(t) = 4*pi*delta_q(t)/lambda
```

- Validation compares baselines and the proposed multi-target structural-main-phase Kalman method.

## Package Structure

- `algorithm.py`: proposed structural-main-phase Kalman estimator, prediction-aided phase correction, calibrated `Q`, SNR-informed initial `R`, posterior-residual / quality-gated target-wise effective `R`, and independent batch `beta` pre-calibration followed by a frozen-`beta` full-record rerun.
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
- During online filtering, only the measurement noise is adapted target-wise as `R_i,k^Theta`. The thesis-method target behavior is to update the base structural-direction measurement noise from posterior residuals, modulated by a target-quality gate, and bounded by robust clipping limits. The gate prevents a large prediction innovation during strong structural response from being interpreted automatically as radar measurement noise. `beta` is frozen before this filtering pass, so its calibration uncertainty is not injected as independent frame-wise white noise.

The current main direction is direct AoA-to-beta mapping followed by a frozen-beta structural filter. The former beta-confidence and dynamic-beta paths remain explicit legacy/ablation modes and are not part of the default report. The structural filter still uses calibrated `Q` + SNR-informed initial `R` + posterior-residual / quality-gated target-wise online `R_i,k`; it should not be described as simultaneous online adaptation of both `Q` and `R`. Sliding-window `q` selection or adaptive `Q_k` is reserved for future work.

The adaptive-`R` policy is literature-guided but not copied verbatim. Akhlaghi, Zhou, and Huang's adaptive noise covariance work motivates the split in which prediction innovation is associated with process/model uncertainty while posterior residual is more appropriate for measurement-noise estimation. Mehra's adaptive filtering taxonomy motivates the covariance-matching view, and Li et al.'s redundant measurement-noise covariance estimation motivates per-channel measurement weighting. The Phase-1 thesis method adapts these ideas to mmWave radar by making `R_i,k^Theta` target-wise and gating upward `R` changes by radar target quality.

In code, `proposed_full_pipeline_aoa_fixed_beta` and `proposed_full_pipeline_beta_confidence` both implement the `Q` calibration as a candidate-grid selection over `calibrated_q_candidates`. Each candidate runs the corresponding structural-main-phase Kalman filter, and the selected `q^\star` minimizes target-level innovation energy. This calibration uses only algorithm-visible measurements and not truth RMSE; the selected `Q=q^\star Q_0` is then fixed for the reported online filtering result. If `calibrated_process_noise_intensity` is set explicitly in `Phase1Config`, that manual value is used directly.

For the AoA cold-start problem, the fixed-beta full-pipeline method keeps `beta_i` equal to the AoA-derived initial value. `proposed_full_pipeline_beta_confidence` instead performs an independent pre-pass on raw measurements before any Kalman filtering. A shared AoA-angle correction remains an auxiliary mount-bias hypothesis, while the actual target-specific path estimates a rank-1 common vibration component and one relative projection per target from the raw multi-target phase matrix. A native-timestamp ADXL regression separately estimates an absolute projection candidate and one common residual delay. Both paths use two disjoint temporal folds.

The calibrator separates two provenance-selected modes. A capture with independently validated ADXL axis, sensitivity, and fixture transfer uses `adxl_absolute`; every other capture uses `aoa_anchored_relative`. A missing validation flag is treated as unvalidated. The relative mode identifies only cross-target projection ratios from radar and fixes their otherwise-unidentifiable common scale with the original AoA values. Each temporal fold selects references using only that fold's training-block ADXL coherence; the opposite block validates the fitted candidate and never changes the training reference set. Final availability still requires at least three targets to pass both train and holdout ADXL coherence, and the first singular component must explain at least the configured fraction in both folds. Mode selection never reuses holdout scores. Global timeline, excitation, common-delay, reference-count, and shared-motion failures reject the whole calibration pass. Phase continuity, target coherence, fold consistency, bounds, relative change, uncertainty, and conditional leave-one-target-out holdout improvement are evaluated per target, so a failed target returns exactly to its own AoA beta without discarding valid corrections for other targets. Setting `beta_calibration_use_adxl=False` remains an explicit common-AoA-only experiment.

The reported relative-fit variance is a stability diagnostic, not a complete probabilistic standard error: it does not include uncertainty in the SVD direction, AoA normalization, or reference-mask selection. Rank-1 consistency proves only a shared waveform. Interpreting each coefficient as an AoA projection additionally requires the experiment to place all radar targets on the same rigidly moving radar/structure degree of freedom; target-specific scattering gain, multipath nonlinearity, radar rotation, or different modal participation are not identified by this gate. The per-fold polynomial nuisance model also removes very-low-frequency content; short calibration records therefore validate the remaining dynamic band and must not be presented as proof of quasi-static displacement scale.

After that decision, every accepted or per-target fallback `beta_i` is frozen and the existing full-pipeline Kalman filter is run again from frame 0. No current-target Kalman posterior or prediction-corrected phase is fed back into `beta`. The result records the AoA initial value, absolute and relative candidates, per-target acceptance masks/reasons, ADXL-eligible reference mask, fold rank-1/reference diagnostics, uncertainty/coherence/holdout diagnostics, common AoA correction, ADXL delay/common scale, and the frozen `beta_history` used by every frame. For schema compatibility, `beta_calibration_accepted` continues to mean that every selected target passed; partial-aware consumers use `beta_calibration_any_accepted` together with `beta_calibration_accepted_mask`. Numeric reason codes are `0=fallback`, `1=common-AoA-only accepted`, and `2=one or more target-wise candidates accepted`; the separate stage flags retain more detail.

Each target contributes:

```text
phi_i,k^LOS,corr = psi_i,k + 2*pi*round((Theta_pred/beta_hat_i + b_i - psi_i,k)/(2*pi))
```

The corrected LoS phase is used only to form the structural-direction observation during the frozen-`beta` Kalman pass; it is not a calibration input.

The default validation uses a clean paper method set. Only current paper methods and necessary ablations are registered in `method_registry.py`; old target-level or pre-beta-confidence variants are no longer part of the reportable method set.

Default paper/reference methods:

- `oracle`: relative truth upper reference.
- `range_bin_itoh`: conventional range-bin phase baseline. It selects the strongest range bin from the ADC range FFT profile, extracts the strongest virtual-RX slow-time complex value at that range bin, applies Itoh unwrapping, and converts LoS phase to structural displacement with the measured/equivalent `beta`. It does not use target-level oracle phase or true `beta`.
- `ma2026_reproduction`: Ma 2026 paper-equation baseline. The simulation wrapper uses a Range FFT range-bin candidate adapter and passes the first distance-spectrum candidate into the target-specific paper method, then runs the Ma 2026 LoS-phase Kalman stage: state `[phi, dot phi]`, acceleration input `4*pi*a/(beta*lambda)`, continuous `R=1` discretized as `R_d=R/T_a`, `Q=10^j` selected by the corrected/unwrapped measurement phase `z_corr` energy in Eq. (16), band-pass alpha fitting with `[0.5 Hz, 3 Hz]` as the paper experiment default, and Section 3.3 minimum convergence-time diagnostics. In synthetic scenarios, the alpha fit uses the available true continuous LoS phase as the corrected/unwrapped radar phase input; if that oracle calibration phase cannot be uniquely attached to a range-bin candidate, the wrapper falls back to ordinary wrapped-phase unwrapping as an input adapter. It does not run beta-grid target selection. The scenario adapter may raise the alpha-fit upper cutoff to cover configured structural frequencies, following the paper's cutoff rule. It does not use the Range-Angle frontend or angle-bin target selection.
- `selected_aoa_fixed_beta`: frontend-selected targets with AoA initial `beta` fixed, used as the selected-target fixed-geometry baseline.
- `proposed_full_pipeline_aoa_fixed_beta`: the full pipeline with innovation-energy-selected global `Q`, SNR-informed initial `R_i,0^Theta`, posterior-residual / quality-gated target-wise effective `R_i,k^Theta`, and fixed AoA-derived `beta_i`.
- `proposed_full_pipeline_beta_confidence`: the same filtering pipeline, preceded by fail-closed independent `beta` pre-calibration and followed by a full-record run with the accepted or fallback `beta_i` frozen. This is the current Phase 1 calibration method.

Explicit ablation methods:

- `range_bin_only_mixed_phase`: range-bin-only mixed phase Kalman ablation that uses the same range-FFT range-bin observation as a single pseudo-target. It is retained for same-range far-angle mechanism analysis, but is not part of the default paper method set.
- `multitarget_aoa_fixed_beta`: all-target AoA-fixed ablation without frontend selection.

The default paper scenario set is deliberately small. It contains five scenarios: `literature_maglev_modal_response`, `strong_wrapping`, `same_range_far_angles`, `aoa_error_bootstrap`, and `target_snr_drop`. The registered diagnostic set additionally contains literature/angle-resolution and robustness checks: `literature_mmwbats_same_range_aliasing`, `literature_mmshm_adjacent_range_clutter`, `mixed_scatterer_rangebin`, and `low_snr_multitarget`.

Default synthetic scenarios are normalized by the generated truth peak displacement rather than by component amplitudes alone. Regular synthetic cases now use a cold-start ramp profile: 0-0.2 s is quiet, 0.2-0.8 s is a weak calibration vibration of roughly 0.05-0.20 mm, 0.8-1.4 s smoothly grows toward the main response, and the later interval reaches the scenario peak of about `1.5 mm`. `strong_wrapping` keeps a stronger cold-start/micro-vibration/ramp/strong-response/decay profile and targets about `5.0 mm` peak displacement. This makes the wrapping scenario cross multiple radar phase periods for a 77 GHz carrier while keeping the other scenarios in a realistic millimeter-level response range.

`sample_rate_hz` is always the slow-time phase/frame/Kalman sampling rate. It is not the ADC sampling rate. ADC fast-time parameters are represented separately by `adc_sample_rate_hz`, `adc_samples_per_chirp`, `chirp_duration_s`, and `chirps_per_frame`. The synthetic ADC cube is therefore suitable for algorithm-level frontend validation, but it is not a parser or replay of real IWR1843 raw ADC files.

In the synthetic frontend, `target_snr_db` is calibrated at the target observation level: each scatterer's slow-time complex IQ is perturbed before ADC cube synthesis, so range/angle FFT processing does not artificially convert a configured target SNR into a much higher post-FFT SNR. ADC background noise is still added to keep the Range-Angle Map background non-degenerate, but it is not the primary definition of target quality.

The `literature_maglev_modal_response` scenario replaces the local TDMS-driven bridge case in default validation. It uses reported maglev concrete girder vertical modal frequencies `7.7737 Hz`, `11.5742 Hz`, and `26.5642 Hz`, a quiet-start vehicle-event envelope, a `200 Hz` slow-time rate, and a normalized peak displacement of about `1.8 mm`. Finite-window nonstationarity gives broadened modal bands and spectral leakage rather than ideal single-line sinusoids. The scenario is intended as the formal literature-driven bridge-response simulation when measured radar ADC is unavailable.

The `same_range_far_angles` scenario is the formal angle-bin motivation case: all main scatterers are placed in the same range bin but with substantially different AoA values. The default paper comparison uses `range_bin_itoh` and `ma2026_reproduction` as the range-bin / single-target baselines. `range_bin_only_mixed_phase` remains available under diagnostic/extended validation for mechanism analysis of mixed range-bin phases. The ADC/range-angle frontend must split the targets before selection and Kalman fusion.

## Capture-Compatible Maglev Beam Full Flow

The capture-based simulation has exactly one supported scene: the magnetic-
levitation track-beam event in `datafile/20250320test12.tdms`, laser channel
`卡3激光位移/3-4`, from 15.33 s to 19.33 s. The dedicated command has no
scenario selector:

```bash
python3 -m venv .venv-sim
.venv-sim/bin/python -m pip install -e capture_program nptdms
PYTHONPATH=capture_program/src \
  .venv-sim/bin/python -m \
  simulation.phase1.run_maglev_capture_simulation \
  --output /tmp/maglev_capture_sim --run-algorithm
```

The first two lines are one-time environment setup; subsequent runs only need
the `PYTHONPATH=...` command.

This path generates the same stable radar and ADXL algorithm-input arrays used
by the offline capture reader, then runs the ordinary asynchronous fusion
algorithm. Its fixed contract is:

- measured input: the raw TDMS laser-voltage waveform only;
- derived input: relative displacement using the explicitly uncalibrated
  provisional scale `1 V = 1 mm`, and X-axis acceleration obtained by an FFT
  second derivative;
- synthetic input: radar ADC/IQ, the two other ADXL axes, sensor noise, and all
  timestamps;
- error boundary: the laser-derived physical displacement/acceleration is built
  first, then all stochastic sensor errors and quantization are applied exactly
  once by the capture-package writer. Loading the package, target detection,
  asynchronous preintegration, and fusion are deterministic and never add a
  second artificial noise layer;
- ADXL355 profile: the calibrated-25-degC typical profile injects the Rev. D
  `22.5 ug/sqrt(Hz)` noise-density model using a documented 250 Hz rectangular
  ENBW engineering approximation, followed by 20-bit quantization. Offset,
  sensitivity tolerance, cross-axis sensitivity, nonlinearity, temperature
  drift, and the 1.78 ms digital-filter delay are recorded but not injected.
  The synthetic timeline declares the group delay uncalibrated; strict real
  fusion must measure and compensate it;
- radar/DCA profile: one common complex receiver-AWGN layer is applied before
  signed 12-bit I/Q quantization. Target SNR values are scenario/link-budget
  assumptions rather than values derived from the IWR1843 noise figure alone.
  DCA1000 adds no analog noise; incomplete or inconsistent packet transport is
  an integrity failure rather than a stochastic measurement model;
- rates: 100 Hz externally triggered radar frames and a separate 1 kHz ADXL
  schedule. The nested radar export retains the CFG's 9 ms minimum/nominal
  schedule, while fusion uses the root package's actual 10 ms trigger schedule;
- radar template: 2 TX, 16 loops/32 physical chirps, 8 azimuth virtual
  channels, 256 ADC samples, 5.209 MHz ADC sampling, 57.14 us ramp, and 70 us
  idle time;
- signal preparation: the approximately 3 kHz laser source is limited to
  0.2-40 Hz before either output rate is formed;
- chirp behavior: the 16 loops use their actual within-frame loop-start times
  and independent synthetic receiver noise, then `adc_cube` is their coherent
  mean. Its effective radar observation timestamp is the center of that
  coherent aperture, exactly 1.9071 ms after the synthetic trigger reference;
  this is a model-derived timestamp, not a measured ADC timestamp. TX0-to-TX2
  skew inside one virtual-array observation is not modeled and no TDM motion
  compensation is claimed;
- evaluation reference: both the estimator and stored displacement RMSE use
  the same 0.20 s cold-start mean. The result file retains the absolute derived
  laser displacement, the cold-start reference, and the relative truth used by
  the RMSE;
- estimator default: capture runs use measured-AoA `fixed_beta`, innovation-
  selected fixed `Q`, posterior-residual `R`, and a measured-map `-20 dB`
  candidate gate capped at 12 candidates. `adaptive_beta` invokes the independent
  pre-calibration path described above. A global failure produces the fixed-AoA
  result; a target-specific failure falls back only that target and is recorded
  explicitly in the result diagnostics.

No PCAP, DCA1000 Ethernet receive timing, GPIO edge, or physical DRDY event is
fabricated. The package is marked `simulation_ready`, never `algorithm_ready`,
`fusion_ready`, or hardware validated. Generic capture loading rejects it by
default; only explicit `--allow-simulation` or the dedicated command permits
it. The stored truth is used after estimation for RMSE evaluation and is not
exposed to target detection or the estimator. Both the radar-grid displacement
reference and 1 kHz laser-derived acceleration reference are retained for
evaluation. Their RMSE values are semi-measured mechanism/sensor-simulation
errors, not measured radar/ADXL accuracy.

The focused regression evaluates five deterministic hardware-noise seeds and
requires every 4 s run to remain below `0.01 mm` displacement RMSE. This is a
numerical acceptance criterion for this one provisional-scale magnetic-
levitation waveform, not an accuracy guarantee for real hardware. Real results
still depend on fixture geometry, AoA/channel/range calibration, ADXL axis and
group-delay calibration, received power/multipath, actual timestamps, and a
calibrated laser voltage-to-displacement scale.

The older multi-scenario Phase-1 framework remains available for algorithm
ablation and literature comparisons, but it is not part of this
capture-compatible full-flow command.

## Legacy Algorithm-Level Measured Bridge Scenario

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

### Run the complete offline fusion path

For a synchronized hardware capture, run the acquisition-independent algorithm
from the repository root:

```bash
PYTHONPATH=capture_program/src \
  capture_program/.venv/bin/python -m simulation.phase1.run_captured \
  example_synchronized_dataset/capture_00000/synchronized \
  --method adaptive_beta --adxl-axis x --adxl-sign 1
```

Choose `x`, `y`, or `z` to match the ADXL355 structural-motion direction. The
sign must match the positive radar/structural displacement direction; use
`--adxl-sign -1` when the selected sensor axis points the other way. The
default operational gate accepts Pi-controlled `SYNC_IN` captures referenced by
GPIO SET completion; a GPIO24 loopback is optional. Radar frames and ADXL355
samples keep their separate native `CLOCK_MONOTONIC` timelines. The adapter
preintegrates every ADXL interval over the actual radar intervals, so unequal
or slightly nonuniform sample rates do not need matching timestamps or an
acquisition-time resample. When native ADXL calibration is requested, every
preintegrated interval must also carry `radar_start_time_ns` and
`radar_end_time_ns` that exactly match the radar frame timeline; missing or
mismatched anchors reject beta calibration rather than silently aligning it.

Without a validated fixture calibration, the runner uses the selected ADXL axis,
raw radar channels, nominal half-wavelength virtual-array spacing, and zero
range bias. Those assumptions are written as warnings in the result summary.
In this mode `adaptive_beta` requests `aoa_anchored_relative`, because an
uncalibrated ADXL gain must not be mistaken for the same beta shift on every
target. A validated value/geometry calibration instead selects
`adxl_absolute` before fitting; holdout results never choose between modes.
Use `--require-calibrated` to reject nominal assumptions and require the
stricter calibrated `fusion_ready` contract.

The command writes each of these files through an atomic replacement:

- `algorithm/phase1_result.npz`: native timestamps, estimated displacement and
  phase states, target bins/angles, frozen beta, beta-calibration numeric
  diagnostics, and ADXL interval preintegration.
- `algorithm/phase1_result.json`: method, readiness levels, timing/calibration
  modes, warnings, sample counts, provenance, selected scale mode, per-target
  acceptance mask/count, and readable beta-calibration rejection reasons.

Use `--range-bins` together with `--angle-bins` to override automatic target
detection. `--method adaptive_beta` selects the current fail-closed
pre-calibration pipeline; the CLI retains `fixed_beta` as its conservative
default until real-fixture calibration thresholds are validated. Use
`--method fixed_beta` explicitly for the fixed-geometry ablation, and
`--overwrite` only when deliberately replacing an existing algorithm result.

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
