import contextlib
import json
import pathlib as pl
import threading as th

from .base import CacheBase


class SimpleCache[T](CacheBase[T]):
    """
    Caché simple que almacena datos en memoria y opcionalmente en disco.

    Esta implementación de caché mantiene los datos en un diccionario en
    memoria para acceso rápido. Además, puede opcionalmente persistir
    los datos en un archivo JSON en disco para mantener el estado entre
    ejecuciones.

    Parameters
    ----------
    cache_file : str | None, optional
        Ruta al archivo donde se almacenará la caché en disco. Si es
        None, la caché solo existirá en memoria (por defecto None).

    Attributes
    ----------
    cache_file : pathlib.Path | None
        Ruta al archivo de caché en disco, o None si no se usa.
    cache : dict[str, T]
        Diccionario que almacena los datos en memoria.
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

    def __init__(self, cache_file: str | None = None) -> None:
        self.cache_file = pl.Path(cache_file) if cache_file else None
        self.cache: dict[str, T] = {}
        self._lock = th.Lock()

        self._load_from_disk()

    def __repr__(self) -> str:
        return f"SimpleCache(cache_file='{self.cache_file}')"

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
        Invalida (elimina) un objeto específico de la caché.

        Parameters
        ----------
        path : str
            Clave del objeto a eliminar de la caché.
        """
        with self._lock:
            if path in self.cache:
                self.cache.pop(path, None)
                self._save_to_disk()

    def purge(self) -> None:
        """
        Elimina entradas expiradas de la caché.

        Notes
        -----
        SimpleCache no tiene expiración, por lo que purge no hace nada.
        """
        pass

    def get(self, path: str) -> T | None:
        """
        Obtiene un objeto de la caché por su clave.

        Parameters
        ----------
        path : str
            Clave del objeto a obtener.

        Returns
        -------
        T | None
            El objeto almacenado en la caché, o None si no existe.
        """
        with self._lock:
            return self.cache.get(path, None)

    def set(self, path: str, data: T) -> None:
        """
        Almacena un objeto en la caché bajo una clave específica.

        Parameters
        ----------
        path : str
            Clave bajo la cual se almacenará el objeto.
        data : T
            Objeto a almacenar en la caché.
        """
        with self._lock:
            self.cache[path] = data
            self._save_to_disk()

    def _load_from_disk(self) -> None:
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text(encoding="utf-8")
            self.cache = json.loads(content)
        except (OSError, json.JSONDecodeError):
            # Si falla la carga, iniciamos con caché vacío por seguridad
            self.cache = {}

    def _save_to_disk(self) -> None:
        if not self.cache_file:
            return

        with contextlib.suppress(IOError):
            # Escribe de forma atómica (idealmente)
            content = json.dumps(self.cache, indent=2)
            self.cache_file.write_text(content, encoding="utf-8")


__all__ = ["SimpleCache"]
