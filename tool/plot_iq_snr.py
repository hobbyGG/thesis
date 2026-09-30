"""Plot the simulated target IQ trajectories for the configured SNR values.

The slow-time target signal follows the same model as
``paper_bridge_simulation.package_builder._radar_package``:

    s(t) = A exp(j(theta(t) / beta + bias)) + n(t)

where the real and imaginary parts of ``n`` have standard deviation
``A / sqrt(2 * SNR_linear)``. The points are normalized by ``A`` in the
figure so that the change in cloud thickness is caused by SNR rather than by
the target amplitudes.

The figure intentionally uses a restrained MATLAB-like style suitable for a
paper: white background, a single blue connected trajectory, no diagnostic
color bar, and a black dashed reference circle. Connecting the samples is
important here: it shows the temporal IQ path and makes the low-SNR radial
jumps visible, in the same spirit as the IQ trajectories in mmVib.

The default displacement is the A20 paper-parameterized guideway response;
``--source sine`` remains available for a controlled single-frequency figure.
This is a plotting helper only. It does not create or modify a capture
package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper_bridge_simulation.package_builder import (  # noqa: E402
    RADAR_RATE_HZ,
    TARGET_AMPLITUDES,
    TARGET_ANGLES_DEG,
    TARGET_SNR_DB,
    WAVELENGTH_M,
)
from paper_bridge_simulation.response import REFERENCE_RATE_HZ, simulate_response  # noqa: E402


def _target_iq(
    displacement_m: np.ndarray,
    angle_deg: float,
    amplitude: float,
    snr_db: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Generate one target's slow-time IQ and its noiseless phase."""

    beta = 1.0 / abs(np.cos(np.deg2rad(angle_deg)))
    bias = rng.uniform(-np.pi, np.pi)
    ideal_phase = 4.0 * np.pi * displacement_m / WAVELENGTH_M / beta + bias
    noise_std = amplitude / np.sqrt(2.0 * 10.0 ** (snr_db / 10.0))
    noise = noise_std * (rng.standard_normal(displacement_m.size) + 1j * rng.standard_normal(displacement_m.size))
    return amplitude * np.exp(1j * ideal_phase) + noise, ideal_phase, noise_std


