import pathlib as pl

from .base import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Backend de almacenamiento para el sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones de E/S para leer, escribir,
    eliminar y listar archivos.  No conoce rutas lógicas, realiza
    operaciones crudas de E/S sobre una ruta nativa absoluta.

    Methods
    -------
    content(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    delete(uri: str) -> None
        Elimina los datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    read(uri: str) -> bytes
        Lee los datos desde la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI especificada.

    Notes
    -----
    - Todas las URI pasadas a sus métodos deben ser rutas absolutas
      nativas del sistema de archivos.  Las URI devueltas por los
      métodos también serán rutas absolutas nativas del sistema de
      archivos.
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    - Asegura que los directorios intermedios necesarios se creen al
      escribir datos para emular el comportamiento típico de un backend
      de almacenamiento de objetos.
    """

    def __repr__(self) -> str:
        return "FilesystemBackend()"

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las rutas que comienzan con el prefijo especificado.

        Obteniene la lista de todos los archivos cuyas rutas comienzan
        con el prefijo dado.  `prefix` debe ser una ruta nativa absoluta
        completa, o parcial, válida para el backend.  Devuelve una lista
        de rutas nativas absolutas del backend.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las rutas.

        Returns
        -------
        tp.List[str]
            Una lista de rutas que comienzan con el prefijo dado.
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

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la ruta especificada.

        Elimina archivos individuales; no elimina directorios.  La
        operación es idempotente, la ruta puede no existir o ser un
        directorio sin que se genere un error.  `uri` debe ser una ruta
        nativa absoluta completa válida para el sistema de archivos.

        Parameters
        ----------
        uri : str
            La ruta de los datos a eliminar.
        """
        path = _check_uri(uri)
        if path.is_file():
            path.unlink(missing_ok=True)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la ruta especificada.

        Verifica si un archivo existe en la ruta dada.  La ruta debe
        apuntar a un archivo individual.  `uri` debe ser una ruta nativa
        absoluta completa válida para el sistema de archivos.

        Parameters
        ----------
        uri : str
            La ruta de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen en la ruta dada, False en caso
            contrario.
        """
        path = _check_uri(uri)
        return path.exists()

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la ruta especificada.

        Carga los datos desde la ruta dada.  La ruta debe apuntar a un
        archivo individual.  `uri` debe ser una ruta nativa absoluta
        completa válida para el sistema de archivos.

        Parameters
        ----------
        uri : str
            La ruta de los datos a leer.

        Returns
        -------
        bytes
            Los datos leídos desde la ruta dada.
        """
        path = _check_uri(uri)
        return path.read_bytes()

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la ruta especificada.

        Guarda los datos en la ruta dada.  Al finalizar la operación, la
        ruta debe apuntar a un archivo individual.  `uri` debe ser una
        ruta nativa absoluta completa válida para el sistema de
        archivos.

        Parameters
        ----------
        uri : str
            La ruta donde se escribirán los datos.
        data : bytes
            Los datos a escribir en la ruta dada.
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
