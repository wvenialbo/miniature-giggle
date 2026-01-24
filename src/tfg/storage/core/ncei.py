"""
Configure dataset access for NCEI.

This module provides high-level configuration helpers to establish
connections to NCEI HTTP archives. It orchestrates the backend,
caching, and mapping components required to traverse and download
data from NCEI's public servers.

Functions
---------
use_ncei_archive(*, dataset_path, root_path=None, cache_file=None,
                 expire_after=None)
    Configure access to a remote NCEI dataset via HTTP.
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
    Configure access to a remote NCEI dataset via HTTP.

    Establish a data service connection to a specific dataset within
    the NCEI public archive. This service handles URL mapping, local
    specific caching, and remote file retrieval using a reliable HTTP
    backend.

    Parameters
    ----------
    dataset_path : str
        The relative URL path to the specific dataset on the NCEI
        server. For example, 'global-hourly/access/'.
    root_path : str | None, optional
        The local directory path to use as the root for downloaded
        files. If ``None``, a default location is determined by the
        system.
    cache_file : str | Path | None, optional
        The path to a file for persisting calculation or listing
        caches. If ``None``, caching may be transient or in-memory
        only.
    expire_after : float | None, optional
        The duration in seconds before cached entries are considered
        stale. If ``None``, entries might never expire or use a
        default policy.

    Returns
    -------
    Datasource
        The initialized data service configured for the specified NCEI
        archive.

    Examples
    --------
    >>> service = use_ncei_archive(
    ...     dataset_path="ghcnd/daily",
    ...     root_path="./data/weather",
    ...     expire_after=3600.0,
    ... )
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
