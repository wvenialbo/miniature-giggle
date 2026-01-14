import contextlib
import dataclasses as dc
import json
import pathlib as pl
import threading as th
import time
import typing as tp

T = tp.TypeVar("T")


class SimpleCache(tp.Generic[T]):

    def __init__(self, cache_file: str | None = None) -> None:
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, T] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def get(self, path: str) -> T | None:
        with self._lock:
            return self.cache.get(path, None)

    def set(self, path: str, item: T) -> None:
        with self._lock:
            self.cache[path] = item
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


@dc.dataclass(frozen=True)
class CacheItem(tp.Generic[T]):
    data: T
    created_at: float


class TimedCache(tp.Generic[T]):

    def __init__(
        self, cache_file: str | None = None, life_time: float | None = None
    ) -> None:
        self.life_time: float = (
            float("+inf") if life_time is None else life_time
        )
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, CacheItem[T]] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def get(self, path: str) -> T | None:
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
        with self._lock:
            self.cache[path] = CacheItem[T](data=data, created_at=time.time())
            self._save_to_disk()

    def remove(self, path: str) -> None:
        with self._lock:
            if path in self.cache:
                self._remove_item(path)

    def clear(self) -> None:
        with self._lock:
            self.cache.clear()
            self._save_to_disk()

    def purge(self) -> None:
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

    def _load_from_disk(self) -> None:
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            raw_cache: dict[str, dict[str, tp.Any]] = json.loads(content)
            self.cache = {
                key: CacheItem[T](
                    data=tp.cast(T, value["data"]),
                    created_at=value["created_at"],
                )
                for key, value in raw_cache.items()
            }
        except (IOError, json.JSONDecodeError, KeyError):
            # Si falla la carga, iniciamos con caché vacío por seguridad
            self.cache = {}

    def _save_to_disk(self) -> None:
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
        self.cache.pop(path, None)
        self._save_to_disk()


NamesCache = SimpleCache[str]
InventoryCache = SimpleCache[list[str]]
TimedNamesCache = TimedCache[str]
TimedInventoryCache = TimedCache[list[str]]

__all__ = [
    "CacheItem",
    "InventoryCache",
    "NamesCache",
    "SimpleCache",
    "TimedCache",
    "TimedInventoryCache",
    "TimedNamesCache",
]
