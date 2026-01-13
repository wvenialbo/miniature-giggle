import os
import typing as tp

from .utils import check_is_active, format_report, format_table, get_columns_size
from .filehandler import FileHandler
from .filesystem import FileSystemMounter


class StorageDriver:
    """
    Clase para manejar la conexión con el sistema de archivos.

    Parameters
    ----------
    storage : list[tuple[str, StorageInterface]]
        Lista de tuplas con el nombre del formato y la instancia del
        manejador de almacenamiento correspondiente.
    directory : str
        Directorio en el sistema de archivos donde se almacenan los
        archivos.
    mountpoint : str, optional
        Punto de montaje en el sistema de archivos.  Por defecto es
        '/content/drive'.

    Attributes
    ----------
    mountpoint : str
        Punto de montaje en el sistema de archivos.
    directory : str
        Directorio en el sistema de archivos donde se almacenan los
        archivos.
    rootpath_ : str
        Ruta raíz en el sistema de archivos después de montar (se crea
        al montar).

    Methods
    -------
    exists(filename: str) -> bool
        Verifica si un archivo existe en el sistema de archivos.
    get_pathname(filename: str) -> str
        Obtiene la ruta completa de un archivo en el sistema de
        archivos.
    is_mounted() -> bool
        Verifica si el sistema de archivos está montado.
    load(filename: str) -> Any
        Carga datos desde un archivo en el sistema de archivos.
    mount(fail: bool = True) -> None
        Monta el sistema de archivos si aún no está montado.
    save(data: Any, filename: str) -> None
        Guarda datos en un archivo en el sistema de archivos.
    unmount(fail: bool = True) -> None
        Desmonta el sistema de archivos y guarda todos los cambios.

    Examples
    --------
    >>> # En Colab
    >>> driver = StorageDriver(
    >>>     filesystem=GoogleColabFileSystem(mountpoint="/content/drive"),
    >>>     directory="mi_directorio",
    >>>     handlers=[(".npz", NumpyFileHandler()), (".pkl", PickleFileHandler())]
    >>> )

    >>> # Localmente
    >>> driver = StorageDriver(
    >>>     filesystem=LocalFileSystem(base_path="/ruta/local"),
    >>>     directory="mi_directorio",
    >>>     handlers=[(".npz", NumpyFileHandler()), (".pkl", PickleFileHandler())]
    >>> )
    """

    def __init__(
        self,
        *,
        directory: str,
        filehandler: list[tuple[str, FileHandler]],
        filesystem: FileSystemMounter,
    ) -> None:
        self.directory = directory
        self.filehandler = filehandler
        self.filesystem = filesystem

    def __repr__(self) -> str:
        filehandlers = [
            f"('{ext}', {repr(handler)})" for ext, handler in self.filehandler
        ]
        return (
            f"StorageDriver(directory='{self.directory}', "
            f"filehandler=[{', '.join(filehandlers)}]), "
            f"filesystem={repr(self.filesystem)}"
        )

    def __str__(self) -> str:
        """
        Genera un reporte profesional con el estado y configuración.

        Returns
        -------
        str
            Reporte formateado con la configuración y estado actual.
        """
        is_mounted = self._is_active()

        rootpath = self.rootpath_ if is_mounted else "No montado"

        config_data = [
            ("Directorio en Drive", f"'{self.directory}'", ""),
            ("Punto de montaje", f"'{self.filesystem.get_mountpoint()}'", ""),
            ("Ruta raíz", f"'{rootpath}'", ""),
        ]

        # Construir tabla de configuración
        size = get_columns_size(config_data)

        config_table = format_table(size, "CONFIGURACIÓN", config_data)

        status = "Montado" if is_mounted else "Desmontado"

        header = f"StorageDriver - Estado: {status}"

        return format_report(header, config_table)

    def _activate(self) -> None:
        if self._is_active():
            return

        mountpoint = self.filesystem.get_mountpoint()
        rootpath = os.path.join(mountpoint, self.directory)

        if not (os.path.exists(rootpath) and os.path.isdir(rootpath)):
            raise RuntimeError(
                f"La ruta '{rootpath}' no existe en el sistema de archivos."
            )

        self.rootpath_ = rootpath
        self.filehandler_map_ = dict(self.filehandler)

    def _deactivate(self) -> None:
        if not self._is_active():
            return

        del self.rootpath_
        del self.filehandler_map_

    def exists(self, *, filename: str) -> bool:
        """
        Verifica si un archivo existe en el sistema de archivos.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        bool
            True si el archivo existe, False en caso contrario.
        """
        check_drive_mounted(self)

        pathname = self.get_pathname(filename=filename)

        return os.path.exists(pathname) and os.path.isfile(pathname)

    def get_pathname(self, *, filename: str) -> str:
        """
        Obtiene la ruta completa en el sistema de archivos.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        str
            Ruta completa del archivo en el sistema de archivos.
        """
        check_drive_mounted(self)

        return os.path.join(self.rootpath_, filename)

    def _get_storage_handler(self, pathname: str) -> FileHandler:
        """
        Obtiene el manejador de almacenamiento para un archivo dado.

        Parameters
        ----------
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        StorageInterface
            Manejador de almacenamiento correspondiente.

        Raises
        ------
        ValueError
            Si el formato del archivo no es compatible.
        """
        path_ext = os.path.splitext(pathname)[1]

        if path_ext in self.filehandler_map_:
            return self.filehandler_map_[path_ext]

        raise ValueError(
            f"El formato del archivo '{pathname}' no es compatible"
        )

    def _is_active(self) -> bool:
        """
        Verifica si el manejador de almacenamiento está activo.

        Returns
        -------
        bool
            True si el manejador está activo, False en caso contrario.
        """
        return check_is_active(self, ["rootpath_", "filehandler_map_"])

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de archivos está montado.

        Returns
        -------
        bool
            True si el sistema de archivos está montado, False en caso
            contrario.
        """
        return self.filesystem.is_mounted() and self._is_active()

    def load(self, *, filename: str) -> tp.Any:
        """
        Carga datos desde un archivo en el sistema de archivos.

        Parameters
        ----------
        filename : str
            Nombre del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        pathname = self.get_pathname(filename=filename)

        loaded_data = self._load_from_drive(pathname)

        print(f"Datos cargados desde: '{filename}'")

        return loaded_data

    def _load_from_drive(self, pathname: str) -> tp.Any:
        """
        Carga datos desde un archivo en el sistema de archivos.

        Parameters
        ----------
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        Any
            Datos cargados desde el archivo.
        """
        check_drive_mounted(self)

        storage_handler = self._get_storage_handler(pathname)

        return storage_handler.load(filename=pathname)

    def mount(self, *, fail: bool = True) -> None:
        """
        Monta el sistema de archivos si aún no está montado.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede montar Google
            Drive.  Por defecto es True.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Si la ruta raíz no existe en el sistema de archivos.
        """
        if self.filesystem.mount(fail=fail):
            self._activate()

    def register_storage(
        self,
        *,
        storage: list[tuple[str, FileHandler]] | tuple[str, FileHandler],
    ) -> None:
        """
        Registra un nuevo manejador de almacenamiento.

        Parameters
        ----------
        storage : list[tuple[str, FileHandler]] | tuple[str, FileHandler]
            Manejador de almacenamiento a registrar.

        Returns
        -------
        None
        """
        if isinstance(storage, tuple):
            storage = [storage]

        self.filehandler.extend(storage)

    def save(self, *, data: tp.Any, filename: str) -> None:
        """
        Guarda datos en un archivo en Google Drive.

        Parameters
        ----------
        data : Any
            Datos a guardar.
        filename : str
            Nombre del archivo.

        Returns
        -------
        None
        """
        pathname = self.get_pathname(filename=filename)

        self._save_to_drive(data, pathname)

        print(f"Datos guardados en: '{pathname}'")

    def _save_to_drive(self, data: tp.Any, pathname: str) -> None:
        """
        Guarda datos en un archivo en Google Drive.

        Parameters
        ----------
        data : Any
            Datos a guardar.
        pathname : str
            Ruta completa del archivo.

        Returns
        -------
        None
        """
        check_drive_mounted(self)

        storage_handler = self._get_storage_handler(pathname)

        return storage_handler.save(data=data, filename=pathname)

    def unmount(self, *, fail: bool = True) -> None:
        """
        Desmonta Google Drive y guarda todos los cambios.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede desmontar
            Google Drive.  Por defecto es True.

        Returns
        -------
        None
        """
        if self.filesystem.unmount(fail=fail):
            self._deactivate()


def check_drive_mounted(drive: StorageDriver) -> None:
    """
    Verifica si el sistema de archivos está montado.

    Parameters
    ----------
    drive : StorageDriver
        Instancia de StorageDriver.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        Si el sistema de archivos no está montado.
    """
    if not drive.is_mounted():
        raise RuntimeError(
            "El sistema de archivos no está montado. Por favor, "
            "monte el sistema de archivos antes de continuar"
        )
