# β pressure test report

This report evaluates the retained N=4 frame path (884.850823 Hz) with the same causal IQ-circle phase and common structural Kalman. Three response intervals are scored: 0.5–1.3 s, 6.3–7.1 s, and 12.1–12.9 s.

The ADXL branch uses causal matched filters and prefix-only least squares. The regularized branch is fixed before the runs: 75% AoA prior + 25% matched ADXL β. No truth is used by the estimator.

## AoA angle bias

| bias | AoA β event RMSE (μm) | ADXL match (μm) | regularized (μm) |
|---:|---:|---:|---:|
| +0.0° | 3.73/3.47/3.69 | 7.19/4.65/3.97 | 4.58/3.84/3.94 |
| +1.0° | 7.52/6.89/6.96 | 7.48/4.65/3.97 | 7.59/6.20/6.12 |
| +2.0° | 14.10/16.81/16.72 | 8.22/4.65/3.97 | 12.38/10.63/9.72 |
| +3.0° | 25.02/25.50/25.71 | 9.37/4.65/3.97 | 21.11/21.09/21.22 |

At +2° the AoA branch is 14.10/16.81/16.72 μm; the ADXL branch stays 8.22/4.65/3.97 μm. At +3° only the ADXL branch remains below 10 μm in all three events.

## Measured range-FFT SNR

| measured SNR | AoA β event RMSE (μm) | ADXL match (μm) | regularized (μm) |
|---:|---:|---:|---:|
| 19.9 dB | 3.28/3.19/3.16 | 4.15/3.11/3.10 | 3.52/3.18/3.17 |
| 14.9 dB | 4.29/6.34/6.80 | 4.24/5.14/5.36 | 4.10/5.89/6.29 |
| 9.9 dB | 13.49/22.64/24.93 | 7.97/13.13/12.53 | 11.12/19.84/21.35 |

At approximately 10 dB, no branch keeps all three events below 10 μm. AoA has the smallest β-only error, so the excess is mainly phase/target-observation noise rather than β.

The isolated β contribution confirms this: at +2° AoA bias, β-only RMSE is AoA 11.67/14.89/14.54 μm, ADXL 5.57/2.32/1.36 μm, and regularized 9.85/8.63/7.49 μm. At 9.9 dB, β-only RMSE is AoA 5.69/8.49/7.07 μm, ADXL 14.98/19.10/20.97 μm, and regularized 8.47/11.38/10.74 μm.

## Target separation

| case | detected targets | AoA β event RMSE (μm) | ADXL match (μm) | regularized (μm) |
|---|---:|---:|---:|---:|
| close-1 | 4 | 3.45/3.01/3.18 | 7.53/4.90/4.26 | 4.41/3.61/3.81 |
| close-2 | 4 | 3.61/3.28/3.51 | 7.52/5.02/4.40 | 4.52/3.78/3.99 |
| close-3 | 1 | 16.62/16.15/16.02 | 11.71/12.75/13.27 | 15.33/15.28/15.32 |

The first two close cases merge two of five returns and still pass the 10 μm event limit for all methods. When all five angles are around 20° the detector returns one equivalent target; all methods exceed 10 μm. A unique β-only error is not reported for merged targets.

## Decision

- Keep AoA β as the nominal path: it is best at 20 dB and nominal angular geometry.
- Use causal ADXL matching as a correction/fallback when AoA has a systematic bias of about 2° or more.
- Do not claim that ADXL solves 10 dB SNR; target observation quality fails before β becomes the only error.
- Do not treat the unresolved five-target case as a β failure; it is a target separation/equivalent-target failure.

Raw results: `results.json`; protocol: `protocol.json`.
