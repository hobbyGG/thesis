"""Interactive operator recorder for the capture station.

The hardware is initialized and then held idle. Nothing is armed or recorded
until the operator presses Enter; a stop key ends the continuous capture early
and the partial recording is validated, exported and saved by the normal
capture lifecycle. One status line is rewritten in place (no scrolling).
"""

import json
import os
import pathlib
import select
import shutil
import sys
import termios
import threading
import time
import tty
from typing import Callable, Optional

import click
import numpy as np
import toml
from loguru import logger

from mmwavecapture.adxl355_input import (
    RAW_HEADER_BYTES,
    RAW_RECORD_BYTES,
    RECORD_DTYPE,
    SENSITIVITY_LSB_PER_G,
    STANDARD_GRAVITY_MPS2,
)
from mmwavecapture.capture import CaptureManager
from mmwavecapture.capture.adxl355 import Adxl355Process
from mmwavecapture.capture.radardca import RadarDCA
from mmwavecapture.capture.synchronized import SynchronizedRadarAdxl

REFRESH_S = 0.5
KEY_POLL_S = 0.1
START_KEYS = ("\r", "\n")
STOP_KEYS = ("s", "S", " ", "\x03")
CANCEL_KEYS = ("q", "Q", "\x03")


class _Cancelled(Exception):
    pass


