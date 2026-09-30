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
DURATION_S = 4.0

# Assumptions, not values identified from the paper.
ARRIVAL_S = 0.5
CAR_COUNT = 5
DYNAMIC_ACCELERATION_PEAK_MPS2 = 0.45  # illustrative scale near Fig. 4(b)'s range
EXCITATION_WEIGHTS = np.array([1.0, 0.8, 0.7, 0.5])


def excitation_frequencies_hz() -> np.ndarray:
    return SPEED_KMH / (3.6 * CHARACTERISTIC_LENGTHS_M)


def _smooth_step(time_s: np.ndarray, start_s: float, width_s: float):
    """C2 transition and its analytic second time derivative."""
    u = np.clip((time_s - start_s) / width_s, 0.0, 1.0)
    value = u**3 * (10.0 - 15.0 * u + 6.0 * u**2)
    second = 60.0 * u * (1.0 - u) * (1.0 - 2.0 * u) / width_s**2
    return value, second


def simulate_response():
    """Return time, total displacement, consistent acceleration and modal q.

    q = q_quasi_static + sum(q_mode). Each mode satisfies
    q'' + 2*zeta*omega*q' + omega**2*q = assumed_drive.
    The acceleration is computed from this equation and the analytic envelope,
    never independently synthesized or derived from noisy displacement.
    """
    dt = 1.0 / REFERENCE_RATE_HZ
    time_s = np.arange(round(DURATION_S * REFERENCE_RATE_HZ)) * dt
    crossing_s = GUIDEWAY_SPAN_M / (SPEED_KMH / 3.6)
    exit_s = ARRIVAL_S + CAR_COUNT * CHARACTERISTIC_LENGTHS_M[0] / (SPEED_KMH / 3.6)
    rise, rise_second = _smooth_step(time_s, ARRIVAL_S, crossing_s)
    fall, fall_second = _smooth_step(time_s, exit_s, crossing_s)
    envelope = rise - fall
    envelope_second = rise_second - fall_second
    drive = envelope * np.sum(
        EXCITATION_WEIGHTS[:, None]
        * np.sin(2.0 * np.pi * excitation_frequencies_hz()[:, None] * (time_s - ARRIVAL_S)),
        axis=0,
    )

    omega = 2.0 * np.pi * MODAL_FREQUENCIES_HZ
    state = np.zeros((2, omega.size))
    modal_q = np.zeros((omega.size, time_s.size))
    modal_a = np.zeros_like(modal_q)

    def derivative(y, force):
        q, velocity = y
        return np.array([velocity, force - 2.0 * MODAL_DAMPING * omega * velocity - omega**2 * q])

    for k in range(time_s.size - 1):
        midpoint_drive = (drive[k] + drive[k + 1]) / 2.0
        k1 = derivative(state, drive[k])
        k2 = derivative(state + dt * k1 / 2.0, midpoint_drive)
        k3 = derivative(state + dt * k2 / 2.0, midpoint_drive)
        k4 = derivative(state + dt * k3, drive[k + 1])
        state += dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        modal_q[:, k + 1] = state[0]
        modal_a[:, k + 1] = derivative(state, drive[k + 1])[1]

    dynamic_scale = DYNAMIC_ACCELERATION_PEAK_MPS2 / np.max(np.abs(modal_a.sum(axis=0)))
    modal_q *= dynamic_scale
    modal_a *= dynamic_scale
    displacement = PEAK_DEFLECTION_M * envelope + modal_q.sum(axis=0)
    acceleration = PEAK_DEFLECTION_M * envelope_second + modal_a.sum(axis=0)
    scale = PEAK_DEFLECTION_M / np.max(np.abs(displacement))
    return time_s, scale * displacement, scale * acceleration, scale * modal_q


def reference_metadata() -> dict:
    """Keep published quantities separate from assumed synthesis parameters."""
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
            "car_count": CAR_COUNT,
            "envelope": "quintic entry/exit transitions over one span-crossing time",
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
