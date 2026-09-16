# Raspberry Pi 4 synchronized capture: IWR1843BOOST + DCA1000EVM + ADXL355

The Raspberry Pi 4 is the only acquisition host in this project. The operator
computer connects to the Pi over Wi-Fi and SSH; it does not connect to the
radar USB interface or the DCA1000EVM Ethernet interface and it does not
receive the live data stream.

```text
operator computer --Wi-Fi / SSH--> Raspberry Pi 4
                                      |--SPI + DRDY--> ADXL355
                                      |--USB---------> IWR1843BOOST
                                      |--GPIO18------> IWR1843BOOST SYNC_IN
                                      |       `------> GPIO24 loopback input (optional)
                                      |--GND---------> IWR1843BOOST GND
                                      `--Ethernet----> DCA1000EVM

IWR1843BOOST <--------60-pin HD connector--------> DCA1000EVM
```

Radar UART control, DCA1000 packet capture, ADXL355 sampling, timestamps,
validation, and initial file output all run locally on the Pi. Copy completed
captures to the operator computer only after acquisition has stopped.

> **Validation status:** the software and hardware-free focused tests exist,
> but this document does not claim that the current Pi, ADXL355, radar
> firmware, J6 routing, or trigger waveform has passed a powered bench test.
> Keep `hardware_validated = false` until those checks have actually been
> measured and recorded.

## 1. Make all connections with power off

1. Join IWR1843BOOST and DCA1000EVM through their 60-pin HD connector.
2. Connect the IWR1843BOOST XDS110 USB port to the Pi. It exposes the radar
   configuration and data UARTs, normally `/dev/ttyACM0` and `/dev/ttyACM1`.
3. Connect DCA1000EVM Ethernet directly to the Pi wired interface, normally
   `eth0`.
4. Keep the Pi on the normal LAN through Wi-Fi for SSH control.
5. Connect ADXL355 directly to the Pi GPIO header as shown below.
6. Power each board from its specified supply. USB, Ethernet, and GPIO are not
   substitutes for the required radar-board power supplies.

Never move the 60-pin connector, GPIO wires, or adapter while powered.

### ADXL355 SPI and DRDY wiring

The acquisition configuration uses SPI0 CE0 and BCM GPIO25. Raspberry Pi
physical pin numbers and BCM GPIO line offsets are different; both are shown.

| ADXL355 PMDZ pin | Signal | Raspberry Pi 4 physical pin | BCM line |
| --- | --- | ---: | ---: |
| P1-6 | VDD, 3.3 V | 1 | — |
| P1-5 | DGND | 6 | — |
| P1-2 | MOSI | 19 | GPIO10 |
| P1-3 | MISO | 21 | GPIO9 |
| P1-4 | SCLK | 23 | GPIO11 |
| P1-1 | CS | 24 | GPIO8 / CE0 |
| P1-10 | DRDY | 22 | GPIO25 |

Use 3.3 V only. Confirm the ADXL board's P1 numbering and continuity before
powering it; wire colour is not an electrical identifier. The example
configuration consequently uses:

```toml
spi_device = "/dev/spidev0.0"
gpiochip = "/dev/gpiochip0"
drdy_line = 25
odr_hz = 1000
range_g = 2
spi_hz = 5000000
```

### Radar frame-trigger wiring

Software timestamp mode needs no GPIO connection between the Pi and radar.
Hardware-trigger mode adds the following signals:

| Purpose | Raspberry Pi 4 | IWR1843BOOST |
| --- | --- | --- |
| Frame trigger | physical pin 12 / GPIO18 output | J6-9 `SYNC_IN` |
| Common reference | physical pin 14 / GND | J6-4 GND |
| Optional kernel edge observation | branch the GPIO18 trigger net to physical pin 18 / GPIO24 input | no extra radar pin |

The normal hardware-trigger connection needs two conductors: GPIO18 (physical
pin 12) to `SYNC_IN`, and GND (physical pin 14) to radar GND. The supplied
hardware example uses this layout with `use_loopback = false`; each completed
GPIO SET operation becomes the frame reference and is suitable for the
operational `algorithm_ready` gate.

