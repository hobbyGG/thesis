import numpy as np


def wrap_to_pi(values):
    arr = np.asarray(values, dtype=float)
    wrapped = (arr + np.pi) % (2.0 * np.pi) - np.pi
    return np.where(wrapped <= -np.pi, wrapped + 2.0 * np.pi, wrapped)


def prediction_correct_wrapped_phase(wrapped, prediction):
    wrapped_arr = np.asarray(wrapped, dtype=float)
    prediction_arr = np.asarray(prediction, dtype=float)
    return wrapped_arr + 2.0 * np.pi * np.round((prediction_arr - wrapped_arr) / (2.0 * np.pi))


def itoh_unwrap(wrapped_phase):
    return np.unwrap(np.asarray(wrapped_phase, dtype=float))


def count_branch_errors(estimated_phase, true_phase, tolerance=np.pi):
    estimated = np.asarray(estimated_phase, dtype=float)
    truth = np.asarray(true_phase, dtype=float)
    valid = np.isfinite(estimated) & np.isfinite(truth)
    if not np.any(valid):
        return 0
    branch_error = np.abs(estimated[valid] - truth[valid]) > float(tolerance)
    return int(np.count_nonzero(branch_error))
