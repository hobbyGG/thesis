# DOI and literature addendum: profile-LS, coherent sources, beta, and covariance

Date: 2026-10-03  
Scope: additive cross-review for the thesis mainline. This file supplements
`AUDIT_NOTE.md` and `NEXT_PROTOCOL.json`; it does not replace either file.

The sibling `DOI_SUPPLEMENT_2026-10-03.md` is treated as the current baseline.
This file is a separate, more detailed addendum. It agrees with that baseline
that the exact thesis complex profile-LS DOI and the acceleration-aided Kalman
paper DOI remain **pending**; the generic ML, variable-projection, WSF, and
off-grid papers below are methodological neighbors, not substitutions for
those pending direct matches.

## Provenance and evidence fence

The local checkout was inspected before adding this file. The relevant local
anchors are:

- `docs/current_research_data_flow.md:345-385`: the retained AoA path forms a
  same-range virtual-array snapshot `X`, estimates `Rxx = XX^H/K`, uses local
  MUSIC for an initial spatial frequency, and refines it with the complex
  profile residual
  `J(u) = ||X - A(u) A(u)^dagger X||_F^2`.
- `spatial_recovery_rebuilt_validation_2026-10-03/README.md` and
  `READINESS.json`: the fresh 400-frame smoke establishes package/guard and
  truth-free bookkeeping, but the retained `algorithm.run` route still builds
  geometry from all 400 ADC frames; it is not strict held-out geometry
  evidence.
- `spatial_recovery_rebuilt/calibration_only/smoke_truth_free_v3/`: the
  exploratory calibration-only wrapper uses 200 calibration and 200 test
  frames, freezes target/angle/beta fields, and checks that test-only ADC
  perturbation does not change frozen geometry. Its cold-start bias and
  initial-`R` use still need a strict protocol decision.
- `spatial_recovery_rebuilt/p3_fusion_strict_followup/`: six descriptive rows
  record innovation correlations, not truth-error covariance. The diagonal
  covariance route and `N_eff = 1/sum(w_i^2)` are not full-GLS or
  independent-target evidence.
- `experiments/same_range_merge_mechanism_v2/`: a bounded synthetic
  split/merge mechanism check. It does not establish a universal angle
  resolution, coherent-source robustness, or field accuracy.

The current checkout search did not locate a standalone fresh
profile-LS/covariance artifact for the referenced “400–402” diagnostic. No
numbers from an unavailable artifact are filled in here.

## Five-question audit

### 1. Calibration-only off-grid/profile-LS

**Literature facts.** For a narrowband array model

`X = A(theta) S + N`,

the nuisance source amplitudes/waveforms can be profiled out at a candidate
`theta` with `S_hat(theta) = A(theta)^dagger X`. Under spatially white complex
Gaussian noise, minimizing the resulting residual is the conditional maximum
likelihood form; with colored noise, the residual must be whitened or weighted
by a declared noise covariance. The retained implementation is therefore best
described as **local MUSIC-seeded profile-residual refinement**, not as a new
ML estimator, and it currently has no colored-noise whitening or joint
mutual-coupling/position-error fit.

Verified original references:

