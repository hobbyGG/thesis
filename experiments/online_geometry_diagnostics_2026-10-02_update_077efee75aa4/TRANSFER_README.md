# Online geometry diagnostic transfer snapshot

This is an updated compact preservation copy of the existing online-geometry
scratch research and the current manuscript plan, packaged on 2026-10-02.
Source files are unchanged. The archive is not a release, a complete
repository, or a validated experiment.

## Scientific interpretation required for every use

- Every result in this archive is a synthetic stationary diagnostic. It does
  not establish moving-structure, hardware, field, or general accuracy.
- The earlier gauge-mode routed reports remain retrospective selection or
  composition of saved full-horizon route scores. They are not validated
  streamed causal performance.
- `gauge_mode_routed_stream_trial.py` and its run directory are the later
  prefix/no-lookahead causality-correction artifact: raw and transport states
  are advanced causally, the route freezes after the declared prefix, and the
  prefix fallback is never retroactively replaced. Its numerical scores are
  still post-run truth-scoring summaries, so this correction does not establish
  validated streamed accuracy or erase the retrospective limitation of the
  earlier routed result. The latest routed result is therefore a retrospective
  correction to the earlier interpretation, not validated streamed performance.
- Mode thresholds were evaluated on the same development cases. They are not
  independent held-out validation or evidence of generalization.
- Steering ramps are signal-processing perturbations, not a physically
  consistent moving target, real physical target migration, or measured drift.
- `same_range_pair_stream_smoke.py` exercises same-range angular association
  and a stateful beta interface, with truth loaded only for post-run scoring.
  Its same-range score is not ADXL accuracy evidence, ADXL calibration evidence,
  radar–ADXL fusion accuracy evidence, or field displacement evidence.
- Accuracy and novelty are not established. Numerical improvements are
  conditional on these diagnostics and require independent validation.
- `manuscript_plan.md` is an unchanged planning snapshot. Its current wording
  already retracts retrospective causal claims and records the same-range and
  prefix boundaries. Preserve it for provenance and apply the limitations above
  when interpreting or reusing these artifacts. Other experiments mentioned by
  the manuscript are outside this backup scope.

## Contents and exclusions

Repository-relative names are preserved without an extra enclosing
`cloud_thesis` directory. The update includes the new true-prefix stream
script/results, same-range pair stream script/results, and current manuscript
snapshot, together with the earlier compact online-loop source and protocol or
result JSON files.

No raw ADC capture package, `.npy`/`.npz`, cache or `__pycache__`, binary,
credential, Git metadata, or helper tooling is included. The archive does not
include the imported `algorithm/` or `spatial_recovery_rebuilt/` packages,
environment dependencies, or generator data. Rerunning scripts needs a
compatible existing thesis checkout and its dependencies. No experiment was
rerun to make this backup.

## Local transfer contract

1. Retrieve the exact Library item identified in the accompanying handoff.
   Verify its byte size and whole-archive SHA-256 before extracting.
2. Inspect archive member names. Only regular files with relative paths are
   allowed; reject absolute paths, parent traversal, symbolic or hard links,
   device entries, and any path outside the listed scope.
3. Extract into a fresh staging directory, not directly over the local thesis.
   Verify every member against `TRANSFER_MANIFEST.json` and require the member
   set to match its files plus `TRANSFER_MANIFEST.json` exactly.
4. Resolve the intended local thesis repository and compare before copy. Copy
   absent files at the same repository-relative paths; skip identical ones.
   Preserve conflicting local files first and report differences for a merge
   decision rather than silently overwriting newer local research or deleting
   anything. Keep the transfer README and manifest with the backup even if not
   incorporated into the repository.
5. Recheck copied destination SHA-256 values against the manifest. Report
   copied, identical, and conflict counts and any unresolved paths.
6. This transfer must not commit or push to GitHub, modify remote access, or
   imply that Library preservation means the local transfer has completed.
