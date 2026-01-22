import pathlib as pl

from ..backend import FilesystemBackend
from ..datasource import DataService, Datasource
from ..mapper import PathURIMapper


def use_local_drive(*, root_path: str | None = None) -> Datasource:
    r"""
    Crea el contexto para el sistema de archivos local.

    Parameters
    ----------
    root_path : str, optional
        Ruta raíz dentro del sistema de archivos local para el contexto.
        Si es None, se utiliza la raíz del sistema ("/" en Unix, "C:\"
        en Windows).

    Returns
    -------
    Datasource
        Contexto configurado listo para usar.
    """
    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath("/")
    mountpoint = local_root / base_path.as_posix()

    backend = FilesystemBackend()

    mapper = PathURIMapper()

    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
    )
