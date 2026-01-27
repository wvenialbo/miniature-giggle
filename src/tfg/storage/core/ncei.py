"""
Provide interface for NOAA's NCEI Archive HTTP data sources.

This module implements a single entry point, `use_ncei_archive`, to
instantiate and configure `Datasource` instances that access National
Centers for Environmental Information (NCEI) Archive datasets via HTTP.
It handles URI mapping and automated caching, providing a seamless
interface for remote data access.

Functions
---------
use_ncei_archive(*, dataset_path, root_path=None, cache_file=None,
                 expire_after=None)
    Create a data source context for NOAA's NCEI Archive HTTP server.

"""

from pathlib import Path

import requests

from ..backend import NCEIBackend
from ..cache import TimedCache
from ..datasource import DataService, Datasource
from ..mapper import NCEIURIMapper
from .utils import calculate_mountpoint


NCEI_BASE_URL = "https://www.ncei.noaa.gov/data/"


def use_ncei_archive(
    *,
    dataset_path: str,
    root_path: str | None = None,
    cache_file: str | Path | None = None,
    expire_after: float | None = None,
) -> Datasource:
    """
    Create a data source context for NOAA's NCEI Archive HTTP server.

    Establish a data service connection to a specific dataset within the
    NOAA's National Centers for Environmental Information (NCEI) public
    archive. This service handles URL mapping, automated caching, and
    remote file retrieval using the ``requests`` library.

    Parameters
    ----------
    dataset_path : str
        The relative URL path to the specific dataset on the NCEI server
        (e.g. ``"global-hourly/access/"``).
    root_path : str | None, optional
        The directory path to use as the data root. Relative paths are
        resolved against the current working directory; absolute paths
        map directly to the corresponding location in both the local
        filesystem and the remote archive. If ``None``, the dataset path
        (`dataset_path`) is used as the root.
    cache_file : str | Path | None, optional
        The path to a JSON file for persisting directory listing caches.
        If ``None``, caching is transient or in-memory only.
    expire_after : float | None, optional
        The duration in seconds before cached entries are considered
        stale. If ``None``, entries might never expire.

    Returns
    -------
    Datasource
        The initialised data service configured for the specified NCEI
        archive.

    Notes
    -----
    This service maintains a symmetric mapping: the provided `root_path`
    resolves to identical relative or absolute locations in both the
    local filesystem and the remote environment. Path resolution
    follows the mapping logic implemented in `calculate_mountpoint`.

    References
    ----------
    National Oceanic and Atmospheric Administration (NOAA):
        https://www.noaa.gov/
    National Centers for Environmental Information (NCEI):
        https://www.ncei.noaa.gov/

    Examples
    --------
    Initialise a data source for the Global Historical Climatology
    Network:

    >>> from tfg.storage import use_ncei_archive
    >>> datasource = use_ncei_archive(
    ...     dataset_path="ghcnd/daily",
    ...     root_path="./data/weather",
    ...     expire_after=3600.0,
    ... )  # doctest: +SKIP
    """
    root_url = NCEI_BASE_URL.rstrip("/")
    dataset_path = dataset_path.lstrip("/")
    base_url = f"{root_url}/{dataset_path}"

    mountpoint = calculate_mountpoint(root_path=root_path)

    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedCache[list[str]](
        cache_file=cache_path_str, expire_after=expire_after
    )

    session = requests.Session()

    mapper = NCEIURIMapper(base_url=base_url)
    backend = NCEIBackend(session=session, scan_cache=scan_cache)

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )


__all__ = ["use_ncei_archive"]
