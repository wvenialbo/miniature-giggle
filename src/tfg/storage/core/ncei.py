import pathlib as pl

import requests

from ..backend import NCEIBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import NCEIURIMapper


def use_ncei_archive(
    *,
    base_url: str,
    root_path: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource para el archivo HTTP de NCEI.

    Parameters
    ----------
    base_url : str
        URL base del dataset en NCEI (ej. https://www.ncei.noaa.gov/data/...)
    cache_file : str | Path, optional
        Ruta para persistir el listado de archivos.
    expire_after : float, optional
        Tiempo de expiración de la caché en segundos.
    """
    # 1. Configurar caché
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedScanCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath("/")
    mountpoint = local_root / base_path.as_posix()

    # 2. Instanciar componentes
    session = requests.Session()

    mapper = NCEIURIMapper(base_url=base_url)
    backend = NCEIBackend(session=session, scan_cache=scan_cache)

    # 3. Retornar orquestador
    # El mountpoint es "/" porque el Mapper ya gestiona la base_url
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )
