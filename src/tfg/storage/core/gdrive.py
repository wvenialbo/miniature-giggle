"""
Configure dataset access for Google Drive.

This module provides high-level configuration helpers to establish
connections to Google Drive folders. It orchestrates the backend,
caching, mapping, and authentication components required to traverse
and download file from Google Drive.

Functions
---------
use_google_drive(*, root_path=None, credentials=None, cache_file=None,
                 expire_after=None)
    Configure access to a Google Drive folder via API.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from ..backend import GoogleDriveBackend
from ..cache import GoogleDriveCacheWrapper, TimedCache
from ..datasource import DataService, Datasource
from ..mapper import GoogleDriveURIMapper
from .gdauth import get_gdrive_client
from .utils import calculate_mountpoint


if TYPE_CHECKING:
    from google.auth.credentials import Credentials


def use_google_drive(
    *,
    root_path: str | None = None,
    credentials: "Credentials | None" = None,
    cache_file: str | Path | None = None,
    expire_after: float | None = None,
) -> Datasource:
    """
    Configure access to a Google Drive folder via API.

    Establish a data service connection to a Google Drive account. This
    service handles file ID mapping, dual-strategy caching (ID and
    listing), and file retrieval using the authenticated Google Drive
    API backend.

    Parameters
    ----------
    root_path : str | None, optional
        The local directory path to use as the root for downloaded
        files. If ``None``, a default location is determined by the
        system.
    credentials : Credentials | None, optional
        The Google OAuth2 credentials to use for authentication. If
        ``None``, the system attempts to find default application
        credentials or initiates an interactive login flow.
    cache_file : str | Path | None, optional
        The base path to a file for persisting caches. This path is
        split into two separate files (suffixed with ``-id`` and
        ``-index``) to store ID mappings and directory listings
        independently. If ``None``, caching is transient.
    expire_after : float | None, optional
        The duration in seconds before cached entries are considered
        stale. If ``None``, entries might never expire.

    Returns
    -------
    Datasource
        The initialized data service configured for Google Drive access.

    Examples
    --------
    >>> creds = get_credentials()
    >>> service = use_google_drive(
    ...     root_path="./data/gdrive",
    ...     credentials=creds,
    ...     cache_file="./cache/gdrive.pkl",
    ... )
    """
    mountpoint = calculate_mountpoint(root_path=root_path)

    def path_str(path: Path, suffix: str) -> str | None:
        return str(path.with_name(f"{path.stem}{suffix}{path.suffix}"))

    drive_path: str | None = None
    scan_path: str | None = None

    if cache_file is not None:
        # Split the single cache path to maintain separate persistent
        # stores for file-id mapping and for directory listings.
        cache_file = Path(cache_file)
        drive_path = path_str(cache_file, "-id")
        scan_path = path_str(cache_file, "-index")

    drive_cache = TimedCache[tuple[str, str]](
        cache_file=drive_path, expire_after=expire_after
    )
    scan_cache = TimedCache[list[str]](
        cache_file=scan_path, expire_after=expire_after
    )
    gdrive_cache = GoogleDriveCacheWrapper(
        drive_cache=drive_cache, scan_cache=scan_cache
    )

    service = get_gdrive_client(credentials)

    mapper = GoogleDriveURIMapper(service=service, drive_cache=drive_cache)
    backend = GoogleDriveBackend(
        service=service, drive_cache=drive_cache, scan_cache=scan_cache
    )

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=gdrive_cache,
    )


__all__ = ["use_google_drive"]
