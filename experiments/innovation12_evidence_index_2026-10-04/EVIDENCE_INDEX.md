# Innovation 1–2 local evidence index

Date: 2026-10-04  
Purpose: read-only inventory for the first two thesis innovations. No new
experiment was run while preparing this index.

## Local status

| Item | Checkout status | Evidence level | Action |
|---|---|---|---|
| Same-range split/merge/abstain, corrected v2 | Present at `experiments/same_range_merge_mechanism_v2/`; its six core files are Git-tracked | Bounded synthetic mechanism check | Use the existing protocol and compact JSON as the current local evidence. The older `experiments/same_range_merge_mechanism/` directory is superseded provenance and is not evidence. |
| Calibration-only off-grid/profile-LS geometry, 400–402 | Missing. `experiments/same_range_geometry_reference_diagnostic/heldout_20261003/` does not exist, and no matching runner or compact 400–402 output was found by the local filename/text scan | No fresh profile-LS or held-out evidence in this checkout | Keep the pairing protocol fail-closed. Restore the exact v22 archive contents before any reproduction. |

## Innovation 1: minimum reproducible and citable record

The corrected v2 record is self-contained enough to reproduce the declared
mechanism study from source and protocol:

- Protocol: [`PROTOCOL.md`](../same_range_merge_mechanism_v2/PROTOCOL.md)
- Runner: [`run_experiment.py`](../same_range_merge_mechanism_v2/run_experiment.py)
- Deterministic smoke output: [`smoke.json`](../same_range_merge_mechanism_v2/smoke.json)
- 12-seed compact output: [`multiseed.json`](../same_range_merge_mechanism_v2/multiseed.json)
- Findings and evidence boundary: [`FINDINGS.md`](../same_range_merge_mechanism_v2/FINDINGS.md), [`EVIDENCE_NOTE.md`](../same_range_merge_mechanism_v2/EVIDENCE_NOTE.md)

The compact output records seeds 200–211, six fixed scenes, unit checks, and
the source/protocol hashes. The declared hashes are:

```text
run_experiment.py  4d524eab105dac4e2360f2c1aa0b49366a411475307228afd7e973e826bc66c9
PROTOCOL.md        e9089a42a90686954dd4b3619ff89a55d42c7c52f340672b8154e708b0ee3ac0
```

The smallest rerun is the one-seed smoke command below. The second command is
the already recorded 12-seed reproduction; neither command was executed in
this audit.

```bash
python3 experiments/same_range_merge_mechanism_v2/run_experiment.py \
  --seeds 100 --out /tmp/same_range_v2_smoke_repro.json

python3 experiments/same_range_merge_mechanism_v2/run_experiment.py \
  --seeds 200 201 202 203 204 205 206 207 208 209 210 211 \
  --out /tmp/same_range_v2_multiseed_repro.json
```

The unit checks in the recorded output are positive-angle recovery at 25°,
covariance/direct-spectrum maximum error `2.8e-15`, identical-opposite-source
cancellation `1.6e-16`, and noiseless single-source waveform RMSE
`7.6e-17 mm`.

The 12-seed summary supports the following narrow statements:

- In the two clearly separated benign scenes, split-LS covered 12/12 trials,
  beat merge in 12/12 paired trials, and reduced median RMSE by `0.02119 mm`
  (`-10°,45°`, amplitudes `1/.8`) and `0.01115 mm`
  (`-10°,45°`, amplitudes `1/.5`).
- In the close benign scene, the split route abstained in 12/12 trials while
  merge covered 12/12 with median RMSE `0.00142 mm`; this is the local
  mechanism evidence for a split/merge/abstain policy.
- The symmetric control had split worse than merge by `0.00150 mm` median,
  and the coincident cancellation scene failed the amplitude guard for every
  route. The close destructive scene produced large errors even though the
  split route was lower than merge.

These results are a bounded mechanism observation for the fixed eight-element
ULA, one range cell, fixed noise, phases, amplitudes, and Bartlett/LS rules.
They do not establish a universal angular threshold, real FMCW or field
performance, a `0.01 mm` guarantee, or behavior under range leakage,
multipath, drift, migration, association, Kalman fusion, or ADXL timing.

The v2 note names an archive `same_range_merge_v2.tgz` with size 32,132 bytes
and SHA-256
`202b6b2481dc07578b12742dda439f92c116819fedd94c25eb62b139d3915ed8`, but that
tar file itself is not present in the checkout. The tracked source, protocol,
and compact outputs are the available evidence; the archive hash is retained
as provenance only.

## Innovation 2: profile-LS status and minimum v22 restore set

The existing fail-closed design is [`PROTOCOL.md`](../profile_ls_init_pairing_2026-10-04/PROTOCOL.md), with the preflight entrypoint
[`run_when_archive_present.py`](../profile_ls_init_pairing_2026-10-04/run_when_archive_present.py).
Its expected source directory is absent:

```text
experiments/same_range_geometry_reference_diagnostic/heldout_20261003/
```

The local synthetic angle/beta pilots and literature notes explicitly state
that they do not reproduce this profile-LS artifact. They must not be used as
held-out profile-LS evidence.

Restore the following minimum set from the v22 archive before attempting even
one seed:

1. `protocol.json` — frozen protocol, seed list, frame split, estimator inputs,
   and scoring reference.
2. `manifest.json` — source/artifact hashes, package identity, and the exact
   400/401/402 provenance.
3. The original runner/source script(s) used to generate and execute the
   400–402 diagnostic.
4. The capture package or compact IQ input for each of seeds 400, 401, and
   402, including the calibration/test frame boundaries.
5. The physical reference definition and frame indexing used for scoring.
6. The Bartlett and profile-LS route configuration: angle grid or bounds,
   complex profile objective, nuisance parameters, weighting/regularization,
   geometry parameterization, and frozen calibration-only fields.
7. Any compact prior result JSON/Markdown and per-seed output manifest needed
   to check that the restored numbers correspond to the original claim. These
   are provenance checks, not replacements for the source inputs.

The archive-level restore record previously identified locally is v22,
3,723,687 bytes, expected SHA-256
`f692ad87a6258b680ad8d5873ac7d653c45bf64e42adb9df557118c55d545c1b`.
This audit did not retry or validate a cloud transfer. Until the directory and
hashes above are present, the safe paper statement is: **fresh profile-LS /
geometry 400–402 artifact not found in the current checkout**.

After restore, use the existing four-route pairing design (Bartlett/profile-LS
× cold/warm), first on one seed, with identical IQ, calibration-only frozen
geometry, downstream settings, reference, and scoring origin. Do not call it a
new held-out validation or infer a geometry gain from the separate causal
initialization pilot.

