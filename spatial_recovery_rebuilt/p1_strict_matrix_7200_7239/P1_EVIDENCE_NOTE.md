# P1 strict calibration-only matrix evidence

This directory is a local synchronization of the updated cloud P1 artifact
`strict_p1_matrix_7200_7239(1).tgz`.

- Archive size: 134,312 bytes
- Archive SHA-256: `353fe77644346bb0f8aea605282fbee21203e993eae9cf0baed377fd271801b4`
- Extracted root: `strict_matrix_7200_7239/`
- Contents: compact JSON summaries, per-trial JSON records, the strict runner,
  and smoke/full protocols and manifests; no raw capture arrays are retained.

## Full matrix evidence

The full route uses 40 seeds (`7200`–`7239`) across five strata (stationary,
0.005, 0.010, 0.020, and 0.050 mm requested `q_true` RMS), for 200 trials.
It freezes calibration geometry from frames 0–199, uses test frames 200–399 for
phase/Kalman input, and performs no test-side target detection, selection,
MUSIC/ML angle refinement, or angle-derived beta update.

- Accepted: 191/200
- Abstention/error trials: 9/200
- All-trial success rate, counting abstentions as failures: 0.955
- Accepted-only pooled RMSE: 0.001355051626199677 mm (1.355051626 um)
- Accepted-only mean-of-trials RMSE: 0.0013242379858395496 mm (1.324237986 um)
- Each trial record preserves realized `q_true` and `q_proxy` RMS for the full, calibration, and test windows.
- The nine rejects are frozen test ADXL guard failures (`acceleration_within_frozen_limit=false`), at seeds 7227 and/or 7238 by stratum; no estimator score is claimed for those trials.

The test-only perturbation probe reports `first_200_exactly_unchanged=true`,
no truth in estimator copies, no changed frozen geometry fields, and a changed
test observation. The full manifest reports `guards_fixed_before_test=true`,
`test_target_detection_executed=false`, `full_window_route_called=false`, and
truth-free estimator copies.

Geometry, angle, and beta are calibration-only. The frozen-test ADXL guard still
checks frames 200–399, and rejected trials never enter the estimator. Therefore
the 191/200 coverage and accepted-only RMSE are conditional on test-window
quality screening; they are not test-free online performance.

## Evidence limits retained with the result

- Every accepted trial starts a fresh retained Kalman state on test frames
  200–399; this is a cold start and is not comparable to a warm full-window
  state.
- The 21-frame score reference and truth alignment are post-run diagnostics;
  they do not establish online unbiasedness or deployment behavior.
- Retained adaptive `R` settings were not independently calibrated or
  identified by this matrix.
- The current retained frontend defines beta as `1/abs(cos(theta))`. That is
  numerically equivalent to signed beta only for the current positive-cos
  angles (less than 25 degrees); the general mounting sign remains unvalidated.
- The compact estimator copies are truth-free according to the manifest, but
  non-truth scratch files and estimator-copy provenance still need a separate
  audit before treating this as publication-ready evidence.
- `claims_parity_with_lost_workspace=false`; this is reconstructed evidence,
  not a parity claim with unavailable prior results.
