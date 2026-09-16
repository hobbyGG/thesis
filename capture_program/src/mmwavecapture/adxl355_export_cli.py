"""Command-line export for a completed native ADXL355 capture."""

from __future__ import annotations

import pathlib

import click

from mmwavecapture.adxl355_input import export_adxl355_input


@click.command()
@click.argument(
    "raw_file",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=False),
)
@click.argument(
    "summary_file",
    type=click.Path(path_type=pathlib.Path, exists=True, dir_okay=False),
)
@click.argument(
    "output_directory",
    type=click.Path(path_type=pathlib.Path, file_okay=False),
)
def cli(
    raw_file: pathlib.Path,
    summary_file: pathlib.Path,
    output_directory: pathlib.Path,
) -> None:
    """Validate RAW_FILE and publish an atomic algorithm-input directory."""

    manifest = export_adxl355_input(raw_file, summary_file, output_directory)
    click.echo(str(manifest))
