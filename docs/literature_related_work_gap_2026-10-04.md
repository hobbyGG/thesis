# Related-work gap: phase-preserving geometry and common-state fusion

Date: 2026-10-04  
Scope: targeted literature cross-check for the thesis mainline. This is an
additive literature note; it does not change code, experiments, or existing
user notes.

## Central conclusion

The defensible gap is not another MUSIC, profile-LS, Kalman, or beamforming
formula in isolation. The literature already contains those components in
separate streams. The less-covered combination is:

```text
same-range / natural-scatterer isolation
  -> complex slow-time phase is preserved
  -> AoA/geometry is estimated on a declared calibration prefix and frozen
  -> all usable targets observe one structural state
  -> target errors are treated as potentially correlated
  -> split / merge / abstain is reported when identifiability fails
```

This is a **combination and protocol gap**, not evidence that each component is
new. The thesis can claim this chain only after the calibration fence,
coherent-source boundary, and covariance consistency are measured separately.

## 1. Profile-LS and geometry calibration

### Verified primary references

| Reference | DOI | What it establishes | Boundary for this thesis |
|---|---|---|---|
| Stoica & Sharman, “Maximum likelihood methods for direction-of-arrival estimation,” IEEE T-ASSP (1990) | [10.1109/29.57542](https://doi.org/10.1109/29.57542) | ML/conditional profile treatment of nuisance source amplitudes under a declared array/noise model. | Supports the interpretation of the local complex residual as a standard separable estimation family; it does not validate this IWR1843 geometry or held-out protocol. |
| Golub & Pereyra, “Separable nonlinear least squares: the variable projection method and its applications,” Inverse Problems (2003) | [10.1088/0266-5611/19/2/201](https://doi.org/10.1088/0266-5611/19/2/201) | Eliminating linear complex amplitudes with a pseudoinverse and optimizing nonlinear manifold parameters. | Direct mathematical precedent for `S_hat=A(u)^dagger X` and `J(u)=||X-AA^dagger X||_F^2`; not a radar-SHM accuracy claim. |
| Ng & See, “Sensor-array calibration using a maximum-likelihood approach,” IEEE TAP (1996) | [10.1109/8.509886](https://doi.org/10.1109/8.509886) | Calibration requires an explicit source/array response model and a calibration measurement design. | Supports separating calibration data from later estimation; it does not imply that the thesis's local AoA refinement is a new calibration estimator. |
| Jansson, Swindlehurst & Ottersten, “Weighted subspace fitting for general array error models,” IEEE T-SP (1998) | [10.1109/78.709536](https://doi.org/10.1109/78.709536) | Gain/phase/position/model-error parameters need a declared perturbation model; the signal-subspace formulation can remain consistent for fully correlated sources under its assumptions. | Gives the boundary for gain/phase/mutual-coupling claims. The thesis has not fitted a general array-error model. |

### Local implementation boundary

The retained path in `docs/current_research_data_flow.md:345-385` forms
`Rxx=XX^H/K`, uses local MUSIC for an initial spatial frequency, then refines
it with the complex projection residual. This is best described as
**MUSIC-seeded local profile-residual refinement**. It is not by itself a new
ML estimator, a full off-grid Bayesian method, or a general array
self-calibration method.

The paper-facing contribution can instead be stated as a protocol claim:
geometry, target support, continuous angle, and derived beta are estimated
from a declared calibration prefix, frozen, and applied to held-out frames
without test-time target search or truth-based updates. This is a transferable
inference from the estimator literature, not a claim that any cited paper used
the same split.

The key missing assumption is a phase-preserving identifiability statement:
profile residual minimization can return a low cost even when a same-range
mixture is represented by one effective phasor. A low residual therefore does
not prove that the selected target has a physically meaningful LOS-to-structure
beta.

## 2. Coherent or near-coherent multi-target boundary

### Verified primary references

| Reference | DOI | What it establishes | Boundary for this thesis |
|---|---|---|---|
| Shan, Wax & Kailath, “On spatial smoothing for direction-of-arrival estimation of coherent signals,” IEEE TASSP (1985) | [10.1109/TASSP.1985.1164649](https://doi.org/10.1109/TASSP.1985.1164649) | Coherent sources make the sample covariance rank deficient; spatial smoothing is a remedy under ULA, narrowband, subarray, and snapshot assumptions, with reduced effective aperture. | A same-range split claim must state source correlation, aperture, snapshots, and whether smoothing assumptions hold. |
| Li et al., “Multi-scale and full-field vibration measurement via millimetre-wave sensing,” MSSP 177 (2022), 109178 | [10.1016/j.ymssp.2022.109178](https://doi.org/10.1016/j.ymssp.2022.109178) | Range-angle joint phase tracking can separate targets that collide in range-only processing and preserve a target-level interferometric phase. | Its experiments establish a useful mechanism, but do not establish coherent-source robustness for a low-channel natural-scatterer setup. |
| Ahmad et al., “Vital signs monitoring of multiple people using a FMCW millimeter-wave sensor,” IEEE RadarConf (2018) | [10.1109/RADAR.2018.8378778](https://doi.org/10.1109/RADAR.2018.8378778) | Same radial-distance targets can be separated by angular processing and then assigned separate slow-time phase signals. | Human/controlled targets and usable angle spacing do not prove structural natural-scatterer separation or long-term phase stability. |
| Jansson et al. (1998) | [10.1109/78.709536](https://doi.org/10.1109/78.709536) | A signal-subspace array-error model can be designed for correlated sources, but only with explicit perturbation statistics and identifiability assumptions. | The thesis has not shown those statistics or a joint gain/phase/position/coupling fit. |

The direct conclusion is stronger than “MUSIC fails for coherent sources”:

1. covariance methods can lose rank or resolve a wrong effective component;
2. direct complex profile fitting avoids *one* covariance-rank dependency but
   still needs a correct manifold, enough independent snapshots, and distinct
   identifiable components;
3. if two scatterers occupy one range-angle cell, their complex sum can be
   physically non-identifiable even when an optimizer converges.

Therefore `split`, `merge`, and `abstain` are measurement-validity decisions,
not merely peak-count heuristics. The current bounded same-range mechanism may
support this boundary, but it cannot provide a universal angular-resolution
threshold or a coherent-source guarantee.

## 3. Shared structural state and covariance-aware fusion

### Verified primary references

| Reference | DOI | What it establishes | Boundary for this thesis |
|---|---|---|---|
| Chen, Arambel & Mehra, “Fusion under unknown correlation—Covariance Intersection as a special case,” Information Fusion (2002) | [10.1109/ICIF.2002.1020908](https://doi.org/10.1109/ICIF.2002.1020908) | Unknown cross-correlation prevents ordinary independent-error fusion from being justified; conservative covariance-intersection rules address that case. | A diagonal inverse-variance target average cannot be called full-covariance fusion when target errors share phase, clock, array, or acceleration-model errors. |
| Ajgl & Straka, “Covariance Intersection fusion with element-wise partial knowledge of correlation,” Automatica 139 (2022), 110168 | [10.1016/j.automatica.2022.110168](https://doi.org/10.1016/j.automatica.2022.110168) | Partial correlation knowledge changes the admissible fusion rule; unknown correlation is not equivalent to independent measurements. | Current innovation correlation is not truth-error covariance. The thesis must not infer a calibrated `Sigma` or optimal GLS from innovation correlation alone. |
| Piché, “Online NIS consistency test for Kalman filters,” Aerospace Science and Technology 59 (2016), 115–124 | [10.1002/acs.2571](https://doi.org/10.1002/acs.2571) | NIS can test innovation consistency online when the test statistic and gating rule are declared. | NIS/coverage belongs in the covariance-validation experiment; it is not evidence that current target weights are statistically calibrated. |

The shared-state gap is specific. A set of targets observing one structural
phase is not a set of independent sensors merely because their scalar
innovations differ. Shared contributors include the structural state itself,
phase-reference offsets, radar oscillator/array errors, target association,
acceleration prediction, and common time alignment. `N_eff = 1/sum(w_i^2)`
only describes weight concentration; it is not an independent-target count.

Existing structural radar work in the local library commonly uses a best target,
FIR/acceleration fusion, or target-wise scalar weighting. That is useful prior
art but does not establish a full truth-error covariance for the thesis's
common-state update. The defensible novelty boundary is therefore:

> multi-target observations are projected to one structural state and fused
> with a declared covariance model; if cross-correlation is unknown, report a
> conservative or abstaining route rather than label diagonal weights as GLS.

## 4. Paper-ready related-work gap statement

The following paragraph is supportable after the DOI checks above:

> Prior mmWave structural-monitoring studies establish range-angle phase
> tracking, multi-target vibration extraction, and acceleration-assisted phase
> unwrapping. Array-processing studies establish profile likelihood,
> variable-projection, spatial-smoothing, and array-error models, while sensor
> fusion studies establish the need to account for unknown cross-correlation.
> These strands are usually evaluated separately: angle estimators report peak
> or localization accuracy, structural-radar studies often assume a separable
> target or a short excitation-based conversion-factor calibration, and fusion
> studies do not model the shared complex radar phase of natural scatterers.
> The remaining gap is a calibration-frozen, phase-preserving target path that
> converts only identifiable range-angle components into a common structural
> state and reports split/merge/abstain and covariance consistency when the
> components are correlated or unresolved.

This paragraph deliberately says “remaining gap” rather than “no prior work”:
the cited components are established, and the thesis contribution is their
explicit coupling plus an auditable validity boundary.

## 5. Minimum evidence still needed

No new experiment was run for this note. The smallest evidence set is:

1. **Calibration fence:** freeze target support, continuous AoA, beta, phase
   offsets, and any covariance from a declared prefix; verify that test-only
   perturbations do not update them.
2. **Coherent same-range probe:** vary angle spacing, source correlation,
   amplitude ratio, SNR, and snapshot count; compare covariance MUSIC/FBSS with
   direct profile residual and an abstention rule.
3. **Common-state fusion probe:** estimate a full or block residual covariance
   from calibration observables only; compare diagonal weighting, full GLS,
   and a conservative unknown-correlation route; report condition number, NIS,
   empirical coverage, bias, RMSE, and abstention.
4. **Natural-target transfer:** repeat the accepted route with natural
   scatterers or target changes while keeping the geometry fence explicit; do
   not transfer corner-reflector separation results into a field-accuracy
   claim.

These are design requirements only. They do not authorize a large seed matrix.

## DOI status

Verified in this note: 10.1109/29.57542, 10.1088/0266-5611/19/2/201,
10.1109/8.509886, 10.1109/78.709536, 10.1109/TASSP.1985.1164649,
10.1016/j.ymssp.2022.109178, 10.1109/RADAR.2018.8378778,
10.1109/ICIF.2002.1020908, 10.1016/j.automatica.2022.110168, and
10.1002/acs.2571.

No DOI was asserted for the thesis's exact local complex profile-LS objective,
for which the references above are methodological neighbors. The note also
does not use the DOI of a 3D multi-radar paper as evidence for the single-radar
beta or covariance claim.
