"""One A20-informed synthetic response; no measured time history is replayed.

A20 Table 1 supplies modal frequencies/damping, Fig. 4's accompanying text
supplies the measured total peak deflection, and Eq. (19) supplies excitation
frequencies. Force amplitudes, modal participation and passage envelope below
are explicit simulation assumptions. All modes describe one off-axis scalar
observation, not a spatial reconstruction of the girder.
"""

import numpy as np

REFERENCE_TITLE = (
    "Dynamics identification of guideway girder and assessment of the effects "
    "on high-speed maglev vehicle-guideway coupled system"
)
MODAL_FREQUENCIES_HZ = np.array([10.35, 13.41, 27.10, 43.84, 52.93, 84.44])
MODAL_DAMPING = np.array([0.0255, 0.0144, 0.0029, 0.0057, 0.0045, 0.0021])
CHARACTERISTIC_LENGTHS_M = np.array([24.768, 6.192, 3.096, 1.032])
GUIDEWAY_SPAN_M = 24.768
SPEED_KMH = 300.0
PEAK_DEFLECTION_M = 1.712e-3  # A20 Fig. 4 measured value, not modal amplitude.
REFERENCE_RATE_HZ = 3000.0
DURATION_S = 13.0

# Assumptions, not values identified from the paper.
ARRIVAL_S = 0.5
STATIC_INTERVAL_S = 5.0
CAR_COUNT = 5
PASSAGE_DURATION_S = 0.8
TRANSITION_DURATION_S = 0.12
DYNAMIC_ACCELERATION_PEAK_MPS2 = 0.45  # illustrative scale near Fig. 4(b)'s range
EXCITATION_WEIGHTS = np.array([1.0, 0.8, 0.7, 0.5])
# Ambient microtremor: band-limited white forcing of the same modes.  The
# 2 s pre-roll lets the modal states reach their stationary level before t = 0.
AMBIENT_CORNER_HZ = 120.0
AMBIENT_PRE_ROLL_S = 2.0


def excitation_frequencies_hz(speed_kmh: float = SPEED_KMH) -> np.ndarray:
    return speed_kmh / (3.6 * CHARACTERISTIC_LENGTHS_M)


def _smooth_step(time_s: np.ndarray, start_s: float, width_s: float):
    """C2 transition and its analytic second time derivative."""
    u = np.clip((time_s - start_s) / width_s, 0.0, 1.0)
    value = u**3 * (10.0 - 15.0 * u + 6.0 * u**2)
    second = 60.0 * u * (1.0 - u) * (1.0 - 2.0 * u) / width_s**2
    return value, second


