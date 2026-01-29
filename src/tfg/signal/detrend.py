"""
Implement signal detrending with missing data and GPU support.

This module provides the `SignalDetrender` class, which offers
functionality similar to `scipy.signal.detrend` but handles `NaN` values
gracefully and utilises GPU acceleration when CuPy is available.

Classes
-------
SignalDetrender
    Encapulate settings and logic for removing trends from signals.

"""

import typing as tp

import numpy as np
import numpy.typing as npt
import scipy as sp

from ..utils import check_mode


# Determine if CuPy is available for GPU acceleration.
try:
    import cupy as cp
    import cupyx.scipy as spx

    zp = spx
    xp = cp

except ImportError:
    zp = sp
    xp = np

__all__ = ["SignalDetrender"]

type DetrendMode = tp.Literal["linear", "l", "constant", "c"]


class SignalDetrender:
    """
    Encapulate settings and logic for removing trends from signals.

    This class provides tools to remove linear or constant trends from
    time series data. It is designed to handle missing data (NaNs) and
    automatically leverage GPU acceleration if CuPy is installed.

    Parameters
    ----------
    axis : int, default=-1
        The axis along which the detrending logic is applied.
    mode : DetrendMode, default="linear"
        The type of detrending to perform:
        - "linear": Remove the least-squares linear fit.
        - "constant": Remove the mean value of each series.

    Attributes
    ----------
    axis : int
        The axis configuration for signal processing.
    mode : DetrendMode
        The selected detrending algorithm.
    """

    def __init__(
        self, *, axis: int = -1, mode: DetrendMode = "linear"
    ) -> None:
        """Initialise the signal detrender with settings."""
        self.axis = axis
        self.mode = mode

    def detrend(
        self,
        timeseries: npt.ArrayLike,
        indices: npt.ArrayLike | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Remove linear or constant trend from a timeseries.

        This method is numerically identical to `scipy.signal.detrend`
        but extends functionality to handle missing data (NaN values)
        and provides GPU support when available.

        Parameters
        ----------
        timeseries : npt.ArrayLike
            Input data array of shape (m, n) where m is the number of
            series and n is the number of time samples.
        indices : npt.ArrayLike, optional
            Array of indices specifying which samples to use for
            fitting the trend. Useful when data contains NaNs at known
            positions. If `None`, all samples are used.

        Returns
        -------
        npt.NDArray[np.float64]
            The detrended data as a CPU-based NumPy array.

        Raises
        ------
        ValueError
            If the indices are negative or exceed series length.

        Notes
        -----
        For ``mode='linear'``, the fit is calculated using only the
        samples at the specified `indices`, but the result is applied
        across the entire series.

        Examples
        --------
        >>> import numpy as np
        >>> data = np.array(
        ...     [[1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0]], dtype=np.float64
        ... )
        >>> detrender = SignalDetrender()
        >>> detrended = detrender.detrend(data)
        """
        check_mode(self, "mode", DetrendMode)

        if self.mode in ["constant", "c"]:
            return self._detrend_constant(timeseries)

        return self._detrend_linear(timeseries, indices)

    def _detrend_constant(
        self, timeseries: npt.ArrayLike
    ) -> npt.NDArray[np.float64]:
        """
        Remove the mean value from each series.

        Parameters
        ----------
        timeseries : npt.ArrayLike
            The input data.

        Returns
        -------
        npt.NDArray[np.float64]
            The demeaned data.
        """
        timeseries_arr = xp.asarray(timeseries, dtype=np.float64)

        result = timeseries_arr - xp.nanmean(
            timeseries_arr, self.axis, keepdims=True
        )

        return xp.asnumpy(result) if xp is not np else result  # type: ignore

    def _detrend_linear(
        self, timeseries: npt.ArrayLike, indices: npt.ArrayLike | None
    ) -> npt.NDArray[np.float64]:
        """
        Remove the linear trend from each series.

        Parameters
        ----------
        timeseries : npt.ArrayLike
            The input data.
        indices : npt.ArrayLike, optional
            The indices to use for calculating the linear fit.

        Returns
        -------
        npt.NDArray[np.float64]
            The detrended data.

        Raises
        ------
        ValueError
            If indices are invalid for the input dimensions.
        """
        axis = self.axis

        timeseries_arr = np.asarray(timeseries)

        ts_shape = timeseries_arr.shape
        n_samples = ts_shape[axis]

        if indices is None:
            indices = np.arange(n_samples, dtype=np.int32)

        valid_indices = np.sort(np.unique(indices))

        n_valid = len(valid_indices)

        if valid_indices[-1] >= n_samples:
            raise ValueError("Indices must be less than series length.")

        if valid_indices[0] < 0:
            raise ValueError("Indices must be non-negative.")

        if n_valid < 2:
            return timeseries_arr.copy()

        ts_dtype = timeseries_arr.dtype.char

        if ts_dtype not in "dfDF":
            ts_dtype = "d"

        # Reference axis for the fit.
        x_min = np.min(valid_indices)
        x_max = np.max(valid_indices)
        x_axis = xp.arange(n_samples, dtype=ts_dtype)
        x_axis = (x_axis[valid_indices] - x_min + 1.0) / (x_max - x_min + 1.0)

        # Design matrix for linear fit: [x, ones].
        a_matrix = xp.ones((n_valid, 2), dtype=ts_dtype)
        a_matrix[:, 0] = x_axis

        # Move processed axis to the front for easier reshaping.
        rank = len(ts_shape)
        if axis < 0:
            axis = axis + rank

        ts_active = (
            xp.asarray(timeseries_arr)
            if xp is not np
            else timeseries_arr.copy()
        )

        ts_restructured = xp.moveaxis(ts_active, axis, 0)
        tr_shape = ts_restructured.shape
        ts_restructured = ts_restructured.reshape(n_samples, -1)

        if ts_restructured.dtype.char not in "dfDF":
            ts_restructured = ts_restructured.astype(ts_dtype)

        # Valid values to adjust.
        y_values = ts_restructured[valid_indices, :]

        # Resolve least squares.
        coefs, _, _, _ = zp.linalg.lstsq(a_matrix, y_values)

        # Subtract trend.
        y_detrended = y_values - a_matrix @ coefs

        # Place back into result.
        ts_restructured[valid_indices, :] = y_detrended

        # Restore original shape.
        ts_restructured = ts_restructured.reshape(tr_shape)
        result = xp.moveaxis(ts_restructured, 0, axis)

        return xp.asnumpy(result) if xp is not np else result
