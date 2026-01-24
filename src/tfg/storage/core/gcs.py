"""
Provide Google Cloud Storage (GCS) backend helpers.

This module contains utilities to configure and create data sources
backed by Google Cloud Storage buckets.

Functions
---------
use_gcs_cloud(*, bucket, root_path=None, cache_file=None,
              expire_after=None, **kwargs)
    Create a data source context for a Google Cloud Storage bucket.

Classes
-------
GCSClientArgs
    Define configuration arguments for GCS data sources.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Unpack

from ..backend import GCSBackend
from ..cache import TimedCache
from ..datasource import DataService, Datasource
from ..mapper import GCSURIMapper
from .gcsauth import GCSAuthArgs, get_gcs_client
from .utils import calculate_mountpoint


if TYPE_CHECKING:
    from google.auth.credentials import Credentials


class GCSClientArgs(GCSAuthArgs):
    """
    Define configuration arguments for GCS data sources.

    Attributes
    ----------
    project : str | None
        The Google Cloud project ID.
    credentials : Credentials | None
        Explicit credentials for authentication.
    """

    project: str | None
    credentials: "Credentials | None"


def use_gcs_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    cache_file: str | Path | None = None,
    expire_after: float | None = None,
    **kwargs: Unpack[GCSClientArgs],
) -> Datasource:
    """
    Create a data source context for a Google Cloud Storage bucket.

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket.
    root_path : str | None
        The root path within the virtual mountpoint. If ``None``, the
        system root is used.
    cache_file : str | pathlib.Path | None
        Path to the cache file.
    expire_after : float | None
        Time in seconds before cache entries expire.
    **kwargs : Unpack[GCSClientArgs]
        Additional authentication arguments (e.g., project,
        credentials).

    Returns
    -------
    Datasource
        The configured data source context ready for use.
    """
    mountpoint = calculate_mountpoint(root_path=root_path)

    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedCache[list[str]](
        cache_file=cache_path_str, expire_after=expire_after
    )

    client = get_gcs_client(bucket=bucket, **kwargs)

    mapper = GCSURIMapper(bucket=bucket)
    backend = GCSBackend(bucket=bucket, client=client, scan_cache=scan_cache)

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )


__all__ = ["use_gcs_cloud"]
