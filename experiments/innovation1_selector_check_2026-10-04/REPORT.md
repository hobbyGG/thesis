# Same-range selector check: seed 212

This report evaluates one automatic truth-free route decision on the six
corrected-v2 scenes. It leaves the original 12-seed/72-trial record unchanged.
The selected route is chosen from calibration IQ, then scored on the same 128
test frames used by the independent merge and split-LS routes.

## Result

The selector accepted 5/6 scenes and abstained on 1/6. Its decisions were:

| Scene | Calibration peaks | Decision | Selected coverage / RMSE mm | Independent merge RMSE mm | Independent split-LS RMSE mm | Post-run diagnostic |
|---|---:|---|---:|---:|---:|---|
| `close_benign` | `[26.75]` | merge | 1/1; `0.001310` | `0.001310` | rejected: fewer than two peaks | accepted, below `0.01 mm` |
| `separated_benign` | `[-10.25, 45.25]` | split-LS | 1/1; `0.002220` | `0.017496` | `0.002220` | accepted, below `0.01 mm` |
| `separated_unequal` | `[-10.00, 45.75]` | split-LS | 1/1; `0.002395` | `0.010332` | `0.002395` | accepted, below `0.01 mm` |
| `close_destructive` | `[16.75, 38.50]` | split-LS | 1/1; `0.024401` | `0.017580` | `0.024401` | **accepted high error**; false destructive peaks, split worse than merge |
| `coincident_cancel` | `[28.75, -31.75]` | split-LS proposal | 0/1; rejected by test-amplitude guard | rejected by test-amplitude guard | rejected by test-amplitude guard | false two-peak proposal was rejected |
| `symmetric_control` | `[-24.25, 23.75]` | split-LS | 1/1; `0.004499` | `0.003698` | `0.004499` | accepted, but merge was lower by `0.000802 mm` |

Coverage therefore reflects the declared guards, not correctness of the
detected geometry. The coincident-cancellation row is useful because the
selector proposed a split from noise-induced peaks but the amplitude guard
prevented an output. The close-destructive row shows the remaining failure:
the selector accepted a finite split estimate with RMSE above `0.01 mm`.

Among five accepted outputs, one was high-error by the descriptive
post-run threshold `RMSE > 0.01 mm`. In two accepted rows
(`close_destructive` and `symmetric_control`), the selected route had higher
RMSE than the other independently scored route. Those comparisons use truth
only after routing and are diagnostics; they are not selector inputs.

## Truth-free audit

`selector(iq)` calls calibration geometry, the frozen peak rule, steering
conditioning, and the selected route's amplitude/finite guards. It does not
receive the scene name, source angles, amplitudes, phases, generated `q`, or
any RMSE. Truth appears only in `score(route, qhat, truth)` after both routing
and estimation. The selector never falls back from a failed split route to
merge.

The scratch runner uses a NumPy-only local implementation of the declared v2
local-maximum/prominence rule because the available environment has no SciPy.
It is recorded with a source hash and is not production code. The one-seed
result should therefore be treated as a routing smoke check, not as a new
validation matrix or replacement for the tracked v2 record.

## Safe interpretation

This check supports the narrower statement that the frozen calibration-only
geometry rule can produce an explicit merge/split/abstain decision without
truth leakage on one new seed. It does not support claiming that the rule
chooses the lower-error route in general, that finite coverage means correct
angle separation, or that the mechanism reaches field or `0.01 mm` accuracy.
The next minimum step is a pre-registered paired seed set using the same
selector and a declared error/abstention policy, without tuning on truth.

