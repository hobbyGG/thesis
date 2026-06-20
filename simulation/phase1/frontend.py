from dataclasses import dataclass, replace
from typing import Optional, Sequence, Tuple

import numpy as np

from .config import Phase1Config
from .radar import RadarAlgorithmInput
from .truth import TruthSignal


@dataclass(frozen=True)
class FrontendConfig:
    """Configuration for the Phase-1 synthetic range-angle frontend.

    The ADC fields describe synthetic fast-time samples inside a chirp, while
    Phase1Config.sample_rate_hz describes the slow-time frame/Kalman rate.
    """

    num_virtual_rx: int = 8
    num_adc_samples: int = 256
    adc_sample_rate_hz: float = 6.0e6
    chirp_duration_s: float = 60.0e-6
    chirps_per_frame: int = 4
    num_range_bins: int = 64
    num_angle_bins: int = 64
    range_resolution_m: float = 0.15
    antenna_spacing_wavelengths: float = 0.5
    radar_mount: str = "downward"
    noise_power: float = 0.0
    use_phase1_snr: bool = True
    default_range_bin_start: int = 4


@dataclass(frozen=True)
class ScattererTruth:
    range_m: float
    angle_deg: float
    amplitude: float = 1.0
    phase_bias_rad: float = 0.0
    kappa: Optional[float] = None
    measured_kappa: Optional[float] = None
    snr_db: float = np.inf
    target_index: int = 0
    range_bin_index: Optional[int] = None


@dataclass(frozen=True)
class ADCCubeObservation:
    adc_cube: np.ndarray
    range_axis_m: np.ndarray
    frame_times_s: np.ndarray
    scatterers: Tuple[ScattererTruth, ...]


@dataclass(frozen=True)
class RangeAngleObservation:
    range_angle_cube: np.ndarray
    range_axis_m: np.ndarray
    angle_axis_deg: np.ndarray
    spatial_frequency_axis: np.ndarray
    frame_times_s: np.ndarray


@dataclass(frozen=True)
class FrontendTargetObservation:
    measured_kappa: np.ndarray
    slow_time: np.ndarray
    wrapped_phase_rad: np.ndarray
    available_mask: np.ndarray
    range_bins: np.ndarray
    angle_bins: np.ndarray
    range_m: np.ndarray
    angle_deg: np.ndarray
    target_reference_indices: Optional[np.ndarray] = None


def angle_deg_to_measured_kappa(angle_deg, radar_mount: str = "downward"):
    """Map an angle estimate into the kappa used by Phase-1 estimators."""

    if radar_mount != "downward":
        raise ValueError(f"unsupported radar_mount: {radar_mount}")

    angle_arr = np.asarray(angle_deg, dtype=float)
    kappa = np.cos(np.deg2rad(angle_arr))
    if np.isscalar(angle_deg):
        return float(kappa)
    return kappa


def range_axis_m(frontend_config: FrontendConfig) -> np.ndarray:
    _validate_frontend_config(frontend_config)
    return np.arange(frontend_config.num_range_bins, dtype=float) * float(frontend_config.range_resolution_m)


def spatial_frequency_axis(frontend_config: FrontendConfig) -> np.ndarray:
    _validate_frontend_config(frontend_config)
    return np.fft.fftshift(np.fft.fftfreq(frontend_config.num_angle_bins, d=1.0))


def angle_axis_deg(frontend_config: FrontendConfig) -> np.ndarray:
    _validate_frontend_config(frontend_config)
    spatial = spatial_frequency_axis(frontend_config)
    sin_angle = spatial / float(frontend_config.antenna_spacing_wavelengths)
    return np.rad2deg(np.arcsin(np.clip(sin_angle, -1.0, 1.0)))


