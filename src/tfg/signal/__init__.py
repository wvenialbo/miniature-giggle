"""
Implement signal processing algorithms and utilities.

This subpackage provides tools for signal enhancement, including
detrending and envelope-based normalisation.

Modules
-------
detrend : Signal detrending implementations.
normalize : Signal normalisation utilities.

"""

from .detrend import SignalDetrender
from .normalize import normalize_by_envelope

__all__ = ["SignalDetrender", "normalize_by_envelope"]
