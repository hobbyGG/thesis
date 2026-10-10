# Frozen beta/angle sensitivity v1 pilot

Seed 20261001, stratum low_motion_0p005mm, requested RMS 0.005 mm; one synthetic capture package, calibration frames 0-199, test frames 200-399.

Estimator copy removed truth/ and paper_response_metadata.json; truth was used only after estimation for scoring. Geometry, target selection, and base beta came from calibration frames only. Test projection used frozen geometry with declared angle offsets 0, -1, +1 degrees.

| delta theta (deg) | finite coverage | signed bias (mm) | RMSE (mm) | targets |
|---:|---:|---:|---:|---:|
| +0.0 | 1.000000 | 0.000206788 | 0.001113915 | 5 |
| -1.0 | 1.000000 | 0.000187712 | 0.001103387 | 5 |
| +1.0 | 1.000000 | 0.000230547 | 0.001133493 | 5 |

This is a bounded synthetic sensitivity pilot. It does not reproduce the cloud profile-LS artifact, establish field accuracy, or authorize the 40-seed matrix.
