import pathlib as pl
import typing as tp

from ..backend import GoogleDriveBackend
from ..cache import TimedDriveCache, TimedScanCache
from ..cache.gdrive import GoogleDriveCacheWrapper
from ..datasource import DataService, Datasource
from ..mapper import GoogleDriveURIMapper
from .gdauth import get_gdrive_client


if tp.TYPE_CHECKING:
    from google.auth.credentials import Credentials


def use_google_drive(
    *,
    root_path: str | None = None,
    credentials: "Credentials | None" = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> Datasource:
    """
    Crea un contexto de Datasource conectado a Google Drive vía API.

    Utiliza una cuenta de servicio (Service Account) para la
    autenticación y configura un mapeo de rutas POSIX sobre la
    estructura de archivos de Drive.

    Parameters
    ----------
    root_path : str, optional
        Ruta raíz dentro de Google Drive para el contexto. Si es None,
        se utiliza la raíz del Drive.
    credentials: Credentials | None, optional
        Credenciales para autenticación. Si es None, se usan las
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de IDs. Si es None, el
        caché será volátil (en memoria).
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

    # 2. Preparación de Rutas de Caché
    def path_str(path: pl.Path, suffix: str) -> str | None:
        return str(path.with_name(f"{path.stem}{suffix}{path.suffix}"))

    drive_path: str | None = None
    scan_path: str | None = None

    if cache_file is not None:
        cache_file = pl.Path(cache_file)
        drive_path = path_str(cache_file, "-id")
        scan_path = path_str(cache_file, "-index")

    # 3. Inicialización del Cache
    drive_cache = TimedDriveCache(
        cache_file=drive_path, expire_after=expire_after
    )
    scan_cache = TimedScanCache(
        cache_file=scan_path, expire_after=expire_after
    )
    gdrive_cache = GoogleDriveCacheWrapper(
        drive_cache=drive_cache,
        scan_cache=scan_cache,
    )

    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath("/")
    mountpoint = local_root / base_path.as_posix()

    # 4. Instanciación de Protocolos (Inyección de Dependencias)
    # Ambos componentes comparten la misma instancia de 'service'.
    backend = GoogleDriveBackend(
        service=service, drive_cache=drive_cache, scan_cache=scan_cache
    )

    mapper = GoogleDriveURIMapper(service=service, drive_cache=drive_cache)

    # 6. Retorno del Datasource Orquestador
    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=gdrive_cache,
    )
