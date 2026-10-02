# Manuscript plan: five-day SCI2 submission

## 1. One-sentence paper story

A structure-mounted (inverted) FMCW radar can use range–angle-separated environmental returns as multiple line-of-sight observations, normalize them with calibration-frozen AoA geometry, and combine them with native-timestamp accelerometer pre-integration in a shared structural-phase Kalman filter; the strongest current evidence is a reproducible, guard-fenced synthetic evaluation, while fusion gains, quality-gate benefit, range-only comparisons, and field accuracy remain unproven.

## 2. Recommended title

**Range–Angle Multi-Target FMCW Radar–Accelerometer Fusion with Calibration-Frozen Geometry: An Evidence-Bounded Simulation Study**

Acceptable shorter alternative: **Range–Angle Multi-Target and Asynchronous Accelerometer Fusion for Structural Phase Tracking with an Inverted FMCW Radar**. The title refers to frozen geometry/selection, not a fully calibration-initialized Kalman state. Avoid “field validation,” “sub-10-µm accuracy,” “RA superiority,” or “causal fusion” in the title.

## 3. Abstract claim skeleton

- **Problem.** A radar that moves with a structure cannot rely on a dedicated fixed target; environmental returns have different angles, wrapped phase, and unequal quality. Accelerometers provide dynamic constraints but drift after double integration.
- **Gap.** Prior radar–accelerometer displacement studies commonly select one best target or switch among targets, while range–angle studies generally output target-wise traces. Acceleration-aided phase Kalman methods commonly assume a separately estimated line-of-sight conversion factor. The present study combines target-level range–angle geometry with a common structural phase state.
- **Method.** Detect range–angle candidates, refine local AoA with MUSIC/ML, compute target-wise `beta_i = 1/|cos(theta_i)|`, and freeze geometry/selection before the test window. Integrate ADXL355 data on its native timestamp axis over each radar interval and use it to predict a shared `[Theta, Theta_dot]` state. Correct wrapped target phases near the prediction and adapt target-wise measurement noise `R_i` from residuals.
- **Evaluation.** Use truth-free estimator copies of the A20-parameterized synthetic capture package. The principal protocol has 400 radar frames (frames 0–199 calibration; 200–399 frozen test), five displacement-RMS strata, and 40 seeds (200 trials total); guards are frozen before test scoring.
- **Results.** The strict P1 route accepted 191/200 trials (95.5%); the other nine abstained on a frozen-test acceleration guard. Pooled accepted-only frozen-test RMSE was **1.355 µm** (mean of accepted trial RMSEs: 1.324 µm). This is conditional on guard acceptance and a fresh test-window Kalman cold start, and is synthetic evidence rather than field accuracy. In a separate post-warm-up P3 follow-up (frames 220–399 scored; six trials), the common-state route had lower RMSE than the selected single target in all rows, with descriptive reductions of **7.4–27.3%**; common-route innovation pairwise medians were about **0.59–0.62**, so weight diversity (`N_eff` about 4.77–4.92) is not an independent-target count.
- **Boundary.** A 10-trial P2 gate smoke accepted six trials, but all ten ungated trials already met the 10-µm criterion; no gate benefit is claimed. The planned RO-all-channel estimator is absent, so no RA-versus-RO result is reported. No causal fusion, calibrated uncertainty, 0.01-mm field-accuracy, or deployment claim is made.

## 4. Literature anchors and defensible gap wording

Use four compact literature groups rather than a long catalog:

1. **Radar–accelerometer displacement baselines.** Ma, Choi and Sohn (MSSP 2023) select a best environmental target, estimate a direction-conversion factor from a short synchronized segment, and combine radar and acceleration through complementary filtering. Follow-up work (MSSP 2023; MSSP 2025) retains multiple good targets mainly for occlusion detection, switching, and recovery, rather than simultaneous common-state updates.
2. **Range–angle phase sensing.** mmWBat (Research 2021) and mmSHM/full-field range–angle work (MSSP 2022 and 2025) separate targets in range–angle space and track each target’s phase. They support target-level spatial separation but generally report target-wise outputs or multi-LOS reconstruction, not one shared structural phase state for a single co-moving radar.
3. **Acceleration-aided phase Kalman.** Ma et al. (MSSP 2026) establish the acceleration-predicted wrapped-phase Kalman pattern; their workflow still assumes a separately estimated conversion factor. Present work should be described as an integration/operating-geometry extension, not as a new Kalman principle.
4. **Multi-LOS geometry.** Multimonostatic and full-field microwave studies reconstruct vector displacement from multiple radar stations/LOS. They motivate geometric normalization but are not a direct baseline for one inverted radar observing environmental scatterers.

