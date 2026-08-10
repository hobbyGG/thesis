# IWR1843 + DCA1000 capture under WSL 2

This program only records raw DCA1000 network traffic and the configuration
needed to interpret it later. Signal processing is deliberately outside this
repository.

## 1. Prepare WSL

Use an up-to-date WSL 2 Ubuntu installation. On Windows 11 22H2 or newer,
mirrored networking usually gives the DCA Ethernet path the best chance of
being visible inside WSL. Add this to `%UserProfile%\\.wslconfig` if needed:

```ini
[wsl2]
networkingMode=mirrored
```

Then run `wsl --shutdown` in PowerShell and start Ubuntu again.

Reference: [Microsoft WSL networking documentation](https://learn.microsoft.com/windows/wsl/networking).

Install the Linux tools:

```bash
sudo apt update
sudo apt install -y git tcpdump libcap2-bin
```

Install `uv` by following its official installation instructions, then clone
or copy this repository into the WSL Linux filesystem rather than running it
from `/mnt/c`.

```bash
cd ~/iwr1843-capture
uv sync
uv run pytest -q
```

The expected software-only result is currently `13 passed`; hardware and
optional parser/RealSense tests are skipped by default.

## 2. Attach the radar USB UARTs

WSL does not automatically expose every USB device. Use `usbipd-win` from
PowerShell to attach the IWR1843/XDS110 USB device to WSL. The current Microsoft
workflow is:

```powershell
usbipd list
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

`bind` requires an administrator PowerShell. In Ubuntu, verify the result:

```bash
lsusb
ls -l /dev/ttyACM*
```

Reference: [Microsoft WSL USB attachment documentation](https://learn.microsoft.com/windows/wsl/connect-usb).

If normal-user serial access is denied, add the user to `dialout`, then log out
of WSL and back in:

```bash
sudo usermod -aG dialout "$(id -un)"
```

## 3. Expose and configure the DCA Ethernet interface

Find the interface that is physically connected to DCA1000:

```bash
ip -br link
ip -br address
```

The interface must be visible inside WSL and have the host address
`192.168.33.30/24`. Replace `eth1` below with the actual interface:

```bash
sudo ip address add 192.168.33.30/24 dev eth1
sudo ip link set eth1 up
```

If the physical DCA interface never appears inside WSL, the capture code cannot
fix that virtualization boundary. Use a USB Ethernet adapter attached directly
to WSL or boot native Linux.

Allow the unprivileged tcpdump process launched by Python to capture packets:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip "$(command -v tcpdump)"
getcap "$(command -v tcpdump)"
```

## 4. Run the read-only preflight

The preflight does not send commands to either board. It checks Linux,
tcpdump, the interface address, both UART paths, and whether UDP ports 4096 and
4098 can be bound:

```bash
uv run mmwavecapture-preflight \
  --interface eth1 \
  --config-serial /dev/ttyACM0 \
  --data-serial /dev/ttyACM1
```

Do not start a capture until every line reports `PASS`.

## 5. Record a short fixture

Edit `examples/capture_iwr1843.toml`:

- set `dca_eth_interface` to the preflight interface;
- set both radar serial paths;
- point `radar_config_filename` at the desired xWR18xx configuration;
- begin with `capture_frames = 10`.

Then run:

```bash
uv run mmwavecapture-std examples/capture_iwr1843.toml
```

Successful output contains:

```text
example_dataset/capture_00000/
├── capture.log
├── config.toml
└── iwr1843/
    ├── dca.json
    ├── dca.pcap
    └── radar.cfg
```

Confirm that data packets exist before moving the dataset to the offline
algorithm machine:

```bash
test -s example_dataset/capture_00000/iwr1843/dca.pcap
tcpdump -nn -r example_dataset/capture_00000/iwr1843/dca.pcap 'udp port 4098' -c 5
```

## What the Mac tests do not prove

The mock suite verifies command encoding, serial command flow, subprocess
ordering, timeout handling, and cleanup. Only the WSL fixture above can verify:

- USB/UART passthrough;
- visibility of the physical DCA Ethernet interface;
- tcpdump permissions;
- real sustained packet loss at the selected radar configuration.
