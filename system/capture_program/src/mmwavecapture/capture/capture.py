#
# Copyright (c) 2023 Louie Lu <louielu@cs.unc.edu>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import annotations

import abc
import datetime
import importlib
import json
import pathlib
import sys
from typing import Any, Dict, Optional

import toml
from loguru import logger


class CaptureHardware(abc.ABC):
    """CaptureHardware is the abstract class for all capture hardware.


    For each capture hardware, there are 6 stages of capture process:

    1. Initialize capture hardware

        This stage should initialize and config the capture hardware,
        and make sure the capture hardware is ready to capture data.

        .. note:: Do not create any output files in this stage.

    2. Prepare capture environment and output files

        This stage should setup the capture environment and create
        output files for the capture hardware. You should also setup
        thread/processes for capturing data at this stage, but not start them.

        .. warning:: The output files should be created under `base_path`

        If you are using `Capture` class, the hardware `base_path` will
        be setup after calling `Capture.add_capture_hardware()`.
        If you are using `CaptureManager` class, the hardware `base_path`
        will be setup during `CaptureManager.capture()`.
        It not using any of the above classes, you should setup the
        `base_path` by yourself before calling `CaptureHardware.prepare_capture()`.

    3. Start capture

        This stage should start the capture process/thread.

    4. Stop capture

        This stage should stop the capture process/thread and close
        the output files.

    5. Dump configuration

        This stage should dump the configuration of the capture hardware
        to `base_path/<config_name>` for future reference.

    6. Finalize capture output

        This success-only stage validates and publishes consumer-facing data.
        Partial raw files from a failed capture are never finalized as complete.
    """

    _hw_name: str = ""
    _base_path: Optional[pathlib.Path] = None

    @property
    def hw_name(self) -> str:
        return self._hw_name

    @hw_name.setter
    def hw_name(self, hw_name: str) -> None:
        self._hw_name = hw_name

    @property
    def base_path(self) -> Optional[pathlib.Path]:
        """The base path for the capture hardware

        The base path will be set by `Capture` class or `CaptureManager` class.
        Or by yourself if you are not using any of the above classes.

        If set it by `CaptureManager`, the base path should be
        `<dataset_path>/<capture_path>/<hw_name>/`.

        :setter: Set the base path for the capture hardware
        :getter: Get the base path for the capture hardware
        """
        return self._base_path

    @base_path.setter
    def base_path(self, base_path: pathlib.Path) -> None:
        if not base_path.exists():
            raise ValueError(f"Base path `{base_path}/` does not exist")
        if not base_path.is_dir():
            raise ValueError(f"Base path `{base_path}/` is not a directory")

        self._base_path = base_path

    @abc.abstractmethod
    def init_capture_hw(self) -> None:
        """Initialize the capture hardware"""
        raise NotImplementedError

    @abc.abstractmethod
    def prepare_capture(self) -> None:
        """Prepare the capture environment and output files

        Output filename should be `self.base_path`/<sensor>.*
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_capture(self) -> None:
        """Start the sensor to capture data"""
        raise NotImplementedError

    @abc.abstractmethod
    def stop_capture(self) -> None:
        """Stop the sensor and capture output files"""
        raise NotImplementedError

    @abc.abstractmethod
    def dump_config(self) -> None:
        """Dump the configuration of the capture hardware to `base_path`"""
        raise NotImplementedError

    def finalize_capture(self) -> None:
        """Create validated, consumer-facing outputs after configuration dump.

        Hardware implementations may override this hook. It runs only after a
        successful capture, so failure cleanup can still preserve partial raw
        files without attempting to publish them as complete algorithm input.
        """

    def close(self) -> None:
        """Release hardware resources after capture.

        Hardware implementations with persistent sockets, serial ports, or
        pipelines should override this method. The default is a no-op so older
        optional capture plugins remain compatible.
        """


class Capture:
    def __init__(self, base_path: pathlib.Path):
        self._cap_hw: list[CaptureHardware] = []
        self._base_path: pathlib.Path = base_path

        # Create directory for `Capture`
        self._base_path.mkdir(exist_ok=True)
        logger.debug(f"Capture directory created at `{self._base_path}/`")

    def add_capture_hardware(self, hw: CaptureHardware) -> None:
        # Creat directory for capture hardware
        hardware_base_path = self._base_path / hw.hw_name
        hardware_base_path.mkdir(exist_ok=True)
        logger.debug(f"Capture hardware directory created at `{hardware_base_path}/`")

        hw.base_path = hardware_base_path

        self._cap_hw.append(hw)

    @logger.catch(reraise=True)
    def capture(self) -> None:
        try:
            logger.info("Preparing capture hardware")
            for hw in self._cap_hw:
                hw.prepare_capture()

            logger.info("Starting capture hardware")
            for hw in self._cap_hw:
                hw.start_capture()
            logger.success("Capture started")

            for hw in self._cap_hw:
                hw.stop_capture()
            logger.info("Capture finished")

            logger.info("Dumping capture hardware configurations")
            self._dump_configs()
            logger.info("Finalizing capture outputs")
            self._finalize_outputs()
        except BaseException:
            self._abort_hardware()
            self._dump_configs(suppress_errors=True)
            self._close_hardware(suppress_errors=True)
            raise
        else:
            self._close_hardware()

    def _abort_hardware(self) -> None:
        for hw in reversed(self._cap_hw):
            abort_capture = getattr(hw, "abort_capture", None)
            if not callable(abort_capture):
                continue
            try:
                abort_capture()
            except Exception:
                logger.exception(f"Failed to abort capture hardware `{hw.hw_name}`")

    def _dump_configs(self, suppress_errors: bool = False) -> None:
        errors = []
        for hw in self._cap_hw:
            try:
                hw.dump_config()
            except Exception as exc:
                errors.append(f"{hw.hw_name}: {exc}")
                logger.exception(
                    f"Failed to dump capture hardware configuration `{hw.hw_name}`"
                )
        if errors and not suppress_errors:
            raise RuntimeError(
                "hardware configuration dump failed: " + "; ".join(errors)
            )

    def _close_hardware(self, suppress_errors: bool = False) -> None:
        errors = []
        for hw in reversed(self._cap_hw):
            try:
                hw.close()
            except Exception as exc:
                errors.append(f"{hw.hw_name}: {exc}")
                logger.exception(f"Failed to close capture hardware `{hw.hw_name}`")
        if errors and not suppress_errors:
            raise RuntimeError("hardware close failed: " + "; ".join(errors))

    def _finalize_outputs(self) -> None:
        errors = []
        for hw in self._cap_hw:
            try:
                hw.finalize_capture()
            except Exception as exc:
                errors.append(f"{hw.hw_name}: {exc}")
                logger.exception(
                    f"Failed to finalize capture output for `{hw.hw_name}`"
                )
        if errors:
            raise RuntimeError("hardware output finalization failed: " + "; ".join(errors))


class CaptureManager:
    """Capture Manager manages HDF5-like dataset directory structure
    and handle capture hardware initialization and capture process.

    The layout of dataset directory is as follows::

        dataset_path/           # Create when initalizing `CaptureManager`
        ├── capture_00000/      # Create when calling `CaptureManager.capture()`
        │   ├── config.toml     # Capture configuration
        │   ├── iwr1843_vert/   # Capture hardware name
        │   │   ├── dca.pcap    # DCA1000EVM capture pcap
        │   │   ├── radar.cfg   # Radar configuration
        │   │   ├── dca.json    # DCA1000EVM configuration
        │   ├── realsense/         # Another capture hardware name
        │   │   ├── color.avi      # Color video
        ├── capture_00001/
        │   ├── config.toml
        │   ├── iwr1843_vert/
        │   │   ├── dca.pcap
        ...

    The calling sequence of `CaptureManager` is as follows:

    1. Initialize `CaptureManager` with `config.toml` path
    2. Initialize capture hardware with `CaptureManager.init_hw()`
    3. Start capture by calling `CaptureManager.capture()`
    """

    CAPTURE_LOG_FILENAME = "capture.log"
    CAPTURE_MANAGER_CONFIG_OUTPUT_FILENAME = "config.toml"
    CAPTURE_STATUS_FILENAME = "status.json"
    CAPTURE_DIR_PREFIX = "capture_"
    CAPTURE_DIR_FORMAT = CAPTURE_DIR_PREFIX + "{:05d}"

    def __init__(self, config_filename: pathlib.Path):
        self._hw: list[CaptureHardware] = []
        self._config_filename: pathlib.Path = config_filename
        self._config: Dict[str, Any] = {}

        # Load config and create dataset directory
        self._load_config(self._config_filename)
        self._dataset_dir = pathlib.Path(self._config["dataset_dir"])
        self._dataset_dir.mkdir(parents=True, exist_ok=True)

        # Allocate the capture directory atomically so concurrent invocations do
        # not write into the same capture_XXXXX directory.
        self._capture_dir = self._create_next_capture_dir()

        # Init logging
        logger.remove()

        # Add stderr logger
        if self._config["logging"]["stderr"]["enable"]:
            logger.add(sys.stderr, level=self._config["logging"]["stderr"]["level"])

        # Add logfile logger
        if self._config["logging"]["logfile"]["enable"]:
            logger.add(
                self._capture_dir / self.CAPTURE_LOG_FILENAME,
                level=self._config["logging"]["logfile"]["level"],
                serialize=self._config["logging"]["logfile"]["serialize"],
            )

        # Unfotunately, we will need to log them here
        logger.debug(f"Dataset directory created at `{self._dataset_dir}/`")
        logger.debug(f"Capture directory created at `{self._capture_dir}/`")

        # Persist provenance before touching hardware. A failed initialization
        # or capture must still leave enough evidence to reproduce the attempt.
        self._write_config()
        self._write_status(status="pending", phase="created")

    def _load_config(self, path: pathlib.Path) -> None:
        with open(path, encoding="utf-8") as config_file:
            self._config = toml.load(config_file)

        if not self._config.get("dataset_dir"):
            raise ValueError("`dataset_dir` is not specified in config")

        hardware = self._config.get("hardware")
        if not isinstance(hardware, dict) or not hardware:
            raise ValueError("No capture hardware is specified in config")
        for hw_name, hw_config in hardware.items():
            if not isinstance(hw_config, dict) or not hw_config.get("hw_def_class"):
                raise ValueError(
                    f"Capture hardware `{hw_name}` is missing `hw_def_class`"
                )

        metadata = self._config.setdefault("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("`metadata` must be a TOML table")
        metadata_defaults = {
            "title": "Millimeter-wave dataset",
            "creator": "unknown",
            "subject": "",
            "description": "",
            "license": "CC-BY-SA-4.0",
        }
        for key, default in metadata_defaults.items():
            metadata.setdefault(key, default)
        if metadata.get("date", "<today>") == "<today>":
            metadata["date"] = datetime.datetime.now()

        logging_config = self._config.setdefault("logging", {})
        if not isinstance(logging_config, dict):
            raise ValueError("`logging` must be a TOML table")
        stderr_config = logging_config.setdefault("stderr", {})
        logfile_config = logging_config.setdefault("logfile", {})
        if not isinstance(stderr_config, dict):
            raise ValueError("`logging.stderr` must be a TOML table")
        if not isinstance(logfile_config, dict):
            raise ValueError("`logging.logfile` must be a TOML table")
        stderr_config.setdefault("enable", True)
        stderr_config.setdefault("level", "INFO")
        logfile_config.setdefault("enable", True)
        logfile_config.setdefault("level", "TRACE")
        logfile_config.setdefault("serialize", True)

    def _create_next_capture_dir(self) -> pathlib.Path:
        capture_ids = []
        for path in self._dataset_dir.glob(f"{self.CAPTURE_DIR_PREFIX}*"):
            suffix = path.name[len(self.CAPTURE_DIR_PREFIX) :]
            if suffix.isdigit():
                capture_ids.append(int(suffix))

        next_id = max(capture_ids, default=-1) + 1
        while True:
            capture_dir = self._dataset_dir / self.CAPTURE_DIR_FORMAT.format(next_id)
            try:
                capture_dir.mkdir(exist_ok=False)
            except FileExistsError:
                next_id += 1
                continue
            logger.info(f"Capture ID: {next_id}")
            return capture_dir

    def _write_config(self) -> None:
        output = self._capture_dir / self.CAPTURE_MANAGER_CONFIG_OUTPUT_FILENAME
        temporary = output.with_suffix(output.suffix + ".tmp")
        with open(temporary, "w", encoding="utf-8") as config_file:
            toml.dump(self._config, config_file)
        temporary.replace(output)

    def _write_status(
        self,
        status: str,
        phase: str,
        error: Optional[BaseException] = None,
    ) -> None:
        output = self._capture_dir / self.CAPTURE_STATUS_FILENAME
        temporary = output.with_suffix(output.suffix + ".tmp")
        payload = {
            "schema_version": 1,
            "status": status,
            "phase": phase,
            "updated_at": datetime.datetime.now().astimezone().isoformat(),
        }
        if error is not None:
            payload["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(output)

    def _record_failure(self, phase: str, error: BaseException) -> None:
        try:
            self._write_status(status="failed", phase=phase, error=error)
        except Exception:
            logger.exception("Failed to persist capture failure status")

    def _close_initialized_hardware(self) -> None:
        for hw in reversed(self._hw):
            try:
                hw.close()
            except Exception:
                logger.exception(f"Failed to close capture hardware `{hw.hw_name}`")

    def init_hw(self) -> None:
        if self._hw:
            raise RuntimeError("Capture hardware is already initialized")

        self._write_status(status="running", phase="initializing")
        try:
            for hw in self._config["hardware"]:
                logger.info(
                    f"Initializing capture hardware `{hw}` from "
                    f"`{self._config['hardware'][hw]['hw_def_class']}`"
                )
                # Get capture hardware class by `hw_def_class`
                module_name, class_name = self._config["hardware"][hw][
                    "hw_def_class"
                ].rsplit(".", 1)
                module = importlib.import_module(module_name)
                hw_class = getattr(module, class_name)

                # Create capture hardware instance
                hw_config = self._config["hardware"][hw]
                hw_obj = hw_class(hw_name=hw, **hw_config)
                self._hw.append(hw_obj)
                logger.success(f"Capture hardware `{hw}` initialized")
        except BaseException as exc:
            self._close_initialized_hardware()
            self._record_failure("initialization", exc)
            raise

        self._write_status(status="ready", phase="initialized")
        logger.success(
            f"Total of {len(self._config['hardware'])} capture hardware initialized"
        )

    def capture(self) -> None:
        if not self._hw:
            error = RuntimeError("Capture hardware is not initialized")
            self._record_failure("capture", error)
            raise error

        # Initialize capture hardware and setup capture
        capture = Capture(self._capture_dir)
        for hw in self._hw:
            logger.info(f"Adding capture hardware `{hw.hw_name}`")
            capture.add_capture_hardware(hw)

        self._write_status(status="running", phase="capture")
        try:
            capture.capture()
        except BaseException as exc:
            self._record_failure("capture", exc)
            raise

        self._write_status(status="complete", phase="complete")
        logger.success(f"Capture finished, all files output to `{capture._base_path}/`")
