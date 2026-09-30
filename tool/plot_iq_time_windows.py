"""Compare time windows of the same unfiltered A20 target IQ record."""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tool.plot_iq_snr import _target_iq
from paper_bridge_simulation.package_builder import (
    RADAR_RATE_HZ, TARGET_AMPLITUDES, TARGET_ANGLES_DEG, TARGET_SNR_DB,
)
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response


def main():
    _, displacement, _, _ = simulate_response()
    displacement = displacement[::round(REFERENCE_RATE_HZ / RADAR_RATE_HZ)]
    time_s = np.arange(displacement.size) / RADAR_RATE_HZ
    # Generate once, then slice. Every window retains the original noise samples.
    iq, phase, _ = _target_iq(
        displacement, TARGET_ANGLES_DEG[0], TARGET_AMPLITUDES[0],
        TARGET_SNR_DB[0], np.random.default_rng(2026),
    )
    iq /= TARGET_AMPLITUDES[0]
    windows = [(0.0, 4.0, "Full record"), (0.5, 0.8, "Entry"), (1.0, 1.3, "Plateau")]
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 10, "axes.linewidth": 0.8, "axes.grid": False,
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    figure, axes = plt.subplots(1, 3, figsize=(10, 3.8))
    circle = np.linspace(0, 2 * np.pi, 361)
    for axis, (start, stop, name) in zip(axes, windows):
        mask = (time_s >= start) & (time_s < stop)
        axis.plot(np.cos(circle), np.sin(circle), "--", color="0.65", lw=0.8)
        axis.plot(np.cos(phase[mask]), np.sin(phase[mask]), color="black", lw=1.0)
        axis.plot(iq[mask].real, iq[mask].imag, color="#0072BD", lw=0.75)
        axis.set(xlim=(-1.3, 1.3), ylim=(-1.3, 1.3), xlabel="I / A", ylabel="Q / A")
        axis.set_aspect("equal")
        axis.set_title(f"{name}: {start:g}-{stop:g} s\n{mask.sum()} samples", fontsize=10)
        axis.text(0.04, 0.04, f"Phase span: {np.rad2deg(np.ptp(phase[mask])):.1f} deg",
                  transform=axis.transAxes, fontsize=9)
    figure.suptitle(f"Same target, same noise samples: {TARGET_SNR_DB[0]:g} dB, 200 Hz", fontsize=11)
    figure.legend(axes[0].lines, ["unit circle", "noiseless trajectory", "noisy IQ"],
                  loc="lower center", ncol=3, frameon=False, fontsize=9)
    figure.subplots_adjust(top=0.76, bottom=0.20, left=0.055, right=0.99, wspace=0.3)
    output = ROOT / "reports/numerical_simulation_assets_png/iq_time_window_comparison.png"
    figure.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
