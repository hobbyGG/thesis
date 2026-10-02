# Strict P3 follow-up: paired seeds and post-warm-up scoring

Status: completed exploratory scratch follow-up. Six trials were run: seeds `20261001` and `20261002` crossed with stationary, 0.005 mm RMS, and 0.050 mm RMS strata. No raw capture is retained. No causal fusion claim is made.

## Why this follow-up is strict about the score fence

The current calibration-only wrapper freezes geometry and target selection on frames 0--199. The retained Kalman API then estimates phase bias and initial target measurement variance `R_i` from its first 20 supplied samples. To remove that test warm-start interval from the accuracy score without changing tracked code, the follow-up predeclares:

- geometry/selection source: frames 0--199 only
- test warm-up for retained bias/R initialization: frames 200--219
- score: frames 220--399 only (180 frames)
- truth: absent from estimator copies and opened only after all three route outputs are complete, for post-run scoring

This removes warm-start samples from the score. It does not turn the route into a strict calibration-only bias/R estimator; that remains an API limitation and is reported explicitly in each trial JSON.

## Compared routes

- Single target: largest median calibration complex-return magnitude
- Independent per-target: one retained filter per selected target, with the common route's test-warm-up initial `R_i` reused to avoid the singleton `R=9` fallback; each filter adapts its own `R_i` afterward
- Common-state: one shared `[Theta, Theta_dot]` filter with precision-weighted observations and adaptive target `R_i`

All routes use the same package, calibration-frozen geometry, test observations, beta, acceleration preintegration, process parameters, and 20-frame warm-up. The independent baseline is conditional on shared initial `R_i`; it is not a standalone single-target system.

## Metrics

Each compact trial JSON stores test-tail RMSE, MAE, signed bias, standard deviation, maximum absolute error, truth RMS, per-target independent scores, common-vs-single and common-vs-independent-median RMSE reductions, active-target count, internal posterior phase covariance, and target weights/R values.

The common-route innovation diagnostics compute Pearson correlations for the ten target pairs over scored frames 220--399. These are correlations of filter innovations, not truth-error covariance or independent-target noise. Independent-route innovation correlations are also stored.

`N_eff = 1 / sum_i(w_i^2)` is explicitly labeled weight diversity only. It is not covariance-adjusted information or an independent-target count. Off-diagonal observation covariance is not estimated; with covariance `Sigma`, the appropriate combined observation variance would be `wᵀ Sigma w`, while the retained filter uses the diagonal approximation `1/sum_i(1/R_i)`.

## Results (RMSE in micrometres)

| Stratum | Seed | Single | Common | Independent target RMSEs | Common reduction vs single | Common reduction vs independent median | Common innovation corr median (min–max) |
|---|---:|---:|---:|---|---:|---:|---|
| stationary | 20261001 | 1.510 | 1.098 | 1.510, 3.224, 4.583, 2.476, 1.965 | 27.3% | 55.7% | 0.591 (0.397–0.726) |
| stationary | 20261002 | 1.189 | 0.966 | 1.189, 1.585, 3.053, 2.044, 3.927 | 18.8% | 52.7% | 0.618 (0.394–0.881) |
| 0.005 mm | 20261001 | 1.511 | 1.120 | 1.511, 3.235, 4.588, 2.489, 1.980 | 25.9% | 55.0% | 0.591 (0.397–0.726) |
| 0.005 mm | 20261002 | 1.224 | 0.986 | 1.224, 1.607, 3.050, 2.058, 3.928 | 19.4% | 52.1% | 0.618 (0.394–0.881) |
| 0.050 mm | 20261001 | 2.073 | 1.920 | 2.073, 3.622, 4.836, 2.973, 2.541 | 7.4% | 35.4% | 0.592 (0.398–0.726) |
| 0.050 mm | 20261002 | 2.035 | 1.822 | 2.035, 2.257, 3.347, 2.610, 4.218 | 10.5% | 30.2% | 0.619 (0.394–0.881) |

Across these six exploratory trials, common-route RMSE is lower than the selected single target in all six rows, with reductions from 7.4% to 27.3%. Common-route scored innovations have positive median pairwise correlations around 0.59--0.62 (maximum pair 0.73--0.88), demonstrating that the five target innovations are not empirically independent in this route. Independent-route innovation correlations are near zero in these trials (median approximately −0.008 to +0.047, absolute median approximately 0.059), but these are correlations of separate filter residuals and do not prove independent measurement noise.

The weight-diversity median is approximately 4.77--4.92 with five active targets. This must not be interpreted as 4.8 independent observations because common-state innovation correlations are material and off-diagonal observation covariance was not estimated.

## Interpretation and fallback

The six paired rows are a useful descriptive stress check and show a repeatable common-vs-single reduction under this synthetic generator. They do not isolate causality: common and independent routes share geometry, beta, acceleration, phase-bias and initial-R construction; the common state uses a diagonal covariance approximation despite correlated innovations; and two seeds are not a confirmatory sample.

Paper-safe wording:

> After excluding the first 20 test frames used by the retained warm-start initializer, the common structural-state route had lower frozen-test RMSE than the calibration-selected single target in all six exploratory trials. The same trials showed positive pairwise correlations among common-route target innovations (median 0.59--0.62), so `1/sum(w_i^2)` is only weight diversity and cannot be treated as an independent-target count. The result supports a descriptive implementation observation, not a causal accuracy claim or calibrated uncertainty statement. Confirmatory attribution requires calibration-only bias/R initialization, a declared covariance estimator, and a larger paired seed matrix.

If strict calibration-only bias/R initialization is required, the current API cannot provide it without a scratch wrapper that explicitly carries calibration-derived bias/R into the test route. That was not implemented here; no tracked source was changed.

## Files

- `p3_strict_followup.py`: portable runner; output path is a CLI argument; stages temporary packages on the same filesystem and removes each package after scoring
- `results/*.json`: six compact trial records
- `strict_followup_summary.json`: grouped compact summary
- `strict_followup_manifest.json`: seed/stratum scope, truth-free audit and raw-retention status

No raw `.npy`/`.npz` files are retained in this directory.
