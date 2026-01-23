import pathlib as pl
import warnings

from ...utils import running_on_colab
from ..backend import FilesystemBackend
from ..datasource import DataService, Datasource
from ..mapper import PathURIMapper


try:
    from google.colab import drive

    def _colab_drive_flush_and_unmount() -> None:
        drive.flush_and_unmount()

    def _colab_drive_mount(mountpoint: str) -> None:
        drive.mount(mountpoint)

except ImportError:

    def _colab_drive_flush_and_unmount() -> None:
        _colab_not_found_error(_MOUNT_POINT)

    def _colab_drive_mount(mountpoint: str) -> None:
        _colab_not_found_error(mountpoint)

    def _colab_not_found_error(mountpoint: str) -> None:
        raise RuntimeError(
            "El módulo 'colab' de Google no está disponible. "
            "Asegúrate de estar ejecutando este código en "
            "Google Colab"
        )


_MOUNT_POINT = "/content/drive"
_ROOT_PATH = "MyDrive"


def _is_mounted() -> bool:
    """
    Verifica si el sistema de almacenamiento está montado.

    Returns
    -------
    bool
        True si el sistema de almacenamiento está montado, False en
        caso contrario.
    """
    return running_on_colab() and pl.Path(_MOUNT_POINT).is_mount()


def _mount_drive(*, fail: bool = False) -> None:
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
    """
    if _is_mounted():
        return

    _colab_drive_mount(_MOUNT_POINT)

    if not _is_mounted():
        _report_failure(
            f"Google Drive no se pudo montar en '{_MOUNT_POINT}'", fail=fail
        )


def _report_failure(error_message: str, *, fail: bool) -> None:
    """
    Informa de un fallo lanzando una excepción o una advertencia.

    Parameters
    ----------
    error_message : str
        Mensaje de error a utilizar en la excepción o advertencia.
    fail : bool
        Si es True, lanza una excepción RuntimeError con el mensaje
        de error.  Si es False, emite una advertencia RuntimeWarning
        con el mensaje de error.

    Raises
    ------
    RuntimeError
        Si `fail` es True.
    """
    if fail:
        raise RuntimeError(error_message)

    warnings.warn(error_message, RuntimeWarning, stacklevel=3)


def _unmount_drive(*, fail: bool = False) -> None:
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
    """
    if not _is_mounted():
        return

    _colab_drive_flush_and_unmount()

    if _is_mounted():
        _report_failure("Google Drive no se pudo desmontar", fail=fail)


def use_colab_drive(*, root_path: str | None = None) -> Datasource:
    """
    Crea el contexto para el acceso a Google Drive en Google Colab.

    Parameters
    ----------
    root_path : str, optional
        Ruta raíz dentro de Google Drive para el contexto. Si es None,
        se utiliza la raíz del Drive del usuario ("MyDrive").

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    # 1. Configurar el mountpoint
    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)
    gdrive_root = pl.PurePosixPath(_MOUNT_POINT) / _ROOT_PATH
    mountpoint = gdrive_root / base_path.as_posix()

    # 2. Instanciar los servicios
    _mount_drive(fail=True)

    # 3. Instanciar los componentes
    mapper = PathURIMapper()
    backend = FilesystemBackend()

    # 4. Instanciar el DataService orquestador
    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
    )


def release_colab_drive(*, fail: bool = False) -> None:
    """
    Cierra la conexión con Google Drive usada en Colab.

    Parameters
    ----------
    fail : bool, optional
        Si es True, lanza una excepción si no se puede cerrar la
        conexión con Google Drive.  Por defecto es False.
    """
    _unmount_drive(fail=fail)


__all__ = ["release_colab_drive", "use_colab_drive"]
