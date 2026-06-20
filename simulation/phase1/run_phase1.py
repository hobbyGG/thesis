import argparse
from pathlib import Path

import numpy as np

from .accelerometer import simulate_accelerometer
from .config import Phase1Config
from .algorithm import cold_start_reference_mean
from .radar import simulate_radar_targets
from .truth import generate_multifrequency_truth


def run(output_path: Path, config: Phase1Config) -> None:
    truth = generate_multifrequency_truth(config)
    radar = simulate_radar_targets(truth, config)
    accel = simulate_accelerometer(truth, config)
    q_ref_m = cold_start_reference_mean(truth.q_m, config)
    delta_q_m = truth.q_m - q_ref_m
    delta_main_phase_rad = 4.0 * np.pi * delta_q_m / config.wavelength_m()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        t=truth.t,
        q_m=truth.q_m,
        q_ref_m=np.asarray(q_ref_m),
        delta_q_m=delta_q_m,
        v_mps=truth.v_mps,
        a_true_mps2=truth.a_mps2,
        a_meas_mps2=accel.measured_mps2,
        frequencies_hz=np.asarray(truth.frequencies_hz),
        amplitudes_m=np.asarray(truth.amplitudes_m),
        phases_rad=np.asarray(truth.phases_rad),
        kappa=radar.kappa,
        target_angles_deg=radar.target_angles_deg,
        target_snr_db=radar.snr_db,
        main_phase_rad=radar.true_main_phase_rad,
        delta_main_phase_rad=delta_main_phase_rad,
        los_phase_rad=radar.true_los_phase_rad,
        wrapped_phase_rad=radar.wrapped_phase_rad,
        iq=radar.iq,
    )

    print(f"saved: {output_path}")
    print("component frequencies (Hz):", ", ".join(f"{f:.2f}" for f in truth.frequencies_hz))
    print(f"q peak-to-peak: {(truth.q_m.max() - truth.q_m.min()) * 1e3:.4f} mm")
    print(f"wrapped phase shape: {radar.wrapped_phase_rad.shape}")
    print("target kappa:", ", ".join(f"{v:.4f}" for v in radar.kappa))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run phase-1 multifrequency radar simulation.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("simulation/outputs/phase1_multifrequency.npz"),
        help="Path to the generated npz data file.",
    )
    args = parser.parse_args()
    run(args.output, Phase1Config())


if __name__ == "__main__":
    main()
