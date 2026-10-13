Setup
=====

Supported deployment
--------------------

The Raspberry Pi 4 is the only acquisition host for this project. The operator
computer only sends commands to the Pi over Wi-Fi/SSH. It is not connected to
the radar USB interface or the DCA1000EVM capture Ethernet interface.

::

   operator computer --Wi-Fi / SSH--> Raspberry Pi 4
                                         |--SPI + DRDY--> ADXL355
                                         |--USB---------> IWR1843BOOST
                                         |--GPIO18------> IWR1843BOOST SYNC_IN
                                         |       `------> GPIO24 loopback input (optional)
                                         |--GND---------> IWR1843BOOST GND
                                         |  (hardware-trigger mode only)
                                         `--Ethernet----> DCA1000EVM

   IWR1843BOOST <--------60-pin HD connector--------> DCA1000EVM

Live data, UART control, DCA packet recording, ADXL355 acquisition, and all
initial files are handled on Pi-local storage. The operator computer may copy a
completed capture after acquisition has stopped; it remains outside the live
data path.

The Python package and native mock modes can be tested on other systems, but
physical deployment is defined for Raspberry Pi 4 running 64-bit Raspberry Pi
OS.

.. warning::

   The current code and focused tests do not prove powered hardware timing.
   Keep ``hardware_validated = false`` until the actual Pi, firmware, J6
   routing, voltage levels, trigger waveform, frame count, and latency have
   passed recorded bench measurements.

Physical connections
--------------------

Make and check every connection while all boards are powered off:

#. Join IWR1843BOOST and DCA1000EVM through the 60-pin HD connector.
#. Connect IWR1843BOOST XDS110 USB directly to the Pi. It provides the radar
   configuration and data UARTs.
#. Connect DCA1000EVM Ethernet directly to the Pi wired interface, normally
   ``eth0``.
#. Keep the Pi connected to the normal LAN over Wi-Fi for SSH control.
#. Connect ADXL355 directly to the Pi SPI/GPIO header.
#. Use each radar board's specified external power supply. Do not power radar
   hardware from Pi GPIO.

ADXL355 SPI and DRDY
````````````````````

The synchronized examples use SPI0 CE0 and BCM GPIO25. BCM line offsets are
not Raspberry Pi physical header pin numbers.

.. list-table:: ADXL355 PMDZ to Raspberry Pi 4
   :header-rows: 1

   * - ADXL355 pin
     - Signal
     - Pi physical pin
     - BCM line
   * - P1-6
     - VDD, 3.3 V
     - 1
     - --
   * - P1-5
     - DGND
     - 6
     - --
   * - P1-2
     - MOSI
     - 19
     - GPIO10
   * - P1-3
     - MISO
     - 21
     - GPIO9
   * - P1-4
     - SCLK
     - 23
     - GPIO11
   * - P1-1
     - CS
     - 24
     - GPIO8 / CE0
   * - P1-10
     - DRDY
     - 22
     - GPIO25

Use only 3.3 V. Confirm the actual ADXL board's P1 numbering and continuity;
do not infer signals from wire colour.

