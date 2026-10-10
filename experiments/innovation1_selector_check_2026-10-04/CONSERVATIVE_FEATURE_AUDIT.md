# Conservative calibration-feature audit

The existing corrected-v2 compact output retains truth-free calibration
features. Across the 12 recorded seeds, the two cases of interest have these
ranges:

| Feature | `close_destructive` | `symmetric_control` |
|---|---:|---:|
| two-peak angular span | `21.75–22.00°` | `48.00–48.25°` |
| steering condition | `1.2473–1.2520` | `1.0982–1.1030` |
| calibration weight imbalance `|w1−w2|` | about `0.0001–0.0028` | about `0.2248–0.2270` |

The angle span and steering condition separate these two fixed scenes in the
stored records. Weight imbalance also separates them, but it is more tied to
the particular extraction and amplitude model. The direct LOS projection gap
`|cos(theta1)−cos(theta2)|` is the most interpretable near-equal-geometry
feature.

This is a development diagnosis. It does not prove general coherent-source
identifiability and uses no post-run RMSE, truth, or seed-212 score at route
time.

## Frozen conservative rule for the next smoke

After the existing Bartlett peak rule returns two angles, compute:

```text
span_deg = abs(theta_1 - theta_2)
projection_gap = abs(cos(theta_1) - cos(theta_2))
```

Abstain when `span_deg < 30°` **or** `projection_gap < 0.05`. Otherwise keep
the existing condition-number guard and select split-LS. One peak selects
merge; a failed test-amplitude or finite-output guard abstains; no fallback is
allowed.

The `30°` span guard catches the narrow destructive false-peak pattern in the
stored mechanism. The `0.05` projection-gap guard protects near-equal LOS
conversion factors such as the symmetric control. These are conservative
development guards for this fixed synthetic mechanism, not universal angle
thresholds.