def build_default_scatterers(
    truth: TruthSignal,
    phase1_config: Phase1Config,
    frontend_config: FrontendConfig,
) -> Tuple[ScattererTruth, ...]:
    """Create default frontend scatterers from Phase1Config targets."""

    del truth
    count = int(phase1_config.num_targets)
    angles_deg = _fit_sequence(phase1_config.target_angles_deg, count, "target_angles_deg")
    snr_db = _fit_sequence(phase1_config.target_snr_db, count, "target_snr_db")
    amplitudes = _fit_sequence(phase1_config.target_amplitudes, count, "target_amplitudes")
    if len(phase1_config.target_range_bins) > 0:
        range_bins = _fit_sequence(phase1_config.target_range_bins, count, "target_range_bins").astype(int)
    else:
        range_bins = _default_range_bins(count, frontend_config)

    bias_rng = np.random.default_rng(phase1_config.seed + 2)
    biases = bias_rng.uniform(-np.pi, np.pi, size=count)

    scatterers = []
    for idx in range(count):
        range_bin = int(range_bins[idx])
        angle_deg = float(angles_deg[idx])
        scatterers.append(
            ScattererTruth(
                range_m=range_bin * float(frontend_config.range_resolution_m),
                angle_deg=angle_deg,
                amplitude=float(amplitudes[idx]),
                phase_bias_rad=float(biases[idx]),
                kappa=float(angle_deg_to_measured_kappa(angle_deg, frontend_config.radar_mount)),
                measured_kappa=float(
                    angle_deg_to_measured_kappa(
                        angle_deg + float(phase1_config.aoa_error_deg),
                        frontend_config.radar_mount,
                    )
                ),
                snr_db=float(snr_db[idx]),
                target_index=idx,
                range_bin_index=range_bin,
            )
        )

    if phase1_config.enable_mixed_scatterer_target:
        scatterers = _with_mixed_scatterer_target(scatterers, phase1_config, frontend_config)

    return tuple(scatterers)


def simulate_adc_cube(
    truth: TruthSignal,
    phase1_config: Phase1Config,
    frontend_config: FrontendConfig = FrontendConfig(),
    scatterers: Optional[Sequence[ScattererTruth]] = None,
) -> ADCCubeObservation:
    """Generate a complex ADC cube with axes (frame, virtual_rx, adc_sample)."""

    _validate_frontend_config(frontend_config)
    if scatterers is None:
        normalized_scatterers = build_default_scatterers(truth, phase1_config, frontend_config)
    else:
        normalized_scatterers = _normalize_scatterers(scatterers, frontend_config)

    n_frames = int(np.asarray(truth.t).size)
    adc_cube = np.zeros(
        (n_frames, frontend_config.num_virtual_rx, frontend_config.num_adc_samples),
        dtype=complex,
    )
    if n_frames == 0:
        return ADCCubeObservation(
            adc_cube=adc_cube,
            range_axis_m=range_axis_m(frontend_config),
            frame_times_s=np.asarray(truth.t, dtype=float).copy(),
            scatterers=normalized_scatterers,
        )

    theta = 4.0 * np.pi * np.asarray(truth.q_m, dtype=float) / phase1_config.wavelength_m()
    rx_index = np.arange(frontend_config.num_virtual_rx, dtype=float)
    adc_index = np.arange(frontend_config.num_adc_samples, dtype=float)
    target_noise_rng = np.random.default_rng(phase1_config.seed + 37)
    degraded_targets = {int(idx) for idx in phase1_config.degraded_target_indices}
    dropout_targets = {int(idx) for idx in phase1_config.dropout_target_indices}
    in_degradation = (truth.t >= phase1_config.degradation_start_s) & (truth.t <= phase1_config.degradation_end_s)
    in_dropout = (truth.t >= phase1_config.dropout_start_s) & (truth.t <= phase1_config.dropout_end_s)
    degradation_factor = 10.0 ** (float(phase1_config.degradation_snr_drop_db) / 20.0)

    for scatterer in normalized_scatterers:
        range_bin = float(scatterer.range_m) / float(frontend_config.range_resolution_m)
        range_tone = np.exp(2j * np.pi * range_bin * adc_index / float(frontend_config.num_range_bins))

        spatial_frequency = float(frontend_config.antenna_spacing_wavelengths) * np.sin(
            np.deg2rad(float(scatterer.angle_deg))
        )
        angle_tone = np.exp(2j * np.pi * spatial_frequency * rx_index)

        los_phase = float(scatterer.kappa) * theta + float(scatterer.phase_bias_rad)
        slow_time = float(scatterer.amplitude) * np.exp(1j * los_phase)
        if frontend_config.use_phase1_snr and np.isfinite(scatterer.snr_db):
            snr_linear = 10.0 ** (float(scatterer.snr_db) / 10.0)
            noise_std = float(scatterer.amplitude) / np.sqrt(2.0 * snr_linear)
            noise_scale = np.full(n_frames, noise_std, dtype=float)
            if int(scatterer.target_index) in degraded_targets:
                noise_scale[in_degradation] = noise_std * degradation_factor
            slow_time = slow_time + noise_scale * (
                target_noise_rng.standard_normal(n_frames) + 1j * target_noise_rng.standard_normal(n_frames)
            )
        if int(scatterer.target_index) in dropout_targets:
            slow_time = slow_time.copy()
            slow_time[in_dropout] = 0.0
        adc_cube += slow_time[:, None, None] * angle_tone[None, :, None] * range_tone[None, None, :]

    noise_power = _adc_noise_power(normalized_scatterers, frontend_config)
    if noise_power > 0.0:
        rng = np.random.default_rng(phase1_config.seed + 31)
        noise_std = np.sqrt(noise_power / 2.0)
        noise = noise_std * (
            rng.standard_normal(adc_cube.shape) + 1j * rng.standard_normal(adc_cube.shape)
        )
        adc_cube += noise

    return ADCCubeObservation(
        adc_cube=adc_cube,
        range_axis_m=range_axis_m(frontend_config),
        frame_times_s=np.asarray(truth.t, dtype=float).copy(),
        scatterers=normalized_scatterers,
    )


def range_angle_process(
    adc: ADCCubeObservation,
    frontend_config: FrontendConfig = FrontendConfig(),
) -> RangeAngleObservation:
    """Apply range FFT followed by spatial-frequency angle FFT/DBF."""

    _validate_frontend_config(frontend_config)
    adc_cube = np.asarray(adc.adc_cube, dtype=complex)
    if adc_cube.ndim != 3:
        raise ValueError("adc_cube must have shape (num_frames, num_virtual_rx, num_adc_samples)")
    if adc_cube.shape[1] != frontend_config.num_virtual_rx:
        raise ValueError("adc_cube virtual RX axis does not match frontend_config")
    if adc_cube.shape[2] != frontend_config.num_adc_samples:
        raise ValueError("adc_cube ADC sample axis does not match frontend_config")

    range_fft = np.fft.fft(adc_cube, n=frontend_config.num_range_bins, axis=2)
    range_by_rx = np.transpose(range_fft, (0, 2, 1))
    angle_fft = np.fft.fft(range_by_rx, n=frontend_config.num_angle_bins, axis=2)
    range_angle_cube = np.fft.fftshift(angle_fft, axes=2)
    range_angle_cube = range_angle_cube / float(frontend_config.num_adc_samples * frontend_config.num_virtual_rx)

    return RangeAngleObservation(
        range_angle_cube=range_angle_cube.astype(complex),
        range_axis_m=range_axis_m(frontend_config),
        angle_axis_deg=angle_axis_deg(frontend_config),
        spatial_frequency_axis=spatial_frequency_axis(frontend_config),
        frame_times_s=adc.frame_times_s.copy(),
    )


