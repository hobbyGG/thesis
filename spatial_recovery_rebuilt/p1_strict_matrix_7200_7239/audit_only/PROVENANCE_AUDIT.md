# Strict matrix provenance audit

Generated: 2026-10-02T04:13:59.038069+00:00

Scope: compact post-run provenance comparison only. No rerun, no raw captures regenerated, and raw per-trial trial.json files were not overwritten

Run status and source
- Manifest status/mode: completed / full
- Compact rows: 200; raw per-trial JSON rows: 200; IDs equal: True
- Shared-field mismatches: 0
- Recorded runner SHA-256 matches current runner: True
- Run manifest SHA-256: `6cc2f4257ecd22f9bc040cd3a4ea9a2b7b76febc0f6e093f750540d3b5efe2bd`

Post-processing and rejected records
- Compact `trials.json` was post-processed after the run: added `abstention_reason` and structured `frozen_guard` to 9 rejected rows; summary received derived audit counters
- Raw per-trial records remain unchanged; synchronized rejected views are in `rejected_trial_summaries.json`
- Rejected rows: 9; all are frozen-test acceleration guard failures
- Raw rejected-row missing audit fields: {"calibration_input_hashes": 9, "frozen_guard": 9, "route_audit": 9, "truth_free_estimator_copy": 9}
  - low_motion_0p005mm__seed7227: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p005mm__seed7238: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p010mm__seed7227: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p010mm__seed7238: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p020mm__seed7227: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p020mm__seed7238: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - low_motion_0p050mm__seed7227: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - stationary__seed7227: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit
  - stationary__seed7238: frozen_test_guard:acceleration_within_frozen_limit=false; raw missing frozen_guard, truth_free_estimator_copy, calibration_input_hashes, route_audit

Retention
- Raw capture arrays retained under full output: 0
- Source hashes and run status are recorded in `PROVENANCE_AUDIT.json`

Protocol and execution metadata
- The copied `protocol.json` has SHA-256 `6006e73fcb5840c8f666b1740c1b7076791ffdc277cf6f0c9b3d8143f806bb0e` and retains legacy `smoke.full_matrix_started=false` plus a descriptive `metrics.full_window_comparison` string
- Those fields are legacy metadata only: the strict runner completed 200 calibration-only trials, called no full-window route, and performed no test-side target detection. The original protocol was preserved
- Corrected audit-only protocol: `spatial_recovery_rebuilt/calibration_only/strict_matrix_7200_7239/full/audit_only/protocol_corrected.json` (SHA-256 `9ab1625b7d317ff59e0f4c63a8fba5613df2efa211741b93e74829e0cb91bc61`)
- `run_manifest.json` source hashes/status are retained for provenance only; they are non-operative and did not control trial behavior

Guard screening and Kalman cold start
- Guards were computed from calibration ADC/ADXL arrays, frozen before test, and checked across test radar frames 200–399 plus ADXL samples 2000–3999; a failed guard abstained before estimator execution
- Matrix guard result: 191 accepted, 9 abstentions; all 9 had acceleration limit failure while finite/time/ADC checks passed
- Each accepted trial starts a fresh retained Kalman state on test frames 200–399. At 100 Hz, the retained 0.20 s cold-start rule selects 20 test frames [200..219] for bias/initial-R residual statistics
- The 21-frame truth reference (elapsed <=0.20 s) is post-run scoring only and is distinct from the 20-frame estimator cold start
