from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from .response import (
    DURATION_S,
    REFERENCE_RATE_HZ,
    reference_metadata,
    simulate_response,
)

# This is a direct IWR1843 profile/frame model.  The radar frame rate is the
# physical acquisition rate; the 3 kHz A20 reference response is only used to
# evaluate the displacement at the individual TX chirp times.
RADAR_RATE_HZ = 100.0
RADAR_EXTERNAL_TRIGGER_PERIOD_S = 1.0 / RADAR_RATE_HZ
RADAR_MINIMUM_FRAME_PERIOD_S = 9.0e-3
ADXL_RATE_HZ = 1000.0
C_LIGHT_MPS = 299_792_458.0
RADAR_IDLE_TIME_S = 70.0e-6
RADAR_ADC_START_TIME_S = 7.0e-6
# ``rampEndTime`` in the profileCfg line.  ADC sampling ends before this
# value (7 us start plus 256/5.209 MS/s is about 56.1 us).
RADAR_RAMP_END_TIME_S = 57.14e-6
RADAR_TX_CHIRPS_PER_LOOP = 2
RADAR_LOOPS_PER_FRAME = 16
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
ADXL_GROUP_DELAY_S = 1.78e-3
RADAR_LOOP_REFERENCE_OFFSET_S = (
    RADAR_IDLE_TIME_S + RADAR_ADC_START_TIME_S
    + (ADC_SAMPLES - 1) / (2.0 * ADC_SAMPLE_RATE_HZ)
    + (RADAR_TX_CHIRPS_PER_LOOP - 1) * (RADAR_IDLE_TIME_S + RADAR_RAMP_END_TIME_S) / 2.0
)
RADAR_APERTURE_CENTER_OFFSET_S = RADAR_LOOP_REFERENCE_OFFSET_S + (RADAR_LOOPS_PER_FRAME - 1) * RADAR_LOOP_START_INTERVAL_S / 2.0
RANGE_RESOLUTION_M = C_LIGHT_MPS * ADC_SAMPLE_RATE_HZ / (2.0 * CHIRP_SLOPE_HZ_PER_S * ADC_SAMPLES)
MAX_BEAT_RANGE_M = C_LIGHT_MPS * ADC_SAMPLE_RATE_HZ / (2.0 * CHIRP_SLOPE_HZ_PER_S)
GUIDEWAY_TO_GROUND_HEIGHT_M = 10.0
TARGET_ANGLES_DEG = np.asarray((3.0, 9.0, 15.0, 21.0, 25.0))
TARGET_X_M = GUIDEWAY_TO_GROUND_HEIGHT_M * np.tan(np.deg2rad(TARGET_ANGLES_DEG))
TARGET_RANGES_M = np.sqrt(GUIDEWAY_TO_GROUND_HEIGHT_M**2 + TARGET_X_M**2)
TARGET_RANGE_BINS = np.rint(TARGET_RANGES_M / RANGE_RESOLUTION_M).astype(int)
TARGET_AMPLITUDES = np.asarray((0.25, 0.2375, 0.225, 0.2125, 0.2))
TARGET_SNR_DB = np.asarray((30.0, 27.5, 25.0, 22.5, 20.0))
TARGET_REFERENCE_RANGE_M = GUIDEWAY_TO_GROUND_HEIGHT_M
# Keep the reflected path inside the complex-ADC beat-frequency limit even
# for the outermost (25 degree) ground point at about 11.03 m.
MULTIPATH_DELAY_M = 0.08
MULTIPATH_AMPLITUDE_RATIO = 0.08

# Outdoor scene assumptions for the field site: the guideway is about 10 m
# above sandy soil and trees.  These are weak stationary point scatterers,
# not an attempt to reproduce a full electromagnetic environment.  Their
# ranges stay below the complex-ADC beat-frequency limit for this profile.
STATIC_SCATTERERS = (
    {"name": "sandy_ground", "range_m": 10.82, "angle_deg": -18.0, "amplitude": 0.025},
    {"name": "tree_line", "range_m": 11.08, "angle_deg": 28.0, "amplitude": 0.01875},
)


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _array(path: Path, values: np.ndarray, axes: list[str]) -> dict:
    np.save(path, values, allow_pickle=False)
    return {"file": path.name, "dtype": values.dtype.name, "shape": list(values.shape), "axes": axes}


