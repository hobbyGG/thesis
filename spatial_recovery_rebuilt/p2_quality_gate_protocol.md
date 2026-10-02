# P2 observable quality gate (scratch only)

Status: development protocol and 10-trial smoke, no thesis-source changes.
This gate wraps the current fixed-geometry RA route. It is a record-level
abstention gate; it does not alter the estimator or claim parity with the lost
workspace.

Fence caveat: the retained RA frontend still detects/refines target geometry
from the full ADC window. The gate itself is calibration-only, but a strict
deployment P2 claim remains blocked until geometry/selection are frozen before
frame 200 (the existing `ra_fence_audit` documents this route limitation).

## Data fence and estimator isolation

- Build one current-contract package for each stratum/seed (400 radar frames at
  100 Hz, 8 virtual channels, 4000 ADXL samples).
- Freeze the gate decision from calibration frames 0--199 only. Frozen test
  frames 200--399 are never used to choose limits or accept a record.
- Before invoking `algorithm.run`, remove `truth/` and
  `paper_response_metadata.json`, and remove the manifest `source` block. The
  estimator receives only radar ADC, ADXL and synchronization inputs.
- Truth is copied to a separate post-run evaluator solely to label false
  accepts. `q_proxy` is never read by the estimator or gate.

## Observable predicates

1. Signed beta: `beta_signed = 1/cos(theta)` under the declared positive
   mounting convention (`cos(theta)>0`). Require finite values, `|cos(theta)| >=
   0.50`, and agreement with the reported `beta_hat` within 0.2% plus 0.002.
   Any unresolved sign or geometry ambiguity abstains; `abs(cos(theta))` is not
   used to repair a sign.
2. Excitation proxy: median target-wise standard deviation of the beta-signed,
   calibration-corrected structural phase. Require `>= 0.012 rad`. This is a
   pre-registered observable floor, not a truth/RMS label.
3. Corrected residual: with per-target calibration bias removed, form the
   leave-all-target median structural phase and compute the inverse-`R_theta`
   weighted RMS residual. Require `<= 0.020 rad`.
4. Primary fit quality: for each target, fit its structural phase to the
   leave-one-target-out median common phase (`intercept + slope`) and use the
   median target `R²` as the one primary fit metric. Require `median R² >= 0.80`.
5. IQ/SNR: from the calibration ADC range FFT, use the median target-bin
   magnitude divided by a robust off-target noise floor. Require median `SNR >=
   20 dB`.
6. Cross-channel consistency: at each selected range bin, unwrap each of the
   eight channel phases over calibration, remove channel means, compute all
   pairwise absolute correlations, and take the median across targets. Require
   `median |corr| >= 0.80`.

All six predicates must pass. A rejected record is an abstention and counts as
a failure in the primary all-trial metric.

## Smoke scoring

Run 2 seeds for stationary, 0.005, 0.010, 0.020 and 0.050 mm requested RMS.
After the gate decision is frozen, compute post-run frozen-test RMSE against the
separate truth copy only for reporting. A false accept is a gate acceptance with
test RMSE `> 0.010 mm`; report coverage, false accepts, abstention-as-failure
success, and accepted-only RMSE separately. Accepted-only RMSE is descriptive
and must not replace the all-trial metric.

The script is `p2_quality_gate.py`; outputs are
`p2_gate_smoke/p2_quality_gate_protocol.json` and
`p2_gate_smoke/p2_quality_gate_report.json`.
