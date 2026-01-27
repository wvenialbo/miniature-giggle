"""
Provide interface for Google Cloud Storage (GCS) data sources.

This module implements a single entry point, `use_gcs_cloud`, to
initialise and configure `Datasource` instances that access Google
Cloud Storage buckets. It handles credential resolution for both
authenticated and anonymous (public bucket) access modes, providing a
seamless interface for remote data access.

Functions
---------
use_gcs_cloud(*, bucket, root_path=None, cache_file=None,
              expire_after=None, **kwargs)
    Create a data source context for a Google Cloud Storage bucket.

Classes
-------
GCSClientArgs
    Define client and session parameters for GCS authentication.

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
    Define client and session parameters for GCS authentication.

    Attributes
    ----------
    project : str | None, optional
        The Google Cloud project ID.
    credentials : Credentials | None, optional
        Explicit ``google-auth`` credentials for authentication.
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

    Establish a data service connection to a specific GCS bucket. This
    service handles key mapping, local caching for listings, and file
    retrieval using the ``google-cloud-storage`` library.

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket to access (e.g.
        ``"gcp-public-data-goes-16"``).
    root_path : str | None, optional
        The directory path to use as the data root. Relative paths
        are resolved against the current working directory; absolute
        paths map directly to the corresponding location in both the
        local filesystem and the cloud storage bucket. If ``None``, the
        bucket is used as the root.
    cache_file : str | Path | None, optional
        The path to a file for persisting directory listing caches.
        If ``None``, caching is transient or in-memory only.
    expire_after : float | None, optional
        The duration in seconds before cached entries are considered
        stale. If ``None``, entries might never expire.
    **kwargs : Unpack[GCSClientArgs]
        Additional arguments for the GCS client, including project,
        credentials, and other session parameters.

    Returns
    -------
    Datasource
        The initialised data service configured for the specified GCS
        bucket.

    Notes
    -----
    This service maintains a symmetric mapping: the provided `root_path`
    resolves to identical relative or absolute locations in both the
    local filesystem and the cloud storage environment. Path
    resolution follows the symmetric mapping logic implemented in
    `calculate_mountpoint`.

    Examples
    --------
    Initialise a data source for a public GOES-16 satellite imagery
    bucket:

    >>> from tfg.storage import use_gcs_cloud
    >>> datasource = use_gcs_cloud(
    ...     bucket="gcp-public-data-goes-16",
    ...     expire_after=3600.0,
    ... )  # doctest: +SKIP
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
