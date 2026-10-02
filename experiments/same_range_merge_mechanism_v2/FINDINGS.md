# Same-range split/merge mechanism, final v2

This is a bounded, reproducible simplified-array mechanism check. It is not a full FMCW/radar or real-data validation. All six scenes contain the same common structural motion and one range cell. The estimator sees IQ plus fixed instrument constants only; `q`, true angles, amplitudes and static phases are used only by the generator/evaluator. The 8-element ULA uses an array-only Bartlett calibration spectrum, conventional merge, a two-angle least-squares split route, and a one-RX `range_only` control. Every route uses the same positive phase sign and first-test-sample reference.

Protocol was fixed in `PROTOCOL.md`, then unit checks passed before 12 seeds (200–211). Unit checks: positive-angle recovery 25.0 degrees, covariance-vs-direct spectrum max error 2.8e-15, noiseless single-source RMSE 7.6e-17 mm, exact opposite-source cancellation 1.6e-16.

## 12-seed results

| case | route | coverage | median RMSE mm | p90 RMSE mm | paired split−merge |
|---|---|---:|---:|---:|---:|
| close_benign (25°,29°, amplitudes 1/.8) | range_only | 12/12 | 0.00392 | 0.00510 | — |
|  | merge | 12/12 | 0.00142 | 0.00207 | — |
|  | split_ls | 0/12 | — | — | — |
| separated_benign (-10°,45°, 1/.8) | range_only | 12/12 | 0.11837 | 0.14872 | — |
|  | merge | 12/12 | 0.02361 | 0.02572 | — |
|  | split_ls | 12/12 | 0.00215 | 0.00315 | -0.02119 |
| separated_unequal (-10°,45°, 1/.5) | range_only | 12/12 | 0.07765 | 0.09185 | — |
|  | merge | 12/12 | 0.01385 | 0.01591 | — |
|  | split_ls | 12/12 | 0.00270 | 0.00386 | -0.01115 |
| close_destructive (25°,29°, equal, phase offset pi) | range_only | 12/12 | 0.11715 | 0.14906 | — |
|  | merge | 12/12 | 0.08210 | 0.09932 | — |
|  | split_ls | 12/12 | 0.02681 | 0.03156 | -0.05557 |
| coincident_cancel (27°,27°, equal, phase offset pi) | all routes | 0/12 | — | — | — |
| symmetric_control (-25°,25°, 1/.8; same cos projection) | merge | 12/12 | 0.00531 | 0.00664 | — |
|  | split_ls | 12/12 | 0.00687 | 0.00837 | +0.00150 |

## Supports

- When same-range angles are clearly separable in this model, target-level split produced a large and repeatable waveform improvement over one merged phasor: split beat merge in all 12 paired trials for both separated benign cases, with median RMSE reductions of 0.0212 mm and 0.0111 mm. The raw range-only control was much worse.
- For a benign close pair, the array-only detector returned one peak in every seed; split abstained and the merge route had full coverage and low error. This is the mechanism-level condition under which an equivalent target is useful.
- The asymmetric separated cases differ in `cos(theta)` as well as steering angle, so their gain is not explainable only by a symmetric-angle amplitude weighting artifact. The symmetric control (−25°, +25°) had the same `cos(theta)` projection and showed no split benefit (split RMSE was 0.0015 mm worse), a useful negative control.

## Refutes / limits

- An unresolved mixture is not always geometrically equivalent. In the close destructive case, opposite static phases generated false Bartlett peaks near 16.5° and 38.5° instead of the true 25°/29° pair; all routes remained covered but waveform errors were large. In the coincident cancellation limit, every route failed the amplitude guard in all seeds.
- Coverage alone is unsafe: a false split can be finite yet geometrically wrong. Low-amplitude/conditioning diagnostics or an abstention policy are required.
- These numbers support only this fixed array, SNR, phase/amplitude set and simple beamforming/LS estimator. They do not establish a universal angular threshold, prove real-radar performance, or test range leakage, multipath, calibration drift, target migration, tracker association, Kalman fusion or ADXL timing.

Artifacts: `PROTOCOL.md`, `run_experiment.py`, `smoke.json`, and `multiseed.json`.
