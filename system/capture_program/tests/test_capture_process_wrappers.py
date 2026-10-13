import json
import signal
import subprocess

import pytest

from mmwavecapture.capture.adxl355 import Adxl355Process
from mmwavecapture.capture.trigger import FrameTriggerError, FrameTriggerProcess


def complete_adxl_summary(samples=3):
    return {
        "schema_version": 1,
        "status": "complete",
        "samples": samples,
        "samples_written": samples,
        "first_drdy_monotonic_ns": 1_000_000_000,
        "last_drdy_monotonic_ns": 1_000_000_000 + (samples - 1) * 1_000_000,
        "line_seq_gaps": 0,
        "fifo_overruns": 0,
        "gpio_backlog_events": 0,
        "fifo_protocol_errors": 0,
        "fifo_xyz_mismatches": 0,
        "fifo_xyz_sets_drained": 0,
        "mock": True,
        "sample_source": "mock",
        "timestamp_pairing": "synthetic",
        "clock": "CLOCK_MONOTONIC",
        "timestamp_semantics": "drdy_edge",
        "group_delay_ns": 0,
        "group_delay_calibrated": False,
        "group_delay_source": None,
    }


class AdxlFakeProcess:
    def __init__(self, summary_path):
        self.summary_path = summary_path
        self.returncode = None
        self.stderr = None
        self.signals = []

    def poll(self):
        return self.returncode

    def send_signal(self, requested_signal):
        self.signals.append(requested_signal)
        self.summary_path.write_text(
            json.dumps(complete_adxl_summary()), encoding="utf-8"
        )
        self.returncode = 0

    def wait(self, timeout=None):
        return self.returncode

    def terminate(self):
        self.returncode = -signal.SIGTERM

    def kill(self):
        self.returncode = -signal.SIGKILL


def test_adxl_process_uses_expected_pi_lines_and_validates_summary(tmp_path):
    output = tmp_path / "adxl355"
    observed = {}

    def popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        (output / "ready.json").write_text(
            json.dumps({"status": "ready"}), encoding="utf-8"
        )
        return AdxlFakeProcess(output / "summary.json")

    capture = Adxl355Process(
        output,
        executable="adxl355_capture",
        popen=popen,
        sleep=lambda _seconds: None,
    )

    assert capture.start() == {"status": "ready"}
    summary = capture.stop()

    command = observed["command"]
    assert command[command.index("--spi-device") + 1] == "/dev/spidev0.0"
    assert command[command.index("--drdy-line") + 1] == "25"
    assert command[command.index("--odr-hz") + 1] == "1000"
    assert summary["samples"] == 3
    assert capture._process.signals == [signal.SIGINT]


@pytest.mark.parametrize("odr_hz", [1, 800, 8000, True])
def test_adxl_process_rejects_unsupported_odr(odr_hz):
    with pytest.raises(ValueError, match="odr_hz must be one of"):
        Adxl355Process(odr_hz=odr_hz)


@pytest.mark.parametrize("spi_hz", [0, 10_000_001, True, 1.5])
def test_adxl_process_rejects_unsupported_spi_clock(spi_hz):
    with pytest.raises(ValueError, match="spi_hz must be an integer"):
        Adxl355Process(spi_hz=spi_hz)


@pytest.mark.parametrize(
    "options,match",
    [
        ({"group_delay_ns": -1}, "nonnegative integer"),
        (
            {"group_delay_ns": 1_780_000},
            "requires group_delay_calibrated=true",
        ),
        (
            {"group_delay_calibrated": True},
            "greater than zero",
        ),
        (
            {"group_delay_ns": 1_780_000, "group_delay_calibrated": True},
            "requires group_delay_source",
        ),
    ],
)
def test_adxl_process_rejects_incomplete_group_delay_calibration(options, match):
    with pytest.raises(ValueError, match=match):
        Adxl355Process(**options)


def test_adxl_process_passes_calibrated_group_delay_to_native_command(tmp_path):
    output = tmp_path / "adxl355"
    observed = {}

    def popen(command, **kwargs):
        observed["command"] = command
        (output / "ready.json").write_text(
            json.dumps({"status": "ready"}), encoding="utf-8"
        )
        process = AdxlFakeProcess(output / "summary.json")

        def calibrated_signal(requested_signal):
            process.signals.append(requested_signal)
            summary = complete_adxl_summary()
            summary.update(
                {
                    "group_delay_ns": 1_780_000,
                    "group_delay_calibrated": True,
                    "group_delay_source": "bench-scope-v1",
                }
            )
            process.summary_path.write_text(json.dumps(summary), encoding="utf-8")
            process.returncode = 0

        process.send_signal = calibrated_signal
        return process

    capture = Adxl355Process(
        output,
        group_delay_ns=1_780_000,
        group_delay_calibrated=True,
        group_delay_source="bench-scope-v1",
        popen=popen,
        sleep=lambda _seconds: None,
    )

    capture.start()
    capture.stop()

    command = observed["command"]
    assert command[command.index("--group-delay-ns") + 1] == "1780000"
    assert "--group-delay-calibrated" in command
    assert command[command.index("--group-delay-source") + 1] == "bench-scope-v1"


def test_adxl_check_running_detects_early_exit(tmp_path):
    output = tmp_path / "adxl355"

    def popen(_command, **_kwargs):
        (output / "ready.json").write_text(
            json.dumps({"status": "ready"}), encoding="utf-8"
        )
        return AdxlFakeProcess(output / "summary.json")

    capture = Adxl355Process(output, popen=popen, sleep=lambda _seconds: None)
    capture.start()
    capture.check_running()
    capture._process.returncode = 1

    with pytest.raises(RuntimeError, match="while expected to be running"):
        capture.check_running()


