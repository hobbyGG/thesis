# Conservative selector smoke: seed 213

This is one new six-scene smoke using only calibration features for routing.
The old corrected-v2 12-seed record and seed-212 selector output are unchanged.

## Results

The selector accepted `3/6` scenes and abstained on `3/6`. All accepted
outputs had post-run RMSE at or below `0.01 mm`.

| Scene | Calibration action/reason | Selected coverage; RMSE mm | Independent merge RMSE mm | Independent split-LS RMSE mm |
|---|---|---:|---:|---:|
| `close_benign` | merge: one peak `[26.75°]` | 1/1; `0.001543` | `0.001543` | rejected: one peak |
| `separated_benign` | split-LS: span `55.50°`, projection gap `0.2800`, condition `1.1342` | 1/1; `0.002606` | `0.016430` | `0.002606` |
| `separated_unequal` | split-LS: span `55.75°`, projection gap `0.2870`, condition `1.1335` | 1/1; `0.003102` | `0.010090` | `0.003102` |
| `close_destructive` | abstain: span `21.75° < 30°` | 0/1; — | `0.052222` | `0.017018` |
| `coincident_cancel` | split proposal, then abstain: test-amplitude guard | 0/1; — | rejected by guard | rejected by guard |
| `symmetric_control` | abstain: projection gap `0.00535 < 0.05` | 0/1; — | `0.003174` | `0.003571` |

The selected-route output rate is therefore `3/6 = 50%`; accepted high-error
count is `0/3`. The three rejected rows retain independent-route diagnostics:
the destructive row had high errors under both routes, the cancellation row
failed both amplitude guards, and the symmetric row showed merge lower than
split while the projection-gap guard correctly abstained from choosing.

## Interpretation

The two calibration guards remove the two observed failure patterns without
reading truth or post-run error. They also intentionally reduce coverage. This
is evidence for a conservative abstention policy on the fixed synthetic
mechanism, not evidence that the thresholds generalize or that the selector
chooses the lower-error route in all scenes.

The estimator input path is truth-free: `conservative_selector(iq)` uses the
calibration IQ, frozen angle grid, peak rule, steering condition, angular span,
and cosine-projection gap. Truth is passed to `score()` only after selection.
There is no fallback after a selected-route failure.

The smoke runner is scratch code and uses the NumPy-only peak-rule
reimplementation already recorded for seed212. The output is a compact
diagnostic, not a production algorithm result or a validation matrix.

## Minimum frozen holdout proposal

Before any broader claim, freeze the rule and run a paired holdout that varies
geometry near both boundaries while keeping the protocol and noise seed plan
fixed:

- angular span neighborhoods: `24°, 28°, 30°, 32°, 36°`;
- cosine-projection-gap neighborhoods: `0.00, 0.02, 0.05, 0.08, 0.12`;
- include benign, destructive-phase, and symmetric-projection controls;
- use at least one new seed per cell first, then expand only if package,
  truth-free, and guard checks pass;
- score selected output, abstention rate, and independent merge/split
  diagnostics on the same test aperture;
- predeclare false-accept and false-abstain counts, with no threshold changes
  from test truth.

This geometry-neighborhood holdout tests the decision boundary directly. A
noise-only seed expansion cannot establish that boundary.

