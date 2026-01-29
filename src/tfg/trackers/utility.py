"""
Provide formatting utilities for coordinate and time sequences.

This module contains helper functions for type conversion, primarily
translating string representations into numerical formats.

Functions
---------
str_to_float
    Convert a sequence of numeric strings to a list of floats.
iso_to_timestamp
    Convert a sequence of ISO date strings to Unix timestamps.

"""

from collections.abc import Sequence
from datetime import datetime


def str_to_float(value_strings: Sequence[str]) -> list[float]:
    """
    Convert a sequence of numeric strings to a list of floats.

    Parameters
    ----------
    value_strings : Sequence[str]
        A sequence of strings representing numeric values.

    Returns
    -------
    list[float]
        The input values converted to floating point.
    """
    return [float(value) for value in value_strings]


def iso_to_timestamp(iso_strings: Sequence[str]) -> list[float]:
    """
    Convert a sequence of ISO date strings to Unix timestamps.

    Each ISO date string is expected to follow the format
    'YYYY-MM-DDTHH[:MM[:SS]]Z'.

    Parameters
    ----------
    iso_strings : Sequence[str]
        A sequence of date strings in ISO 8601 format.

    Returns
    -------
    list[float]
        A list of numerical timestamps in seconds since the epoch.
    """
    return [
        datetime.fromisoformat(iso_string).timestamp()
        for iso_string in iso_strings
    ]


__all__ = ["iso_to_timestamp", "str_to_float"]
