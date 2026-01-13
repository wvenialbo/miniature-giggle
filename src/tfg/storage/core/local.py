"""
Fábrica para crear contextos de almacenamiento preconfigurados.

Proporciona una interfaz simple para crear DataSourceContexts
preconfigurados para diferentes backends (Colab, local, S3, etc.).
"""

import pathlib as pl

from ..backend import FilesystemBackend
from ..datasource import Datasource, DatasourceContext
from ..handler import DataHandler
from ..uri import PathURIMapper
from .handlers import get_file_handlers


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
        Ruta base dentro del sistema de archivos local.  Debe ser una
        ruta relativa al punto de montaje.  Por defecto ''.
    mountpoint : str, optional
        Punto de montaje del sistema de archivos local.  Por defecto
        '.'.
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    if pl.Path(root_path).is_absolute():
        raise ValueError(
            "`root_path` debe ser una ruta relativa al punto de montaje: "
            f"'{root_path}'"
        )

    # URI Mapper
    full_base = str(pl.Path(mountpoint) / root_path)
    mapper = PathURIMapper(base_path=full_base)

    # Backend y handlers
    backend = FilesystemBackend()
    if handlers is None:
        handlers = get_file_handlers()

    return DatasourceContext(
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )
