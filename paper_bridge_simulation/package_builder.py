from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import numpy as np

from .response import (
    DURATION_S,
    REFERENCE_RATE_HZ,
    reference_metadata,
    simulate_response,
)
from .scenario import Impairments, Scenario

# Four TX0+TX2 loops are coherently averaged into each slow-time frame.
# Use an integer-friendly 2 ms trigger period for the retained 500 Hz path.
RADAR_FRAME_PERIOD_NS = 2_000_000
RADAR_EXTERNAL_TRIGGER_PERIOD_S = RADAR_FRAME_PERIOD_NS * 1.0e-9
RADAR_RATE_HZ = 1.0 / RADAR_EXTERNAL_TRIGGER_PERIOD_S
RADAR_MINIMUM_FRAME_PERIOD_S = 1.01712e-3
# Both sensors have a nominal 2 ms period; retain their timestamp alignment.
ADXL_RATE_HZ = 500.0
ADXL_PERIOD_NS = round(1.0e9 / ADXL_RATE_HZ)
# The DRDY schedule runs a few samples past the last radar frame so that the
# clock phase and group-delay compensation never leave the end of the radar
# record without a following sample.
ADXL_TAIL_SAMPLES = 4
C_LIGHT_MPS = 299_792_458.0
RADAR_IDLE_TIME_S = 70.0e-6
RADAR_ADC_START_TIME_S = 7.0e-6
# ``rampEndTime`` in the profileCfg line.  ADC sampling ends before this
# value (7 us start plus 256/5.209 MS/s is about 56.1 us).
RADAR_RAMP_END_TIME_S = 57.14e-6
RADAR_TX_CHIRPS_PER_LOOP = 2
RADAR_LOOPS_PER_FRAME = 4
RADAR_CHIRP_CYCLE_S = RADAR_IDLE_TIME_S + RADAR_RAMP_END_TIME_S
RADAR_LOOP_START_INTERVAL_S = RADAR_TX_CHIRPS_PER_LOOP * RADAR_CHIRP_CYCLE_S
BASE_TIME_NS = 1_000_000_000
RADAR_START_FREQUENCY_HZ = 77.0e9
WAVELENGTH_M = C_LIGHT_MPS / RADAR_START_FREQUENCY_HZ
VIRTUAL_RX = 8
ADC_SAMPLES = 256
ADC_SAMPLE_RATE_HZ = 5.209e6
CHIRP_SLOPE_HZ_PER_S = 70.0e12
# The profile bandwidth and the sampled bandwidth are distinct.  The latter
# determines the FFT bin spacing used by the algorithm.
RADAR_BANDWIDTH_HZ = CHIRP_SLOPE_HZ_PER_S * RADAR_RAMP_END_TIME_S
ADC_CAPTURE_TIME_S = ADC_SAMPLES / ADC_SAMPLE_RATE_HZ
ADC_CAPTURE_BANDWIDTH_HZ = CHIRP_SLOPE_HZ_PER_S * ADC_CAPTURE_TIME_S
ADC_BITS = 12
ADC_FULL_SCALE = 2.0
ADC_LSB = 2.0 * ADC_FULL_SCALE / (2**ADC_BITS)
RECEIVER_NOISE_STD = 4.0e-4
RX_GAIN_MISMATCH_DB_STD = 0.5
RX_PHASE_MISMATCH_DEG_STD = 3.0
PLL_PHASE_NOISE_STD_RAD = 2.5e-3
PLL_PHASE_NOISE_RHO = 0.98
ADXL_NOISE_DENSITY_G_PER_SQRT_HZ = 22.5e-6
ADXL_BIAS_MPS2 = np.asarray((4.0e-4, -3.0e-4, 2.0e-4))
ADXL_GROUP_DELAY_S = 3.26e-3  # ADXL355 Rev. D, Table 10, 500 Hz ODR.
ADXL_GROUP_DELAY_NS = round(ADXL_GROUP_DELAY_S * 1.0e9)
RADAR_LOOP_REFERENCE_OFFSET_S = (
    RADAR_IDLE_TIME_S + RADAR_ADC_START_TIME_S
    + (ADC_SAMPLES - 1) / (2.0 * ADC_SAMPLE_RATE_HZ)
    + (RADAR_TX_CHIRPS_PER_LOOP - 1) * (RADAR_IDLE_TIME_S + RADAR_RAMP_END_TIME_S) / 2.0
)
RADAR_APERTURE_CENTER_OFFSET_S = RADAR_LOOP_REFERENCE_OFFSET_S + (RADAR_LOOPS_PER_FRAME - 1) * RADAR_LOOP_START_INTERVAL_S / 2.0
RANGE_RESOLUTION_M = C_LIGHT_MPS * ADC_SAMPLE_RATE_HZ / (2.0 * CHIRP_SLOPE_HZ_PER_S * ADC_SAMPLES)
MAX_BEAT_RANGE_M = C_LIGHT_MPS * ADC_SAMPLE_RATE_HZ / (2.0 * CHIRP_SLOPE_HZ_PER_S)
_DEFAULT_SCENE = Scenario()
GUIDEWAY_TO_GROUND_HEIGHT_M = _DEFAULT_SCENE.height_m
TARGET_ANGLES_DEG = np.asarray(_DEFAULT_SCENE.target_angles_deg)
TARGET_X_M = GUIDEWAY_TO_GROUND_HEIGHT_M * np.tan(np.deg2rad(TARGET_ANGLES_DEG))
TARGET_RANGES_M = np.sqrt(GUIDEWAY_TO_GROUND_HEIGHT_M**2 + TARGET_X_M**2)
TARGET_RANGE_BINS = np.rint(TARGET_RANGES_M / RANGE_RESOLUTION_M).astype(int)
TARGET_AMPLITUDES = np.asarray(_DEFAULT_SCENE.target_amplitudes)
TARGET_SNR_DB = np.asarray(_DEFAULT_SCENE.target_snr_db)
# Amplitudes refer to this range whatever the height of the drawn scene.
TARGET_REFERENCE_RANGE_M = GUIDEWAY_TO_GROUND_HEIGHT_M
# Keep the reflected path inside the complex-ADC beat-frequency limit even
# for the outermost (25 degree) ground point at about 11.03 m.
MULTIPATH_DELAY_M = 0.08
MULTIPATH_AMPLITUDE_RATIO = 0.08
# Keep the synthetic writer's working set independent of the requested capture
# duration.  The resulting .npy files still contain the complete record, but
# only this many frames are materialised while generating each block.
RADAR_GENERATION_BLOCK_FRAMES = 32

