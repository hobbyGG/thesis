# Same-range selector geometry-neighborhood holdout

This independent scratch experiment tests the frozen conservative selector near
its two calibration thresholds. It does not modify corrected v2, seed212, or
seed213 outputs.

## Cells and seeds

One new deterministic seed is assigned to each of nine geometry cells:

```text
span 24°, 28°, 30°, 32°, 36° at projection gap 0.05
span 30° at projection gaps 0.00, 0.02, 0.08, 0.12
```

For a requested span `s` and projection gap `g`, the generator uses a centered
pair `theta1 = c - s/2`, `theta2 = c + s/2`, with `c` solved so that
`|cos(theta1)-cos(theta2)| = g` before grid detection. The realized
calibration angles are recorded separately because the estimator uses the fixed
0.25° angle grid.

Each cell uses one seed for these applicable semantics:

- balanced benign pair: amplitudes `1/.8`, phases `.15/-.30`;
- unequal pair: amplitudes `1/.5`, phases `.15/-.30`;
- opposed-phase pair: amplitudes `1/1`, phases `0/pi`;
- coincident cancellation control: fixed angles `27°/27°`, amplitudes `1/1`,
  phases `0/pi`, independent of the requested cell geometry.

The exact `symmetric_control` semantic is represented by the span-30,
projection-gap-0 cell. The balanced pair in span cells below 30° corresponds to
the prior close-benign semantics; cells at or above 30° correspond to the prior
separated-benign semantics.

## Frozen route order

The selector receives calibration IQ and fixed constants only:

1. one detected peak: merge;
2. two peaks with span `<30°`: abstain;
3. two peaks with `abs(cos(theta1)-cos(theta2)) < 0.05`: abstain;
4. otherwise, condition number `<=20`: split-LS;
5. any amplitude or finite-output guard failure: abstain without fallback.

Truth is passed only to post-run scoring. For every row, selected output and
independent merge/split diagnostics use the identical 128-frame test aperture.
No threshold is changed using holdout error.

## Required outputs

Report per cell and semantic: requested/realized geometry, seed, action/reason,
selected coverage, selected RMSE when accepted, rejection count, accepted
`RMSE > 0.01 mm` count, and counterfactual merge/split RMSE. Summarize whether
actions are monotonic across each threshold neighborhood. This is a boundary
check, not a generalization claim.

