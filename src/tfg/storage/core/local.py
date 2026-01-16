import pathlib as pl

from ..backend import FilesystemBackend
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import PathURIMapper
from .handlers import get_file_handlers


def use_local_drive(
    *,
    root_path: str | None = None,
    mountpoint: str = "/",
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
    base_path = pl.Path(mountpoint or "/") / (root_path or "")
    backend = FilesystemBackend()

    mapper = PathURIMapper()

    if handlers is None:
        handlers = get_file_handlers()

    return Datasource(
        mountpoint=str(base_path),
        backend=backend,
        mapper=mapper,
        handlers=handlers,
    )