def _scatterer_if(
    range_m: np.ndarray | float,
    angle_deg: float,
    amplitude: np.ndarray | float,
    phase_bias: float,
    positions: np.ndarray,
    adc_time_s: np.ndarray,
) -> np.ndarray:
    """Return one point-scatterer dechirped FMCW IF contribution.

    The model uses the usual narrow-band approximation.  For each chirp the
    propagation phase is ``4*pi*R/lambda`` and the beat tone is
    ``f_b=2*slope*R/c``.  The eight channels are the 2-TX x 4-RX virtual array
    represented by the saved cube.
    """
    ranges = np.asarray(range_m, dtype=float)
    amplitude = np.asarray(amplitude, dtype=complex)
    beat_hz = 2.0 * CHIRP_SLOPE_HZ_PER_S * ranges / C_LIGHT_MPS
    fast_time = np.exp(2j * np.pi * beat_hz[..., None] * adc_time_s[None, :])
    propagation = np.exp(1j * (4.0 * np.pi * ranges / WAVELENGTH_M + phase_bias))
    angle_tone = np.exp(2j * np.pi * positions * np.sin(np.deg2rad(angle_deg)))
    return amplitude[..., None, None] * propagation[..., None, None] * angle_tone[None, :, None] * fast_time[..., None, :]


