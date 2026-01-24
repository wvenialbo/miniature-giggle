"""
Provide local filesystem storage helpers.

This module offers utilities to configure and create data sources based
on the local file system.

Functions
---------
use_local_drive(root_path)
    Create a data source context for the local filesystem.
"""

from ..backend import FilesystemBackend
from ..datasource import DataService, Datasource
from ..mapper import PathURIMapper
from .utils import calculate_mountpoint


def use_local_drive(*, root_path: str | None = None) -> Datasource:
    r"""
    Create a data source context for the local filesystem.

    Parameters
    ----------
    root_path : str | None
        The root path within the local filesystem for the context. If
        ``None``, the system root is used (e.g., "/" on Unix, "C:\" on
        Windows).

    Returns
    -------
    Datasource
        The configured data source context ready for use.
    """
    mountpoint = calculate_mountpoint(root_path=root_path)

    mapper = PathURIMapper()
    backend = FilesystemBackend()

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
    )


__all__ = ["use_local_drive"]