GPIO24 is an optional diagnostic branch of the same GPIO18 electrical net. It
lets Linux timestamp a returned rising edge as `kernel_loopback_edge`, but it
does not synchronize either ADC clock and it is not required to run the
offline algorithm. If that branch is installed, set `use_loopback = true` and
`loopback_line = 24`. Do not enable GPIO24 while leaving it floating.

J6 is a 2×10 mother connector and may be obstructed by DCA1000EVM. If a passive
right-angle adapter is used, check for mirrored numbering with a continuity
meter. Do not connect J6 3.3 V or 5 V to a Pi GPIO. Keep GPIO18 low until both
boards are correctly powered and the trigger test is intentionally started.
Normal completion and SIGTERM only make a best-effort attempt to return GPIO18
low; SIGKILL cannot run cleanup. Add a hardware pull-down to the real trigger
net and verify its idle level and pulse waveform on the assembled fixture with
an oscilloscope or logic analyzer.

## 2. Understand the two synchronization modes

### `software_timestamp`

- Uses `examples/capture_synchronized_software.toml`.
- Requires radar `frameCfg triggerSelect=1`.
- Adds no radar synchronization wire.
- Records the Pi `CLOCK_MONOTONIC` times immediately before sending and after
  returning from `sensorStart`.
- Estimates radar-frame times from that bracket and the nominal frame period
  in the successfully decoded radar algorithm manifest. Configured frame count
  is never accepted as a fallback.

The DCA1000 PCAP timestamp is the time an Ethernet packet reached the Pi. It
is **not** the radar ADC time or radar frame-start time. Nanosecond storage
resolution does not turn transport latency into nanosecond timing accuracy.

### `hardware_trigger`

- Uses `examples/capture_synchronized_hardware.toml`.
- Requires radar `frameCfg triggerSelect=2`.
- Sends a finite pulse train from GPIO18 to J6-9 `SYNC_IN`.
- Requires the trigger count to equal `capture_frames` and caps trigger
  frequency at 90% of the configured radar frame rate. If omitted, the
  coordinator chooses that 90% value (100 Hz for the supplied 9 ms frameCfg).
- Records `frame_trigger_events.csv` and `frame_trigger_summary.json`; GPIO24
  loopback provides kernel edge timestamps when the optional branch is present.
  Without it, timestamp quality is `userspace_set_completed`, which remains a
  valid Pi-controlled hardware-trigger reference for `algorithm_ready` data.

This provides one Pi-timed trigger reference per intended radar frame, but the
edge is not itself a measured radar ADC or frame-start instant. It also does
not give ADXL355 and the radar a common ADC clock. ADXL355 still free-runs at
nominal 1 kHz, radar chirp/ADC timing remains internal to the radar, and
sensor/filter latencies still require characterization.
`hardware_validated = false` is the correct setting until firmware acceptance
of `SYNC_IN`, DCA routing, voltage levels, trigger count, and measured timing
have all passed a bench test.

The initial delay and every inter-trigger period must both stay below 5 s.
This is a conservative guard against DCA1000 stopping after roughly 10 seconds
without LVDS data; values at or above 5 s are rejected.

## 3. Prepare 64-bit Raspberry Pi OS

Run all deployment commands on the Pi, normally through SSH:

```bash
sudo apt update
sudo apt install -y \
  git tcpdump libcap2-bin build-essential linux-libc-dev
```

The native ADXL and frame-trigger helpers use the Linux GPIO character-device
uAPI v2 directly through `linux/gpio.h`. They do not link to `libgpiod` and do
not require `pkg-config`. A normal hardware build fails clearly if the installed
Linux UAPI headers do not expose v2.

Enable SPI through `raspi-config` (`Interface Options` → `SPI`), reboot if
requested, and confirm the devices:

```bash
ls -l /dev/spidev0.0 /dev/gpiochip0
```

Install `uv` using its official instructions, then install the Python project
and build both native helpers:

```bash
cd ~/thesis/capture_program
uv sync

make -C native/adxl355_capture
make -C native/adxl355_capture print-hw
make -C native/frame_trigger
```

`print-hw` must report:

```text
ADXL355 Linux hardware support: 1
```

The build products used by the synchronized examples are:

