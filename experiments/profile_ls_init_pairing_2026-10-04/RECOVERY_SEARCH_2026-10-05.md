# Local recovery search: profile-LS heldout 400–402

**Date:** 2026-10-05  
**Mode:** bounded read-only search; no archive extraction, experiment run, permission change, or push.

## Search scope and result

The expected original source path remains absent:

`experiments/same_range_geometry_reference_diagnostic/heldout_20261003/`

The following local sources were searched by path and, where appropriate, by
bounded text/content markers:

- repository `archive/`, `experiments/`, `output/`, `outputs/`, `tmp/`, plus
  current `simulation/outputs/` and `reports/` artifacts;
- all local branches and remotes listed by Git (`main`, the phase1 validation
  branch, `origin/main`, `origin/archive/mmwavecapture-main`, and
  `origin/codex/phase1-simulation-validation`), using recursive tree-path
  search;
- reachable Git history and unreachable Git blobs/trees, using markers
  `heldout_20261003`, `same_range_geometry_reference`, `profile-LS`,
  `seed-400/401/402`, `development300`, and `v22`;
- `/Users/umep/Downloads` to depth 3 for archive names containing
  `thesis`, `profile`, `geometry`, `archive`, `heldout`, `400`, `401`, `402`,
  or `v22`, plus the exact clue size 3,723,687 bytes;
- `/tmp` and the task temporary directory for the same bounded filename
  markers.

No file matched the expected v22 size (3,723,687 bytes), and no file with the
expected SHA-256 was found:

`f692ad87a6258b680ad8d5873ac7d653c45bf64e42adb9df557118c55d545c1b`

The Downloads search found unrelated installer/export archives only; their
contents were not inspected because their names did not match the requested
thesis/profile/geometry/archive scope. The temporary-directory match was an
unrelated `WeTypeLogs.zip`, also not inspected.

The Git object search recovered only already-known cross-review notes and local
pilot/protocol objects. It did not recover a heldout directory, runner, IQ
package, manifest, or result. No archive was therefore extracted, and there is
no independent recovery directory or recovered-file hash to report.

## What exists locally

The current checkout contains an intentionally blocked design:

- `PROTOCOL.md`, `PROTOCOL.json`, and `run_when_archive_present.py` in this
  directory;
- local MUSIC/LS implementation in `algorithm/angle_estimation.py`;
- generic current package/generator code under `paper_bridge_simulation/`,
  `algorithm/`, and `spatial_recovery_rebuilt/`;
- local synthetic angle/beta and same-range mechanism pilots.

These are source or exploratory artifacts, not the original v22 profile-LS
400–402 evidence. The local pilots explicitly identify themselves as not
reproducing the cloud/heldout profile-LS artifact.

## Missing restore set and rerun status

The following items are still required before even one paired seed can be
rerun:

1. v22 `protocol.json` and `manifest.json`, including source/artifact hashes;
2. the original 400–402 runner/source script(s);
3. capture package or compact IQ for seeds 400, 401, and 402;
4. calibration/test frame boundaries and physical reference/scoring indices;
5. Bartlett/profile-LS route configuration, including profile objective,
   angle bounds/grid, nuisance parameters, weighting/regularization, geometry
   parameterization, and frozen calibration-only fields;
6. compact prior outputs and per-seed output manifest for provenance checks.

**Rerun status:** cannot rerun from the current local material. The existing
`run_when_archive_present.py` correctly stops before execution when the source
directory or required manifest is missing. Generic package-generation code can
support a future reconstruction, but it cannot establish that reconstruction is
the historical 400–402 experiment.

The minimum safe statement remains: **the original profile-LS geometry 400–402
artifact was not found in the bounded local search.**

