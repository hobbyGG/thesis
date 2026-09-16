# Pi 4 focused hardware validation — 2026-08-30

This report records focused bench checks only. It is not a timing-calibration
certificate and does not set `hardware_validated=true`.

## Validated paths

- Native ADXL355 capture on Pi SPI0 CE0 and GPIO25 DRDY completed 100/100
  samples at 1 kHz and 5 MHz SPI. Kernel line sequence gaps, FIFO overruns,
  GPIO backlog, FIFO protocol errors, and post-pop depth errors were all zero.
  Mean DRDY interval was approximately 999.4 us; the static acceleration norm
  was approximately 0.99 g after the startup transient.
- Software-timestamp synchronized capture
  `example_synchronized_dataset/capture_00001` completed with 10 radar frames,
  8300 ADXL samples, an ADC cube of `(10, 8, 256)`, and a lossless chirp cube of
  `(10, 16, 8, 256)`. The ADXL timeline covered every radar reference.
- Hardware `SYNC_IN` diagnostic capture with `use_loopback=false`,
  `example_synchronized_dataset/capture_00003`, completed with 10 radar frames,
  9275 ADXL samples, packet integrity, a `(10, 8, 256)` ADC cube, and a
  `(10, 16, 8, 256)` chirp cube. This proves that GPIO18 pulses reach the radar,
  and provides an operational `userspace_set_completed` frame reference.
- The normal hardware configuration with `use_loopback=true` failed closed in
  `capture_00002`: 10 output pulses were emitted and zero GPIO24 rising edges
  were observed. The partial capture was not published as valid synchronized
  data.

## Optional wiring for a kernel-loopback timing check

```text
Pi physical 12 / GPIO18 ----+----> IWR1843BOOST SYNC_IN
                            |
                            +----> Pi physical 18 / GPIO24 input

Pi physical 14 / GND ------------> IWR1843BOOST GND
```

GPIO24 must be a branch of the same GPIO18 electrical net. Do not connect a
power rail to either GPIO. Power down before changing the wiring. After adding
the branch, set `use_loopback=true` and `loopback_line=24`, then rerun the
hardware example. Success requires 10 emitted and 10 kernel-observed loopback
edges plus 10 lossless radar frames. This check is optional for the operational
algorithm path.

## Scientific-readiness items still intentionally blocked

- Measure GPIO loopback edge timestamp uncertainty.
- Calibrate radar trigger-reference-to-ADC latency and uncertainty.
- Calibrate ADXL355 1 kHz digital-filter group delay and uncertainty.
- Validate ADXL bias/scale/axis rotation and radar range/channel/array geometry.
- Set `hardware_validated=true` only after the physical checks and attach a
  validated fusion-calibration artifact.

Until then, `mmwavecapture-fusion-check` may report `algorithm_ready=true` for
complete hardware-SYNC data but must keep `fusion_ready=false` and list the
remaining scientific-calibration blockers.
