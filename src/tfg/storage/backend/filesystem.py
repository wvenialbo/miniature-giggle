import pathlib as pl

from .base import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Backend para sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones para leer, escribir, eliminar
    y listar archivos.

    Methods
    -------
    delete(uri: str) -> None
        Elimina los datos en la URI física especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI física especificada.
    content(prefix: str) -> list[str]
        Lista las URI físicas que comienzan con el prefijo especificado.
    read(uri: str) -> bytes
        Lee los datos desde la URI física especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI física especificada.
    """

    def __repr__(self) -> str:
        return "FilesystemBackend()"

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a eliminar.
        """
        pl.Path(uri).unlink(missing_ok=True)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        return pl.Path(uri).exists()

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las URI físicas que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI físicas.

        Returns
        -------
        tp.List[str]
            Una lista de URI físicas que comienzan con el prefijo dado.
        """
        return [
            str(entry)
            for entry in pl.Path(prefix).rglob("*")
            if entry.is_file()
        ]

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a leer.
        """
        return pl.Path(uri).read_bytes()

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        target = pl.Path(uri)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
