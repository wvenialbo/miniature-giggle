"""
Implement dataset management for tropical cyclone tracks.

This module provides the `EventTrackDataset` class, which serves as a
high-level interface for accessing storm tracks from various data
sources (e.g. HURDAT2).

Classes
-------
EventTrackDataset
    Represent a collection of storm tracks from a specific source.

"""

from pathlib import Path

from .track_info import TrackInfo
from .tracker_stock import (
    DEFAULT_TRACKER_ID,
    track_parsers_stock,
    validate_supported_dataset,
)
from .validation import validate_dataset_file


class EventTrackDataset:
    """
    Represent a collection of storm tracks from a specific source.

    This class coordinates file validation and parser selection to
    retrieve specific cyclone trajectories from a dataset file.

    Parameters
    ----------
    path : str | Path
        The filesystem path to the dataset file.
    dataset : str, default=DEFAULT_TRACKER_ID
        The identifier for the dataset format/source.

    Attributes
    ----------
    dataset : str
        The validated dataset identifier.
    path : str | Path
        The validated path to the source data.
    """

    def __init__(
        self, path: str | Path, dataset: str = DEFAULT_TRACKER_ID
    ) -> None:
        """Initialise the event track dataset."""
        dataset_id = validate_supported_dataset(dataset)
        path_obj = validate_dataset_file(path)

        self.dataset = dataset_id
        self.path = path_obj

    def get_track(self, event: str, year: int) -> TrackInfo:
        """
        Retrieve a specific storm track from the dataset.

        Parameters
        ----------
        event : str
            The name of the storm.
        year : int
            The year of the storm.

        Returns
        -------
        TrackInfo
            The trajectory and metadata for the requested event.

        Raises
        ------
        ValueError
            If the tracker for the specified dataset is not implemented.
        """
        try:
            tracker_class = track_parsers_stock[self.dataset]
        except KeyError as error:
            raise ValueError(
                f"Tracker for '{self.dataset}' is not implemented."
            ) from error
        tracker = tracker_class(self.path)
        return tracker.get_track(event, year)


__all__ = ["EventTrackDataset"]
