import io
import math
import signal
import subprocess
import threading

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
    monkeypatch.setattr(radardca_module.netifaces, "interfaces", lambda: ["eth0"])
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


def make_capture(
    monkeypatch,
    tmp_path,
    *,
    capture_frames=10,
    capture_duration_s=None,
    **mock_options,
):
    processes = []
    install_hardware_mocks(monkeypatch, processes, **mock_options)
    capture = radardca_module.RadarDCA(
        hw_name="iwr1843",
        dca_eth_interface="eth0",
        radar_config_filename=radar_config(tmp_path),
        capture_frames=capture_frames,
        capture_duration_s=capture_duration_s,
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
    precision_index = capture_process.args.index("--time-stamp-precision")
    assert capture_process.args[precision_index + 1] == "nano"
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
            dca_eth_interface="eth0",
            radar_config_filename=radar_config(tmp_path),
            init_capture_hw=False,
        )


def test_continuous_duration_stops_normally_without_no_lvds_catcher(
    monkeypatch, tmp_path
):
    capture, processes = make_capture(
        monkeypatch,
        tmp_path,
        capture_frames=0,
        capture_duration_s=0.001,
    )
    export_calls = []

    def fake_export(*args, **kwargs):
        export_calls.append((args, kwargs))
        return tmp_path / "output" / "algorithm_input" / "manifest.json"

    monkeypatch.setattr(radardca_module, "export_algorithm_input", fake_export)

    capture.prepare_capture()
    capture.start_capture()
    capture.stop_capture()
    capture.finalize_capture()

    assert capture.radar.kwargs["capture_frames"] == 0
    assert capture.radar.calls[-2:] == ["start_sensor", "stop_sensor"]
    assert capture.dca.calls[-2:] == ["start_record", "stop_record"]
    assert len(processes) == 1
    assert processes[0].signals == [signal.SIGUSR2, signal.SIGINT]
    assert len(export_calls) == 1
    _, export_kwargs = export_calls[0]
    assert "capture_frames" not in export_kwargs
    assert "expected_frames" not in export_kwargs


class ObservableEvent:
    def __init__(self):
        self._event = threading.Event()
        self.wait_started = threading.Event()

    def clear(self):
        self._event.clear()

    def set(self):
        self._event.set()

    def wait(self, timeout=None):
        self.wait_started.set()
        return self._event.wait(timeout)


def test_indefinite_continuous_abort_unblocks_wait_and_cannot_finalize(
    monkeypatch, tmp_path
):
    capture, processes = make_capture(
        monkeypatch,
        tmp_path,
        capture_frames=0,
        capture_duration_s=None,
    )
    wait_event = ObservableEvent()
    capture._capture_wait_event = wait_event
    export_called = False

    def unexpected_export(*_args, **_kwargs):
        nonlocal export_called
        export_called = True
        raise AssertionError("interrupted capture must not be exported")

    monkeypatch.setattr(radardca_module, "export_algorithm_input", unexpected_export)
    capture.prepare_capture()
    capture.start_capture()

    stop_errors = []

    def stop_in_background():
        try:
            capture.stop_capture()
        except BaseException as exc:
            stop_errors.append(exc)

    stop_thread = threading.Thread(target=stop_in_background)
    stop_thread.start()
    assert wait_event.wait_started.wait(timeout=1.0)

    capture.abort_capture()
    stop_thread.join(timeout=1.0)

    assert not stop_thread.is_alive()
    assert len(stop_errors) == 1
    assert "aborted before normal completion" in str(stop_errors[0])
    assert capture.radar.calls.count("stop_sensor") == 1
    assert capture.dca.calls.count("stop_record") == 1
    assert len(processes) == 1
    assert processes[0].signals == [signal.SIGUSR2, signal.SIGINT]
    with pytest.raises(RuntimeError, match="cannot finalize an interrupted"):
        capture.finalize_capture()
    assert export_called is False


def test_indefinite_continuous_normal_stop_can_finalize(monkeypatch, tmp_path):
    capture, processes = make_capture(
        monkeypatch,
        tmp_path,
        capture_frames=0,
        capture_duration_s=None,
    )
    wait_event = ObservableEvent()
    capture._capture_wait_event = wait_event
    export_calls = []

    def fake_export(*args, **kwargs):
        export_calls.append((args, kwargs))
        return tmp_path / "output" / "algorithm_input" / "manifest.json"

    monkeypatch.setattr(radardca_module, "export_algorithm_input", fake_export)
    capture.prepare_capture()
    capture.start_capture()
    capture.request_continuous_stop()
    capture.stop_capture()
    capture.finalize_capture()

    assert capture.radar.calls.count("stop_sensor") == 1
    assert capture.dca.calls.count("stop_record") == 1
    assert len(processes) == 1
    assert len(export_calls) == 1


@pytest.mark.parametrize(
    "options, expected_message",
    [
        ({"capture_frames": -1}, "zero or positive"),
        ({"capture_frames": 1.5}, "must be an integer"),
        ({"capture_frames": True}, "must be an integer"),
        (
            {"capture_frames": 0, "capture_duration_s": 0},
            "capture_duration_s must be a positive finite number",
        ),
        (
            {"capture_frames": 0, "capture_duration_s": math.inf},
            "capture_duration_s must be a positive finite number",
        ),
        (
            {"capture_frames": 0, "capture_duration_s": math.nan},
            "capture_duration_s must be a positive finite number",
        ),
        (
            {"capture_frames": 10, "capture_duration_s": 1.0},
            "capture_duration_s is only valid when capture_frames is zero",
        ),
        (
            {"capture_frames": 0, "capture_timeout_s": 1.0},
            "capture_timeout_s is only valid when capture_frames is positive",
        ),
        (
            {"capture_frames": 10, "capture_timeout_s": math.nan},
            "capture_timeout_s must be a positive finite number",
        ),
    ],
)
def test_capture_length_parameters_are_validated_before_hardware_access(
    monkeypatch, tmp_path, options, expected_message
):
    monkeypatch.setattr(radardca_module.shutil, "which", lambda _name: None)

    with pytest.raises(ValueError, match=expected_message):
        radardca_module.RadarDCA(
            hw_name="iwr1843",
            dca_eth_interface="eth0",
            radar_config_filename=radar_config(tmp_path),
            init_capture_hw=False,
            **options,
        )
