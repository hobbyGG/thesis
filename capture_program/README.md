Millimeter-wave Capture Standard (mmwave-capture-std)
=====================================================

[![Documentation Status](https://readthedocs.org/projects/mmwave-capture-std/badge/?version=latest)](https://mmwave-capture-std.readthedocs.io/en/latest/?badge=latest)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![License: BSD 3-Clause-Clear](https://img.shields.io/badge/License-BSD%203--Clause--Clear-green.svg)](https://spdx.org/licenses/BSD-3-Clause-Clear.html)

**mmwave-capture-std** is a *fast*, *reliable*, and *replicable*
Texas Instruments millimeter-wave capture toolkit,
focus on data capturing and raw data parsing.

Project deployment topology
---------------------------

The Raspberry Pi 4 is the only acquisition host. The operator computer only
controls the Pi through Wi-Fi/SSH; no radar USB or DCA1000 Ethernet capture
connection terminates at the operator computer.

```text
operator computer --Wi-Fi / SSH--> Raspberry Pi 4
                                      |--SPI + DRDY--> ADXL355
                                      |--USB---------> IWR1843BOOST
                                      |--GPIO18------> IWR1843BOOST SYNC_IN
                                      |       `------> GPIO24 loopback input (optional)
                                      |--GND---------> IWR1843BOOST GND
                                      |  (two required wires in hardware-trigger mode)
                                      `--Ethernet----> DCA1000EVM

IWR1843BOOST <--------60-pin HD connector--------> DCA1000EVM
```

The capture command, radar UART control, DCA packet recording, ADXL355 sampling,
timestamps, integrity checks, and initial file output all run locally on the Pi. See
[PI4_CAPTURE.md](PI4_CAPTURE.md) for the required setup.

It stands out with three key attributes:

1. Fast: It parses raw data into `np.ndarray[np.complex64]` **2.09** times
   faster than state-of-the-art packages (0.59s v.s. 1.239s).

2. Reliable: It makes users easily identify and debug hardware issues,
   and provides fine-grained control over different hardware.
   It achieves this by comprehensive logging (stderr & file) and by separating
   the hardware setup from the data capture code.

3. Replicable: It simplifies the process of replicating the recording setup
   by using a toml config file to manage capture hardware, layout the dataset
   as HDF5-like structure, and provide sensor config files to each capture result.

Capture Millimeter-wave Raw Data is Easy
----------------------------------------

Here is an example of using `mmwave-capture-std` to capture mmwave data
from IWR1843BOOST and DCA1000EVM:

```bash
$ uv run mmwavecapture-std examples/capture_iwr1843.toml
2023-06-02 :43.91 | INFO     | ...:...:225 - Capture ID: 0
2023-06-02 :43.91 | INFO     | ...:init_hw:230 - Initializing capture hardware `iwr1843`..
2023-06-02 :49.32 | SUCCESS  | ...:init_hw:245 - Capture hardware `iwr1843` initialized
2023-06-02 :49.32 | SUCCESS  | ...:init_hw:247 - Total of 1 capture hardware initialized
2023-06-02 :49.32 | INFO     | ...:capture:258 - Adding capture hardware `iwr1843`
2023-06-02 :49.32 | INFO     | ...:capture:121 - Preparing capture hardware
2023-06-02 :49.32 | INFO     | ...:capture:125 - Starting capture hardware
2023-06-02 :49.42 | SUCCESS  | ...:capture:128 - Capture started
2023-06-02 :52.49 | INFO     | ...:capture:132 - Capture finished
2023-06-02 :52.49 | INFO     | ...:capture:134 - Dumping capture hardware configurations
2023-06-02 :52.49 | SUCCESS  | ...:capture:270 - Capture finished, all files ...
```

Nice and easy! Your capture result will be stored like this with HDF5-like structure:

```bash
☁  mmwave-capture-std [main]  tree example_dataset
example_dataset
└── capture_00000
    ├── capture.log
    ├── config.toml
    ├── status.json
    └── iwr1843
        ├── algorithm_input
        │   ├── adc_cube.npy
        │   ├── chirp_cube.npy
        │   ├── frame_times_s.npy
        │   └── manifest.json
        ├── dca.json
        ├── dca.pcap
        └── radar.cfg
```

You probably will need to modify the configuration to reflect your
capture hardware setup. Change the following setting in `example/capture_iwr1843.toml`
to your setup: (assume you did not change any setting on DCA1000EVM EEPROM)

```toml
[hardware.iwr1843]
dca_eth_interface = "eth0" # Pi wired port connected directly to DCA1000EVM
radar_config_port = "/dev/ttyACM0"
radar_data_port = "/dev/ttyACM1"
capture_frames = 10
```

Synchronized radar and ADXL355 capture
--------------------------------------

The synchronized collector runs the radar/DCA and ADXL355 under one Pi capture
lifecycle. Build the two native GPIO helpers on the Pi first:

```bash
sudo apt install -y build-essential linux-libc-dev
make -C native/adxl355_capture
make -C native/adxl355_capture print-hw   # must report hardware support: 1
make -C native/frame_trigger
```

Both native helpers use the Linux GPIO character-device uAPI v2 directly.
They need compatible kernel UAPI headers, but do not link to `libgpiod` and do
not require `pkg-config`.

The default ADXL355 wiring is SPI0 CE0 plus DRDY on GPIO25: physical pins
1/6/19/21/23/24/22 provide 3.3 V, GND, MOSI, MISO, SCLK, CE0, and DRDY. Full
ADXL board pin mapping and power-off checks are in
[PI4_CAPTURE.md](PI4_CAPTURE.md).

Choose one configuration:

- `examples/capture_synchronized_software.toml` needs no radar GPIO wire. It
  brackets `sensorStart` with Pi `CLOCK_MONOTONIC` timestamps and estimates
  later frame references using the nominal period in the decoded radar
  algorithm manifest. There is no configured-frame-count fallback.
- `examples/capture_synchronized_hardware.toml` uses GPIO18 (physical pin 12)
  to IWR1843BOOST J6-9 `SYNC_IN` plus Pi GND (physical pin 14) to J6-4. The
  normal configuration records the Pi `CLOCK_MONOTONIC` time immediately after
  each GPIO SET completes. An optional branch to GPIO24 adds kernel edge
  observations for diagnostics, but it is not required for acquisition or the
  asynchronous algorithm.

Focused Pi hardware results are recorded in
[PI4_VALIDATION_2026-08-30.md](PI4_VALIDATION_2026-08-30.md).

Hardware-trigger mode requires `frameCfg triggerSelect=2`; software mode
requires `triggerSelect=1`. A hardware edge is a radar trigger reference, not
a measured radar ADC sampling instant. It also does not frequency-lock the
ADXL355 and radar ADC clocks. Keep `hardware_validated = false` until the
powered wiring, firmware, trigger waveform, frame count, and latency have been
measured on the actual fixture.

For hardware mode, trigger count must equal `capture_frames`, frequency must
not exceed 90% of the configured radar frame rate, and both the initial delay
and inter-trigger period must stay below the conservative 5 s DCA no-LVDS
guard. The 100 Hz hardware example uses a 9 ms radar minimum period and a
10 ms GPIO trigger period, retaining that 10% timing guard. Normal completion
and SIGTERM make a best-effort attempt to leave GPIO18 low; SIGKILL cannot
provide that guarantee. Use a hardware pull-down on the real trigger net and
verify idle and pulse levels on the assembled fixture with a scope or logic
analyzer.

Run a read-only Pi preflight, then start with the software configuration:
Replace `CONFIG_UART` and `DATA_UART` with the two actual XDS110 by-id names.

```bash
uv run mmwavecapture-preflight \
  --interface eth0 --host-ip 192.168.33.30 \
  --config-serial /dev/serial/by-id/CONFIG_UART \
  --data-serial /dev/serial/by-id/DATA_UART \
  --spi-device /dev/spidev0.0 --gpiochip /dev/gpiochip0 \
  --adxl-binary native/adxl355_capture/build/adxl355_capture \
  --radar-config examples/configs/iwr1843_software_trigger.cfg \
  --capture-frames 10 --output-path example_synchronized_dataset \
  --sync-mode software_timestamp

uv run mmwavecapture-std examples/capture_synchronized_software.toml
```

For hardware mode, change preflight to `--sync-mode hardware_trigger` and add
`--trigger-binary native/frame_trigger/frame_trigger`, use the hardware-trigger
radar config, and then run
`examples/capture_synchronized_hardware.toml` only after making the extra
power-off wiring checks.

A completed synchronized directory contains `radar/`, `adxl355/`, and `sync/`.
The ADXL directory contains the fail-closed native stream plus a validated
`algorithm_input/` package. The sync directory contains the combined manifest,
`timeline.json`, and `radar_frame_monotonic_ns.npy`; hardware mode also records
the finite trigger CSV and summary.

The timeline is published only after the decoded radar algorithm manifest has
certified packet integrity. Its loader also requires the sibling combined
manifest to be complete and, when present, the capture-root `status.json` to
be complete. Optional output paths appear in the combined file map only when
their exports were requested.

```python
from mmwavecapture import load_adxl355_input, load_synchronized_timeline

run = "example_synchronized_dataset/capture_00000/synchronized"
adxl = load_adxl355_input(f"{run}/adxl355")
timeline = load_synchronized_timeline(run)
assert timeline.combined_manifest["status"] == "complete"
```

The software timeline uses the `sensorStart` bracket midpoint plus nominal
period from the decoded radar package. The hardware timeline uses GPIO18
`userspace_set_completed` references by default and optional GPIO24 loopback
edges when explicitly configured. Neither reference is labelled as radar ADC
time. DCA1000 PCAP timestamps are Ethernet receive times, never frame-start
timestamps.

At the configured 1 kHz ADXL ODR, any DRDY sequence gap, queued GPIO-event
backlog, FIFO overrun/protocol error, non-one-set pre-pop depth, or nonzero
post-pop FIFO depth fails the capture instead of silently assigning uncertain
data to a timestamp. Each accepted edge uses a `STATUS`/`FIFO_ENTRIES`/
temperature snapshot, one nine-byte `FIFO_DATA` XYZ pop, then confirmation that
`FIFO_ENTRIES` is zero; it does not compare FIFO XYZ with current-data XYZ.
Focused mock tests do not prove that a powered Pi can sustain this policy. The
coordinator supervises the ADXL child through pre-roll, trigger waiting, and
radar completion; an early ADXL exit interrupts the blocking radar/trigger
backend and fails the combined package.

Algorithm-ready and calibrated-fusion-ready packages
-----------------------------------------------------

Structural validity and scientific fusion readiness are separate. Validate a
completed directory with:

```bash
uv run mmwavecapture-fusion-check \
  example_synchronized_dataset/capture_00000/synchronized
```

The loader exposes two gates. `algorithm_ready` requires complete DCA decoding,
a loss-free non-mock ADXL stream, hardware-trigger-controlled frame references,
a lossless radar chirp cube, and full native-time coverage. It accepts either
the default GPIO SET-completion reference or an optional GPIO24 loopback edge.
`fusion_ready` is the stricter calibrated/metrology gate and additionally
requires characterized timing, validated hardware, calibrated ADXL delay, and
validated value/geometry calibration. The checker enforces `algorithm_ready`
by default; add `--require-calibrated` to enforce `fusion_ready`, or
`--allow-not-ready` to print diagnostics without a failing exit status.

Start from `examples/fusion_calibration.template.json`, replace every
placeholder with measured ADXL bias/scale/installation rotation and measured
radar range/channel/array geometry, then set `validated=true`. The template is
deliberately not accepted as fusion-ready.

```python
from mmwavecapture import load_fusion_input

capture = load_fusion_input(
    "example_synchronized_dataset/capture_00000/synchronized"
)
assert capture.algorithm_ready, capture.quality.algorithm_readiness_failures

# These remain two different native-rate CLOCK_MONOTONIC timelines. Until
# radar latency is calibrated, use the hardware-trigger reference timeline.
radar_t_ns = (
    capture.radar_adc_sample_monotonic_ns
    if capture.radar_adc_sample_monotonic_ns is not None
    else capture.radar_reference_monotonic_ns
)
adxl_t_ns = capture.adxl_sample_monotonic_ns
adxl_xyz_mps2 = capture.adxl355.acceleration_mps2
```

No nearest-neighbour timestamp pairing or acquisition-time resampling is
performed. The Phase-1 adapter integrates the chosen structural-axis ADXL
samples over each actual radar interval, so unequal rates and nonuniform radar
intervals are handled explicitly. Samples with uncovered endpoints, invalid
data, or an excessive ADXL gap are rejected rather than interpolated through
silently.

After copying a completed capture, run the algorithm independently from the
repository root. Without a calibration file it uses the selected nominal ADXL
axis and half-wavelength array geometry and records explicit warnings:

```bash
python3 -m algorithm.run \
  --input example_synchronized_dataset/capture_00000/synchronized \
  --output /tmp/algorithm_result.npz
```

The command writes `algorithm_result.npz` and a JSON provenance summary.
Use `--adxl-sign -1` when the selected sensor axis points opposite to the
positive structural-displacement direction.
Add `--require-calibrated` only when the stricter `fusion_ready` gate is needed.

Where to start?
---------------

First, set up Raspberry Pi OS, the direct hardware connections, and the
dedicated Pi-to-DCA network by following [PI4_CAPTURE.md](PI4_CAPTURE.md).

Then, read our quickstart to get familiar with how mmwave-capture-std works:
[Quickstart](https://mmwave-capture-std.readthedocs.io/en/latest/quickstart.html).

See the full documentation:
[mmwave-capture-std Documentation](https://mmwave-capture-std.readthedocs.io/en/latest/index.html)
for more information.

Algorithm input contract
------------------------

A successful radar capture publishes a versioned `algorithm_input/` package.
The acquisition program owns all DCA1000 packet ordering/integrity checks,
two-lane LVDS decoding, `Q0,Q1,I0,I1` to `I+jQ` conversion, and radar-config
reshaping. Downstream code never needs to parse PCAP, LVDS, or `radar.cfg`.

- `chirp_cube.npy` is the lossless standardized `complex64` cube with axes
  `(frame, chirp_loop, virtual_antenna, adc_sample)`.
- `adc_cube.npy` is the frame-level `complex64` cube with axes
  `(frame, virtual_antenna, adc_sample)`. By default it is the coherent mean
  over chirp loops and matches the current algorithm frontend directly.
- `frame_times_s.npy` is the nominal relative radar-frame reference axis; it is
  not a measured ADC or hardware frame-start timestamp.
- `frame_receive_times_epoch_ns.npy` records the Pi PCAP receive time of the
  packet containing each frame's first raw byte. It is transport diagnostics,
  not a radar-frame or ADC timestamp.
- `manifest.json` records the schema version, exact axes, radar dimensions,
  TX/RX mapping, timing, transform, and DCA packet-integrity result.

Read the stable package through the provided reader:

```python
from mmwavecapture import load_algorithm_input

capture = load_algorithm_input("example_dataset/capture_00000/iwr1843")
print(capture.adc_cube.shape)
print(capture.frame_times_s)
```

To convert an older capture that already contains `dca.pcap` and `radar.cfg`:

```bash
uv run mmwavecapture-export example_dataset/capture_00000/iwr1843
```

The export fails closed on packet loss, byte-counter gaps, sequence gaps,
unsupported ADC layouts, or a sample count that disagrees with `radar.cfg`.
Set `export_algorithm_data = false` only when intentionally recording raw PCAP
without publishing algorithm-ready data.

Acquisition reliability notes
-----------------------------

This checkout keeps hardware-specific adaptation at the acquisition boundary.
The default install does not require the optional legacy `disspcap` extension;
the stable exporter is implemented in the core package.

The acquisition lifecycle has additional failure cleanup and mock coverage for
DCA command packets, radar UART commands, tcpdump startup, finite-capture
timeouts, asynchronous DCA1000 status packets, and interrupted sensor startup.
Each attempt writes `config.toml` and `status.json` before hardware access; a
failed capture therefore retains its configuration, phase, and error message.
Before using the hardware, run `mmwavecapture-preflight` locally on the Pi and
do not capture until every prerequisite reports `PASS`.

Links
-----

* Homepage: <https://www.cs.unc.edu/~louielu/p/mmwave-capture-std/>
* Documentation: [mmwave-capture-std Documentation](https://mmwave-capture-std.readthedocs.io/en/latest/)
* Source Code: [mmwave-capture-std/mmwave-capture-std](https://github.com/mmwave-capture-std/mmwave-capture-std/)
* License: [BSD 3-Clause Clear License](https://github.com/mmwave-capture-std/mmwave-capture-std/blob/main/LICENSE)

Contribute
----------

Use the following snippet to setup your development environment:

```bash
git clone <repo-url>
cd mmwave-capture-std
uv sync # Prepare env and install deps
uv run pre-commit install # Install pre-commit hooks
```

Related Publications
--------------------

* mmCounter: Static People Counting in Dense Indoor Scenarios using mmWave Radar
  - Tarik Reza Toha, Shao-Jung (Louie) Lu, and Shahriar Nirjon
  - The 22nd International Conference on Embedded Wireless Systems and Networks (EWSN '25)

* mmDefender: A mmWave System for On-Body Localization of Concealed Threats in Moving Persons
  - Shao-Jung (Louie) Lu, Mahathir Monjur, Sirajum Munir, and Shahriar Nirjon
  - The 22nd International Conference on Embedded Wireless Systems and Networks (EWSN '25)

LICENSE
-------

```text
The Clear BSD License

Copyright (c) 2023 Louie Lu <louielu@cs.unc.edu>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted (subject to the limitations in the disclaimer
below) provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holder nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
```
