# RO-all-channel baseline: executable design (blocked)

Status: design-only.  This file deliberately does not add an estimator or
change tracked `algorithm/` code.  It is the smallest route that can be
implemented after the missing beta/backend decisions are reviewed.

## Fair fence and observable input

- One shared package: `adc_cube` is `[400, 8, 256]` complex64 and ADXL is
  `[4000, 3]` float64.
- Calibration is radar frames `[0:200]` and ADXL samples `[0:2000]`.
- Frozen test is radar frames `[200:400]` and ADXL samples `[2000:4000]`.
- The estimator may read raw ADC, ADXL structural-axis samples, and monotonic
  timestamps only.  It must not read `truth/`, `q_proxy`, paper response
  metadata, target bins/angles, array positions, or post-run metrics.

## Calibration route

1. Compute `X = fft(adc_cube[0:200], n=256, axis=-1)`, retaining all eight
   virtual channels.  No angle FFT, steering matrix, DBF, MUSIC, or ML call is
   permitted.
2. Form one declared range statistic, `E[r] = median_t(sum_v |X[t,v,r]|^2)`.
   On bins 1..254, retain local maxima above
   `max(median(E)+6*MAD(E), 4*median(E))`, enforce a 3-bin minimum separation,
   and keep at most `K=5` bins.  Record the actual range-bin count.  No RA
   target count or target indices may be copied.  If no bin passes, the branch
   abstains.
3. For each selected bin, remove fixed channel phase offsets learned only from
   calibration, `c_v = exp(j*(angle(mean_t X[t,v,r]) - angle(mean_t
   X[t,0,r])))`.  Use the all-channel projection `z[t,r] = (1/8) * sum_v
   conj(c_v) * X[t,v,r]`.  The phase origin is the channel-0 calibration
   reference; this is a nuisance phase alignment only and produces no angle or
   geometry estimate.
4. Estimate one scalar phase-noise variance per range bin from calibration
   residuals after the common phase is removed: `e_t = wrap(angle(z_t) -
   median_v(angle(conj(c_v)*X[t,v,r])))`, `R=(1.4826*MAD(e))^2`.  Treat the
   eight channels as correlated views (shared target/PLL terms); do not sum
   eight independent precisions.  Require a finite fraction >=0.99 and a
   nonzero aligned mean amplitude; otherwise abstain.

## Beta decision (the current blocker)

Range-only ADC data cannot identify the structural conversion
`beta=1/|cos(theta)|`.  A real branch must select one of these explicit modes:

- `fixed_identity_los`: set `beta=1` and report line-of-sight displacement.  It
  is numerically valid but cannot be scored as structural displacement against
  the retained RA branch.
- `adxl_phase_fit`: integrate the calibration ADXL axis to a displacement
  reference `u(t)` and fit each unwrapped projected phase to
  `a0 + a1*t + a2*t^2 + gamma*u(t)`.  Derive
  `beta=(4*pi/lambda)/abs(gamma)` only when an excitation, finite-fit,
  condition-number, and residual-quality guard passes; otherwise abstain.
  Stationary and the requested low-motion strata are expected to fail this
  guard at the current ADXL noise level.  The fit is a candidate observable
  design, not a validated estimator.

`q_proxy`/truth phase fits are diagnostic only and are forbidden estimator
  inputs.  Until one beta mode and its thresholds are approved, there is no
  scientifically defensible structural RO baseline.

## Frozen test route

Compute `fft(adc_cube[200:400], axis=-1)`, apply only the calibration-frozen
range bins, `c_v`, projection, quality mask, beta, and phase convention.  Do
not re-detect peaks, refit channel weights, update beta, or inspect test values
when choosing geometry.  Preintegrate the test ADXL samples with the shared
timestamps.  Emit one observation row per selected range bin (not one row per
virtual channel); preserve the scalar `R` estimated above and record the
calibration/test source ranges in metadata.

## Minimal code contract after approval

Create a scratch-only `ro_all_channel.py` with three pure entry points:

```text
fit_calibration(adc_cal, adxl_cal, radar_time_cal, adxl_time_cal, cfg)
    -> ROCalibration(range_bins, channel_phase, combine_weights, beta,
                     initial_r, quality, provenance)
observe_frozen(adc_test, radar_time_test, frozen_calibration)
    -> ROObservations(wrapped_phase, available, selection_scores, provenance)
run_ro(observations, acceleration, cfg)
    -> ROResult(q_hat_m, beta_hat, r_history, extra)
```

`ROCalibration.provenance` must include `route=ro_all_channel`,
`geometry_source=calibration_frames_0_199`, `beta_source` (never
`angle_geometry`), channel-combine rule, covariance rule, and quality guards.
The adapter must either implement a covariance-aware Kalman update or clearly
use the single combined row with the declared scalar `R`; the retained
`run_fixed_beta_kalman` currently hardcodes `beta_source=angle_geometry` and
assumes scalar row variances, so passing RO data through it without a scratch
adapter would mislabel the result.

## Smoke acceptance checks (before any matrix run)

1. Input whitelist and shape check: raw eight channels, 200/200 fence, no
   truth/proxy/angular metadata.
2. Test-only perturbation: modifying frames 200--399 changes observations but
   leaves bins, phase offsets, weights, beta, and quality guards bit-identical.
3. Route audit: no `range_angle_process`, angle/MUSIC/ML, truth/q_proxy, or
   RA fallback; output row count is actual range-bin count.
4. Numerical quality: finite FFT/phase/R, monotonic timestamps, and explicit
   abstention on failed excitation or quality guards.

The current checkout passes only the input-isolation smoke.  The route,
beta, covariance, and matched-backend decisions above remain blockers.
