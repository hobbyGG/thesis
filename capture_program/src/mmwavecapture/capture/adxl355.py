"""Process wrapper for the native ADXL355 collector.

The native process owns SPI/GPIO access and writes the raw data.  This module
only manages its lifecycle and validates the completion summary; it does not
invent sample timestamps in Python.
"""

from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import tempfile
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Union


PathLike = Union[str, pathlib.Path]


class Adxl355Process:
    """Manage one native ``adxl355_capture`` process.

    ``start`` waits until the collector atomically publishes ``ready.json``.
    ``stop`` requests a graceful SIGINT shutdown and requires a complete,
    loss-free summary.  The injectable process/time functions deliberately
    keep this wrapper testable on hosts without SPI or GPIO hardware.
    """

    RAW_FILENAME = "samples.bin"
    SUMMARY_FILENAME = "summary.json"
    READY_FILENAME = "ready.json"
    CONFIG_FILENAME = "config.json"
    ALGORITHM_INPUT_DIRECTORY = "algorithm_input"
    SUPPORTED_ODR_HZ = (125, 250, 500, 1000, 2000, 4000)
    MIN_SPI_HZ = 1
    MAX_SPI_HZ = 10_000_000

    def __init__(
        self,
        base_path: Optional[PathLike] = None,
        executable: PathLike = "adxl355_capture",
        spi_device: str = "/dev/spidev0.0",
        gpiochip: str = "/dev/gpiochip0",
        drdy_line: int = 25,
        odr_hz: int = 1000,
        range_g: int = 2,
        spi_hz: int = 5_000_000,
        group_delay_ns: int = 0,
        group_delay_calibrated: bool = False,
        group_delay_source: Optional[str] = None,
        mock: bool = False,
        ready_timeout_s: float = 5.0,
        stop_timeout_s: float = 5.0,
        terminate_timeout_s: float = 2.0,
        poll_interval_s: float = 0.01,
        popen: Callable[..., Any] = subprocess.Popen,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if drdy_line < 0:
            raise ValueError("drdy_line must be zero or positive")
        if isinstance(odr_hz, bool) or odr_hz not in self.SUPPORTED_ODR_HZ:
            raise ValueError(
                "odr_hz must be one of 125, 250, 500, 1000, 2000, or 4000"
            )
        if range_g not in (2, 4, 8):
            raise ValueError("range_g must be one of 2, 4, or 8")
        if (
            isinstance(spi_hz, bool)
            or not isinstance(spi_hz, int)
            or not self.MIN_SPI_HZ <= spi_hz <= self.MAX_SPI_HZ
        ):
            raise ValueError("spi_hz must be an integer from 1 through 10000000")
        if (
            isinstance(group_delay_ns, bool)
            or not isinstance(group_delay_ns, int)
            or group_delay_ns < 0
        ):
            raise ValueError("group_delay_ns must be a nonnegative integer")
        if not isinstance(group_delay_calibrated, bool):
            raise ValueError("group_delay_calibrated must be boolean")
        if group_delay_source is not None and (
            not isinstance(group_delay_source, str)
            or not group_delay_source.strip()
        ):
            raise ValueError("group_delay_source must be a nonempty string or null")
        if group_delay_calibrated:
            if group_delay_ns <= 0:
                raise ValueError(
                    "calibrated group delay requires group_delay_ns greater than zero"
                )
            if group_delay_source is None:
                raise ValueError(
                    "calibrated group delay requires group_delay_source"
                )
        elif group_delay_ns != 0 or group_delay_source is not None:
            raise ValueError(
                "nonzero group delay/source requires group_delay_calibrated=true"
            )
        if ready_timeout_s <= 0:
            raise ValueError("ready_timeout_s must be positive")
        if stop_timeout_s <= 0:
            raise ValueError("stop_timeout_s must be positive")
        if terminate_timeout_s <= 0:
            raise ValueError("terminate_timeout_s must be positive")
        if poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be positive")

        self.base_path = pathlib.Path(base_path) if base_path is not None else None
        self.executable = str(executable)
        self.spi_device = spi_device
        self.gpiochip = gpiochip
        self.drdy_line = drdy_line
        self.odr_hz = odr_hz
        self.range_g = range_g
        self.spi_hz = spi_hz
        self.group_delay_ns = group_delay_ns
        self.group_delay_calibrated = group_delay_calibrated
        self.group_delay_source = (
            group_delay_source.strip()
            if isinstance(group_delay_source, str)
            else None
        )
        self.mock = mock
        self.ready_timeout_s = ready_timeout_s
        self.stop_timeout_s = stop_timeout_s
        self.terminate_timeout_s = terminate_timeout_s
        self.poll_interval_s = poll_interval_s

        self._popen = popen
        self._clock = clock
        self._sleep = sleep
        self._process: Optional[Any] = None
        self._state = "idle"
        self._ready: Optional[Dict[str, Any]] = None
        self._summary: Optional[Dict[str, Any]] = None

    @property
    def raw_path(self) -> pathlib.Path:
        return self._required_base_path() / self.RAW_FILENAME

    @property
    def summary_path(self) -> pathlib.Path:
        return self._required_base_path() / self.SUMMARY_FILENAME

    @property
    def ready_path(self) -> pathlib.Path:
        return self._required_base_path() / self.READY_FILENAME

    @property
    def config_path(self) -> pathlib.Path:
        return self._required_base_path() / self.CONFIG_FILENAME

    @property
    def ready(self) -> Optional[Dict[str, Any]]:
        return dict(self._ready) if self._ready is not None else None

    @property
    def summary(self) -> Optional[Dict[str, Any]]:
        return dict(self._summary) if self._summary is not None else None

    @property
    def config(self) -> Dict[str, Any]:
        """Return a JSON-serializable description of the collector contract."""

        paths: Dict[str, Optional[str]] = {
            "output": None,
            "summary": None,
            "ready_file": None,
        }
        if self.base_path is not None:
            paths = {
                "output": str(self.raw_path),
                "summary": str(self.summary_path),
                "ready_file": str(self.ready_path),
            }
        return {
            "executable": self.executable,
            "spi_device": self.spi_device,
            "gpiochip": self.gpiochip,
            "drdy_line": self.drdy_line,
            "odr_hz": self.odr_hz,
            "range_g": self.range_g,
            "spi_hz": self.spi_hz,
            "group_delay_ns": self.group_delay_ns,
            "group_delay_calibrated": self.group_delay_calibrated,
            "group_delay_source": self.group_delay_source,
            "mock": self.mock,
            "ready_timeout_s": self.ready_timeout_s,
            "stop_timeout_s": self.stop_timeout_s,
            "paths": paths,
        }

    def _required_base_path(self) -> pathlib.Path:
        if self.base_path is None:
            raise RuntimeError("ADXL355 output directory is not set")
        return self.base_path

    def _command(self) -> List[str]:
        command = [
            self.executable,
            "--output",
            str(self.raw_path),
            "--summary",
            str(self.summary_path),
            "--ready-file",
            str(self.ready_path),
            "--spi-device",
            self.spi_device,
            "--gpiochip",
            self.gpiochip,
            "--drdy-line",
            str(self.drdy_line),
            "--odr-hz",
            str(self.odr_hz),
            "--range-g",
            str(self.range_g),
            "--spi-hz",
            str(self.spi_hz),
            "--group-delay-ns",
            str(self.group_delay_ns),
        ]
        if self.group_delay_calibrated:
            if self.group_delay_source is None:  # constructor invariant
                raise RuntimeError("calibrated group delay has no source")
            command.extend(
                [
                    "--group-delay-calibrated",
                    "--group-delay-source",
                    self.group_delay_source,
                ]
            )
        if self.mock:
            command.append("--mock")
        return command

    @staticmethod
    def _read_json(path: pathlib.Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict):
            raise RuntimeError(f"expected a JSON object in {path}")
        return payload

    @staticmethod
    def _atomic_write_json(path: pathlib.Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.tmp-",
            dir=path.parent,
        )
        temporary = pathlib.Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def _mark_summary_aborted(self) -> None:
        prior: Dict[str, Any] = {}
        read_error: Optional[str] = None
        if self.summary_path.is_file():
            try:
                prior = self._read_json(self.summary_path)
            except (OSError, ValueError, RuntimeError) as exc:
                read_error = str(exc)

        aborted: Dict[str, Any] = dict(prior)
        aborted["schema_version"] = 1
        aborted["native_prior_status"] = prior.get("status")
        aborted["status"] = "aborted"
        aborted["abort_reason"] = "coordinator_abort"
        aborted["aborted_realtime_ns"] = time.time_ns()
        aborted["native_summary_present"] = bool(prior)
        if read_error is not None:
            aborted["native_summary_read_error"] = read_error
        self._atomic_write_json(self.summary_path, aborted)
        self.ready_path.unlink(missing_ok=True)
        self._summary = aborted

    @staticmethod
    def _stderr_text(process: Any) -> str:
        stream = getattr(process, "stderr", None)
        if stream is None:
            return ""
        try:
            content = stream.read()
        except Exception:
            return ""
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace").strip()
        return str(content).strip()

    def _early_exit_error(self, returncode: Any, phase: str) -> RuntimeError:
        detail = self._stderr_text(self._process)
        message = (
            f"ADXL355 collector exited {phase} with code {returncode}"
        )
        if detail:
            message = f"{message}: {detail}"
        return RuntimeError(message)

    def start(self, output_dir: Optional[PathLike] = None) -> Dict[str, Any]:
        """Start the collector and wait for its ready handshake."""

        if self._state != "idle":
            raise RuntimeError(
                f"cannot start ADXL355 collector while state is {self._state!r}"
            )
        if output_dir is not None:
            self.base_path = pathlib.Path(output_dir)
        directory = self._required_base_path()
        directory.mkdir(parents=True, exist_ok=True)

        existing = [
            path
            for path in (self.raw_path, self.summary_path, self.ready_path)
            if path.exists()
        ]
        if existing:
            names = ", ".join(str(path) for path in existing)
            raise FileExistsError(
                "refusing to reuse existing ADXL355 capture artifacts: " + names
            )

        try:
            self._process = self._popen(
                self._command(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except BaseException:
            self._state = "failed"
            raise
        self._state = "starting"

        deadline = self._clock() + self.ready_timeout_s
        last_json_error: Optional[BaseException] = None
        while True:
            if self.ready_path.exists():
                try:
                    ready = self._read_json(self.ready_path)
                except (OSError, ValueError, RuntimeError) as exc:
                    last_json_error = exc
                else:
                    status = ready.get("status")
                    if status != "ready":
                        self.abort()
                        raise RuntimeError(
                            "ADXL355 ready handshake has unexpected status "
                            f"{status!r}"
                        )
                    self._ready = ready
                    self._state = "running"
                    return dict(ready)

            process = self._process
            if process is None:
                self._state = "failed"
                raise RuntimeError("ADXL355 collector process was not created")
            returncode = process.poll()
            if returncode is not None:
                self._state = "failed"
                raise self._early_exit_error(returncode, "before becoming ready")

            if self._clock() >= deadline:
                self.abort()
                detail = ""
                if last_json_error is not None:
                    detail = f"; last ready-file error: {last_json_error}"
                raise TimeoutError(
                    "timed out waiting for ADXL355 ready handshake "
                    f"at {self.ready_path}{detail}"
                )
            self._sleep(self.poll_interval_s)

    def check_running(self) -> None:
        """Raise immediately if the ready collector is no longer alive."""

        if self._state != "running":
            raise RuntimeError(
                f"ADXL355 collector is not running (state={self._state!r})"
            )
        process = self._process
        if process is None:
            self._state = "failed"
            raise RuntimeError("ADXL355 collector process is missing")
        returncode = process.poll()
        if returncode is not None:
            self._state = "failed"
            raise self._early_exit_error(returncode, "while expected to be running")

    def _wait_with_escalation(self, graceful: bool) -> Any:
        process = self._process
        if process is None:
            return None

        if process.poll() is None:
            if graceful:
                process.send_signal(signal.SIGINT)
            else:
                process.terminate()
            try:
                return process.wait(timeout=self.stop_timeout_s)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    return process.wait(timeout=self.terminate_timeout_s)
                except subprocess.TimeoutExpired:
                    process.kill()
                    return process.wait(timeout=self.terminate_timeout_s)
        return process.poll()

    @staticmethod
    def validate_summary_payload(
        summary: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Validate the native collector's loss-free completion contract."""

        if summary.get("schema_version") != 1:
            raise RuntimeError(
                "ADXL355 summary schema_version must be 1, got "
                f"{summary.get('schema_version')!r}"
            )

        if summary.get("status") != "complete":
            raise RuntimeError(
                "ADXL355 summary status must be 'complete', got "
                f"{summary.get('status')!r}"
            )

        samples = summary.get("samples")
        if isinstance(samples, bool) or not isinstance(samples, int) or samples <= 0:
            raise RuntimeError(
                f"ADXL355 summary samples must be a positive integer, got {samples!r}"
            )
        if summary.get("samples_written") != samples:
            raise RuntimeError(
                "ADXL355 summary samples_written must equal samples, got "
                f"{summary.get('samples_written')!r} and {samples!r}"
            )
        for field in (
            "line_seq_gaps",
            "fifo_overruns",
            "gpio_backlog_events",
            "fifo_protocol_errors",
            "fifo_xyz_mismatches",
        ):
            value = summary.get(field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise RuntimeError(
                    f"ADXL355 summary {field} must be an integer, got {value!r}"
                )
            if value != 0:
                raise RuntimeError(
                    f"ADXL355 summary reports {field}={value}; capture is incomplete"
                )
        is_mock = summary.get("mock")
        if not isinstance(is_mock, bool):
            raise RuntimeError("ADXL355 summary mock must be boolean")
        drained = summary.get("fifo_xyz_sets_drained")
        if isinstance(drained, bool) or not isinstance(drained, int) or drained < 0:
            raise RuntimeError(
                "ADXL355 summary fifo_xyz_sets_drained must be non-negative"
            )
        if is_mock:
            expected_source = "mock"
            expected_pairing = "synthetic"
            expected_drained = 0
        else:
            expected_source = "FIFO_DATA_oldest"
            expected_pairing = "one_drdy_edge_to_one_fifo_xyz"
            expected_drained = samples
        if summary.get("sample_source") != expected_source:
            raise RuntimeError("ADXL355 summary has unexpected sample_source")
        if summary.get("timestamp_pairing") != expected_pairing:
            raise RuntimeError("ADXL355 summary has unexpected timestamp_pairing")
        if drained != expected_drained:
            raise RuntimeError(
                "ADXL355 summary FIFO drain count disagrees with sample count"
            )
        if summary.get("clock") != "CLOCK_MONOTONIC":
            raise RuntimeError("ADXL355 summary must use CLOCK_MONOTONIC")
        if summary.get("timestamp_semantics") != "drdy_edge":
            raise RuntimeError("ADXL355 summary timestamps must be DRDY edges")
        group_delay_ns = summary.get("group_delay_ns")
        if (
            isinstance(group_delay_ns, bool)
            or not isinstance(group_delay_ns, int)
            or group_delay_ns < 0
        ):
            raise RuntimeError(
                "ADXL355 summary group_delay_ns must be a nonnegative integer"
            )
        group_delay_calibrated = summary.get("group_delay_calibrated")
        if not isinstance(group_delay_calibrated, bool):
            raise RuntimeError(
                "ADXL355 summary group_delay_calibrated must be boolean"
            )
        group_delay_source = summary.get("group_delay_source")
        if group_delay_source is not None and (
            not isinstance(group_delay_source, str)
            or not group_delay_source.strip()
        ):
            raise RuntimeError(
                "ADXL355 summary group_delay_source must be nonempty or null"
            )
        if group_delay_calibrated and (
            group_delay_ns <= 0 or group_delay_source is None
        ):
            raise RuntimeError(
                "calibrated ADXL355 group delay requires a positive value and source"
            )
        if not group_delay_calibrated and (
            group_delay_ns != 0 or group_delay_source is not None
        ):
            raise RuntimeError(
                "uncalibrated ADXL355 group delay must be zero with no source"
            )
        first_edge = summary.get("first_drdy_monotonic_ns")
        last_edge = summary.get("last_drdy_monotonic_ns")
        if (
            isinstance(first_edge, bool)
            or not isinstance(first_edge, int)
            or first_edge <= 0
            or isinstance(last_edge, bool)
            or not isinstance(last_edge, int)
            or last_edge < first_edge
        ):
            raise RuntimeError(
                "ADXL355 summary has invalid first/last DRDY timestamps"
            )
        return dict(summary)

    def validate_summary(self) -> Dict[str, Any]:
        summary = self._read_json(self.summary_path)
        validated = self.validate_summary_payload(summary)
        expected_group_delay = {
            "group_delay_ns": self.group_delay_ns,
            "group_delay_calibrated": self.group_delay_calibrated,
            "group_delay_source": self.group_delay_source,
        }
        for field, expected in expected_group_delay.items():
            if validated.get(field) != expected:
                raise RuntimeError(
                    f"ADXL355 summary {field} disagrees with requested "
                    f"calibration: {validated.get(field)!r} != {expected!r}"
                )
        self._summary = validated
        return dict(validated)

    def stop(self) -> Dict[str, Any]:
        """Gracefully stop the process and validate its completion summary."""

        if self._state != "running":
            raise RuntimeError(
                f"cannot stop ADXL355 collector while state is {self._state!r}"
            )
        process = self._process
        if process is None:
            self._state = "failed"
            raise RuntimeError("ADXL355 collector process is missing")

        premature_returncode = process.poll()
        returncode = self._wait_with_escalation(graceful=True)
        if premature_returncode is not None:
            self._state = "failed"
            raise self._early_exit_error(
                premature_returncode, "unexpectedly before stop was requested"
            )
        if returncode not in (0, -signal.SIGINT):
            self._state = "failed"
            raise self._early_exit_error(returncode, "during shutdown")

        try:
            summary = self.validate_summary()
        except BaseException:
            self._state = "failed"
            raise
        self._state = "stopped"
        return summary

    def abort(self) -> None:
        """Stop and atomically mark retained component evidence as aborted."""

        if self._state in ("aborted", "closed", "stopped"):
            return
        if self._state == "idle":
            self._state = "aborted"
            return
        try:
            process = self._process
            if process is not None and process.poll() is None:
                self._wait_with_escalation(graceful=True)
        finally:
            try:
                self._mark_summary_aborted()
            finally:
                self._state = "aborted"

    def close(self) -> None:
        """Idempotently release the process while preserving capture evidence."""

        if self._state == "closed":
            return
        try:
            self.abort()
        finally:
            self._process = None
            self._state = "closed"
