# NEW SYNTHETIC HELD-OUT EXPERIMENT: bounded profile-LS vs Bartlett

Status: new synthetic experiment, independent of the missing historical
400–402 archive. It must not be described as a 400–402 recovery or as field
validation.

## Fixed package and estimator model

- centered eight-element half-wavelength ULA, nominal element coordinates
  `[-3.5,…,3.5]` in half-wavelength spacing, `lambda = 4 mm`;
- 256 slow-time IQ frames at 100 Hz; frames `0–127` are calibration and
  `128–255` are test;
- one common structural displacement
  `q(t) = 0.8 sin(2 pi 3 t + p) + 0.2 sin(2 pi 5 t + 0.43 - 0.2 p) mm`;
- fixed complex noise sigma `10^(-35/20)/sqrt(2)` per real/imag coordinate;
- one off-grid source per seed; the generator uses true angle, beta scale, and
  actual array positions only to generate IQ and truth.

The estimator sees IQ plus nominal array constants. It never receives true
angle, true beta scale, true positions, `q`, or any truth-derived score.

## Three new seeds and predeclared mismatch strata

| Seed | True angle | Beta scale in generator | Position mismatch in generator |
|---:|---:|---:|---|
| 4101 | `17.37°` | `1.000` | zero |
| 4102 | `17.83°` | `1.015` | fixed nominal-position offsets `[0,.015,-.010,.020,-.012,.008,-.018,.005]` |
| 4103 | `18.21°` | `0.985` | the same fixed offsets |

The position offsets are in nominal half-wavelength spacing units. The angle is
off the Bartlett grid in every seed. Beta/geometry mismatch is generated only
for seeds 4102–4103 and is never fitted from truth.

## Calibration-only geometry routes

**Bartlett.** Form the calibration covariance and choose the strongest angle on
the fixed `-60°…60°`, `0.25°` grid.

**Bounded profile-LS.** Around the Bartlett angle, search only
`[theta_B - 1.5°, theta_B + 1.5°]` at `0.01°` increments. For each candidate,
eliminate one complex nuisance coefficient per calibration snapshot by least
squares and minimize the normalized residual

```text
||Z_cal - c(theta) a(theta)^T||_F^2 / ||Z_cal||_F^2.
```

This is a bounded separable/profile least-squares refinement. Both routes freeze
their angle before any test-frame processing.

## Shared downstream conversion

For either frozen angle, beamform test IQ with the nominal steering vector,
unwrap phase, and convert with the same fixed geometric factor
`lambda/(4 pi cos(theta_hat))`. The generated beta scale and position mismatch
remain unmodeled. Both routes use the same amplitude/finite guard:
minimum test magnitude must exceed `5 * noise_sigma * extraction_gain`.

## Cold and legal warm initialization

- **Cold:** estimate every test frame relative to test frame 128.
- **Warm:** use test frames 128–147 only as a legal prefix, then reset the
  phase reference at frame 148 and score frames 148–255. No truth or fitted
  offset enters the prefix.

For a fair paired comparison, cold estimates are rebased at frame 148 using the
cold estimate itself and are scored on the same frames 148–255 as warm. Report
cold full-test RMSE on frames 128–255 separately. Warm and cold dynamic proxy is
the RMSE of first differences on the shared score window.

## Post-run metrics and stop conditions

Per seed and route report angle, objective/peak diagnostics, finite coverage,
full-q RMSE, paired-window RMSE, and first-difference dynamic-proxy RMSE. Report
median and per-seed values across the three seeds.

Stop and invalidate a row if calibration geometry reads test/truth data, if the
profile search leaves its bounded interval, if the physical reference differs,
if guard failures are converted to estimates, or if cold/warm score windows
cannot be aligned from estimator-side samples.

This experiment can support only a bounded synthetic mechanism comparison. It
does not support historical 400–402 recovery, field accuracy, an LVDT claim, or
an absolute `0.01 mm` result.

