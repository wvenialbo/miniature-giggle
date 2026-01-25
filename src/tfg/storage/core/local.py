"""
Provide interface for local filesystem storage data sources.

This module implements a single entry point, `use_local_drive`, to
instantiate and configure `Datasource` instances that access local
disk resources. It maps the local filesystem into a standardized
interface, providing consistent file access across storage backends.

Functions
---------
use_local_drive(*, root_path=None)
    Create a data source context for the local filesystem.

"""

from ..backend import FilesystemBackend
from ..datasource import DataService, Datasource
from ..mapper import PathURIMapper
from .utils import calculate_mountpoint


def use_local_drive(*, root_path: str | None = None) -> Datasource:
    r"""
    Create a data source context for the local filesystem.

    Establish a data service connection to the local machine's storage.
    This service maps local paths into the standardized datasource
    abstraction, allowing local files to be treated identically to
    remote resources.

    Parameters
    ----------
    root_path : str | None, optional
        The root path within the local filesystem for the context. If
        ``None``, the system root is used (e.g., "/" on Unix, "C:\" on
        Windows).

    Returns
    -------
    Datasource
        The initialized data service configured for local access.

    Examples
    --------
    >>> service = use_local_drive(root_path="./data")
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
