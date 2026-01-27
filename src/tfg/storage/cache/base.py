"""
Define protocols for data storage cache implementations.

This module provides the structural contracts for caching mechanisms
used within the storage layer. It includes a base protocol for general
cache management and a generic protocol for typed item storage.

Classes
-------
AbstractCache
    Represent the base protocol for data storage caches.
CacheBase
    Represent a protocol for data storage caches.

"""

from typing import Protocol


class AbstractCache(Protocol):
    """
    Represent the base protocol for data storage caches.

    Define the minimum interface that must be implemented by any
    data storage cache.

    Methods
    -------
    clear()
        Remove all objects from the cache.
    invalidate(path)
        Remove an object from the cache using the specified path.
    purge()
        Remove expired entries from the cache.
    """

    def clear(self) -> None:
        """
        Remove all objects from the cache.

        This operation deletes every object currently stored in the
        cache.
        """
        ...

    def invalidate(self, path: str) -> None:
        """
        Remove an object from the cache using the specified path.

        Parameters
        ----------
        path : str
            The path of the object to be removed from the cache.
        """
        ...

    def purge(self) -> None:
        """
        Remove expired entries from the cache.

        Implementations may define expiration policies for stored
        objects, e.g. a maximum time-to-live. This method deletes all
        objects that have expired according to those policies.
        """
        ...


class CacheBase[T](AbstractCache):
    """
    Represent a protocol for data storage caches.

    Define the interface for caches that store data in memory or local
    storage to accelerate read and write operations on remote backends.
    It extends `AbstractCache` by adding methods to retrieve and store
    objects.

    Methods
    -------
    get(path)
        Retrieve an object from the cache using the specified path.
    set(path, data)
        Store an object in the cache under the specified path.
    """

    def get(self, path: str) -> T | None:
        """
        Retrieve an object from the cache using the specified path.

        Parameters
        ----------
        path : str
            The path of the object to retrieve.

        Returns
        -------
        T | None
            The object stored in the cache under the given path, or
            ``None`` if it does not exist.
        """
        ...

    def set(self, path: str, data: T) -> None:
        """
        Store an object in the cache under the specified path.

        Parameters
        ----------
        path : str
            The path under which to store the object.
        data : T
            The object to be stored in the cache.
        """
        ...


__all__ = ["AbstractCache", "CacheBase"]