Radar synchronization modes
```````````````````````````

``software_timestamp`` needs no GPIO connection between the Pi and radar. Its
radar configuration must contain ``frameCfg triggerSelect=1``. The coordinator
records Pi ``CLOCK_MONOTONIC`` values immediately before and after
``sensorStart`` returns, then uses their midpoint plus the nominal frame period
from the decoded radar algorithm manifest as a reference timeline. It never
falls back to a configured frame count.

``hardware_trigger`` requires ``frameCfg triggerSelect=2`` and adds:

.. list-table:: Hardware-trigger wiring
   :header-rows: 1

   * - Purpose
     - Raspberry Pi 4
     - IWR1843BOOST
   * - Frame trigger
     - physical pin 12 / GPIO18 output
     - J6-9 ``SYNC_IN``
   * - Common ground
     - physical pin 14 / GND
     - J6-4 GND
   * - Optional kernel edge observation
     - branch GPIO18 to physical pin 18 / GPIO24 input
     - no additional radar pin

The normal hardware-trigger connection has two conductors: GPIO18 (physical
pin 12) to ``SYNC_IN`` and GND (physical pin 14) to radar GND. The supplied
hardware TOML sets ``use_loopback = false``. Its ``userspace_set_completed``
references are valid for the operational ``algorithm_ready`` gate.

GPIO24 is an optional branch of the same GPIO18 electrical net. With
``use_loopback = true`` and ``loopback_line = 24``, Linux records a kernel
rising-edge timestamp. This is a useful timing diagnostic, not a second radar
signal and not an ADC frequency lock. Do not enable GPIO24 while leaving it
floating.

Trigger count must equal ``capture_frames``. Frequency is capped at 90% of the
configured radar frame rate and defaults to that value when omitted. Both the
initial delay and inter-trigger period must stay below 5 seconds, providing a
conservative guard against DCA1000's roughly 10-second no-LVDS timeout.

J6 is a 2x10 mother connector and can be obstructed by DCA1000EVM. Verify any
passive right-angle adapter for mirrored numbering with a continuity meter.
Never connect the J6 3.3 V or 5 V pins to Pi GPIO, and keep GPIO18 low until an
intentional trigger run. Normal exit and SIGTERM only make a best-effort attempt
to return GPIO18 low; SIGKILL cannot run cleanup. Use a hardware pull-down on
the real trigger net and verify idle level and waveform on the assembled fixture
with a scope or logic analyzer.

Neither mode measures the radar ADC sampling instant. Hardware mode records a
kernel-observed loopback edge when the optional branch is present; otherwise
it records a ``userspace_set_completed`` reference. Both can pass the
operational ``algorithm_ready`` gate. The stricter ``fusion_ready`` gate
requires characterized uncertainty and calibrated radar-to-ADC/ADXL delays.
Neither connection shares or frequency-locks the ADXL355 and radar ADC clocks.
DCA1000 PCAP timestamps are Ethernet packet receive times, not radar
frame-start times.

Hardware references
-------------------

IWR1843BOOST
````````````

- Firmware target: out-of-box demo SDK 3.6.0
- `MMWAVE SDK User Guide Product Release 3.6 LTS <https://dr-download.ti.com/software-development/software-development-kit-sdk/MD-PIrUeCYr3X/03.06.00.00-LTS/mmwave_sdk_user_guide.pdf>`_

DCA1000EVM
``````````

- FPGA firmware target: 2.8
- `DCA1000EVM Quick Start Guide <https://www.ti.com/lit/ml/spruik7/spruik7.pdf>`_
- `DCA1000EVM User's Guide <https://www.ti.com/lit/ug/spruij4a/spruij4a.pdf>`_

Raspberry Pi OS and Linux GPIO uAPI v2
--------------------------------------

Install the compiler, Linux UAPI headers, and capture tools on the Pi:

.. code-block:: bash

   sudo apt update
   sudo apt install -y \
     git tcpdump libcap2-bin build-essential linux-libc-dev

The native ADXL and frame-trigger programs use the Linux GPIO
character-device uAPI v2 directly through ``linux/gpio.h``. They do not link to
``libgpiod`` and do not require ``pkg-config``. A normal hardware build fails
clearly if the installed Linux UAPI headers do not expose v2.

Enable SPI through ``raspi-config`` (``Interface Options`` -> ``SPI``), reboot
if requested, and verify the devices:

.. code-block:: bash

   ls -l /dev/spidev0.0 /dev/gpiochip0

Install `uv <https://docs.astral.sh/uv/getting-started/installation/>`_, then
install the Python project and build both native programs:

.. code-block:: bash

   cd ~/thesis/capture_program
   uv sync
   make -C native/adxl355_capture
   make -C native/adxl355_capture print-hw
   make -C native/frame_trigger

``print-hw`` must report ``ADXL355 Linux hardware support: 1``. The executable
paths used by the examples are:

::

   native/adxl355_capture/build/adxl355_capture
   native/frame_trigger/frame_trigger

The following are focused native mock/format tests, not real-hardware tests:

.. code-block:: bash

   make -C native/adxl355_capture test
   make -C native/frame_trigger test

