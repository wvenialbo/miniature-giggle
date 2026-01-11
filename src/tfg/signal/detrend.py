import typing as tp

import numpy as np
import numpy.typing as npt
import scipy as sp

from ..utils import check_mode

try:
    import cupy as cp
    import cupyx.scipy as spx

    zp = spx
    xp = cp

except ImportError:
    zp = sp
    xp = np

DetrendMode = tp.Literal["linear", "l", "constant", "c"]


class SignalDetrender:

    def __init__(
        self, *, axis: int = -1, mode: DetrendMode = "linear"
    ) -> None:
        self.axis = axis
        self.mode = mode

    def detrend(
        self,
        timeseries: npt.ArrayLike,
        indices: npt.ArrayLike | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Remove linear or constant trend from a timeseries.

        This function is numerically identical to `scipy.signal.detrend` but
        extends functionality to handle missing data (NaN values) and
        provides GPU support when available. It can operate on subsets of
        data using the `indices` parameter.

        Parameters
        ----------
        timeseries : ArrayLike
            Input data array of shape (m, n) where m is the number of series
            and n is the number of time samples. Supports both float32 and
            float64.
        indices : ArrayLike or None, optional
            Array of indices specifying which samples to use for linear
            detrending.  Useful when data contains NaN values at known
            positions. Must be non-negative and less than the length of the
            time series along the specified axis. If None, all samples are
            used (default).
        axis : int, optional
            Axis along which to detrend the data. Default is -1 (last axis).
        mode : {'linear', 'constant'}, optional
            Type of detrending to perform:
            - 'linear': Remove the linear least-squares fit from the data.
            - 'constant': Remove only the mean (set the mean to zero).
            Default is 'linear'.

        Returns
        -------
        NDArray[np.float64]
            The detrended data with the same shape as `timeseries`. The
            result is always returned as a NumPy array on CPU, regardless of
            whether GPU acceleration was used internally.

        Raises
        ------
        ValueError
            - If `mode` is not 'linear' or 'constant'.
            - If `indices` contains values outside the valid range [0, n_samples-1].
            - If `indices` contains negative values.

        Notes
        -----
        - For `mode='linear'`, the function uses the same algorithm as
        `scipy.signal.detrend(type='linear')`, producing numerically identical
        results for complete data (no NaN).
        - When `indices` is provided, only the specified samples are used for
        calculating the linear fit, but the detrending is applied to all
        samples (with NaN preserved at other positions).
        - The function never modifies the input array.
        - GPU acceleration is automatically used if CuPy is available and
        `FORCE_CPU=False`.

        Examples
        --------
        >>> import numpy as np
        >>> data = np.array([[1.0, 2.0, 3.0, 4.0],
        ...                  [2.0, 4.0, 6.0, 8.0]], dtype=np.float64)

        # Remove linear trend (default)
        >>> detrended = detrend(data, mode='linear')
        >>> np.allclose(detrended.mean(axis=-1), 0, atol=1e-10)
        True

        # Remove only the mean
        >>> demeaned = detrend(data, mode='constant')
        >>> np.allclose(demeaned.mean(axis=-1), 0)
        True

        # Use only specific indices for linear fit (e.g., handle NaN)
        >>> data_with_nan = np.array([[1.0, np.nan, 3.0, 4.0],
        ...                           [2.0, np.nan, 6.0, 8.0]])
        >>> valid_indices = np.array([0, 2, 3], dtype=np.int32)
        >>> detrended_nan = detrend(data_with_nan, indices=valid_indices)
        """
        check_mode(self, "mode", DetrendMode)

        if self.mode in ["constant", "c"]:
            return self._detrend_constant(timeseries)

        return self._detrend_linear(timeseries, indices)

    def _detrend_constant(
        self, timeseries: npt.ArrayLike
    ) -> npt.NDArray[np.float64]:
        timeseries = xp.asarray(timeseries, dtype=np.float64)

        result = timeseries - xp.nanmean(timeseries, self.axis, keepdims=True)

        return xp.asnumpy(result) if xp is not np else result  # type: ignore

    def _detrend_linear(
        self, timeseries: npt.ArrayLike, indices: npt.ArrayLike | None
    ) -> npt.NDArray[np.float64]:
        axis = self.axis

        timeseries = np.asarray(timeseries)

        ts_shape = timeseries.shape
        n_samples = ts_shape[axis]

        if indices is None:
            indices = np.arange(n_samples, dtype=np.int32)

        valid_indices = np.sort(np.unique(indices))

        n_valid = len(valid_indices)

        if valid_indices[-1] >= n_samples:
            raise ValueError(
                "Los índices deben ser menores que "
                "la longitud de la serie de tiempo"
            )

        if valid_indices[0] < 0:
            raise ValueError("Los índices deben ser no negativos")

        if n_valid < 2:
            return timeseries.copy()

        ts_dtype = timeseries.dtype.char

        if ts_dtype not in "dfDF":
            ts_dtype = "d"

        # Eje de referencia para el ajuste
        x_min = np.min(valid_indices)
        x_max = np.max(valid_indices)
        x = xp.arange(n_samples, dtype=ts_dtype)
        x = (x[valid_indices] - x_min + 1.0) / (x_max - x_min + 1.0)

        # Matriz de diseño para el ajuste lineal: [x, ones]
        a = xp.ones((n_valid, 2), dtype=ts_dtype)
        a[:, 0] = x

        # Reestructurar los datos para que el último eje quede como primer eje
        rank = len(ts_shape)
        if axis < 0:
            axis = axis + rank

        ts_active = (
            xp.asarray(timeseries) if xp is not np else timeseries.copy()
        )

        ts_restructured = xp.moveaxis(ts_active, axis, 0)
        tr_shape = ts_restructured.shape
        ts_restructured = ts_restructured.reshape(n_samples, -1)

        if ts_restructured.dtype.char not in "dfDF":
            ts_restructured = ts_restructured.astype(ts_dtype)

        # Valores válidos a ajustar
        y = ts_restructured[valid_indices, :]

        # Resolver mínimos cuadrados
        # coefs: (2, m) -> [pendientes, interceptos]
        # coefs, _, _, _ = xp.linalg.lstsq(a, y)
        coefs, _, _, _ = zp.linalg.lstsq(a, y)

        # Restar la tendencia
        y_detrended = y - a @ coefs

        # Colocar de vuelta en el resultado
        ts_restructured[valid_indices, :] = y_detrended

        # Disponer los datos en su forma original
        ts_restructured = ts_restructured.reshape(tr_shape)
        result = xp.moveaxis(ts_restructured, 0, axis)

        return xp.asnumpy(result) if xp is not np else result  # type: ignore
