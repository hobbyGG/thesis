# Calibration-only geometry scratch wrapper

This directory is untracked scratch validation code. It does not modify the
tracked `algorithm/` package or claim parity with the lost workspace.

`calibration_only_wrapper.py` implements the requested 200/200 fence:

1. Frames `0:200` are passed to the retained range FFT/angle map, target
   detection, local MUSIC/ML refinement, and `select_targets`.
2. The resulting range bins, refined angles, selected indices, and
   angle-derived beta are copied into a frozen geometry record.
3. Frames `200:400` are range-FFT processed only and projected with a fixed
   steering matrix built from the calibration geometry. The test half does not
   run target detection, angle-map peak finding, or local MUSIC/ML.
4. Only those 200 complex observations and ADXL samples at or after the test
   start are passed to the retained `run_fixed_beta_kalman` implementation.

The wrapper keeps the existing guard contract: limits are computed from
calibration ADC/ADXL arrays, the full test half is checked against those limits,
and a failed check prevents estimation. RMSE is computed outside the estimator
on the frozen test using the existing physical 0.20 s truth reference. The
full-window route is run on the same truth-free input copy only as a comparison;
its RMSE is not mixed into the calibration-only result.

Run the 10-trial smoke (two seeds for each of five strata) with:

```bash
PYTHONPYCACHEPREFIX=/tmp/calonly-pyc \
python3 spatial_recovery_rebuilt/calibration_only/calibration_only_wrapper.py \
  --output spatial_recovery_rebuilt/calibration_only/smoke_truth_free_v3
```

The completed, truth-free smoke artifacts are under `smoke_truth_free_v3/`.
(`smoke/` and `smoke_truth_free/` are earlier retained audit artifacts.) In
particular, `smoke_truth_free_v3/test_only_perturbation_probe.json` keeps calibration frames exactly unchanged,
perturbs only frames 200--399, and verifies that frozen geometry fields remain
identical while test observations change. This deliberately large perturbation
is a geometry-fence diagnostic and is not submitted to the guard or RMSE
score. The run manifest records source
hashes, git status, realized `q_true`/`q_proxy` RMS values, the 21-frame
reference definition, and the fact that no full matrix was started. The
full-window comparison is descriptive: it filters all 400 frames, while the
calibration-only route starts a fresh retained Kalman state on test frames
200--399.

This is a wrapper-level experiment. The tracked command
`python3 -m algorithm.run` remains the existing full-window route and was not
changed. `calibration_only_wrapper.py` and `smoke_truth_free_v3/` are the
authoritative direct-FFT implementation and smoke output; other scratch helper
files and earlier smoke directories are retained as audit history only.
