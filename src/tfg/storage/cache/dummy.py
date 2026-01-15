import typing as tp

from .base import CacheBase

T = tp.TypeVar("T")


class DummyCache(CacheBase[T]):
    """
    Caché dummy que no almacena ningún dato.

    Esta implementación de caché cumple con la interfaz `CacheBase`, pero no
    realiza ninguna operación de almacenamiento. Todos los métodos son
    efectivamente no operativos (no-ops).

    Methods
    -------
    get(path: str) -> None
        Siempre devuelve None, ya que no almacena datos.
    set(path: str, item: Any) -> None
        No realiza ninguna operación.
    remove(path: str) -> None
        No realiza ninguna operación.
    clear() -> None
        No realiza ninguna operación.
    """

    def get(self, path: str) -> T | None:
        """
        Siempre devuelve None, ya que no almacena datos.

        Parameters
        ----------
        path : str
            La ruta del objeto a recuperar.

        Returns
        -------
        None
            Siempre devuelve None.
        """
        return None

    def set(self, path: str, data: T) -> None:
        """
        No realiza ninguna operación.

        Parameters
        ----------
        path : str
            La ruta bajo la cual almacenar el objeto.
        data : Any
            El objeto a almacenar en la caché.
        """
        pass

    def remove(self, path: str) -> None:
        """
        No realiza ninguna operación.

        Parameters
        ----------
        path : str
            La ruta del objeto a eliminar.
        """
        pass

    def clear(self) -> None:
        """
        No realiza ninguna operación.
        """
        pass

    def purge(self) -> None:
        """
        No realiza ninguna operación.
        """
        pass


NoopCache = DummyCache[int]

__all__ = ["DummyCache", "NoopCache"]
