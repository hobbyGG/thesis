# RO-all-channel design audit

Status: **design blocked; no RO estimator or pair smoke was implemented**.

This document is a scratch-only contract review. It does not modify
`algorithm/`, does not reuse the current RA route under an RO label, and does
not claim a fair comparison.

## Observed input contract

The current package exposes:

- `radar/algorithm_input/adc_cube.npy`: complex64 `[400, 8, 256]`, one
  frame-level average per frame, virtual channel, and ADC sample.
- `radar/algorithm_input/chirp_cube.npy`: complex64 `[400, 16, 8, 256]`, with
  16 loops per frame and 8 virtual channels. The observed package is not a
  10-loop package.
- `adxl355/algorithm_input/acceleration_mps2.npy`: float64 `[4000, 3]` at
  1 kHz.
- synchronized radar timestamps with 400 samples.

`algorithm/io.py:22-75` loads these fields into `CapturePackage`; the optional
`truth/` directory is also loaded when present. `algorithm/types.py:33-41`
requires a `RadarInput` with `measured_beta`, wrapped phase, availability,
selected indices, initial measurement variance, and a free-form `extra` map.

## Minimal range-only all-channel route

If an implementation is supplied, its contract should be the following.

1. On calibration frames `adc_cube[0:200]`, compute a range FFT over the 256
   ADC samples for all eight channels. Build a range-only energy statistic such
   as a robust median over frames of the channel-summed power. Detect local
   range-bin peaks and retain at most `K` **range bins**. No angle FFT, angle
   axis, MUSIC, ML refinement, or angle metadata may be read.
2. For each retained range bin, derive one all-channel complex observation from
   all eight channels using weights frozen from calibration. A defensible
   implementation would document a channel-combination rule (for example, a
   calibration covariance principal vector or a declared equal-weight
   projection), its phase convention, and the mixture/degeneracy policy. It
   must not silently choose the strongest single RX.
3. Freeze the range-bin list, channel weights, selection, and beta before frame
   200. On frames `200:400`, compute only the range FFT and apply the frozen
   projection. No range-peak re-detection, channel-weight refit, phase-based
   target addition, or beta refit may occur.
4. Emit a `RadarInput` whose row count is `range_bin_count`, not an asserted
   number of physical targets. `extra` must state
   `geometry_source=calibration_frames_only`, `route=ro_all_channel`, the
   calibration/test frame ranges, the weight rule, and the beta source.

The retained Kalman can consume the resulting array shapes numerically:
`algorithm/kalman.py:77-112` copies `RadarInput.measured_beta`, uses the
wrapped observations, and applies the acceleration preintegration. However,
`algorithm/kalman.py:146-150` unconditionally writes
`extra["beta_source"] = "angle_geometry"`. Passing an RO beta through this API
would therefore produce a mislabeled result unless a scratch wrapper replaces
that metadata and records the replacement. The current API has no explicit
route or beta-source enum.

## Beta identifiability

For a point scatterer the simulated phase follows the radial projection
`q*cos(theta)` (`paper_bridge_simulation/package_builder.py:141-143`). The
structural Kalman beta is the conversion from LOS phase to structural phase,
approximately `1/|cos(theta)|`. A range-only signal does not identify
`theta`; channel phase differences would identify an angle and therefore
violate the RO definition.

Fitting phase against `q_proxy` is an oracle diagnostic, not an observable
replacement. The scratch generator defines `q_proxy = q_true*cos(15 deg)`
(`rebuild_validation.py:100-113`) and writes it only under `truth/`
(`rebuild_validation.py:172-187`). A fit against that proxy estimates the
proxy/LOS slope. Converting it to structural beta requires the external 15°
factor and the simulated truth definition, so it cannot be used online.

The only candidate that avoids `truth/q_proxy` is an ADXL-regressed phase
slope. Use calibration-only ADXL acceleration, form a double-integral relative
displacement `u(t)`, unwrap each projected phase series, and fit

```text
phi(t) = c0 + c1*t + c2*t^2 + gamma*u(t)
```

where the polynomial absorbs initial position, initial velocity, and a constant
acceleration bias. With an independently calibrated ADXL scale,
`gamma` can be converted to a signed LOS projection factor and then to beta
only under a declared sign convention. This is a possible future diagnostic,
but it is not a safe current baseline:

- stationary has no excitation, so `gamma` and beta are unidentifiable;
- the requested low-motion strata are below the simulated ADXL noise level;
- 0.005/0.010/0.020/0.050 mm RMS at 1 Hz imply acceleration RMS of about
  0.000197/0.000395/0.000790/0.001974 m/s², versus approximately 0.004934
  m/s² ADXL noise (about −28/−22/−16/−8 dB);
- phase unwrapping, range-bin leakage, multipath, and channel mixing can make
  the fitted slope target-dependent or unstable;
- the current preintegration API (`algorithm/acceleration.py:14-40`) returns
  interval `delta_q`/`delta_v`, not a globally anchored displacement, so the
  nuisance-polynomial and excitation checks are part of the missing contract.

A fixed `beta=1` could be declared as a range-only LOS displacement output,
but it is not a structural displacement estimate and must be scored in an LOS
metric rather than compared to the structural-q Kalman output.

## Why channel count is not target count

The simulator places five primary target contributions, two weak static
scatterers, and one multipath contribution per moving target. Each contribution
is projected into all eight virtual channels (`package_builder.py:141-189`).
Receiver noise is channel-independent, while the PLL term is common to the four
RX channels of each physical TX (`package_builder.py:191-208`). Thus the eight
channels are correlated views of a mixture; they are not eight independent
targets. An RO implementation must report range-bin count and document whether
multiple scatterers in one range bin are intentionally mixed.

## Required blocker before implementation

The following must be supplied and validated before a route can be written or
called fair:

1. all-channel combination weights and phase convention;
2. range-bin candidate threshold, merging, and count semantics;
3. an observable beta definition, with identifiability and abstention rules;
4. phase unwrapping and measurement-variance equations for the matched backend;
5. a route-specific result method and `beta_source` metadata that does not
   claim `angle_geometry`;
6. a test-only perturbation check proving calibration range bins, weights, and
   beta are unchanged.

Until then, the existing RO status remains `blocked_missing_safe_reusable_implementation`.
