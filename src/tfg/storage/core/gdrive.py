import pathlib as pl
import typing as tp

from ..backend import GoogleDriveBackend
from ..cache import TimedDriveCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import GoogleDriveURIMapper
from .gdauth import get_gdrive_client

Credentials = tp.Any


def use_google_drive(
    *,
    root_path: str | None = None,
    credentials: Credentials | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a Google Drive vía API.

    Utiliza una cuenta de servicio (Service Account) para la autenticación
    y configura un mapeo de rutas POSIX sobre la estructura de archivos
    de Drive.

    Parameters
    ----------
    root_path : str, optional
        Ruta raíz dentro de Google Drive para el contexto. Si es None,
        se utiliza la raíz del Drive.
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de IDs. Si es None,
        el caché será volátil (en memoria).
    expire_after : float, optional
        Tiempo en segundos tras el cual las entradas del caché expiran.
        Si es None, el caché no expira.

    Returns
    -------
    Datasource
        Objeto orquestador configurado con el backend de Drive API.
    """
    # 1. Construcción del Cliente de API (Service)
    service = get_gdrive_client(credentials)

    # 3. Inicialización del Cache
    # Si cache_file es None, NamesCache trabajará en memoria.
    cache_path_str = str(cache_file) if cache_file else None
    drive_cache = TimedDriveCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath("/")
    mountpoint = local_root / base_path.as_posix()

    # 4. Instanciación de Protocolos (Inyección de Dependencias)
    # Ambos componentes comparten la misma instancia de 'service'.
    backend = GoogleDriveBackend(service=service, cache=drive_cache)

    mapper = GoogleDriveURIMapper(service=service, cache=drive_cache)

    # 6. Retorno del Datasource Orquestador
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=drive_cache,
    )