# Outdoor scene assumptions for the field site: the guideway is about 10 m
# above sandy soil and trees.  These are weak stationary point scatterers,
# not an attempt to reproduce a full electromagnetic environment.  Their
# ranges stay below the complex-ADC beat-frequency limit for this profile.
STATIC_SCATTERERS = tuple(_DEFAULT_SCENE.static_scatterer_dicts())
# Structural response is generated this much beyond the record so that the
# chirp and DRDY instants of the last frames stay inside the reference grid.
RESPONSE_MARGIN_S = 0.05


@lru_cache(maxsize=16)
def structural_response(scene: Scenario, duration_s: float):
    """Truth displacement and acceleration of ``scene`` on the 3 kHz reference grid."""
    time_s, displacement, acceleration, _ = simulate_response(
        duration_s + RESPONSE_MARGIN_S, **scene.response_kwargs()
    )
    for array in (time_s, displacement, acceleration):
        array.setflags(write=False)
    return time_s, displacement, acceleration


def sway_series(seed: int, frames: int, n_targets: int, std_m: float, corner_hz: float, targets) -> np.ndarray:
    """Independent first-order low-pass LOS motion of ``targets`` (zero at the first frame)."""
    sway = np.zeros((frames, n_targets))
    targets = [t for t in targets if t < n_targets]
    if std_m <= 0.0 or not targets:
        return sway
    rho = np.exp(-2.0 * np.pi * corner_hz / RADAR_RATE_HZ)
    innovation = np.random.default_rng([seed, 7]).standard_normal((frames, len(targets)))
    state = np.zeros(len(targets))
    for k in range(1, frames):
        state = rho * state + np.sqrt(1.0 - rho**2) * innovation[k]
        sway[k, targets] = state
    return sway * std_m


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _array(path: Path, values: np.ndarray, axes: list[str]) -> dict:
    np.save(path, values, allow_pickle=False)
    return {"file": path.name, "dtype": values.dtype.name, "shape": list(values.shape), "axes": axes}


def _open_array(path: Path, shape: tuple[int, ...], dtype: np.dtype, axes: list[str]):
    """Create a .npy-backed array without materialising the whole record."""
    values = np.lib.format.open_memmap(path, mode="w+", dtype=dtype, shape=shape)
    description = {"file": path.name, "dtype": values.dtype.name,
                   "shape": list(values.shape), "axes": axes}
    return values, description


def _scatterer_if(
    range_m: np.ndarray | float,
    angle_deg: float,
    amplitude: np.ndarray | float,
    phase_bias: float,
    positions: np.ndarray,
    adc_time_s: np.ndarray,
    chirp_slope_hz_per_s: float = CHIRP_SLOPE_HZ_PER_S,
) -> np.ndarray:
    """Return one point-scatterer dechirped FMCW IF contribution.

    The model uses the usual narrow-band approximation.  For each chirp the
    propagation phase is ``4*pi*R/lambda`` and the beat tone is
    ``f_b=2*slope*R/c``.  The eight channels are the 2-TX x 4-RX virtual array
    represented by the saved cube.
    """
    ranges = np.asarray(range_m, dtype=float)
    amplitude = np.asarray(amplitude, dtype=complex)
    beat_hz = 2.0 * chirp_slope_hz_per_s * ranges / C_LIGHT_MPS
    fast_time = np.exp(2j * np.pi * beat_hz[..., None] * adc_time_s[None, :])
    propagation = np.exp(1j * (4.0 * np.pi * ranges / WAVELENGTH_M + phase_bias))
    angle_tone = np.exp(2j * np.pi * positions * np.sin(np.deg2rad(angle_deg)))
    return amplitude[..., None, None] * propagation[..., None, None] * angle_tone[None, :, None] * fast_time[..., None, :]


