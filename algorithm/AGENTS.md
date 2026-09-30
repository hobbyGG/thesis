# Offline algorithm rules

This folder contains the single thesis estimator. It is academic experiment
code, not production software.

- Read the capture package produced by `capture_program/` or
  `paper_bridge_simulation/`.
- Keep the current chain: Range FFT and angle processing, target selection,
  local MUSIC/ML angle refinement, frozen geometry beta, native-time ADXL
  preintegration, and the structural phase Kalman filter.
- Keep modules small and equation-oriented. A module should have one signal
  processing responsibility.
- Do not add hardware control, scenario dispatch, Ma methods, baselines,
  service abstractions, retries, logging frameworks, or generic input
  validation/fallback paths.
- Numerical safeguards that are part of the estimator are valid; keep them in
  the numerical module that uses them.
- `truth/` is for evaluation after estimation and must never influence target
  detection, AoA, beta, or filtering.

The command-line entry point is `python3 -m algorithm.run`. Its only input is a
capture package and its only output is the algorithm result plus summary.
