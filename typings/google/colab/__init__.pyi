# Copyright 2017 Google Inc.
"""Colab Python APIs."""

from typing import Any

from . import auth as auth
from . import drive as drive
from . import files as files

__all__ = [
    "auth",
    "drive",
    "files",
]

__version__: str = "0.0.1a2"

def _jupyter_nbextension_paths() -> list[dict[str, str]]:
    """Inferred from list of dict returning resources path."""
    ...

def _jupyter_server_extension_points() -> list[dict[str, str]]:
    """Inferred from static module mapping."""
    ...

def load_jupyter_server_extension(server_app: Any) -> None:
    """
    Called by Jupyter server to handle static file requests.
    Args:
        server_app: Jupyter server application instance.
    """
    ...

def load_ipython_extension(ipython: Any) -> None:
    """
    Called by IPython when this module is loaded.
    Args:
        ipython: The interactive shell instance.
    """
    ...
