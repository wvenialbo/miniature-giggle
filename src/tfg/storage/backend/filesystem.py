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
    content(prefix: str) -> list[str]
        Lista las URI físicas que comienzan con el prefijo especificado.
    delete(uri: str) -> None
        Elimina los datos en la URI física especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI física especificada.
    read(uri: str) -> bytes
        Lee los datos desde la URI física especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI física especificada.

    Notes
    -----
    - La clase espera que todas las URIs pasadas a sus métodos sean
      rutas absolutas del sistema de archivos. Las rutas devueltas por
      el método `content` también serán rutas absolutas.
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    - Asegura que los directorios necesarios se creen al escribir datos.
    """

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las URI físicas que comienzan con el prefijo especificado.

        Devuelve la lista de identificadores nativos del backend (rutas
        absolutas, claves, etc.) que comienzan con el prefijo dado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI físicas.

        Returns
        -------
        tp.List[str]
            Una lista de URI físicas que comienzan con el prefijo dado.
        """
        path = _check_uri(prefix)
        base = path.parent

        files = [
            str(entry)
            for entry in base.glob(f"{path.name}*")
            if entry.is_file()
        ]

        folders = [
            entry for entry in base.glob(f"{path.name}*") if entry.is_dir()
        ]

        return files + [
            str(entry)
            for folder in folders
            for entry in folder.rglob("*")
            if entry.is_file()
        ]

    def __repr__(self) -> str:
        return "FilesystemBackend()"

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI física especificada.

        Elimina archivos u objetos individuales si existen. No elimina
        contenedores o directorios. La operación es idempotente.

        Parameters
        ----------
        uri : str
            La URI física de los datos a eliminar.
        """
        path = _check_uri(uri)
        if path.is_file():
            path.unlink(missing_ok=True)

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
        path = _check_uri(uri)
        return path.exists()

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a leer.
        """
        path = _check_uri(uri)
        return path.read_bytes()

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
        target = _check_uri(uri)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _check_uri(uri: str) -> pl.Path:
    path = pl.Path(uri)
    if not path.is_absolute():
        raise ValueError(
            f"El prefijo debe ser una ruta absoluta. Se recibió: '{uri}'. "
            "Posible error en la capa superior (URIMapper o DataContext)."
        )
    return path
