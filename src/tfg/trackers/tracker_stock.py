"""
Manage the registry of available trajectory data parsers.

This module provides a central registry for storm track parsers and
helper functions to validate requested dataset identifiers.

Functions
---------
validate_supported_dataset
    Verify that a dataset identifier is supported by the registry.

Symbols
-------
DEFAULT_TRACKER_ID : str
    The identifier for the default parser (HURDAT2).
track_parsers_stock : dict[str, type[TrackParser]]
    The registry mapping identifiers to parser classes.

"""

from .hurdat2 import TrackParserHurdat2
from .track_parser import TrackParser

# Registry of available track parsers.
track_parsers_stock: dict[str, type[TrackParser]] = {
    TrackParserHurdat2.ID: TrackParserHurdat2,
}

DEFAULT_TRACKER_ID = TrackParserHurdat2.ID


def validate_supported_dataset(dataset: str) -> str:
    """
    Verify that a dataset identifier is supported by the registry.

    Parameters
    ----------
    dataset : str
        The dataset identifier to validate.

    Returns
    -------
    str
        The validated dataset identifier.

    Raises
    ------
    ValueError
        If the dataset identifier is not found in the registry.
    """
    if dataset not in track_parsers_stock:
        raise ValueError(f"Dataset '{dataset}' is not supported.")

    return dataset


__all__ = [
    "DEFAULT_TRACKER_ID",
    "track_parsers_stock",
    "validate_supported_dataset",
]
