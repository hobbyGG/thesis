"""Plot the A20 paper-parameterized high-speed maglev response."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper_bridge_simulation.response import (  # noqa: E402
    MODAL_FREQUENCIES_HZ,
    excitation_frequencies_hz,
    simulate_response,
)


def plot_response(output: str | Path, csv_output: str | Path) -> Path:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit("matplotlib is required; run `uv run --with matplotlib python tool/simulate_a20_response.py`") from exc

    time_s, displacement, acceleration, modal_displacement = simulate_response()
    sample_rate_hz = 1.0 / np.median(np.diff(time_s))
    frequency = np.fft.rfftfreq(time_s.size, 1.0 / sample_rate_hz)
    displacement_amplitude = 2.0 * np.abs(np.fft.rfft(displacement - displacement.mean())) / time_s.size
    acceleration_amplitude = 2.0 * np.abs(np.fft.rfft(acceleration - acceleration.mean())) / time_s.size
    csv_path = Path(csv_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    header = "time_s,displacement_m,acceleration_mps2," + ",".join(
        f"modal_{value:g}Hz_m" for value in MODAL_FREQUENCIES_HZ
    )
    np.savetxt(csv_path, np.column_stack((time_s, displacement, acceleration, modal_displacement.T)),
               delimiter=",", header=header, comments="")

    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "black",
        "axes.linewidth": 0.8, "axes.grid": False, "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "savefig.facecolor": "white",
    })
    blue, orange, grey, green = "#0072BD", "#D95319", "#7F7F7F", "#009E73"
    figure, axes = plt.subplots(2, 2, figsize=(10.0, 6.4))
    axes = axes.ravel()
    view = time_s <= 3.0
    axes[0].plot(time_s[view], displacement[view] * 1e3, color=blue, linewidth=1.0)
    axes[0].set_title("Guideway displacement")
    axes[0].set_xlabel("Time (s)"); axes[0].set_ylabel("Displacement (mm)")
    axes[1].plot(time_s[view], acceleration[view], color=orange, linewidth=1.0)
    axes[1].set_title("Guideway acceleration (paper-parameterized)")
    axes[1].set_xlabel("Time (s)"); axes[1].set_ylabel("Acceleration (m/s$^2$)")
    axes[2].plot(frequency, displacement_amplitude * 1e3, color=blue, linewidth=1.0)
    axes[2].set_title("Displacement spectrum"); axes[2].set_xlabel("Frequency (Hz)"); axes[2].set_ylabel("Amplitude (mm)")
    axes[3].plot(frequency, acceleration_amplitude, color=orange, linewidth=1.0)
    axes[3].set_title("Acceleration spectrum (paper-parameterized)"); axes[3].set_xlabel("Frequency (Hz)"); axes[3].set_ylabel("Amplitude (m/s$^2$)")
    for axis in axes:
        axis.tick_params(which="both", direction="out", width=0.8)
        for spine in axis.spines.values():
            spine.set_linewidth(0.8)
    for axis in axes[2:]:
        axis.set_xlim(0.0, 100.0)
    for value in MODAL_FREQUENCIES_HZ:
        for axis in axes[2:]:
            axis.axvline(value, color=grey, linestyle="--", linewidth=0.7, alpha=0.7)
    for value in excitation_frequencies_hz():
        for axis in axes[2:]:
            axis.axvline(value, color=green, linestyle=":", linewidth=0.9, alpha=0.9)
    figure.suptitle("A20 high-speed maglev guideway response: 24.768 m, 300 km/h", fontsize=11, fontweight="normal")
    figure.legend(
        (plt.Line2D([], [], color=grey, linestyle="--"), plt.Line2D([], [], color=green, linestyle=":")),
        ("identified modal frequencies", "characteristic excitations"), loc="lower center", ncol=2,
        frameon=False, fontsize=8, bbox_to_anchor=(0.5, 0.005),
    )
    figure.subplots_adjust(top=0.88, bottom=0.14, left=0.08, right=0.98, wspace=0.27, hspace=0.34)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"saved {output_path}")
    print(f"saved {csv_path}")
    print("modal_frequencies_hz=" + ", ".join(f"{v:.2f}" for v in MODAL_FREQUENCIES_HZ))
    print("excitation_frequencies_hz=" + ", ".join(f"{v:.3f}" for v in excitation_frequencies_hz()))
    print(f"max_displacement_mm={np.max(np.abs(displacement)) * 1e3:.6f}")
    print(f"max_acceleration_mps2={np.max(np.abs(acceleration)):.6f}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/numerical_simulation_assets_png/a20_paper_response.png")
    parser.add_argument("--csv", type=Path, default=ROOT / "reports/numerical_simulation_assets_csv/a20_paper_response.csv")
    args = parser.parse_args()
    plot_response(args.output, args.csv)


if __name__ == "__main__":
    main()