Safe gap sentence: “Prior studies provide the ingredients separately—best-target or occlusion-oriented radar–accelerometer fusion, range–angle target-wise phase tracking, and acceleration-aided phase Kalman filtering. This study evaluates their combination for a single structure-mounted radar with multiple environmental reference directions, using a calibration-frozen geometry fence.” Avoid “first,” “never previously,” and “solves the field problem” unless a fresh systematic review supports those claims.

## 5. Contributions ranked by evidence

| Rank | Contribution to present as | Evidence level and safe wording | Do not claim |
|---|---|---|---|
| 1 (strongest) | **Calibration-frozen range–angle reference construction.** Range–angle peaks are separated/merged at target level; local AoA/MUSIC-ML produces continuous angles; target selection and `beta_i` are frozen from frames 0–199, then fixed-angle projection is used on frames 200–399. | The 200-trial P1 matrix executed this route with 191 accepted trials. A test-only ADC perturbation changed test observations while leaving every frozen geometry field unchanged. Claim a reproducible geometry fence and a valid synthetic execution boundary. | Do not call this proof of absolute beta accuracy, online re-association, or real-time deployment. The beta formula depends on array calibration, angle convention, mounting, and structure-direction assumptions. |
| 2 | **Native-time acceleration prediction plus shared structural-phase Kalman.** Each target is mapped to the same structural phase; interval pre-integrated acceleration drives prediction; all available targets update one state with target-wise adaptive `R_i`. | The six-row P3 tail-window follow-up (two seeds × three strata, frames 220–399 scored) shows common-vs-single reductions of 7.4–27.3%. Present this as a descriptive implementation observation; disclose correlated innovations and shared initialization. | Do not claim causal superiority, independent observations, calibrated uncertainty, or a general accuracy improvement over any baseline. |
| 3 (engineering/reproducibility) | **A unified truth-free capture contract and explicit guard/abstention accounting.** The same radar/ADXL/sync package feeds simulation and acquisition paths; truth is post-run only; acceptance, abstention, guard failures, and coverage are reported separately. | P1 records 95.5% accepted coverage with all nine rejects identified as acceleration-guard failures. The P2 smoke exposes that a development gate can abstain without improving accuracy. Frame this as auditability and reproducibility, not a new estimator theorem. | Do not claim that the P2 gate improves discrimination or accuracy, or that accepted-only metrics represent unconditional performance. |

## 6. Planned experiment and result tables

### Table 1 — Data and protocol (Methods)

| Item | Fixed value / description | Reporting rule |
|---|---|---|
| Synthetic source | A20-parameterized response; 24.768-m beam, 300 km/h, 4 s; IWR1843-like 77-GHz chain and ADXL355-like 1-kHz stream | State all response, RCS/noise, multipath, delay, and modal-participation assumptions; call it parameterized simulation, not a field dataset |
| Main fence | 400 radar frames at 100 Hz; frames 0–199 calibration, 200–399 test; 4000 ADXL samples with corresponding 2000/2000 fence | Geometry/selection/beta frozen before test; truth and `q_proxy` removed from estimator copies |
| Motion strata | stationary, 0.005, 0.010, 0.020, 0.050 mm requested `q_true` RMS | Explain that requested RMS labels describe the generator and are not an accuracy guarantee |
| Primary metric | Frozen-test RMSE; report coverage, abstention rate, all-trial success and accepted-only RMSE separately | Never replace all-trial accounting with accepted-only RMSE |

### Table 2 — Strict P1 matrix (main quantitative table)

Report the following exact values from `spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/full/summary.json`:

- 200 trials; 191 accepted; 9 abstentions; coverage/all-trial success **0.955**
- All 9 abstentions: `frozen_test_guard:acceleration_within_frozen_limit=false`
- Pooled accepted-only RMSE **0.001355051626 mm = 1.355051626 µm**
- Mean of accepted-trial RMSEs **1.324237986 µm**
- By-stratum accepted-trial mean RMSE (µm): stationary **1.133863**; 0.005 mm **1.146075**; 0.010 mm **1.176332**; 0.020 mm **1.285453**; 0.050 mm **1.865231**
- Accepted-only minimum/maximum trial RMSE: **0.967618–1.989449 µm**
- Report 9 rejected trials as abstentions before estimator execution; their missing counterfactual estimates make selection bias unquantifiable from retained outputs.

Use a sentence such as: “Under the declared synthetic protocol, the strict calibration-frozen route completed 191 of 200 trials; pooled RMSE among guard-accepted trials was 1.355 µm. This conditional result includes a fresh retained Kalman cold start on the test half and does not establish unconditional or field accuracy.”

