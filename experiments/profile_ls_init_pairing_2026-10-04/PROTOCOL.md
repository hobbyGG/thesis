# Profile-LS initialization pairing: blocked protocol

This is the executable design for the requested Bartlett/profile-LS × cold/warm
pairing. The original `experiments/same_range_geometry_reference_diagnostic/heldout_20261003/`
directory, seed-400/401/402 runner, frozen protocol, and compact outputs are not
present in the current checkout. The earlier Library archive was not confirmed
materialized locally, so no substitute pilot is used.

When the archive is restored, the runner must first verify the exact source and
manifest hashes, the calibration/test split, the physical reference, and the
seed list. It should run one seed before the three-seed set.

The four paired routes use identical IQ, calibration-only frozen geometry,
downstream settings, and scoring reference:

1. Bartlett-cold
2. profile-LS-cold
3. Bartlett-warm
4. profile-LS-warm

Cold starts state at the common scoring origin. Warm may use only legal history
before scoring. If that history is the first 20 test frames, all four routes
must score from frame 220 and the warmup latency must be reported separately.
State coordinates must be aligned from the model definition; do not subtract a
fitted offset or use truth to align routes.

For each seed, record paired MSE differences
`D_cold = MSE(Bartlett-cold) - MSE(profile-LS-cold)` and
`D_warm = MSE(Bartlett-warm) - MSE(profile-LS-warm)`, plus interaction
`D_warm - D_cold`, RMSE, finite coverage and abstention. Truth and `q_proxy`
are post-run scoring inputs only.

The existing 400–402 item, if recovered, remains a mechanism diagnostic rather
than new held-out evidence. Do not infer a geometry benefit by subtracting the
separate 0.05 mm pilot's 11.99% initialization difference.
