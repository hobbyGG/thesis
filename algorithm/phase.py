import numpy as np


def prediction_correct_wrapped_phase(wrapped, prediction):
    wrapped = np.asarray(wrapped, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    return wrapped + 2.0 * np.pi * np.round((prediction - wrapped) / (2.0 * np.pi))


def itoh_unwrap(values):
    return np.unwrap(np.asarray(values, dtype=float))
