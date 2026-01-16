import contextlib
import dataclasses as dc
import json
import pathlib as pl
import threading as th
import time
import typing as tp

from .base import CacheBase

T = tp.TypeVar("T")


@dc.dataclass(frozen=True)
class CacheItem(tp.Generic[T]):
    data: T
    created_at: float


class TimedCache(CacheBase[T]):
    """
    Caché con tiempo de vida que almacena datos en memoria y
    opcionalmente en disco.

    Esta implementación de caché mantiene los datos en un diccionario en
    memoria para acceso rápido. Además, puede opcionalmente persistir
    los datos en un archivo JSON en disco para mantener el estado entre
    ejecuciones. Cada objeto almacenado tiene un tiempo de vida, y los
    objetos expirados se eliminan automáticamente.

    Parameters
    ----------
    cache_file : str | None, optional
        Ruta al archivo donde se almacenará la caché en disco. Si es
        None, la caché solo existirá en memoria (por defecto None).
    expire_after : float | None, optional
        Tiempo de vida en segundos para cada objeto en la caché. Si es
        None, los objetos no expiran (por defecto None).

    Attributes
    ----------
    life_time : float
        Tiempo de vida en segundos para cada objeto en la caché.
    cache_file : pathlib.Path | None
        Ruta al archivo de caché en disco, o None si no se usa.
    cache : dict[str, CacheItem[T]]
        Diccionario que almacena los datos en memoria junto con su
        tiempo de creación.
    _lock : threading.Lock
        Bloqueo para asegurar operaciones thread-safe en la caché.

    Methods
    -------
    clear() -> None
        Limpia todos los objetos almacenados en la caché.
    get(path: str) -> Any
        Recupera un objeto desde la caché usando la ruta especificada.
    invalidate(path: str) -> None
        Elimina un objeto de la caché usando la ruta especificada.
    purge() -> None
        Elimina entradas expiradas de la caché.
    set(path: str, item: Any) -> None
        Almacena un objeto en la caché bajo la ruta especificada.
    """

    def __init__(
        self, cache_file: str | None = None, expire_after: float | None = None
    ) -> None:
        self.life_time: float = (
            float("+inf") if expire_after is None else expire_after
        )
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, CacheItem[T]] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def __repr__(self) -> str:
        return (
            f"TimedCache(cache_file='{self.cache_file}', "
            f"expire_after={self.life_time})"
        )

    def clear(self) -> None:
        """
        Limpia todos los objetos almacenados en la caché.

        Esta operación elimina todos los objetos actualmente almacenados
        en la caché.
        """
        with self._lock:
            self.cache.clear()
            self._save_to_disk()

    def invalidate(self, path: str) -> None:
        """
        Elimina un objeto de la caché usando la ruta especificada.

        Parameters
        ----------
        path : str
            La ruta del objeto a eliminar de la caché.
        """
        with self._lock:
            if path in self.cache:
                self._remove_item(path)

    def purge(self) -> None:
        """
        Elimina entradas expiradas de la caché.

        Notes
        -----
        En esta implementación, se eliminan todos los objetos cuyo
        tiempo de vida haya expirado.
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
        Recupera un objeto desde la caché usando la ruta especificada.

        Si el objeto ha expirado, se elimina de la caché y se devuelve
        None.

        Parameters
        ----------
        path : str
            La ruta del objeto a recuperar.

        Returns
        -------
        T | None
            El objeto almacenado en la caché bajo la ruta dada, o None
            si no existe o ha expirado.
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
        Almacena un objeto en la caché bajo la ruta especificada.

        Establece el tiempo de creación del objeto al momento actual.

        Parameters
        ----------
        path : str
            La ruta bajo la cual almacenar el objeto.
        data : T
            El objeto a almacenar en la caché.
        """
        with self._lock:
            self.cache[path] = CacheItem[T](data=data, created_at=time.time())
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


TimedDriveCache = TimedCache[str]
TimedScanCache = TimedCache[list[str]]

__all__ = ["CacheItem", "TimedCache", "TimedDriveCache", "TimedScanCache"]
