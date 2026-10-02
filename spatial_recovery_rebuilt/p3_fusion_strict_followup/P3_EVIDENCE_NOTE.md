# P3 strict follow-up evidence

This directory synchronizes `p3_strict_followup.tgz` from the cloud scratch
run.

- Archive size: 16,997 bytes
- Archive SHA-256: `bb70f35f8a300118c12e27730d23cafb3dafc4e24b3bf14dfd7fb3248edd327e`
- Extracted root: `strict_followup/`
- Six trials: seeds `20261001` and `20261002` crossed with stationary,
  0.005 mm RMS, and 0.050 mm RMS strata
- Estimator copies were truth-free and no raw captures were retained

## Strict score fence

Calibration geometry and target selection use frames 0–199. The retained
bias/initial-R warm-up uses test frames 200–219. Accuracy is scored only on the
tail frames 220–399 (180 samples), with truth opened after route outputs for
post-run scoring.

Across all six rows, common-state fusion has lower tail RMSE than the selected
single target, with common-vs-single reductions of 7.4%–27.3%. Common-vs-
independent-median reductions are 30.2%–55.7%. Common-route target innovation
Pearson correlations over frames 220–399 have median values about 0.591–0.619
(and maximum pair correlations about 0.726–0.881). These are innovation
correlations, not truth-error covariance; the independent-route correlations do
not prove independent measurement noise.

The reported `N_eff = 1 / sum_i(w_i^2)` is weight diversity only. It is not an
independent-target count or covariance-adjusted information measure. Off-
diagonal observation covariance was not estimated; the retained filter uses a
diagonal approximation.

This is preliminary mechanism evidence only. It does not make a causal fusion
gain claim or a calibrated uncertainty claim. The routes share geometry, beta,
acceleration, phase-bias and initial-R construction, and the six paired rows
use only two seeds. Strict calibration-only bias/R initialization remains an
API limitation and was not implemented; no tracked thesis source was changed.
