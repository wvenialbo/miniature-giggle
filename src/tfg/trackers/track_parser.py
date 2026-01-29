"""
Define the protocol for trajectory data parsers.

This module provides the `TrackParser` protocol, which standardises the
interface for classes that extract storm trajectory data from various
file formats.

Classes
-------
TrackParser
    Protocol for storm trajectory data extractors.

"""

from pathlib import Path
from typing import Protocol

from .track_info import TrackInfo


class TrackParser(Protocol):
    """
    Protocol for storm trajectory data extractors.

    Implementations of this protocol are responsible for parsing
    specific file formats and returning standard `TrackInfo` objects.

    Attributes
    ----------
    ID : str
        The unique identifier for the parser type/source.
    """

    ID: str

    def __init__(self, path: Path) -> None:
        """Initialise the parser with a source path."""
        ...

    def get_track(self, event: str, year: int) -> TrackInfo:
        """
        Extract track information for a specific storm and year.

        Parameters
        ----------
        event : str
            The name or identifier of the storm event.
        year : int
            The season year.

        Returns
        -------
        TrackInfo
            The coordinates and metadata for the requested event.
        """
        ...


__all__ = ["TrackParser"]
