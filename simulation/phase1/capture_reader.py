"""Thin reader from the acquisition schema into the Phase-1 ADC frontend.

All hardware-specific adaptation lives in ``mmwavecapture.algorithm_input``.
This module only maps that stable schema into the existing frontend dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import numpy as np

from .frontend import ADCCubeObservation, FrontendConfig, range_axis_m


@dataclass(frozen=True)
class CapturedFrontendInput:
    adc: ADCCubeObservation
    frontend_config: FrontendConfig
    manifest: Mapping[str, Any]
    source_directory: Path


def load_captured_frontend_input(
    path: Union[str, Path],
    *,
    mmap_mode: Optional[str] = "r",
) -> CapturedFrontendInput:
    """Load capture-produced arrays without parsing PCAP, LVDS, or radar CFG."""

    try:
        from mmwavecapture.algorithm_input import load_algorithm_input
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "the capture reader requires the local capture_program package; "
            "install it with `pip install -e capture_program`"
        ) from exc

    capture = load_algorithm_input(path, mmap_mode=mmap_mode)
    radar = capture.manifest["radar"]
    frontend_config = FrontendConfig(
        num_tx=len(radar["tx_indices"]),
        num_rx=len(radar["rx_indices"]),
        num_virtual_rx=int(radar["virtual_antennas"]),
        num_adc_samples=int(radar["adc_samples_per_chirp"]),
        adc_sample_rate_hz=float(radar["adc_sample_rate_hz"]),
        chirp_duration_s=float(radar["ramp_end_time_s"]),
        chirps_per_frame=int(radar["physical_chirps_per_frame"]),
        num_range_bins=int(radar["adc_samples_per_chirp"]),
        range_resolution_m=float(radar["range_resolution_m"]),
    )
    adc = ADCCubeObservation(
        adc_cube=np.asarray(capture.adc_cube),
        range_axis_m=range_axis_m(frontend_config),
        frame_times_s=np.asarray(capture.frame_times_s),
        scatterers=(),
    )
    return CapturedFrontendInput(
        adc=adc,
        frontend_config=frontend_config,
        manifest=capture.manifest,
        source_directory=capture.directory,
    )
