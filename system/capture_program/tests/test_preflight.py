import os
import subprocess
from types import SimpleNamespace

import mmwavecapture.preflight as preflight


def write_radar_config(path, frames=0):
    path.write_text(
        "\n".join(
            [
                "channelCfg 15 5 0",
                "adcCfg 2 1",
                "profileCfg 0 77 429 7 57.14 0 0 70 1 256 5209 0 0 30",
                f"frameCfg 0 1 16 {frames} 100 1 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class FakeSocket:
    def __init__(self, *_args):
        self.bound = None

    def bind(self, address):
        self.bound = address

    def close(self):
        pass


def test_preflight_passes_with_mocked_pi_resources(monkeypatch, tmp_path):
    config_serial = tmp_path / "ttyACM0"
    data_serial = tmp_path / "ttyACM1"
    spi_device = tmp_path / "spidev0.0"
    gpiochip = tmp_path / "gpiochip0"
    radar_config = write_radar_config(tmp_path / "radar.cfg")
    config_serial.touch()
    data_serial.touch()
    spi_device.touch()
    gpiochip.touch()

    monkeypatch.setattr(preflight.platform, "system", lambda: "Linux")
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/tcpdump")
    monkeypatch.setattr(preflight.netifaces, "interfaces", lambda: ["eth0"])
    monkeypatch.setattr(
        preflight.netifaces,
        "ifaddresses",
        lambda _interface: {
            preflight.netifaces.AF_INET: [
                {"addr": "192.168.33.30", "netmask": "255.255.255.0"}
            ]
        },
    )
    monkeypatch.setattr(preflight.socket, "socket", FakeSocket)
    monkeypatch.setattr(os, "access", lambda *_args: True)
    monkeypatch.setattr(
        preflight.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=10 * (1 << 30)),
    )
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"schema_version":1,"hardware_support":true}',
            stderr="",
        ),
    )

    checks = preflight.run_checks(
        interface="eth0",
        host_ip="192.168.33.30",
        config_serial=str(config_serial),
        data_serial=str(data_serial),
        spi_device=str(spi_device),
        gpiochip=str(gpiochip),
        sync_mode="hardware_trigger",
        radar_config=str(radar_config),
        capture_frames=10,
        output_path=str(tmp_path),
        allow_unstable_serial=True,
    )

    assert checks
    assert all(check.ok for check in checks)


def test_preflight_reports_missing_network_and_serial(monkeypatch):
    monkeypatch.setattr(preflight.platform, "system", lambda: "Linux")
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: None)
    monkeypatch.setattr(preflight.netifaces, "interfaces", lambda: ["eth0"])

    checks = preflight.run_checks(
        interface="missing0",
        host_ip="192.168.33.30",
        config_serial="/missing/config",
        data_serial="/missing/data",
    )

    failures = {check.name for check in checks if not check.ok}
    assert failures == {
        "tcpdump",
        "DCA interface",
        "Pi DCA IPv4",
        "DCA network configuration",
        "radar config UART",
        "radar data UART",
        "ADXL355 SPI device",
        "GPIO character device",
        "ADXL355 collector",
        "DCA UDP bind",
        "DCA output storage",
    }


def test_preflight_rejects_mock_only_adxl_binary(monkeypatch, tmp_path):
    binary = tmp_path / "adxl355_capture"
    binary.touch(mode=0o755)
    monkeypatch.setattr(os, "access", lambda *_args: True)
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                '{"schema_version":1,"hardware_support":false,'
                '"mock_support":true}'
            ),
            stderr="",
        ),
    )

    check = preflight._adxl_binary_check(str(binary))

    assert not check.ok
    assert "mock-only" in check.detail


def test_serial_paths_require_stable_by_id_or_explicit_diagnostic_opt_out(
    monkeypatch, tmp_path
):
    serial = tmp_path / "ttyACM0"
    serial.touch()
    monkeypatch.setattr(os, "access", lambda *_args: True)

    rejected = preflight._serial_check(str(serial), "radar config UART")
    allowed = preflight._serial_check(
        str(serial),
        "radar config UART",
        allow_unstable_serial=True,
    )

    assert not rejected.ok
    assert "/dev/serial/by-id" in rejected.detail
    assert allowed.ok
    assert "explicitly allowed for diagnostics" in allowed.detail
    assert preflight._is_stable_serial_path(
        "/dev/serial/by-id/usb-Texas_Instruments_XDS110-if00"
    )
    assert not preflight._is_stable_serial_path("/dev/ttyACM0")


def test_estimate_dca_raw_data_uses_frame_override_and_full_chirp_range(
    tmp_path,
):
    radar_config = write_radar_config(tmp_path / "radar.cfg", frames=0)

    estimate = preflight.estimate_dca_raw_data(
        str(radar_config), capture_frames=10
    )

    assert estimate.frames == 10
    assert estimate.chirps_per_frame == 32
    assert estimate.rx_channels == 4
    assert estimate.adc_samples == 256
    assert estimate.bytes_per_adc_sample == 4
    assert estimate.raw_bytes == 10 * 32 * 4 * 256 * 4


def test_storage_check_fails_closed_when_free_space_is_insufficient(
    monkeypatch, tmp_path
):
    radar_config = write_radar_config(tmp_path / "radar.cfg", frames=10)
    monkeypatch.setattr(
        preflight.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=1_000_000),
    )

    check = preflight._storage_check(
        radar_config=str(radar_config),
        capture_frames=None,
        output_path=str(tmp_path / "future" / "capture"),
        safety_factor=3.0,
        reserve_bytes=0,
    )

    assert not check.ok
    assert "raw=1.2 MiB (1310720 bytes)" in check.detail
    assert "free=976.6 KiB (1000000 bytes)" in check.detail
    assert f"filesystem={tmp_path}" in check.detail


def test_network_configuration_reports_interface_host_target_and_subnet():
    addresses = [
        {"addr": "192.168.33.30", "netmask": "255.255.255.0"}
    ]

    valid = preflight._network_configuration_check(
        "eth0", "192.168.33.30", "192.168.33.180", addresses
    )
    outside = preflight._network_configuration_check(
        "eth0", "192.168.33.30", "192.168.34.180", addresses
    )

    assert valid.ok
    assert "interface=eth0" in valid.detail
    assert "host=192.168.33.30/24" in valid.detail
    assert "target=192.168.33.180" in valid.detail
    assert "subnet=192.168.33.0/24" in valid.detail
    assert not outside.ok
    assert "not a usable address" in outside.detail
