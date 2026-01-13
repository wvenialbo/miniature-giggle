"""
Fábrica para crear contextos de almacenamiento preconfigurados.

Proporciona una interfaz simple para crear DataSourceContexts
preconfigurados para diferentes backends (Colab, local, S3, etc.).
"""

import collections.abc as ca
import typing as tp
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

# Tipo para funciones fábrica
FactoryFunc = ca.Callable[..., Datasource]

# Registro global de fábricas
_STORAGE_FACTORIES: dict[str, FactoryFunc] = {}

# Handlers de archivo por defecto
_FILE_HANDLERS: list[DataHandler] = [
    NumpyHandler(),
    PickleHandler(),
    CSVHandler(),
    JSONHandler(),
    YAMLHandler(),
]


def register_factory(name: str, factory: FactoryFunc) -> None:
    """
    Registra un nuevo constructor de contexto de almacenamiento.

    Parameters
    ----------
    name : str
        Nombre identificador del almacenamiento.
    factory : FactoryFunc
        Función que crea un DataSource.

    Raises
    ------
    ValueError
        Si ya existe un constructor de contexto de almacenamiento
        registrado con ese nombre.
    """
    if name in _STORAGE_FACTORIES:
        raise ValueError(f"Una fábrica para '{name}' ya está registrada.")

    _STORAGE_FACTORIES[name] = factory


def get(
    storage_name: str,
    *,
    mountpoint: str = "",
    handlers: list[DataHandler] | None = None,
    **kwargs: tp.Any,
) -> Datasource:
    """
    Crea un DataSourceContext para un tipo de almacenamiento.

    Parameters
    ----------
    storage_name : str
        Nombre del almacenamiento ('colab', 'local', etc.)
    root_path : str, optional
        Ruta base dentro del almacenamiento.
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.
    **kwargs
        Parámetros específicos del almacenamiento.

    Returns
    -------
    DataSourceContext
        Contexto configurado listo para usar.

    Raises
    ------
    ValueError
        Si el nombre del contexto de almacenamiento no está registrado.
    """
    if storage_name not in _STORAGE_FACTORIES:
        available = list(_STORAGE_FACTORIES.keys())
        raise ValueError(
            f"Almacenamiento '{storage_name}' no disponible. "
            f"Opciones: {available}"
        )

    return _STORAGE_FACTORIES[storage_name](
        root_path=mountpoint,
        handlers=handlers,
        **kwargs,
    )


def _create_colab_context(
    root_path: str = "MyDrive",
    mountpoint: str = "/content/drive",
    handlers: list[DataHandler] | None = None,
    **kwargs: tp.Any,
) -> DatasourceContext:
    """Fábrica interna para Google Drive para Google Colab."""
    # Connection Manager
    connection = ColabDriveConnectionManager(mountpoint=mountpoint)

    # URI Mapper: combina mountpoint + root_path
    full_base = str(Path(connection.get_mountpoint()) / root_path)
    mapper = PathURIMapper(base_path=full_base)

    # Backend y handlers
    backend = FilesystemBackend()
    if handlers is None:
        handlers = _FILE_HANDLERS

    return DatasourceContext(
        connection=connection,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )


def _create_local_context(
    root_path: str = "",
    base_dir: str = ".",
    handlers: list[DataHandler] | None = None,
    **kwargs: tp.Any,
) -> DatasourceContext:
    """Fábrica interna para sistema de archivos local."""
    # Connection Manager (siempre "montado")
    connection = LocalConnectionManager(mountpoint=base_dir)

    # URI Mapper
    full_base = str(Path(connection.get_mountpoint()) / root_path)
    mapper = PathURIMapper(base_path=full_base)

    # Backend y handlers
    backend = FilesystemBackend()
    if handlers is None:
        handlers = _FILE_HANDLERS

    return DatasourceContext(
        connection=connection,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )


# Fábricas de conveniencia
def for_colab(**kwargs: tp.Any) -> DatasourceContext:
    """Crea contexto para Google Drive en Colab."""
    return _create_colab_context(**kwargs)


def for_local(**kwargs: tp.Any) -> DatasourceContext:
    """Crea contexto para sistema de archivos local."""
    return _create_local_context(**kwargs)


# Registrar fábricas por defecto
register_factory("colab", _create_colab_context)
register_factory("local", _create_local_context)