```text
native/adxl355_capture/build/adxl355_capture
native/frame_trigger/frame_trigger
```

The two native test targets are focused, hardware-free checks and can be run
without invoking the complete repository suite:

```bash
make -C native/adxl355_capture test
make -C native/frame_trigger test
```

They do not prove real SPI, DRDY, `SYNC_IN`, or timing behaviour.

If the SSH user cannot access UART, SPI, or GPIO devices, add it to the groups
present on the Pi and reconnect the SSH session:

```bash
sudo usermod -aG dialout,spi,gpio "$(id -un)"
```

## 4. Identify the radar UARTs

After connecting IWR1843BOOST USB, inspect the paths on the Pi:

```bash
lsusb
ls -l /dev/ttyACM*
ls -l /dev/serial/by-id/ 2>/dev/null || true
```

Resolve which by-id symlink is configuration and which is data, then put those
stable `/dev/serial/by-id/...` paths in both TOML files. Preflight rejects
`/dev/ttyACM*` ordering by default; `--allow-unstable-serial` exists only for
explicit diagnostics.

## 5. Configure the direct Pi-to-DCA link

The dedicated link uses:

- Pi wired interface: `192.168.33.30/24`
- DCA1000EVM: `192.168.33.180`
- DCA control/data UDP ports: `4096` and `4098`
- Pi Wi-Fi: normal LAN address, used only for SSH

Find and configure the wired interface without adding a default gateway:

```bash
ip -br link
sudo ip link set eth0 up
sudo ip address replace 192.168.33.30/24 dev eth0
ip -br address show dev eth0
ip route
```

Keep the default route on Wi-Fi. Grant the local `tcpdump` process only its
packet-capture capabilities:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip "$(command -v tcpdump)"
getcap "$(command -v tcpdump)"
```

## 6. Edit and preflight one mode

Start with software timestamp mode. In both example TOML files, verify the Pi
interface, host IP, both UART paths, radar configuration path, frame count,
and native binary paths. The ADXL executable must point to the Makefile output:

```toml
executable = "native/adxl355_capture/build/adxl355_capture"
```

Run the read-only preflight for software timestamp mode:

```bash
cd ~/thesis/capture_program
uv run mmwavecapture-preflight \
  --interface eth0 \
  --host-ip 192.168.33.30 \
  --config-serial /dev/serial/by-id/CONFIG_UART \
  --data-serial /dev/serial/by-id/DATA_UART \
  --spi-device /dev/spidev0.0 \
  --gpiochip /dev/gpiochip0 \
  --adxl-binary native/adxl355_capture/build/adxl355_capture \
  --radar-config examples/configs/iwr1843_software_trigger.cfg \
  --capture-frames 10 \
  --output-path example_synchronized_dataset \
  --sync-mode software_timestamp
```

For hardware-trigger mode, also check the trigger executable:

```bash
uv run mmwavecapture-preflight \
  --interface eth0 \
  --host-ip 192.168.33.30 \
  --config-serial /dev/serial/by-id/CONFIG_UART \
  --data-serial /dev/serial/by-id/DATA_UART \
  --spi-device /dev/spidev0.0 \
  --gpiochip /dev/gpiochip0 \
  --adxl-binary native/adxl355_capture/build/adxl355_capture \
  --radar-config examples/configs/iwr1843_hardware_trigger.cfg \
  --capture-frames 10 \
  --output-path example_synchronized_dataset \
  --sync-mode hardware_trigger \
  --trigger-binary native/frame_trigger/frame_trigger
