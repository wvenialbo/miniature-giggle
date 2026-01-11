import abc
import os

from .base import StorageBackend


class FilesystemBackend(StorageBackend, abc.ABC):
    """
    Backend para sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones para leer, escribir, eliminar
    y listar archivos.

    Parameters
    ----------
    mountpoint : str
        Ruta base para todas las URIs.

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

    def __init__(self, *, mountpoint: str) -> None:
        self.mountpoint = mountpoint

    def __repr__(self) -> str:
        return f"FilesystemBackend(mountpoint='{self.mountpoint}')"

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        path = self._resolve_path(uri)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        self._check_ready()

        path = self._resolve_path(uri)

        return os.path.exists(path)

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las URIs que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URIs.

        Returns
        -------
        list[str]
            Una lista de URIs que comienzan con el prefijo dado.
        """
        self._check_ready()

        base_dir = self._resolve_path(prefix)

        uris: list[str] = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.mountpoint)
                uris.append(relative_path)

        return uris

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        """
        self._check_ready()

        path = self._resolve_path(uri)

        with open(path, "rb") as f:
            return f.read()

    def _resolve_path(self, uri: str) -> str:
        """
        Resuelve la URI a una ruta de archivo absoluta.

        Parameters
        ----------
        uri : str
            La URI a resolver.

        Returns
        -------
        str
            La ruta de archivo absoluta correspondiente a la URI.
        """
        full_path = os.path.join(self.mountpoint, uri)
        return os.path.normpath(full_path)

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        self._check_ready()

        path = self._resolve_path(uri)
        # os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            f.write(data)

    @abc.abstractmethod
    def _check_ready(self) -> None:
        """
        Verifica si el backend está listo para usarse.

        Raises
        ------
        RuntimeError
            Si el backend no está listo.
        """
        mountpoint = self.mountpoint
        if not (os.path.exists(mountpoint) and os.path.isdir(mountpoint)):
            raise RuntimeError(
                f"El punto de montaje '{mountpoint}' no existe "
                "o no es un directorio."
            )