def _radar_package(root: Path, tx_q: np.ndarray, seed: int) -> None:
    frames, loops = tx_q.shape[:2]
    rng = np.random.default_rng(seed)
    chirp = np.zeros((frames, loops, VIRTUAL_RX, ADC_SAMPLES), dtype=np.complex128)
    # TX0/RX0..3 and TX2/RX0..3 are stored as one virtual snapshot for each
    # loop.  Each group of four channels is produced by its own physical TDM
    # chirp; the pair is combined only at export so the existing algorithm
    # contract can consume eight virtual antennas per loop.
    rx_positions = np.arange(4, dtype=float) * 0.5
    tx_positions = np.asarray((0.0, 2.0), dtype=float)
    positions = np.concatenate([tx + rx_positions for tx in tx_positions])
    adc_time_s = RADAR_ADC_START_TIME_S + np.arange(ADC_SAMPLES, dtype=float) / ADC_SAMPLE_RATE_HZ
    # Keep the geometric ranges continuous.  The FFT bin in the manifest is
    # only the expected extraction bin; snapping the physical target to that
    # bin would hide range leakage and bias the propagation phase.
    target_ranges_m = TARGET_RANGES_M.copy()

    # Fixed-world environmental reference points.  The radar is attached to
    # the guideway, so tx_q is evaluated at each physical TDM chirp time and
    # its radial projection changes the range in the radar coordinate frame.
    for angle, range_m, amplitude, snr_db in zip(TARGET_ANGLES_DEG, target_ranges_m, TARGET_AMPLITUDES, TARGET_SNR_DB):
        radial_q = tx_q * np.cos(np.deg2rad(angle))
        ranges = range_m + radial_q
        range_attenuation = (TARGET_REFERENCE_RANGE_M / ranges) ** 2
        target_amplitude = amplitude * range_attenuation
        target_noise_std = target_amplitude / np.sqrt(2.0 * 10.0 ** (snr_db / 10.0))
        target_noise = target_noise_std * (
            rng.standard_normal(target_amplitude.shape) + 1j * rng.standard_normal(target_amplitude.shape)
        )
        propagation_bias = rng.uniform(-np.pi, np.pi)
        multipath_bias = rng.uniform(-np.pi, np.pi)
        for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
            channel_slice = slice(tx * 4, (tx + 1) * 4)
            contribution = _scatterer_if(
                ranges[:, :, tx], angle,
                target_amplitude[:, :, tx] + target_noise[:, :, tx],
                propagation_bias, positions[channel_slice], adc_time_s,
            )
            chirp[:, :, channel_slice, :] += contribution

            # One weak reflected path for every moving target.  The excess
            # path is intentionally resolvable but remains below the target
            # selection floor.
            multipath_ranges = ranges[:, :, tx] + MULTIPATH_DELAY_M
            chirp[:, :, channel_slice, :] += _scatterer_if(
                multipath_ranges, angle + 2.0,
                MULTIPATH_AMPLITUDE_RATIO * target_amplitude[:, :, tx]
                * (ranges[:, :, tx] / multipath_ranges) ** 2,
                multipath_bias, positions[channel_slice], adc_time_s,
            )

    # The radar is fixed to the guideway, so a world-fixed ground/tree
    # scatterer has the same guideway displacement projected onto its LOS.
    # It is stationary in the scene, but its range is not constant in the
    # radar coordinate frame.
    for scatterer in STATIC_SCATTERERS:
        static_ranges = scatterer["range_m"] + tx_q * np.cos(np.deg2rad(scatterer["angle_deg"]))
        static_amplitude = np.full(
            (frames, loops),
            scatterer["amplitude"] * (TARGET_REFERENCE_RANGE_M / scatterer["range_m"]) ** 2,
            dtype=float,
        )
        propagation_bias = rng.uniform(-np.pi, np.pi)
        for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
            channel_slice = slice(tx * 4, (tx + 1) * 4)
            chirp[:, :, channel_slice, :] += _scatterer_if(
                static_ranges[:, :, tx], scatterer["angle_deg"], static_amplitude,
                propagation_bias, positions[channel_slice], adc_time_s,
            )

    # Independent receiver noise is added at the ADC input.  Quantisation and
    # saturation are applied to I and Q independently, like a complex ADC
    # assembled from two signed converter channels.
    # The gain/phase mismatch is a fixed per-RX calibration error and the PLL
    # term is common to the four RX channels of each physical TX chirp.
    gain = 10.0 ** (rng.normal(0.0, RX_GAIN_MISMATCH_DB_STD, VIRTUAL_RX) / 20.0)
    phase = np.deg2rad(rng.normal(0.0, RX_PHASE_MISMATCH_DEG_STD, VIRTUAL_RX))
    chirp *= (gain * np.exp(1j * phase))[None, None, :, None]
    pll = np.zeros((frames, loops, RADAR_TX_CHIRPS_PER_LOOP), dtype=float)
    innovation_std = PLL_PHASE_NOISE_STD_RAD * np.sqrt(1.0 - PLL_PHASE_NOISE_RHO**2)
    for frame in range(frames):
        for loop in range(loops):
            previous = pll[frame - 1, loop, :] if frame else np.zeros(RADAR_TX_CHIRPS_PER_LOOP)
            pll[frame, loop, :] = PLL_PHASE_NOISE_RHO * previous + innovation_std * rng.standard_normal(RADAR_TX_CHIRPS_PER_LOOP)
    for tx in range(RADAR_TX_CHIRPS_PER_LOOP):
        chirp[:, :, tx * 4:(tx + 1) * 4, :] *= np.exp(1j * pll[:, :, tx, None, None])
    chirp += RECEIVER_NOISE_STD * (
        rng.standard_normal(chirp.shape) + 1j * rng.standard_normal(chirp.shape)
    )
    real = np.clip(np.real(chirp), -ADC_FULL_SCALE, ADC_FULL_SCALE - ADC_LSB)
    imag = np.clip(np.imag(chirp), -ADC_FULL_SCALE, ADC_FULL_SCALE - ADC_LSB)
    chirp = (np.rint(real / ADC_LSB) + 1j * np.rint(imag / ADC_LSB)) * ADC_LSB
    chirp = chirp.astype(np.complex64)
    adc = np.mean(chirp, axis=1).astype(np.complex64, copy=False)
    range_spectrum = np.fft.fft(chirp.astype(np.complex128), axis=-1)
    range_power = np.median(np.abs(range_spectrum) ** 2, axis=(0, 1, 2))
    excluded = np.zeros(ADC_SAMPLES, dtype=bool)
    for target_bin in TARGET_RANGE_BINS:
        excluded[max(0, target_bin - 2):min(ADC_SAMPLES, target_bin + 3)] = True
    noise_floor = float(np.median(range_power[~excluded]))
    range_fft_snr_db = [
        float(10.0 * np.log10(max(range_power[int(target_bin)], 1.0e-30) / max(noise_floor, 1.0e-30)))
        for target_bin in TARGET_RANGE_BINS
    ]
    directory = root / "radar" / "algorithm_input"
    directory.mkdir(parents=True)
    arrays = {
        "adc_cube": _array(directory / "adc_cube.npy", adc, ["frame", "virtual_antenna", "adc_sample"]),
        "frame_times_s": _array(directory / "frame_times_s.npy", np.arange(frames) / RADAR_RATE_HZ, ["frame"]),
        "chirp_cube": _array(directory / "chirp_cube.npy", chirp, ["frame", "chirp_loop", "virtual_antenna", "adc_sample"]),
    }
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.algorithm-input", "schema_version": 1,
        "source": {"kind": "paper_bridge_simulation", "radar_adc_iq": "synthetic_if_chirp", "seed": seed,
                   "target_range_bins": TARGET_RANGE_BINS.tolist(),
                   "target_ranges_m": target_ranges_m.tolist(),
                   "target_angles_deg": TARGET_ANGLES_DEG.tolist(),
                   "target_geometry": {
                       "guideway_height_m": GUIDEWAY_TO_GROUND_HEIGHT_M,
                       "target_state": "fixed_world_ground_or_tree_reference; radar follows guideway",
                       "target_x_m": TARGET_X_M.tolist(),
                       "baseline_range_m": TARGET_RANGES_M.tolist(),
                       "radial_displacement_projection": "q(t) * cos(angle)",
                       "reference_target_range_m": TARGET_REFERENCE_RANGE_M,
                   },
                   "target_snr_db": TARGET_SNR_DB.tolist(),
                   "snr_semantics": "per-target, per-TX, per-loop complex scattering coefficient before array projection and loop averaging",
                   "range_fft_snr_db": range_fft_snr_db,
                   "scene": {"guideway_height_m": GUIDEWAY_TO_GROUND_HEIGHT_M, "surface": "sandy soil with tree line",
                             "static_scatterers": list(STATIC_SCATTERERS),
                             "multipath_excess_path_m": MULTIPATH_DELAY_M,
                             "multipath_amplitude_ratio": MULTIPATH_AMPLITUDE_RATIO}},
        "packet_integrity": {"complete": True, "mode": "synthetic_payload_integrity", "payload_bytes": int(chirp.size * 4)},
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
            "virtual_array_positions_wavelengths": positions.tolist(),
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
            "adc_lsb": ADC_LSB, "receiver_noise_std": RECEIVER_NOISE_STD,
            "wavelength_m": WAVELENGTH_M,
            "tx_chirp_offsets_s": [0.0, RADAR_CHIRP_CYCLE_S],
            "adc_quantization": {
                "bits": ADC_BITS, "full_scale_v": ADC_FULL_SCALE,
                "lsb_v": ADC_LSB, "stored_dtype": "complex64",
                "quantized_array": "chirp_cube",
                "saturated_i_count": int(np.count_nonzero((np.real(chirp) <= -ADC_FULL_SCALE) | (np.real(chirp) >= ADC_FULL_SCALE - ADC_LSB))),
                "saturated_q_count": int(np.count_nonzero((np.imag(chirp) <= -ADC_FULL_SCALE) | (np.imag(chirp) >= ADC_FULL_SCALE - ADC_LSB))),
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


def _adxl_package(root: Path, acceleration: np.ndarray, seed: int) -> None:
    rng = np.random.default_rng(seed + 1)
    sample_count = acceleration.size
    values = np.zeros((sample_count, 3), dtype=np.float64)
    # ADXL355 at the configured 1 kHz ODR: use the ±2 g noise density from
    # the data sheet, a small fixed bias, and a sub-percent scale error.  The
    # other two axes contain only cross-axis leakage and sensor noise.
    noise_std = (
        ADXL_NOISE_DENSITY_G_PER_SQRT_HZ * 9.80665
        * np.sqrt(ADXL_RATE_HZ / 2.0)
    )
    delay_samples = int(round(ADXL_GROUP_DELAY_S * ADXL_RATE_HZ))
    delayed_acceleration = np.empty_like(acceleration)
    delayed_acceleration[:delay_samples] = acceleration[0]
    delayed_acceleration[delay_samples:] = acceleration[:-delay_samples]
    values[:, 0] = (1.0003 * delayed_acceleration + ADXL_BIAS_MPS2[0]
                    + noise_std * rng.standard_normal(sample_count))
    values[:, 1] = 0.001 * delayed_acceleration + ADXL_BIAS_MPS2[1] + noise_std * rng.standard_normal(sample_count)
    values[:, 2] = -0.0007 * delayed_acceleration + ADXL_BIAS_MPS2[2] + noise_std * rng.standard_normal(sample_count)
    raw = np.rint(values / 9.80665 * 256000.0).astype(np.int32)
    directory = root / "adxl355" / "algorithm_input"
    directory.mkdir(parents=True)
    times = BASE_TIME_NS + np.arange(sample_count, dtype=np.int64) * round(1.0e9 / ADXL_RATE_HZ)
    arrays = {
        "acceleration_raw": _array(directory / "acceleration_raw.npy", raw, ["sample", "axis"]),
        "acceleration_mps2": _array(directory / "acceleration_mps2.npy", values, ["sample", "axis"]),
        "drdy_monotonic_ns": _array(directory / "drdy_monotonic_ns.npy", times, ["sample"]),
        "estimated_sample_monotonic_ns": _array(directory / "estimated_sample_monotonic_ns.npy", times, ["sample"]),
        "sample_times_s": _array(directory / "sample_times_s.npy", np.arange(sample_count) / ADXL_RATE_HZ, ["sample"]),
    }
    _json(directory / "manifest.json", {
        "schema": "mmwavecapture.adxl355-input", "schema_version": 1,
        "source": {"kind": "paper_bridge_simulation", "structural_axis": "paper-parameterized",
                   "noise_density_g_per_sqrt_hz": ADXL_NOISE_DENSITY_G_PER_SQRT_HZ,
                   "bias_mps2": ADXL_BIAS_MPS2.tolist(), "scale_x": 1.0003,
                   "cross_axis_coefficients": [0.001, -0.0007],
                   "digital_group_delay_s": ADXL_GROUP_DELAY_S},
        "capture": {"complete": True, "samples": sample_count, "odr_hz_nominal": ADXL_RATE_HZ, "range_g": 2,
                    "group_delay_ns": round(ADXL_GROUP_DELAY_S * 1.0e9), "group_delay_calibrated": True,
                    "native_summary": {"samples": sample_count, "mock": True, "simulation": True}},
        "timing": {"clock": "CLOCK_MONOTONIC", "drdy_monotonic_ns_semantics": "synthetic nominal DRDY schedule",
                   "estimated_sample_monotonic_ns_semantics": "synthetic nominal sample schedule"},
        "arrays": arrays,
    })


def generate(output: str | Path, *, duration_s: float = 4.0, seed: int = 2026) -> Path:
    output = Path(output)
    if duration_s <= 0.0 or duration_s > DURATION_S:
        raise ValueError(f"duration must be in (0, {DURATION_S:g}] seconds")
    reference_time_s, displacement, acceleration, _ = simulate_response()
    count = round(duration_s * RADAR_RATE_HZ)
    if count < 2:
        raise ValueError("duration does not contain enough radar frames")
    adxl_step = round(REFERENCE_RATE_HZ / ADXL_RATE_HZ)
    frame_time_s = np.arange(count, dtype=float) / RADAR_RATE_HZ + RADAR_APERTURE_CENTER_OFFSET_S
    loop_offsets_s = (np.arange(RADAR_LOOPS_PER_FRAME, dtype=float) - (RADAR_LOOPS_PER_FRAME - 1) / 2.0) * RADAR_LOOP_START_INTERVAL_S
    tx_offsets_s = (np.arange(RADAR_TX_CHIRPS_PER_LOOP) - (RADAR_TX_CHIRPS_PER_LOOP - 1) / 2.0) * (RADAR_IDLE_TIME_S + RADAR_RAMP_END_TIME_S)
    tx_time_s = frame_time_s[:, None, None] + loop_offsets_s[None, :, None] + tx_offsets_s[None, None, :]
    tx_q = np.interp(tx_time_s, reference_time_s, displacement)
    frame_a = acceleration[::adxl_step][: round(duration_s * ADXL_RATE_HZ)]
    with tempfile.TemporaryDirectory(prefix="bridge-package-") as temporary:
        staging = Path(temporary) / "package"
        staging.mkdir()
        _radar_package(staging, tx_q, seed)
        _adxl_package(staging, frame_a, seed)
        sync = staging / "sync"
        sync.mkdir()
        radar_time = BASE_TIME_NS + np.arange(count, dtype=np.int64) * round(1.0e9 / RADAR_RATE_HZ)
        np.save(sync / "radar_frame_monotonic_ns.npy", radar_time, allow_pickle=False)
        radar_adc_time = radar_time + round(RADAR_APERTURE_CENTER_OFFSET_S * 1.0e9)
        np.save(sync / "radar_adc_sample_monotonic_ns.npy", radar_adc_time, allow_pickle=False)
        _json(staging / "paper_response_metadata.json", reference_metadata())
        _json(sync / "timeline.json", {"schema_version": 1, "status": "complete",
                                        "sync_mode": "software_timestamp", "timestamp_quality": "sensor_start_bracket_estimate",
                                        "hardware_validated": False, "clock": "CLOCK_MONOTONIC", "unit": "nanoseconds",
                                        "frame_count": count, "nominal_frame_period_ns": round(1.0e9 / RADAR_RATE_HZ),
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
        np.save(truth / "acceleration_mps2.npy", frame_a, allow_pickle=False)
        np.save(truth / "adxl_time_ns.npy", BASE_TIME_NS + np.arange(frame_a.size, dtype=np.int64) * round(1.0e9 / ADXL_RATE_HZ), allow_pickle=False)
        _json(staging / "status.json", {"schema_version": 1, "status": "complete", "source_type": "paper_bridge_simulation", "reference": reference_metadata()["paper"]})
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    return output