def extract_frontend_target_observation(
    range_angle: RangeAngleObservation,
    range_bins: Sequence[int],
    angle_bins: Sequence[int],
    radar_mount: str = "downward",
    magnitude_threshold: float = 0.0,
    target_reference_indices: Optional[Sequence[int]] = None,
) -> FrontendTargetObservation:
    """Extract target slow-time series from selected range-angle bins."""

    range_bin_arr = np.atleast_1d(np.asarray(range_bins, dtype=int))
    angle_bin_arr = np.atleast_1d(np.asarray(angle_bins, dtype=int))
    if range_bin_arr.size != angle_bin_arr.size:
        raise ValueError("range_bins and angle_bins must have the same length")
    if target_reference_indices is None:
        reference_indices = None
    else:
        reference_indices = np.atleast_1d(np.asarray(target_reference_indices, dtype=int))
        if reference_indices.size != range_bin_arr.size:
            raise ValueError("target_reference_indices must have one value per target")

    cube = np.asarray(range_angle.range_angle_cube, dtype=complex)
    if cube.ndim != 3:
        raise ValueError("range_angle_cube must have shape (num_frames, num_range_bins, num_angle_bins)")

    n_targets = int(range_bin_arr.size)
    slow_time = np.empty((n_targets, cube.shape[0]), dtype=complex)
    for target_idx, (range_bin, angle_bin) in enumerate(zip(range_bin_arr, angle_bin_arr)):
        slow_time[target_idx] = cube[:, int(range_bin), int(angle_bin)]

    available_mask = np.isfinite(slow_time.real) & np.isfinite(slow_time.imag)
    available_mask &= np.abs(slow_time) > float(magnitude_threshold)

    wrapped_phase_rad = np.angle(slow_time).astype(float)
    wrapped_phase_rad[~available_mask] = np.nan

    target_angles_deg = range_angle.angle_axis_deg[angle_bin_arr]
    return FrontendTargetObservation(
        measured_kappa=np.asarray(angle_deg_to_measured_kappa(target_angles_deg, radar_mount), dtype=float),
        slow_time=slow_time,
        wrapped_phase_rad=wrapped_phase_rad,
        available_mask=available_mask,
        range_bins=range_bin_arr.copy(),
        angle_bins=angle_bin_arr.copy(),
        range_m=range_angle.range_axis_m[range_bin_arr].copy(),
        angle_deg=target_angles_deg.copy(),
        target_reference_indices=None if reference_indices is None else reference_indices.copy(),
    )


def to_algorithm_radar_input(frontend_target: FrontendTargetObservation) -> RadarAlgorithmInput:
    """Adapt frontend target observations to the algorithm-visible radar input."""

    return RadarAlgorithmInput(
        measured_kappa=np.asarray(frontend_target.measured_kappa, dtype=float).copy(),
        wrapped_phase_rad=np.asarray(frontend_target.wrapped_phase_rad, dtype=float).copy(),
        available_mask=np.asarray(frontend_target.available_mask, dtype=bool).copy(),
    )


frontend_target_to_algorithm_input = to_algorithm_radar_input


def _validate_frontend_config(frontend_config: FrontendConfig) -> None:
    if frontend_config.num_virtual_rx <= 0:
        raise ValueError("num_virtual_rx must be positive")
    if frontend_config.num_adc_samples <= 0:
        raise ValueError("num_adc_samples must be positive")
    if frontend_config.adc_sample_rate_hz <= 0.0:
        raise ValueError("adc_sample_rate_hz must be positive")
    if frontend_config.chirp_duration_s <= 0.0:
        raise ValueError("chirp_duration_s must be positive")
    if frontend_config.chirps_per_frame <= 0:
        raise ValueError("chirps_per_frame must be positive")
    if frontend_config.num_range_bins <= 0:
        raise ValueError("num_range_bins must be positive")
    if frontend_config.num_angle_bins <= 0:
        raise ValueError("num_angle_bins must be positive")
    if frontend_config.range_resolution_m <= 0.0:
        raise ValueError("range_resolution_m must be positive")
    if frontend_config.antenna_spacing_wavelengths <= 0.0:
        raise ValueError("antenna_spacing_wavelengths must be positive")
    if frontend_config.noise_power < 0.0:
        raise ValueError("noise_power must be non-negative")


