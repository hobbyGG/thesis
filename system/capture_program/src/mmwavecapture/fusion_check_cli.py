"""Command-line readiness check for a synchronized fusion package."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Mapping, Optional

import click

from mmwavecapture.fusion_input import FusionInputError, load_fusion_input


def _summary(capture: Any) -> Mapping[str, Any]:
    radar_times = (
        capture.radar_adc_sample_monotonic_ns
        if capture.radar_adc_sample_monotonic_ns is not None
        else capture.radar_reference_monotonic_ns
    )
    calibration_id = (
        capture.value_calibration.calibration_id
        if capture.value_calibration is not None
        else None
    )
    return {
        "schema": "mmwavecapture.fusion-readiness",
        "schema_version": 1,
        "algorithm_ready": capture.algorithm_ready,
        "algorithm_readiness_failures": list(
            capture.quality.algorithm_readiness_failures
        ),
        "fusion_ready": capture.fusion_ready,
        "readiness_failures": list(capture.quality.readiness_failures),
        "capture_directory": str(capture.directory),
        "clock": capture.provenance.clock,
        "sync_mode": capture.provenance.sync_mode,
        "radar_timestamp_quality": capture.provenance.radar_timestamp_quality,
        "radar_frames": int(radar_times.shape[0]),
        "adxl_samples": int(capture.adxl_sample_monotonic_ns.shape[0]),
        "radar_adc_timeline_calibrated": (
            capture.radar_adc_sample_monotonic_ns is not None
        ),
        "timing_uncertainty_ns": {
            "radar_reference_edge": (
                capture.calibration.radar_reference_edge_uncertainty_ns
            ),
            "radar_reference_to_adc_latency": (
                capture.calibration.radar_reference_to_adc_latency_uncertainty_ns
            ),
            "adxl_filter_group_delay": (
                capture.calibration.adxl_filter_group_delay_uncertainty_ns
            ),
        },
        "timing_calibration_sources": {
            "radar_reference_to_adc_latency": (
                capture.calibration.radar_latency_source
            ),
            "adxl_filter_group_delay": (
                capture.calibration.adxl_group_delay_source
            ),
        },
        "fusion_calibration_id": calibration_id,
    }


@click.command("mmwavecapture-fusion-check")
@click.argument(
    "capture_path",
    type=click.Path(path_type=pathlib.Path, exists=True),
)
@click.option(
    "--require-ready/--allow-not-ready",
    default=True,
    show_default=True,
    help="Return a failing exit status when the selected readiness gate is blocked.",
)
@click.option(
    "--require-calibrated",
    is_flag=True,
    help=(
        "Use the strict calibrated fusion-ready gate instead of the default "
        "operational algorithm-ready gate."
    ),
)
@click.option(
    "--output",
    type=click.Path(path_type=pathlib.Path),
    help="Optionally write the JSON summary to this file.",
)
def cli(
    capture_path: pathlib.Path,
    require_ready: bool,
    require_calibrated: bool,
    output: Optional[pathlib.Path],
) -> None:
    """Validate CAPTURE_PATH and report fusion readiness as JSON."""

    try:
        capture = load_fusion_input(capture_path)
    except (FusionInputError, OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    payload = _summary(capture)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    click.echo(serialized, nl=False)
    selected_ready = (
        capture.fusion_ready if require_calibrated else capture.algorithm_ready
    )
    if require_ready and not selected_ready:
        gate = "fusion-ready" if require_calibrated else "algorithm-ready"
        failures = (
            capture.quality.readiness_failures
            if require_calibrated
            else capture.quality.algorithm_readiness_failures
        )
        raise click.ClickException(
            f"capture is structurally valid but not {gate}: "
            + ", ".join(failures)
        )


if __name__ == "__main__":
    cli()