def _size(path: pathlib.Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


class Meter:
    """Cheap live metrics from the files the capture is already writing."""

    def __init__(self, base: pathlib.Path, range_g: int, odr_hz: int):
        self._pcap = base / SynchronizedRadarAdxl.RADAR_DIRECTORY / RadarDCA.PCAP_OUTPUT_FILENAME
        self._raw = base / SynchronizedRadarAdxl.ADXL_DIRECTORY / Adxl355Process.RAW_FILENAME
        self._mm_s2_per_lsb = (
            STANDARD_GRAVITY_MPS2 / SENSITIVITY_LSB_PER_G[range_g] * 1000.0
        )
        self._window = max(2, odr_hz // 2)
        self._last: Optional[tuple] = None

    def sample(self, now: float) -> dict:
        pcap_bytes = _size(self._pcap)
        samples = max(0, (_size(self._raw) - RAW_HEADER_BYTES) // RAW_RECORD_BYTES)
        reading = {
            "pcap_bytes": pcap_bytes,
            "samples": samples,
            "pcap_mb_s": None,
            "adxl_hz": None,
            "vibration_mm_s2": self._vibration(samples),
        }
        if self._last is not None and now > self._last[0]:
            dt = now - self._last[0]
            reading["pcap_mb_s"] = (pcap_bytes - self._last[1]) / dt / 1e6
            reading["adxl_hz"] = (samples - self._last[2]) / dt
        self._last = (now, pcap_bytes, samples)
        return reading

    def _vibration(self, samples: int) -> Optional[float]:
        # Peak deviation of the x axis (algorithm acceleration column 0) over
        # the most recent half second, with the static component removed.
        count = min(samples, self._window)
        if count < 2:
            return None
        tail = np.fromfile(
            self._raw,
            dtype=RECORD_DTYPE,
            count=count,
            offset=RAW_HEADER_BYTES + (samples - count) * RAW_RECORD_BYTES,
        )
        x = tail["x_raw"].astype(np.float64)
        return float(np.max(np.abs(x - np.mean(x))) * self._mm_s2_per_lsb)


def status_line(phase: str, elapsed: float, max_s: float, reading: dict, cols: int) -> str:
    def field(value, spec, unit):
        return "--" if value is None else format(value, spec) + unit

    mb = reading["pcap_bytes"] / 1e6
    rate = reading["pcap_mb_s"]
    radar = f"radar {mb:.1f}MB"
    if phase == "RECORDING" and rate is not None:
        radar += " STALL" if rate <= 0 else f" {rate:.1f}MB/s"
    parts = [
        f"{phase} {elapsed:.1f}/{max_s:.0f}s",
        radar,
        f"adxl {reading['samples']} {field(reading['adxl_hz'], '.0f', 'Hz')}",
        f"vib {field(reading['vibration_mm_s2'], '.1f', 'mm/s2')}",
    ]
    hint = {
        "READY": "Enter=start q=quit",
        "STARTING": "s=stop",
        "RECORDING": "s=stop+save",
        "SAVING": "do not unplug",
    }[phase]
    return (" | ".join(parts) + " | " + hint)[: max(cols - 1, 20)]


def _stop_phase(state: str) -> bool:
    return state in ("stopped", "aborted", "finalized", "closed")


def record(
    manager: CaptureManager,
    meter: Meter,
    max_s: float,
    read_key: Callable[[float], Optional[str]],
    out,
    cols: Callable[[], int] = lambda: shutil.get_terminal_size().columns,
) -> dict:
    """Drive one operator-controlled capture; return the outcome."""

    go = threading.Event()
    cancel = threading.Event()
    outcome: dict = {"cancelled": False, "error": None, "recording_s": 0.0}

    def before_start() -> None:
        while not go.wait(KEY_POLL_S):
            if cancel.is_set():
                raise _Cancelled
        if cancel.is_set():
            raise _Cancelled

    def work() -> None:
        try:
            manager.capture(before_start)
        except _Cancelled:
            outcome["cancelled"] = True
        except BaseException as exc:
            outcome["error"] = exc

    worker = threading.Thread(target=work, name="capture")
    worker.start()
    hardware = manager.hardware[0]

    started = False
    stop_pending = False
    stop_sent = False
    recording_since: Optional[float] = None
    reading = meter.sample(time.monotonic())
    last_draw = 0.0
    last_phase = ""

    while worker.is_alive():
        now = time.monotonic()
        state = hardware.state
        if not started:
            phase = "READY"
        elif state == "started":
            phase = "RECORDING"
            if recording_since is None:
                recording_since = now
        elif recording_since is not None or _stop_phase(state):
            phase = "SAVING"
            if recording_since is not None and not outcome["recording_s"]:
                outcome["recording_s"] = now - recording_since
        else:
            phase = "STARTING"

        key = read_key(KEY_POLL_S)
        if key is not None:
            if phase == "READY" and key in START_KEYS:
                started = True
                go.set()
            elif phase == "READY" and key in CANCEL_KEYS:
                cancel.set()
            elif phase in ("STARTING", "RECORDING") and key in STOP_KEYS:
                stop_pending = True
        if phase == "RECORDING" and stop_pending and not stop_sent:
            stop_sent = True
            outcome["recording_s"] = now - recording_since
            try:
                manager.request_stop()
            except RuntimeError:
                # The pulse train ended on its own between the state read and
                # the request; the capture is already finishing.
                pass

        if phase != last_phase or now - last_draw >= REFRESH_S:
            if phase == "RECORDING":
                reading = meter.sample(now)
            elapsed = 0.0 if recording_since is None else now - recording_since
            if phase == "SAVING":
                elapsed = outcome["recording_s"]
            out.write("\r\033[K" + status_line(phase, elapsed, max_s, reading, cols()))
            out.flush()
            last_draw, last_phase = now, phase

    worker.join()
    out.write("\r\033[K")
    out.flush()
    return outcome


def _key_reader(fd: int) -> Callable[[float], Optional[str]]:
    def read_key(timeout: float) -> Optional[str]:
        try:
            if not select.select([fd], [], [], timeout)[0]:
                return None
        except KeyboardInterrupt:  # cbreak keeps ISIG, so Ctrl-C is a signal
            return "\x03"
        data = os.read(fd, 1)
        return data.decode("latin-1") if data else None

    return read_key


@click.command()
@click.argument(
    "config_file",
    default="examples/capture_record.toml",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=False, readable=True),
)
def cli(config_file: pathlib.Path):
    """Interactive recorder: Enter starts, s/space stops and saves, q quits.

    CONFIG_FILE must be a continuous hardware-trigger synchronized capture
    (see examples/capture_record.toml); its trigger count bounds the recording.
    """

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise click.UsageError("mmwavecapture-record needs an interactive terminal")

    config = toml.load(config_file)
    name, hardware_config = next(iter(config["hardware"].items()))
    try:
        trigger = hardware_config["trigger_kwargs"]
        adxl = hardware_config["adxl_kwargs"]
        max_s = trigger["count"] / trigger["frequency_hz"]
        range_g, odr_hz = adxl["range_g"], adxl["odr_hz"]
    except KeyError as exc:
        raise click.UsageError(
            f"{config_file} is not a continuous hardware-trigger capture config: "
            f"missing {exc}"
        )

    click.echo("Initializing radar, DCA1000 and ADXL355 ...")
    manager = CaptureManager(config_file)
    manager.init_hw()
    meter = Meter(manager.capture_dir / name, range_g, odr_hz)

    fd = sys.stdin.fileno()
    saved_attrs = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        outcome = record(manager, meter, max_s, _key_reader(fd), sys.stdout)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_attrs)

    if outcome["cancelled"]:
        logger.remove()
        shutil.rmtree(manager.capture_dir)
        click.echo("Cancelled before recording; nothing saved.")
        return
    if outcome["error"] is not None:
        raise click.ClickException(
            f"capture failed: {outcome['error']} (see {manager.capture_dir}/status.json)"
        )

    status = json.loads((manager.capture_dir / manager.CAPTURE_STATUS_FILENAME).read_text())
    if status.get("status") != "complete":
        raise click.ClickException(f"capture did not complete: {status}")
    click.echo(f"Saved {outcome['recording_s']:.1f} s recording to {manager.capture_dir}")
