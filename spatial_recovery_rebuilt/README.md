# Rebuilt spatial validation scratch workspace

This directory is intentionally untracked. It is a small, external validation
harness reconstructed from the current `paper_bridge_simulation` package
builder. It does not modify the thesis source and it does not claim parity with
the lost scratch workspace or its results.

The protocol recorded here is:

- 400 radar frames at 100 Hz (4.0 s), split into frames 0--199 for calibration
  and 200--399 for a frozen test;
- one stationary stratum and low-motion displacement RMS strata of 0.005,
  0.010, 0.020, and 0.050 mm;
- exact realized `q_true` and `q_proxy` RMS values recorded from the generated
  arrays, rather than trusting requested labels;
- data-only guards computed from calibration radar/ADXL capture arrays and
  serialized before the test half is inspected;
- an explicit 40-seed plan, which is only a plan until a later run is approved.

The scratch definition of the two quantities is deliberately explicit:

* `q_true` is a deterministic 1 Hz sinusoidal guideway displacement. Its
  amplitude is scaled from the generated 3 kHz reference time array so the
  realized RMS is the requested stratum RMS (stationary is exactly zero).
* `q_proxy` is the radial proxy at the 15 degree reference target,
  `q_true*cos(15 degrees)`. It is logged for scale bookkeeping and is not fed
  to the estimator. This is a reconstruction assumption, not evidence of the
  lost workspace's definition.

Each listed stratum is applied across the complete four-second record in this
reconstruction; the first 200 frames are calibration data from the same
stratum, and the final 200 frames are the frozen test. Whether the lost
workspace instead used a stationary calibration half for each moving stratum is
unavailable.

The wrapper calls only private helpers already present in
`paper_bridge_simulation.package_builder` to write a standard capture package;
the retained algorithm still consumes only radar, ADXL355, and sync inputs.
Truth and scratch logs are post-run evaluation data.
The truth-derived RMS log is written separately as `truth/rms_log.json`; it is
not part of the frozen guard artifact and does not determine guard limits.

## Smoke test

From the repository root:

```bash
python3 spatial_recovery_rebuilt/rebuild_validation.py \
  --output spatial_recovery_rebuilt/smoke --smoke
```

The smoke run generates one 400-frame, 200+200 package for the 0.005 mm
stratum, freezes guards before checking the test half, verifies the package
contract, and runs `python3 -m algorithm.run` on that package. It does not run
the 40-seed matrix.

The full matrix is kept separate from the smoke output. Run one seed/stratum at
a time and retain the compact JSON/CSV logs; a full retained package is about
112 MB because the current chirp cube is `[400, 16, 8, 256]` complex64.

The completed effective-seed run uses
`run_40_seed_validation.py --output validation_7200_7239` and treats each
`(stratum, seed)` pair as one trial. Its compact results, rejection log, and
metric-reference audit are under `validation_7200_7239/`; the original smoke
directory is left untouched.

## Fair-branch smoke

`fair_branch_protocol.json` pre-registers a shared 400-frame/100 Hz ADC and
4000-sample/1 kHz ADXL budget, the 200 calibration + 200 frozen-test fence,
the primary all-trial success rule (`accepted` and frozen-test RMSE <= 0.010
mm), and separate coverage/abstention metrics. The RA branch runs the retained
frame route from a truth-free input copy. The current checkout has no
RO-all-channel estimator, so the RO branch is recorded as a fail-closed
abstention and is never relabeled as RA.

Run only the smoke scaffold with:

```bash
python3 spatial_recovery_rebuilt/run_fair_branch_smoke.py \
  --output spatial_recovery_rebuilt/fair_branch_smoke
```

The completed smoke artifacts are in `fair_branch_smoke/`; no full matrix mode
is provided by this runner.

The RO reuse audit is recorded in `ro_allchannel/BLOCKER.md` and
`ro_allchannel/blocker.json`. The deleted historical range-bin functions are
not all-channel implementations and depend on removed legacy contracts, so no
scratch adapter was created.

## Read-only RA frame-fence audit

`ra_fence_audit/run_ra_fence_audit.py` and `ra_fence_audit/ra_fence_audit.json`
are a truth-free, scratch-only probe. They copy the smoke package without
`truth/` or `paper_response_metadata.json`, keep ADC frames 0--199 byte
identical, and add a diagnostic tone only to frames 200--399. The normal RA
frontend changes its detected range, selected target, angle, and beta, so the
current target geometry is built from the full 400-frame ADC cube rather than
calibration frames alone. `target_freeze_probe.json` records a second
post-test-only perturbation with the same conclusion.

## Calibration-only geometry wrapper

`calibration_only/calibration_only_wrapper.py` is the scratch route for a
strict 200/200 geometry fence. It runs detection, local MUSIC/ML, selection,
and angle beta only on frames 0--199; frames 200--399 use direct range FFT and
fixed-angle projection before entering a fresh retained Kalman state. The
truth-free 2-seed × 5-stratum smoke is retained in
`calibration_only/smoke_truth_free_v3/`. Its full-window comparison is
descriptive because the current route filters all 400 frames.
