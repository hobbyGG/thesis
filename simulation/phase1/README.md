# Phase 1 Simulation Validation

This package implements the first-stage synthetic validation for the thesis method:

- Structural truth is a multi-frequency displacement signal with components near 20 Hz, 40 Hz, and 60 Hz.
- Radar observations are target-wise complex IQ signals whose phases are generated from `phi_i = kappa_i * Theta + b_i`.
- The algorithm receives only wrapped phase and measured acceleration.
- Validation compares baselines and the proposed multi-target structural-main-phase Kalman method.

## Current Method Under Test

The proposed method estimates structural main phase:

```text
x_k = [Theta_k, dotTheta_k]^T
Theta_k = 4*pi*q_k/lambda
```

Each target contributes:

```text
z_corr_i,k = psi_i,k + 2*pi*round((kappa_hat_i*Theta_pred + b_i - psi_i,k)/(2*pi))
```

The same corrected phase is used for Kalman update and online `kappa_i` bootstrap.

## Run Tests

```bash
python3 -m unittest discover tests -v
```

## Run Full Phase-1 Validation

```bash
python3 -m simulation.phase1.run_validation --output-dir simulation/outputs/phase1_validation
```

## Main Outputs

- `metrics.csv`: method-by-scenario RMSE/MAE/max error/phase RMSE/unwrap errors.
- `feasibility_gates.json`: pass/fail feasibility checks.
- `summary.md`: readable validation summary.
- `plots/*.svg`: basic displacement plots generated without matplotlib.

## Interpretation

Passing data-generation tests only means the synthetic observations are reproducible and physically shaped. Passing validation gates means the proposed method meets the current synthetic feasibility criteria. If any gate fails, report the failure and inspect the scenario instead of hiding it by tuning parameters.