```

Replace the two UART placeholders with the names observed in step 4. Every line
must report `PASS`. Preflight is deliberately read-only: it checks paths,
permissions, executable capabilities, Pi/DCA subnet, UDP binds, and whether the
estimated capture plus safety margin fits on the output filesystem. It does not
prove ADXL identity, GPIO numbering, electrical continuity, radar firmware
support, or an actual trigger waveform.

## 7. Record a short Pi-local capture

Run software timestamp mode first:

```bash
uv run mmwavecapture-std examples/capture_synchronized_software.toml
```

Only after the additional wiring and firmware checks are ready, run the
hardware-trigger configuration:

```bash
uv run mmwavecapture-std examples/capture_synchronized_hardware.toml
```

The program starts ADXL355, waits for its ready file, and records the configured
pre-roll first. It supervises the ADXL child while waiting for the trigger train
and radar completion; an early child exit interrupts the blocking backend and
fails the combined capture. It then stops radar, records post-roll, and finally
stops and validates ADXL355.
This keeps the pre-roll delay outside DCA1000's no-LVDS timeout window.
Failures are cleaned up in reverse order and partial files are retained for
diagnosis.

## 8. Output and timestamp contract

A successful synchronized run has this layout (array lists abbreviated):

```text
example_synchronized_dataset/capture_00000/
|-- capture.log
|-- config.toml
|-- status.json
`-- synchronized/
    |-- radar/
    |   |-- dca.pcap
    |   |-- radar.cfg
    |   |-- dca.json
    |   `-- algorithm_input/
    |       |-- adc_cube.npy
    |       |-- chirp_cube.npy
    |       |-- frame_times_s.npy
    |       |-- frame_receive_times_epoch_ns.npy
    |       `-- manifest.json
    |-- adxl355/
    |   |-- samples.bin
    |   |-- summary.json
    |   |-- ready.json
    |   |-- config.json
    |   `-- algorithm_input/
    |       |-- acceleration_raw.npy
    |       |-- acceleration_mps2.npy
    |       |-- drdy_monotonic_ns.npy
    |       |-- sample_times_s.npy
    |       `-- manifest.json
    `-- sync/
        |-- config.json
        |-- manifest.json
        |-- timeline.json
        |-- radar_frame_monotonic_ns.npy
        |-- frame_trigger_events.csv       # hardware mode only
        `-- frame_trigger_summary.json     # hardware mode only
```

Only `CLOCK_MONOTONIC` fields are used for alignment. Wall-clock values are
provenance only. In software mode, `sync/manifest.json` reports a
sensor-start-bracket estimate. In hardware mode it records trigger timestamp
quality plus `hardware_validated`; the flag remains false until bench evidence
exists. `radar_frame_monotonic_ns.npy` uses the sensor-start bracket midpoint
plus the decoded radar manifest's nominal frame period in software mode; in
hardware mode it uses GPIO24 kernel loopback edges when the optional branch is
present. Without that branch it has only GPIO18 `userspace_set_completed`
times: a software completion timestamp, not an observed physical edge. Both
forms are accepted for operational `algorithm_ready` processing. These are
reference times, not radar ADC sampling instants. In both modes, PCAP
timestamps remain Ethernet receive times.

`sync/timeline.json` is not published from configured frame counts. It depends
on the real `radar/algorithm_input/manifest.json` produced after packet and
layout validation. `load_synchronized_timeline()` requires that timeline, the
sibling `sync/manifest.json`, and any capture-root `status.json` all report
complete; it also cross-checks their modes, timestamp quality, validation flag,
array metadata, nominal period, provenance, and decoded radar metadata.

Check the final status and manifests before copying data:

```bash
run=example_synchronized_dataset/capture_00000/synchronized
grep -q '"status": "complete"' "$run/../status.json"
test -s "$run/radar/dca.pcap"
test -f "$run/radar/algorithm_input/manifest.json"
test -f "$run/adxl355/algorithm_input/manifest.json"
test -f "$run/sync/manifest.json"
test -f "$run/sync/timeline.json"
tcpdump -nn -r "$run/radar/dca.pcap" 'udp port 4098' -c 5
```

Load the validated ADXL arrays and radar reference timeline without parsing
the native binary or trigger CSV in downstream code:

```python
from mmwavecapture import load_adxl355_input, load_synchronized_timeline

run = "example_synchronized_dataset/capture_00000/synchronized"
adxl = load_adxl355_input(f"{run}/adxl355")
timeline = load_synchronized_timeline(run)
print(adxl.acceleration_mps2.shape)
print(timeline.radar_frame_monotonic_ns)
print(timeline.manifest["provenance"])
print(timeline.combined_manifest["status"])
```

Here `run` is the synchronized hardware directory.

For algorithm work, use the fusion loader/checker rather than treating a
structurally complete directory as usable data:

