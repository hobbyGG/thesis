# Cross-review: profile-LS geometry and covariance assumptions

Date: 2026-10-03  
Scope: thesis mainline only; no algorithm or capture-contract change.

## Method continuity

The method remains a direct offline chain:

`capture/simulation package -> range/range-angle signal processing -> calibration-frozen geometry and beta -> native-time ADXL pre-integration -> shared structural-state Kalman -> displacement result`.

The three linked research points remain:

1. same-range multi-angle reference construction with `split/merge/abstain`;
2. calibration-only off-grid/profile-LS geometry refinement with causal phase-reference and beta handling;
3. shared structural state with covariance-aware multi-target fusion.

This review does not add legacy scenario registries, Ma baselines, service layers, retry frameworks, or a broad baseline runner.

## Evidence ledger

| Topic | Evidence currently present | What it supports | Boundary |
|---|---|---|---|
| Fresh validation smoke | `spatial_recovery_rebuilt_validation_2026-10-03/` | Package contract, calibration-only guards, truth-free estimator copy, post-run scoring bookkeeping | Retained `algorithm.run` still builds geometry from all 400 ADC frames; this is not strict held-out geometry evidence. |
| Calibration-only wrapper | `spatial_recovery_rebuilt/calibration_only/smoke_truth_free_v3/` | 2 seeds x 5 strata; 10/10 guard and truth-removal checks; test-only ADC perturbation leaves frozen geometry fields unchanged | Exploratory wrapper; retained Kalman bias/initial-`R` cold-start still uses test samples. |
| P3 shared-state follow-up | `spatial_recovery_rebuilt/p3_fusion_strict_followup/` | Six descriptive rows where the common route was lower RMSE; innovation correlations are recorded | Correlations are innovations, not truth-error covariance; diagonal covariance is not a full GLS result; `N_eff` is weight diversity, not independent-target count. |
| Same-range v2 | `experiments/same_range_merge_mechanism_v2/` | Bounded synthetic split/merge mechanism check with fixed protocol and 12 seeds | Does not establish coherent-source robustness, general angle resolution, field accuracy, or causal superiority. |
| Fresh profile-LS/covariance artifact | Current checkout search on 2026-10-03 | No standalone fresh profile-LS/covariance artifact was located by name or text search | Do not invent numbers or claim parity with an unavailable workspace. |

## Assumption-to-evidence audit

| Assumption needing literature support | Current local interpretation | Minimum validation still needed |
|---|---|---|
| Profile objective and off-grid identifiability | A calibration-only profile-LS/AoA refinement can be useful for a frozen geometry, but the objective, nuisance parameters, SNR/fast-time snapshot requirements, and local identifiability are not established by the current synthetic diagnostic alone. | Cite an original off-grid/profile or weighted subspace fitting method; record array manifold, nuisance, and held-out-freeze assumptions; run a small calibration/test fence diagnostic with source hashes. |
| Coherent or near-coherent source bias | Coherent scattering can make covariance subspace methods rank deficient; direct complex-profile fitting, spatial smoothing, and structured covariance each have different assumptions. | Cite coherent-source DOA and array self-calibration work; vary source correlation/phase and snapshot count in a bounded synthetic probe, with abstention on non-identifiable cases. |
| Phase reference and beta sensitivity | `beta = 1/|cos(theta)|` is configuration-dependent. Angle convention, mounting direction, array calibration, and reference choice can create displacement bias; current files do not prove absolute beta accuracy. | Cite reference-free radar displacement and geometric projection work; perturb frozen angle/reference in the test route and report bias/RMSE versus perturbation without using truth for estimator decisions. |
| GLS/full covariance fusion | The current P3 route uses target-wise weights and diagonal internal covariance. Innovation correlation does not by itself justify a full covariance estimate or a calibrated uncertainty claim. | Cite GLS/correlated track-to-track fusion and NIS/coverage practice; estimate covariance from declared calibration observables only, compare diagonal versus full/block covariance, and report conditioning plus coverage post-run. |
| Same-range target identifiability | Same range and separated angle can improve a bounded synthetic mechanism case; symmetric and coherent cases can be confounded or unresolvable. | Cite coherent multi-source and range-angle resolution limits; predeclare split/merge/abstain rules and test angle separation/correlation stress cases with no truth-driven selection. |

## Non-duplicative next protocol design (not run here)

The first minimal probe should isolate **frozen beta / reference-angle sensitivity**, because existing same-range v2 already tests a split-versus-merge waveform mechanism and P3 already tests a descriptive shared-state comparison.

* **Input:** the existing capture-package builder and the calibration-only wrapper; seeds `20261001` and `20261002`; strata `stationary`, `low_motion_0p005mm`, and `low_motion_0p050mm` only (six trials).
* **Calibration use:** frames `0:200` and corresponding ADXL samples only for target detection, local angle refinement, target selection, beta, guard limits, and any covariance/phase-reference constants. Freeze and hash all geometry fields before test processing.
* **Test-only perturbation:** keep test ADC/ADXL arrays unchanged, but rerun the frozen projection with predeclared angle offsets `delta_theta_deg in {0, -2, -1, -0.5, +0.5, +1, +2}` (or the equivalent beta perturbation under the documented angle convention). Do not refit geometry, select targets, or tune thresholds from truth or test truth.
* **Estimator fence:** remove `truth/` and post-run metadata from the estimator copy; assert no truth field is emitted; use truth only after all routes finish for scoring.
* **Compact outputs:** protocol JSON, source SHA-256 manifest, per-trial frozen-geometry hash, target count, angle/beta perturbation, finite coverage, test RMSE, signed bias, and a diagnostic curve. Do not save raw arrays.
* **Decision rule:** this probe is descriptive. Stop and mark the route unresolved if geometry hashes change under a test-only ADC perturbation, if the estimator reads truth, if any perturbed route becomes non-finite, or if target association changes without an explicitly declared abstention. Do not use a `0.01 mm` threshold as a field-accuracy claim.

No 40-seed matrix should start until the calibration-only route is independently wired to the selected estimator path, the seed mapping (`20261001..20261040` versus the historical `7200..7239`) is resolved, and strict calibration-only bias/initial-`R` initialization is specified.