def _radar_package(root: Path, tx_q: np.ndarray, seed: int, impairments: Impairments,
                   scene: Scenario, fast: bool) -> None:
    frames, loops = tx_q.shape[:2]
    rng = np.random.default_rng(seed)
    # TX0/RX0..3 and TX2/RX0..3 are stored as one virtual snapshot for each
    # MIMO loop. Each group of four channels is produced by its own
    # physical TDM chirp; the pair is combined only at export so the algorithm
    # receives eight virtual antennas; the frame export averages four loops.
    rx_positions = np.arange(4, dtype=float) * 0.5
    tx_positions = np.asarray((0.0, 2.0), dtype=float)
    nominal_positions = np.concatenate([tx + rx_positions for tx in tx_positions])
    # The physical forward model is deliberately allowed to differ from the
    # nominal values exported to the algorithm.  This is a compact way to
    # exercise angle, array-spacing and range-profile calibration errors.
    positions = nominal_positions * (1.0 + impairments.radar_array_spacing_error)
    actual_chirp_slope = CHIRP_SLOPE_HZ_PER_S * (1.0 + impairments.radar_chirp_slope_error)
    adc_time_s = RADAR_ADC_START_TIME_S + np.arange(ADC_SAMPLES, dtype=float) / ADC_SAMPLE_RATE_HZ
    # Keep the geometric ranges continuous.  The FFT bin in the manifest is
    # only the expected extraction bin; snapping the physical target to that
    # bin would hide range leakage and bias the propagation phase.
    target_ranges_m = scene.target_ranges_m()
    target_angles_deg = np.asarray(scene.target_angles_deg)
    target_amplitudes = np.asarray(scene.target_amplitudes)
    target_x_m = scene.height_m * np.tan(np.deg2rad(target_angles_deg))
    target_range_bins = np.rint(target_ranges_m / RANGE_RESOLUTION_M).astype(int)
    static_scatterers = scene.static_scatterer_dicts()
    array_angle_error_deg = impairments.radar_mount_angle_error_deg

    directory = root / "radar" / "algorithm_input"
    directory.mkdir(parents=True)
    chirp = chirp_description = None
    if not fast:
        chirp, chirp_description = _open_array(
            directory / "chirp_cube.npy",
            (frames, loops, VIRTUAL_RX, ADC_SAMPLES), np.dtype(np.complex64),
            ["frame", "chirp_loop", "virtual_antenna", "adc_sample"],
        )
    adc, adc_description = _open_array(
        directory / "adc_cube.npy",
        (frames, VIRTUAL_RX, ADC_SAMPLES), np.dtype(np.complex64),
        ["frame", "virtual_antenna", "adc_sample"],
    )

    # The radar is fixed to the guideway, so a world-fixed ground/tree
    # scatterer has the same guideway displacement projected onto its LOS.
    # Generate and flush one bounded block at a time; no full-record complex128
    # array is needed by the method.
    gain = 10.0 ** (rng.normal(0.0, RX_GAIN_MISMATCH_DB_STD, VIRTUAL_RX) / 20.0)
    phase = np.deg2rad(rng.normal(0.0, RX_PHASE_MISMATCH_DEG_STD, VIRTUAL_RX))
    rx_calibration = gain * np.exp(1j * phase)
    innovation_std = PLL_PHASE_NOISE_STD_RAD * np.sqrt(1.0 - PLL_PHASE_NOISE_RHO**2)
    pll_previous = np.zeros((loops, RADAR_TX_CHIRPS_PER_LOOP), dtype=float)
    # These are fixed scattering phases, not blockwise motion.  Drawing them
    # inside the loop introduces artificial phase jumps every 32 frames.
    target_phases = rng.uniform(-np.pi, np.pi, (len(target_angles_deg), 2))
    static_phases = rng.uniform(-np.pi, np.pi, len(static_scatterers))
    snr_db_all = np.asarray(scene.target_snr_db) + impairments.snr_offset_db
    receiver_noise_std = RECEIVER_NOISE_STD * 10.0 ** (-impairments.snr_offset_db / 20.0)
    sway = sway_series(seed, frames, len(target_angles_deg), impairments.target_sway_std_m,
                       impairments.target_sway_corner_hz, impairments.target_sway_targets)
    # A constant term in every target's range-angle cell (DC offset, crosstalk
    # and static clutter lumped together).  It does not follow the guideway
    # motion, so it displaces the centre of that target's IQ circle.
    offset_if = np.zeros((RADAR_TX_CHIRPS_PER_LOOP, 1, 1, 4, ADC_SAMPLES), dtype=complex)
    if impairments.iq_offset_ratio > 0.0:
        offset_phases = np.random.default_rng([seed, 13]).uniform(-np.pi, np.pi, len(target_angles_deg))
        for index, (angle, range_m, amplitude) in enumerate(zip(target_angles_deg, target_ranges_m, target_amplitudes)):
            offset_amplitude = np.full(
                (1, 1), impairments.iq_offset_ratio * amplitude * (TARGET_REFERENCE_RANGE_M / range_m) ** 2
            )
            for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
                offset_if[tx] += _scatterer_if(
                    np.full((1, 1), range_m), angle + array_angle_error_deg, offset_amplitude, offset_phases[index],
                    positions[tx * 4:(tx + 1) * 4], adc_time_s, actual_chirp_slope,
                )
    # Effective-SNR diagnostics use the same Hamming range FFT and fixed DBF
    # grid as the retained algorithm.  They are written to the manifest only;
    # no diagnostic statistic is fed back into target extraction or filtering.
    range_power_blocks = []
    dbf_signal_blocks = [[] for _ in target_angles_deg]
    dbf_noise_blocks = []
    iq_sum = np.zeros(len(target_angles_deg), dtype=complex)
    iq_abs2_sum = np.zeros(len(target_angles_deg), dtype=float)
    iq_count = np.zeros(len(target_angles_deg), dtype=np.int64)
    range_window = np.hamming(ADC_SAMPLES)
    angle_window = np.hanning(VIRTUAL_RX)
    spatial = np.fft.fftshift(np.fft.fftfreq(64, d=1.0))
    diagnostic_steering = np.exp(
        -2j * np.pi * nominal_positions[:, None]
        * (spatial / 0.5)[None, :]
    )
    diagnostic_angle_axis = np.rad2deg(np.arcsin(np.clip(spatial / 0.5, -1.0, 1.0)))
    target_angle_bins = np.asarray([
        int(np.argmin(np.abs(diagnostic_angle_axis - (angle + array_angle_error_deg))))
        for angle in target_angles_deg
    ])
    saturated_i_count = 0
    saturated_q_count = 0
    for start in range(0, frames, RADAR_GENERATION_BLOCK_FRAMES):
        end = min(frames, start + RADAR_GENERATION_BLOCK_FRAMES)
        block_q = tx_q[start:end]
        block_frames = end - start
        block = np.zeros((block_frames, loops, VIRTUAL_RX, ADC_SAMPLES), dtype=np.complex128)

        for target_index, (angle, range_m, amplitude, snr_db) in enumerate(zip(target_angles_deg, target_ranges_m, target_amplitudes, snr_db_all)):
            radial_q = block_q * np.cos(np.deg2rad(angle))
            ranges = range_m + radial_q + sway[start:end, target_index][:, None, None]
            range_attenuation = (TARGET_REFERENCE_RANGE_M / ranges) ** 2
            target_amplitude = amplitude * range_attenuation
            target_noise_std = target_amplitude / np.sqrt(2.0 * 10.0 ** (snr_db / 10.0))
            target_noise = target_noise_std * (
                rng.standard_normal(target_amplitude.shape) + 1j * rng.standard_normal(target_amplitude.shape)
            )
            propagation_bias, multipath_bias = target_phases[target_index]
            for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
                channel_slice = slice(tx * 4, (tx + 1) * 4)
                block[:, :, channel_slice, :] += _scatterer_if(
                    ranges[:, :, tx], angle + array_angle_error_deg,
                    target_amplitude[:, :, tx] + target_noise[:, :, tx],
                    propagation_bias, positions[channel_slice], adc_time_s, actual_chirp_slope,
                )
                multipath_ranges = ranges[:, :, tx] + MULTIPATH_DELAY_M
                block[:, :, channel_slice, :] += _scatterer_if(
                    multipath_ranges, angle + 2.0 + array_angle_error_deg,
                    MULTIPATH_AMPLITUDE_RATIO * target_amplitude[:, :, tx]
                    * (ranges[:, :, tx] / multipath_ranges) ** 2,
                    multipath_bias, positions[channel_slice], adc_time_s, actual_chirp_slope,
                )

        for scatterer_index, scatterer in enumerate(static_scatterers):
            static_ranges = scatterer["range_m"] + block_q * np.cos(np.deg2rad(scatterer["angle_deg"]))
            static_amplitude = np.full(
                (block_frames, loops),
                scatterer["amplitude"] * (TARGET_REFERENCE_RANGE_M / scatterer["range_m"]) ** 2,
                dtype=float,
            )
            propagation_bias = static_phases[scatterer_index]
            for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
                channel_slice = slice(tx * 4, (tx + 1) * 4)
                block[:, :, channel_slice, :] += _scatterer_if(
                    static_ranges[:, :, tx], scatterer["angle_deg"] + array_angle_error_deg, static_amplitude,
                    propagation_bias, positions[channel_slice], adc_time_s, actual_chirp_slope,
                )

        if impairments.iq_offset_ratio > 0.0:
            for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
                block[:, :, tx * 4:(tx + 1) * 4, :] += offset_if[tx]

        block *= rx_calibration[None, None, :, None]
        pll_block = np.empty((block_frames, loops, RADAR_TX_CHIRPS_PER_LOOP), dtype=float)
        for frame in range(block_frames):
            for loop in range(loops):
                pll_previous[loop, :] = PLL_PHASE_NOISE_RHO * pll_previous[loop, :] + innovation_std * rng.standard_normal(RADAR_TX_CHIRPS_PER_LOOP)
                pll_block[frame, loop, :] = pll_previous[loop, :]
        for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
            block[:, :, tx * 4:(tx + 1) * 4, :] *= np.exp(1j * pll_block[:, :, tx, None, None])

        # Add I and Q noise separately so the temporary working set is bounded.
        block += receiver_noise_std * rng.standard_normal(block.shape)
        block += 1j * receiver_noise_std * rng.standard_normal(block.shape)
        real = np.clip(np.real(block), -ADC_FULL_SCALE, ADC_FULL_SCALE - ADC_LSB)
        imag = np.clip(np.imag(block), -ADC_FULL_SCALE, ADC_FULL_SCALE - ADC_LSB)
        quantized = (np.rint(real / ADC_LSB) + 1j * np.rint(imag / ADC_LSB)) * ADC_LSB
        block = quantized.astype(np.complex64)
        saturated_i_count += int(np.count_nonzero((block.real <= -ADC_FULL_SCALE) | (block.real >= ADC_FULL_SCALE - ADC_LSB)))
        saturated_q_count += int(np.count_nonzero((block.imag <= -ADC_FULL_SCALE) | (block.imag >= ADC_FULL_SCALE - ADC_LSB)))
        if chirp is not None:
            chirp[start:end] = block
        frame_adc = np.mean(block, axis=1).astype(np.complex64, copy=False)
        if impairments.radar_dropout_s > 0.0:
            drop_start = int(round(impairments.radar_dropout_start_s * RADAR_RATE_HZ))
            drop_end = drop_start + int(round(impairments.radar_dropout_s * RADAR_RATE_HZ))
            s0 = max(start, drop_start) - start
            s1 = min(end, drop_end) - start
            if s1 > s0:
                frame_adc = frame_adc.copy()
                frame_adc[s0:s1] = np.complex64(np.nan + 1j * np.nan)
        adc[start:end] = frame_adc

        # Keep these calculations bounded by the generation block.  The
        # nominal positions intentionally differ from the physical positions
        # above, matching what the algorithm receives in its manifest.
        range_spectrum = np.fft.fft(
            block.astype(np.complex128) * range_window[None, None, None, :], axis=-1
        )
        range_power_blocks.append(np.nanmedian(np.abs(range_spectrum) ** 2, axis=(0, 1, 2)))
        snapshots = np.transpose(range_spectrum, (0, 1, 3, 2))
        dbf_cube = np.einsum(
            "flrv,va->flra", snapshots * angle_window[None, None, None, :],
            diagnostic_steering, optimize=True,
        )
        dbf_power = np.abs(dbf_cube) ** 2
        dbf_power_map = np.nanmedian(dbf_power, axis=(0, 1))
        excluded = np.zeros(dbf_power_map.shape, dtype=bool)
        for target_bin, angle_bin in zip(target_range_bins, target_angle_bins):
            excluded[max(0, target_bin - 2):min(ADC_SAMPLES, target_bin + 3),
                     max(0, angle_bin - 2):min(64, angle_bin + 3)] = True
        dbf_noise_blocks.append(float(np.nanmedian(dbf_power_map[~excluded])))
        for target_index, (target_bin, angle_bin) in enumerate(zip(target_range_bins, target_angle_bins)):
            dbf_signal_blocks[target_index].append(
                float(np.nanmedian(dbf_power[:, :, int(target_bin), int(angle_bin)]))
            )
            quiet_end = max(0, min(block_frames, int(round(0.2 * RADAR_RATE_HZ)) - start))
            if quiet_end:
                quiet_iq = dbf_cube[:quiet_end, :, int(target_bin), int(angle_bin)].reshape(-1)
                finite = np.isfinite(quiet_iq)
                quiet_iq = quiet_iq[finite]
                iq_sum[target_index] += np.sum(quiet_iq)
                iq_abs2_sum[target_index] += float(np.sum(np.abs(quiet_iq) ** 2))
                iq_count[target_index] += quiet_iq.size

    adc.flush()
    arrays = {
        "adc_cube": adc_description,
        "frame_times_s": _array(directory / "frame_times_s.npy", np.arange(frames) / RADAR_RATE_HZ, ["frame"]),
    }
    # The fast record omits the lossless chirp cube, but the bounded effective
    # SNR diagnostics are retained for both modes.
    chirp_payload_bytes = 0
    range_power = np.nanmedian(np.stack(range_power_blocks, axis=0), axis=0)
    excluded_range = np.zeros(ADC_SAMPLES, dtype=bool)
    for target_bin in target_range_bins:
        excluded_range[max(0, target_bin - 2):min(ADC_SAMPLES, target_bin + 3)] = True
    range_noise_floor = float(np.nanmedian(range_power[~excluded_range]))
    range_fft_snr_db = [
        float(10.0 * np.log10(max(range_power[int(target_bin)], 1.0e-30)
                               / max(range_noise_floor, 1.0e-30)))
        for target_bin in target_range_bins
    ]
    dbf_noise_floor = float(np.nanmedian(np.asarray(dbf_noise_blocks)))
    dbf_snr_db = [
        float(10.0 * np.log10(max(float(np.nanmedian(values)), 1.0e-30)
                               / max(dbf_noise_floor, 1.0e-30)))
        for values in dbf_signal_blocks
    ]
    iq_snr_db = []
    for index in range(len(target_angles_deg)):
        count = max(int(iq_count[index]), 1)
        mean_iq = iq_sum[index] / count
        noise_power = max(iq_abs2_sum[index] / count - abs(mean_iq) ** 2, 1.0e-30)
        iq_snr_db.append(float(10.0 * np.log10(max(abs(mean_iq) ** 2, 1.0e-30) / noise_power)))
    if chirp is not None:
        chirp.flush()
        chirp_payload_bytes = int(np.prod((frames, loops, VIRTUAL_RX, ADC_SAMPLES)) * 4)
        arrays["chirp_cube"] = chirp_description
    del chirp, adc
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.algorithm-input", "schema_version": 1,
        "source": {"kind": "paper_bridge_simulation", "radar_adc_iq": "synthetic_if_chirp", "seed": seed,
                   "fast_without_chirp_cube": fast,
                   "target_range_bins": target_range_bins.tolist(),
                   "target_ranges_m": target_ranges_m.tolist(),
                   "target_angles_deg": target_angles_deg.tolist(),
                   "target_geometry": {
                       "guideway_height_m": scene.height_m,
                       "target_state": "fixed_world_ground_or_tree_reference; radar follows guideway",
                       "target_x_m": target_x_m.tolist(),
                       "baseline_range_m": target_ranges_m.tolist(),
                       "radial_displacement_projection": "q(t) * cos(angle)",
                       "reference_target_range_m": TARGET_REFERENCE_RANGE_M,
                   },
                   "target_snr_db": snr_db_all.tolist(),
                   "snr_semantics": "per-target, per-TX, per-loop complex scattering coefficient before array projection and loop averaging",
                   "range_fft_snr_db": range_fft_snr_db,
                   "effective_snr_db": {
                       "range_fft": range_fft_snr_db,
                       "dbf": dbf_snr_db,
                       "iq": iq_snr_db,
                       "target_angle_bins": target_angle_bins.tolist(),
                       "quiet_window_s": [0.0, 0.2],
                       "semantics": {
                           "range_fft": "Hamming-windowed range FFT; target bin power divided by median non-target range-bin power before DBF",
                           "dbf": "nominal-position fixed-grid DBF; target range-angle cell power divided by median non-target range-angle cell power",
                           "iq": "quiet-window complex IQ mean power divided by residual complex variance at the nominal target range-angle cell",
                       },
                   },
                   "impairments": asdict(impairments),
                   "scenario": asdict(scene),
                   "range_fft_snr_statistic": "Hamming-windowed median of bounded-block medians",
                   "scene": {"guideway_height_m": scene.height_m, "surface": "sandy soil with tree line",
                             "static_scatterers": static_scatterers,
                             "multipath_excess_path_m": MULTIPATH_DELAY_M,
                             "multipath_amplitude_ratio": MULTIPATH_AMPLITUDE_RATIO}},
        "packet_integrity": {"complete": True, "mode": "synthetic_payload_integrity", "payload_bytes": chirp_payload_bytes},
        "radar": {
            "frames": frames, "frame_period_s": 1.0 / RADAR_RATE_HZ, "frame_rate_hz": RADAR_RATE_HZ,
            "minimum_frame_period_s": RADAR_MINIMUM_FRAME_PERIOD_S,
            "external_trigger_period_s": RADAR_EXTERNAL_TRIGGER_PERIOD_S,
            "chirp_loops_per_frame": RADAR_LOOPS_PER_FRAME,
            "tx_chirps_per_loop": RADAR_TX_CHIRPS_PER_LOOP,
            "physical_chirps_per_frame": RADAR_LOOPS_PER_FRAME * RADAR_TX_CHIRPS_PER_LOOP,
            "idle_time_s": RADAR_IDLE_TIME_S,
            "adc_start_time_s": RADAR_ADC_START_TIME_S,
            "ramp_end_time_s": RADAR_RAMP_END_TIME_S,
            "chirp_cycle_time_s": RADAR_CHIRP_CYCLE_S,
            "loop_start_interval_s": RADAR_LOOP_START_INTERVAL_S,
            "loop_reference_offset_s": RADAR_LOOP_REFERENCE_OFFSET_S,
            "coherent_aperture_center_offset_s": RADAR_APERTURE_CENTER_OFFSET_S,
            "tx_indices": [0, 2], "rx_indices": [0, 1, 2, 3], "virtual_antennas": VIRTUAL_RX,
            "virtual_array_positions_wavelengths": nominal_positions.tolist(),
            "chirp_cube_semantics": "paired TDM virtual snapshot: channels 0..3 are TX0/RX0..3 and 4..7 are TX2/RX0..3",
            "adc_samples_per_chirp": ADC_SAMPLES, "adc_sample_rate_hz": ADC_SAMPLE_RATE_HZ,
            "adc_capture_time_s": ADC_CAPTURE_TIME_S,
            "start_frequency_hz": RADAR_START_FREQUENCY_HZ,
            "chirp_slope_hz_per_s": CHIRP_SLOPE_HZ_PER_S,
            "bandwidth_hz": RADAR_BANDWIDTH_HZ,
            "adc_capture_bandwidth_hz": ADC_CAPTURE_BANDWIDTH_HZ,
            "maximum_beat_range_m": MAX_BEAT_RANGE_M,
            "range_resolution_m": RANGE_RESOLUTION_M, "angle_bins": 64,
            "adc_bits": ADC_BITS, "adc_full_scale": ADC_FULL_SCALE,
            "adc_lsb": ADC_LSB, "receiver_noise_std": receiver_noise_std,
            "wavelength_m": WAVELENGTH_M,
            "tx_chirp_offsets_s": [0.0, RADAR_CHIRP_CYCLE_S],
            "adc_quantization": {
                "bits": ADC_BITS, "full_scale_v": ADC_FULL_SCALE,
                "lsb_v": ADC_LSB, "stored_dtype": "complex64",
                "quantized_array": "chirp_cube" if chirp_description is not None else "not_saved",
                "saturated_i_count": saturated_i_count,
                "saturated_q_count": saturated_q_count,
            },
            "receiver_impairments": {
                "rx_gain_mismatch_db_std": RX_GAIN_MISMATCH_DB_STD,
                "rx_phase_mismatch_deg_std": RX_PHASE_MISMATCH_DEG_STD,
                "pll_phase_noise_std_rad": PLL_PHASE_NOISE_STD_RAD,
                "pll_phase_noise_rho": PLL_PHASE_NOISE_RHO,
            },
            "signal_model": "dechirped FMCW point scatterers with propagation, range beat, TDM array phase, attenuation, clutter, multipath, noise and ADC quantisation",
        },
        "arrays": arrays,
    })