def _load_displacement(
    *,
    source: str,
    duration_s: float,
    frames: int,
    sample_rate_hz: float,
    frequency_hz: float,
    amplitude_um: float,
) -> tuple[np.ndarray, float, str]:
    """Return a displacement sequence and the sampling rate used for plotting."""

    if source == "paper":
        _, displacement, _, _ = simulate_response()
        radar_step = round(REFERENCE_RATE_HZ / RADAR_RATE_HZ)
        count = min(displacement.size // radar_step, round(duration_s * RADAR_RATE_HZ), frames)
        if count < 2:
            raise ValueError("duration_s does not contain enough radar frames")
        return displacement[::radar_step][:count], RADAR_RATE_HZ, "A20 paper-parameterized guideway response"

    if source == "sine":
        if sample_rate_hz <= 2.0 * frequency_hz:
            raise ValueError("sample_rate_hz must be greater than twice frequency_hz")
        count = min(round(duration_s * sample_rate_hz), frames)
        if count < 2:
            raise ValueError("duration_s does not contain enough synthetic samples")
        time_s = np.arange(count, dtype=float) / sample_rate_hz
        displacement = amplitude_um * 1.0e-6 * np.sin(2.0 * np.pi * frequency_hz * time_s)
        return displacement, sample_rate_hz, f"synthetic {amplitude_um:g} um, {frequency_hz:g} Hz vibration"

    raise ValueError(f"unknown source {source!r}; choose 'paper' or 'sine'")


def plot_iq_snr(
    output: str | Path,
    *,
    duration_s: float = 4.0,
    frames: int = 800,
    seed: int = 2026,
    source: str = "paper",
    sample_rate_hz: float = 2000.0,
    frequency_hz: float = 50.0,
    amplitude_um: float = 100.0,
) -> Path:
    """Create and save the multi-SNR IQ figure, returning its path."""

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - depends on local plotting environment
        raise SystemExit(
            "matplotlib is required for this plotting helper; run it with "
            "`uv run --with matplotlib python tool/plot_iq_snr.py`"
        ) from exc

    if frames < 2:
        raise ValueError("frames must be at least 2")
    if duration_s <= 0.0:
        raise ValueError("duration_s must be positive")

    frame_displacement, actual_sample_rate_hz, source_label = _load_displacement(
        source=source,
        duration_s=duration_s,
        frames=frames,
        sample_rate_hz=sample_rate_hz,
        frequency_hz=frequency_hz,
        amplitude_um=amplitude_um,
    )

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "black",
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "savefig.facecolor": "white",
        }
    )

    rng = np.random.default_rng(seed)
    figure, axes_grid = plt.subplots(2, 3, figsize=(10.0, 6.0), sharex=True, sharey=True)
    axes = axes_grid.ravel()
    matlab_blue = "#0072BD"
    circle_phase = np.linspace(0.0, 2.0 * np.pi, 361)
    stats: list[str] = []
    handles = None

    for axis, angle_deg, amplitude, snr_db in zip(
        axes[: TARGET_SNR_DB.size], TARGET_ANGLES_DEG, TARGET_AMPLITUDES, TARGET_SNR_DB
    ):
        iq, ideal_phase, noise_std = _target_iq(frame_displacement, angle_deg, amplitude, snr_db, rng)
        normalized_iq = iq / amplitude
        radial_error = np.abs(normalized_iq) - 1.0
        expected_radial_std = noise_std / amplitude
        stats.append(
            f"{snr_db:.0f} dB: radial std {np.std(radial_error):.3f} "
            f"(high-SNR approximation {expected_radial_std:.3f})"
        )

        ideal_circle, = axis.plot(
            np.cos(circle_phase),
            np.sin(circle_phase),
            linestyle="--",
            color="black",
            linewidth=1.0,
        )
        ideal_path, = axis.plot(
            np.cos(ideal_phase),
            np.sin(ideal_phase),
            color="#7F7F7F",
            linewidth=0.8,
        )
        noisy_iq, = axis.plot(
            normalized_iq.real,
            normalized_iq.imag,
            linestyle="-",
            color=matlab_blue,
            linewidth=1.0,
            alpha=0.80,
        )
        if handles is None:
            handles = (noisy_iq, ideal_circle, ideal_path)
        axis.set_title(f"SNR = {snr_db:.0f} dB", fontweight="normal")
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlim(-1.8, 1.8)
        axis.set_ylim(-1.8, 1.8)
        axis.tick_params(which="both", direction="out", width=0.8)
        for spine in axis.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)
        axis.text(
            0.03,
            0.04,
            f"A={amplitude:.2f}, sigma_r={np.std(radial_error):.3f}",
            transform=axis.transAxes,
            fontsize=8,
            color="#333333",
        )

    axes[-1].axis("off")
    for axis in axes:
        if axis.axison:
            axis.set_xlabel("I / A")
            axis.set_ylabel("Q / A")
    figure.suptitle(
        f"Target IQ trajectories: {source_label}\n"
        f"({frame_displacement.size} samples at {actual_sample_rate_hz:g} Hz)",
        fontsize=11,
        fontweight="normal",
    )
    if handles is not None:
        figure.legend(
            handles,
            ("noisy IQ trajectory", "unit circle", "ideal trajectory"),
            loc="lower center",
            ncol=3,
            frameon=False,
            fontsize=8,
            bbox_to_anchor=(0.5, 0.01),
        )
    figure.subplots_adjust(top=0.88, bottom=0.13, left=0.07, right=0.98, wspace=0.25, hspace=0.35)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"saved {output_path}")
    for line in stats:
        print(line)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/numerical_simulation_assets_png/iq_snr_target_comparison.png",
    )
    parser.add_argument("--duration", type=float, default=4.0, help="paper-response duration available to the plot")
    parser.add_argument("--frames", type=int, default=800, help="number of samples/frames to draw")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--source",
        choices=("paper", "sine"),
        default="paper",
        help="A20 paper-parameterized response or a controlled sinusoid",
    )
    parser.add_argument("--sample-rate-hz", type=float, default=2000.0, help="sample rate for --source sine")
    parser.add_argument("--frequency-hz", type=float, default=50.0, help="frequency for --source sine")
    parser.add_argument("--amplitude-um", type=float, default=100.0, help="amplitude for --source sine")
    args = parser.parse_args()
    plot_iq_snr(
        args.output,
        duration_s=args.duration,
        frames=args.frames,
        seed=args.seed,
        source=args.source,
        sample_rate_hz=args.sample_rate_hz,
        frequency_hz=args.frequency_hz,
        amplitude_um=args.amplitude_um,
    )


if __name__ == "__main__":
    main()