```bash
uv run mmwavecapture-fusion-check "$run"
```

This command enforces the operational `algorithm_ready` gate. Add
`--require-calibrated` when the stricter `fusion_ready` gate is required.

```python
from mmwavecapture import load_fusion_input

capture = load_fusion_input(run)
assert capture.algorithm_ready, capture.quality.algorithm_readiness_failures
```

`algorithm_ready` is the default operational gate: hardware `SYNC_IN`, a
complete non-mock ADXL stream, lossless radar chirps, and full native-time
coverage. It accepts the normal `userspace_set_completed` timeline or the
optional GPIO24 `kernel_loopback_edge` timeline.

`fusion_ready` is the stricter calibrated/metrology gate. It additionally
requires bench-validated hardware, characterized uncertainty for the chosen
trigger reference, measured radar reference-to-ADC latency and uncertainty,
calibrated ADXL digital-filter delay and uncertainty, and a validated
value/geometry file copied into the package. Copy
`examples/fusion_calibration.template.json`, replace the placeholders with
fixture-specific measurements, and only then set `validated=true`. The radar
and ADXL arrays retain separate native timelines; Phase-1 performs exact ADXL
preintegration over each radar interval instead of forcing equal rates.

Run the complete offline path from the repository root after copying the
finished capture (or directly on the Pi):

```bash
PYTHONPATH=capture_program/src \
  capture_program/.venv/bin/python -m simulation.phase1.run_captured \
  "$run" --adxl-axis x --adxl-sign 1
```

This writes `algorithm/phase1_result.npz` plus a JSON provenance summary. Use
the ADXL axis matching the installed sensor orientation and set
`--adxl-sign -1` if its positive direction is opposite to the chosen positive
structural-displacement direction. Add
`--require-calibrated` only when the stricter `fusion_ready` gate is required.

The operator computer may retrieve that completed directory with `scp` or
`rsync`. It remains outside the live capture path.

## 9. ADXL355 1 kHz fail-closed policy

At 1 kHz, the collector accepts a real sample only when the timestamp/data
pair is unambiguous:

1. Kernel DRDY line sequence numbers are contiguous.
2. Each GPIO uAPI v2 read contains exactly one DRDY event; queued historical
   batches are treated as scheduler backlog.
3. A pre-pop `STATUS`/`FIFO_ENTRIES`/temperature snapshot reports exactly three
   FIFO axis entries (one XYZ set) and no FIFO overrun.
4. Exactly nine bytes are popped from `FIFO_DATA`; FIFO markers, empty flags,
   and virtual bits must be valid.
5. A second `FIFO_ENTRIES` read must be zero before the record is accepted.

The collector does not compare FIFO XYZ with current-data XYZ. The summary's
`fifo_xyz_mismatches` counter is retained for schema compatibility and remains
zero in this implementation. Any line gap, backlog, overrun, FIFO protocol
error, nonzero post-pop depth, I/O error, or zero-sample run produces a failed
summary. Already-written records remain diagnostic partial data and no complete
ADXL algorithm-input package is published. Do not weaken these checks merely
to make a stressed Pi appear to pass; first reduce system/storage load or
redesign the timestamp reconstruction and record schema.

The current raw header marks ADXL355 digital-filter group delay as
uncalibrated. A stored value of zero means “not calibrated,” not zero physical
latency.

## 10. What focused tests and preflight do not prove

A powered, measured fixture is still required to establish:

- correct ADXL pin numbering, SPI mode/signal integrity, and sustainable 1 kHz
  DRDY servicing without backlog;
- actual XDS110 UART mapping and sustained DCA packet integrity;
- coexistence of Wi-Fi SSH and the direct DCA Ethernet stream;
- IWR1843 firmware acceptance of `frameCfg triggerSelect=2`;
- J6-9 routing while DCA1000EVM is attached, GPIO voltage compatibility, and
  the physical `SYNC_IN` waveform;
- one trigger per decoded radar frame, measured trigger latency/jitter, and
  ADXL355 digital-filter group delay.

Until those checks pass, use the output for software development and fixture
validation, not as proof of experimentally validated hardware synchronization.
