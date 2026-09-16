# ADXL355 native capture

`adxl355_capture` is a C11 collector for Raspberry Pi/Linux. It timestamps each
ADXL355 DRDY rising edge using the `CLOCK_MONOTONIC` timestamp attached by the
Linux GPIO character-device subsystem. It snapshots `STATUS` (`0x04`),
`FIFO_ENTRIES` (`0x05`), and `TEMP2/TEMP1` (`0x06`/`0x07`), reads exactly nine
bytes from `FIFO_DATA` (`0x11`) for one XYZ set, then reads `FIFO_ENTRIES` again
and requires zero. The recorded XYZ value comes only from the FIFO transaction;
the collector does not read or compare the newest-data XYZ registers. A
deterministic `--mock` mode builds and runs without hardware on macOS and Linux.

## Build and focused tests

```sh
cd capture_program/native/adxl355_capture
make
make print-hw
make test
```

The real hardware path uses the Linux GPIO character-device **uAPI v2**
directly. It does not link to libgpiod, so Ubuntu 24.04's libgpiod 1.6 package
does not block the build. The kernel v2 event ABI supplies both the
`CLOCK_MONOTONIC` timestamp and `line_seqno` required by the fail-closed gap
check. A normal Linux build fails immediately if `linux/gpio.h` does not expose
that ABI. Use `make MOCK_ONLY=1` only when a mock-only Linux build is
intentional. macOS builds are always mock-only. Running any mock-only binary
without `--mock` exits with a clear error and writes a failed summary.

There is deliberately no GPIO uAPI v1/libgpiod 1.x fallback. Its edge-event
record has a timestamp but no kernel line sequence number, so it cannot provide
equivalent overflow/gap evidence. Synthesizing a sequence from the number of
events read would hide lost kernel events. The collector instead fails at
build time when v2 headers are absent, or with an explicit error if the running
kernel/device rejects `GPIO_V2_GET_LINE_IOCTL`.

On the Pi running Ubuntu 24.04:

```sh
sudo apt update
sudo apt install --yes build-essential linux-libc-dev
cd capture_program/native/adxl355_capture
make
make print-hw
./build/adxl355_capture --capabilities
```

The last command must report all of:

```json
{"hardware_support":true,"gpio_backend":"linux-gpio-uapi-v2","gpio_event_clock":"CLOCK_MONOTONIC","line_sequence_source":"kernel_line_seqno","line_sequence_certified":true}
```

The capability object contains additional fields; the fragment above lists the
ones that must match. Header availability is checked at build time. Actual
kernel/device support is checked when the GPIO line is requested.

`./build/adxl355_capture --capabilities` prints a one-line JSON object. Pi
preflight requires `hardware_support` to be `true`; executable presence alone
is not sufficient.

## CLI

```sh
./build/adxl355_capture \
  --output /data/run.partial/adxl355.raw \
  --summary /data/run.partial/adxl355-summary.json \
  --ready-file /data/run.partial/adxl355-ready.json \
  --spi-device /dev/spidev0.0 \
  --gpiochip /dev/gpiochip0 \
  --drdy-line 25 \
  --odr-hz 1000 \
  --range-g 2 \
  --spi-hz 5000000 \
  --max-samples 60000
```

Defaults are `/dev/spidev0.0`, `/dev/gpiochip0`, GPIO line 25, 1 kHz,
plus/minus 2 g, and 5 MHz SPI. Supported integer ODRs are 125, 250, 500,
1000, 2000, and 4000 Hz. Omit `--max-samples` for a continuous run stopped by
SIGINT or SIGTERM. If a finite run is interrupted before its target, its
summary is `failed`.

