"""Read-only Pi-local checks for IWR1843BOOST + DCA1000EVM capture."""

from __future__ import annotations

import ipaddress
import json
import math
import os
import pathlib
import platform
import shutil
import socket
import subprocess
from dataclasses import dataclass
from typing import Iterable, Optional

import click
import netifaces


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class DcaDataEstimate:
    """Raw complex ADC payload implied by one finite radar capture."""

    frames: int
    chirps_per_frame: int
    rx_channels: int
    adc_samples: int
    bytes_per_adc_sample: int
    raw_bytes: int


SERIAL_BY_ID_DIRECTORY = pathlib.Path("/dev/serial/by-id")
DEFAULT_DCA_IP = "192.168.33.180"
DEFAULT_DISK_SAFETY_FACTOR = 3.0
DEFAULT_DISK_RESERVE_BYTES = 1 << 30


def _is_stable_serial_path(path: str) -> bool:
    """Return whether *path* names a persistent udev by-id entry."""

    candidate = pathlib.Path(os.path.abspath(os.path.expanduser(path)))
    try:
        relative = candidate.relative_to(SERIAL_BY_ID_DIRECTORY)
    except ValueError:
        return False
    return bool(relative.parts)


def _serial_check(
    path: str,
    label: str,
    allow_unstable_serial: bool = False,
) -> Check:
    device = pathlib.Path(path)
    if not device.exists():
        return Check(label, False, f"{path} does not exist")
    if not os.access(device, os.R_OK | os.W_OK):
        return Check(label, False, f"{path} is not readable and writable")
    if not _is_stable_serial_path(path):
        if not allow_unstable_serial:
            return Check(
                label,
                False,
                f"{path} is an unstable serial path; use "
                "/dev/serial/by-id/... or explicitly enable "
                "allow_unstable_serial for diagnostics",
            )
        return Check(
            label,
            True,
            f"{path} (unstable serial ordering explicitly allowed for diagnostics)",
        )
    return Check(label, True, f"{path} (stable by-id path)")


def _device_check(path: str, label: str) -> Check:
    device = pathlib.Path(path)
    if not device.exists():
        return Check(label, False, f"{path} does not exist")
    if not os.access(device, os.R_OK | os.W_OK):
        return Check(label, False, f"{path} is not readable and writable")
    return Check(label, True, path)


def _executable_check(path: str, label: str) -> Check:
    resolved = shutil.which(path)
    if resolved is None and os.sep in path:
        candidate = pathlib.Path(path)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            resolved = str(candidate)
    return Check(label, resolved is not None, resolved or f"{path} is not executable")


