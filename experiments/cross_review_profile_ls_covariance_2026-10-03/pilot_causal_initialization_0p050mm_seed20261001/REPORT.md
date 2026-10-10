# Causal initialization comparison — bounded local pilot

Seed 20261001, synthetic 1 Hz sine, requested RMS 0.05 mm. Generated input file hashes and frozen geometry exactly match the preceding 0.05 mm pilot. Same IQ, selected targets, geometry/beta, Q, P0 and ADXL preintegration feed both routes. No tracked algorithm changes, Git writes, or truth-based tuning.

Existing interfaces suffice: AlgorithmConfig(cold_start_duration_s=0.0, cold_start_r_mode="fixed") gives one-sample bias; RadarInput.initial_r=9 fixes the initial R; P0=diag(25,400) and Q=50000 are existing defaults. Subsequent posterior adaptive R remains identical in both routes: fixed *initial* R does not mean fixed R throughout.

For the causal route q0 is the first test sample, all five biases use that sample only and q_hat[0]=0. No future samples are used for initialization. Changing radar phases in frames 100–199 of the test window leaves its first 100 outputs exactly unchanged. Both routes are scored post-run using q_hat-q_hat[0] against truth-truth[0], with all 200 samples included. This is a predetermined reference, not a fitted error correction.

The historical warmup uses 20 test samples before recursion, requiring 0.19 s sample-span latency (nominal warmup setting 0.20 s). Its 200-sample series is retained solely as a retrospective offline comparator; its early outputs are NOT presented as causally available or retroactively emitted online. A genuinely delayed online warmup implementation would require a different state-handoff protocol and is not claimed here. Finite coverage below is not online availability or uncertainty coverage.

| Route | First-reference full RMSE mm | Bias mm | q RMS mm | Finite coverage | Initialization latency s |
|---|---:|---:|---:|---:|---:|
| warmup20_retrospective_offline_comparator | 0.002016931 | -0.000770191 | 0.051561550 | 1.000 | 0.19 |
| causal_first_sample | 0.002258717 | -0.000989879 | 0.051584750 | 1.000 | 0.00 |

Original warmup matched-mean score: 0.002084585 mm; historical 21-frame reference score: 0.001924382 mm. These reproduce the previous pilot.

Causal RMSE increases by 0.000241786 mm (11.99%), so this pilot does not show an accuracy gain from causal initialization. It demonstrates executable first-sample startup without excitation-based DCF fitting in this one synthetic case. Geometry still requires frames 0–199; causality here is relative to the subsequent test start, not immediate startup from the first capture frame. General field validity, high-amplitude phase-slip robustness, absolute displacement, and multi-target superiority remain unproved.

Run command from repository root:

```sh
python3 experiments/cross_review_profile_ls_covariance_2026-10-03/pilot_causal_initialization_0p050mm_seed20261001/run_pilot.py
```

Protocol and source manifest were frozen before execution. Three estimation calls comprise two comparison routes and one future-radar causal fence; no seed/stratum matrix. All raw arrays existed only in temporary directories.
