# Strict paired geometry-boundary protocol

Status: **blocked at protocol stage**. No new boundary results are claimed in
this directory.

## Why the existing runner is not strictly paired

`experiments/innovation1_geometry_neighborhood_2026-10-05/run_neighborhood.py`
assigns different seeds (`3000`–`3008`) to different geometry cells. Its
`generate()` function draws the motion phase `p` and the complex noise from
that seed for every cell. A span/gap change therefore changes both geometry
and random realization. The runner does record requested angles and detected
angles, but that does not remove the randomization confound.

The existing rows can remain a bounded neighborhood smoke. They must not be
described as a strict paired geometry holdout.

## Minimum strict paired grid

Use the nine cells:

```text
span ∈ {28°, 30°, 32°}
projection gap ∈ {0.02, 0.05, 0.08}
```

For each semantic block, use one common-random-number realization across all
nine cells. A paired block contains one fixed motion phase, one fixed complex
noise array, fixed amplitudes/phases, and the same frame split. Geometry is the
only changed input. The implementation may label this with one paired seed per
block; assigning nine independent seeds would cease to be strict pairing.

Applicable semantic blocks are balanced benign, unequal benign, opposed phase,
and the exact coincident-cancellation guard. The zero-projection symmetric
control belongs to the separate gap-0 control and is not silently substituted
for the `0.02` cell.

## Required generator contract

Before running, the new scratch adapter must expose either:

1. `generate(angles, amplitudes, phases, latent_phase, fixed_noise)`, where
   `latent_phase` and `fixed_noise` are created once per paired block; or
2. a deterministic common-random-number stream keyed by
   `(paired_seed, semantic, frame, sensor)` and independent of geometry.

The adapter must save hashes for the latent phase/noise realization and the
requested geometry. It must not pass structural truth, true angles, source
amplitudes, or post-run error into the selector.

## Frozen route and metrics

Keep the current order: one detected peak → merge; two peaks with detected span
`<30°` or `abs(cos(theta1)-cos(theta2)) < 0.05` → abstain; otherwise condition
number `<=20` → split-LS; amplitude/finite failure → abstain without fallback.

Record both requested and detected geometry for every row, then report:

- action and rejection reason;
- selected coverage and successful yield;
- accepted `RMSE > 0.01 mm` count;
- false-accept count: selected finite output above the predeclared error
  threshold;
- false-abstain count: selector abstains while a counterfactual route has a
  finite post-run error at or below the predeclared threshold;
- counterfactual merge and split diagnostics on the identical test aperture;
- paired differences within the same common-random-number block.

Truth enters only after route selection for these evaluation labels. Thresholds
cannot change after seeing holdout error.

## Stop conditions

Invalidate the paired block if random phase/noise hashes differ across cells,
if requested or detected geometry is missing, if route scoring windows differ,
if truth reaches selection, or if failed split silently falls back to merge.

