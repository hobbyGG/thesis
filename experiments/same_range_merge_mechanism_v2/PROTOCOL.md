# Locked development protocol, version 2

This protocol is written before running the v2 cases. It follows exploratory smoke work in the parent directory, which exposed a conjugated covariance sign error and symmetric-angle confounding. Earlier outputs are development-only, superseded, and must not be cited as final evidence. This is a bounded mechanism study, not a preregistered or held-out validation study.

## Generator

Eight centered half-wavelength ULA elements. Lambda = 4 mm. All scatterers occupy one range cell. Complex IQ is sum_i a_i exp(j*psi_i) a(theta_i) exp(j*4*pi*q(t)*cos(theta_i)/lambda) + circular complex Gaussian noise. One structural displacement q(t) is shared; directions have different LOS projections. Motion q(t) = 0.8*sin(2*pi*3*t+p) + 0.2*sin(2*pi*5*t+0.43-0.2*p) mm, 256 frames at 100 Hz. p varies with seed. Fixed noise sigma per real/imag coordinate = 10^(-35/20)/sqrt(2), independent of scene/cancellation. No range migration, angle migration, chirp physics, hardware impairments, independent scatterer motion or multipath.

## Estimator (IQ and fixed instrument constants only)

- First 128 frames are calibration; last 128 frames are evaluation
- Bartlett calibration spectrum (z.T @ z.conj(), no conjugate-sign reversal) on -60..60 degrees in 0.25-degree steps
- Detect local peaks with 12-degree separation, prominence >=1% of strongest spectrum power, amplitude >=18% of strongest peak power; at most 2 peaks
- merge: one strongest detected angle, one conventional projection, fixed geometry cos(theta_hat)
- split_ls: two detected angles, joint least-squares reconstruction from A(theta_hat), fixed geometry per channel; amplitude-squared calibration weights for common displacement fusion. Abstain if fewer than 2 peaks or steering condition >20
- range_only: one physical RX (first centered element), same strongest detected angle conversion. It represents raw range-bin phase with the best available one-angle geometry, not an oracle centroid
- Minimum test IQ amplitude must exceed 5*fixed noise sigma times the extraction noise gain. No truth-derived gates
- All routes unwrap their own test IQ and subtract the first test phase, comparing with q_test-q_test[0], same sign, without truth-based fit, sign selection or offset correction
- No Kalman/ADXL; isolate frontend target definition and phase/geometry mechanism

## Fixed cases

All use the same motion/noise above:

1. close_benign: angles 25,29 degrees; amplitudes 1,0.8; phases 0.15,-0.30 rad
2. separated_benign: angles -10,45 degrees; amplitudes 1,0.8; phases 0.15,-0.30 rad
3. separated_unequal: angles -10,45 degrees; amplitudes 1,0.5; phases 0.15,-0.30 rad
4. close_destructive: angles 25,29 degrees; amplitudes 1,1; phases 0,pi rad
5. coincident_cancel: angles 27,27 degrees; amplitudes 1,1; phases 0,pi rad
6. symmetric_control: angles -25,25 degrees; amplitudes 1,0.8; phases 0.15,-0.30 rad (same cos projection; no geometric-mixing difference)

## Sequence and outcomes

Run algebra unit checks: one source returns its positive angle; noiseless single-source waveform recovery at known grid angle; opposite identical sources cancel; covariance spectrum agrees with direct mean beam power. Then seed 100 deterministic cases. Only if checks and execution succeed, run 12 new seeds 200..211 with no case/threshold changes. Report every trial's coverage, abstention reason, waveform RMSE, max error and detected angles. Summaries report coverage and accepted-only median/p90; paired improvements only for mutually covered trials. A 0.01 mm waveform RMSE success threshold is descriptive, not an estimator gate. Do not claim statistical generalization or universal merge equivalence.
