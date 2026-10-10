import numpy as np


def prediction_correct_wrapped_phase(wrapped, prediction):
    wrapped = np.asarray(wrapped, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    return wrapped + 2.0 * np.pi * np.round((prediction - wrapped) / (2.0 * np.pi))


def itoh_unwrap(values):
    return np.unwrap(np.asarray(values, dtype=float))


def causal_iq_circle_phase(iq_slow_time: np.ndarray, *, min_radius: float = 1.0e-12):
    """Estimate a running IQ-circle center and return wrapped phase.

    The sufficient statistics are updated in time order.  At sample ``k`` the
    circle fit therefore uses samples through ``k`` only.  A changing center
    must not create a fictitious phase step, so each increment uses the
    current center for both the current and previous IQ sample.  The returned
    phase is referenced to zero at the first valid sample and is wrapped to
    ``(-pi, pi]``; the Kalman stage performs only the ordinary nearest-branch
    continuation from the previous target phase.  The fifth return value is
    the centered, radius-normalized IQ stream for diagnostics and later
    fusion extensions.
    """

    values = np.asarray(iq_slow_time, dtype=np.complex128)
    if values.ndim != 2:
        raise ValueError("iq_slow_time must have shape (targets, samples)")
    targets, samples = values.shape
    wrapped = np.full((targets, samples), np.nan, dtype=float)
    centers = np.zeros((targets, samples), dtype=np.complex128)
    radii = np.full((targets, samples), np.nan, dtype=float)
    residuals = np.full((targets, samples), np.nan, dtype=float)
    normalized = np.full((targets, samples), np.nan + 1j * np.nan, dtype=np.complex128)

    for target in range(targets):
        gram = np.zeros((3, 3), dtype=float)
        rhs = np.zeros(3, dtype=float)
        count = 0
        center = 0.0 + 0.0j
        radius = min_radius
        previous = np.nan + 1j * np.nan
        phase = 0.0
        for sample in range(samples):
            z = values[target, sample]
            if not (np.isfinite(z.real) and np.isfinite(z.imag)):
                centers[target, sample] = center
                radii[target, sample] = radius
                continue

            x, y = float(z.real), float(z.imag)
            row = np.array([2.0 * x, 2.0 * y, 1.0], dtype=float)
            gram += np.outer(row, row)
            rhs += row * (x * x + y * y)
            count += 1
            if count >= 3:
                try:
                    condition = np.linalg.cond(gram)
                    # A short arc makes the algebraic circle problem nearly
                    # singular.  Waiting for a well-conditioned geometry is
                    # preferable to accepting a huge false center that would
                    # rotate the phase by radians.
                    estimate = np.linalg.solve(gram, rhs) if np.isfinite(condition) and condition < 1.0e4 else None
                except np.linalg.LinAlgError:
                    estimate = None
                if estimate is not None and np.all(np.isfinite(estimate)):
                    cx, cy, d = (float(value) for value in estimate)
                    radius_squared = d + cx * cx + cy * cy
                    if np.isfinite(radius_squared) and radius_squared > min_radius * min_radius:
                        candidate = np.hypot(cx, cy)
                        # Reject an ill-conditioned algebraic fit that would
                        # make a single noisy sample dominate the phase.
                        if candidate < 1.0e6 and np.sqrt(radius_squared) < 1.0e6:
                            center = complex(cx, cy)
                            radius = max(float(np.sqrt(radius_squared)), min_radius)

            centered = z - center
            magnitude = abs(centered)
            if magnitude < min_radius:
                centered = z
                magnitude = abs(centered)
            if magnitude >= min_radius:
                if np.isfinite(previous.real) and np.isfinite(previous.imag):
                    previous_centered = previous - center
                    if abs(previous_centered) < min_radius:
                        previous_centered = previous
                    increment = np.angle(centered * np.conj(previous_centered))
                    if np.isfinite(increment):
                        phase += float(increment)
                wrapped[target, sample] = float(np.angle(np.exp(1j * phase)))
                previous = z

            centers[target, sample] = center
            if radius <= min_radius:
                radius = max(magnitude, min_radius)
            radii[target, sample] = radius
            residuals[target, sample] = abs(abs(centered) - radius)
            normalized[target, sample] = centered / max(radius, min_radius)

    return wrapped, centers, radii, residuals, normalized
