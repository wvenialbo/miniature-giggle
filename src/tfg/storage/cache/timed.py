"""
Implement a timed cache with optional disk persistence.

This module provides a thread-safe caching mechanism that supports
in-memory storage and optional serialisation to a JSON file. Cached
items include a creation timestamp to manage expiration based on a
defined life time.

Classes
-------
CacheItem
    Represent a cached data item and its creation timestamp.
RawCacheItem
    Represent the raw dictionary structure of a cached item.
TimedCache
    Manage a simple in-memory cache with optional disk persistence.

"""

import contextlib
import dataclasses as dc
import json
import pathlib as pl
import threading as th
import time
from typing import TypedDict

from .base import CacheBase


@dc.dataclass(frozen=True)
class CacheItem[T]:
    """
    Represent a cached data item and its creation timestamp.

    Attributes
    ----------
    data : T
        The cached data item.
    created_at : float
        The Unix timestamp indicating when the item was added to the
        cache.
    """

    data: T
    created_at: float


class RawCacheItem[T](TypedDict):
    """
    Represent the raw dictionary structure of a cached item.

    This structure is used for serialisation and de-serialisation of
    cache items when persisting to or loading from disk.

    Attributes
    ----------
    data : T
        The cached data item.
    created_at : float
        The Unix timestamp indicating when the item was added to the
        cache.
    """

    data: T
    created_at: float


class TimedCache[T](CacheBase[T]):
    """
    Manage a simple in-memory cache with optional disk persistence.

    This implementation maintains data in a dictionary for fast access,
    optionally persisting state to a JSON file. Items are removed
    automatically upon retrieval if they have expired, or manually via
    the `purge` method.

    Parameters
    ----------
    cache_file : str, optional
        The path to the file where the cache is stored on disk.
    expire_after : float, optional
        The life time in seconds for each item in the cache.

    Attributes
    ----------
    life_time : float
        The duration in seconds before an item is considered expired.
    cache_file : Path, optional
        The path to the on-disk cache file.
    cache : dict[str, CacheItem[T]]
        The internal dictionary holding cached items and timestamps.

    Methods
    -------
    clear()
        Remove all objects from the memory and disk cache.
    get(path)
        Retrieve an object from the cache, removing it if expired.
    invalidate(path)
        Remove an object from the cache and update the disk state.
    purge()
        Remove expired entries according to the defined life time.
    set(path, data)
        Store an object in the cache with the current timestamp.

    Notes
    -----
    Items are considered expired if the current time exceeds the sum
    of the creation timestamp and the defined life time. Automatic
    cleanup of expired entries occurs during retrieval; no background
    process is used for real-time maintenance.

    This class is thread-safe, using an internal lock to synchronise
    concurrent access to the cache and its persistent state.
    """

    def __init__(
        self, cache_file: str | None = None, expire_after: float | None = None
    ) -> None:
        """
        Initialise the timed cache.

        Calculate the effective life time and load any existing state
        from the disk cache if a path is provided.
        """
        self.life_time: float = (
            float("+inf") if expire_after is None else expire_after
        )
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, CacheItem[T]] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def __repr__(self) -> str:
        """
        Return a string representation of the cache.

        Returns
        -------
        str
            A string representation of the cache instance.
        """
        return (
            f"TimedCache(cache_file='{self.cache_file}', "
            f"expire_after={self.life_time:.2f})"
        )

    def clear(self) -> None:
        """
        Remove all objects from the memory and disk cache.

        Override `AbstractCache.clear` to ensure the persistent state
        is also cleared.
        """
        with self._lock:
            self.cache.clear()
            self._save_to_disk()

    def invalidate(self, path: str) -> None:
        """
        Remove an object from the cache and update the disk state.

        Override `AbstractCache.invalidate` to synchronise the deletion
        with the persistent storage.
        """
        with self._lock:
            if path in self.cache:
                self._remove_item(path)

    def purge(self) -> None:
        """
        Remove expired entries according to the defined life time.

        Override `AbstractCache.purge` to filter the internal dictionary
        and update the disk cache.
        """
        with self._lock:
            current_time = time.time()
            keys_to_remove = [
                key
                for key, item in self.cache.items()
                if current_time >= item.created_at + self.life_time
            ]
            for key in keys_to_remove:
                self.cache.pop(key, None)
            if keys_to_remove:
                self._save_to_disk()

    def get(self, path: str) -> T | None:
        """
        Retrieve an object from the cache, removing it if expired.

        Override `CacheBase.get` to implement lazy expiration during
        the retrieval process.

        Returns
        -------
        T | None
            The cached data item if found and not expired, otherwise
            ``None``.
        """
        with self._lock:
            item = self.cache.get(path, None)
            if item is None:
                return None

            expire_time: float = item.created_at + self.life_time
            current_time: float = time.time()
            if expire_time >= current_time:
                return item.data

            self._remove_item(path)
            return None

    def set(self, path: str, data: T) -> None:
        """
        Store an object in the cache with the current timestamp.

        Override `CacheBase.set` to record the creation time and commit
        the change to disk.
        """
        with self._lock:
            self.cache[path] = CacheItem[T](data=data, created_at=time.time())
            self._save_to_disk()

    def _load_from_disk(self) -> None:
        """Load the cache state from the JSON file on disk."""
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            raw_cache: dict[str, RawCacheItem[T]] = json.loads(content)
            self.cache = {
                key: CacheItem[T](**value) for key, value in raw_cache.items()
            }
        except (OSError, json.JSONDecodeError, KeyError):
            # Si falla la carga, iniciamos con caché vacío por seguridad
            self.cache = {}

    def _save_to_disk(self) -> None:
        """Save the current cache state to the JSON file on disk."""
        if not self.cache_file:
            return

        with contextlib.suppress(IOError):
            serializable_cache = {
                key: {"data": item.data, "created_at": item.created_at}
                for key, item in self.cache.items()
            }
            content = json.dumps(serializable_cache, indent=2)
            self.cache_file.write_text(content, encoding="utf-8")

    def _remove_item(self, path: str) -> None:
        """Delete an item from the cache and persist the change."""
        self.cache.pop(path, None)
        self._save_to_disk()


__all__ = ["CacheItem", "TimedCache"]
