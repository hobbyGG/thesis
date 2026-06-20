"""Synchronized radar and accelerometer capture orchestration.

This module owns the experiment-level timeline. Device-specific drivers should
live behind the small ``start``/``stop`` interface used by SyncCaptureSession.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class CaptureDevice(Protocol):
    """Minimal interface for a hardware capture stream."""

    def start(self, output_dir: Path) -> Dict[str, Any]:
        """Start recording into output_dir and return device metadata."""

    def stop(self) -> Dict[str, Any]:
        """Stop recording and return final device metadata."""


class CaptureClock(Protocol):
    """Clock interface used to make sync metadata testable."""

    def wall_time_iso(self) -> str:
        """Return a human-readable wall-clock timestamp."""

    def monotonic_ns(self) -> int:
        """Return a monotonic timestamp for time-difference calculations."""


class SystemClock:
    """Production clock: wall time for logs, monotonic time for alignment."""

    def wall_time_iso(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat()

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


@dataclass
class SyncCaptureSession:
    """Coordinate one radar + ADXL355 field capture session."""

    root_dir: str | Path
    session_name: str
    radar: CaptureDevice
    accel: CaptureDevice
    clock: CaptureClock = field(default_factory=SystemClock)
    session_dir: Path = field(init=False)
    events: List[Dict[str, Any]] = field(default_factory=list, init=False)
    streams: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    _started: bool = field(default=False, init=False)
    _stopped: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.session_dir = Path(self.root_dir) / self.session_name

    def start(self) -> Path:
        """Create output folders, start radar then accelerometer, and log events."""
        if self._started:
            raise RuntimeError("capture session has already started")

        self.session_dir.mkdir(parents=True, exist_ok=False)
        radar_dir = self.session_dir / "radar"
        accel_dir = self.session_dir / "accel"
        radar_dir.mkdir()
        accel_dir.mkdir()

        self._record_event("session_prepare")

        radar_start = self._timestamp()
        radar_meta = self.radar.start(radar_dir)
        self.streams["radar"] = {
            "device": "radar",
            "output_dir": str(radar_dir),
            "start_wall_time": radar_start["wall_time"],
            "start_monotonic_ns": radar_start["monotonic_ns"],
            "start_metadata": radar_meta,
        }
        self._record_event("radar_start", stream="radar")

        accel_start = self._timestamp()
        accel_meta = self.accel.start(accel_dir)
        self.streams["accel"] = {
            "device": "adxl355",
            "output_dir": str(accel_dir),
            "start_wall_time": accel_start["wall_time"],
            "start_monotonic_ns": accel_start["monotonic_ns"],
            "start_metadata": accel_meta,
        }
        self._record_event("accel_start", stream="accel")

        self._record_event("session_start_complete")
        self._started = True
        return self.session_dir

    def stop(self) -> Path:
        """Stop accelerometer then radar and write sync.json."""
        if not self._started:
            raise RuntimeError("capture session has not started")
        if self._stopped:
            raise RuntimeError("capture session has already stopped")

        self._record_event("session_stop_request")

        accel_stop = self._timestamp()
        accel_meta = self.accel.stop()
        self.streams["accel"].update(
            {
                "stop_wall_time": accel_stop["wall_time"],
                "stop_monotonic_ns": accel_stop["monotonic_ns"],
                "stop_metadata": accel_meta,
            }
        )
        self._record_event("accel_stop", stream="accel")

        radar_stop = self._timestamp()
        radar_meta = self.radar.stop()
        self.streams["radar"].update(
            {
                "stop_wall_time": radar_stop["wall_time"],
                "stop_monotonic_ns": radar_stop["monotonic_ns"],
                "stop_metadata": radar_meta,
            }
        )
        self._record_event("radar_stop", stream="radar")

        self._record_event("session_stop_complete")
        self._stopped = True
        return self.write_sync_json()

    def write_sync_json(self) -> Path:
        """Persist the synchronization manifest for this experiment."""
        sync_path = self.session_dir / "sync.json"
        tmp_path = sync_path.with_suffix(".json.tmp")
        payload = {
            "session_name": self.session_name,
            "schema_version": 1,
            "clock": {
                "wall_time": "system local timezone",
                "monotonic_ns": "same Pi process monotonic clock",
            },
            "streams": self.streams,
            "events": self.events,
        }
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(sync_path)
        return sync_path

    def _timestamp(self) -> Dict[str, Any]:
        return {
            "wall_time": self.clock.wall_time_iso(),
            "monotonic_ns": self.clock.monotonic_ns(),
        }

    def _record_event(self, event: str, stream: Optional[str] = None) -> None:
        timestamp = self._timestamp()
        item = {
            "event": event,
            "wall_time": timestamp["wall_time"],
            "monotonic_ns": timestamp["monotonic_ns"],
        }
        if stream is not None:
            item["stream"] = stream
        self.events.append(item)
