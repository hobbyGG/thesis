from dataclasses import dataclass
from typing import Optional

import numpy as np

from .config import Phase1Config
from .truth import TruthSignal


@dataclass(frozen=True)
class RadarObservation:
    kappa: np.ndarray
    measured_kappa: np.ndarray
    target_angles_deg: np.ndarray
    snr_db: np.ndarray
    true_main_phase_rad: np.ndarray
    true_los_phase_rad: np.ndarray
    iq: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray


@dataclass(frozen=True)
class RadarAlgorithmInput:
    measured_kappa: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    selected_indices: Optional[np.ndarray] = None
    initial_r: Optional[np.ndarray] = None
    selection_scores: Optional[np.ndarray] = None


def to_algorithm_radar_input(radar: RadarObservation) -> RadarAlgorithmInput:
    return RadarAlgorithmInput(
        measured_kappa=radar.measured_kappa.copy(),
        wrapped_phase_rad=radar.wrapped_phase_rad.copy(),
        available_mask=radar.available_mask.copy(),
    )


def _fit_sequence(values, count: int, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size != count:
        raise ValueError(f"{name} must contain {count} values")
    return arr


def simulate_radar_targets(truth: TruthSignal, config: Phase1Config) -> RadarObservation:
    """Generate noisy complex radar observations and wrapped phases for each target."""

    angles_deg = _fit_sequence(config.target_angles_deg, config.num_targets, "target_angles_deg")
    snr_db = _fit_sequence(config.target_snr_db, config.num_targets, "target_snr_db")
    amplitudes = _fit_sequence(config.target_amplitudes, config.num_targets, "target_amplitudes")

    kappa = np.cos(np.deg2rad(angles_deg))
    measured_angles_deg = angles_deg + float(config.aoa_error_deg)
    measured_kappa = np.cos(np.deg2rad(measured_angles_deg))
    wavelength_m = config.wavelength_m()
    true_main_phase_rad = 4.0 * np.pi * truth.q_m / wavelength_m

    bias_rng = np.random.default_rng(config.seed + 2)
    target_bias = bias_rng.uniform(-np.pi, np.pi, size=config.num_targets)
    true_los_phase_rad = kappa[:, None] * true_main_phase_rad[None, :] + target_bias[:, None]

    clean_iq = amplitudes[:, None] * np.exp(1j * true_los_phase_rad)
    if config.enable_mixed_scatterer_target:
        idx = int(config.mixed_target_index)
        kappas = np.asarray(config.mixed_scatterer_kappas, dtype=float)
        amps = np.asarray(config.mixed_scatterer_amplitudes, dtype=float)
        biases = np.asarray(config.mixed_scatterer_biases_rad, dtype=float)
        if kappas.size != amps.size or kappas.size != biases.size:
            raise ValueError("mixed scatterer kappas, amplitudes, and biases must have the same length")
        mixed = np.zeros_like(clean_iq[idx])
        for scatter_kappa, scatter_amp, scatter_bias in zip(kappas, amps, biases):
            mixed += scatter_amp * np.exp(1j * (scatter_kappa * true_main_phase_rad + scatter_bias))
        clean_iq[idx] = mixed

    snr_linear = 10.0 ** (snr_db / 10.0)
    noise_std = amplitudes / np.sqrt(2.0 * snr_linear)

    noise_rng = np.random.default_rng(config.seed + 3)
    noise = noise_std[:, None] * (
        noise_rng.standard_normal(clean_iq.shape) + 1j * noise_rng.standard_normal(clean_iq.shape)
    )
    available_mask = np.ones(clean_iq.shape, dtype=bool)
    if config.degraded_target_indices:
        in_degradation = (truth.t >= config.degradation_start_s) & (truth.t <= config.degradation_end_s)
        factor = 10.0 ** (float(config.degradation_snr_drop_db) / 20.0)
        for idx in config.degraded_target_indices:
            noise[int(idx), in_degradation] *= factor
    if config.dropout_target_indices:
        in_dropout = (truth.t >= config.dropout_start_s) & (truth.t <= config.dropout_end_s)
        for idx in config.dropout_target_indices:
            available_mask[int(idx), in_dropout] = False

    iq = clean_iq + noise
    wrapped_phase_rad = np.angle(iq)
    wrapped_phase_rad = wrapped_phase_rad.astype(float)
    wrapped_phase_rad[~available_mask] = np.nan
    iq = iq.astype(complex)
    iq[~available_mask] = np.nan + 1j * np.nan

    return RadarObservation(
        kappa=kappa,
        measured_kappa=measured_kappa,
        target_angles_deg=angles_deg,
        snr_db=snr_db,
        true_main_phase_rad=true_main_phase_rad,
        true_los_phase_rad=true_los_phase_rad,
        iq=iq,
        wrapped_phase_rad=wrapped_phase_rad,
        available_mask=available_mask,
    )