class AdxlStream(NamedTuple):
    drdy_ns: np.ndarray
    estimated_ns: np.ndarray
    values: np.ndarray
    bias_mps2: np.ndarray
    # Structural acceleration at the physical content instants (no filter
    # delay).  ``truth_content_ns`` is the time axis for this array; it is
    # intentionally distinct from DRDY and published/estimated timestamps.
    truth_mps2: np.ndarray
    truth_content_ns: np.ndarray


def adxl_samples(scene: Scenario, impairments: Impairments, seed: int, duration_s: float) -> AdxlStream:
    """ADXL355 DRDY stream of one record: sampled content, errors and published times."""
    reference_time_s, displacement, acceleration = structural_response(scene, duration_s)
    count = round(duration_s * ADXL_RATE_HZ) + ADXL_TAIL_SAMPLES
    index = np.arange(count, dtype=np.int64)
    drdy_ns = (
        BASE_TIME_NS + round(impairments.adxl_clock_phase_s * 1.0e9)
        + np.rint(index * ADXL_PERIOD_NS * (1.0 + impairments.adxl_odr_error)).astype(np.int64)
    )
    drdy_s = (drdy_ns - BASE_TIME_NS) * 1.0e-9
    # The ADXL355 digital filter delays the output by ADXL_GROUP_DELAY_S: the
    # sample published at DRDY time t carries the structure at t - delay.
    content_s = drdy_s - ADXL_GROUP_DELAY_S
    sensed = np.interp(content_s, reference_time_s, acceleration)
    local_deflection = np.interp(content_s, reference_time_s, displacement)
    rng = np.random.default_rng(seed + 1)
    values = np.zeros((count, 3), dtype=np.float64)
    # ADXL355 at the configured 500 Hz ODR: use the ±2 g noise density from
    # the data sheet, a small fixed bias, and a sub-percent scale error.  The
    # other two axes contain only cross-axis leakage and sensor noise.
    noise_std = (
        ADXL_NOISE_DENSITY_G_PER_SQRT_HZ * 9.80665
        * np.sqrt(ADXL_RATE_HZ / 2.0)
        * impairments.adxl_noise_scale
    )
    bias = ADXL_BIAS_MPS2.copy()
    if impairments.adxl_bias_x_mps2 is not None:
        bias[0] = impairments.adxl_bias_x_mps2
    values[:, 0] = ((1.0 + impairments.adxl_scale_error) * sensed
                    + impairments.adxl_tilt_gain_mps2_per_m * local_deflection
                    + bias[0] + noise_std * rng.standard_normal(count))
    values[:, 1] = 0.001 * sensed + bias[1] + noise_std * rng.standard_normal(count)
    values[:, 2] = -0.0007 * sensed + bias[2] + noise_std * rng.standard_normal(count)
    if impairments.adxl_bias_walk_mps2_per_sqrt_s > 0.0:
        walk_rng = np.random.default_rng([seed, 3])
        step = impairments.adxl_bias_walk_mps2_per_sqrt_s * np.sqrt(1.0 / ADXL_RATE_HZ)
        values[:, 0] += np.cumsum(step * walk_rng.standard_normal(count))
    # Same export rule as system/capture_program/adxl355_input.py with a
    # configured group delay: estimated sample time = DRDY edge - group delay.
    # The impairment offset is the residual error of that calibration.
    estimated_ns = drdy_ns - ADXL_GROUP_DELAY_NS + round(impairments.adxl_timestamp_offset_s * 1.0e9)
    if impairments.adxl_timestamp_jitter_std_s > 0.0:
        jitter_rng = np.random.default_rng([seed, 5])
        estimated_ns = estimated_ns + np.rint(
            jitter_rng.standard_normal(count) * impairments.adxl_timestamp_jitter_std_s * 1.0e9
        ).astype(np.int64)
    # Timestamp jitter can make neighbouring published timestamps equal or
    # reverse.  The capture contract requires strict ordering for interval
    # preintegration, so repair only the timestamp sequence, never the sample
    # values or their physical truth times.
    for index in range(1, estimated_ns.size):
        if estimated_ns[index] <= estimated_ns[index - 1]:
            estimated_ns[index] = estimated_ns[index - 1] + 1
    truth_content_s = content_s
    truth_content_ns = BASE_TIME_NS + np.rint(truth_content_s * 1.0e9).astype(np.int64)
    truth_mps2 = np.interp(truth_content_s, reference_time_s, acceleration)
    return AdxlStream(drdy_ns, estimated_ns, values, bias, truth_mps2, truth_content_ns)


