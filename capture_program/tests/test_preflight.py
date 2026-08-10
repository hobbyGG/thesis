import os

import mmwavecapture.preflight as preflight


class FakeSocket:
    def __init__(self, *_args):
        self.bound = None

    def bind(self, address):
        self.bound = address

    def close(self):
        pass


def test_preflight_passes_with_mocked_wsl_resources(monkeypatch, tmp_path):
    config_serial = tmp_path / "ttyACM0"
    data_serial = tmp_path / "ttyACM1"
    config_serial.touch()
    data_serial.touch()

    monkeypatch.setattr(preflight.platform, "system", lambda: "Linux")
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/tcpdump")
    monkeypatch.setattr(preflight.netifaces, "interfaces", lambda: ["eth1"])
    monkeypatch.setattr(
        preflight.netifaces,
        "ifaddresses",
        lambda _interface: {preflight.netifaces.AF_INET: [{"addr": "192.168.33.30"}]},
    )
    monkeypatch.setattr(preflight.socket, "socket", FakeSocket)
    monkeypatch.setattr(os, "access", lambda *_args: True)

    checks = preflight.run_checks(
        interface="eth1",
        host_ip="192.168.33.30",
        config_serial=str(config_serial),
        data_serial=str(data_serial),
    )

    assert checks
    assert all(check.ok for check in checks)


def test_preflight_reports_missing_network_and_serial(monkeypatch):
    monkeypatch.setattr(preflight.platform, "system", lambda: "Linux")
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: None)
    monkeypatch.setattr(preflight.netifaces, "interfaces", lambda: ["eth0"])

    checks = preflight.run_checks(
        interface="eth1",
        host_ip="192.168.33.30",
        config_serial="/missing/config",
        data_serial="/missing/data",
    )

    failures = {check.name for check in checks if not check.ok}
    assert failures == {
        "tcpdump",
        "DCA interface",
        "DCA host IPv4",
        "radar config UART",
        "radar data UART",
        "DCA UDP bind",
    }
