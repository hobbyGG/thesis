import io
import pathlib
import threading
import time

import numpy as np
import pytest

from mmwavecapture import record_cli
from mmwavecapture.adxl355_input import (
    RAW_HEADER_BYTES,
    RECORD_DTYPE,
    SENSITIVITY_LSB_PER_G,
    STANDARD_GRAVITY_MPS2,
)
from mmwavecapture.capture.capture import Capture, CaptureHardware


class OrderedHardware(CaptureHardware):
    def __init__(self, calls):
        self.hw_name = "hw"
        self.calls = calls

    def init_capture_hw(self):
        pass

    def prepare_capture(self):
        self.calls.append("prepare")

    def start_capture(self):
        self.calls.append("start")

    def stop_capture(self):
        self.calls.append("stop")

    def dump_config(self):
        self.calls.append("dump")

    def finalize_capture(self):
        self.calls.append("finalize")

    def abort_capture(self):
        self.calls.append("abort")

    def close(self):
        self.calls.append("close")


def test_before_start_runs_before_any_hardware_is_armed(tmp_path):
    calls = []
    capture = Capture(tmp_path / "cap")
    capture.add_capture_hardware(OrderedHardware(calls))
    capture.capture(lambda: calls.append("operator"))
    assert calls[:3] == ["operator", "prepare", "start"]


def test_before_start_failure_aborts_without_arming(tmp_path):
    calls = []
    capture = Capture(tmp_path / "cap")
    capture.add_capture_hardware(OrderedHardware(calls))

    def refuse():
        raise record_cli._Cancelled

    with pytest.raises(record_cli._Cancelled):
        capture.capture(refuse)
    assert "prepare" not in calls and "start" not in calls
    assert calls[0] == "abort" and calls[-1] == "close"


def write_samples(path, x_raw):
    records = np.zeros(len(x_raw), dtype=RECORD_DTYPE)
    records["x_raw"] = x_raw
    path.parent.mkdir(parents=True)
    path.write_bytes(bytes(RAW_HEADER_BYTES) + records.tobytes())


def test_meter_reports_sizes_and_peak_vibration(tmp_path):
    base = tmp_path / "hw"
    write_samples(base / "adxl355" / "samples.bin", [1000] * 249 + [1250])
    (base / "radar").mkdir()
    (base / "radar" / "dca.pcap").write_bytes(b"\0" * 2_000_000)

    meter = record_cli.Meter(base, range_g=2, odr_hz=500)
    reading = meter.sample(10.0)
    assert reading["samples"] == 250
    assert reading["pcap_bytes"] == 2_000_000
    assert reading["pcap_mb_s"] is None
    scale = STANDARD_GRAVITY_MPS2 / SENSITIVITY_LSB_PER_G[2] * 1000.0
    assert reading["vibration_mm_s2"] == pytest.approx(249 * scale)

    (base / "radar" / "dca.pcap").write_bytes(b"\0" * 10_000_000)
    reading = meter.sample(11.0)
    assert reading["pcap_mb_s"] == pytest.approx(8.0)


def test_meter_before_files_exist(tmp_path):
    reading = record_cli.Meter(tmp_path, 2, 500).sample(0.0)
    assert reading["samples"] == 0 and reading["vibration_mm_s2"] is None


def test_status_line_is_single_line_and_fits_width():
    reading = {
        "pcap_bytes": 51_200_000,
        "pcap_mb_s": 16.0,
        "samples": 1602,
        "adxl_hz": 500.0,
        "vibration_mm_s2": 3.21,
    }
    line = record_cli.status_line("RECORDING", 3.2, 30, reading, 200)
    assert "\n" not in line and "16.0MB/s" in line and "adxl 1602 500Hz" in line
    assert len(record_cli.status_line("RECORDING", 3.2, 30, reading, 40)) <= 39
    reading["pcap_mb_s"] = 0.0
    assert "STALL" in record_cli.status_line("RECORDING", 3.2, 30, reading, 200)


class FakeSync:
    def __init__(self):
        self.state = "initialized"
        self._stop = threading.Event()

    def request_stop(self):
        assert self.state == "started"
        self._stop.set()


class FakeManager:
    def __init__(self, tmp_path):
        self.capture_dir = tmp_path
        self.sync = FakeSync()
        self.hardware = (self.sync,)
        self.armed = False

    def request_stop(self):
        self.sync.request_stop()

    def capture(self, before_start):
        before_start()
        self.armed = True
        self.sync.state = "prepared"
        time.sleep(0.05)
        self.sync.state = "started"
        self.sync._stop.wait(5.0)
        self.sync.state = "stopped"
        time.sleep(0.4)
        self.sync.state = "finalized"


def script(keys):
    queue = list(keys)

    def read_key(timeout):
        time.sleep(timeout)
        return queue.pop(0) if queue else None

    return read_key


def meter_for(tmp_path):
    return record_cli.Meter(tmp_path, 2, 500)


def test_idle_until_enter_then_stop_key_saves(tmp_path):
    manager = FakeManager(tmp_path)
    out = io.StringIO()
    outcome = record_cli.record(
        manager, meter_for(tmp_path), 30, script([None, None, "\r", None, None, None, None, None, "s"]), out, lambda: 120
    )
    assert manager.armed and outcome["error"] is None and not outcome["cancelled"]
    assert outcome["recording_s"] > 0
    shown = out.getvalue()
    assert shown.index("READY") < shown.index("RECORDING") < shown.index("SAVING")
    assert "\n" not in shown


def test_nothing_is_armed_before_enter_and_q_cancels(tmp_path):
    manager = FakeManager(tmp_path)
    outcome = record_cli.record(
        manager, meter_for(tmp_path), 30, script([None, "x", "q"]), io.StringIO(), lambda: 120
    )
    assert outcome["cancelled"] and not manager.armed


def test_stop_during_startup_is_applied_once_recording(tmp_path):
    manager = FakeManager(tmp_path)
    outcome = record_cli.record(
        manager, meter_for(tmp_path), 30, script(["\n", "s"]), io.StringIO(), lambda: 120
    )
    assert outcome["error"] is None and manager.sync.state == "finalized"


def test_worker_error_is_reported(tmp_path):
    manager = FakeManager(tmp_path)

    def failing(before_start):
        before_start()
        raise RuntimeError("DCA timeout")

    manager.capture = failing
    outcome = record_cli.record(
        manager, meter_for(tmp_path), 30, script(["\r"]), io.StringIO(), lambda: 120
    )
    assert str(outcome["error"]) == "DCA timeout"