def test_adxl_abort_atomically_overrides_native_complete_summary(tmp_path):
    output = tmp_path / "adxl355"

    def popen(_command, **_kwargs):
        (output / "ready.json").write_text(
            json.dumps({"status": "ready"}), encoding="utf-8"
        )
        return AdxlFakeProcess(output / "summary.json")

    capture = Adxl355Process(output, popen=popen, sleep=lambda _seconds: None)
    capture.start()
    capture.abort()

    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "aborted"
    assert summary["native_prior_status"] == "complete"
    assert summary["samples"] == 3
    assert summary["line_seq_gaps"] == 0
    assert not (output / "ready.json").exists()
    assert not list(output.glob(".summary.json.tmp-*"))


def test_adxl_ready_requires_explicit_ready_status(tmp_path):
    output = tmp_path / "adxl355"

    def popen(_command, **_kwargs):
        (output / "ready.json").write_text("{}", encoding="utf-8")
        return AdxlFakeProcess(output / "summary.json")

    capture = Adxl355Process(output, popen=popen, sleep=lambda _seconds: None)

    with pytest.raises(RuntimeError, match="unexpected status None"):
        capture.start()
    assert json.loads((output / "summary.json").read_text())["status"] == "aborted"


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("line_seq_gaps", 1, "line_seq_gaps"),
        ("fifo_overruns", 1, "fifo_overruns"),
        ("clock", "CLOCK_REALTIME", "CLOCK_MONOTONIC"),
        ("samples_written", 2, "must equal samples"),
    ],
)
def test_adxl_process_rejects_incomplete_native_summary(field, value, match):
    summary = complete_adxl_summary()
    summary[field] = value

    with pytest.raises(RuntimeError, match=match):
        Adxl355Process.validate_summary_payload(summary)


class TriggerFakeProcess:
    def __init__(self, summary_path, payload):
        self.summary_path = summary_path
        self.payload = payload
        self.returncode = None

    def communicate(self, timeout=None):
        self.summary_path.write_text(json.dumps(self.payload), encoding="utf-8")
        self.returncode = 0
        return "", ""

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = -signal.SIGTERM

    def kill(self):
        self.returncode = -signal.SIGKILL


def test_frame_trigger_mock_never_claims_loopback_timestamp(tmp_path):
    observed = {}
    payload = {
        "schema_version": 1,
        "status": "ok",
        "requested_count": 4,
        "emitted_count": 4,
        "observed_count": 0,
        "missed_loopback": 0,
        "timestamp_quality": "userspace_set_completed",
        "clock": "CLOCK_MONOTONIC",
        "configuration": {
            "gpiochip": "/dev/gpiochip0",
            "output_line": 18,
            "loopback_line": None,
            "frequency_hz": 10.0,
            "count": 4,
            "pulse_width_us": 100,
            "initial_delay_ms": 0,
            "mock": True,
        },
    }

    def popen(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return TriggerFakeProcess(
            tmp_path / "frame_trigger_summary.json", payload
        )

    trigger = FrameTriggerProcess(
        tmp_path,
        binary_path="frame_trigger",
        frequency_hz=10.0,
        count=4,
        initial_delay_ms=0,
        mock=True,
        popen=popen,
    )

    trigger.start()
    summary = trigger.wait()

    assert "--mock" in observed["command"]
    assert "--loopback-line" not in observed["command"]
    assert summary["timestamp_quality"] == "userspace_set_completed"
    assert trigger.config["output_line"] == 18
    assert trigger.config["loopback_line"] is None
    assert trigger.config["use_loopback"] is False


def test_frame_trigger_rejects_false_success_summary(tmp_path):
    payload = {
        "schema_version": 1,
        "status": "ok",
        "requested_count": 2,
        "emitted_count": 1,
        "observed_count": 0,
        "missed_loopback": 0,
        "timestamp_quality": "userspace_set_completed",
        "clock": "CLOCK_MONOTONIC",
        "configuration": {
            "gpiochip": "/dev/gpiochip0",
            "output_line": 18,
            "loopback_line": None,
            "frequency_hz": 10.0,
            "count": 2,
            "pulse_width_us": 100,
            "initial_delay_ms": 0,
            "mock": True,
        },
    }

    trigger = FrameTriggerProcess(
        tmp_path,
        binary_path="frame_trigger",
        frequency_hz=10.0,
        count=2,
        initial_delay_ms=0,
        mock=True,
        popen=lambda *_args, **_kwargs: TriggerFakeProcess(
            tmp_path / "frame_trigger_summary.json", payload
        ),
    )
    trigger.start()

    with pytest.raises(FrameTriggerError, match="emitted_count"):
        trigger.wait()


def test_frame_trigger_loopback_can_be_disabled_from_toml_boolean(tmp_path):
    trigger = FrameTriggerProcess(
        tmp_path,
        binary_path="frame_trigger",
        frequency_hz=9.0,
        count=2,
        use_loopback=False,
    )

    assert trigger.loopback_line is None
    assert trigger.config["use_loopback"] is False
    assert "--loopback-line" not in trigger.command


def test_frame_trigger_loopback_requires_explicit_input_line(tmp_path):
    with pytest.raises(ValueError, match="requires loopback_line"):
        FrameTriggerProcess(
            tmp_path,
            binary_path="frame_trigger",
            frequency_hz=9.0,
            count=2,
            use_loopback=True,
        )