def simulate_response(
    duration_s: float = DURATION_S,
    *,
    speed_kmh: float = SPEED_KMH,
    peak_deflection_m: float = PEAK_DEFLECTION_M,
    passage_duration_s: float = PASSAGE_DURATION_S,
    event_starts_s=None,
    dynamic_acceleration_peak_mps2: float = DYNAMIC_ACCELERATION_PEAK_MPS2,
    excitation_weights=None,
    excitation_phases_rad=None,
    ambient_acceleration_rms_mps2: float = 0.0,
    ambient_seed: int = 0,
):
    """Return time, total displacement, consistent acceleration and modal q.

    q = q_quasi_static + sum(q_mode). Each mode satisfies
    q'' + 2*zeta*omega*q' + omega**2*q = assumed_drive.
    The acceleration is computed from this equation and the analytic envelope,
    never independently synthesized or derived from noisy displacement.

    The defaults reproduce the A20-parameterized reference response.  Optional
    ambient microtremor is an independent random forcing of the same modes,
    scaled to ``ambient_acceleration_rms_mps2`` and added to displacement and
    acceleration after the passage peak has been normalised.
    """
    dt = 1.0 / REFERENCE_RATE_HZ
    time_s = np.arange(round(duration_s * REFERENCE_RATE_HZ)) * dt
    # Each event matches the roughly 1 s laser response: a fast 0.12 s rise,
    # 0.56 s near-peak interval, and fast 0.12 s fall. Five seconds of quiet
    # time separates consecutive responses so the three responses can be
    # inspected independently in one deterministic run.
    if event_starts_s is None:
        event_starts_s = ARRIVAL_S + np.arange(3, dtype=float) * (PASSAGE_DURATION_S + STATIC_INTERVAL_S)
    weights = EXCITATION_WEIGHTS if excitation_weights is None else np.asarray(excitation_weights, dtype=float)
    phases = np.zeros(weights.size) if excitation_phases_rad is None else np.asarray(excitation_phases_rad, dtype=float)
    frequencies = excitation_frequencies_hz(speed_kmh)
    envelope = np.zeros_like(time_s)
    envelope_second = np.zeros_like(time_s)
    drive = np.zeros_like(time_s)
    for event_start in event_starts_s:
        exit_s = event_start + passage_duration_s - TRANSITION_DURATION_S
        rise, rise_second = _smooth_step(time_s, event_start, TRANSITION_DURATION_S)
        fall, fall_second = _smooth_step(time_s, exit_s, TRANSITION_DURATION_S)
        event_envelope = rise - fall
        envelope += event_envelope
        envelope_second += rise_second - fall_second
        drive += event_envelope * np.sum(
            weights[:, None]
            * np.sin(2.0 * np.pi * frequencies[:, None] * (time_s - event_start) + phases[:, None]),
            axis=0,
        )

    omega = 2.0 * np.pi * MODAL_FREQUENCIES_HZ

    def integrate(force):
        """RK4 of the six modal oscillators; returns modal q and modal acceleration."""
        state = np.zeros((2, omega.size))
        modal_q = np.zeros((omega.size, force.size))
        modal_a = np.zeros_like(modal_q)

        def derivative(y, f):
            q, velocity = y
            return np.array([velocity, f - 2.0 * MODAL_DAMPING * omega * velocity - omega**2 * q])

        for k in range(force.size - 1):
            midpoint_force = (force[k] + force[k + 1]) / 2.0
            k1 = derivative(state, force[k])
            k2 = derivative(state + dt * k1 / 2.0, midpoint_force)
            k3 = derivative(state + dt * k2 / 2.0, midpoint_force)
            k4 = derivative(state + dt * k3, force[k + 1])
            state += dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
            modal_q[:, k + 1] = state[0]
            modal_a[:, k + 1] = derivative(state, force[k + 1])[1]
        return modal_q, modal_a

    modal_q, modal_a = integrate(drive)
    dynamic_scale = dynamic_acceleration_peak_mps2 / np.max(np.abs(modal_a.sum(axis=0)))
    modal_q *= dynamic_scale
    modal_a *= dynamic_scale
    displacement = peak_deflection_m * envelope + modal_q.sum(axis=0)
    acceleration = peak_deflection_m * envelope_second + modal_a.sum(axis=0)
    scale = peak_deflection_m / np.max(np.abs(displacement))
    displacement, acceleration, modal_q = scale * displacement, scale * acceleration, scale * modal_q

    if ambient_acceleration_rms_mps2 > 0.0:
        pre_roll = round(AMBIENT_PRE_ROLL_S * REFERENCE_RATE_HZ)
        rho = np.exp(-2.0 * np.pi * AMBIENT_CORNER_HZ / REFERENCE_RATE_HZ)
        white = np.random.default_rng([ambient_seed, 21]).standard_normal(time_s.size + pre_roll)
        kernel = rho ** np.arange(int(np.ceil(12.0 / -np.log(rho))))
        ambient_force = np.sqrt(1.0 - rho**2) * np.convolve(white, kernel)[: white.size]
        ambient_q, ambient_a = integrate(ambient_force)
        ambient_q = ambient_q.sum(axis=0)[pre_roll:]
        ambient_a = ambient_a.sum(axis=0)[pre_roll:]
        gain = ambient_acceleration_rms_mps2 / np.std(ambient_a)
        displacement = displacement + gain * ambient_q
        acceleration = acceleration + gain * ambient_a
    return time_s, displacement, acceleration, modal_q


def reference_metadata() -> dict:
    """Keep published quantities separate from assumed synthesis parameters."""
    event_starts = ARRIVAL_S + np.arange(3, dtype=float) * (PASSAGE_DURATION_S + STATIC_INTERVAL_S)
    return {
        "source_type": "paper_parameterized_synthetic",
        "paper": REFERENCE_TITLE,
        "publication": "High-speed Railway 4 (2026), 124–129",
        "published": {
            "span_m": GUIDEWAY_SPAN_M,
            "speed_kmh": SPEED_KMH,
            "modal_frequencies_hz": MODAL_FREQUENCIES_HZ.tolist(),
            "damping_ratios": MODAL_DAMPING.tolist(),
            "characteristic_lengths_m": CHARACTERISTIC_LENGTHS_M.tolist(),
            "measured_peak_deflection_m": PEAK_DEFLECTION_M,
            "locations": "Table 1, Eq. (19), Fig. 4 and accompanying text",
        },
        "assumed": {
            "arrival_s": ARRIVAL_S,
            "event_start_s": event_starts.tolist(),
            "car_count": CAR_COUNT,
            "passage_duration_s": PASSAGE_DURATION_S,
            "static_interval_s": STATIC_INTERVAL_S,
            "transition_duration_s": TRANSITION_DURATION_S,
            "envelope": "quintic entry/exit transitions around a short laser-like passage",
            "excitation_weights": EXCITATION_WEIGHTS.tolist(),
            "modal_participation": "unit gains at one illustrative off-axis observation",
            "dynamic_acceleration_peak_before_total_rescale_mps2": DYNAMIC_ACCELERATION_PEAK_MPS2,
        },
        "limitations": [
            "No original field time histories or full vehicle-guideway coupled model are reproduced.",
            "Total deflection includes quasi-static displacement; its FFT maximum need not be a structural mode.",
            "Amplitude scaling and forcing assumptions are not independent validation against the paper.",
        ],
    }
