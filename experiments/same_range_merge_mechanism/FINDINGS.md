# Same-range split versus merge: bounded mechanism findings

Run command:

```bash
python same_range_merge_split.py --seeds 0 --out deterministic_results.json
python same_range_merge_split.py --seeds $(seq 0 11) --out multiseed_results.json
```

The model is deliberately small: same-range complex array IQ from an 8-element half-wavelength ULA, with one common structural displacement waveform and target-dependent `cos(theta)` phase projection. It has no range FFT, multipath, calibration errors, tracker, or real capture. Simulation truth is used only to generate/evaluate `q`; the estimator receives array IQ and declared instrument constants.

Metrics use the same positive phase sign and first-sample displacement reference for both routes. Coverage counts finite estimates that pass the declared minimum-magnitude guard; failed/abstained trials remain in the denominator.

## 12-seed results

| case | split coverage | split median RMSE (mm) | split p90 (mm) | merge coverage | merge median RMSE (mm) | merge p90 (mm) |
|---|---:|---:|---:|---:|---:|---:|
| close_same_phase | 0/12 | — | — | 12/12 | 0.00141 | 0.00267 |
| separated_balanced | 12/12 | 0.00300 | 0.00547 | 12/12 | 0.00393 | 0.00774 |
| separated_unequal | 12/12 | 0.00161 | 0.00234 | 12/12 | 0.00365 | 0.00623 |
| close_destructive | 12/12* | 0.00345 | 0.00462 | 12/12* | 0.00439 | 0.00655 |
| coincident_destructive | 0/12 | — | — | 0/12 | — | — |

`*` The close destructive case is a deliberate negative: the opposite static phases create a spatial cancellation pattern that the array-only Bartlett detector reports as false peaks near ±9.75° (the true angles are ±4°). Coverage therefore does not mean the geometry was correctly resolved; both waveform errors are materially worse than the benign close mixture.

## What this supports

- For these declared separated-angle cases, splitting into two detected range-angle phasors reduced covered displacement RMSE versus a single strongest-angle phasor (about 24% lower median error for balanced and 56% lower for unequal amplitudes).
- For the benign close-angle case, the array-only detector returned one peak and the merge route had full coverage; forcing split had 0/12 coverage. This is consistent with treating genuinely unresolved close directions as one channel when the phasors are not cancelling.
- Coverage/failure reporting matters: the exact coincident opposite-phasor case failed the magnitude guard for both routes in all 12 seeds.

## What this refutes or leaves open

- It refutes the blanket claim that an unresolved same-range mixture is always geometrically equivalent. Destructive interference can create false angle peaks or complete signal loss; the estimator must abstain or flag low-quality mixtures.
- It does not establish a universal merge threshold, angle-resolution limit, or real-radar performance. Results depend on the array, SNR, phase offsets, amplitudes, and the simple beamformer/unwrap estimator.
- The experiment does not test dynamic target motion, range leakage, multipath, calibration bias, or online re-association. Those require separate validation.

Artifacts: `same_range_merge_split.py`, `protocol.json`, `deterministic_results.json`, and `multiseed_results.json`.
