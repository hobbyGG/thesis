# NEW SYNTHETIC HELD-OUT EXPERIMENT: profile-LS vs Bartlett

This is a new synthetic calibration/test experiment. It does not restore or reproduce historical 400–402, and it does not modify production algorithm code.

## Protocol and truth boundary

- Three fresh seeds: `4101`, `4102`, `4103`.
- Calibration frames are `0–127`; test frames are `128–255`.
- Bartlett uses a fixed `0.25°` grid. Bounded profile-LS searches Bartlett ±`1.5°` at `0.01°` resolution with one complex nuisance coefficient per calibration snapshot.
- Cold scores all 128 test frames. Warm uses a legal 20-frame prefix and scores frames `148–255`; cold is also rebased and scored on that shared window for paired comparison.
- Truth is used only after geometry, phase extraction, and guard decisions.

## Per-seed results

| Seed / mismatch | Bartlett angle | Profile-LS angle | Bartlett cold full RMSE mm | Profile-LS cold full RMSE mm | Bartlett paired/warm RMSE mm | Profile-LS paired/warm RMSE mm | Bartlett dynamic proxy | Profile-LS dynamic proxy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 4101 (theta=17.37°, beta=1.0, pos=no) | 17.25° | 17.37° | 0.001671 | 0.001807 | 0.002365 | 0.002504 | 0.002429 | 0.002434 |
| 4102 (theta=17.83°, beta=1.015, pos=yes) | 17.75° | 17.80° | 0.014872 | 0.015158 | 0.012622 | 0.012882 | 0.002689 | 0.002710 |
| 4103 (theta=18.21°, beta=0.985, pos=yes) | 18.25° | 18.18° | 0.016358 | 0.016768 | 0.011936 | 0.012260 | 0.003061 | 0.003085 |

All 12 route rows were finite and passed the amplitude guard (`12/12` coverage). The profile objective remained bounded around the Bartlett angle, with profile angles moving toward the off-grid generator angles in seeds 4101 and 4102.

## Three-seed summary

| Route | Coverage | Median full/route-window RMSE mm | Median paired-window RMSE mm | Median dynamic proxy mm |
|---|---:|---:|---:|---:|
| bartlett / cold | 3/3 | 0.014872 | 0.011936 | 0.002610 |
| bartlett / warm | 3/3 | 0.011936 | 0.011936 | 0.002689 |
| profile_ls / cold | 3/3 | 0.015158 | 0.012260 | 0.002632 |
| profile_ls / warm | 3/3 | 0.012260 | 0.012260 | 0.002710 |

The paired-window median differences are profile-LS minus Bartlett:

- cold paired RMSE: `+0.000324 mm`;
- warm paired RMSE: `+0.000324 mm`;
- cold dynamic proxy: `+0.000021 mm`;
- warm dynamic proxy: `+0.000021 mm`.

These three seeds show off-grid angle movement without an accuracy gain under the declared beta/geometry mismatch strata. The result is a bounded synthetic mechanism observation and does not support a field, LVDT, or `0.01 mm` claim. It is independent of the missing 400–402 archive.

## Boundary and implementation checks

- Geometry is calibration-only and frozen before test processing.
- Profile search stays inside the declared Bartlett-centered ±1.5° bounds.
- Cold and warm use the same physical test IQ and downstream conversion; warm consumes only the first 20 test frames before the shared score window.
- No route fallback, truth-based sign/offset fit, or test-truth threshold tuning is present.
- The local checkout still lacks `experiments/same_range_geometry_reference_diagnostic/heldout_20261003`; this experiment must not be cited as its recovery.
