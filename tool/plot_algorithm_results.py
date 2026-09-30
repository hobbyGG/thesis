"""Plot the retained A20 parameterized simulation's algorithm diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper_bridge_simulation.package_builder import TARGET_SNR_DB  # noqa: E402


def plot_results(result_path: str | Path, output: str | Path) -> Path:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("matplotlib is required; run `uv run --with matplotlib python tool/plot_algorithm_results.py`") from exc

    data = np.load(result_path)
    time_s = np.asarray(data["time_s"], dtype=float)
    truth = np.asarray(data["truth_displacement_m"], dtype=float)
    estimate = np.asarray(data["q_hat_m"], dtype=float)
    reference = float(np.mean(truth[: max(1, round(0.2 * 200.0))]))
    truth_relative = truth - reference
    error_um = (estimate - truth_relative) * 1e6
    innovation = np.asarray(data["innovation_rad"], dtype=float)
    r_history = np.asarray(data["r_theta_history"], dtype=float)
    selected = np.asarray(data["selected_target_indices"], dtype=int)
    angles = np.asarray(data["target_angle_deg"], dtype=float)
    ranges = np.asarray(data["target_range_m"], dtype=float)
    beta = np.asarray(data["beta_hat"], dtype=float)

    rms_innovation = np.array([
        np.sqrt(np.nanmean(innovation[i] ** 2)) if np.any(np.isfinite(innovation[i])) else np.nan
        for i in selected
    ])

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

    axes[0].plot(time_s, truth_relative * 1e3, color=grey, linewidth=1.0, label="truth")
    axes[0].plot(time_s, estimate * 1e3, color=blue, linewidth=1.0, label="estimate")
    axes[0].set_title("Structural displacement")
    axes[0].set_xlabel("Time (s)"); axes[0].set_ylabel("Displacement (mm)")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].plot(time_s, error_um, color=orange, linewidth=0.9)
    axes[1].axhline(0.0, color="black", linewidth=0.7)
    axes[1].set_title(f"Estimation error (RMSE = {np.sqrt(np.mean(error_um ** 2)):.2f} $\\mu$m)")
    axes[1].set_xlabel("Time (s)"); axes[1].set_ylabel("Error ($\\mu$m)")

    labels = [f"{angles[i]:g}°\n{ranges[i]:.2f} m" for i in selected]
    bars = axes[2].bar(np.arange(selected.size), rms_innovation, color=blue, width=0.65)
    axes[2].set_xticks(np.arange(selected.size), labels)
    axes[2].set_title("Per-target innovation RMS")
    axes[2].set_xlabel("Selected target (angle / range)"); axes[2].set_ylabel("Phase residual (rad)")
    for bar, snr in zip(bars, TARGET_SNR_DB[selected]):
        axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{snr:g} dB", ha="center", va="bottom", fontsize=8)

    for i in selected:
        axes[3].plot(time_s, r_history[i], linewidth=0.9, label=f"{angles[i]:g}°")
    axes[3].set_yscale("log")
    axes[3].set_title("Adaptive phase measurement variance $R_i$")
    axes[3].set_xlabel("Time (s)"); axes[3].set_ylabel("Variance (rad$^2$)")
    axes[3].legend(frameon=False, fontsize=7, ncol=2)

    for axis in axes:
        axis.tick_params(which="both", direction="out", width=0.8)
        for spine in axis.spines.values():
            spine.set_linewidth(0.8)
    figure.suptitle("A20 parameterized guideway: algorithm diagnostics", fontsize=11, fontweight="normal")
    figure.subplots_adjust(top=0.88, bottom=0.14, left=0.08, right=0.98, wspace=0.28, hspace=0.38)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"saved {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/numerical_simulation_assets_png/a20_algorithm_diagnostics.png")
    args = parser.parse_args()
    plot_results(args.result, args.output)


if __name__ == "__main__":
    main()
