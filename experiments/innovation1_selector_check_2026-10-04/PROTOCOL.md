# Same-range selector check, one new seed

This is an independent scratch check for the deployable routing decision. It
does not modify the corrected-v2 estimator or its 72 recorded trials.

## Question

Does a truth-free rule choose merge, split-LS, or abstain from the calibration
IQ alone, and what happens when that chosen route is scored on the same test
window as the two independent routes?

## Frozen selector

For each trial, the selector builds the calibration Bartlett spectrum using the
existing v2 constants: centered eight-element half-wavelength ULA, angle grid
`-60°…60°` in `0.25°` steps, minimum peak separation `12°`, prominence at
least `1%` of the strongest spectrum power, second-peak power at least `18%`
of the strongest peak, and at most two peaks.

- zero calibration peaks: abstain;
- exactly one calibration peak: choose `merge`;
- two calibration peaks: compute the steering condition; choose `split_ls` if
  condition number is at most `20`, otherwise abstain;
- run only the selected route; if its test amplitude guard or finite-output
  guard fails, abstain;
- never fall back from a failed selected split route to merge.

The implementation uses a small NumPy-only local-maximum/prominence routine so
the check can run in the available environment without changing the frozen
rules. It is a scratch reimplementation of the v2 peak rule, recorded with a
source hash; it is not production code.

## Data and scoring

The six v2 scenes are regenerated at one new seed, `212`, with the v2 generator
and noise constants. The first 128 frames are calibration and the last 128 are
the test window. The selector sees IQ and fixed instrument constants only.
The generator truth is passed to `score()` only after selection and estimation.

For every scene, the output records:

- selector decision, candidate angles, condition number, and abstention reason;
- selected-route coverage and waveform RMSE on the 128-frame test window;
- independent merge and split-LS route coverage/RMSE on that same window;
- post-run diagnostic `high_error_gt_0p01mm` for accepted outputs. This label
  is never used by the selector.

“Error acceptance” therefore means a selector-accepted finite output whose
post-run RMSE exceeds `0.01 mm`; it is an evaluation label, not a routing
criterion. A rejection is an explicit abstention reason, not a zero-filled
estimate.

## Stop conditions

Stop and mark the check invalid if truth, scene labels, or post-run RMSE enter
the selector; if selector and independent routes use different IQ or scoring
frames; if the source/protocol hash is absent; or if a selected-route failure
silently falls back to another route.

This one-seed check does not establish generalization, a universal angular
threshold, real-radar performance, field accuracy, or a `0.01 mm` guarantee.
