# Innovation 1 paper evidence summary: same-range split/merge/abstain

Date: 2026-10-04  
Status: read-only summary of the tracked corrected-v2 record. No experiment,
large matrix, archive download, commit, or push was performed for this note.

## Evidence record

The record contains six fixed scenes × 12 seeds (`200`–`211`) = **72 trials**.
Each trial has 256 IQ frames from an eight-element centered half-wavelength ULA
and one common structural displacement. The first 128 frames are calibration;
the last 128 are evaluation. The estimator receives array IQ and fixed
instrument constants only. Truth is opened only for post-run waveform scoring.

Primary files:

- [`PROTOCOL.md`](../same_range_merge_mechanism_v2/PROTOCOL.md)
- [`run_experiment.py`](../same_range_merge_mechanism_v2/run_experiment.py)
- [`multiseed.json`](../same_range_merge_mechanism_v2/multiseed.json)
- [`FINDINGS.md`](../same_range_merge_mechanism_v2/FINDINGS.md)
- [`EVIDENCE_NOTE.md`](../same_range_merge_mechanism_v2/EVIDENCE_NOTE.md)

The source and protocol hashes recorded in `multiseed.json` are:

```text
run_experiment.py  4d524eab105dac4e2360f2c1aa0b49366a411475307228afd7e973e826bc66c9
PROTOCOL.md        e9089a42a90686954dd4b3619ff89a55d42c7c52f340672b8154e708b0ee3ac0
```

## Estimator and abstention rules

The calibration-only Bartlett spectrum uses the declared sign convention on a
`-60°…60°` grid at `0.25°` steps. Local peaks must be at least `12°` apart;
the peak rule uses `>=1%` prominence and a second-peak power of at least `18%`
of the strongest peak, with at most two retained peaks.

- **merge:** use the strongest detected angle, one conventional projection,
  and fixed `cos(theta_hat)` geometry.
- **split-LS:** require two detected angles, jointly reconstruct the two
  channels with the steering-matrix pseudoinverse, use fixed per-channel
  geometry, and fuse the channel waveforms with calibration amplitude-squared
  weights. Abstain when fewer than two peaks are available or steering
  condition number exceeds `20`.
- **amplitude guard:** every route abstains if any test-channel magnitude is
  below `5 × fixed_noise_sigma × extraction_noise_gain`.
- **reference and score:** each route unwraps its own test phase and subtracts
  its first test sample, then is scored against `q_test - q_test[0]`. There is
  no truth-based sign selection, offset fit, or route-specific refit.

The one-RX `range_only` route is an auxiliary control in the stored record. The
claims below concern the split-LS versus merge pairing.

## 12-seed / 72-trial results

RMSE values are millimetres. Coverage is the number of finite, guard-passing
outputs out of 12. `Delta` is the median of paired
`RMSE_split - RMSE_merge`; pairing is reported only when both routes are
covered.

| Scene (fixed angles, amplitudes, phases) | Merge coverage; median / p90 RMSE | Split-LS coverage; median / p90 RMSE | Paired n; Delta (mm) | Reading |
|---|---:|---:|---:|---|
| `close_benign` (25°, 29°; 1/.8; .15/−.30) | 12/12; 0.001418 / 0.002069 | 0/12; — / — | 0; — | Split abstained on all trials because fewer than two calibration peaks were found; merge remained covered. |
| `separated_benign` (−10°, 45°; 1/.8; .15/−.30) | 12/12; 0.023613 / 0.025717 | 12/12; 0.002146 / 0.003149 | 12; −0.021187 | Split beat merge in 12/12 paired trials. |
| `separated_unequal` (−10°, 45°; 1/.5; .15/−.30) | 12/12; 0.013852 / 0.015906 | 12/12; 0.002697 / 0.003862 | 12; −0.011148 | Split beat merge in 12/12 paired trials. |
| `close_destructive` (25°, 29°; 1/1; 0/π) | 12/12; 0.082103 / 0.099317 | 12/12; 0.026808 / 0.031558 | 12; −0.055567; split wins 11/12 | False Bartlett peaks near the destructive mixture made all routes inaccurate; lower split RMSE is a boundary observation, not a general benefit claim. |
| `coincident_cancel` (27°, 27°; 1/1; 0/π) | 0/12; — / — | 0/12; — / — | 0; — | Every route hit the test-amplitude guard. |
| `symmetric_control` (−25°, 25°; 1/.8; .15/−.30) | 12/12; 0.005307 / 0.006637 | 12/12; 0.006873 / 0.008365 | 12; **+0.001502**; split wins 0/12 | Split was worse in the same-cosine-projection control. |

The symmetric control is the required negative case: the split route does not
improve every two-peak scene, and the close benign case shows why abstention is
part of the proposed behavior. The destructive and coincident cases show that
finite coverage or two detected peaks does not guarantee correct geometry.

## Claims that can be written

The following wording stays within the stored evidence:

1. “In a bounded eight-element ULA, one-range-cell synthetic mechanism study,
   array-only split-LS reduced waveform RMSE relative to a strongest-peak merge
   in all 12 paired trials of each of two clearly separated scenes.”
2. “For the close benign pair, the declared two-peak rule abstained in all 12
   trials while merge remained covered in 12/12, motivating an explicit
   split/merge/abstain decision.”
3. “A symmetric same-cosine-projection control did not show a split gain:
   split-minus-merge median RMSE was `+0.001502 mm` and split won 0/12.”
4. “Destructive and coincident cancellation cases expose identifiability and
   amplitude-guard boundaries for the mechanism.”

These are descriptive synthetic mechanism statements. They should identify the
array size, one-range-cell model, fixed scene/noise settings, and 12-seed
scope when quoted in the thesis.

## Claims that must not be written

- A universal angular resolution, threshold, or guarantee that every same-range
  mixture can be split or represented by one equivalent target.
- “Split is always better,” including a claim based only on the destructive
  case; that case produced false peaks and large errors.
- Coverage as proof that the detected angles or split geometry are correct.
- Full FMCW, real-radar, field, hardware, multipath, range-leakage, migration,
  association, Kalman, ADXL, or cross-excitation validation.
- A `0.01 mm` accuracy guarantee or any field-level absolute-accuracy claim.
- Statistical generalization beyond the six fixed scenes and 12 seeds, or a
  claim that this is held-out/preregistered validation.
- A causal end-to-end gain for the complete thesis pipeline; this record
  intentionally excludes Kalman/ADXL fusion and isolates the frontend
  target-definition mechanism.

