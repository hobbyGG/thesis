# Frozen beta / angle pilot: short conclusion

Date: 2026-10-03  
Scope: two bounded local pilots only; no cloud 400–402 reproduction and no
40-seed matrix.

## What the pilots establish

1. The earlier `0.005 mm RMS`, seed `20261001`, `0/-1/+1°` pilot changes both
   the angle-derived beta and the fixed-angle pseudoinverse steering used to
   extract test IQ. It is therefore a **joint steering-plus-beta sensitivity**
   test. It is not a beta-only perturbation.
2. The same combined route at `0.05 mm RMS` gives finite coverage 100% for all
   three routes and, using a common test-prefix reference, RMSE values of
   `0.002084585 mm` (0°), `0.001871346 mm` (-1°), and `0.002326791 mm` (+1°).
   The per-target beta values and the projection identity
   `sec(theta+delta)/sec(theta)-1` are in the pilot report. The identity is an
   explanation of pure scale sensitivity, not a score or tuning rule.
3. The original score reference used the full-record first 21 frames (`elapsed
   <= 0.20 s`), while the retained Kalman cold start uses the first 20 **test**
   frames for phase bias and residual-R initialization. The 0.05 mm pilot
   reports both: primary matched-test-prefix scores and legacy-reference scores.
   The reference difference is `0.001411045 mm` in this pilot.
4. Strict calibration-only initialization remains unresolved: test-prefix bias
   and initial-R cold start still occur inside the retained Kalman route. The
   geometry/target/beta fence is calibration-only, but the phase-reference and
   covariance initialization are exploratory.

## Wording allowed in the thesis

> In a bounded synthetic calibration-frozen diagnostic, a declared angular
> perturbation was applied to the frozen steering geometry and its derived beta
> while target identity and range were held fixed. The resulting signed bias and
> RMSE were scored only after estimation. The diagnostic quantifies sensitivity
> under the stated geometry and initialization protocol.

> The implementation obtains range-angle geometry from a calibration prefix and
> freezes it for test projection; this removes a separate excitation-based DCF
> fitting stage under the declared fixed-geometry model.

## Wording forbidden

- “The ±1° pilot is a beta-only experiment.”
- “The result reproduces the cloud profile-LS or the missing 400–402 artifact.”
- “Strict held-out calibration-only estimation is already demonstrated.”
- “The method needs no calibration at all.”
- “Vehicle or excitation changes necessarily change beta.”
- “0.01 mm or field accuracy is established.”
- “The pilot proves causal multi-target superiority over a single target.”

## Artifacts

- `pilot_frozen_beta_angle_v1_seed20261001_low_motion_0p005mm/`: 0.005 mm
  pilot, joint steering-plus-beta sensitivity.
- `pilot_angle_0p050mm_seed20261001/`: 0.05 mm pilot, matched-reference and
  legacy-reference scoring, per-target beta and theoretical projection error.
- `MA2026_KALMAN_BETA_AUDIT_2026-10-03.md`: Ma 2026 DCF evidence boundary.

No raw arrays are retained by either pilot. No GitHub push was attempted.
