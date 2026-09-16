"""Coordinated Raspberry Pi capture for IWR1843/DCA1000 and ADXL355."""

from __future__ import annotations

import csv
import datetime
import inspect
import json
import math
import os
import pathlib
import shutil
import threading
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

import numpy as np

from mmwavecapture.algorithm_input import (
    MANIFEST_FILENAME as RADAR_ALGORITHM_MANIFEST_FILENAME,
    SCHEMA_NAME as RADAR_ALGORITHM_SCHEMA_NAME,
    SCHEMA_VERSION as RADAR_ALGORITHM_SCHEMA_VERSION,
)
from mmwavecapture.adxl355_input import export_adxl355_input
from mmwavecapture.capture.adxl355 import Adxl355Process
from mmwavecapture.capture.capture import CaptureHardware
from mmwavecapture.capture.radardca import RadarDCA
from mmwavecapture.capture.trigger import FrameTriggerProcess
from mmwavecapture.fusion_calibration import (
    FusionValueCalibration,
    load_fusion_calibration,
)
from mmwavecapture.radar import RadarCoreConfig


class SynchronizedRadarAdxl(CaptureHardware):
    """Coordinate radar and accelerometer capture on one Pi monotonic clock.

    ``software_timestamp`` brackets the radar ``sensorStart`` call but never
    labels Ethernet packet receive timestamps as radar frame-start timestamps.
    ``hardware_trigger`` uses a finite native GPIO trigger process, or an
    injected compatible object. Its small protocol is ``start(sync_dir)`` (a
    no-argument ``start`` is also accepted), ``wait()``, ``abort()``,
    ``close()``, and a ``summary`` mapping.
    """

    RADAR_DIRECTORY = "radar"
    ADXL_DIRECTORY = "adxl355"
    SYNC_DIRECTORY = "sync"
    MANIFEST_FILENAME = "manifest.json"
    SYNC_CONFIG_FILENAME = "config.json"
    RADAR_TIMELINE_FILENAME = "radar_frame_monotonic_ns.npy"
    TIMELINE_MANIFEST_FILENAME = "timeline.json"
    SCHEMA_VERSION = 1
    SYNC_MODES = ("software_timestamp", "hardware_trigger")
    TRIGGER_RATE_FRACTION = 0.90
    DCA_NO_LVDS_GUARD_S = 5.0
    ADXL_SUPERVISION_INTERVAL_S = 0.05
    ADXL_SUPERVISION_ABORT_TIMEOUT_S = 5.0

    def __init__(
        self,
        hw_name: str,
        radar_kwargs: Optional[Mapping[str, Any]] = None,
        adxl_kwargs: Optional[Mapping[str, Any]] = None,
        trigger_kwargs: Optional[Mapping[str, Any]] = None,
        radar_capture: Optional[Any] = None,
        adxl_capture: Optional[Any] = None,
        trigger_capture: Optional[Any] = None,
        sync_mode: str = "software_timestamp",
        pre_roll_s: float = 2.0,
        post_roll_s: float = 2.0,
        hardware_validated: bool = False,
        fusion_calibration_filename: Optional[Union[str, pathlib.Path]] = None,
        trigger_edge_uncertainty_ns: Optional[int] = None,
        radar_trigger_latency_ns: Optional[int] = None,
        radar_trigger_latency_uncertainty_ns: Optional[int] = None,
        radar_trigger_latency_source: Optional[str] = None,
        adxl_filter_group_delay_uncertainty_ns: Optional[int] = None,
        export_adxl_algorithm_data: bool = True,
        export_sync_timeline: bool = True,
        init_capture_hw: bool = True,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
        wall_time_ns: Callable[[], int] = time.time_ns,
        sleep: Callable[[float], None] = time.sleep,
        **kwargs: Any,
    ) -> None:
        if sync_mode not in self.SYNC_MODES:
            raise ValueError(
                f"sync_mode must be one of {self.SYNC_MODES}, got {sync_mode!r}"
            )
        if pre_roll_s < 0:
            raise ValueError("pre_roll_s must be zero or positive")
        if post_roll_s < 0:
            raise ValueError("post_roll_s must be zero or positive")
        if (
            sync_mode == "hardware_trigger"
            and trigger_capture is None
            and trigger_kwargs is None
        ):
            raise ValueError(
                "hardware_trigger mode requires trigger_kwargs or an injected "
                "trigger_capture"
            )
        if sync_mode == "software_timestamp" and (
            trigger_capture is not None or trigger_kwargs is not None
        ):
            raise ValueError(
                "software_timestamp mode must not configure a frame trigger"
            )
        if trigger_capture is not None and trigger_kwargs is not None:
            raise ValueError(
                "provide trigger_kwargs or trigger_capture, not both"
            )

        unknown = set(kwargs) - {"hw_def_class"}
        if unknown:
            names = ", ".join(sorted(unknown))
            raise TypeError(f"unexpected synchronized capture options: {names}")

        self.hw_name = hw_name
        self.sync_mode = sync_mode
        self.pre_roll_s = float(pre_roll_s)
        self.post_roll_s = float(post_roll_s)
        self.hardware_validated = bool(hardware_validated)
        self._trigger_edge_uncertainty_ns = self._optional_nonnegative_integer(
            trigger_edge_uncertainty_ns,
            "trigger_edge_uncertainty_ns",
        )
        if (
            self._trigger_edge_uncertainty_ns is not None
            and sync_mode != "hardware_trigger"
        ):
            raise ValueError(
                "trigger edge uncertainty requires hardware_trigger mode"
            )
        self._radar_trigger_latency_ns = self._optional_nonnegative_integer(
            radar_trigger_latency_ns,
            "radar_trigger_latency_ns",
        )
        self._radar_trigger_latency_uncertainty_ns = (
            self._optional_nonnegative_integer(
                radar_trigger_latency_uncertainty_ns,
                "radar_trigger_latency_uncertainty_ns",
            )
        )
        if radar_trigger_latency_source is not None and (
            not isinstance(radar_trigger_latency_source, str)
            or not radar_trigger_latency_source.strip()
        ):
            raise ValueError(
                "radar_trigger_latency_source must be a nonempty string or null"
            )
        self._radar_trigger_latency_source = (
            radar_trigger_latency_source.strip()
            if isinstance(radar_trigger_latency_source, str)
            else None
        )
        radar_latency_fields = (
            self._radar_trigger_latency_ns,
            self._radar_trigger_latency_uncertainty_ns,
            self._radar_trigger_latency_source,
        )
        populated_latency_fields = sum(
            value is not None for value in radar_latency_fields
        )
        if populated_latency_fields not in (0, len(radar_latency_fields)):
            raise ValueError(
                "radar trigger latency calibration requires value, uncertainty, "
                "and source together"
            )
        if populated_latency_fields and sync_mode != "hardware_trigger":
            raise ValueError(
                "radar trigger latency calibration requires hardware_trigger mode"
            )
        self._radar_latency_calibrated = bool(populated_latency_fields)
        self._adxl_filter_group_delay_uncertainty_ns = (
            self._optional_nonnegative_integer(
                adxl_filter_group_delay_uncertainty_ns,
                "adxl_filter_group_delay_uncertainty_ns",
            )
        )
        self._fusion_calibration_source: Optional[pathlib.Path] = None
        self._fusion_value_calibration: Optional[FusionValueCalibration] = None
        self._fusion_calibration_copied = False
        if fusion_calibration_filename is not None:
            source = pathlib.Path(fusion_calibration_filename)
            self._fusion_value_calibration = load_fusion_calibration(source)
            self._fusion_calibration_source = source
        self.export_adxl_algorithm_data = bool(export_adxl_algorithm_data)
        self.export_sync_timeline = bool(export_sync_timeline)
        self._monotonic_ns = monotonic_ns
        self._wall_time_ns = wall_time_ns
        self._sleep = sleep

        # Validate/build the process-only ADXL wrapper before RadarDCA opens
        # serial ports and UDP sockets.  This keeps an invalid ADXL option from
        # leaking already-initialized radar resources during construction.
        if adxl_capture is None:
            adxl_options = dict(adxl_kwargs or {})
            adxl_options.pop("base_path", None)
            self.adxl_capture = Adxl355Process(**adxl_options)
        else:
            self.adxl_capture = adxl_capture

        radar_options = dict(radar_kwargs or {})
        radar_options.pop("hw_name", None)
        radar_config_filename = radar_options.get("radar_config_filename")
        if radar_config_filename is not None:
            radar_config_filename = pathlib.Path(radar_config_filename)
            radar_options["radar_config_filename"] = radar_config_filename

        radar_algorithm_requested = radar_options.get("export_algorithm_data")
        if radar_algorithm_requested is None and radar_capture is not None:
            for attribute in ("export_algorithm_data", "_export_algorithm_data"):
                value = getattr(radar_capture, attribute, None)
                if isinstance(value, bool):
                    radar_algorithm_requested = value
                    break
        if radar_algorithm_requested is None:
            radar_algorithm_requested = True
        self._radar_algorithm_requested = bool(radar_algorithm_requested)
        if self.export_sync_timeline and not self._radar_algorithm_requested:
            raise ValueError(
                "export_sync_timeline=true requires RadarDCA "
                "export_algorithm_data=true because decoded radar metadata is "
                "the only accepted timeline source"
            )

        self._radar_trigger_config_validated = False
        self._radar_frame_period_s: Optional[float] = None
        self._radar_capture_frames: Optional[int] = None
        self._radar_continuous = False
        if radar_config_filename is not None:
            radar_config = RadarCoreConfig(radar_config_filename)
            frame_cfgs = radar_config.command_args("frameCfg")
            if len(frame_cfgs) != 1 or len(frame_cfgs[0]) < 7:
                raise ValueError(
                    "radar config must contain exactly one complete frameCfg"
                )
            expected_trigger_select = 2 if sync_mode == "hardware_trigger" else 1
            try:
                trigger_select = int(frame_cfgs[0][5])
            except ValueError as exc:
                raise ValueError("frameCfg triggerSelect must be an integer") from exc
            if trigger_select != expected_trigger_select:
                raise ValueError(
                    f"{sync_mode} requires frameCfg triggerSelect="
                    f"{expected_trigger_select}, got {trigger_select}"
                )
            self._radar_trigger_config_validated = True
            self._radar_frame_period_s = radar_config.frame_period / 1000.0
            configured_capture_frames = int(
                radar_options.get("capture_frames", 100)
            )
            self._radar_continuous = configured_capture_frames == 0
            self._radar_capture_frames = (
                None if self._radar_continuous else configured_capture_frames
            )

        self._trigger_options: Optional[Dict[str, Any]] = None
        if trigger_kwargs is not None:
            trigger_options = dict(trigger_kwargs)
            trigger_options.pop("sync_dir", None)
            trigger_options.setdefault("binary_path", pathlib.Path("frame_trigger"))
            if self._radar_capture_frames is not None:
                trigger_options.setdefault("count", self._radar_capture_frames)
                if int(trigger_options["count"]) != self._radar_capture_frames:
                    raise ValueError(
                        "frame trigger count must equal radar capture_frames"
                    )
            if self._radar_frame_period_s is not None:
                maximum_frequency_hz = (
                    self.TRIGGER_RATE_FRACTION / self._radar_frame_period_s
                )
                trigger_options.setdefault("frequency_hz", maximum_frequency_hz)
            if "count" not in trigger_options or "frequency_hz" not in trigger_options:
                raise ValueError(
                    "trigger_kwargs require count and frequency_hz when radar "
                    "configuration metadata is unavailable"
                )
            self._validate_trigger_contract(
                count=trigger_options["count"],
                frequency_hz=trigger_options["frequency_hz"],
                initial_delay_ms=trigger_options.get("initial_delay_ms", 1000),
                expected_count=self._radar_capture_frames,
                radar_frame_period_s=self._radar_frame_period_s,
            )
            self._trigger_options = trigger_options

            # A slower external trigger extends the finite recording beyond the
            # nominal frameCfg schedule. Ensure RadarDCA's termination wait is
            # long enough unless the operator supplied a stricter timeout.
            if (
                radar_capture is None
                and self._radar_capture_frames is not None
                and "capture_timeout_s" not in radar_options
            ):
                trigger_count = int(trigger_options["count"])
                trigger_frequency = float(trigger_options["frequency_hz"])
                initial_delay_s = (
                    int(trigger_options.get("initial_delay_ms", 1000)) / 1000.0
                )
                final_frame_s = self._radar_frame_period_s or (
                    1.0 / trigger_frequency
                )
                radar_options["capture_timeout_s"] = (
                    initial_delay_s
                    + max(trigger_count - 1, 0) / trigger_frequency
                    + final_frame_s
                    + 15.0
                )

            # Construct the process wrapper now, before RadarDCA opens serial
            # ports or sockets, so every GPIO/count/timing option is validated
            # without touching hardware. The final sync directory is assigned
            # in prepare_capture().
            if trigger_capture is None:
                trigger_capture = FrameTriggerProcess(
                    sync_dir=pathlib.Path("."),
                    **trigger_options,
                )

        if trigger_capture is not None:
            trigger_count = getattr(trigger_capture, "count", None)
            trigger_frequency = getattr(trigger_capture, "frequency_hz", None)
            trigger_initial_delay = getattr(
                trigger_capture, "initial_delay_ms", None
            )
            if trigger_count is not None or trigger_frequency is not None:
                if trigger_count is None or trigger_frequency is None:
                    raise ValueError(
                        "injected frame trigger must expose both count and "
                        "frequency_hz when either field is exposed"
                    )
                self._validate_trigger_contract(
                    count=trigger_count,
                    frequency_hz=trigger_frequency,
                    initial_delay_ms=trigger_initial_delay,
                    expected_count=self._radar_capture_frames,
                    radar_frame_period_s=self._radar_frame_period_s,
                )

        if radar_capture is None:
            if radar_kwargs is None:
                raise ValueError(
                    "radar_kwargs are required when radar_capture is not injected"
                )
            radar_options.setdefault("init_capture_hw", init_capture_hw)
            self.radar_capture = RadarDCA(hw_name="radar", **radar_options)
            self._initialized = bool(init_capture_hw)
        else:
            self.radar_capture = radar_capture
            # Injected objects are assumed to have completed their own mock or
            # hardware initialization; this avoids an unexpected side effect in
            # constructor-driven unit tests.
            self._initialized = True

        self.trigger_capture = trigger_capture

        self._state = "initialized" if self._initialized else "new"
        self._closed = False
        self._events: List[Dict[str, Any]] = []
        self._adxl_summary: Optional[Dict[str, Any]] = None
        self._trigger_summary: Optional[Any] = None
        self._radar_prepared = False
        self._radar_started = False
        self._adxl_started = False
        self._trigger_started = False
        self._radar_finalized = False
        self._adxl_finalized = False
        self._radar_algorithm_manifest: Optional[pathlib.Path] = None
        self._adxl_algorithm_manifest: Optional[pathlib.Path] = None
        self._sync_timeline_exported = False

        self._radar_dir: Optional[pathlib.Path] = None
        self._adxl_dir: Optional[pathlib.Path] = None
        self._sync_dir: Optional[pathlib.Path] = None

    @property
    def state(self) -> str:
        return self._state

    @staticmethod
    def _optional_nonnegative_integer(value: Any, label: str) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label} must be a nonnegative integer or null")
        return value

    def _require_state(self, action: str, allowed: Sequence[str]) -> None:
        if self._state not in allowed:
            expected = ", ".join(repr(item) for item in allowed)
            raise RuntimeError(
                f"cannot {action} while synchronized capture state is "
                f"{self._state!r}; expected {expected}"
            )

    def _event(self, name: str, **details: Any) -> Dict[str, Any]:
        wall_ns = int(self._wall_time_ns())
        event: Dict[str, Any] = {
            "name": name,
            "monotonic_ns": int(self._monotonic_ns()),
            "wall_time_ns": wall_ns,
            "wall_time_utc": datetime.datetime.fromtimestamp(
                wall_ns / 1_000_000_000,
                tz=datetime.timezone.utc,
            ).isoformat(),
        }
        if details:
            event["details"] = self._json_value(details)
        self._events.append(event)
        return event

    @classmethod
    def _json_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, pathlib.Path):
            return str(value)
        if isinstance(value, Mapping):
            return {str(key): cls._json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._json_value(item) for item in value]
        return str(value)

    @classmethod
    def _atomic_write_json(cls, path: pathlib.Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(
                cls._json_value(payload),
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)

    @staticmethod
    def _call_start(component: Any, output_dir: pathlib.Path) -> Any:
        method = getattr(component, "start", None)
        if not callable(method):
            raise TypeError(f"{type(component).__name__} does not provide start()")
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            return method(output_dir)
        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.VAR_POSITIONAL,
            )
        ]
        if positional:
            return method(output_dir)
        return method()

    @classmethod
    def _validate_trigger_contract(
        cls,
        *,
        count: Any,
        frequency_hz: Any,
        initial_delay_ms: Any,
        expected_count: Optional[int],
        radar_frame_period_s: Optional[float],
    ) -> None:
        if isinstance(count, bool):
            raise ValueError("frame trigger count must be a positive integer")
        try:
            parsed_count = int(count)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "frame trigger count must be a positive integer"
            ) from exc
        if parsed_count <= 0 or parsed_count != count:
            raise ValueError("frame trigger count must be a positive integer")
        if expected_count is not None and parsed_count != expected_count:
            raise ValueError("frame trigger count must equal radar capture_frames")

        if isinstance(frequency_hz, bool):
            raise ValueError("frame trigger frequency_hz must be finite and positive")
        try:
            parsed_frequency_hz = float(frequency_hz)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "frame trigger frequency_hz must be finite and positive"
            ) from exc
        if not math.isfinite(parsed_frequency_hz) or parsed_frequency_hz <= 0:
            raise ValueError("frame trigger frequency_hz must be finite and positive")

        if initial_delay_ms is not None:
            if isinstance(initial_delay_ms, bool) or not isinstance(
                initial_delay_ms, int
            ):
                raise ValueError(
                    "frame-trigger initial_delay_ms must be a non-negative integer"
                )
            if initial_delay_ms < 0:
                raise ValueError(
                    "frame-trigger initial_delay_ms must be a non-negative integer"
                )
            if initial_delay_ms >= cls.DCA_NO_LVDS_GUARD_S * 1000.0:
                raise ValueError(
                    "frame-trigger initial_delay_ms must stay below 5000 so "
                    "DCA1000 retains a conservative margin from its roughly 10 s "
                    "no-LVDS timeout"
                )

        trigger_period_s = 1.0 / parsed_frequency_hz
        if trigger_period_s >= cls.DCA_NO_LVDS_GUARD_S:
            raise ValueError(
                "frame-trigger period must stay below 5 s to preserve a "
                "conservative margin from the DCA1000 roughly 10 s no-LVDS "
                "timeout"
            )
        if radar_frame_period_s is not None:
            maximum_frequency_hz = (
                cls.TRIGGER_RATE_FRACTION / radar_frame_period_s
            )
            if parsed_frequency_hz > maximum_frequency_hz and not math.isclose(
                parsed_frequency_hz,
                maximum_frequency_hz,
                rel_tol=1e-9,
                abs_tol=1e-12,
            ):
                raise ValueError(
                    "frame trigger frequency must not exceed 90% of the "
                    "configured radar frame rate"
                )

    @staticmethod
    def _component_value(component: Any, name: str) -> Any:
        value = getattr(component, name, None)
        if callable(value):
            value = value()
        return value

    def _run_with_adxl_supervision(
        self,
        operation: Callable[[], Any],
        *,
        wait_label: str,
        interrupt: Callable[[], Optional[str]],
    ) -> Any:
        """Run one blocking capture wait while polling the ADXL child.

        The blocking radar/trigger API runs in a daemon worker so this thread can
        continue checking the native ADXL collector.  If that collector exits,
        the active wait is interrupted first; the caller's existing failure path
        then unwinds the remaining resources in reverse order and writes the
        failed manifest.
        """

        check_running = getattr(self.adxl_capture, "check_running", None)
        if not callable(check_running):
            return operation()

        completed = threading.Event()
        outcome: Dict[str, Any] = {}

        def run_operation() -> None:
            try:
                outcome["result"] = operation()
            except BaseException as exc:
                outcome["error"] = exc
            finally:
                completed.set()

        worker = threading.Thread(
            target=run_operation,
            name=f"synchronized-{wait_label}",
            daemon=True,
        )
        worker.start()

        adxl_error: Optional[BaseException] = None
        while not completed.wait(self.ADXL_SUPERVISION_INTERVAL_S):
            try:
                check_running()
            except BaseException as exc:
                adxl_error = exc
                break

        if adxl_error is not None:
            interrupt_error = interrupt()
            stopped = completed.wait(self.ADXL_SUPERVISION_ABORT_TIMEOUT_S)
            self._event(
                "adxl_runtime_failure",
                wait=wait_label,
                error_type=type(adxl_error).__name__,
                error_message=str(adxl_error),
                interrupt_error=interrupt_error,
                blocking_operation_stopped=stopped,
            )
            details = f"ADXL355 collector failed during {wait_label}: {adxl_error}"
            if interrupt_error:
                details += f"; {interrupt_error}"
            if not stopped:
                details += "; blocking capture operation did not stop after abort"
            raise RuntimeError(details) from adxl_error

        worker.join()
        error = outcome.get("error")
        if isinstance(error, BaseException):
            raise error
        return outcome.get("result")

    def _interrupt_trigger_wait(self) -> Optional[str]:
        error = self._abort_component(
            self.trigger_capture,
            ("abort", "abort_capture"),
            "trigger",
        )
        if error is None:
            self._trigger_started = False
        return error

    def _interrupt_radar_wait(self) -> Optional[str]:
        error = self._abort_component(
            self.radar_capture,
            ("abort_capture", "abort"),
            "radar",
        )
        if error is None:
            self._radar_started = False
            self._radar_prepared = False
        return error

    def _require_directories(self) -> None:
        if self.base_path is None:
            raise RuntimeError("synchronized capture base_path is not set")
        if self._radar_dir is None or self._adxl_dir is None or self._sync_dir is None:
            raise RuntimeError("synchronized capture directories are not prepared")

    def _copy_fusion_calibration(self) -> None:
        if self._fusion_calibration_source is None:
            return
        self._require_directories()
        destination = self._sync_dir / "fusion_calibration.json"  # type: ignore[operator]
        temporary = destination.with_name(destination.name + ".tmp")
        with self._fusion_calibration_source.open("rb") as source, temporary.open(
            "wb"
        ) as target:
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(destination)
        self._fusion_calibration_copied = True

    def init_capture_hw(self) -> None:
        self._require_state("initialize hardware", ("new",))
        initialize = getattr(self.radar_capture, "init_capture_hw", None)
        if not callable(initialize):
            raise TypeError("radar_capture does not provide init_capture_hw()")
        initialize()
        self._initialized = True
        self._state = "initialized"

    def prepare_capture(self) -> None:
        self._require_state("prepare capture", ("initialized",))
        if self.base_path is None:
            raise RuntimeError("synchronized capture base_path is not set")

        self._radar_dir = self.base_path / self.RADAR_DIRECTORY
        self._adxl_dir = self.base_path / self.ADXL_DIRECTORY
        self._sync_dir = self.base_path / self.SYNC_DIRECTORY
        for directory in (self._radar_dir, self._adxl_dir, self._sync_dir):
            directory.mkdir(parents=True, exist_ok=True)
        # Bind the diagnostic/configuration path before starting ADXL. If the
        # accelerometer fails during pre-roll, Capture's failure cleanup can
        # still persist the untouched radar/DCA configuration without a
        # secondary "Base path is not set" error.
        self.radar_capture.base_path = self._radar_dir

        if self.sync_mode == "hardware_trigger":
            if self.trigger_capture is None:
                raise RuntimeError("frame-trigger process was not initialized")
            if hasattr(self.trigger_capture, "sync_dir"):
                self.trigger_capture.sync_dir = self._sync_dir

        self._event("prepare_begin")
        try:
            self._copy_fusion_calibration()
            if self._fusion_value_calibration is not None:
                self._event(
                    "fusion_calibration_copied",
                    calibration_id=self._fusion_value_calibration.calibration_id,
                )
            self._adxl_started = True
            self._event("adxl_start_begin")
            ready = self._call_start(self.adxl_capture, self._adxl_dir)
            self._event("adxl_ready", ready=ready)

            self._event("pre_roll_begin", duration_s=self.pre_roll_s)
            if self.pre_roll_s:
                self._sleep(self.pre_roll_s)
            self._event("pre_roll_complete", duration_s=self.pre_roll_s)

            check_running = getattr(self.adxl_capture, "check_running", None)
            if callable(check_running):
                self._event("adxl_running_check_begin")
                running = check_running()
                self._event("adxl_running_check_complete", result=running)

            # Arm DCA/tcpdump only after pre-roll. RadarDCA's termination
            # catcher must not sit through the accelerometer warm-up window and
            # mistake a pre-start "no LVDS" status for finite-capture completion.
            self._radar_prepared = True
            self._event("radar_prepare_begin")
            self.radar_capture.prepare_capture()
            self._event("radar_prepare_complete")
        except BaseException as exc:
            self._handle_failure("prepare_capture", exc)
            raise
        self._state = "prepared"
        self._event("prepare_complete")

    def start_capture(self) -> None:
        self._require_state("start capture", ("prepared",))
        self._require_directories()
        try:
            # DCA/tcpdump preparation can take long enough for a collector
            # failure to occur after the pre-roll check. Re-check immediately
            # before sensorStart so a dead ADXL process never starts the radar.
            check_running = getattr(self.adxl_capture, "check_running", None)
            if callable(check_running):
                self._event("adxl_pre_sensor_start_check_begin")
                running = check_running()
                self._event(
                    "adxl_pre_sensor_start_check_complete",
                    result=running,
                )

            self._radar_started = True
            self._event("radar_sensor_start_send_before")
            self.radar_capture.start_capture()
            self._event("radar_sensor_start_return_after")

            if self.sync_mode == "hardware_trigger":
                # Set the flag before calling into the backend because start()
                # may partially configure GPIO before reporting an error.
                self._trigger_started = True
                self._event("trigger_start_begin")
                trigger_result = self._call_start(
                    self.trigger_capture,
                    self._sync_dir,  # type: ignore[arg-type]
                )
                self._event("trigger_start_return_after", result=trigger_result)
        except BaseException as exc:
            self._handle_failure("start_capture", exc)
            raise
        self._state = "started"
        self._event("capture_started")

    def stop_capture(self) -> None:
        self._require_state("stop capture", ("started",))
        try:
            if self.sync_mode == "hardware_trigger":
                self._event("trigger_wait_begin")
                result = self._run_with_adxl_supervision(
                    self.trigger_capture.wait,
                    wait_label="frame-trigger wait",
                    interrupt=self._interrupt_trigger_wait,
                )
                self._trigger_started = False
                self._trigger_summary = self._component_value(
                    self.trigger_capture, "summary"
                )
                if self._trigger_summary is None and isinstance(result, Mapping):
                    self._trigger_summary = result
                self._event(
                    "trigger_wait_complete",
                    summary=self._trigger_summary,
                )

                if self._radar_continuous:
                    request_stop = getattr(
                        self.radar_capture,
                        "request_continuous_stop",
                        None,
                    )
                    if not callable(request_stop):
                        raise RuntimeError(
                            "continuous hardware-trigger capture requires the "
                            "radar backend to support request_continuous_stop()"
                        )
                    self._event("radar_continuous_stop_request_begin")
                    request_stop()
                    self._event("radar_continuous_stop_request_complete")

            self._event("radar_stop_begin")
            self._run_with_adxl_supervision(
                self.radar_capture.stop_capture,
                wait_label="radar completion wait",
                interrupt=self._interrupt_radar_wait,
            )
            self._radar_started = False
            self._radar_prepared = False
            self._event("radar_stop_complete")

            self._event("post_roll_begin", duration_s=self.post_roll_s)
            if self.post_roll_s:
                self._sleep(self.post_roll_s)
            self._event("post_roll_complete", duration_s=self.post_roll_s)

            self._event("adxl_stop_begin")
            result = self.adxl_capture.stop()
            self._adxl_started = False
            if isinstance(result, Mapping):
                self._adxl_summary = dict(result)
            else:
                summary = self._component_value(self.adxl_capture, "summary")
                if isinstance(summary, Mapping):
                    self._adxl_summary = dict(summary)
            self._event("adxl_stop_complete", summary=self._adxl_summary)
        except BaseException as exc:
            self._handle_failure("stop_capture", exc)
            raise
        self._state = "stopped"
        self._event("capture_stopped")

    def _abort_component(
        self,
        component: Any,
        method_names: Sequence[str],
        label: str,
    ) -> Optional[str]:
        for name in method_names:
            method = getattr(component, name, None)
            if callable(method):
                try:
                    method()
                except Exception as exc:
                    return f"{label} {name} failed: {exc}"
                return None
        return f"{label} does not provide any of {tuple(method_names)}"

    def _abort_resources(self) -> List[str]:
        errors: List[str] = []
        # Resource start order is ADXL, radar, trigger; unwind in reverse.
        if self._trigger_started and self.trigger_capture is not None:
            error = self._abort_component(
                self.trigger_capture, ("abort", "abort_capture"), "trigger"
            )
            if error:
                errors.append(error)
            self._trigger_started = False
        if self._radar_started or self._radar_prepared:
            error = self._abort_component(
                self.radar_capture, ("abort_capture", "abort"), "radar"
            )
            if error:
                errors.append(error)
            self._radar_started = False
            self._radar_prepared = False
        if self._adxl_started:
            error = self._abort_component(
                self.adxl_capture, ("abort", "abort_capture"), "ADXL355"
            )
            if error:
                errors.append(error)
            self._adxl_started = False
        return errors

    def _handle_failure(self, phase: str, error: BaseException) -> None:
        self._event(
            "capture_failure",
            phase=phase,
            error_type=type(error).__name__,
            error_message=str(error),
        )
        cleanup_errors = self._abort_resources()
        self._state = "aborted"
        self._event("abort_complete", cleanup_errors=cleanup_errors)
        try:
            self._write_manifest(
                status="failed",
                error={
                    "phase": phase,
                    "type": type(error).__name__,
                    "message": str(error),
                    "cleanup_errors": cleanup_errors,
                },
            )
        except Exception:
            # The original capture exception remains authoritative.  A .tmp
            # file, if any, is intentionally retained as additional evidence.
            pass

    def abort_capture(self) -> None:
        if self._state in ("aborted", "closed", "finalized"):
            return
        self._event("abort_begin", prior_state=self._state)
        errors = self._abort_resources()
        self._state = "aborted"
        self._event("abort_complete", cleanup_errors=errors)
        try:
            self._write_manifest(
                status="failed",
                error={
                    "phase": "abort_capture",
                    "type": "CaptureAborted",
                    "message": "capture was aborted before finalization",
                    "cleanup_errors": errors,
                },
            )
        except Exception:
            pass
        if errors:
            raise RuntimeError("; ".join(errors))

    def _component_config(self, component: Any) -> Any:
        config = self._component_value(component, "config")
        if config is None:
            return {"implementation": type(component).__name__}
        return config

    def dump_config(self) -> None:
        self._require_state(
            "dump configuration",
            ("stopped", "aborted", "finalized"),
        )
        if self.base_path is None:
            raise RuntimeError("synchronized capture base_path is not set")
        if self._radar_dir is None:
            self._radar_dir = self.base_path / self.RADAR_DIRECTORY
            self._radar_dir.mkdir(parents=True, exist_ok=True)
            self.radar_capture.base_path = self._radar_dir
        if self._adxl_dir is None:
            self._adxl_dir = self.base_path / self.ADXL_DIRECTORY
            self._adxl_dir.mkdir(parents=True, exist_ok=True)
        if self._sync_dir is None:
            self._sync_dir = self.base_path / self.SYNC_DIRECTORY
            self._sync_dir.mkdir(parents=True, exist_ok=True)

        errors: List[str] = []
        try:
            self.radar_capture.dump_config()
        except Exception as exc:
            errors.append(f"radar config dump failed: {exc}")

        try:
            self._atomic_write_json(
                self._adxl_dir / Adxl355Process.CONFIG_FILENAME,
                self._component_config(self.adxl_capture),
            )
        except Exception as exc:
            errors.append(f"ADXL355 config dump failed: {exc}")

        sync_config = {
            "schema_version": self.SCHEMA_VERSION,
            "sync_mode": self.sync_mode,
            "timestamp_quality": self._timestamp_quality(),
            "hardware_validated": self.hardware_validated,
            "radar_trigger_config_validated": (
                self._radar_trigger_config_validated
            ),
            "pre_roll_s": self.pre_roll_s,
            "post_roll_s": self.post_roll_s,
            "export_adxl_algorithm_data": self.export_adxl_algorithm_data,
            "export_sync_timeline": self.export_sync_timeline,
            "clock": self._clock_manifest(),
            "trigger_edge_uncertainty_ns": self._trigger_edge_uncertainty_ns,
            "radar_trigger_latency_ns": self._radar_trigger_latency_ns,
            "radar_trigger_latency_uncertainty_ns": (
                self._radar_trigger_latency_uncertainty_ns
            ),
            "radar_trigger_latency_source": self._radar_trigger_latency_source,
            "radar_trigger_latency_calibrated": self._radar_latency_calibrated,
            "adxl_filter_group_delay_uncertainty_ns": (
                self._adxl_filter_group_delay_uncertainty_ns
            ),
        }
        if self._fusion_value_calibration is not None:
            sync_config["fusion_calibration_id"] = (
                self._fusion_value_calibration.calibration_id
            )
        if self.trigger_capture is not None:
            sync_config["trigger"] = self._component_config(self.trigger_capture)
        try:
            self._atomic_write_json(
                self._sync_dir / self.SYNC_CONFIG_FILENAME,
                sync_config,
            )
        except Exception as exc:
            errors.append(f"sync config dump failed: {exc}")

        if errors:
            raise RuntimeError("; ".join(errors))

    def _validated_adxl_summary(self) -> Dict[str, Any]:
        validator = getattr(self.adxl_capture, "validate_summary", None)
        if callable(validator):
            summary = validator()
        else:
            summary = self._adxl_summary
            if summary is None:
                summary = self._component_value(self.adxl_capture, "summary")
            if not isinstance(summary, Mapping):
                raise RuntimeError("ADXL355 capture did not provide a summary mapping")
            summary = Adxl355Process.validate_summary_payload(summary)
        if not isinstance(summary, Mapping):
            raise RuntimeError("ADXL355 summary validator did not return a mapping")
        validated = Adxl355Process.validate_summary_payload(summary)
        self._adxl_summary = dict(validated)
        return dict(validated)

    def _radar_timeline_dimensions(self) -> tuple[int, int]:
        """Return decoded frame count and nominal frame period in nanoseconds."""

        self._require_directories()
        radar_manifest = (
            self._radar_dir  # type: ignore[operator]
            / RadarDCA.ALGORITHM_INPUT_DIRECTORY
            / RADAR_ALGORITHM_MANIFEST_FILENAME
        )
        if not radar_manifest.is_file():
            raise RuntimeError(
                "cannot export synchronized timeline without the decoded radar "
                "algorithm manifest; configuration frame counts are not accepted"
            )
        try:
            payload = json.loads(radar_manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                f"cannot read decoded radar algorithm manifest: {exc}"
            ) from exc
        if not isinstance(payload, Mapping):
            raise RuntimeError("radar algorithm manifest must be a JSON object")
        if (
            payload.get("schema") != RADAR_ALGORITHM_SCHEMA_NAME
            or payload.get("schema_version") != RADAR_ALGORITHM_SCHEMA_VERSION
        ):
            raise RuntimeError("radar algorithm manifest has an unsupported schema")
        packet_integrity = payload.get("packet_integrity")
        if not isinstance(packet_integrity, Mapping) or (
            packet_integrity.get("complete") is not True
        ):
            raise RuntimeError(
                "radar algorithm manifest does not certify complete packet integrity"
            )
        radar = payload.get("radar")
        if not isinstance(radar, Mapping):
            raise RuntimeError("radar algorithm manifest has no radar metadata")
        frames_value = radar.get("frames")
        frame_period_value = radar.get("frame_period_s")
        if (
            isinstance(frames_value, bool)
            or not isinstance(frames_value, int)
            or isinstance(frame_period_value, bool)
            or not isinstance(frame_period_value, (int, float))
        ):
            raise RuntimeError("radar frame count/period is invalid")
        frames = frames_value
        frame_period_s = float(frame_period_value)
        if frames <= 0 or not math.isfinite(frame_period_s) or frame_period_s <= 0:
            raise RuntimeError("radar frame count/period is invalid")
        arrays = payload.get("arrays")
        adc_cube = arrays.get("adc_cube") if isinstance(arrays, Mapping) else None
        adc_shape = adc_cube.get("shape") if isinstance(adc_cube, Mapping) else None
        if (
            not isinstance(adc_shape, list)
            or not adc_shape
            or isinstance(adc_shape[0], bool)
            or not isinstance(adc_shape[0], int)
            or adc_shape[0] != frames
        ):
            raise RuntimeError(
                "radar algorithm manifest ADC cube disagrees with radar frame count"
            )
        self._radar_algorithm_manifest = radar_manifest
        frame_period_ns = int(round(frame_period_s * 1_000_000_000.0))
        if frame_period_ns <= 0:
            raise RuntimeError("radar frame period has no positive nanosecond value")
        return frames, frame_period_ns

    def _single_event(self, name: str) -> Mapping[str, Any]:
        matches = [event for event in self._events if event.get("name") == name]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected exactly one synchronized event {name!r}, got {len(matches)}"
            )
        return matches[0]

    def _hardware_frame_times(
        self,
        frames: int,
        frame_period_ns: int,
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        if not isinstance(self._trigger_summary, Mapping):
            raise RuntimeError("hardware trigger has no validated summary")
        quality = self._trigger_summary.get("timestamp_quality")
        if quality not in ("kernel_loopback_edge", "userspace_set_completed"):
            raise RuntimeError(f"unsupported frame-trigger timestamp quality {quality!r}")
        if (
            int(self._trigger_summary.get("requested_count", -1)) != frames
            or int(self._trigger_summary.get("emitted_count", -1)) != frames
        ):
            raise RuntimeError(
                "frame-trigger summary count disagrees with decoded radar frames"
            )
        self._require_directories()
        events_filename = getattr(
            self.trigger_capture,
            "EVENTS_FILENAME",
            FrameTriggerProcess.EVENTS_FILENAME,
        )
        events_path = self._sync_dir / events_filename  # type: ignore[operator]
        if not events_path.is_file():
            raise FileNotFoundError(events_path)
        timestamps: List[int] = []
        with events_path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            expected_fields = {
                "sequence",
                "scheduled_monotonic_ns",
                "asserted_monotonic_ns",
                "deasserted_monotonic_ns",
                "loopback_monotonic_ns",
            }
            if set(reader.fieldnames or ()) != expected_fields:
                raise RuntimeError("frame-trigger CSV has an unexpected schema")
            for expected_sequence, row in enumerate(reader):
                if int(row["sequence"]) != expected_sequence:
                    raise RuntimeError("frame-trigger CSV sequence is not contiguous")
                field = (
                    "loopback_monotonic_ns"
                    if quality == "kernel_loopback_edge"
                    else "asserted_monotonic_ns"
                )
                raw_timestamp = row.get(field, "")
                if raw_timestamp is None or not raw_timestamp.strip():
                    raise RuntimeError(
                        f"frame-trigger CSV is missing {field} for frame "
                        f"{expected_sequence}"
                    )
                timestamps.append(int(raw_timestamp))
        if len(timestamps) != frames:
            raise RuntimeError(
                "frame-trigger event count disagrees with decoded radar frames"
            )
        array = np.asarray(timestamps, dtype=np.int64)
        if np.any(array <= 0) or (array.size > 1 and np.any(np.diff(array) <= 0)):
            raise RuntimeError("frame-trigger timestamps are not positive/increasing")
        if array.size > 1 and np.any(np.diff(array) < frame_period_ns):
            raise RuntimeError(
                "measured frame-trigger interval is shorter than radar frame period"
            )
        if quality == "kernel_loopback_edge":
            edge_observation = "physical_loopback_input"
            semantics = (
                "Pi kernel timestamp of the observed GPIO loopback rising edge; "
                "radar trigger latency and ADC timing are not yet calibrated"
            )
        else:
            edge_observation = "userspace_gpio_set_completion"
            semantics = (
                "Pi userspace timestamp recorded after the GPIO set request "
                "completed; this is not an observation of the physical SYNC_IN "
                "edge, radar response, or ADC timing"
            )
        return array, {
            "source": quality,
            "edge_observation": edge_observation,
            "is_measured_radar_frame_start": False,
            "semantics": semantics,
        }

    def _software_frame_times(
        self,
        frames: int,
        frame_period_ns: int,
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        before = int(
            self._single_event("radar_sensor_start_send_before")["monotonic_ns"]
        )
        after = int(
            self._single_event("radar_sensor_start_return_after")["monotonic_ns"]
        )
        if after < before:
            raise RuntimeError("sensorStart monotonic-time bracket is inverted")
        origin = before + (after - before) // 2
        indices = np.arange(frames, dtype=np.int64)
        array = origin + indices * np.int64(frame_period_ns)
        return array, {
            "source": "sensor_start_bracket_midpoint_plus_nominal_period",
            "is_measured_radar_frame_start": False,
            "sensor_start_before_monotonic_ns": before,
            "sensor_start_after_monotonic_ns": after,
            "bracket_width_ns": after - before,
            "bracket_midpoint_uncertainty_ns": (after - before + 1) // 2,
            "semantics": (
                "Estimated only; includes unknown firmware start latency and "
                "unmeasured radar-clock drift"
            ),
        }

    def _export_radar_timeline(self) -> pathlib.Path:
        frames, frame_period_ns = self._radar_timeline_dimensions()
        if self.sync_mode == "hardware_trigger":
            frame_times, provenance = self._hardware_frame_times(
                frames,
                frame_period_ns,
            )
        else:
            frame_times, provenance = self._software_frame_times(
                frames,
                frame_period_ns,
            )
        self._require_directories()
        output = self._sync_dir / self.RADAR_TIMELINE_FILENAME  # type: ignore[operator]
        temporary = output.with_name(output.name + ".tmp")
        with temporary.open("wb") as stream:
            np.save(stream, frame_times, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(output)
        timeline_manifest = {
            "schema_version": 1,
            "status": "complete",
            "sync_mode": self.sync_mode,
            "timestamp_quality": self._timestamp_quality(),
            "hardware_validated": self.hardware_validated,
            "clock": "CLOCK_MONOTONIC",
            "unit": "nanoseconds",
            "frame_count": frames,
            "nominal_frame_period_ns": frame_period_ns,
            "radar_algorithm_manifest": (
                f"../{self.RADAR_DIRECTORY}/"
                f"{RadarDCA.ALGORITHM_INPUT_DIRECTORY}/"
                f"{RADAR_ALGORITHM_MANIFEST_FILENAME}"
            ),
            "radar_packet_integrity_complete": True,
            "array": {
                "file": self.RADAR_TIMELINE_FILENAME,
                "dtype": "int64",
                "shape": [frames],
                "axes": ["radar_frame"],
            },
            "provenance": provenance,
            "warning": (
                "These values reference radar trigger/start timing, not ADC "
                "sample time. Calibrate radar latency before precision claims."
            ),
        }
        manifest_path = self._sync_dir / self.TIMELINE_MANIFEST_FILENAME  # type: ignore[operator]
        self._atomic_write_json(manifest_path, timeline_manifest)
        self._sync_timeline_exported = True
        return manifest_path

    def finalize_capture(self) -> None:
        self._require_state("finalize capture", ("stopped",))
        try:
            self.radar_capture.finalize_capture()
            self._radar_finalized = True
            self._event("radar_finalize_complete")
            self._validated_adxl_summary()
            self._event("adxl_validation_complete")
            if self.export_adxl_algorithm_data:
                self._require_directories()
                self._adxl_algorithm_manifest = export_adxl355_input(
                    self._adxl_dir / Adxl355Process.RAW_FILENAME,  # type: ignore[operator]
                    self._adxl_dir / Adxl355Process.SUMMARY_FILENAME,  # type: ignore[operator]
                    self._adxl_dir / Adxl355Process.ALGORITHM_INPUT_DIRECTORY,  # type: ignore[operator]
                )
                self._adxl_finalized = True
                self._event(
                    "adxl_finalize_complete",
                    manifest=self._adxl_algorithm_manifest,
                )
            if self.export_sync_timeline:
                timeline_manifest = self._export_radar_timeline()
                self._event(
                    "sync_timeline_finalize_complete",
                    manifest=timeline_manifest,
                )
            self._write_manifest(status="complete")
        except BaseException as exc:
            self._handle_failure("finalize_capture", exc)
            raise
        self._state = "finalized"

    def _timestamp_quality(self) -> str:
        if self.sync_mode == "hardware_trigger":
            if isinstance(self._trigger_summary, Mapping):
                quality = self._trigger_summary.get("timestamp_quality")
                if isinstance(quality, str):
                    return quality
            return "trigger_edge_pending_validation"
        return "sensor_start_bracket_estimate"

    @staticmethod
    def _clock_manifest() -> Dict[str, Any]:
        return {
            "alignment_clock": "CLOCK_MONOTONIC",
            "unit": "nanoseconds",
            "wall_clock": "CLOCK_REALTIME",
            "wall_time_used_for_alignment": False,
        }

    def _uncertainty_manifest(self) -> Dict[str, Any]:
        if self.sync_mode == "hardware_trigger":
            adxl_delay = None
            adxl_delay_calibrated = False
            adxl_delay_source = None
            if isinstance(self._adxl_summary, Mapping):
                adxl_delay = self._adxl_summary.get("group_delay_ns")
                adxl_delay_calibrated = bool(
                    self._adxl_summary.get("group_delay_calibrated", False)
                )
                adxl_delay_source = self._adxl_summary.get("group_delay_source")
            fully_characterized = bool(
                self.hardware_validated
                and self._trigger_edge_uncertainty_ns is not None
                and self._radar_latency_calibrated
                and adxl_delay_calibrated
                and isinstance(adxl_delay_source, str)
                and bool(adxl_delay_source.strip())
                and self._adxl_filter_group_delay_uncertainty_ns is not None
                and self._fusion_value_calibration is not None
                and self._fusion_value_calibration.validated
            )
            return {
                "status": (
                    "characterized"
                    if fully_characterized
                    else (
                        "not_characterized"
                        if self.hardware_validated
                        else "hardware_not_bench_validated"
                    )
                ),
                "trigger_edge_uncertainty_ns": self._trigger_edge_uncertainty_ns,
                "radar_trigger_latency_ns": self._radar_trigger_latency_ns,
                "radar_trigger_latency_uncertainty_ns": (
                    self._radar_trigger_latency_uncertainty_ns
                ),
                "radar_trigger_latency_calibrated": (
                    self._radar_latency_calibrated
                ),
                "radar_trigger_latency_source": (
                    self._radar_trigger_latency_source
                ),
                "adxl_filter_group_delay_ns": adxl_delay,
                "adxl_filter_group_delay_calibrated": adxl_delay_calibrated,
                "adxl_filter_group_delay_source": adxl_delay_source,
                "adxl_filter_group_delay_uncertainty_ns": (
                    self._adxl_filter_group_delay_uncertainty_ns
                ),
            }
        return {
            "status": "not_characterized",
            "initial_offset_ns": None,
            "clock_drift_ppm": None,
            "packet_receive_time_is_frame_start": False,
            "radar_frame_time_source": (
                "estimated from the sensorStart monotonic-time bracket and "
                "the decoded radar algorithm manifest's nominal frame period"
            ),
        }

    def _files_manifest(self) -> Dict[str, Any]:
        files: Dict[str, Dict[str, Any]] = {
            "radar": {
                "directory": self.RADAR_DIRECTORY,
                "pcap": f"{self.RADAR_DIRECTORY}/{RadarDCA.PCAP_OUTPUT_FILENAME}",
                "radar_config": (
                    f"{self.RADAR_DIRECTORY}/{RadarDCA.RADAR_CONFIG_FILENAME}"
                ),
                "dca_config": (
                    f"{self.RADAR_DIRECTORY}/{RadarDCA.DCA_CONFIG_FILENAME}"
                ),
            },
            "adxl355": {
                "directory": self.ADXL_DIRECTORY,
                "raw": f"{self.ADXL_DIRECTORY}/{Adxl355Process.RAW_FILENAME}",
                "summary": (
                    f"{self.ADXL_DIRECTORY}/{Adxl355Process.SUMMARY_FILENAME}"
                ),
                "ready": f"{self.ADXL_DIRECTORY}/{Adxl355Process.READY_FILENAME}",
                "config": f"{self.ADXL_DIRECTORY}/{Adxl355Process.CONFIG_FILENAME}",
            },
            "sync": {
                "directory": self.SYNC_DIRECTORY,
                "config": f"{self.SYNC_DIRECTORY}/{self.SYNC_CONFIG_FILENAME}",
                "manifest": f"{self.SYNC_DIRECTORY}/{self.MANIFEST_FILENAME}",
            },
        }
        if self._radar_algorithm_requested:
            files["radar"].update(
                {
                    "algorithm_input_directory": (
                        f"{self.RADAR_DIRECTORY}/"
                        f"{RadarDCA.ALGORITHM_INPUT_DIRECTORY}"
                    ),
                    "algorithm_input_manifest": (
                        f"{self.RADAR_DIRECTORY}/"
                        f"{RadarDCA.ALGORITHM_INPUT_DIRECTORY}/"
                        f"{RADAR_ALGORITHM_MANIFEST_FILENAME}"
                    ),
                }
            )
        if self.export_adxl_algorithm_data:
            files["adxl355"].update(
                {
                    "algorithm_input_directory": (
                        f"{self.ADXL_DIRECTORY}/"
                        f"{Adxl355Process.ALGORITHM_INPUT_DIRECTORY}"
                    ),
                    "algorithm_input_manifest": (
                        f"{self.ADXL_DIRECTORY}/"
                        f"{Adxl355Process.ALGORITHM_INPUT_DIRECTORY}/manifest.json"
                    ),
                }
            )
        if self.export_sync_timeline:
            files["sync"].update(
                {
                    "radar_frame_monotonic_ns": (
                        f"{self.SYNC_DIRECTORY}/{self.RADAR_TIMELINE_FILENAME}"
                    ),
                    "timeline_manifest": (
                        f"{self.SYNC_DIRECTORY}/"
                        f"{self.TIMELINE_MANIFEST_FILENAME}"
                    ),
                }
            )
        if self._fusion_calibration_copied:
            files["sync"]["fusion_calibration"] = (
                f"{self.SYNC_DIRECTORY}/fusion_calibration.json"
            )
        if self.sync_mode == "hardware_trigger" and self.trigger_capture is not None:
            events_filename = getattr(
                self.trigger_capture,
                "EVENTS_FILENAME",
                "frame_trigger_events.csv",
            )
            summary_filename = getattr(
                self.trigger_capture,
                "SUMMARY_FILENAME",
                "frame_trigger_summary.json",
            )
            files["sync"]["trigger_events"] = (
                f"{self.SYNC_DIRECTORY}/{events_filename}"
            )
            files["sync"]["trigger_summary"] = (
                f"{self.SYNC_DIRECTORY}/{summary_filename}"
            )
        return files

    def _validation_manifest(self, status: str) -> Dict[str, Any]:
        return {
            "status": status,
            "radar_finalized": self._radar_finalized,
            "adxl355_finalized": self._adxl_finalized,
            "sync_timeline_exported": self._sync_timeline_exported,
            "adxl355": self._adxl_summary,
            "trigger": self._trigger_summary,
            "hardware_validated": self.hardware_validated,
            "radar_trigger_config_validated": (
                self._radar_trigger_config_validated
            ),
        }

    def _write_manifest(
        self,
        status: str,
        error: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if self.base_path is None:
            raise RuntimeError("synchronized capture base_path is not set")
        if self._sync_dir is None:
            self._sync_dir = self.base_path / self.SYNC_DIRECTORY
        quality = self._timestamp_quality()
        if self.sync_mode == "software_timestamp":
            radar_timestamp_semantics = (
                "estimated frame reference from the sensorStart bracket and "
                "decoded nominal period; not a packet receive timestamp"
            )
        elif quality == "kernel_loopback_edge":
            radar_timestamp_semantics = (
                "Pi kernel timestamp of an observed GPIO loopback rising edge; "
                "not the radar ADC sample time"
            )
        elif quality == "userspace_set_completed":
            radar_timestamp_semantics = (
                "Pi userspace timestamp after a GPIO set request completed; "
                "not an observed physical SYNC_IN edge or radar ADC sample time"
            )
        else:
            radar_timestamp_semantics = (
                "hardware trigger timing is pending a validated trigger summary"
            )
        payload: Dict[str, Any] = {
            "schema_version": self.SCHEMA_VERSION,
            "status": status,
            "sync_mode": self.sync_mode,
            "timestamp_quality": quality,
            "hardware_validated": self.hardware_validated,
            "clock": self._clock_manifest(),
            "pre_roll_s": self.pre_roll_s,
            "post_roll_s": self.post_roll_s,
            "path_base": "synchronized hardware directory",
            "events": list(self._events),
            "files": self._files_manifest(),
            "validation": self._validation_manifest(status),
            "uncertainty": self._uncertainty_manifest(),
            "timestamp_semantics": {
                "adxl355": "DRDY edge on the Pi CLOCK_MONOTONIC timeline",
                "radar": radar_timestamp_semantics,
                "pcap": (
                    "Ethernet packet receive time only; never radar frame_start"
                ),
                "pcap_is_frame_start": False,
            },
        }
        if error is not None:
            payload["error"] = dict(error)
        self._atomic_write_json(
            self._sync_dir / self.MANIFEST_FILENAME,
            payload,
        )

    def close(self) -> None:
        if self._closed:
            return
        errors: List[str] = []
        if self._state not in ("aborted", "finalized", "closed"):
            errors.extend(self._abort_resources())

        # Close in reverse construction/use order as well.
        for label, component in (
            ("trigger", self.trigger_capture),
            ("radar", self.radar_capture),
            ("ADXL355", self.adxl_capture),
        ):
            if component is None:
                continue
            close = getattr(component, "close", None)
            if not callable(close):
                continue
            try:
                close()
            except Exception as exc:
                errors.append(f"{label} close failed: {exc}")
        self._closed = True
        self._state = "closed"
        if errors:
            raise RuntimeError("; ".join(errors))
