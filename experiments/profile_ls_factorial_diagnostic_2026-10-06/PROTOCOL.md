# Matched factorial diagnostic: profile-LS vs Bartlett

This is an independent follow-up to the NEW SYNTHETIC HELD-OUT experiment. It
does not alter the 4101–4103 results and is not historical 400–402 recovery.

## Matched factors

Use three common-random-number blocks (`4201`, `4202`, `4203`). Every block
shares the same off-grid true angle `17.37°`, motion phase, complex noise array,
amplitude, phases, frame split, and scoring reference across all three factor
conditions:

| Factor | Beta scale | Array-position mismatch |
|---|---:|---|
| `offgrid_only` | `1.000` | zero |
| `offgrid_beta` | `1.015` | zero |
| `offgrid_array` | `1.000` | `[0,.015,-.010,.020,-.012,.008,-.018,.005]` nominal half-wavelength units |

This isolates beta and array-position effects while preserving the same IQ
noise realization inside each block. The source angle is off the Bartlett grid
in every factor.

## Routes and scoring

Use the same bounded Bartlett and profile-LS estimators as the preceding
synthetic experiment. Run both cold and legal warm prefix initialization. All
four routes are scored on the same frames `148–255`: cold estimates are
rebased at frame 148 using estimator samples; warm consumes frames `128–147`
and starts its reference at frame 148. Truth is used only after estimation.

For every row report finite/amplitude coverage, RMSE, first-difference dynamic
proxy, angle error, phase residual bias/RMSE, and beta/geometry conversion
ratio error:

```text
conversion_ratio = beta_scale * cos(theta_true) / cos(theta_hat)
```

Profile-LS minus Bartlett differences are computed within each matched block;
factor medians and the beta/array interaction are descriptive. No threshold is
retuned on these results.

## Boundaries

The design can show whether profile-LS helps any controlled factor in this
array model. It cannot establish universal off-grid performance, field
accuracy, LVDT equivalence, or an absolute `0.01 mm` result.

