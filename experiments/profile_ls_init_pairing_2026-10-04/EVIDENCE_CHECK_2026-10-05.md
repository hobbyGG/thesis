# Evidence check: profile-LS initialization pairing and DOI sources

**Date:** 2026-10-05  
**Scope:** read-only archive/source audit; no experiment, production-code edit, or push.

## 1. Held-out archive and 2×2 pairing

The requested original directory is absent:

`experiments/same_range_geometry_reference_diagnostic/heldout_20261003/`

The local profile-LS directory contains only `PROTOCOL.md`, `PROTOCOL.json`, and
`run_when_archive_present.py`. There is no local seed-400/401/402 runner, capture
package or compact IQ artifact, manifest, calibration/test split, physical reference,
or prior compact output. A repository search found no matching `heldout_20261003`,
`seed400`, `seed401`, or `seed402` artifact.

`run_when_archive_present.py` is intentionally fail-closed: it requires the original
archive plus `protocol.json` and `manifest.json`, then stops before any estimator is
run. Therefore the Bartlett/profile-LS × cold/warm 2×2 comparison **cannot run from
the current checkout**. The protocol's intended comparison remains:

- identical IQ, calibration-only frozen geometry, downstream settings, and scoring reference;
- Bartlett-cold, profile-LS-cold, Bartlett-warm, profile-LS-warm;
- warm history must be legal pre-scoring history; if a 20-frame test-prefix warmup is
  used, every route scores from frame 220 and warmup latency is reported separately;
- report per-seed `D_cold`, `D_warm`, `D_warm-D_cold`, RMSE, finite coverage, and
  abstention. Truth and `q_proxy` are post-run scoring inputs only.

The separate 0.05 mm pilot and its reported initialization percentage cannot be used
to infer this geometry × initialization interaction. The protocol classifies the
recovered 400–402 item as a bounded mechanism diagnostic, not new held-out evidence.

## 2. DOI/source inventory

| DOI / source | Local status and verified facts | Boundary or limitation for this thesis |
|---|---|---|
| `10.1016/j.ymssp.2024.111888` — *Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion* | A 19-page local PDF exists, but it is image-only (`pdftotext` returns no text). The local primary-reference card and the institutional/publisher abstract identify the method: short synchronized radar/accelerometer calibration, multiple good targets and direction-conversion factors, occlusion detection/reconstruction, and post-recovery multi-target phase handling. DOI is verified by the institutional record and DOI metadata; page-level extraction remains pending. | This is continuity/occlusion management with acceleration assistance. It does not verify same-range angle splitting, profile-LS, or the present calibration/test fence. The local card still describes short calibration and good-target selection, so “no calibration” must not be claimed. |
| `10.1016/j.ymssp.2026.114434` — Ma et al., *Simultaneous displacement and rotation estimation for flexible structures through millimeter-wave radar and inertial sensor fusion* | Full 14-page PDF with DOI in PDF metadata. Abstract (p.1) derives LOS displacement with rotation, estimates initial rotation from IMU acceleration, and uses radar to decouple translation; laboratory displacement error is reported below 0.3 mm up to 6.5° rotation. The paper states a small-angle basis and a rotation-aware conversion-factor calibration (pp.2, 7): band-pass initial rotation and integrated angular velocity, then minimize their discrepancy; calibration is done once and reused. Quasi-static/ultra-low-frequency motion can make calibration unreliable (p.7). A 301-sample fusion window adds 1.5 s delay (p.9). The prior calibration fails under rotation in its setup (p.11: 38.135 mm displacement error with the wrong factor). | The result is a laboratory, two-dimensional rotation-aware fusion study, not evidence for profile-LS or same-range identifiability. Its <0.3 mm result is setup- and reference-specific; it cannot be transferred to the current algorithm or an LVDT-level claim. |
| `10.1016/j.measurement.2026.120848` — Lee et al., *Improved structural acceleration estimation using low-cost MEMS accelerometer and FMCW millimeter-wave radar* | Full 14-page PDF with DOI in PDF metadata. The abstract (p.1) combines low-frequency radar and high-frequency MEMS acceleration with an FIR complementary filter; lab tests use 0.1 and 3.0 Hz and a bridge test reports relative RMSE reductions of 85.4%, 82.5%, and 64.5% versus the MEMS baseline at 20/50/80 km/h. The method text (p.2) selects an optimal radar target and estimates a vertical-displacement conversion factor during a short initial calibration, then fuses the signals. | This is acceleration estimation and best-target conversion-factor calibration. It does not establish multi-target shared-state fusion, same-range angle separation, profile-LS, or held-out frozen geometry. The reported percentages are relative to that paper's MEMS baseline and test conditions. |
| `10.3390/rs14092005` — Wang et al., *Fast Displacement Estimation of Multiple Close Targets with MIMO Radar and MUSICAPES Method* | No local full text was found. The publisher record/abstract is web-only: SISO range processing cannot separate close targets in the same radial-range cell; MIMO angular MUSIC separates them and APES recovers target phases while reducing mutual interference. Full-text page verification is pending because the publisher request was unavailable during this audit. | This is direct prior art for same-range, different-angle separation and phase recovery. A novelty claim should be downstream geometry-to-structural-state calibration/fusion and the frozen calibration fence, rather than basic same-range separation itself. |

Local full-text links: [Ma 2026 B42 PDF](/Users/umep/thesis/ref_papers/02_recent_uncollected/B42_Simultaneous_displacement_and_rotation_estimation_for_flexible_structures_through_millimeter-wave_radar_and_inertial_sensor_fusion.pdf), [Lee 2026 PDF](</Users/umep/thesis/ref_papers/00_primary_references/Improved structural acceleration estimation using low-cost MEMS   accelerometer and FMCW millimeter-wave radar.pdf>), and the image-only [occlusion paper PDF](</Users/umep/thesis/ref_papers/00_primary_references/Accelerometer-aided millimeter-wave radar interferometry for uninterrupted bridge displacement estimation considering intermittent radar target occlusion.pdf>). The Wang paper is available from the [MDPI publisher record](https://www.mdpi.com/2072-4292/14/9/2005) and DOI [10.3390/rs14092005](https://doi.org/10.3390/rs14092005).

## 3. Claim boundary and minimum next checks

**Literature facts:** the four source records above support (i) acceleration-assisted
radar displacement with short conversion-factor calibration, (ii) rotation-aware
one-time calibration and its small-angle/quasi-static limits, (iii) radar/accelerometer
complementary fusion, and (iv) MIMO same-range angular separation plus phase recovery.

**Transferable inference:** the thesis can motivate a geometry-calibration and
structural-state/fusion contribution around these precedents, provided calibration
frames are fenced from scoring frames. It cannot present same-range angle separation,
best-target conversion-factor fitting, or radar/accelerometer fusion as unexplored by
itself.

**Still unverified:** no 400–402 held-out evidence, no matched 2×2 interaction, no
page-level extraction for the image-only 111888 PDF, and no local full text/page
verification for 2005. None of the cited paper-specific errors or relative RMSE
reductions proves the current method's accuracy or LVDT equivalence.

Minimum design-only follow-up after the exact archive is restored:

1. Verify source/manifest hashes, seed list, calibration/test split, physical reference,
   and route configurations; run the fail-closed preflight and one seed first.
2. Only then run the four paired routes on identical IQ with frozen calibration-only
   geometry and common scoring frames; retain the stated stopping rules and do not
   launch a 40-seed expansion.
3. Obtain page-addressable text for 111888 and the Wang article before using either
   for page-specific claims.

