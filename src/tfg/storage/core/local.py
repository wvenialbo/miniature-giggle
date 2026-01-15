"""
Fábrica para crear contextos de almacenamiento preconfigurados.

Proporciona una interfaz simple para crear DataSourceContexts
preconfigurados para diferentes backends (Colab, local, S3, etc.).
"""

from ..backend import FilesystemBackend
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import PathURIMapper
from .handlers import get_file_handlers


def use_local_drive(
    handlers: list[DataHandler] | None = None,
) -> DatasourceContract:
    """
    Crea contexto para sistema de archivos local.

    Parameters
    ----------
    handlers : list[DataHandler], optional
        Handlers de formato personalizados.

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    backend = FilesystemBackend()

    mapper = PathURIMapper()

    if handlers is None:
        handlers = get_file_handlers()

    return Datasource(
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )
