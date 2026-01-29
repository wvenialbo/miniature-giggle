"""
Implement interpolation logic for tropical cyclone trajectories.

This module provides the `EventTracker` class, which allows retrieving
coordinates for any given timestamp along a storm's track through
linear interpolation and extrapolation.

Classes
-------
EventTracker
    Handle coordinate retrieval and interpolation for cyclone tracks.

"""

from numpy import array, float64, interp

from ..utils.array import ArrayFloat64
from .track_info import TrackInfo


class EventTracker:
    """
    Handle coordinate retrieval and interpolation for cyclone tracks.

    This class wraps a `TrackInfo` object and provides methods to
    calculate the storm's position at any point in time using linear
    regression between known trajectory points.

    Parameters
    ----------
    track_info : TrackInfo
        The storm metadata and known coordinate sequences.

    Attributes
    ----------
    timestamps : ArrayFloat64
        The numerical timestamps of the track points.
    latitudes : ArrayFloat64
        The latitude coordinates of the track.
    longitudes : ArrayFloat64
        The longitude coordinates of the track.
    track_info : TrackInfo
        The source trajectory information.
    """

    timestamps: ArrayFloat64
    latitudes: ArrayFloat64
    longitudes: ArrayFloat64

    track_info: TrackInfo

    def __init__(self, track_info: TrackInfo) -> None:
        """Initialise the tracker with trajectory data."""
        self.track_info = track_info

        # Convert to NumPy arrays.
        self.timestamps = array(track_info.timestamps, dtype=float64)
        self.latitudes = array(track_info.latitudes, dtype=float64)
        self.longitudes = array(track_info.longitudes, dtype=float64)

    def get(self, t: float) -> tuple[float, float]:
        """
        Retrieve the interpolated coordinates for a given timestamp.

        If the timestamp falls between known points, linear interpolation
        is used. If it falls outside the recorded range, linear
        extrapolation is performed using the nearest edge interval.

        Parameters
        ----------
        t : float
            The target timestamp for coordinate retrieval.

        Returns
        -------
        tuple[float, float]
            The interpolated longitude and latitude respectively.
        """
        return self._interpolate_coordinates(
            t, self.timestamps, self.longitudes, self.latitudes
        )

    @staticmethod
    def _interpolate_value(
        x: float, xp: ArrayFloat64, fp: ArrayFloat64
    ) -> float:
        """
        Perform linear interpolation or extrapolation.

        Parameters
        ----------
        x : float
            The target x-coordinate.
        xp : ArrayFloat64
            The reference x-coordinates.
        fp : ArrayFloat64
            The reference values.

        Returns
        -------
        float
            The estimated value.
        """
        if x < xp[0]:
            # Linear extrapolation to the left.
            slope = (fp[1] - fp[0]) / (xp[1] - xp[0])
            return float(fp[0] + slope * (x - xp[0]))

        if x > xp[-1]:
            # Linear extrapolation to the right.
            slope = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
            return float(fp[-1] + slope * (x - xp[-1]))

        # Interpolation within the domain.
        return float(interp(x, xp, fp))

    @classmethod
    def _interpolate_coordinates(
        cls,
        t: float,
        timestamps: ArrayFloat64,
        longitudes: ArrayFloat64,
        latitudes: ArrayFloat64,
    ) -> tuple[float, float]:
        """
        Calculate both spatial coordinates for a given time.

        Parameters
        ----------
        t : float
            The target timestamp.
        timestamps : ArrayFloat64
            The reference timestamps.
        longitudes : ArrayFloat64
            The reference longitude values.
        latitudes : ArrayFloat64
            The reference latitude values.

        Returns
        -------
        tuple[float, float]
            The estimated longitude and latitude.
        """
        # Interpolate or extrapolate for the given timestamp.
        lon_interp = cls._interpolate_value(t, timestamps, longitudes)
        lat_interp = cls._interpolate_value(t, timestamps, latitudes)

        return lon_interp, lat_interp


__all__ = ["EventTracker"]
