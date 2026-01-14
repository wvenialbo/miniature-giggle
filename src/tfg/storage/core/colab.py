import os
import pathlib as pl
import warnings

from ..backend import FilesystemBackend
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..uri import PathURIMapper
from .handlers import get_file_handlers

try:
    from google import colab

    def colab_drive_flush_and_unmount() -> None:  # type: ignore
        colab.drive.flush_and_unmount()

    def colab_drive_mount(mountpoint: str) -> None:  # type: ignore
        colab.drive.mount(mountpoint)

    def running_on_colab() -> bool:
        return bool(os.getenv("COLAB_RELEASE_TAG"))

except ImportError:

    def colab_drive_flush_and_unmount() -> None:
        colab_not_found_error()

    def colab_drive_mount(_: str) -> None:
        colab_not_found_error()

    def colab_not_found_error() -> None:
        raise RuntimeError(
            "El módulo 'colab' de Google no está disponible. "
            "Asegúrate de estar ejecutando este código en "
            "Google Colab"
        )

    def running_on_colab() -> bool:
        return False


class ColabDrive:
    """
    Gestiona la conexión con Google Drive desde Google Colab.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para el sistema de almacenamiento.  Por
        defecto es "/content/drive".

    Methods
    -------
    close(fail: bool = False) -> bool
        Cierra la conexión con el sistema de almacenamiento.
    ensure_mounted() -> None
        Asegura que el sistema de almacenamiento esté montado.
    get_mountpoint() -> str
        Obtiene el punto de montaje del sistema de almacenamiento.
    is_mounted() -> bool
        Verifica si el sistema de almacenamiento está montado.
    open(fail: bool = False) -> bool
        Abre la conexión con el sistema de almacenamiento.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        self.mountpoint = mountpoint

    def __repr__(self) -> str:
        return f"ColabDrive(mountpoint='{self.mountpoint}')"

    def close(self, *, fail: bool = False) -> bool:
        """
        Cierra la conexión con el sistema de almacenamiento.

        Desmonta y cierra la conexión con el sistema de almacenamiento
        local o remoto.

        Si no se puede cerrar la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede cerrar la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            cerrada después de la llamada, False en caso contrario.
        """
        if not self.is_mounted():
            return True

        colab_drive_flush_and_unmount()

        if self.is_mounted():
            self._report_failure("Google Drive no se pudo desmontar", fail)
            return False

        return True

    def ensure_mounted(self) -> None:
        """
        Asegura que el sistema de almacenamiento esté montado.

        Si el sistema de almacenamiento no está montado, lo monta.
        Si ya está montado, no hace nada.

        Returns
        -------
        None
        """
        if not self.is_mounted():
            self.open(fail=True)

    def get_mountpoint(self) -> str:
        """
        Obtiene el punto de montaje del sistema de almacenamiento.

        Devuelve la ruta del directorio dentro del sistema de archivos
        local donde se montó el sistema de almacenamiento.

        Returns
        -------
        str
            La ruta del punto de montaje del sistema de almacenamiento.
        """
        return self.mountpoint

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de almacenamiento está montado.

        Returns
        -------
        bool
            True si el sistema de almacenamiento está montado, False en
            caso contrario.
        """
        return running_on_colab() and pl.Path(self.mountpoint).is_mount()

    def open(self, *, fail: bool = False) -> bool:
        """
        Abre la conexión con el sistema de almacenamiento.

        Abre la conexión con el sistema de almacenamiento remoto y lo
        monta en el punto de montaje obtenido por `get_mountpoint()`.

        Si no se puede abrir la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede abrir la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            abierta después de la llamada, False en caso contrario.
        """
        if self.is_mounted():
            return True

        colab_drive_mount(self.mountpoint)

        if not self.is_mounted():
            self._report_failure(
                f"Google Drive no se pudo montar en '{self.mountpoint}'", fail
            )
            return False

        return True

    @staticmethod
    def _report_failure(error_message: str, fail: bool) -> None:
        """
        Informa de un fallo lanzando una excepción o emitiendo una
        advertencia.

        Parameters
        ----------
        error_message : str
            Mensaje de error a utilizar en la excepción o advertencia.
        fail : bool
            Si es True, lanza una excepción RuntimeError con el mensaje
            de error.  Si es False, emite una advertencia RuntimeWarning
            con el mensaje de error.

        Returns
        -------
        None
        """
        if fail:
            raise RuntimeError(error_message)

        warnings.warn(error_message, RuntimeWarning)


_drive: ColabDrive | None = None


def use_drive_for_colab(
    *,
    root_path: str = "MyDrive",
    mountpoint: str = "/content/drive",
    handlers: list[DataHandler] | None = None,
) -> DatasourceContract:
    """
    Crea contexto para Google Drive para Google Colab.

    Parameters
    ----------
    root_path : str, optional
        Ruta base dentro de Google Drive.  Debe ser una ruta relativa al
        punto de montaje.  Por defecto 'MyDrive'.
    mountpoint : str, optional
        Punto de montaje de Google Drive en Colab.  Por defecto
        '/content/drive'.
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    if pl.Path(root_path).is_absolute():
        raise ValueError(
            "`root_path` debe ser una ruta relativa dentro de Drive: "
            f"'{root_path}'"
        )

    # Connection Manager
    connection = ColabDrive(mountpoint=mountpoint)
    connection.open(fail=True)

    mountpoint = connection.get_mountpoint()
    base_path = pl.Path(mountpoint) / root_path

    backend = FilesystemBackend()

    mapper = PathURIMapper()

    if handlers is None:
        handlers = get_file_handlers()

    global _drive
    _drive = connection

    return Datasource(
        mountpoint=str(base_path),
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )


def close_use_drive_for_colab(fail: bool = False) -> bool:
    """
    Cierra la conexión con Google Drive usada en Colab.

    Parameters
    ----------
    fail : bool, optional
        Si es True, lanza una excepción si no se puede cerrar la
        conexión con Google Drive.  Por defecto es False.

    Returns
    -------
    bool
        True si la conexión con Google Drive está cerrada después de
        la llamada, False en caso contrario.
    """
    global _drive

    if _drive is None:
        return True

    result = _drive.close(fail=fail)

    if result:
        _drive = None

    return result
