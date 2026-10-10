# Ma 2026 acceleration-aided Kalman / beta audit

Date: 2026-10-03  
Scope: independent additive note for the thesis mainline. This note does not
modify `AUDIT_NOTE.md`, `NEXT_PROTOCOL.json`, `DOI_SUPPLEMENT_2026-10-03.md`,
or the algorithm. It records the evidence boundary for the Ma 2026 prior and
for the thesis claim that a dedicated excitation-based beta fit is removed.

## 1. Bibliographic verification

| Field | Verified record |
|---|---|
| Title | Zhanxiong Ma, Tongtong Zhang, Yang Zhu, Shuhan Lin, Jigu Lee, Hoon Sohn, Qiangqiang Zhang, “Acceleration-aided Kalman filtering for joint phase denoising and unwrapping in FMCW radar-based displacement monitoring.” |
| Venue / year | *Mechanical Systems and Signal Processing*, 2026, journal article. |
| DOI | **10.1016/j.ymssp.2026.113991**. The exact-title ScienceDirect abstract record exposes this DOI; the KAIST record independently confirms the title, author list, and peer-reviewed journal output. |
| Publisher / institutional records | [ScienceDirect abstract record](https://www.sciencedirect.com/science/article/abs/pii/S0888327026001482); [KAIST record](https://pure.kaist.ac.kr/en/publications/acceleration-aided-kalman-filtering-for-joint-phase-denoising-and/fingerprints/). |
| Access limit in this pass | The ScienceDirect full page returned HTTP 403, so equation numbers and every implementation detail were not re-read from the PDF in this run. The abstract search snippet is still direct publisher metadata and states the beta calibration operation quoted below. |

The previously encountered candidate `10.1016/j.ymssp.2026.114434` belongs to
a different Ma paper (“Simultaneous displacement and rotation estimation for
flexible ...”), so it must not be attached to this Kalman paper.

The publisher abstract snippet states: “a direction conversion factor is
calibrated by band-pass filtering radar- and acceleration-derived phases.”
The publisher page also describes a collocated radar/accelerometer setup and an
acceleration-aided Kalman framework for joint phase denoising and unwrapping.
These are source facts; the detailed calibration window, regression equation,
and acceptance rule still need the full text or a local copy for equation-level
citation.

## 2. Short evidence table

| Question | Original source / local record supports | Transferable inference for this thesis | Still needs experiment or full-text check |
|---|---|---|---|
| Is Ma's beta a pure geometry lookup? | **No.** The publisher abstract explicitly says the direction conversion factor is calibrated by band-pass filtering radar- and acceleration-derived phases. Local `docs/innovation_points.md:7-10` records the same prior boundary: a short synchronized radar/accelerometer phase interval is used before online processing. | The prior beta/DCF is an excitation-assisted estimate, even though the physical direction factor has a geometric interpretation. The thesis can accurately say it removes dependence on a separate excitation-based DCF file under its declared fixed-geometry model. | Retrieve the paper PDF and record the exact filter bands, fitting statistic, calibration duration, and target-selection rule. Do not cite an equation number until this is done. |
| Does vehicle/excitation change necessarily change beta? | The source says calibration uses signal phases, but the available metadata does not claim that beta is a function of vehicle identity or excitation class. | Under fixed radar pose, target position, and structural motion direction, `q_struct = beta q_los` and `beta = 1/|cos(theta)|` contain no vehicle or excitation variable. Changing excitation alone should not change the ideal geometric beta. | Fixed-geometry low/nominal excitation comparison: estimate beta by both routes, report beta drift and uncertainty, and separate geometric bias from weak-excitation fit failure. |
| When can a frozen beta become mismatched? | Local thesis docs explicitly retain installation direction, angle convention, array geometry, and target identity as conditions; the prior DCF is target/installation dependent. | A mismatch can arise from mount/structure rotation, changed target or effective scatterer, changed structural mode/translation direction, target association, multipath/mixed scatterers, or a weak/poorly conditioned excitation fit. These are mechanisms, not evidence that every vehicle change changes beta. | Hold excitation fixed and vary one geometry/target factor at a time; include target dropout/switch and a small rotation perturbation. |
| What information is online in the Ma prior? | Title/abstract support acceleration-aided Kalman phase prediction, and the abstract says beta is calibrated from band-passed radar/acceleration phases before recursion. Local review describes a synchronized calibration stage followed by online phase processing. | The thesis may characterize Ma as requiring a dedicated pre-run or calibration interval that uses an acceleration-derived displacement/phase relation. It should not claim that Kalman recursion itself is the novel contribution. | Full text needed to distinguish a one-time pre-run, a rolling update, or a startup-only fit and to determine whether beta is frozen for a record. |
| Is IQ-angle startup initialization “no calibration”? | Current implementation computes AoA from the record's IQ/range-angle data, forms beta, and freezes it for that record (`docs/innovation_points.md:20-37`; `docs/current_research_data_flow.md:382-398`). It does not fit beta against acceleration displacement. | This satisfies “no independent offline excitation fit” if the protocol declares the angle/beta prefix and forbids later test updates. It is still a record-level geometric initialization/calibration stage, so use “免离线方向转换因子拟合” rather than “完全不需要标定”. | Run a startup-fence check: only declared prefix frames may determine target/AoA/beta; test-only perturbation must not change frozen fields. Report initialization duration and cold-start bias separately. |

## 3. Geometry, excitation, and identifiability

With the thesis sign convention,

```text
q_struct(t) = beta q_los(t),       beta = 1 / |cos(theta)|.
```

This is a geometric relation. If radar pose, target/scatterer, and structural
motion direction remain fixed, excitation amplitude, vehicle identity, or
vehicle speed is not an argument of the ideal beta. A change of excitation can
still change the *quality of an excitation-based estimate* because the filtered
signals may have low variance, poor band overlap, low SNR, or phase slips. A
band-pass slope estimate is then weakly identified even when the physical beta
is unchanged.

For a generic synchronized fit of structural phase `p_a` from acceleration and
radar LOS phase `p_r`, a slope-like estimate has the form

```text
beta_hat = argmin_b || W (p_a - b p_r) ||^2,
```

possibly after band-pass filtering, offset removal, and a paper-specific
normalization. This is a conceptual identifiability statement, not a claim
about Ma's exact objective. It requires nonzero weighted variance of `p_r` and
usable phase alignment. The thesis must not replace the paper's exact formula
with this schematic equation in a citation.

For angle-derived beta, first-order propagation away from grazing angles is

```text
d beta / d theta = beta tan(theta),
```

so an AoA error `delta_theta` gives approximately
`delta_beta ~= beta tan(theta) delta_theta`; sensitivity grows as the target
approaches 90 degrees. This is a thesis-side geometry inference and needs the
existing frozen-angle sensitivity probe; it is not a reported Ma result.

## 4. Boundary of the contribution claim

Supported wording:

> Under the declared fixed-geometry model, the proposed route removes the
> separate excitation-based direction-conversion-factor fitting stage: it
> obtains AoA from the current record, computes the geometric beta, freezes it
> for the declared record/calibration prefix, and then runs the acceleration-
> aided Kalman phase recursion.

Avoid these unsupported formulations:

- “beta is always invariant to vehicle, load, or excitation in the field”;
- “the method requires no calibration at all”;
- “acceleration-aided Kalman filtering is a new algorithm”;
- “cross-excitation cannot cause failure.”

The defensible distinction is **geometry invariance versus estimator
identifiability**: vehicle excitation does not enter the ideal geometric beta,
but it can expose a weak calibration fit, change which structural mode or
motion direction dominates, or change target visibility and association.

## 5. Minimal design-only validation set

No experiment was run for this note. The smallest follow-up set is:

1. **Fixed geometry / two excitation levels.** Keep radar pose, target, and
   motion direction fixed. Compare IQ-only angle beta with the Ma-style
   acceleration/radar phase fit under nominal and weak excitation. Report beta
   estimate, fit condition/variance, phase residual, and displacement bias/RMSE.
2. **Same excitation / geometry or target change.** Keep excitation fixed and
   change one of mount angle, structural motion direction, or target identity.
   Test whether frozen-beta residuals follow geometry/target rather than the
   vehicle label.
3. **Weak-excitation abstention.** Reduce amplitude or SNR with geometry fixed;
   record beta uncertainty and a declared abstention condition instead of
   silently treating a poorly identified slope as a new beta.
4. **Startup fence.** Use only a pre-registered prefix for IQ target/AoA/beta
   initialization. Hash frozen fields and verify that test-only ADC changes do
   not update them. Do not equate this prefix automatically with an offline
   excitation calibration stage.

These are protocol items only; they do not authorize a 40-seed run or a change
to the algorithm.

## Provenance and status

- DOI status for Ma 2026: **verified** from the exact-title publisher abstract
  record and independently matching institutional metadata.
- Full-text equation-level beta details: **pending** because the publisher full
  page was inaccessible in this pass and the local `ref_papers` scan did not
  find the PDF under its title.
- Algorithm changes: none.
- Matrix/seed experiments: none.
- GitHub push: none.
- Existing user-owned notes and the unrelated
  `experiments/same_range_merge_mechanism/` directory were not modified.
