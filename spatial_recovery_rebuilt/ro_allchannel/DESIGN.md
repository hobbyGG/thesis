# RO-all-channel minimum contract (design-only)

Status: **blocked design; no estimator implementation or fairness claim**.

This note records the smallest interface that would be needed for a real
range-only all-channel route.  It is not an implementation.  The input
isolation smoke only proves that the current package contains the required
arrays and that the proposed calibration/test fence can be observed without
exposing truth.

## Available package and current API

The capture exporter publishes `adc_cube` with axes
`(frame, virtual_antenna, adc_sample)` and optional `chirp_cube` with axes
`(frame, chirp_loop, virtual_antenna, adc_sample)`
(`capture_program/src/mmwavecapture/algorithm_input.py:603-612,
643-665`).  The current scratch package has shape `(400, 8, 256)` and the
manifest declares eight virtual channels (`radar.virtual_antennas` and
`virtual_array_positions_wavelengths`).  `algorithm.io.load_capture_package`
loads these arrays and ADXL/timestamps (`algorithm/io.py:22-75`).  The
synthetic manifest also carries oracle target bins/angles and full-signal
`range_fft_snr_db` under `source`; a strict RO reader must whitelist only
dimensions/timing needed for the FFT and must remove `source`, array
positions, `angle_bins`, and scene geometry.  It must not treat the retained
loader's `radar_metadata` or `FrontendConfig` as the RO interface.

The retained `build_algorithm_inputs` has no range-only branch:
`algorithm/io.py:98-126` always calls `range_angle_process`, angle-map
detection, target extraction/selection, and ADXL preintegration.  The frontend
does a range FFT on every supplied frame and then angle DBF
(`algorithm/frontend.py:46-56`); `extract_targets` calls local MUSIC/ML and
computes `beta=1/|cos(angle)|` (`algorithm/frontend.py:59-98`).  Therefore an
RO adapter must be a separate scratch route and must not call that function or
reuse its `RadarInput` geometry fields.

## Proposed RO data contract

For each shared package:

1. **Calibration input.** Read only `adc_cube[0:200, :, :]`, verify its hash,
   and compute `X[f,v,r] = FFT(adc_cube[f,v,:])`.  A deterministic range-only
   selector must operate on an explicitly declared all-channel statistic (for
   example a robust median of `|X|^2` over `f` and `v`), use fixed peak
   separation and a pre-registered `K`, and record the actual selected range
   bins.  It must not construct an angle axis, steering matrix, AoA, MUSIC, or
   ML estimate.
2. **Eight-channel observations.** For each selected range bin, preserve the
   eight complex channel series, or define an explicit channel-combination
   vector with its sign/normalization.  The contract must state whether one
   Kalman observation is emitted per channel, per range bin after a declared
   combine, or both.  Copying RA's selected indices or target count is
   forbidden.  Eight rows are eight observations of one range return, not
   eight targets.  Target scattering noise is shared within each TX's RX
   group (`package_builder.py:146-159`) and PLL phase noise is shared by
   channels 0--3 and 4--7 (`:194-206`).  The current Kalman precision sum
   assumes scalar row variances (`kalman.py:112-118`), so correlation must be
   disclosed or a calibrated channel combine/covariance specified.
3. **Frozen test input.** Read only `adc_cube[200:400, :, :]`, apply the same
   range FFT and the frozen calibration bins/channel combination, and emit
   test complex phase samples.  No test-side range selection, candidate
   count, target selection, angle estimate, or beta update is allowed.
4. **Kalman adapter.** The current `run_fixed_beta_kalman` accepts a
   `RadarInput` and `AccelerationInput`, then uses `measured_beta` as a fixed
   vector (`algorithm/kalman.py:77-112`).  A real adapter would need to define
   a test-only `RadarInput` with the RO observation rows, selected rows, beta,
   finite mask, initial measurement variance, timestamps, and a matching
   test-only ADXL preintegration.  Its metadata must identify
   `geometry_source=calibration_frames_0_199` and `observation_source=frames_200_399`.
   Signed beta is numerically accepted by `kalman.py:81,109-111`, but the
   backend metadata hardcodes `beta_source="angle_geometry"` at `:148`.
   A scratch wrapper must declare RO provenance separately.  The backend also
   estimates phase bias and initial R from its first 20 observations
   (`kalman.py:23-74,82`) and adapts R from test residuals (`:123-133`), so
   frozen geometry/beta does not mean frozen bias/R; freezing those requires a
   separate adapter contract.

## Beta fit: oracle versus observable

The requested signed phase-vs-`q_proxy` fit is diagnostically definable as a
calibration regression, e.g. unwrap each channel phase, remove a fitted
intercept, and fit its signed slope against `q_proxy`.  If
`c_proxy=s*lambda/(4*pi)` for `s=d(phi)/dq_proxy`, then
`beta_proxy=1/c_proxy=cos(15 deg)/cos(theta)` maps phase to proxy displacement;
the structural beta would be `beta_proxy/cos(15 deg)`.  That conversion
depends on the truth-defined proxy convention.  The signed slope is therefore
not automatically the backend beta.  It cannot be an
estimator input here.  `q_proxy_m.npy` is under `truth/`, and the generated
metadata explicitly marks truth as post-run-only; `algorithm/AGENTS.md` also
forbids truth from detection, beta, or filtering.  A fit that reads that file
would be a truth oracle, even if it uses only frames 0--199.

The only currently available online candidate is an ADXL-derived displacement
reference: use calibration-only native acceleration and
`preintegrate_acceleration_to_radar` (`algorithm/acceleration.py:7-39`) to
obtain a signed `q_accel` sequence, then fit phase slope with a declared
finite/excitation guard.  This is an explicit design alternative, not a
validated estimator: bias, group delay, double integration drift, and weak
motion can make the fit unidentifiable.  The route must abstain or use a
pre-registered fixed beta when calibration excitation is insufficient.  The
current API has no beta-fit function, no excitation threshold, and no route
entry point, so this choice cannot be silently inferred.

## Blocking decisions

The RO route remains unavailable until the following are supplied and tested
on the same shared package:

- all-channel range statistic, peak separation, and `K`/target-count rule;
- channel-preserving or combined observation shape and sign convention;
- beta source (online ADXL reference or declared fixed value), regression
  window, intercept/unwrap rule, excitation guard, and fallback/abstention;
- matched phase, variance, and cold-start equations for the Kalman adapter;
- a concrete scratch entry point whose input manifest excludes `truth/`,
  `q_proxy`, and paper response metadata.

Until then, RO attempts must be recorded as `blocked_missing_route`; the RA
route must not be relabeled or used as a fallback.
