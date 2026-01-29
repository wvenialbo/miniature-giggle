"""
Provide signal normalisation utilities.

This module contains functions to normalise signals based on their
physical characteristics, such as Hilbert envelope-based normalisation
to mitigate damping effects.

Functions
---------
normalize_by_envelope
    Normalise a signal using its Hilbert envelope.

"""

import numpy as np
import numpy.typing as npt
import scipy as sp


def normalize_by_envelope(
    timeseries: npt.ArrayLike, epsilon: float = 1e-9
) -> npt.NDArray[np.float64]:
    """
    Normalise a signal using its Hilbert envelope.

    This function mitigates damping effects by dividing the source
    signal by its analytic envelope.

    Parameters
    ----------
    timeseries : npt.ArrayLike
        The input time series data.
    epsilon : float, default=1e-9
        A small value to avoid division by zero in regions where the
        signal amplitude vanishes.

    Returns
    -------
    npt.NDArray[np.float64]
        The normalised signal with constant-amplitude characteristics.
    """
    # Calculate the analytic signal.
    analitics = sp.signal.hilbert(timeseries)
    envelope = np.abs(analitics)

    # Avoid division by zero in signals that completely die out.
    envelope[envelope < epsilon] = epsilon

    # Signal with constant amplitude.
    result = timeseries / envelope

    return result.astype(np.float64).view(np.ndarray)


__all__ = ["normalize_by_envelope"]
