"""
Provide general utility functions and environment detection.

This module contains helpers for environment identification (e.g.
Notebook, Colab, Kaggle), array manipulation, and validation logic.

Classes
-------
ProgressTracker
    Represent a protocol for progress tracking function factories.

Functions
---------
running_on_colab
    Check if the code is running on Google Colab.
running_on_kaggle
    Check if the code is running on Kaggle.
running_on_notebook
    Check if the code is running in a Jupyter Notebook.
to_indices
    Convert a boolean mask into indices of True elements.
check_frequencies
    Validate frequency array consistency and suitability.
check_is_active
    Verify if a class instance possesses specified attributes.
check_is_fitted
    Verify if an estimator instance has been fitted.
check_mode
    Ensures an attribute value is within permitted modes.
check_timeseries
    Validate time series array structure and consistency.
format_table
    Generate formatted table lines from provided data.
format_report
    Generate a formatted report string with headers and rules.
get_columns_size
    Calculate suitable column widths for table formatting.

Symbols
-------
TOPRULE : str
    Special marker for the top boundary of a report.
MIDRULE : str
    Special marker for horizontal separators within a report.
BOTTOMRULE : str
    Special marker for the bottom boundary of a report.

"""

import collections.abc as col
import os
import pathlib
import typing as tp

import numpy as np
import numpy.typing as npt


def running_on_colab() -> bool:
    """
    Check if the code is running on Google Colab.

    Returns
    -------
    bool
        True if the execution environment is Google Colab.
    """
    return bool(os.getenv("COLAB_RELEASE_TAG"))


def running_on_kaggle() -> bool:
    """
    Check if the code is running on Kaggle.

    Returns
    -------
    bool
        True if the execution environment is Kaggle.
    """
    return (
        pathlib.Path("/kaggle/working").exists()
        or os.environ.get("KAGGLE_KERNEL_RUN_TYPE") is not None
    )


def running_on_notebook() -> bool:
    """
    Check if the code is running in a Jupyter Notebook.

    Returns
    -------
    bool
        True if the code is executed within a Jupyter notebook or
        similar interactive environment.
    """
    try:
        from IPython.core.getipython import get_ipython

        return get_ipython() is not None

    except ImportError:
        return False


def to_indices(mask: npt.NDArray[np.bool_]) -> npt.NDArray[np.intp]:
    """
    Convert a boolean mask into indices of True elements.

    Parameters
    ----------
    mask : npt.NDArray[np.bool_]
        A boolean mask array.

    Returns
    -------
    npt.NDArray[np.intp]
        An array of indices corresponding to True values in the mask.
    """
    return np.flatnonzero(mask)