Give the SSH user access to the device groups present on the Pi, then log out
and reconnect:

.. code-block:: bash

   sudo usermod -aG dialout,spi,gpio "$(id -un)"

Radar UART access
-----------------

Confirm that both IWR1843BOOST XDS110 interfaces are visible on the Pi:

.. code-block:: bash

   lsusb
   ls -l /dev/ttyACM*
   ls -l /dev/serial/by-id/ 2>/dev/null || true

The examples use ``/dev/ttyACM0`` for configuration and ``/dev/ttyACM1`` for
data. Confirm the real order; prefer stable ``/dev/serial/by-id/...`` paths
when possible.

DCA1000EVM network setup
------------------------

The Pi uses ``wlan0`` for normal-LAN SSH and ``eth0`` for its direct DCA link.
The example addresses are Pi ``192.168.33.30/24`` and DCA1000EVM
``192.168.33.180``. The wired interface must not install a default gateway.

.. code-block:: bash

   ip -br link
   sudo ip link set eth0 up
   sudo ip address replace 192.168.33.30/24 dev eth0
   ip -br address show dev eth0
   ip route

Grant the Pi-local ``tcpdump`` process only its packet-capture capabilities:

.. code-block:: bash

   sudo setcap cap_net_raw,cap_net_admin=eip "$(command -v tcpdump)"
   getcap "$(command -v tcpdump)"

Read-only preflight
-------------------

Run software timestamp preflight first:

.. code-block:: bash

   uv run mmwavecapture-preflight \
     --interface eth0 \
     --host-ip 192.168.33.30 \
     --config-serial /dev/ttyACM0 \
     --data-serial /dev/ttyACM1 \
     --spi-device /dev/spidev0.0 \
     --gpiochip /dev/gpiochip0 \
     --adxl-binary native/adxl355_capture/build/adxl355_capture \
     --sync-mode software_timestamp

For hardware-trigger mode, use ``--sync-mode hardware_trigger`` and add:

.. code-block:: bash

   --trigger-binary native/frame_trigger/frame_trigger

Every check must report ``PASS``. Preflight checks local paths, permissions,
executables, the Pi Ethernet address, and UDP bind availability without sending
hardware commands. It cannot verify sensor identity, wiring continuity, GPIO
line selection, firmware support, or the physical trigger waveform.

Storage and fail-closed acquisition
-----------------------------------

The DCA stream and all derived files are written on the Pi. Begin with ten
frames and use fast Pi-local storage. A DCA sequence/byte gap prevents radar
algorithm input from being published.

At 1 kHz, ADXL355 accepts a sample only when there is one contiguous DRDY edge,
exactly one queued GPIO event, exactly one complete FIFO XYZ set, no overrun,
valid FIFO markers, and an empty FIFO after the pop. It first snapshots
``STATUS``, ``FIFO_ENTRIES``, and temperature, pops exactly nine bytes from
``FIFO_DATA``, then confirms ``FIFO_ENTRIES=0``. It does not compare FIFO XYZ
with current-data XYZ. ``fifo_xyz_mismatches`` remains in the summary only for
schema compatibility and stays zero. A line gap, scheduler backlog, FIFO
protocol error, nonzero post-pop depth, I/O failure, or zero-sample run marks
the capture failed and retains only diagnostic partial evidence. This
conservative policy must be tested under real Pi load.

After pre-roll, the coordinator checks that the ADXL process still runs before
preparing DCA/tcpdump and again immediately before ``sensorStart``. It also
supervises the ADXL child while waiting for the trigger helper and radar
completion; an early exit interrupts the active wait and fails the package.

The synchronized timeline is published only from a complete decoded radar
algorithm manifest. Its loader also requires the sibling combined manifest and,
when present, capture-root ``status.json`` to be complete and mutually
consistent. PCAP timestamps remain Ethernet receive times, never frame-start
timestamps.

The ADXL digital-filter group delay is currently uncalibrated. A stored zero
means unknown, not zero physical latency.

For the complete run procedure and output tree, see the repository-level
``PI4_CAPTURE.md`` and :doc:`Quickstart <quickstart>`.
