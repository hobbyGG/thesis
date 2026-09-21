# Semi-measured experiment rules

This folder creates the one retained semi-measured scene. It is a reproducible
research-data generator, not a simulator framework.

- Read the measured TDMS bridge displacement record from `datafile/`.
- Generate the radar ADC/IQ stream, ADXL355 structural-axis stream, timing
  arrays, manifests, and optional truth using the same `capture_root` layout as
  `capture_program/`.
- Keep the generator direct and deterministic under an explicit seed.
- Do not add a scenario registry, multiple synthetic scenes, Ma code, baseline
  methods, deployment code, retries, or generic defensive wrappers.
- Truth is written only for post-run evaluation; it is not an algorithm input.

The output must remain consumable by `python3 -m algorithm.run` without a
source-specific branch in the algorithm.