### Table 3 — P3 common-state ablation (secondary/descriptive table)

Use the six post-warm-up rows from `spatial_recovery_rebuilt/p3_fusion_docs/strict_followup/STRICT_FOLLOWUP_PROTOCOL.md`; score frames 220–399 after frames 200–219 warm-start bias/`R` initialization:

| Stratum / seed | Single RMSE (µm) | Common RMSE (µm) | Reduction vs single |
|---|---:|---:|---:|
| stationary / 20261001 | 1.510 | 1.098 | 27.3% |
| stationary / 20261002 | 1.189 | 0.966 | 18.8% |
| 0.005 mm / 20261001 | 1.511 | 1.120 | 25.9% |
| 0.005 mm / 20261002 | 1.224 | 0.986 | 19.4% |
| 0.050 mm / 20261001 | 2.073 | 1.920 | 7.4% |
| 0.050 mm / 20261002 | 2.035 | 1.822 | 10.5% |

Annotate the table: six exploratory trials only; common and independent routes share geometry, beta, acceleration, warm-up, and initial-`R` construction; common-route innovations have pairwise median correlations about 0.591–0.619 (pair maxima about 0.726–0.881); the diagonal covariance approximation is not a measured covariance model; `N_eff` is weight diversity only.

### Table 4 — P2 gate smoke (negative control, likely supplement)

- 10 trials; 6 accepted; 4 abstentions; coverage **0.60**; false accepts **0**.
- Stationary: 0/2 accepted; 0.005 mm: 0/2; 0.010, 0.020, 0.050 mm: 2/2 each.
- All 10 ungated trials met the 10-µm frozen-test RMSE criterion, including gate-rejected trials; therefore the gate did not demonstrate accuracy improvement or weak-target discrimination in this sample.
- Gate decisions used calibration observables, but retained RA geometry/selection used the full 400-frame ADC window, so a strict calibration-only P2 deployment claim is blocked.

### Table 5 — Route availability and comparison boundary

List RA as available and RO-all-channel as **unavailable / fail-closed**. Do not insert a fabricated RO value, relabel RA as RO, or report a RA-vs-RO effect size. Keep the fair-branch protocol and RO blocker in supplementary material.

### Recommended figures (only if already available)

1. Pipeline schematic: ADC → range–angle candidates → local AoA → frozen `beta_i` → native-time ADXL pre-integration → common structural-phase Kalman.
2. Fence diagnostic: calibration geometry unchanged under test-only perturbation; clearly label as a diagnostic, not a robustness or accuracy result.
3. P1 coverage/RMSE by stratum: accepted count and accepted-only RMSE with abstentions shown explicitly.
4. P3 six-row paired plot: common vs single RMSE and a companion innovation-correlation annotation; avoid a “number of independent targets” graphic.

## 7. Limitations to state explicitly

1. **Synthetic-only validation.** The A20 response, scattering, multipath, noise, array errors, ADXL delay, and modal participation are parameterized assumptions. The 14.674-µm seed-2026 A20 chain result (if shown) validates package execution, not hardware or field precision.
2. **Conditional P1 metric.** Accepted-only 1.355 µm is conditioned on the frozen guard; nine rejected trials have no counterfactual estimate in retained outputs. Report coverage and abstentions beside every RMSE number.
3. **Cold start and adaptive `R`.** P1 freezes geometry/selection/beta, but each accepted test starts a fresh retained Kalman state; the first 20 test frames use retained cold-start bias/initial-`R` logic, and adaptive `R` settings remain unchanged. This is not a fully calibration-initialized end-to-end test.
4. **P3 is exploratory.** Six trials and two seeds cannot support a confirmatory or causal claim. Common and independent routes share initialization and all upstream processing. Positive innovation correlations (median about 0.59–0.62) contradict an independent-noise interpretation; `N_eff` is weight diversity only.
5. **No measured observation covariance or uncertainty calibration.** The filter uses a diagonal precision-weighted variance approximation; no off-diagonal covariance estimate, NIS calibration, phase-slip analysis, or empirical confidence coverage was completed.
6. **No RO branch.** The current checkout has no faithful range-only all-channel estimator or matched beta/backend contract. A failed naive ADXL double-integration path is not evidence that all acceleration-only calibration is impossible.
7. **P2 gate is development-only.** Thresholds are development choices; static acceptance is not a motion false-alarm test. Full-record geometry in the retained RA frontend blocks a strict calibration-only deployment claim.
8. **Geometry assumptions.** `beta_i = 1/|cos(theta_i)|` is a configuration-dependent mapping. Absolute beta accuracy requires independent array, mounting, axis, and structure-direction calibration. A range–angle cluster may be an equivalent observation, not a single physical point.
9. **Target management scope.** The target set is record-level with availability masking; dynamic add/remove/reassociation and online occlusion recovery are not implemented.
10. **External validity.** No field capture, laser reference, weather/traffic variation, or independent hardware repeatability study is included. Do not use a 0.01-mm success threshold as a field-accuracy statement.