Digital-filter delay defaults to exactly `0`, `group_delay_calibrated=false`,
and a null calibration source. A positive delay is accepted only when
`--group-delay-calibrated` and a non-whitespace `--group-delay-source` are also
provided. Conversely, the calibration flag requires a delay greater than zero
and a source. Invalid combinations fail during argument validation, before SPI
or GPIO is opened. Raw format v1 stores the delay value in its header; a
positive value is therefore only emitted for a validated calibration triple.
The ready metadata, summary, and summary config additionally carry the explicit
flag and source. The collector never supplies a default calibration value; the
delay must not be guessed. After a bench calibration for the selected
ODR/filter settings, append these arguments using the measured integer and a
traceable artifact identifier:

```text
--group-delay-ns <MEASURED_NS> \
--group-delay-calibrated \
--group-delay-source <CALIBRATION_ARTIFACT_ID>
```

The real path first checks identity (`AD`, `1D`, `ED`) and saves NVM shadow
registers `0x50` through `0x54`. It then resets (`0x52`), waits for `NVM_BUSY`
to clear, verifies that the shadow bytes are unchanged, and configures standby,
range, FILTER with HPF disabled, and internal SYNC. Every configuration value is
read back and the FIFO must be empty before measurement mode starts. This follows
the data-sheet workaround for early mask revisions instead of trusting a software
reset silently. DRDY is inherently active high on this part; the configured
`INT_POL` range bit only affects mapped INT1/INT2 signals. Shutdown attempts to
return the sensor to standby.

## FIFO and timestamp pairing policy

The ADXL355 FIFO has 96 **axis locations**, so one complete XYZ sample occupies
three FIFO entries and the maximum depth is 32 XYZ samples. The device's
`XDATA` through `ZDATA` registers expose the newest sample, while a read from
`FIFO_DATA` pops the oldest unread axis values. The collector deliberately uses
only FIFO XYZ for accepted samples; newest-data XYZ is neither read nor used as
a comparison source.

This collector deliberately uses a fail-closed one-to-one policy:

1. The first kernel GPIO v2 `line_seqno` must be 1 and every later sequence
   must increment by exactly one.
2. A GPIO uAPI v2 dequeue must contain exactly one DRDY event. A batch of two or
   more historical events is treated as scheduler backlog and fails the run
   before any of those events is assigned data.
3. A `STATUS`/`FIFO_ENTRIES`/temperature snapshot must report exactly three FIFO
   entries and no `FIFO_OVR`. Zero entries, a partial set, or more than one XYZ
   set fails the run.
4. Exactly nine bytes are read from `FIFO_DATA`, popping X, Y, and Z. The FIFO
   empty indicators, X marker sequence, and virtual bits are validated.
5. `FIFO_ENTRIES` is read again and must be zero. A newly queued axis entry or
   XYZ set before this confirmation makes the timestamp/sample pairing
   ambiguous and fails the run.
6. Only after all checks pass is one record written with that DRDY edge time.

Consequently, this version drains one FIFO XYZ set per accepted DRDY and never
silently reconstructs timestamps after backlog. A failed summary makes all
already-written records a diagnostic partial capture, not a valid experiment.
This trades recoverability for unambiguous timestamp semantics. `temp_raw` and
`status` are service-time register snapshots; temperature is not double
buffered by the sensor and must not be interpreted as a separately timed FIFO
measurement. `spi_complete_monotonic_ns` is taken after the FIFO transaction.