def check_frequencies(frequencies: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Validate frequency array consistency and suitability.

    Parameters
    ----------
    frequencies : npt.ArrayLike
        The frequencies to validate.

    Returns
    -------
    npt.NDArray[np.float64]
        The validated frequencies as a 64-bit float array.

    Raises
    ------
    ValueError
        If the frequencies are not unidimensional, empty, contain non-
        finite values, or negative values.
    TypeError
        If the frequencies do not contain numerical float values.
    """
    # Quick validation.
    frequencies = np.asarray(frequencies, dtype=np.float64)

    if frequencies.ndim != 1:
        raise ValueError("Frequency array must be unidimensional.")

    if frequencies.size == 0:
        raise ValueError("Frequency array is empty.")

    # General data validation.
    if not np.issubdtype(frequencies.dtype, np.floating):
        raise TypeError(
            "Frequency array must contain numerical float values, "
            f"but has type '{frequencies.dtype}'."
        )

    if not np.all(np.isfinite(frequencies)):
        raise ValueError("Frequency array contains non-finite values.")

    if not np.all(frequencies >= 0):
        raise ValueError("Frequency array contains negative values.")

    return frequencies


def check_is_active(self: tp.Any, attributes: list[str]) -> bool:
    """
    Verify if a class instance possesses specified attributes.

    Parameters
    ----------
    self : tp.Any
        The instance to check.
    attributes : list[str]
        List of attribute names to verify.

    Returns
    -------
    bool
        True if all specified attributes exist on the instance.
    """
    return all(hasattr(self, attr) for attr in attributes)


def check_is_fitted(self: tp.Any, attributes: list[str]) -> None:
    """
    Verify if an estimator instance has been fitted.

    Parameters
    ----------
    self : tp.Any
        The estimator instance to check.
    attributes : list[str]
        List of attribute names that should exist after fitting.

    Raises
    ------
    ValueError
        If any of the required attributes are missing.
    """
    for attr in attributes:
        if not hasattr(self, attr):
            raise ValueError(f"Estimator has not been fitted with '{attr}'.")


def check_mode(
    self: tp.Any,
    attribute: str,
    mode: tp.Any,
    discourage_single_char: bool = True,
) -> None:
    """
    Ensures an attribute value is within permitted modes.

    Parameters
    ----------
    self : tp.Any
        The instance containing the attribute.
    attribute : str
        The name of the attribute to verify.
    mode : tp.Any
        The allowed modes for the attribute.
    discourage_single_char : bool, default=True
        If True, single-character modes are discouraged in error
        messages.

    Raises
    ------
    ValueError
        If the attribute does not exist or its value is not permitted.
    """
    if not hasattr(self, attribute):
        raise ValueError(f"Parameter '{attribute}' does not exist.")

    attribute_value = getattr(self, attribute)
    valid_modes = set(tp.get_args(mode))

    if attribute_value not in valid_modes:
        modes = sorted(valid_modes)
        if discourage_single_char:
            modes = [mode for mode in modes if len(mode) > 1]

        modes_str = "', '".join(modes)

        raise ValueError(
            f"Parameter '{attribute}' must be one of: '{modes_str}'."
        )


def check_timeseries(time_series: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """
    Validate time series array structure and consistency.

    Parameters
    ----------
    time_series : npt.ArrayLike
        The time series data to validate.

    Returns
    -------
    npt.NDArray[np.float64]
        The validated time series as a 64-bit float 2D array.

    Raises
    ------
    ValueError
        If the data is empty, has insufficient points, or inconsistent
        NaN positions.
    TypeError
        If the data does not contain numerical float values.
    """
    # Quick validation.
    time_series = np.asarray(time_series, dtype=np.float64)

    if time_series.ndim == 1:
        time_series = time_series.reshape(1, -1)

    if time_series.size == 0:
        raise ValueError("Time series array is empty.")

    # General data validation.
    n_times = time_series.shape[1]

    if n_times < 2:
        raise ValueError(
            f"Each time series must have at least 2 points. "
            f"Received: {n_times} points per series."
        )

    if not np.issubdtype(time_series.dtype, np.floating):
        raise TypeError(
            "Time series array must contain numerical float values, "
            f"but has type '{time_series.dtype}'."
        )

    # Ensure all series have NaNs in the same columns.
    nan_mask = np.isnan(time_series)
    nan_by_column = nan_mask == nan_mask[0, :]
    if not np.all(nan_by_column, axis=0).all():
        raise ValueError("Series have NaNs in non-homogeneous columns.")

    return time_series


TOPRULE = "@═"
MIDRULE = "@─"
BOTTOMRULE = "@-"


def format_table(
    size: tuple[int, int], title: str, data_lines: list[tuple[str, str, str]]
) -> list[str]:
    """
    Generate formatted table lines from provided data.

    Parameters
    ----------
    size : tuple[int, int]
        Maximum widths for the first two columns.
    title : str
        The table title.
    data_lines : list[tuple[str, str, str]]
        Data rows for the table. Each tuple contains a label, a value,
        and units.

    Returns
    -------
    list[str]
        A list of formatted strings representing the table content.
    """
    data_table = [f"{title}", MIDRULE]
    for label, value, units in data_lines:
        if not value:
            continue
        if value in {"No ajustado", "No establecido", "No montado"}:
            units = ""
        data_table.append(f"{label:<{size[0]}}:{value:>{size[1]}} {units}")

    return data_table


def format_report(header: str, data_table: list[str]) -> str:
    """
    Generate a formatted report string with headers and rules.

    Parameters
    ----------
    header : str
        The report header.
    data_table : list[str]
        The content lines of the report.

    Returns
    -------
    str
        The complete formatted report as a single string.
    """
    formatted_lines = _format_lines(header, data_table)

    return "\n".join(formatted_lines)


def _format_lines(header: str, data_table: list[str]) -> list[str]:
    """
    Format report lines by applying boundaries and rules.

    Parameters
    ----------
    header : str
        The report header.
    data_table : list[str]
        The content lines of the report.

    Returns
    -------
    list[str]
        The report lines with boundary markers resolved to correct
        length.
    """
    report_lines = [TOPRULE, header, TOPRULE] + data_table + [BOTTOMRULE]
    max_length = len(max(report_lines, key=len))

    replacements = {
        TOPRULE: TOPRULE[1] * max_length,
        MIDRULE: MIDRULE[1] * max_length,
    }

    return [replacements.get(line, line) for line in report_lines]


def get_columns_size(
    data_lines: list[tuple[str, str, str]], spacing: int = 1
) -> tuple[int, int]:
    """
    Calculate suitable column widths for table formatting.

    Parameters
    ----------
    data_lines : list[tuple[str, str, str]]
        The data rows to be displayed.
    spacing : int, default=1
        Extra padding to add to each column width.

    Returns
    -------
    tuple[int, int]
        The calculated maximum widths for the first two columns.
    """
    # Calculate column widths.
    label_length = max(len(label) for label, _, _ in data_lines) + spacing
    value_length = max(len(value) for _, value, _ in data_lines) + spacing

    return label_length, value_length


class ProgressTracker(tp.Protocol):
    """
    Represent a protocol for progress tracking function factories.

    A wrapper factory that receives a byte iterable and provides
    progress visualisation during iteration.
    """

    def __call__(
        self,
        *,
        iterable: col.Iterable[bytes],
        total_size: int,
        description: str,
    ) -> col.Iterable[bytes]:
        """
        Create a progress-tracking wrapper around a byte iterable.

        Parameters
        ----------
        iterable : col.Iterable[bytes]
            The source iterable producing byte chunks.
        total_size : int
            The total expected size in bytes of the stream.
        description : str
            A brief description to display in the progress indicator.

        Returns
        -------
        col.Iterable[bytes]
            A new iterable that yields the same bytes while updating
            progress state.
        """
        ...


__all__ = [
    "BOTTOMRULE",
    "MIDRULE",
    "ProgressTracker",
    "TOPRULE",
    "check_frequencies",
    "check_is_active",
    "check_is_fitted",
    "check_mode",
    "check_timeseries",
    "format_report",
    "format_table",
    "get_columns_size",
    "running_on_colab",
    "running_on_kaggle",
    "running_on_notebook",
    "to_indices",
]
