"""
Implement cache coordination for Google Drive storage.

This module provides a wrapper that synchronises multiple cache
instances, such as those for path-to-ID mappings and directory content
listings, ensuring consistency across the caching layer.

Classes
-------
GoogleDriveCacheWrapper
    Coordinate between drive and scan cache implementations.

"""

import pathlib as pl

from .base import AbstractCache, CacheBase


type DriveCache = CacheBase[tuple[str, str]]
type ScanCache = CacheBase[list[str]]


_ID_PREFIX = "id://"


class GoogleDriveCacheWrapper(AbstractCache):
    """
    Coordinate between drive and scan cache implementations.

    Synchronise the invalidation of path-to-ID mappings and directory
    content listings across separate cache instances.

    Parameters
    ----------
    drive_cache : DriveCache
        The cache instance managing path-to-ID mappings.
    scan_cache : ScanCache
        The cache instance managing directory content listings.

    Methods
    -------
    clear()
        Remove all items from both wrapped caches.
    invalidate(path)
        Remove an entry and update related parent folder listings.
    purge()
        Trigger a purge operation on both wrapped caches.
    """

    def __init__(self, drive_cache: DriveCache, scan_cache: ScanCache) -> None:
        """Initialise the Google Drive cache wrapper."""
        self._drive_cache = drive_cache
        self._scan_cache = scan_cache

    def __repr__(self) -> str:
        """
        Return a string representation of the wrapper.

        Returns
        -------
        str
            The string representation of the object.
        """
        return (
            f"GoogleDriveCacheWrapper({self._drive_cache!r}, "
            f"{self._scan_cache!r})"
        )

    def invalidate(self, path: str) -> None:
        """
        Remove an entry and update related parent folder listings.

        Override `AbstractCache.invalidate` to ensure that removing a
        file mapping also updates its parent's directory listing.
        """
        # 1. Obtiene el ítem en caché (si existe)
        cached_item = self._drive_cache.get(path)

        if cached_item is None:
            return

        file_id, _ = cached_item

        # 2. Invalida el mapeo de ruta -> ID
        self._drive_cache.invalidate(path)

        # 3. Actualiza la caché de listados de la carpeta padre
        parent_path = str(pl.PurePosixPath(path).parent)
        cached_content = self._scan_cache.get(parent_path)

        if cached_content is None:
            return

        def get_id(uri: str) -> str:
            return uri.split("|", maxsplit=1)[0].replace(_ID_PREFIX, "")

        if indices_to_remove := [
            i for i, uri in enumerate(cached_content) if get_id(uri) == file_id
        ]:
            index_to_remove = indices_to_remove[0]
            del cached_content[index_to_remove]
            if cached_content:
                self._scan_cache.set(parent_path, cached_content)

        # 4. Invalida las cachés de la carpeta padre si es necesario
        if not cached_content:
            self._scan_cache.invalidate(parent_path)
            self._drive_cache.invalidate(parent_path)

    def clear(self) -> None:
        """
        Remove all items from both wrapped caches.

        Override `AbstractCache.clear` to reset both the drive and
        scan caches to an empty state.
        """
        self._drive_cache.clear()
        self._scan_cache.clear()

    def purge(self) -> None:
        """
        Trigger a purge operation on both wrapped caches.

        Override `AbstractCache.purge` to remove expired entries from
        both the drive and scan caches.
        """
        self._drive_cache.purge()
        self._scan_cache.purge()


__all__ = ["GoogleDriveCacheWrapper"]