- Golub and Pereyra, “Separable nonlinear least squares: the variable
  projection method and its applications,” Inverse Problems 19(2), R1–R26
  (2003), DOI
  [10.1088/0266-5611/19/2/201](https://doi.org/10.1088/0266-5611/19/2/201).
  Variable projection is the direct mathematical precedent for eliminating
  linear complex amplitudes and optimizing only nonlinear angle/manifold
  parameters.
- Stoica and Sharman, “Maximum likelihood methods for direction-of-arrival
  estimation,” IEEE T-ASSP 38(7), 1132–1143 (1990), DOI
  [10.1109/29.57542](https://doi.org/10.1109/29.57542). This supports the
  profile-out nuisance-amplitude interpretation and the need for a declared
  array/noise model.
- Stoica and Nehorai, “MUSIC, maximum likelihood, and Cramér–Rao bound,” IEEE
  T-ASSP 37(5), 720–741 (1989), DOI
  [10.1109/29.17564](https://doi.org/10.1109/29.17564). This is a classical
  MUSIC/ML performance reference; it does not identify the thesis profile-LS
  implementation.
- Viberg, Ottersten, and Kailath, “Detection and estimation in sensor arrays
  using weighted subspace fitting,” IEEE T-SP 39(11), 2436–2449 (1991), DOI
  [10.1109/78.97999](https://doi.org/10.1109/78.97999). This supports a
  covariance-weighted subspace-fitting comparison, with an explicit signal
  subspace/noise-statistics assumption.
- Jansson, Swindlehurst, and Ottersten, “Weighted subspace fitting for general
  array error models,” IEEE T-SP 46(9), 2484–2498 (1998), DOI
  [10.1109/78.709536](https://doi.org/10.1109/78.709536). This supports
  including gain, phase, position, or other low-dimensional array-error
  parameters only when the error parameterization is identifiable.
- Huang, So, and Zoubir, “Off-grid direction-of-arrival estimation using
  second-order Taylor approximation,” Signal Processing 196, 108513 (2022),
  DOI [10.1016/j.sigpro.2022.108513](https://doi.org/10.1016/j.sigpro.2022.108513).
  This is a grid-mismatch reference, not evidence that the retained local
  three-pass refinement is a Bayesian off-grid estimator.
- Yang et al., “Off-grid direction of arrival estimation using sparse Bayesian
  inference,” IEEE T-SP 61(1), 38–43 (2013), DOI
  [10.1109/TSP.2012.2222378](https://doi.org/10.1109/TSP.2012.2222378). This
  is a sparse Bayesian off-grid comparison with shared support assumptions.
- Ng and See, “Sensor-array calibration using a maximum-likelihood approach,”
  IEEE TAP 44(6), 827–835 (1996), DOI
  [10.1109/8.509886](https://doi.org/10.1109/8.509886). This supports the
  general pattern of estimating calibration quantities from a calibration
  record and then treating them as fixed, but it uses a declared calibration
  model/source; it is not a direct proof for the thesis capture package.

**可迁移推论.** The thesis may state a calibration-only protocol as a
measurement-design rule: estimate target support, continuous angle, beta, and
any declared nuisance parameters from frames `0:200`; hash and freeze them;
project frames `200:400` without target detection, angle updates, or
truth-based threshold changes; score truth only after route outputs exist.
This is a defensible train/calibration-versus-held-out protocol inference from
the above estimator literature and the local wrapper, not a claim that any one
paper used the identical 200/200 thesis split.

Local identifiability requires the Jacobian of the modeled complex data with
respect to angle and nuisance parameters to have full rank after gauge choices
(global phase, source-label permutation, and array translation/rotation where
applicable). It also requires enough independent spatial/slow-time snapshots,
nondegenerate source separation, and an array manifold whose errors are not
confounded with the angle parameter. A small grid offset can be locally
linearized; a large offset, wideband coupling, or unknown mutual coupling is a
model-mismatch case.

**仍需实验验证.** The minimum follow-up is the already designed frozen-beta
angle-sensitivity v1 in `NEXT_PROTOCOL.json`. It must report angle offset,
beta offset, residual cost, finite coverage, signed bias, and test RMSE while
keeping calibration geometry fixed. A later profile-only comparison should
use calibration-only whitening and compare the current residual, WSF, and an
off-grid sparse baseline under declared snapshot/SNR grids.

### 2. Coherent or near-coherent sources and array errors

**Literature facts.** If source correlation is one, the source covariance is
rank deficient. A sample-covariance MUSIC/ESPRIT pipeline can then lose signal
subspace rank and merge or miss directions. Shan, Wax, and Kailath,
“On spatial smoothing for direction-of-arrival estimation of coherent
signals,” IEEE T-ASSP 33(4), 806–811 (1985), DOI
[10.1109/TASSP.1985.1164649](https://doi.org/10.1109/TASSP.1985.1164649),
supports forward spatial smoothing for coherent sources under a ULA,
narrowband plane-wave, subarray, and sufficient-snapshot model. Forward/backward
smoothing can exploit the conjugate-reversal symmetry of a suitable ULA, but
it reduces effective aperture and changes the resolution/noise tradeoff.

The local SpSF paper (`ref_papers/01_AoA/An Implementation Scheme of Range and
Angular Measurements for FMCW MIMO Radar via Sparse Spectrum Fitting.pdf`, DOI
[10.3390/electronics9030389](https://doi.org/10.3390/electronics9030389))
explicitly assumes uncorrelated targets. Its low-SNR/small-snapshot result
must therefore not be transferred to coherent same-range sources.

Verified array-error references include Weiss and Friedlander,
“Eigenstructure methods for direction finding with sensor gain and phase
uncertainties,” Circuits Systems Signal Processing 9, 271–300 (1990), DOI
[10.1007/BF01201215](https://doi.org/10.1007/BF01201215); Wijnholds and van
der Veen, “Multisource self-calibration for sensor arrays,” IEEE T-SP 57(9),
3512–3522 (2009), DOI
[10.1109/TSP.2009.2022894](https://doi.org/10.1109/TSP.2009.2022894); and
Ramamohan et al., “Self-Calibration of Acoustic Scalar and Vector Sensor
Arrays,” IEEE T-SP 71, 61–75 (2022), DOI
[10.1109/TSP.2022.3214383](https://doi.org/10.1109/TSP.2022.3214383).
These papers make the same methodological point: gain/phase, position, and
mutual-coupling terms require an explicit error model and a reference/gauge;
otherwise angle and calibration errors can be confounded.

**可迁移推论.** The thesis can use three explicitly different routes:

1. direct complex profile fitting, which avoids relying on a full-rank sample
   covariance but needs a correct steering manifold and enough independent
   complex snapshots;
2. spatial smoothing/FBSS, which restores a usable covariance rank only under
   ULA/subarray/plane-wave assumptions and pays with aperture and variance;
3. structured covariance or self-calibration, which can model shared gain,
   phase, position, or coupling errors but needs calibration identifiability.

None of these routes turns a noise-free synthetic separation result into a
general coherent-source claim.

**仍需实验验证.** Add a bounded two-source probe with fixed range, source
correlation `rho in {0, 0.5, 0.9, 1}`, angle spacing, amplitude ratio, and
snapshot count. Compare ordinary sample-covariance MUSIC, forward/backward
spatial smoothing, and direct profile residual. Report peak count, angle bias,
complex phase residual, displacement RMSE, and abstention. Add gain/phase,
position, and mutual-coupling perturbations only as separate calibration
factors; do not silently absorb them into angle bias.

### 3. Phase reference and beta sensitivity

**Literature facts.** Local structural-radar papers establish the physical
chain but not a universal beta guarantee:

- Ma et al., “Structural displacement estimation using accelerometer and FMCW
  millimeter wave radar,” MSSP 182, 109582 (2023), DOI
  [10.1016/j.ymssp.2022.109582](https://doi.org/10.1016/j.ymssp.2022.109582),
  uses an environment target, an estimated LOS-to-structure conversion factor,
  and radar/accelerometer fusion.
- Li et al., “Multi-scale and full-field vibration measurement via
  millimetre-wave sensing,” MSSP 177, 109178 (2022), DOI
  [10.1016/j.ymssp.2022.109178](https://doi.org/10.1016/j.ymssp.2022.109178),
  supports range-angle component selection and LOS geometry correction for
  vibration measurement.
- Xiong et al., “Millimeter-wave bat for mapping and quantifying micromotions
  in full field of view,” Research 2021, 9787484, DOI
  [10.34133/2021/9787484](https://doi.org/10.34133/2021/9787484), supports
  keeping angle-gated complex slow-time components rather than only a
  range-bin magnitude.
- Guo et al., “Measuring Micrometer-Level Vibrations With mmWave Radar,” IEEE
  TMC 22(4), 2248–2261 (2023), DOI
  [10.1109/TMC.2021.3118349](https://doi.org/10.1109/TMC.2021.3118349). This
  supports the controlled range-angle/IQ micromotion context; it does not
  establish the thesis beta or shared-state accuracy.
- Xu et al., “Simultaneous monitoring of multiple people's vital sign
  leveraging a single phased-MIMO radar,” IEEE J-ERM 6(3), 311–320 (2022),
  DOI [10.1109/JERM.2022.3143431](https://doi.org/10.1109/JERM.2022.3143431),
  is a same-range angle-separation feasibility reference; it is not structural
  displacement evidence.

With the thesis convention `q_struct = beta q_los` and
`beta = 1/|cos(theta)|`, a small angle error in radians gives

`delta beta approximately beta * tan(theta) * delta theta`,

away from the absolute-value cusp. A phase-reference error `delta b` gives a
first-order displacement bias

`delta q approximately (lambda/(4 pi)) * beta * delta b`,

and beta uncertainty contributes approximately

`Var(q) approximately q_los^2 Var(beta) + beta^2 Var(q_los) + 2 beta q_los Cov(beta,q_los)`.

The sign and exact factor depend on the FMCW round-trip convention and the
declared structural-axis projection. These equations are propagation
identities, not measured accuracy results.

**可迁移推论.** A fixed calibration reference is defensible only for the
declared geometry and time window. A reference target can introduce additive
phase bias; an angle error creates multiplicative beta bias; a structural-axis
or mounting-direction error is another multiplicative projection error. A
mixed angle cluster may have a window-dependent effective beta when component
amplitudes or relative phases change. The paper should therefore describe
`beta` as a frozen model parameter/diagnostic, not as a universally correct
physical constant.

**仍需实验验证.** Keep the existing seven-offset v1 protocol. Score bias and
variance against angle offset and beta offset after the route completes. Add a
second reference-phase perturbation only after v1 passes the geometry-fence
checks; do not tune the reference from test truth. The local Ma-family
references support the motivation, but no cited paper proves the proposed
`1/|cos(theta)|` propagation is sufficient for this exact inverted-radar
natural-scatterer geometry.

### 4. Covariance-aware/GLS fusion

**Literature facts.** For a shared scalar state with observations `y = H q + e`
and residual covariance `Sigma`, full GLS is

`q_hat = (H^T Sigma^{-1} H)^{-1} H^T Sigma^{-1} y`,

with model covariance `(H^T Sigma^{-1} H)^{-1}` when `Sigma` is correctly
specified. Using only `diag(Sigma)` is diagonal WLS and is valid only when the
off-diagonal correlations are negligible or intentionally modeled away.

For unknown cross-correlation, Julier and Uhlmann, “A non-divergent
estimation algorithm in the presence of unknown correlations,” ACC 1997, DOI
[10.1109/ACC.1997.609105](https://doi.org/10.1109/ACC.1997.609105), supports
Covariance Intersection as a conservative consistency mechanism. Chen,
Arambel, and Mehra, “Fusion under unknown correlation—Covariance Intersection
as a special case,” FUSION 2002, DOI
[10.1109/ICIF.2002.1020908](https://doi.org/10.1109/ICIF.2002.1020908), and
Reinhardt et al., “Minimum covariance bounds for the fusion under unknown
correlations,” IEEE SPL 22(9), 1210–1214 (2015), DOI
[10.1109/LSP.2015.2390417](https://doi.org/10.1109/LSP.2015.2390417), provide
the unknown-correlation boundary. These are general estimator-fusion results,
not evidence that the current target observations are independent or that CI
will improve thesis RMSE.

For filter consistency, Piché, “Online tests of Kalman filter consistency,”
International Journal of Adaptive Control and Signal Processing 30(1),
115–124 (2016), DOI [10.1002/acs.2571](https://doi.org/10.1002/acs.2571),
supports using innovation-based NIS checks without using future data. NIS
thresholds must be declared before scoring; gating/selection changes the
conditional distribution. NEES requires truth and therefore belongs only in
post-run evaluation.

The local PDF titled “Acceleration-aided Kalman filtering for joint phase
denoising and unwrapping in FMCW radar-based displacement monitoring” remains
**DOI pending** in this review. Its local bibliographic record is useful for
method comparison, but no DOI is asserted here.

**可迁移推论.** The current P3 innovation correlations do not estimate
truth-error covariance. `N_eff = 1/sum(w_i^2)` measures weight diversity only;
it is not an independent-target count or covariance-adjusted information
measure. A defensible next comparison is diagonal WLS versus calibration-only
full/block-`Sigma` GLS, with covariance conditioning and positive-definiteness
handling recorded. If cross-correlation is unknown, CI is a conservative
reference route, not a claim of optimality for more than two channels.

**仍需实验验证.** Estimate `Sigma` from declared calibration observables,
freeze it, and compare diagonal WLS, full GLS, and CI on held-out test frames.
Report RMSE, signed bias, full-matrix NIS against a predeclared chi-square
interval, empirical coverage, condition number, and any covariance clipping.
Do not call a route calibrated unless coverage is checked. Do not infer
independence from innovation correlation alone.

### 5. Same-range target identifiability

**Literature facts.** Local structural and radar references support the
feasibility of angle-gated complex slow-time extraction, but they also impose
limits:

- Li et al. (MSSP 2022, DOI 10.1016/j.ymssp.2022.109178) explicitly motivates
  range-angle components when range-only processing mixes same-range or nearby
  components.
- Xu et al. (IEEE J-ERM 2022, DOI 10.1109/JERM.2022.3143431) shows a
  same-radial-distance angle-separation chain with Capon/MVDR, while its
  performance still depends on angular spacing and finite aperture.
- Shan et al. (TASSP 1985, DOI 10.1109/TASSP.1985.1164649) bounds the
  covariance-subspace route for coherent sources and a ULA.
- Huang et al. (Electronics 2020, DOI 10.3390/electronics9030389) and the
  local SpSF record assume uncorrelated targets; they are not coherent-source
  evidence.

**可迁移推论.** `split` is justified only when the angle-separated complex
  components are identifiable under the declared aperture, SNR, snapshot, and
  source-correlation conditions. `merge` is appropriate for an unresolved
  cluster when a single effective phase remains stable. `abstain` is required
  when cancellation, rank deficiency, low magnitude, or model mismatch makes
  the component non-identifiable. The current same-range v2 therefore supports
  a bounded mechanism claim and the need for an abstention branch; it does not
  support a universal separation threshold.

**仍需实验验证.** Keep the current v2 boundary. Add the coherent-source
  stress grid only as a small follow-up: angle spacing, `rho`, SNR, snapshot
  count, amplitude ratio, and static phase. Score peak count, phase residual,
  displacement error, and abstention rate. No test truth may select split,
  merge, or thresholds.

## DOI registry and verification status

The following items were checked against local bibliographic records and/or an
original publisher/DOI landing page during this review. “Verified DOI” means
the DOI string and title/journal pairing were checked. It does not mean the
paper validates the thesis claim.

| Reference | Status | Use boundary |
|---|---|---|
| Golub & Pereyra 2003, DOI 10.1088/0266-5611/19/2/201 | verified DOI | separable nonlinear least squares / variable projection |
| Stoica & Sharman 1990, DOI 10.1109/29.57542 | verified DOI | ML/profile objective; known manifold/noise assumptions |
| Stoica & Nehorai 1989, DOI 10.1109/29.17564 | verified DOI | classical MUSIC/ML performance reference |
| Viberg, Ottersten & Kailath 1991, DOI 10.1109/78.97999 | verified DOI | weighted subspace fitting baseline |
| Jansson et al. 1998, DOI 10.1109/78.709536 | verified DOI | general array-error parameterization |
| Rockah & Schultheiss 1987, DOI 10.1109/TASSP.1987.1165144 | verified DOI | far-field shape calibration; gauge/identifiability |
| Weiss & Friedlander 1990, DOI 10.1007/BF01201215 | verified DOI | gain/phase uncertainty model |
| Ng & See 1996, DOI 10.1109/8.509886 | verified DOI | ML calibration; declared calibration source required |
| Wijnholds & van der Veen 2009, DOI 10.1109/TSP.2009.2022894 | verified DOI | multisource self-calibration |
| Ramamohan et al. 2022, DOI 10.1109/TSP.2022.3214383 | verified DOI | joint array-error/DOA calibration |
| Yang et al. 2013, DOI 10.1109/TSP.2012.2222378 | verified DOI | off-grid sparse Bayesian comparison |
| Huang, So & Zoubir 2022, DOI 10.1016/j.sigpro.2022.108513 | verified DOI | second-order off-grid comparison |
| Shan, Wax & Kailath 1985, DOI 10.1109/TASSP.1985.1164649 | verified DOI | coherent-source spatial smoothing |
| Stoica, Babu & Li 2011, DOI 10.1109/TSP.2010.2090525 | verified DOI | sparse covariance matching; not direct phase evidence |
| Ottersten, Stoica & Roy 1998, DOI 10.1006/dspr.1998.0316 | verified DOI | covariance matching; finite-sample conditioning remains |
| Julier & Uhlmann 1997, DOI 10.1109/ACC.1997.609105 | verified DOI | conservative fusion with unknown correlations |
| Chen, Arambel & Mehra 2002, DOI 10.1109/ICIF.2002.1020908 | verified DOI | covariance intersection boundary |
| Reinhardt et al. 2015, DOI 10.1109/LSP.2015.2390417 | verified DOI | minimum covariance bound under unknown correlation |
| Piché 2016, DOI 10.1002/acs.2571 | verified DOI | online NIS consistency test |
| Ma et al. 2023, DOI 10.1016/j.ymssp.2022.109582 | verified local DOI | structural radar/accelerometer conversion factor |
| Li et al. 2022, DOI 10.1016/j.ymssp.2022.109178 | verified local DOI | range-angle vibration components |
| Xiong et al. 2021, DOI 10.34133/2021/9787484 | verified local DOI | full-field mmWave micromotion |
| Guo et al. 2023, DOI 10.1109/TMC.2021.3118349 | verified DOI | controlled mmWave IQ/range-angle micromotion |
| Xu et al. 2022, DOI 10.1109/JERM.2022.3143431 | verified DOI | same-range angle separation feasibility |
| Yang et al. 2024, DOI 10.1109/PIERS62282.2024.10618454 | verified local DOI | MIMO-FMCW range-angle chain; human vital signs |

## Pending or explicitly unverified items

- The exact standalone fresh profile-LS/covariance artifact for the referenced
  400–402 diagnostic was not found in the current checkout. This addendum does
  not report its numbers.
- A DOI directly matching the thesis complex profile-LS geometry objective was
  not identified. Variable projection, ML/profile, WSF, and off-grid DOI
  entries above are adjacent methodological references only; the direct match
  remains pending.
- The DOI for the local acceleration-aided Kalman phase paper remains pending;
  do not infer or copy a DOI from an unrelated Ma-family paper.
- The local records for Ma et al. 2023/2024/2025 bridge-occlusion and low-cost
  deployment papers contain complete title/volume/page metadata, but their DOI
  strings were not required for this addendum and remain unverified here.
- The PIERS 2024 paper is retained as a method-chain feasibility reference;
  it is not structural-displacement evidence.
- No cited paper establishes that the current IWR1843 hardware, natural
  scatterer geometry, or shared phase noise satisfies full-`Sigma` GLS
  assumptions. That bridge remains an experiment.

## Minimal next experiment recommendations

1. **Run only the already designed v1 angle/beta sensitivity probe after its
   source hashes are checked.** Use the six trials and seven frozen angle
   offsets in `NEXT_PROTOCOL.json`; do not start the 40-seed matrix.
2. **Design, but do not yet run, a coherent-source probe.** Use the declared
   `rho`, angle-spacing, SNR, snapshot, amplitude-ratio, and phase grid. Compare
   covariance MUSIC, FBSS, and direct profile residual with abstention.
3. **Design, but do not yet run, a covariance probe.** Estimate a full/block
   residual covariance from calibration observables only; freeze it; compare
   diagonal WLS, full GLS, and CI with NIS/coverage and conditioning reports.

The current evidence permits a bounded calibration-frozen/profile-residual
method claim. It does not permit claims of universal off-grid accuracy,
coherent-source robustness, calibrated full-covariance uncertainty, field
accuracy, or general `0.01 mm` performance.
