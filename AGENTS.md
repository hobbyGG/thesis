# Thesis experiment code

This repository is an offline academic experiment, not a deployable service.

The active data path has three parts:

1. `capture_program/` acquires hardware data and exports the capture package.
2. `measured_bridge_simulation/` uses the measured bridge displacement record to
   produce the same capture package for repeatable semi-measured experiments.
3. `algorithm/` reads either package and writes the displacement result.

Keep these boundaries explicit. Do not reintroduce Ma, legacy scenario
registries, broad baseline runners, service layers, retry frameworks, or generic
configuration and validation scaffolding.

The academic code should be direct: arrays in, equations and signal processing,
arrays out. Numerical operations that are part of the method, such as phase
wrapping, finite-value masks, covariance clipping, and measurement-noise
clipping, are allowed and should stay close to the corresponding equation.

`capture_program/` is the only boundary that may retain hardware lifecycle,
packet-integrity, cleanup, and package-completeness checks. Those checks protect
the acquisition contract and must not spread into the offline algorithm.

After changes, verify the package contract and run the retained algorithm
experiment. Do not add compatibility code for deleted experiments.
