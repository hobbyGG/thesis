import numpy as np


def unwrap_nearest_branch(wrapped_phase_rad, available_mask, selected_indices):
    """Nearest-2*pi unwrapping of each selected target from its previous valid phase.

    phi_u[k] = phi_w[k] + 2*pi*round((phi_u[k-1] - phi_w[k]) / (2*pi)).
    The first valid sample is kept as is; a missing sample leaves the
    reference at the last valid unwrapped phase.  Acceleration is not used.
    """

    wrapped = np.asarray(wrapped_phase_rad, dtype=float)
    unwrapped = np.full(wrapped.shape, np.nan, dtype=float)
    for i in np.asarray(selected_indices, dtype=int):
        previous = np.nan
        for k in range(wrapped.shape[1]):
            phase = wrapped[i, k]
            if not (available_mask[i, k] and np.isfinite(phase)):
                continue
            if np.isfinite(previous):
                phase += 2.0 * np.pi * np.round((previous - phase) / (2.0 * np.pi))
            unwrapped[i, k] = previous = phase
    return unwrapped


def recursive_circle_phase(iq_slow_time: np.ndarray, *, min_radius: float = 1.0e-12):
    """Recursive algebraic (Kasa) circle fit of slow-time IQ and phase extraction.

    The normal equations are accumulated in time order, so the circle centre
    c_k depends on samples 0..k only.  Each phase increment is the angle
    between consecutive samples measured about the current centre c_k, which
    prevents a centre update from producing a spurious phase step.  The
    accumulated phase is zero at the first valid sample and is wrapped to
    (-pi, pi].  Returns (wrapped phase, centre, radius, radial residual,
    centred radius-normalised IQ); the last three are diagnostics only.
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
        coordinate_scale = None
        for sample in range(samples):
            z = values[target, sample]
            if not (np.isfinite(z.real) and np.isfinite(z.imag)):
                centers[target, sample] = center
                radii[target, sample] = radius
                continue

            x, y = float(z.real), float(z.imag)
            if coordinate_scale is None:
                # Keep the algebraic fit coordinates O(10) so the constant
                # term and the IQ terms have comparable numerical weight.
                coordinate_scale = max(abs(z) / 10.0, min_radius)
            x_scaled = x / coordinate_scale
            y_scaled = y / coordinate_scale
            row = np.array([2.0 * x_scaled, 2.0 * y_scaled, 1.0], dtype=float)
            gram += np.outer(row, row)
            rhs += row * (x_scaled * x_scaled + y_scaled * y_scaled)
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
                    cx_scaled, cy_scaled, d_scaled = (float(value) for value in estimate)
                    radius_squared_scaled = d_scaled + cx_scaled * cx_scaled + cy_scaled * cy_scaled
                    if np.isfinite(radius_squared_scaled) and radius_squared_scaled > min_radius * min_radius:
                        candidate = np.hypot(cx_scaled, cy_scaled)
                        # Reject an ill-conditioned algebraic fit that would
                        # make a single noisy sample dominate the phase.
                        if candidate < 1.0e6 and np.sqrt(radius_squared_scaled) < 1.0e6:
                            center = coordinate_scale * complex(cx_scaled, cy_scaled)
                            radius = max(float(coordinate_scale * np.sqrt(radius_squared_scaled)), min_radius)

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