def _adxl_binary_check(path: str) -> Check:
    label = "ADXL355 collector"
    executable = _executable_check(path, label)
    if not executable.ok:
        return executable
    try:
        result = subprocess.run(
            [executable.detail, "--capabilities"],
            capture_output=True,
            check=False,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return Check(label, False, f"cannot query {executable.detail}: {exc}")
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        return Check(label, False, f"capability query failed: {detail}")
    try:
        capabilities = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        return Check(label, False, f"invalid --capabilities JSON: {exc}")
    if not isinstance(capabilities, dict):
        return Check(label, False, "--capabilities did not return a JSON object")
    if capabilities.get("schema_version") != 1:
        return Check(label, False, "unsupported ADXL355 capability schema")
    if capabilities.get("hardware_support") is not True:
        return Check(
            label,
            False,
            f"{executable.detail} is a mock-only build (hardware_support=false)",
        )
    return Check(label, True, f"{executable.detail} (hardware_support=true)")


def _udp_bind_check(host_ip: str, ports: Iterable[int]) -> Check:
    sockets = []
    try:
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sockets.append(sock)
            sock.bind((host_ip, port))
    except OSError as exc:
        return Check("DCA UDP bind", False, str(exc))
    finally:
        for sock in sockets:
            sock.close()
    return Check("DCA UDP bind", True, f"{host_ip} ports {', '.join(map(str, ports))}")


def _network_configuration_check(
    interface: str,
    host_ip: str,
    dca_ip: str,
    addresses: Iterable[dict],
) -> Check:
    """Report and validate the configured direct Pi-to-DCA IPv4 link."""

    label = "DCA network configuration"
    try:
        host = ipaddress.IPv4Address(host_ip)
        target = ipaddress.IPv4Address(dca_ip)
    except ipaddress.AddressValueError as exc:
        return Check(
            label,
            False,
            f"interface={interface} host={host_ip} target={dca_ip}: {exc}",
        )
    if host == target:
        return Check(
            label,
            False,
            f"interface={interface} host={host} target={target}: addresses collide",
        )

    matching = [item for item in addresses if item.get("addr") == host_ip]
    if len(matching) != 1:
        return Check(
            label,
            False,
            f"interface={interface} host={host} target={target}: "
            "host address is not uniquely configured on the interface",
        )
    netmask = matching[0].get("netmask")
    if not netmask:
        return Check(
            label,
            False,
            f"interface={interface} host={host} target={target}: "
            "interface netmask is unavailable",
        )
    try:
        network = ipaddress.IPv4Network((host_ip, netmask), strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as exc:
        return Check(
            label,
            False,
            f"interface={interface} host={host}/{netmask} target={target}: {exc}",
        )
    if target not in network or target in (
        network.network_address,
        network.broadcast_address,
    ):
        return Check(
            label,
            False,
            f"interface={interface} host={host}/{network.prefixlen} target={target}: "
            f"target is not a usable address in {network}",
        )
    return Check(
        label,
        True,
        f"interface={interface} host={host}/{network.prefixlen} "
        f"target={target} subnet={network}",
    )


def _single_radar_command(
    commands: dict,
    name: str,
    minimum_arguments: int,
) -> list[str]:
    matches = commands.get(name, [])
    if len(matches) != 1:
        raise ValueError(
            f"radar config must contain exactly one `{name}` command"
        )
    arguments = matches[0]
    if len(arguments) < minimum_arguments:
        raise ValueError(f"radar config `{name}` command is incomplete")
    return arguments


def estimate_dca_raw_data(
    radar_config: str,
    capture_frames: Optional[int] = None,
) -> DcaDataEstimate:
    """Estimate raw DCA payload bytes without opening either hardware device.

    The supported capture/export contract is 16-bit complex ADC output, so
    every enabled-RX ADC sample contributes one 16-bit I and one 16-bit Q value.
    ``capture_frames`` mirrors the finite frame override used by ``RadarDCA``;
    when omitted, the finite ``frameCfg`` value is used.
    """

    path = pathlib.Path(radar_config)
    commands = {}
    try:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                stripped = line.strip()
                if not stripped or stripped.startswith("%"):
                    continue
                fields = stripped.split()
                commands.setdefault(fields[0], []).append(fields[1:])
    except OSError as exc:
        raise ValueError(f"cannot read radar config {path}: {exc}") from exc

    frame_cfg = _single_radar_command(commands, "frameCfg", 5)
    channel_cfg = _single_radar_command(commands, "channelCfg", 2)
    profile_cfg = _single_radar_command(commands, "profileCfg", 10)
    adc_cfg = _single_radar_command(commands, "adcCfg", 2)
    try:
        chirp_start = int(frame_cfg[0])
        chirp_end = int(frame_cfg[1])
        loops = int(frame_cfg[2])
        configured_frames = int(frame_cfg[3])
        rx_mask = int(channel_cfg[0], 0)
        adc_samples = int(profile_cfg[9])
        adc_bits_code = int(adc_cfg[0])
        adc_output_format = int(adc_cfg[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"radar config contains a non-integer layout field: {exc}"
        ) from exc

    frames = configured_frames if capture_frames is None else capture_frames
    if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
        raise ValueError(
            "a positive finite capture_frames value is required for storage estimation"
        )
    if chirp_start < 0 or chirp_end < chirp_start or loops <= 0:
        raise ValueError("radar frameCfg has an invalid chirp range or loop count")
    rx_channels = (
        rx_mask.bit_count()
        if hasattr(int, "bit_count")
        else bin(rx_mask).count("1")
    )
    if rx_mask <= 0 or rx_channels <= 0:
        raise ValueError("radar channelCfg enables no RX channels")
    if adc_samples <= 0:
        raise ValueError("radar profileCfg has no positive ADC sample count")
    if adc_bits_code != 2 or adc_output_format != 1:
        raise ValueError(
            "storage estimation requires adcCfg 2 1 (16-bit complex ADC output)"
        )

    chirps_per_frame = (chirp_end - chirp_start + 1) * loops
    bytes_per_adc_sample = 4
    raw_bytes = (
        frames
        * chirps_per_frame
        * rx_channels
        * adc_samples
        * bytes_per_adc_sample
    )
    return DcaDataEstimate(
        frames=frames,
        chirps_per_frame=chirps_per_frame,
        rx_channels=rx_channels,
        adc_samples=adc_samples,
        bytes_per_adc_sample=bytes_per_adc_sample,
        raw_bytes=raw_bytes,
    )


def _human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TiB"


def _existing_storage_path(path: str) -> pathlib.Path:
    candidate = pathlib.Path(path).expanduser().absolute()
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            raise ValueError(f"no existing parent filesystem for {path}")
        candidate = parent
    if not candidate.is_dir():
        raise ValueError(f"output path {candidate} is not a directory")
    return candidate


def _storage_check(
    radar_config: Optional[str],
    capture_frames: Optional[int],
    output_path: str,
    safety_factor: float,
    reserve_bytes: int,
) -> Check:
    label = "DCA output storage"
    if radar_config is None:
        return Check(
            label,
            False,
            "radar_config is required to estimate finite DCA output size",
        )
    try:
        estimate = estimate_dca_raw_data(radar_config, capture_frames)
        filesystem_path = _existing_storage_path(output_path)
        free_bytes = int(shutil.disk_usage(filesystem_path).free)
    except (OSError, ValueError) as exc:
        return Check(label, False, str(exc))

    required_bytes = math.ceil(estimate.raw_bytes * safety_factor) + reserve_bytes
    detail = (
        f"output={output_path} filesystem={filesystem_path} "
        f"frames={estimate.frames} chirps_per_frame={estimate.chirps_per_frame} "
        f"rx={estimate.rx_channels} adc_samples={estimate.adc_samples} "
        f"raw={_human_bytes(estimate.raw_bytes)} ({estimate.raw_bytes} bytes) "
        f"required={_human_bytes(required_bytes)} ({required_bytes} bytes, "
        f"factor={safety_factor:g}, reserve={_human_bytes(reserve_bytes)}) "
        f"free={_human_bytes(free_bytes)} ({free_bytes} bytes)"
    )
    if free_bytes < required_bytes:
        return Check(label, False, detail)
    return Check(label, True, detail)


def run_checks(
    interface: str,
    host_ip: str,
    config_serial: str,
    data_serial: str,
    config_port: int = 4096,
    data_port: int = 4098,
    spi_device: str = "/dev/spidev0.0",
    gpiochip: str = "/dev/gpiochip0",
    adxl_binary: str = "adxl355_capture",
    sync_mode: str = "software_timestamp",
    trigger_binary: str = "frame_trigger",
    dca_ip: str = DEFAULT_DCA_IP,
    radar_config: Optional[str] = None,
    capture_frames: Optional[int] = None,
    output_path: str = ".",
    allow_unstable_serial: bool = False,
    disk_safety_factor: float = DEFAULT_DISK_SAFETY_FACTOR,
    disk_reserve_bytes: int = DEFAULT_DISK_RESERVE_BYTES,
) -> list[Check]:
    if sync_mode not in ("software_timestamp", "hardware_trigger"):
        raise ValueError("unsupported sync_mode")
    if (
        isinstance(disk_safety_factor, bool)
        or not isinstance(disk_safety_factor, (int, float))
        or not math.isfinite(float(disk_safety_factor))
        or disk_safety_factor < 1.0
    ):
        raise ValueError("disk_safety_factor must be a finite number >= 1")
    if (
        isinstance(disk_reserve_bytes, bool)
        or not isinstance(disk_reserve_bytes, int)
        or disk_reserve_bytes < 0
    ):
        raise ValueError("disk_reserve_bytes must be a non-negative integer")
    checks = []
    system = platform.system()
    checks.append(Check("Linux", system == "Linux", system))

    tcpdump = shutil.which("tcpdump")
    checks.append(
        Check(
            "tcpdump",
            tcpdump is not None,
            tcpdump or "not found in PATH",
        )
    )

    interfaces = netifaces.interfaces()
    interface_ok = interface in interfaces
    checks.append(
        Check(
            "DCA interface",
            interface_ok,
            interface if interface_ok else f"{interface} not in {interfaces}",
        )
    )

    address_ok = False
    address_detail = f"interface {interface} is unavailable"
    addresses = []
    if interface_ok:
        addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        ipv4 = [item.get("addr") for item in addresses]
        address_ok = host_ip in ipv4
        address_detail = host_ip if address_ok else f"{host_ip} not in {ipv4}"
    checks.append(Check("Pi DCA IPv4", address_ok, address_detail))
    checks.append(
        _network_configuration_check(interface, host_ip, dca_ip, addresses)
    )

    checks.append(
        _serial_check(
            config_serial,
            "radar config UART",
            allow_unstable_serial=allow_unstable_serial,
        )
    )
    checks.append(
        _serial_check(
            data_serial,
            "radar data UART",
            allow_unstable_serial=allow_unstable_serial,
        )
    )
    checks.append(_device_check(spi_device, "ADXL355 SPI device"))
    checks.append(_device_check(gpiochip, "GPIO character device"))
    checks.append(_adxl_binary_check(adxl_binary))
    if sync_mode == "hardware_trigger":
        checks.append(_executable_check(trigger_binary, "radar frame trigger"))

    if address_ok:
        checks.append(_udp_bind_check(host_ip, [config_port, data_port]))
    else:
        checks.append(Check("DCA UDP bind", False, "Pi DCA IPv4 check failed"))
    checks.append(
        _storage_check(
            radar_config=radar_config,
            capture_frames=capture_frames,
            output_path=output_path,
            safety_factor=float(disk_safety_factor),
            reserve_bytes=disk_reserve_bytes,
        )
    )
    return checks


@click.command()
@click.option(
    "--interface",
    required=True,
    help="Raspberry Pi Ethernet interface connected directly to DCA1000",
)
@click.option(
    "--host-ip",
    default="192.168.33.30",
    show_default=True,
    help="Static IPv4 address on the Pi's DCA interface",
)
@click.option(
    "--dca-ip",
    default=DEFAULT_DCA_IP,
    show_default=True,
    help="Static IPv4 address configured on DCA1000EVM",
)
@click.option("--config-serial", default="/dev/ttyACM0", show_default=True)
@click.option("--data-serial", default="/dev/ttyACM1", show_default=True)
@click.option(
    "--allow-unstable-serial",
    is_flag=True,
    help="Diagnostic opt-out permitting non-/dev/serial/by-id UART paths",
)
@click.option("--config-port", default=4096, show_default=True, type=int)
@click.option("--data-port", default=4098, show_default=True, type=int)
@click.option("--spi-device", default="/dev/spidev0.0", show_default=True)
@click.option("--gpiochip", default="/dev/gpiochip0", show_default=True)
@click.option("--adxl-binary", default="adxl355_capture", show_default=True)
@click.option(
    "--radar-config",
    type=click.Path(dir_okay=False, path_type=str),
    help="Radar CLI configuration used to estimate finite raw DCA bytes",
)
@click.option(
    "--capture-frames",
    type=click.IntRange(min=1),
    help="Finite frame override; otherwise use the frameCfg value",
)
@click.option(
    "--output-path",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, path_type=str),
    help="Capture output directory or a not-yet-created path below its filesystem",
)
@click.option(
    "--disk-safety-factor",
    default=DEFAULT_DISK_SAFETY_FACTOR,
    show_default=True,
    type=click.FloatRange(min=1.0),
    help="Multiplier covering PCAP, decoded output, and working space",
)
@click.option(
    "--disk-reserve-mib",
    default=DEFAULT_DISK_RESERVE_BYTES // (1 << 20),
    show_default=True,
    type=click.IntRange(min=0),
    help="Free space kept beyond the multiplied capture estimate",
)
@click.option(
    "--sync-mode",
    type=click.Choice(["software_timestamp", "hardware_trigger"]),
    default="software_timestamp",
    show_default=True,
)
@click.option("--trigger-binary", default="frame_trigger", show_default=True)
def cli(
    interface: str,
    host_ip: str,
    dca_ip: str,
    config_serial: str,
    data_serial: str,
    allow_unstable_serial: bool,
    config_port: int,
    data_port: int,
    spi_device: str,
    gpiochip: str,
    adxl_binary: str,
    radar_config: Optional[str],
    capture_frames: Optional[int],
    output_path: str,
    disk_safety_factor: float,
    disk_reserve_mib: int,
    sync_mode: str,
    trigger_binary: str,
) -> None:
    """Check Pi-local prerequisites without sending commands to hardware."""
    checks = run_checks(
        interface=interface,
        host_ip=host_ip,
        dca_ip=dca_ip,
        config_serial=config_serial,
        data_serial=data_serial,
        allow_unstable_serial=allow_unstable_serial,
        config_port=config_port,
        data_port=data_port,
        spi_device=spi_device,
        gpiochip=gpiochip,
        adxl_binary=adxl_binary,
        radar_config=radar_config,
        capture_frames=capture_frames,
        output_path=output_path,
        disk_safety_factor=disk_safety_factor,
        disk_reserve_bytes=disk_reserve_mib * (1 << 20),
        sync_mode=sync_mode,
        trigger_binary=trigger_binary,
    )
    for check in checks:
        state = "PASS" if check.ok else "FAIL"
        click.echo(f"[{state}] {check.name}: {check.detail}")
    if not all(check.ok for check in checks):
        raise click.exceptions.Exit(1)
