"""Finite radar frame-trigger subprocess wrapper.

This module intentionally has no Python GPIO dependency. The native helper owns
GPIO lines and records all timestamps in the Linux monotonic-clock domain.
"""

from __future__ import annotations

import json
import math
import pathlib
import subprocess
from typing import Any, Callable, Dict, Optional, Sequence


class FrameTriggerError(RuntimeError):
    """The native frame-trigger process failed or produced an invalid summary."""


class FrameTriggerProcess:
    """Manage one finite native radar frame-trigger run.

    `start` is non-blocking. `wait` is the success boundary: it waits for
    the child, loads the atomically published JSON summary, and validates the
    status and event counts. Mock mode omits the configured loopback line so a
    test run cannot fabricate kernel edge timestamps.
    """

    EVENTS_FILENAME = "frame_trigger_events.csv"
    SUMMARY_FILENAME = "frame_trigger_summary.json"

    def __init__(
        self,
        sync_dir: pathlib.Path,
        *,
        binary_path: pathlib.Path,
        frequency_hz: float,
        count: int,
        gpiochip: pathlib.Path = pathlib.Path("/dev/gpiochip0"),
        output_line: int = 18,
        loopback_line: Optional[int] = None,
        use_loopback: bool = False,
        pulse_width_us: int = 100,
        initial_delay_ms: int = 1000,
        mock: bool = False,
        wait_timeout_s: Optional[float] = None,
        popen: Callable[..., Any] = subprocess.Popen,
    ) -> None:
        self.sync_dir = pathlib.Path(sync_dir)
        self.binary_path = pathlib.Path(binary_path)
        self.gpiochip = pathlib.Path(gpiochip)
        self.output_line = self._line_number("output_line", output_line)
        if not isinstance(use_loopback, bool):
            raise ValueError("use_loopback must be boolean")
        if use_loopback and loopback_line is None:
            raise ValueError("use_loopback=true requires loopback_line")
        self.use_loopback = use_loopback
        self.loopback_line = (
            None
            if loopback_line is None or not use_loopback
            else self._line_number("loopback_line", loopback_line)
        )
        self.frequency_hz = self._positive_frequency(frequency_hz)
        self.count = self._positive_integer("count", count)
        self.pulse_width_us = self._positive_integer(
            "pulse_width_us", pulse_width_us
        )
        self.initial_delay_ms = self._nonnegative_integer(
            "initial_delay_ms", initial_delay_ms
        )
        self.mock = bool(mock)
        if wait_timeout_s is None:
            wait_timeout_s = (
                self.initial_delay_ms / 1000.0
                + max(self.count - 1, 0) / self.frequency_hz
                + self.pulse_width_us / 1_000_000.0
                + 10.0
            )
        if (
            isinstance(wait_timeout_s, bool)
            or not math.isfinite(float(wait_timeout_s))
            or float(wait_timeout_s) <= 0
        ):
            raise ValueError("wait_timeout_s must be finite and positive")
        self.wait_timeout_s = float(wait_timeout_s)
        self._popen = popen
        self._process: Optional[Any] = None
        self._summary: Optional[Dict[str, Any]] = None
        self._stderr = ""

        if self.loopback_line == self.output_line:
            raise ValueError("loopback_line must differ from output_line")
        period_ns = round(1_000_000_000.0 / self.frequency_hz)
        if period_ns < 1:
            raise ValueError("frequency_hz produces an unsupported period")
        if self.pulse_width_us * 1000 >= period_ns:
            raise ValueError("pulse_width_us must be shorter than one trigger period")

    @staticmethod
    def _positive_frequency(value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("frequency_hz must be finite and positive")
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            raise ValueError("frequency_hz must be finite and positive")
        if not math.isfinite(parsed) or parsed <= 0.0:
            raise ValueError("frequency_hz must be finite and positive")
        return parsed

    @staticmethod
    def _positive_integer(name: str, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("{} must be a positive integer".format(name))
        if value > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("{} must fit in an unsigned 64-bit integer".format(name))
        return value

    @staticmethod
    def _nonnegative_integer(name: str, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("{} must be a non-negative integer".format(name))
        if value > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("{} must fit in an unsigned 64-bit integer".format(name))
        return value

    @classmethod
    def _line_number(cls, name: str, value: int) -> int:
        parsed = cls._nonnegative_integer(name, value)
        if parsed > 0xFFFFFFFF:
            raise ValueError("{} must fit in an unsigned 32-bit integer".format(name))
        return parsed

    @property
    def events_path(self) -> pathlib.Path:
        return self.sync_dir / self.EVENTS_FILENAME

    @property
    def summary_path(self) -> pathlib.Path:
        return self.sync_dir / self.SUMMARY_FILENAME

    @property
    def command(self) -> Sequence[str]:
        command = [
            str(self.binary_path),
            "--events",
            str(self.events_path),
            "--summary",
            str(self.summary_path),
            "--gpiochip",
            str(self.gpiochip),
            "--output-line",
            str(self.output_line),
            "--frequency-hz",
            repr(self.frequency_hz),
            "--count",
            str(self.count),
            "--pulse-width-us",
            str(self.pulse_width_us),
            "--initial-delay-ms",
            str(self.initial_delay_ms),
        ]
        if self.loopback_line is not None and not self.mock:
            command.extend(["--loopback-line", str(self.loopback_line)])
        if self.mock:
            command.append("--mock")
        return tuple(command)

    @property
    def summary(self) -> Dict[str, Any]:
        if self._summary is None:
            raise RuntimeError(
                "frame-trigger summary is unavailable before wait completes"
            )
        return dict(self._summary)

    @property
    def config(self) -> Dict[str, Any]:
        """Return the exact finite-trigger contract for provenance."""

        return {
            "binary_path": str(self.binary_path),
            "gpiochip": str(self.gpiochip),
            "output_line": self.output_line,
            "loopback_line": self.loopback_line,
            "use_loopback": self.loopback_line is not None,
            "frequency_hz": self.frequency_hz,
            "count": self.count,
            "pulse_width_us": self.pulse_width_us,
            "initial_delay_ms": self.initial_delay_ms,
            "mock": self.mock,
            "wait_timeout_s": self.wait_timeout_s,
            "events": str(self.events_path),
            "summary": str(self.summary_path),
        }

    def start(self) -> "FrameTriggerProcess":
        """Start the native helper without waiting for its finite pulse train."""

        if self._process is not None:
            raise RuntimeError("frame-trigger process has already been started")
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        stale = [
            path
            for path in (self.events_path, self.summary_path)
            if path.exists()
        ]
        if stale:
            raise FileExistsError(
                "refusing to overwrite frame-trigger output: {}".format(stale[0])
            )
        self._process = self._popen(
            list(self.command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return self

    def _communicate(self, timeout: Optional[float]) -> int:
        if self._process is None:
            raise RuntimeError("frame-trigger process has not been started")
        _, stderr = self._process.communicate(timeout=timeout)
        self._stderr = stderr or ""
        returncode = self._process.returncode
        if returncode is None:
            raise FrameTriggerError("frame-trigger process ended without a return code")
        return int(returncode)

    def _load_summary(self) -> Dict[str, Any]:
        try:
            with self.summary_path.open(encoding="utf-8") as stream:
                payload = json.load(stream)
        except (OSError, ValueError) as error:
            raise FrameTriggerError(
                "could not read frame-trigger summary {}: {}".format(
                    self.summary_path, error
                )
            )
        if not isinstance(payload, dict):
            raise FrameTriggerError("frame-trigger summary must be a JSON object")
        return payload

    def _validate_summary(self, payload: Dict[str, Any]) -> None:
        if payload.get("schema_version") != 1:
            raise FrameTriggerError("frame-trigger summary schema_version must be 1")
        for field in (
            "requested_count",
            "emitted_count",
            "observed_count",
            "missed_loopback",
        ):
            value = payload.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise FrameTriggerError(
                    f"frame-trigger summary {field} must be a non-negative integer"
                )
        expected_quality = (
            "kernel_loopback_edge"
            if self.loopback_line is not None and not self.mock
            else "userspace_set_completed"
        )
        expected = {
            "status": "ok",
            "requested_count": self.count,
            "emitted_count": self.count,
            "timestamp_quality": expected_quality,
            "clock": "CLOCK_MONOTONIC",
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise FrameTriggerError(
                    "invalid frame-trigger summary: {}={!r}, expected {!r}".format(
                        key, payload.get(key), value
                    )
                )
        observed = payload.get("observed_count")
        missed = payload.get("missed_loopback")
        if self.loopback_line is not None and not self.mock:
            if observed != self.count or missed != 0:
                raise FrameTriggerError(
                    "invalid loopback counts: observed={!r}, missed={!r}".format(
                        observed, missed
                    )
                )
        elif observed != 0 or missed != 0:
            raise FrameTriggerError(
                "non-loopback trigger unexpectedly reported loopback events"
            )
        configuration = payload.get("configuration")
        if not isinstance(configuration, dict):
            raise FrameTriggerError("frame-trigger summary has no configuration")
        expected_loopback = (
            self.loopback_line
            if self.loopback_line is not None and not self.mock
            else None
        )
        expected_configuration = {
            "gpiochip": str(self.gpiochip),
            "output_line": self.output_line,
            "loopback_line": expected_loopback,
            "count": self.count,
            "pulse_width_us": self.pulse_width_us,
            "initial_delay_ms": self.initial_delay_ms,
            "mock": self.mock,
        }
        for key, value in expected_configuration.items():
            if configuration.get(key) != value:
                raise FrameTriggerError(
                    f"frame-trigger configuration {key} disagrees with request"
                )
        configured_frequency = configuration.get("frequency_hz")
        if (
            isinstance(configured_frequency, bool)
            or not isinstance(configured_frequency, (int, float))
            or not math.isclose(
                float(configured_frequency),
                self.frequency_hz,
                rel_tol=1e-12,
                abs_tol=0.0,
            )
        ):
            raise FrameTriggerError(
                "frame-trigger configuration frequency_hz disagrees with request"
            )

    def wait(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for completion, then validate and return the native summary."""

        if self._summary is not None:
            self._validate_summary(self._summary)
            return dict(self._summary)
        effective_timeout = self.wait_timeout_s if timeout is None else timeout
        try:
            returncode = self._communicate(effective_timeout)
        except subprocess.TimeoutExpired as exc:
            self.abort()
            raise FrameTriggerError(
                f"frame-trigger exceeded {effective_timeout:.3f}s timeout"
            ) from exc
        try:
            payload = self._load_summary()
        except FrameTriggerError:
            detail = self._stderr.strip()
            if detail:
                raise FrameTriggerError(
                    "frame-trigger exited with code {}: {}".format(returncode, detail)
                )
            raise
        if returncode != 0:
            self._summary = payload
            detail = self._stderr.strip() or str(
                payload.get("error") or "unknown error"
            )
            raise FrameTriggerError(
                "frame-trigger exited with code {}: {}".format(returncode, detail)
            )
        self._validate_summary(payload)
        self._summary = payload
        return dict(payload)

    def abort(self, timeout: float = 5.0) -> None:
        """Terminate a running helper, escalating to kill after `timeout`."""

        if self._process is None or self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._communicate(timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._communicate(timeout)
        if self.summary_path.is_file():
            try:
                self._summary = self._load_summary()
            except FrameTriggerError:
                self._summary = None

    def close(self) -> None:
        """Release the child process; safe to call repeatedly."""

        self.abort()

    def __enter__(self) -> "FrameTriggerProcess":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
