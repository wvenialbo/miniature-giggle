import os

from .filesystem import FilesystemBackend


class LocalBackend(FilesystemBackend):
    """
    Backend para sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones para leer, escribir, eliminar
    y listar archivos.

    Parameters
    ----------
    mountpoint : str
        Ruta base para todas las URIs. Si no se proporciona, se usará la
        ruta actual.

    Attributes
    ----------
    mountpoint : str
        Ruta base para todas las URIs.

    Methods
    -------
    delete(uri: str) -> None
        Elimina los datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    list_files(prefix: str) -> list[str]
        Lista todas las URIs que comienzan con el prefijo especificado.
    read(uri: str) -> bytes
        Lee los datos desde la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI especificada.
    """

    def __init__(self, *, mountpoint: str = os.getcwd()) -> None:
        super().__init__(mountpoint=mountpoint)

    def __repr__(self) -> str:
        return f"LocalBackend(mountpoint='{self.mountpoint}')"
