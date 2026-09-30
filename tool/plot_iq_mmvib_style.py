"""Make an mmVib-inspired IQ style comparison without changing the A20 model."""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from paper_bridge_simulation.package_builder import (  # noqa: E402
    RADAR_RATE_HZ, TARGET_AMPLITUDES, TARGET_ANGLES_DEG, TARGET_SNR_DB,
    WAVELENGTH_M,
)
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response  # noqa: E402
from tool.plot_iq_snr import _target_iq  # noqa: E402

# Color order chosen to match the multi-trace visual language in mmVib figures.
MMVIB_COLORS = ["#E69F00", "#D55E00", "#009E73", "#0072B2", "#CC79A7", "#56B4E9", "#F0E442", "#666666"]


def _circle(axis):
    phase = np.linspace(0.0, 2.0 * np.pi, 361)
    axis.plot(np.cos(phase), np.sin(phase), "--", color="#999999", linewidth=0.9, label="reference circle")
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlim(-1.35, 1.35); axis.set_ylim(-1.35, 1.35)
    axis.set_xlabel("I / A"); axis.set_ylabel("Q / A")
    axis.tick_params(which="both", direction="out", width=0.8)


def main():
    _, displacement, _, _ = simulate_response()
    radar_step = round(REFERENCE_RATE_HZ / RADAR_RATE_HZ)
    displacement = displacement[::radar_step]
    target_iq, target_phase, _ = _target_iq(
        displacement, TARGET_ANGLES_DEG[0], TARGET_AMPLITUDES[0], TARGET_SNR_DB[0],
        np.random.default_rng(2026),
    )
    target_iq /= TARGET_AMPLITUDES[0]
    time = np.arange(displacement.size) / RADAR_RATE_HZ
    entry = (time >= 0.5) & (time < 0.8)
    plateau = (time >= 1.0) & (time < 1.3)

    # Controlled reference only: 50 Hz, 100 um and 2 kHz, similar to mmVib's lab setting.
    fs = 2000.0
    t_ref = np.arange(200) / fs
    q_ref = 100e-6 * np.sin(2.0 * np.pi * 50.0 * t_ref)
    base_phase = 4.0 * np.pi * q_ref / WAVELENGTH_M
    rng = np.random.default_rng(2026)

    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "black",
        "axes.linewidth": 0.8, "axes.grid": False, "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "savefig.facecolor": "white",
    })
    figure, axes = plt.subplots(1, 3, figsize=(11.0, 3.8))
    for axis in axes:
        _circle(axis)

    axes[0].plot(target_iq[entry].real, target_iq[entry].imag, color="#0072B2", linewidth=0.9)
    axes[0].plot(np.cos(target_phase[entry]), np.sin(target_phase[entry]), color="#111111", linewidth=1.0)
    axes[0].set_title(f"A20 entry segment\nraw 200 Hz, {TARGET_SNR_DB[0]:g} dB")
    axes[0].text(0.04, 0.04, "60 samples, phase span 311°", transform=axes[0].transAxes, fontsize=8)

    axes[1].plot(target_iq[plateau].real, target_iq[plateau].imag, color="#D55E00", linewidth=0.9)
    axes[1].plot(np.cos(target_phase[plateau]), np.sin(target_phase[plateau]), color="#111111", linewidth=1.0)
    axes[1].set_title(f"A20 plateau segment\nraw 200 Hz, {TARGET_SNR_DB[0]:g} dB")
    axes[1].text(0.04, 0.04, "60 samples, phase span 5.5°", transform=axes[1].transAxes, fontsize=8)

    for g, color in enumerate(MMVIB_COLORS):
        phase = base_phase + (g - 3.5) * 0.12
        noise = 0.07 / np.sqrt(2.0) * (rng.standard_normal(t_ref.size) + 1j * rng.standard_normal(t_ref.size))
        signal = np.exp(1j * phase) + noise
        axes[2].plot(signal.real, signal.imag, color=color, linewidth=0.9, label=f"chirp {g + 1}")
    axes[2].set_title("Controlled reference\n50 Hz, 100 μm, 2 kHz")
    axes[2].legend(frameon=False, fontsize=7, ncol=2, loc="lower left")
    axes[2].text(0.04, 0.93, "8 colored coherent traces", transform=axes[2].transAxes, fontsize=8, va="top")

    figure.suptitle("mmVib-inspired IQ presentation: raw A20 versus controlled reference", fontsize=11)
    figure.subplots_adjust(top=0.78, bottom=0.12, left=0.055, right=0.98, wspace=0.30)
    output = ROOT / "reports/numerical_simulation_assets_png/iq_mmvib_style_comparison.png"
    figure.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