## 8. Claims to remove before submission

| Remove from draft | Replace with |
|---|---|
| “RA outperforms RO” / “RA is superior to range-only” | “The RO-all-channel branch is not implemented in the current checkout; no RA–RO comparison is reported.” |
| “0.01-mm field accuracy,” “sub-10-µm field precision,” or “validated to 0.01 mm” | “In synthetic P1 trials, pooled accepted-only frozen-test RMSE was 1.355 µm at 95.5% coverage; this is conditional simulation evidence, not field accuracy.” |
| “The P2 quality gate improves accuracy / rejects weak targets beneficially” | “The 10-trial gate smoke accepted 6/10, while all 10 ungated trials met the 10-µm criterion; gate benefit was not demonstrated.” |
| “P3 proves causal/common-state fusion gain” | “After excluding the 20-frame retained warm-up, common-state RMSE was lower in all six exploratory rows, with 7.4–27.3% descriptive reductions.” |
| “Five targets provide ~4.8 independent observations” | “`N_eff`≈4.77–4.92 measures precision-weight diversity only; common innovations were correlated.” |
| “Strict calibration-only end-to-end operation” (for P2/P3 or the retained Kalman state) | “Geometry/selection/beta were calibration-frozen; test-state bias/initial-`R` cold start remained in the retained API.” |
| “Online dynamic target tracking/reassociation” | “Record-level range–angle candidate construction with per-frame availability masking.” |
| “Accurate/validated beta from AoA” | “Direct AoA-derived frozen geometric beta under declared array and mounting assumptions; absolute accuracy remains to be calibrated.” |
| “Novel Kalman / first multi-target radar–accelerometer fusion” | “A task-specific combination of established AoA, acceleration-aided phase prediction, and target-wise shared-state filtering; novelty is in the integration and operating geometry.” |

## 9. Five-day execution plan

- **Day 1 — Freeze scope and references.** Lock the title, abstract numbers, contribution language, and the four anchor literature groups: best-target radar–accelerometer displacement; multi-target/occlusion switching; range–angle phase tracking; acceleration-aided Kalman with offline conversion factor. Do not run a new RO substitute or expand the baseline.
- **Day 2 — Methods and main results.** Write the capture contract, geometry fence, native-time pre-integration, shared-state equations, P1 table, and fence diagnostic. Add an explicit “accepted-only vs all-trial” metric definition.
- **Day 3 — Secondary results and limitations.** Add P3 six-row descriptive ablation and P2 negative smoke, then write limitations and remove prohibited claims. Put RO blocker and detailed audit in supplementary material.
- **Day 4 — Figures and reproducibility.** Render only figures supported by existing artifacts; verify all numbers against the compact JSON/Markdown summaries, units, seeds, score windows, and guard/cold-start labels. Check that truth is post-run only in every methods description.
- **Day 5 — Submission QA.** Search the manuscript for “RO,” “0.01 mm,” “field,” “causal,” “independent,” “gate benefit,” and “strict calibration-only”; inspect each occurrence. Confirm no table silently drops abstentions. Package code/protocol hashes and a concise data-availability statement; no source-code changes or push are needed for the paper story.

## 10. Evidence files to cite internally while writing

- `spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/full/summary.json`
- `spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/full/PROVENANCE_AUDIT.md`
- `spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/full/test_only_perturbation_probe.json`
- `spatial_recovery_rebuilt/p3_fusion_docs/strict_followup/STRICT_FOLLOWUP_PROTOCOL.md`
- `spatial_recovery_rebuilt/SPRINT_EVIDENCE_STATUS.md`
- `spatial_recovery_rebuilt/p2_quality_gate_protocol.md` and `p2_gate_smoke/p2_quality_gate_report.json`
- `spatial_recovery_rebuilt/ro_allchannel/BLOCKER.md`
- `docs/literature_fusion_methods.md`, `docs/method_innovation_review.md`, `integrated_literature_review.md`

This file is a planning artifact only; it intentionally makes no claim that the present evidence establishes field accuracy or acceptance.
