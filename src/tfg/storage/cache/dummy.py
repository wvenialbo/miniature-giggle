import typing as tp

from .base import CacheBase


T = tp.TypeVar("T")


class DummyCache(CacheBase[T]):
    """
    Caché dummy que no almacena ningún dato.

    Esta implementación de caché cumple con la interfaz `CacheBase`,
    pero no realiza ninguna operación de almacenamiento. Todos los
    métodos son efectivamente no operativos (no-ops).

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

    def __repr__(self) -> str:
        return "DummyCache()"

    def clear(self) -> None:
        """Caché dummy: no realiza ninguna operación."""
        pass

    def invalidate(self, path: str) -> None:
        """Caché dummy: no realiza ninguna operación."""
        pass

    def purge(self) -> None:
        """Caché dummy: no realiza ninguna operación."""
        pass

    def get(self, path: str) -> T | None:
        """Caché dummy: no realiza ninguna operación."""
        pass

    def set(self, path: str, data: T) -> None:
        """Caché dummy: no realiza ninguna operación."""
        pass


__all__ = ["DummyCache"]
