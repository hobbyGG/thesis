"""Plot saved loop IQ and its frame mean, with no extra noise or filtering."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithm.io import build_algorithm_inputs, load_capture_package  # noqa: E402


def plot_chirp_iq(input_dir: Path, output: Path, range_bin: int = 8) -> Path:
    capture = load_capture_package(input_dir)
    frame_radar, _, frame_targets, _ = build_algorithm_inputs(capture)
    loop_radar, _, loop_targets, _ = build_algorithm_inputs(capture, radar_mode="chirp")
    index = int(np.flatnonzero(frame_targets.range_bins == range_bin)[0])
    loops = capture.chirp_cube.shape[1]
    origin_ns = capture.radar_time_ns[0] - round(
        capture.radar_metadata["coherent_aperture_center_offset_s"] * 1.0e9
    )
    frame_time = (frame_radar.extra["radar_time_ns"] - origin_ns) * 1.0e-9
    loop_time = (loop_radar.extra["radar_time_ns"] - origin_ns) * 1.0e-9
    frame_iq = frame_targets.slow_time[index]
    loop_iq = loop_targets.slow_time[index]
    # One shared amplitude and one constant phase rotation retain radial noise.
    radius = float(np.median(np.abs(frame_iq)))
    rotation = np.exp(-1j * np.angle(np.mean(frame_iq[frame_time < 0.2])))
    frame_iq = frame_iq * rotation / radius
    loop_iq = loop_iq * rotation / radius

    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 10, "axes.linewidth": 0.8, "axes.grid": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "svg.fonttype": "none",
    })
    figure, axes = plt.subplots(2, 2, figsize=(9.2, 7.0))
    circle = np.exp(1j * np.linspace(0.0, 2.0 * np.pi, 2001))
    windows = ((0.5, 0.8, "Entry: full IQ view"), (1.0, 1.3, "Plateau: arc close-up"))
    statistics = []
    for column, (start, end, label) in enumerate(windows):
        frame_mask = (frame_time >= start) & (frame_time < end)
        loop_mask = (loop_time >= start) & (loop_time < end)
        # Both rows use identical limits; the plateau is a genuine zoom.
        if column == 0:
            points = loop_iq[loop_mask]
            extent = max(1.25, float(np.max(np.abs(np.r_[points.real, points.imag]))) + 0.06)
            xlimits = ylimits = (-extent, extent)
        else:
            points = np.r_[loop_iq[loop_mask], frame_iq[frame_mask]]
            center = np.array([(points.real.max() + points.real.min()) / 2.0,
                               (points.imag.max() + points.imag.min()) / 2.0])
            half_width = max(float(np.ptp(points.real)), float(np.ptp(points.imag))) * 0.60
            xlimits = (center[0] - half_width, center[0] + half_width)
            ylimits = (center[1] - half_width, center[1] + half_width)

        for row, (iq, mask, color, mode) in enumerate((
            (frame_iq, frame_mask, "#D55E00", "Frame IQ: mean of 16 loops"),
            (loop_iq, loop_mask, "#0072B2", "Loop IQ: 2 TX per loop"),
        )):
            axis = axes[row, column]
            axis.plot(circle.real, circle.imag, "--", color="0.55", lw=0.9)
            if row == 0:
                axis.plot(iq[mask].real, iq[mask].imag, color=color, lw=1.0)
            else:
                # Each frame is one burst. NaNs prevent a fictitious line
                # across the unobserved gap between bursts.
                burst = np.where(mask, iq, np.nan).reshape(-1, loops)
                trace = np.c_[burst, np.full(burst.shape[0], np.nan)].ravel()
                axis.plot(trace.real, trace.imag, color=color, lw=0.65)
            radial_std = float(np.std(np.abs(iq[mask])))
            axis.set(xlim=xlimits, ylim=ylimits, xlabel="Normalized I", ylabel="Normalized Q")
            axis.set_aspect("equal", adjustable="box")
            axis.tick_params(direction="out", width=0.8)
            axis.set_title(f"{mode}\n{label}, {start:.1f}–{end:.1f} s", fontsize=10)
            axis.text(0.03, 0.97, f"N = {mask.sum()}   radial SD = {radial_std:.3f}",
                      transform=axis.transAxes, va="top", fontsize=9,
                      bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 2})
            statistics.append(f"{label} / {mode}: N={mask.sum()}, radial_SD={radial_std:.6f}")
    figure.suptitle(
        f"Saved A20 target IQ — range bin {range_bin}, angle {frame_targets.angle_deg[index]:.1f}°",
        fontsize=12, y=0.98,
    )
    frame_hz = 1.0 / np.median(np.diff(frame_time))
    loop_us = capture.radar_metadata["loop_start_interval_s"] * 1.0e6
    figure.text(0.5, 0.055,
                f"Frame rate: {frame_hz:g} Hz; within-burst loop interval: {loop_us:.2f} μs. "
                "Dashed line: unit circle.", ha="center", fontsize=9)
    figure.text(0.5, 0.028,
                "Shared fixed normalization and phase rotation; no filtering. Loop lines break at frame boundaries.",
                ha="center", fontsize=9)
    figure.subplots_adjust(top=0.87, bottom=0.14, left=0.09, right=0.98, wspace=0.28, hspace=0.44)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=300, bbox_inches="tight")
    figure.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    plt.close(figure)
    print(output.resolve())
    print("\n".join(statistics))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--range-bin", type=int, default=8)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/numerical_simulation_assets_png/iq_chirp_frame_comparison.png")
    args = parser.parse_args()
    plot_chirp_iq(args.input, args.output, args.range_bin)


if __name__ == "__main__":
    main()
