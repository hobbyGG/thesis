# Hardware acquisition boundary

This folder is the hardware-side acquisition program. It is kept separate from
the academic estimator and owns IWR1843/DCA1000, ADXL355, GPIO timing, packet
decoding, and export of the shared `capture_root` package.

Hardware lifecycle and data-integrity checks are appropriate here because an
incomplete capture cannot be used as an experiment input. Keep those checks
local to this boundary; do not copy them into `algorithm/` or
`paper_bridge_simulation/`.

Do not put thesis methods, target selection, phase unwrapping, Kalman filtering,
Ma methods, or scenario logic in this folder. Changes to the exported package
must preserve the manifests consumed by `algorithm/io.py`.
