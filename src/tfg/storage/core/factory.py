"""
Fábrica para crear contextos de almacenamiento preconfigurados.

Proporciona una interfaz simple para crear DataSourceContexts
preconfigurados para diferentes backends (Colab, local, S3, etc.).
"""

from pathlib import Path

from ..backend import FilesystemBackend
from ..connector import ColabDriveConnectionManager, LocalConnectionManager
from ..datasource import Datasource, DatasourceContext
from ..handler import (
    CSVHandler,
    DataHandler,
    JSONHandler,
    NumpyHandler,
    PickleHandler,
    YAMLHandler,
)
from ..uri import PathURIMapper

_DEFAULT_HANDLERS: list[DataHandler] = [
    NumpyHandler(),
    PickleHandler(),
    CSVHandler(),
    JSONHandler(),
    YAMLHandler(),
]

# Handlers de archivo por defecto
_file_handlers: list[DataHandler] = _DEFAULT_HANDLERS.copy()


def _get_file_handlers() -> list[DataHandler]:
    """Obtiene la lista de handlers de archivo por defecto."""
    return [handler.copy() for handler in _file_handlers]


def reset_default_handlers() -> None:
    """
    Restablece la lista de handlers de archivo por defecto a los originales.

    Parameters
    ----------
    handlers : list[DataHandler]
        Nueva lista de handlers de archivo por defecto.
    """
    global _file_handlers
    _file_handlers = _DEFAULT_HANDLERS.copy()


def set_default_handlers(handlers: list[DataHandler]) -> None:
    """
    Establece la lista de handlers de archivo por defecto.

    Parameters
    ----------
    handlers : list[DataHandler]
        Nueva lista de handlers de archivo por defecto.
    """
    format_id = [id for handler in handlers for id in handler.format_id]
    if len(format_id) != len(set(format_id)):
        repeated = sorted(
            {fmt_id for fmt_id in format_id if format_id.count(fmt_id) > 1}
        )
        duplicates = "', '".join(repeated)
        raise ValueError(
            f"Existen handlers con extensiones duplicados: '{duplicates}'"
        )

    global _file_handlers
    _file_handlers = [handler.copy() for handler in handlers]


# Fábricas de conveniencia
def use_drive_for_colab(
    *,
    root_path: str = "MyDrive",
    mountpoint: str = "/content/drive",
    handlers: list[DataHandler] | None = None,
) -> Datasource:
    """
    Crea contexto para Google Drive para Google Colab.

    Parameters
    ----------
    root_path : str, optional
        Ruta base dentro de Google Drive. Por defecto 'MyDrive'.
    mountpoint : str, optional
        Punto de montaje de Google Drive en Colab. Por defecto
        '/content/drive'.
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    # Connection Manager
    connection = ColabDriveConnectionManager(mountpoint=mountpoint)

    # URI Mapper: combina mountpoint + root_path
    full_base = str(Path(connection.get_mountpoint()) / root_path)
    mapper = PathURIMapper(base_path=full_base)

    # Backend y handlers
    backend = FilesystemBackend()
    if handlers is None:
        handlers = _get_file_handlers()

    return DatasourceContext(
        connection=connection,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )


def use_local_drive(
    root_path: str = "",
    mountpoint: str = ".",
    handlers: list[DataHandler] | None = None,
) -> Datasource:
    """
    Crea contexto para sistema de archivos local.

    Parameters
    ----------
    root_path : str, optional
        Ruta base dentro del sistema de archivos local. Por defecto ''.
    mountpoint : str, optional
        Punto de montaje del sistema de archivos local. Por defecto '.'.
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    # Connection Manager (siempre "montado")
    connection = LocalConnectionManager(mountpoint=mountpoint)

    # URI Mapper
    full_base = str(Path(connection.get_mountpoint()) / root_path)
    mapper = PathURIMapper(base_path=full_base)

    # Backend y handlers
    backend = FilesystemBackend()
    if handlers is None:
        handlers = _get_file_handlers()

    return DatasourceContext(
        connection=connection,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )
