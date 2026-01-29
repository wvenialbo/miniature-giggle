"""
Represent metadata and trajectory information for tropical cyclones.

This module provides the `TrackInfo` class, which stores event
identifiers and coordinate trajectories (temporal and spatial).

Classes
-------
TrackInfo
    Store metadata and trajectory data for a tropical cyclone.

"""

from collections.abc import Sequence
from typing import cast, overload

from .utility import iso_to_timestamp


class TrackInfo:
    """
    Store metadata and trajectory data for a tropical cyclone.

    This class maintains identifying information (name, year, etc.)
    and the physical coordinates (time, latitude, longitude) of a
    storm's path.

    Parameters
    ----------
    name : str
        The storm name (e.g. "KATRINA").
    year : int
        The year of the event.
    sector : str
        The oceanic sector (e.g. "AL" for Atlantic).
    number : int
        The storm number within its season.
    nlines : int
        The number of data records in the source track.

    Attributes
    ----------
    timestamps : Sequence[float]
        The trajectory timestamps in seconds since the epoch.
    latitudes : Sequence[float]
        The latitude coordinates of the track.
    longitudes : Sequence[float]
        The longitude coordinates of the track.
    name : str
        The storm identifier.
    year : int
        The season year.
    sector : str
        The regional basin identifier.
    number : int
        The seasonal sequence number.
    nlines : int
        The total count of trajectory points.
    """

    timestamps: Sequence[float]
    latitudes: Sequence[float]
    longitudes: Sequence[float]

    name: str
    year: int
    sector: str
    number: int
    nlines: int

    def __init__(
        self, name: str, year: int, sector: str, number: int, nlines: int
    ) -> None:
        """Initialise track metadata."""
        self.name = name
        self.year = year
        self.sector = sector
        self.number = number
        self.nlines = nlines

        self.timestamps = ()
        self.latitudes = ()
        self.longitudes = ()

    @overload
    def set_track_data(
        self,
        timestamps: Sequence[float],
        latitudes: Sequence[float],
        longitudes: Sequence[float],
    ) -> None:
        """
        Set the track data using numerical timestamps.

        Parameters
        ----------
        timestamps : Sequence[float]
            The trajectory timestamps.
        latitudes : Sequence[float]
            The latitude coordinates.
        longitudes : Sequence[float]
            The longitude coordinates.
        """

    @overload
    def set_track_data(
        self,
        timestamps: Sequence[str],
        latitudes: Sequence[float],
        longitudes: Sequence[float],
    ) -> None:
        """
        Set the track data using ISO strings.

        Parameters
        ----------
        timestamps : Sequence[str]
            The trajectory timestamps in ISO 8601 format.
        latitudes : Sequence[float]
            The latitude coordinates.
        longitudes : Sequence[float]
            The longitude coordinates.
        """

    def set_track_data(
        self,
        timestamps: Sequence[float] | Sequence[str],
        latitudes: Sequence[float],
        longitudes: Sequence[float],
    ) -> None:
        """
        Set the trajectory coordinates for the event.

        Parameters
        ----------
        timestamps : Sequence[float] | Sequence[str]
            The trajectory timestamps (as floats or ISO strings).
        latitudes : Sequence[float]
            The latitude coordinates.
        longitudes : Sequence[float]
            The longitude coordinates.

        Raises
        ------
        ValueError
            If any sequence is empty or if lengths are inconsistent.
        """
        if not timestamps:
            raise ValueError("`timestamps` cannot be empty.")
        if not latitudes:
            raise ValueError("`latitudes` cannot be empty.")
        if not longitudes:
            raise ValueError("`longitudes` cannot be empty.")

        same_length_latitudes = len(timestamps) == len(latitudes)
        same_length_longitudes = len(timestamps) == len(longitudes)

        if not same_length_latitudes or not same_length_longitudes:
            raise ValueError(
                "The lengths of `timestamps`, `latitudes`, "
                "and `longitudes` must be the same."
            )

        if isinstance(timestamps[0], str):
            timestamps_str = cast(Sequence[str], timestamps)
            self.timestamps = iso_to_timestamp(timestamps_str)
        else:
            self.timestamps = cast(Sequence[float], timestamps)

        self.latitudes = latitudes
        self.longitudes = longitudes


__all__ = ["TrackInfo"]
