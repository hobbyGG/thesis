"""Read-only Linux/WSL checks for IWR1843 + DCA1000 capture."""

from __future__ import annotations

import os
import pathlib
import platform
import shutil
import socket
from dataclasses import dataclass
from typing import Iterable

import click
import netifaces


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def _serial_check(path: str, label: str) -> Check:
    device = pathlib.Path(path)
    if not device.exists():
        return Check(label, False, f"{path} does not exist")
    if not os.access(device, os.R_OK | os.W_OK):
        return Check(label, False, f"{path} is not readable and writable")
    return Check(label, True, path)


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


def run_checks(
    interface: str,
    host_ip: str,
    config_serial: str,
    data_serial: str,
    config_port: int = 4096,
    data_port: int = 4098,
) -> list[Check]:
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
    if interface_ok:
        addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        ipv4 = [item.get("addr") for item in addresses]
        address_ok = host_ip in ipv4
        address_detail = host_ip if address_ok else f"{host_ip} not in {ipv4}"
    checks.append(Check("DCA host IPv4", address_ok, address_detail))

    checks.append(_serial_check(config_serial, "radar config UART"))
    checks.append(_serial_check(data_serial, "radar data UART"))

    if address_ok:
        checks.append(_udp_bind_check(host_ip, [config_port, data_port]))
    else:
        checks.append(Check("DCA UDP bind", False, "host IPv4 check failed"))
    return checks


@click.command()
@click.option("--interface", required=True, help="Linux interface connected to DCA1000")
@click.option("--host-ip", default="192.168.33.30", show_default=True)
@click.option("--config-serial", default="/dev/ttyACM0", show_default=True)
@click.option("--data-serial", default="/dev/ttyACM1", show_default=True)
@click.option("--config-port", default=4096, show_default=True, type=int)
@click.option("--data-port", default=4098, show_default=True, type=int)
def cli(
    interface: str,
    host_ip: str,
    config_serial: str,
    data_serial: str,
    config_port: int,
    data_port: int,
) -> None:
    """Check local prerequisites without sending commands to hardware."""
    checks = run_checks(
        interface=interface,
        host_ip=host_ip,
        config_serial=config_serial,
        data_serial=data_serial,
        config_port=config_port,
        data_port=data_port,
    )
    for check in checks:
        state = "PASS" if check.ok else "FAIL"
        click.echo(f"[{state}] {check.name}: {check.detail}")
    if not all(check.ok for check in checks):
        raise click.exceptions.Exit(1)
