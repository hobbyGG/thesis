# Finite radar frame trigger

`frame_trigger` emits a finite train of active-high GPIO pulses on Linux. It
uses the Linux GPIO character-device uAPI v2 directly for GPIO access and
absolute `CLOCK_MONOTONIC` deadlines for the pulse schedule. It has no
libgpiod or pkg-config dependency. A physical GPIO24 loopback branch records
the kernel's rising-edge timestamp for each pulse, but is optional. The normal
two-wire GPIO18-to-`SYNC_IN` plus GND connection records GPIO SET-completion
references and is sufficient for an `algorithm_ready` capture.

The timestamps expose what the host actually observed; they are not a claim of
unmeasured end-to-end radar synchronization accuracy. IWR1843 trigger behavior,
electrical compatibility, board routing, and timing must still be validated on
the bench.

## Build and focused tests

On the Raspberry Pi running Ubuntu 24.04, install the compiler and Linux uAPI
headers, then build:

```sh
sudo apt-get update
sudo apt-get install -y build-essential linux-libc-dev
cd capture_program/native/frame_trigger
make clean
make
make test
make print-hw
```

`make print-hw` must report `linux-gpio-uapi-v2`. A normal Linux hardware build
fails explicitly if the installed headers lack uAPI v2. `MOCK_ONLY=1 make`
is available for hardware-free tests, but that binary refuses hardware mode;
there is no libgpiod-v1 or userspace-timestamp fallback. At runtime, a kernel
or GPIO device that rejects the v2 request also produces an explicit error.

On macOS, the same commands build and test only the hardware-free `--mock`
path. Hardware mode is deliberately unavailable there.

## CLI

```text
frame_trigger \
  --events PATH \
  --summary PATH \
  --gpiochip PATH \
  --output-line N \
  --frequency-hz FLOAT \
  --count N \
  --pulse-width-us N \
  --initial-delay-ms N \
  [--loopback-line N] \
  [--mock]
```

Normal hardware invocation using Linux GPIO line offset 18:

```sh
./frame_trigger \
  --events /tmp/frame-trigger/events.csv \
  --summary /tmp/frame-trigger/summary.json \
  --gpiochip /dev/gpiochip0 \
  --output-line 18 \
  --frequency-hz 50 \
  --count 500 \
  --pulse-width-us 100 \
  --initial-delay-ms 1000
```

`--output-line` and `--loopback-line` are Linux GPIO line offsets, not physical
header pin numbers. The pulse width must be positive and strictly shorter than
the period. Normal completion and handled `SIGINT`/`SIGTERM` make a best-effort
request to return the output LOW; checked deassertion failures produce a
nonzero exit. `SIGKILL`, sudden power loss, and a kernel/driver failure cannot
run process cleanup and therefore cannot guarantee LOW. Fit a hardware
pull-down on the trigger net for a fail-safe level, then verify the actual
waveform on the Pi bench.

The normal radar connection uses two conductors: GPIO18 (physical pin 12) to
IWR1843BOOST `SYNC_IN`, and Pi GND (physical pin 14) to radar GND. To record a
kernel edge timestamp as an additional diagnostic, branch the same GPIO18 net
to GPIO24 (physical pin 18) and add `--loopback-line 24`. This optional branch
does not replace `SYNC_IN` or common ground and does not frequency-lock the
radar and ADXL355 ADC clocks.

Mock mode never accepts a loopback line, because it must not fabricate kernel
edge timestamps:

```sh
./frame_trigger \
  --events /tmp/frame-trigger/events.csv \
  --summary /tmp/frame-trigger/summary.json \
  --gpiochip /dev/gpiochip0 \
  --output-line 18 \
  --frequency-hz 50 \
  --count 10 \
  --pulse-width-us 100 \
  --initial-delay-ms 1 \
  --mock
```

The CSV columns are:

```text
sequence,scheduled_monotonic_ns,asserted_monotonic_ns,deasserted_monotonic_ns,loopback_monotonic_ns
```

Without a physical loopback, the final column is empty and the JSON summary
reports `timestamp_quality: "userspace_set_completed"`. Only successfully read
kernel loopback events produce `timestamp_quality: "kernel_loopback_edge"`.
Count mismatches and missing loopback edges are failures. A
`userspace_set_completed` reference is accepted by the operational
`algorithm_ready` gate. The stricter `fusion_ready` gate additionally requires
the uncertainty of whichever reference is used, radar-to-ADC latency, ADXL
filter delay, hardware validation, and value/geometry calibration.
