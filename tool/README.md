# Plotting tools

This directory contains small, standalone scripts for paper-style figures
used in the thesis. They are outside the capture, simulation, and algorithm
data path. The plotting defaults use a restrained MATLAB-like style.

For example, to draw target IQ trajectories at the SNR values used by the
A20 paper-parameterized simulator:

```bash
uv run --with matplotlib \
  python tool/plot_iq_snr.py
```

The default figure is written to
`reports/numerical_simulation_assets_png/iq_snr_target_comparison.png`.

To reproduce a denser mmVib-like controlled vibration (100 um, 50 Hz, 2 kHz
slow-time sampling), use:

```bash
uv run --with matplotlib \
  python tool/plot_iq_snr.py --source sine --duration 0.1 --frames 200 \
  --output reports/numerical_simulation_assets_png/iq_snr_mmvib_style.png
```

To reproduce a frequency-content model from the high-speed maglev guideway
paper A20, using its 24.768 m span, 300 km/h operating speed, six identified
modes, damping ratios, and characteristic vehicle lengths, use:

```bash
uv run --with matplotlib python tool/simulate_a20_response.py
```

The figure is written to
`reports/numerical_simulation_assets_png/a20_paper_response.png` and the
simulated time history is written to
`reports/numerical_simulation_assets_csv/a20_paper_response.csv`. The paper
does not publish modal participation factors or the complete force history.
The script records those quantities as explicit assumptions, combines a
quasi-static passage envelope with small damped modal responses, and scales the
common displacement response to the reported 1.712 mm peak. See
`paper_bridge_simulation/README.md` for the model boundary.

To inspect the algorithm output from the same 4 s A20 package, run:

```bash
uv run --with matplotlib python tool/plot_algorithm_results.py \\
  --result reports/a20_algorithm_result.npz
```

This shows the truth/estimate displacement, error, per-target innovation RMS,
and adaptive measurement variance (R_i).

For an mmVib-inspired visual comparison (the right panel is a clearly labeled
controlled reference, not a change to the A20 guideway model), run:

```bash
uv run --with matplotlib python tool/plot_iq_mmvib_style.py
```

To draw IQ extracted from a saved `chirp_cube`, with its frame mean for
comparison, run:

```bash
uv run --with numpy --with matplotlib python tool/plot_chirp_iq.py \
  --input /tmp/chirp_final_capture4 --range-bin 8
```

This reads the same target IQ as the algorithm, without generating new noise.
It shows entry (0.5–0.8 s) and plateau (1.0–1.3 s) windows of the A20 response.
Both modes share one amplitude normalization and one constant phase rotation;
lines break between loop bursts. PNG and SVG outputs are saved alongside each
other under `reports/numerical_simulation_assets_png/`.