def _fit_sequence(values, count: int, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size != count:
        raise ValueError(f"{name} must contain {count} values")
    return arr


def _default_range_bins(count: int, frontend_config: FrontendConfig) -> np.ndarray:
    if count <= 0:
        return np.asarray([], dtype=int)

    first = min(max(int(frontend_config.default_range_bin_start), 0), frontend_config.num_range_bins - 1)
    if count == 1:
        return np.asarray([first], dtype=int)

    last = max(first, frontend_config.num_range_bins - 2)
    return np.rint(np.linspace(first, last, count)).astype(int)


def _normalize_scatterers(
    scatterers: Sequence[ScattererTruth],
    frontend_config: FrontendConfig,
) -> Tuple[ScattererTruth, ...]:
    normalized = []
    for idx, scatterer in enumerate(scatterers):
        kappa = scatterer.kappa
        if kappa is None:
            kappa = float(angle_deg_to_measured_kappa(scatterer.angle_deg, frontend_config.radar_mount))

        measured_kappa = scatterer.measured_kappa
        if measured_kappa is None:
            measured_kappa = float(angle_deg_to_measured_kappa(scatterer.angle_deg, frontend_config.radar_mount))

        range_bin_index = scatterer.range_bin_index
        if range_bin_index is None:
            range_bin_index = int(round(float(scatterer.range_m) / float(frontend_config.range_resolution_m)))

        normalized.append(
            replace(
                scatterer,
                kappa=float(kappa),
                measured_kappa=float(measured_kappa),
                target_index=int(scatterer.target_index if scatterer.target_index is not None else idx),
                range_bin_index=int(range_bin_index),
            )
        )
    return tuple(normalized)


def _adc_noise_power(scatterers: Sequence[ScattererTruth], frontend_config: FrontendConfig) -> float:
    noise_power = float(frontend_config.noise_power)
    if not frontend_config.use_phase1_snr:
        return noise_power

    for scatterer in scatterers:
        if np.isfinite(scatterer.snr_db):
            snr_linear = 10.0 ** (float(scatterer.snr_db) / 10.0)
            noise_power += float(scatterer.amplitude) ** 2 / snr_linear
    return noise_power


def _with_mixed_scatterer_target(
    scatterers: Sequence[ScattererTruth],
    phase1_config: Phase1Config,
    frontend_config: FrontendConfig,
) -> list[ScattererTruth]:
    idx = int(phase1_config.mixed_target_index)
    if idx < 0 or idx >= len(scatterers):
        raise ValueError("mixed_target_index out of range")

    kappas = np.asarray(phase1_config.mixed_scatterer_kappas, dtype=float)
    amps = np.asarray(phase1_config.mixed_scatterer_amplitudes, dtype=float)
    biases = np.asarray(phase1_config.mixed_scatterer_biases_rad, dtype=float)
    if kappas.size != amps.size or kappas.size != biases.size:
        raise ValueError("mixed scatterer kappas, amplitudes, and biases must have the same length")

    result = [scatterer for scatterer in scatterers if scatterer.target_index != idx]
    base = scatterers[idx]
    for kappa, amplitude, bias in zip(kappas, amps, biases):
        angle_deg = float(np.rad2deg(np.arccos(np.clip(kappa, -1.0, 1.0))))
        result.append(
            ScattererTruth(
                range_m=base.range_m,
                angle_deg=angle_deg,
                amplitude=float(amplitude),
                phase_bias_rad=float(bias),
                kappa=float(kappa),
                measured_kappa=float(angle_deg_to_measured_kappa(angle_deg, frontend_config.radar_mount)),
                snr_db=base.snr_db,
                target_index=idx,
                range_bin_index=base.range_bin_index,
            )
        )
    return result
