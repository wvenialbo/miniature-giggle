"""
Provide progress tracking implementations.

This module contains concrete implementations of the `ProgressTracker`
protocol, primarily using the `tqdm` library for visualisation.

Functions
---------
tqdm_progress
    Create a tqdm-based progress tracker for byte iterables.

"""

import collections.abc as col

import tqdm.auto


def tqdm_progress(
    *,
    iterable: col.Iterable[bytes],
    total_size: int,
    description: str | None = None,
) -> col.Iterable[bytes]:
    """
    Create a tqdm-based progress tracker for byte iterables.

    This function wraps an iterable with a tqdm progress bar, scaling
    units to bytes for clear visualisation of data transfers.

    Parameters
    ----------
    iterable : col.Iterable[bytes]
        The source byte iterable to track.
    total_size : int
        The total expected number of bytes.
    description : str, optional
        A message to display alongside the progress bar.

    Returns
    -------
    col.Iterable[bytes]
        A tqdm-wrapped iterable.
    """
    return tqdm.auto.tqdm(
        iterable,
        total=total_size,
        unit="B",
        unit_scale=True,
        desc=description,
        leave=True,
    )


__all__ = ["tqdm_progress"]
