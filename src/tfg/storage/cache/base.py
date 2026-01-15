import typing as tp

T = tp.TypeVar("T")


class AbstractCache(tp.Protocol):
    """
    Protocolo base para cachés de almacenamiento de datos.

    Define la interfaz mínima que debe implementar cualquier caché de
    almacenamiento de datos.

    Methods
    -------
    clear() -> None
        Limpia todos los objetos almacenados en la caché.
    purge() -> None
        Elimina entradas expiradas de la caché.
    remove(path: str) -> None
        Elimina un objeto de la caché usando la ruta especificada.
    """

    def clear(self) -> None:
        """
        Limpia todos los objetos almacenados en la caché.

        Esta operación elimina todos los objetos actualmente almacenados
        en la caché.
        """
        ...

    def purge(self) -> None:
        """
        Elimina entradas expiradas de la caché.

        Las implementaciones pueden definir políticas de expiración para
        los objetos almacenados en la caché (ejemplo: tiempo de vida
        máximo). Esta función elimina todos los objetos que hayan
        expirado según dichas políticas.
        """
        ...

    def remove(self, path: str) -> None:
        """
        Elimina un objeto de la caché usando la ruta especificada.

        Parameters
        ----------
        path : str
            La ruta del objeto a eliminar de la caché.
        """
        ...


class CacheBase(AbstractCache, tp.Generic[T]):
    """
    Protocolo para cachés de almacenamiento de datos.

    Define la interfaz para cachés que almacenan datos en memoria o en
    almacenamiento local para acelerar operaciones de lectura y escritura
    en backends remotos.

    Hereda de AbstractCache y añade métodos para obtener y establecer
    objetos en la caché.

    Methods
    -------
    get(path: str) -> Any
        Recupera un objeto desde la caché usando la ruta especificada.
    set(path: str, item: Any) -> None
        Almacena un objeto en la caché bajo la ruta especificada.
    """

    def get(self, path: str) -> T | None:
        """
        Recupera un objeto desde la caché usando la ruta especificada.

        Parameters
        ----------
        path : str
            La ruta del objeto a recuperar.

        Returns
        -------
        Any | None
            El objeto almacenado en la caché bajo la ruta dada, o None si
            no existe.
        """
        ...

    def set(self, path: str, data: T) -> None:
        """
        Almacena un objeto en la caché bajo la ruta especificada.

        Parameters
        ----------
        path : str
            La ruta bajo la cual almacenar el objeto.
        data : Any
            El objeto a almacenar en la caché.
        """
        ...
