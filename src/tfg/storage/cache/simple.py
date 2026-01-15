import contextlib
import json
import pathlib as pl
import threading as th
import typing as tp

from .base import CacheBase

T = tp.TypeVar("T")


class SimpleCache(CacheBase[T]):

    def __init__(self, cache_file: str | None = None) -> None:
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, T] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def get(self, path: str) -> T | None:
        with self._lock:
            return self.cache.get(path, None)

    def set(self, path: str, data: T) -> None:
        with self._lock:
            self.cache[path] = data
            self._save_to_disk()

    def remove(self, path: str) -> None:
        with self._lock:
            if path in self.cache:
                self.cache.pop(path, None)
                self._save_to_disk()

    def clear(self) -> None:
        with self._lock:
            self.cache.clear()
            self._save_to_disk()

    def purge(self) -> None:
        # SimpleCache no tiene expiración, por lo que purge no hace nada.
        pass

    def _load_from_disk(self) -> None:
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            self.cache = json.loads(content)
        except (IOError, json.JSONDecodeError):
            # Si falla la carga, iniciamos con caché vacío por seguridad
            self.cache = {}

    def _save_to_disk(self) -> None:
        if not self.cache_file:
            return

        with contextlib.suppress(IOError):
            # Escribe de forma atómica (idealmente)
            content = json.dumps(self.cache, indent=2)
            self.cache_file.write_text(content, encoding="utf-8")


NamesCache = SimpleCache[str]
InventoryCache = SimpleCache[list[str]]

__all__ = ["InventoryCache", "NamesCache", "SimpleCache"]