def _adxl_package(root: Path, stream: AdxlStream, impairments: Impairments) -> None:
    values = stream.values
    sample_count = values.shape[0]
    # Export the same quantized value that a ±2 g, 20-bit ADXL355 would
    # deliver after the raw-code-to-acceleration conversion.  The algorithm
    # reads ``acceleration_mps2`` rather than the diagnostic raw-code array,
    # so keeping the pre-quantized floating-point values here would remove
    # quantization from the evaluated estimator entirely.
    sensitivity_lsb_per_g = 256_000.0
    signed_code_min = -(2**19)
    signed_code_max = 2**19 - 1
    raw = np.clip(
        np.rint(values / 9.80665 * sensitivity_lsb_per_g),
        signed_code_min,
        signed_code_max,
    ).astype(np.int32)
    quantized_values = raw.astype(np.float64) / sensitivity_lsb_per_g * 9.80665
    directory = root / "adxl355" / "algorithm_input"
    directory.mkdir(parents=True)
    sample_times_s = (stream.drdy_ns - stream.drdy_ns[0]) * 1.0e-9
    arrays = {
        "acceleration_raw": _array(directory / "acceleration_raw.npy", raw, ["sample", "axis"]),
        "acceleration_mps2": _array(directory / "acceleration_mps2.npy", quantized_values, ["sample", "axis"]),
        "drdy_monotonic_ns": _array(directory / "drdy_monotonic_ns.npy", stream.drdy_ns, ["sample"]),
        "estimated_sample_monotonic_ns": _array(directory / "estimated_sample_monotonic_ns.npy", stream.estimated_ns, ["sample"]),
        "sample_times_s": _array(directory / "sample_times_s.npy", sample_times_s, ["sample"]),
    }
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.adxl355-input", "schema_version": 1,
        "source": {"kind": "paper_bridge_simulation", "structural_axis": "paper-parameterized",
                   "noise_density_g_per_sqrt_hz": ADXL_NOISE_DENSITY_G_PER_SQRT_HZ,
                   "bias_mps2": stream.bias_mps2.tolist(), "scale_x": 1.0 + impairments.adxl_scale_error,
                   "impairments": asdict(impairments),
                   "cross_axis_coefficients": [0.001, -0.0007],
                   "digital_group_delay_s": ADXL_GROUP_DELAY_S},
        "capture": {"complete": True, "samples": sample_count, "odr_hz_nominal": ADXL_RATE_HZ, "range_g": 2,
                    "group_delay_ns": ADXL_GROUP_DELAY_NS,
                    "group_delay_calibrated": True,
                    "native_summary": {"samples": sample_count, "mock": True, "simulation": True}},
        "timing": {"clock": "CLOCK_MONOTONIC", "drdy_monotonic_ns_semantics": "synthetic DRDY schedule with the configured clock phase and ODR error",
                   "estimated_sample_monotonic_ns_semantics": "drdy_monotonic_ns - group_delay_ns + residual timing impairment, strictly increasing after timestamp repair",
                   "truth_content_time_semantics": "truth/adxl_time_ns is the physical sensor content time, drdy_monotonic_ns - group_delay_ns before residual timing impairment"},
        "arrays": arrays,
    })


