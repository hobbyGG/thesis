"""Scenario (what is observed) and impairments (how sensors and environment deviate).

``Scenario()`` is the A20-parameterized nominal scene and ``Impairments()``
adds no error beyond the nominal sensor model, so ``generate()`` with the
defaults is the retained nominal package.  Every field is an explicit
simulation assumption unless the comment names a published source.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .response import (
    ARRIVAL_S,
    DYNAMIC_ACCELERATION_PEAK_MPS2,
    EXCITATION_WEIGHTS,
    PASSAGE_DURATION_S,
    PEAK_DEFLECTION_M,
    SPEED_KMH,
    STATIC_INTERVAL_S,
)

NOMINAL_EVENT_STARTS_S = tuple(
    float(start) for start in ARRIVAL_S + np.arange(3, dtype=float) * (PASSAGE_DURATION_S + STATIC_INTERVAL_S)
)


@dataclass(frozen=True)
class Scenario:
    """Structural response shared by radar and ADXL, and the radar scene."""

    # Structural response (see response.simulate_response).
    speed_kmh: float = SPEED_KMH
    peak_deflection_m: float = PEAK_DEFLECTION_M
    passage_duration_s: float = PASSAGE_DURATION_S
    event_starts_s: tuple[float, ...] = NOMINAL_EVENT_STARTS_S
    dynamic_acceleration_peak_mps2: float = DYNAMIC_ACCELERATION_PEAK_MPS2
    excitation_weights: tuple[float, ...] = tuple(float(w) for w in EXCITATION_WEIGHTS)
    excitation_phases_rad: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0)
    ambient_acceleration_rms_mps2: float = 0.0
    ambient_seed: int = 0
    # Radar scene: world-fixed ground points seen from the guideway, height_m
    # below the radar.  Amplitudes refer to a 10 m reference range.
    height_m: float = 10.0
    target_angles_deg: tuple[float, ...] = (3.0, 9.0, 15.0, 21.0, 25.0)
    target_amplitudes: tuple[float, ...] = (0.25, 0.2375, 0.225, 0.2125, 0.2)
    target_snr_db: tuple[float, ...] = (30.0, 27.5, 25.0, 22.5, 20.0)
    # Weak stationary clutter (sandy ground, tree line).
    static_names: tuple[str, ...] = ("sandy_ground", "tree_line")
    static_ranges_m: tuple[float, ...] = (10.82, 11.08)
    static_angles_deg: tuple[float, ...] = (-18.0, 28.0)
    static_amplitudes: tuple[float, ...] = (0.025, 0.01875)

    def target_ranges_m(self) -> np.ndarray:
        x = self.height_m * np.tan(np.deg2rad(np.asarray(self.target_angles_deg)))
        return np.sqrt(self.height_m**2 + x**2)

    def response_kwargs(self) -> dict:
        return {
            "speed_kmh": self.speed_kmh,
            "peak_deflection_m": self.peak_deflection_m,
            "passage_duration_s": self.passage_duration_s,
            "event_starts_s": np.asarray(self.event_starts_s, dtype=float),
            "dynamic_acceleration_peak_mps2": self.dynamic_acceleration_peak_mps2,
            "excitation_weights": self.excitation_weights,
            "excitation_phases_rad": self.excitation_phases_rad,
            "ambient_acceleration_rms_mps2": self.ambient_acceleration_rms_mps2,
            "ambient_seed": self.ambient_seed,
        }

    def static_scatterer_dicts(self) -> list[dict]:
        return [
            {"name": name, "range_m": r, "angle_deg": a, "amplitude": amplitude}
            for name, r, a, amplitude in zip(
                self.static_names, self.static_ranges_m, self.static_angles_deg, self.static_amplitudes
            )
        ]


@dataclass(frozen=True)
class Impairments:
    """Deviations of sensors and environment from the nominal model."""

    # Radar.  Lowers every target's SNR and raises the receiver noise by this
    # many dB.
    snr_offset_db: float = 0.0
    # Constant complex term at every target's range-angle cell (DC offset,
    # crosstalk, static clutter lumped together), as a fraction of the target
    # amplitude, with a random phase per target.  It moves with the radar, so
    # it does not rotate with the structural motion.
    iq_offset_ratio: float = 0.0
    # Independent low-pass line-of-sight motion (wind-driven non-rigid
    # scatterers) of the listed targets; stationary standard deviation in m.
    target_sway_std_m: float = 0.0
    target_sway_corner_hz: float = 0.5
    target_sway_targets: tuple[int, ...] = (0, 4)
    # Contiguous run of radar frames set to NaN (all targets lost at once).
    radar_dropout_s: float = 0.0
    radar_dropout_start_s: float = 0.53
    # ADXL355 structural axis.  Static offset including the gravity
    # projection (None keeps the nominal turn-on bias).
    adxl_bias_x_mps2: float | None = None
    # Bias random walk intensity, m/s^2 per sqrt(s).
    adxl_bias_walk_mps2_per_sqrt_s: float = 0.0
    # Multiplies the data-sheet white-noise standard deviation.
    adxl_noise_scale: float = 1.0
    # Relative sensitivity error of the structural axis.
    adxl_scale_error: float = 3.0e-4
    # Gravity leaking into the axis with the structural rotation, which
    # follows the local deflection: a_err = gain * q(t), in (m/s^2) per m.
    adxl_tilt_gain_mps2_per_m: float = 0.0
    # Residual error of the calibrated group-delay compensation, and zero-mean
    # jitter of the DRDY timestamps (the samples are taken on the true schedule).
    adxl_timestamp_offset_s: float = 0.0
    adxl_timestamp_jitter_std_s: float = 0.0
    # Phase of the ADXL DRDY grid relative to the radar frame grid, and the
    # relative error of its output data rate.  Unlike the timestamp error,
    # these change the sampling instants and the timestamps together.
    adxl_clock_phase_s: float = 0.0
    adxl_odr_error: float = 0.0
