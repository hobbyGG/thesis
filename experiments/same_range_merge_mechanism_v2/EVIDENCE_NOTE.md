# Same-range split/merge mechanism v2

This is the corrected v2 mechanism study. The superseded v1 directory
`experiments/same_range_merge_mechanism/` is retained for provenance only and
must not be cited or used as evidence.

- Archive: `same_range_merge_v2.tgz`
- Archive size: 32,132 bytes
- Archive SHA-256: `202b6b2481dc07578b12742dda439f92c116819fedd94c25eb62b139d3915ed8`
- Scope: simplified one-range-cell, eight-element ULA IQ mechanism study; not
  full FMCW/radar or real-data validation
- Multiseed: 12 seeds (`200`–`211`) across six fixed scenes
- Unit checks: covariance/direct spectrum max error `2.8e-15`, opposite-source
  cancellation `1.6e-16`, noiseless single-source RMSE `7.6e-17 mm`

The corrected study reports split-vs-merge improvements for clearly separated
same-range cases, no split benefit in the symmetric control, and failure or
large error under destructive or coincident cancellation. These are bounded
mechanism observations under the declared fixed array, noise, phase, amplitude
and beamforming/least-squares settings. They do not establish universal angle
thresholds or real-radar performance, and do not cover range leakage,
multipath, drift, migration, association, Kalman fusion, or ADXL timing.
