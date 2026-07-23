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

import time
import pathlib
import shutil
import signal
import subprocess
from typing import Any, Dict, Optional

import netifaces
from loguru import logger

import mmwavecapture.dca1000
import mmwavecapture.radar
from mmwavecapture.capture.capture import CaptureHardware


class RadarDCA(CaptureHardware):
    PCAP_OUTPUT_FILENAME = "dca.pcap"
    RADAR_CONFIG_FILENAME = "radar.cfg"
    DCA_CONFIG_FILENAME = "dca.json"

    @logger.catch(reraise=True)
    def __init__(
        self,
        hw_name: str,
        dca_eth_interface: str,
        radar_config_filename: pathlib.Path,
        radar_config_port: str = "/dev/ttyACM0",
        radar_data_port: str = "/dev/ttyACM1",
        dca_ip: str = "192.168.33.180",
        dca_config_port: int = 4096,
        host_ip: str = "192.168.33.30",
        capture_frames: int = 100,
        init_capture_hw: bool = True,
        tcpdump_path: Optional[str] = None,
        capture_timeout_s: Optional[float] = None,
        tcpdump_startup_delay_s: float = 0.2,
        **kwargs: Dict[str, Any],
    ) -> None:
        self.hw_name = hw_name
        self._radar_config_filename = radar_config_filename
        self._radar_config_port = radar_config_port
        self._radar_data_port = radar_data_port
        self._dca_eth_interface = dca_eth_interface
        self._dca_ip = dca_ip
        self._dca_config_port = dca_config_port
        self._host_ip = host_ip
        self._capture_frames = capture_frames
        self._initialized = False
        self._tcpdump_startup_delay_s = tcpdump_startup_delay_s

        resolved_tcpdump = tcpdump_path or shutil.which("tcpdump")
        if not resolved_tcpdump:
            raise FileNotFoundError(
                "tcpdump was not found; install it and ensure it is available in PATH"
            )
        self._tcpdump_bin_path = resolved_tcpdump

        radar_config = mmwavecapture.radar.RadarCoreConfig(radar_config_filename)
        if capture_timeout_s is None:
            if capture_frames <= 0:
                raise ValueError(
                    "capture_timeout_s is required when capture_frames is not positive"
                )
            expected_capture_s = capture_frames * radar_config.frame_period / 1000.0
            capture_timeout_s = expected_capture_s + 15.0
        if capture_timeout_s <= 0:
            raise ValueError("capture_timeout_s must be positive")
        self._capture_timeout_s = capture_timeout_s

        # tcpdump
        self._cap_tcpdump = None
        self._catcher = None
        self._dca_recording = False
        self._radar_started = False

        # DCA interface & host IP check
        if dca_eth_interface not in netifaces.interfaces():
            raise ValueError(f"Interface {dca_eth_interface} not found")
        if netifaces.AF_INET not in netifaces.ifaddresses(dca_eth_interface):
            raise ValueError(f"Interface {dca_eth_interface} has no IPv4 address")
        if host_ip not in [
            netif["addr"]
            for netif in netifaces.ifaddresses(dca_eth_interface)[netifaces.AF_INET]
        ]:
            raise ValueError(f"Host IP {host_ip} not found in {dca_eth_interface}")

        # DCA1000EVM
        self.dca = mmwavecapture.dca1000.DCA1000(
            host_ip=self._host_ip,
            dca_ip=self._dca_ip,
            dca_config_port=self._dca_config_port,
        )

        # Radar
        self.radar = mmwavecapture.radar.Radar(
            config_port=self._radar_config_port,
            config_baudrate=115200,
            data_port=self._radar_data_port,
            data_baudrate=921600,
            config_filename=self._radar_config_filename,
            initialize_connection_and_radar=False,
            capture_frames=self._capture_frames,
        )

        if init_capture_hw:
            self.init_capture_hw()

    @staticmethod
    def _require_success(ok: bool, action: str) -> None:
        if not ok:
            raise RuntimeError(f"DCA1000 failed to {action}")

    @logger.catch(reraise=True)
    def init_capture_hw(self) -> None:
        # Check DCA1000EVM connection
        self._require_success(
            self.dca.system_connection(),
            f"respond at {self._dca_ip}",
        )

        # Initialize DCA1000EVM
        self._require_success(self.dca.reset_radar(), "reset the radar")
        self._require_success(self.dca.reset_fpga(), "reset the FPGA")
        self._require_success(self.dca.config_fpga(), "configure the FPGA")
        self._require_success(
            self.dca.config_packet_delay(), "configure the packet delay"
        )

        # Initialize radar
        self.radar.initialize()
        self.radar.config()

        self._initialized = True

    @staticmethod
    def _process_error(process: subprocess.Popen) -> str:
        if process.stderr is None:
            return ""
        stderr = process.stderr.read()
        if isinstance(stderr, bytes):
            return stderr.decode("utf-8", errors="replace").strip()
        return str(stderr).strip()

    def _check_process_started(
        self, process: subprocess.Popen, process_name: str
    ) -> None:
        returncode = process.poll()
        if returncode is not None:
            detail = self._process_error(process)
            message = f"{process_name} exited during startup with code {returncode}"
            if detail:
                message = f"{message}: {detail}"
            raise RuntimeError(message)

    def start_tcpdump_capture(self, outfile: pathlib.Path) -> None:
        self._cap_tcpdump = subprocess.Popen(
            [
                self._tcpdump_bin_path,
                "-i",
                self._dca_eth_interface,
                "-q",
                "-n",
                "-U",
                "-w",
                str(outfile),
                "udp",
                "and",
                "host",
                self._dca_ip,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def stop_tcpdump_capture(self) -> None:
        process = self._cap_tcpdump
        self._cap_tcpdump = None
        if not process:
            return

        if process.poll() is None:
            process.send_signal(signal.SIGUSR2)  # Flush packet buffer
            process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

        if process.returncode not in (0, -signal.SIGINT):
            detail = self._process_error(process)
            message = f"tcpdump exited with code {process.returncode}"
            if detail:
                message = f"{message}: {detail}"
            raise RuntimeError(message)

    def _stop_catcher(self) -> None:
        process = self._catcher
        self._catcher = None
        if not process or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def _shutdown_capture(self) -> None:
        errors = []

        if self._radar_started:
            try:
                self.radar.stop_sensor()
            except Exception as exc:  # Preserve cleanup of the remaining resources.
                errors.append(f"radar stop failed: {exc}")
            finally:
                self._radar_started = False

        if self._dca_recording:
            try:
                self._require_success(self.dca.stop_record(), "stop recording")
            except Exception as exc:
                errors.append(f"DCA1000 stop failed: {exc}")
            finally:
                self._dca_recording = False

        try:
            self._stop_catcher()
        except Exception as exc:
            errors.append(f"termination catcher stop failed: {exc}")

        try:
            self.stop_tcpdump_capture()
        except Exception as exc:
            errors.append(f"tcpdump stop failed: {exc}")

        if errors:
            raise RuntimeError("; ".join(errors))

    def abort_capture(self) -> None:
        """Stop all active resources without waiting for a finite capture."""
        self._shutdown_capture()

    def _abort_safely(self) -> None:
        try:
            self.abort_capture()
        except Exception:
            logger.exception("Capture cleanup failed while handling another error")

    @logger.catch(reraise=True)
    def prepare_capture(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "Capture hardware are not initialized, run `.init_capture_hw()` first"
            )

        if not self.base_path:
            raise ValueError("Base path is not set")

        try:
            # Start DCA tcpdump before enabling the DCA data stream.
            self.start_tcpdump_capture(
                outfile=self.base_path / self.PCAP_OUTPUT_FILENAME
            )

            # Match the DCA1000 "no LVDS data" status packet after finite frames.
            self._catcher = subprocess.Popen(
                [
                    self._tcpdump_bin_path,
                    "-i",
                    self._dca_eth_interface,
                    "-s",
                    "256",
                    "-c",
                    "1",
                    "-q",
                    "-n",
                    "udp[10:4] == 0x0a000001",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

            time.sleep(self._tcpdump_startup_delay_s)
            capture_process = self._cap_tcpdump
            if capture_process is None:
                raise RuntimeError("capture tcpdump was not started")
            self._check_process_started(capture_process, "capture tcpdump")
            catcher_process = self._catcher
            if catcher_process is None:
                raise RuntimeError("termination catcher was not started")
            self._check_process_started(catcher_process, "termination catcher")

            self._require_success(self.dca.start_record(), "start recording")
            self._dca_recording = True
        except Exception:
            self._abort_safely()
            raise

    def start_capture(self) -> None:
        try:
            self.radar.start_sensor()
            self._radar_started = True
        except Exception:
            self._abort_safely()
            raise

    def stop_capture(self) -> None:
        wait_error = None
        try:
            if not self._catcher:
                raise RuntimeError("termination catcher was not started")
            returncode = self._catcher.wait(timeout=self._capture_timeout_s)
            if returncode != 0:
                detail = self._process_error(self._catcher)
                message = f"termination catcher exited with code {returncode}"
                if detail:
                    message = f"{message}: {detail}"
                raise RuntimeError(message)
        except Exception as exc:
            wait_error = exc

        shutdown_error = None
        try:
            self._shutdown_capture()
        except Exception as exc:
            shutdown_error = exc

        if wait_error and shutdown_error:
            raise RuntimeError(f"{wait_error}; cleanup failed: {shutdown_error}")
        if wait_error:
            raise wait_error
        if shutdown_error:
            raise shutdown_error

    def dump_config(self) -> None:
        if not self.base_path:
            raise ValueError("Base path is not set")
        self.radar.dump_config(self.base_path / self.RADAR_CONFIG_FILENAME)
        self.dca.dump_config(self.base_path / self.DCA_CONFIG_FILENAME)
