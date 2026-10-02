# 20-frame causal geometry/beta loop (scratch only)

This directory is an untracked prototype. It does not modify the tracked
`algorithm/` package, the existing `calibration_only` wrapper, or the
generator. It exercises only the retained frontend on a small causal rolling
window:

1. Create one current-contract 400-frame synthetic package with the existing
   scratch generator.
2. Copy only `radar/algorithm_input`, `adxl355/algorithm_input`, and `sync` to
   an estimator input directory. `truth/` and `paper_response_metadata.json`
   are deliberately excluded.
3. For each of 20 output frames, run `range_angle_process`, target detection,
   local MUSIC/ML refinement, and selection on the preceding 20 radar frames
   ending at the current frame. No frame after the current frame is read.
4. Treat the resulting range/angle/`beta = 1/abs(cos(angle))` as the online
   geometry update and retain the final slow-time column as the current phase
   observation. The smoke records geometry/beta continuity and availability;
   it does not run the fixed-beta Kalman or claim displacement accuracy.

Run from the repository root:

```bash
PYTHONPYCACHEPREFIX=/tmp/online-loop-pyc \
python3 experiments/online_geometry_loop_scratch/online_geometry_loop.py \
  --output /tmp/online-geometry-loop-smoke
```

The report is a protocol/safety smoke, not an experiment result. It asserts
that the estimator copy has no truth, q_proxy, or paper-response metadata and
that every rolling window ends at its reported frame.

`stateful_kalman_adapter.py` is the next scratch-only layer. It copies the
retained Kalman equations behind `step(phase_t, beta_t, ...)`, carrying `x`,
`P`, phase biases, and adaptive measurement variances across calls. The
one-seed no-drift check is:

```bash
PYTHONPYCACHEPREFIX=/tmp/online-loop-pyc \
python3 experiments/online_geometry_loop_scratch/stateful_kalman_smoke.py \
  --output experiments/online_geometry_loop_scratch/smoke_stateful_baseline
```

It compares the first 20 causal samples to the retained fixed-beta route on
the same truth-free slice. This only checks state continuity and metre units;
it is not an accuracy claim. The report currently shows exact equality for
phase, beta, and q̂ on the no-drift smoke. Target association is still a
caller responsibility when rolling geometry changes target count or order.

`association_smoke.py` covers that caller boundary with a finite diagnostic
tone on estimator-copy frames 200:209. Its 20-frame windows produce
5 → 1 → 5 targets. The frontend's raw order permutes, so the smoke reindexes
by `(range_bin, angle_bin)` and checks fixed slots. Run it with:

```bash
PYTHONPYCACHEPREFIX=/tmp/online-loop-pyc \
python3 experiments/online_geometry_loop_scratch/association_smoke.py \
  --output experiments/online_geometry_loop_scratch/smoke_association
```

The saved report has 15 raw-order permutations, zero ID mismatches, zero
missing-slot beta contamination, and full restoration of all five slots after
the one-target block. This is availability/association evidence only; the
tone is excluded from any guard or displacement score.

`accuracy_trial.py` runs one seed over frames 200:399 for a no-drift baseline
and an optional post-frame-200 virtual-array phase-ramp diagnostic. It scores
the existing frozen P1 route and the causal rolling/stateful adapter only
after both finish, loading truth from the separate generated package. The
saved baseline and drift JSONs include RMSE, finite coverage, abstain status,
AoA/beta drift, and explicit no-leakage fields. These are single synthetic
trials, not accuracy evidence.

`guard_ablation_trial.py` is a pre-registered negative guard ablation. It uses
fixed thresholds of 0.20 degrees per-window AoA jump or 0.5% beta relative
change between adjacent raw rolling windows, both computed from observable
rolling geometry only. A rejected update
falls back to the previous accepted beta/slot; an explicit abstain counter is
incremented only when no current phase slot is finite. The no-drift and
post-frame-200 phase-ramp reports are saved under `guard_ablation_baseline/`
and `guard_ablation_drift/`. In the drift trial the guard rejected six updates
and changed RMSE only from 0.136529 mm to 0.136528 mm at unchanged 100%
coverage (six fallbacks, zero abstains), so this remains a negative diagnostic
rather than a claimed fix.
