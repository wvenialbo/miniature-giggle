import pathlib as pl

import requests

from ..backend import NCEIBackend
from ..cache import TimedCache
from ..datasource import DataService, Datasource
from ..mapper import NCEIURIMapper


NCEI_BASE_URL = "https://www.ncei.noaa.gov/data/"


def use_ncei_archive(
    *,
    dataset_path: str,
    root_path: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> Datasource:
    """
    Crea un contexto de Datasource para el archivo HTTP de NCEI.

    Parameters
    ----------
    dataset_path : str
        Ruta del dataset en el servidor de NCEI Archive, relativa a
        'https://www.ncei.noaa.gov/data/'.
    root_path : str, optional
        Prefijo raíz dentro del dataset para este Datasource.  Por
        defecto None (raíz del dataset).
    cache_file : str | Path, optional
        Ruta para persistir el listado de archivos.
    expire_after : float, optional
        Tiempo de expiración de la caché en segundos.

    Returns
    -------
    Datasource
        Objeto orquestador configurado para NCEI Archive.
    """
    # 1. Configurar caché
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedCache[list[str]](
        cache_file=cache_path_str, expire_after=expire_after
    )

    root_url = NCEI_BASE_URL.rstrip("/")
    dataset_path = dataset_path.lstrip("/")
    base_url = f"{root_url}/{dataset_path}"

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
    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )


__all__ = ["use_ncei_archive"]
