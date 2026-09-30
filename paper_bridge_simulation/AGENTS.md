# Paper-parameterized experiment rules

This folder creates the one retained paper-parameterized scene. It is a reproducible
research-data generator, not a simulator framework.

- Generate one deterministic high-speed maglev guideway response from the
  published A20 parameters in `response.py`; do not read a measured TDMS file.
- Generate the radar ADC/IQ stream, ADXL355 structural-axis stream, timing
  arrays, manifests, and optional truth using the same `capture_root` layout as
  `capture_program/`.
- Keep the generator direct and deterministic under an explicit seed. Keep
  published values and simulation assumptions separate in the metadata.
- Do not add a scenario registry, multiple synthetic scenes, Ma code, baseline
  methods, deployment code, retries, or generic defensive wrappers.
- Truth is written only for post-run evaluation; it is not an algorithm input.

The output must remain consumable by `python3 -m algorithm.run` without a
source-specific branch in the algorithm.
