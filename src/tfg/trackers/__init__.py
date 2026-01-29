"""
Implement tropical cyclone event tracking and parsing.

This subpackage provides tools for managing hurricane tracks, including
parsing HURDAT2 records and tracking events across spatial-temporal
grids.

Modules
-------
event_track : Dataset representation for event tracks.
tracker : Main event tracking logic.
track_info : Metadata and status for individual tracks.

"""

from .event_track import EventTrackDataset
from .track_info import TrackInfo
from .tracker import EventTracker

__all__ = [
    "EventTrackDataset",
    "EventTracker",
    "TrackInfo",
]