def generate(output: str | Path, *, duration_s: float = DURATION_S, seed: int = 2026,
             impairments: Impairments = Impairments(), scenario: Scenario = Scenario(),
             fast: bool = False) -> Path:
    """Write one capture package.

    ``fast`` omits the lossless chirp cube while retaining effective SNR
    statistics. The ADC cube, ADXL stream, timelines and truth are unchanged.
    It is meant for experiment sweeps that do not need the raw chirp cube.
    """
    output = Path(output)
    if duration_s <= 0.0 or duration_s > DURATION_S:
        raise ValueError(f"duration must be in (0, {DURATION_S:g}] seconds")
    reference_time_s, displacement, _ = structural_response(scenario, duration_s)
    count = round(duration_s * RADAR_RATE_HZ)
    if count < 2:
        raise ValueError("duration does not contain enough radar frames")
    frame_time_s = np.arange(count, dtype=float) / RADAR_RATE_HZ + RADAR_APERTURE_CENTER_OFFSET_S
    loop_offsets_s = (np.arange(RADAR_LOOPS_PER_FRAME, dtype=float) - (RADAR_LOOPS_PER_FRAME - 1) / 2.0) * RADAR_LOOP_START_INTERVAL_S
    tx_offsets_s = (np.arange(RADAR_TX_CHIRPS_PER_LOOP) - (RADAR_TX_CHIRPS_PER_LOOP - 1) / 2.0) * (RADAR_IDLE_TIME_S + RADAR_RAMP_END_TIME_S)
    tx_time_s = frame_time_s[:, None, None] + loop_offsets_s[None, :, None] + tx_offsets_s[None, None, :]
    tx_q = np.interp(tx_time_s, reference_time_s, displacement)
    stream = adxl_samples(scenario, impairments, seed, duration_s)
    with tempfile.TemporaryDirectory(prefix="bridge-package-") as temporary:
        staging = Path(temporary) / "package"
        staging.mkdir()
        _radar_package(staging, tx_q, seed, impairments, scenario, fast)
        _adxl_package(staging, stream, impairments)
        sync = staging / "sync"
        sync.mkdir()
        radar_time = BASE_TIME_NS + np.arange(count, dtype=np.int64) * RADAR_FRAME_PERIOD_NS
        np.save(sync / "radar_frame_monotonic_ns.npy", radar_time, allow_pickle=False)
        radar_adc_time = radar_time + round(RADAR_APERTURE_CENTER_OFFSET_S * 1.0e9)
        np.save(sync / "radar_adc_sample_monotonic_ns.npy", radar_adc_time, allow_pickle=False)
        _json(staging / "paper_response_metadata.json", {**reference_metadata(), "scenario": asdict(scenario)})
        _json(sync / "timeline.json", {"schema_version": 1, "status": "complete",
                                        "sync_mode": "software_timestamp", "timestamp_quality": "sensor_start_bracket_estimate",
                                        "hardware_validated": False, "clock": "CLOCK_MONOTONIC", "unit": "nanoseconds",
                                        "frame_count": count, "nominal_frame_period_ns": RADAR_FRAME_PERIOD_NS,
                                        "radar_algorithm_manifest": "../radar/algorithm_input/manifest.json",
                                        "radar_packet_integrity_complete": True,
                                        "array": {"file": "radar_frame_monotonic_ns.npy", "dtype": "int64", "shape": [count], "axes": ["radar_frame"]},
                                        "adc_array": {"file": "radar_adc_sample_monotonic_ns.npy", "dtype": "int64", "shape": [count]},
                                        "provenance": {"source": "paper_bridge_simulation", "semantics": "synthetic monotonic schedule", "is_measured_radar_frame_start": False}})
        _json(sync / "manifest.json", {"schema_version": 1, "status": "complete",
                                        "sync_mode": "software_timestamp", "timestamp_quality": "sensor_start_bracket_estimate",
                                        "hardware_validated": False,
                                        "clock": {"alignment_clock": "CLOCK_MONOTONIC", "unit": "nanoseconds", "wall_clock": "CLOCK_REALTIME", "wall_time_used_for_alignment": False},
                                        "files": {"radar": {"algorithm_input_manifest": "radar/algorithm_input/manifest.json"},
                                                  "adxl355": {"algorithm_input_manifest": "adxl355/algorithm_input/manifest.json"},
                                                  "sync": {"timeline_manifest": "sync/timeline.json", "radar_frame_monotonic_ns": "sync/radar_frame_monotonic_ns.npy"}},
                                        "validation": {"status": "complete", "radar_finalized": True, "adxl355_finalized": True, "sync_timeline_exported": True, "hardware_validated": False},
                                        "uncertainty": {"status": "not_characterized"},
                                        "timestamp_semantics": {"pcap_is_frame_start": False, "radar": "synthetic monotonic schedule", "adxl355": "synthetic nominal sample schedule"}})
        truth = staging / "truth"
        truth.mkdir()
        truth_count = round(duration_s * REFERENCE_RATE_HZ)
        np.save(truth / "displacement_m.npy", displacement[:truth_count], allow_pickle=False)
        np.save(truth / "time_ns.npy", BASE_TIME_NS + np.rint(reference_time_s[:truth_count] * 1.0e9).astype(np.int64), allow_pickle=False)
        np.save(truth / "acceleration_mps2.npy", stream.truth_mps2, allow_pickle=False)
        np.save(truth / "adxl_time_ns.npy", stream.truth_content_ns, allow_pickle=False)
        np.save(truth / "adxl_published_time_ns.npy", stream.estimated_ns, allow_pickle=False)
        _json(staging / "status.json", {"schema_version": 1, "status": "complete", "source_type": "paper_bridge_simulation", "reference": reference_metadata()["paper"]})
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    return output
