import io
import signal
import subprocess

import pytest

import mmwavecapture.capture.radardca as radardca_module


class FakeDCA:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []

    def _ok(self, name):
        self.calls.append(name)
        return True

    def system_connection(self):
        return self._ok("system_connection")

    def reset_radar(self):
        return self._ok("reset_radar")

    def reset_fpga(self):
        return self._ok("reset_fpga")

    def config_fpga(self):
        return self._ok("config_fpga")

    def config_packet_delay(self):
        return self._ok("config_packet_delay")

    def start_record(self):
        return self._ok("start_record")

    def stop_record(self):
        return self._ok("stop_record")

    def dump_config(self, _path):
        self.calls.append("dump_config")


class FakeRadar:
    fail_start = False

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []

    def initialize(self):
        self.calls.append("initialize")

    def config(self):
        self.calls.append("config")

    def start_sensor(self):
        self.calls.append("start_sensor")
        if self.fail_start:
            raise RuntimeError("mock sensor start failure")

    def stop_sensor(self):
        self.calls.append("stop_sensor")

    def dump_config(self, _path):
        self.calls.append("dump_config")


class FakeProcess:
    def __init__(self, args, timeout_on_first_wait=False):
        self.args = args
        self.returncode = None
        self.stderr = io.BytesIO()
        self.signals = []
        self.terminated = False
        self.killed = False
        self.timeout_on_first_wait = timeout_on_first_wait
        self.wait_calls = 0

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.timeout_on_first_wait and self.wait_calls == 1:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if self.returncode is None:
            self.returncode = 0
        return self.returncode

    def send_signal(self, sig):
        self.signals.append(sig)
        if sig == signal.SIGINT:
            self.returncode = -signal.SIGINT

    def terminate(self):
        self.terminated = True
        self.returncode = -signal.SIGTERM

    def kill(self):
        self.killed = True
        self.returncode = -signal.SIGKILL


def radar_config(tmp_path):
    path = tmp_path / "radar.cfg"
    path.write_text(
        "\n".join(
            [
                "channelCfg 15 5 0",
                "profileCfg 0 77 429 7 57.14 0 0 70 1 256 5209 0 0 30",
                "frameCfg 0 1 16 0 100 1 0",
            ]
        ),
        encoding="utf-8",
    )
    return path


def install_hardware_mocks(monkeypatch, processes, fail_start=False, catcher_timeout=False):
    FakeRadar.fail_start = fail_start
    monkeypatch.setattr(radardca_module.mmwavecapture.dca1000, "DCA1000", FakeDCA)
    monkeypatch.setattr(radardca_module.mmwavecapture.radar, "Radar", FakeRadar)
    monkeypatch.setattr(radardca_module.shutil, "which", lambda _name: "/usr/bin/tcpdump")
    monkeypatch.setattr(radardca_module.netifaces, "interfaces", lambda: ["eth1"])
    monkeypatch.setattr(
        radardca_module.netifaces,
        "ifaddresses",
        lambda _interface: {radardca_module.netifaces.AF_INET: [{"addr": "192.168.33.30"}]},
    )
    monkeypatch.setattr(radardca_module.time, "sleep", lambda _seconds: None)

    def popen(args, **_kwargs):
        is_catcher = "-c" in args
        process = FakeProcess(
            args,
            timeout_on_first_wait=is_catcher and catcher_timeout,
        )
        processes.append(process)
        return process

    monkeypatch.setattr(radardca_module.subprocess, "Popen", popen)


def make_capture(monkeypatch, tmp_path, **mock_options):
    processes = []
    install_hardware_mocks(monkeypatch, processes, **mock_options)
    capture = radardca_module.RadarDCA(
        hw_name="iwr1843",
        dca_eth_interface="eth1",
        radar_config_filename=radar_config(tmp_path),
        capture_frames=10,
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    capture.base_path = output_dir
    return capture, processes


def test_full_capture_lifecycle_uses_safe_order_and_cleanup(monkeypatch, tmp_path):
    capture, processes = make_capture(monkeypatch, tmp_path)

    capture.prepare_capture()
    capture.start_capture()
    capture.stop_capture()

    assert capture._initialized is True
    assert capture.dca.kwargs["host_ip"] == "192.168.33.30"
    assert capture.dca.calls == [
        "system_connection",
        "reset_radar",
        "reset_fpga",
        "config_fpga",
        "config_packet_delay",
        "start_record",
        "stop_record",
    ]
    assert capture.radar.calls == [
        "initialize",
        "config",
        "start_sensor",
        "stop_sensor",
    ]
    capture_process, catcher_process = processes
    assert "-U" in capture_process.args
    assert str(tmp_path / "output" / "dca.pcap") in capture_process.args
    assert capture_process.signals == [signal.SIGUSR2, signal.SIGINT]
    assert catcher_process.returncode == 0


def test_sensor_start_failure_stops_dca_and_tcpdump(monkeypatch, tmp_path):
    capture, processes = make_capture(monkeypatch, tmp_path, fail_start=True)
    capture.prepare_capture()

    with pytest.raises(RuntimeError, match="mock sensor start failure"):
        capture.start_capture()

    assert "stop_record" in capture.dca.calls
    assert processes[0].signals == [signal.SIGUSR2, signal.SIGINT]
    assert processes[1].terminated is True


def test_capture_timeout_still_cleans_up_all_resources(monkeypatch, tmp_path):
    capture, processes = make_capture(monkeypatch, tmp_path, catcher_timeout=True)
    capture.prepare_capture()
    capture.start_capture()

    with pytest.raises(subprocess.TimeoutExpired):
        capture.stop_capture()

    assert "stop_sensor" in capture.radar.calls
    assert "stop_record" in capture.dca.calls
    assert processes[0].signals == [signal.SIGUSR2, signal.SIGINT]
    assert processes[1].terminated is True


def test_missing_tcpdump_is_reported_before_hardware_access(monkeypatch, tmp_path):
    monkeypatch.setattr(radardca_module.shutil, "which", lambda _name: None)

    with pytest.raises(FileNotFoundError, match="tcpdump"):
        radardca_module.RadarDCA(
            hw_name="iwr1843",
            dca_eth_interface="eth1",
            radar_config_filename=radar_config(tmp_path),
            init_capture_hw=False,
        )
