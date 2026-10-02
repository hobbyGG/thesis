# RO-all-channel reuse audit

Status: **blocked; no safe current implementation found**.

This is a read-only source audit. No tracked thesis source was modified and no
RO estimator or pair smoke was started. A design-only input isolation smoke
was run; it invokes no estimator and is recorded in
`input_isolation_smoke.json`. The detailed contract is in `DESIGN.md`.

The current estimator entry point only accepts `radar_mode=frame|chirp`
(`algorithm/run.py:14,106`). Both modes call `build_algorithm_inputs`, whose
common path performs `range_angle_process`, angle-map target detection, target
extraction, target selection, and ADXL preintegration
(`algorithm/io.py:98-126`). The current frontend exposes only the
range-angle path (`algorithm/frontend.py:46-98`); there is no range-only or
all-virtual-channel beta estimator or matched-backend entry point.

Historical code is present only in the deleted Phase 1 tree at the parent of
commit `d47e800`:

- `simulation/phase1/ma2026/rangebin.py:15-50` has
  `rangebin_input_from_range_fft`, but it selects the strongest single RX per
  range bin. It is not an all-channel route and emits no beta estimate.
- `simulation/phase1/scenario_inputs.py:396-430` has
  `range_bin_only_mixed_input`, but it also selects one RX and derives beta
  from an angle map. That violates the RO branch definition.
- `simulation/phase1/baselines.py:68-96` and `:140-151` contain
  `estimate_range_bin_itoh` and `estimate_range_bin_only_mixed_phase`, but they
  require deleted `RadarAlgorithmInput`/`Phase1Config` contracts and the
  removed legacy structural-Kalman stack.

Reusing those functions would therefore either mislabel a single-RX or
angle-derived route as RO-all-channel, or reintroduce the deleted baseline and
scenario registry. Neither is safe under the repository boundary rules.

The missing contract that must be specified before an adapter can be written
is:

1. how the eight virtual channels are combined for a range-only observation;
2. how range-only targets are selected and counted;
3. where beta comes from without angle geometry or truth/q_proxy;
4. the matched-backend phase/unwrap and measurement-variance equations;
5. the adapter output shape and route entry point for the current capture
   package (`adc_cube` `[frames, 8, 256]`, ADXL `[4000, 3]`, synchronized
   timestamps).

The strict reader must also whitelist metadata. The generated manifest embeds
target bins/angles and full-signal range FFT SNR under `source`; these are
oracle fields and cannot be used by RO. Eight channel rows are correlated
observations (shared target and PLL noise), not eight independent targets. A
phase-versus-`q_proxy` slope is a diagnostic truth oracle because `q_proxy` is
under `truth/`; an online alternative would require an explicitly specified
ADXL-derived displacement fit and excitation guard. The current Kalman
backend accepts a finite signed beta numerically but reports a hardcoded
`angle_geometry` beta source and estimates its initial bias/R from the first
20 observations, so it is not a complete frozen calibration backend.

Until those are supplied by a real implementation, the fair-branch runner must
keep RO fail-closed as `blocked_missing_route`; it must not invent a physical
model or run a pair smoke under an RA label.

The follow-up interface design is recorded in `DESIGN.md` and
`ro_design.json`. `input_isolation_strict.json` is an input-only smoke: it
whitelists raw 8-channel ADC/timing fields, removes truth/proxy and angular
metadata, and deliberately invokes no RO estimator, beta fit, Kalman, or score.