The policy follows the [ADXL354/ADXL355 Rev. D data sheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adxl354_adxl355.pdf),
especially its FIFO organization, DRDY, and FIFO_DATA sections. Analog Devices'
[no-OS ADXL355 driver](https://github.com/analogdevicesinc/no-OS/tree/main/drivers/accel/adxl355)
independently demonstrates reading FIFO entries in multiples of three axis
locations and checking the X marker.

## Binary format

All integers are explicitly encoded little-endian; C struct layout is never
written directly.

The 64-byte header is:

| Offset | Type | Meaning |
| ---: | --- | --- |
| 0 | 8 bytes | `ADXLRW01` |
| 8 | u16 | version = 1 |
| 10 | u16 | header bytes = 64 |
| 12 | u16 | record bytes = 48 |
| 14 | u16 | flags (bit 0 = mock) |
| 16 | u32 | ODR in millihertz |
| 20 | u16 | range in g |
| 22 | u16 | reserved |
| 24 | u64 | start `CLOCK_REALTIME` ns |
| 32 | u64 | start `CLOCK_MONOTONIC` ns |
| 40 | i64 | explicitly configured group delay ns; zero means uncalibrated |
| 48 | 16 bytes | reserved |

Each 48-byte record is:

| Offset | Type | Meaning |
| ---: | --- | --- |
| 0 | u64 | sample sequence |
| 8 | u64 | kernel GPIO line sequence |
| 16 | u64 | DRDY `CLOCK_MONOTONIC` edge ns |
| 24 | u64 | SPI completion `CLOCK_MONOTONIC` ns |
| 32/36/40 | i32 | signed 20-bit X/Y/Z raw values |
| 44 | i16 | service-time raw 12-bit temperature snapshot |
| 46 | u8 | pre-pop STATUS snapshot |
| 47 | u8 | pre-pop FIFO_ENTRIES snapshot (3 for valid real records) |

The ready and summary files are written using fsync plus atomic rename. The raw
file is flushed and fsynced on normal completion and handled SIGINT/SIGTERM.
The ready marker means the SPI sensor configuration and GPIO edge request are
armed; measurement mode is entered immediately after publishing that marker.
This ordering prevents metadata fsync latency from accumulating unread startup
DRDY events. A failed run removes its ready marker and writes a failed summary.
The summary preserves raw DRDY timestamp semantics and records the group-delay
value, explicit calibration flag, and provenance source. It also records
`gpio_backend`, `line_sequence_source`, and `line_sequence_certified`; a real
hardware capture built with this backend reports `linux-gpio-uapi-v2`,
`kernel_line_seqno`, and `true`. Mock data reports synthetic provenance and is
never sequence-certified. The summary exposes both `samples` and
`samples_written` with the same count so the coordinator contract and raw
collector diagnostics remain explicit. FIFO integrity diagnostics include
`gpio_backlog_events`, `fifo_protocol_errors`, `fifo_xyz_mismatches`,
`fifo_xyz_sets_drained`, and `max_fifo_entries`; a complete real capture also
declares `sample_source` as `FIFO_DATA_oldest` and `timestamp_pairing` as
`one_drdy_edge_to_one_fifo_xyz`. `fifo_xyz_mismatches` is retained only for
summary-schema compatibility; this implementation does not compare FIFO XYZ
with current-data XYZ and leaves the counter at zero.

## Hardware validation still required

The mock tests verify byte layout, status/FIFO/temperature snapshot and FIFO
decoding, FIFO marker and post-pop empty detection, fail-closed pairing
decisions, CLI lifecycle, atomic metadata, and incomplete-run failure behavior.
They do not validate physical SPI signal integrity, real FIFO pointer behavior,
whether the Pi scheduler can service every 1 kHz DRDY without ever batching
events, ADXL355 filter group delay, or sustained filesystem latency. Those
items require focused bench tests on the powered Pi before use in an experiment.
If real tests show occasional event batching, do not relax this check without
introducing a new record schema that can honestly represent reconstructed FIFO
timestamps and ancillary-value timing.

The GPIO v2 ABI and its timing/sequence semantics are documented by the Linux
kernel in [GPIO Character Device Userspace API](https://www.kernel.org/doc/html/latest/userspace-api/gpio/chardev.html)
and [GPIO_V2_LINE_EVENT_READ](https://www.kernel.org/doc/html/latest/userspace-api/gpio/gpio-v2-line-event-read.html).
The v2 ABI was added in Linux 5.10; Raspberry Pi Ubuntu 24.04 kernels are new
enough, but the runtime request remains the authoritative check.
