"""Command-line export of an existing radar capture."""

from __future__ import annotations

import pathlib

import click

from mmwavecapture.algorithm_input import (
    DEFAULT_OUTPUT_DIRECTORY,
    export_algorithm_input,
)


@click.command()
@click.argument(
    "radar_capture_directory",
    type=click.Path(
        path_type=pathlib.Path,
        exists=True,
        file_okay=False,
        readable=True,
    ),
)
@click.option(
    "--data-port",
    type=click.IntRange(1, 65535),
    default=4098,
    show_default=True,
    help="DCA1000 UDP data destination port.",
)
@click.option(
    "--aggregation",
    type=click.Choice(("coherent_mean", "first"), case_sensitive=True),
    default="coherent_mean",
    show_default=True,
    help="Reduction used to create the frame-level ADC cube.",
)
@click.option(
    "--save-chirp-cube/--no-save-chirp-cube",
    default=True,
    show_default=True,
    help="Also retain the standardized four-dimensional chirp cube.",
)
def cli(
    radar_capture_directory: pathlib.Path,
    data_port: int,
    aggregation: str,
    save_chirp_cube: bool,
) -> None:
    """Export DCA.PCAP + RADAR.CFG into a stable algorithm-input package."""

    manifest = export_algorithm_input(
        radar_capture_directory / "dca.pcap",
        radar_capture_directory / "radar.cfg",
        radar_capture_directory / DEFAULT_OUTPUT_DIRECTORY,
        data_port=data_port,
        chirp_aggregation=aggregation,
        save_chirp_cube=save_chirp_cube,
    )
    click.echo(str(manifest))
