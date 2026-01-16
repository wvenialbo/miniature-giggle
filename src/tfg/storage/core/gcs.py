import pathlib as pl
import typing as tp

from google.cloud import storage

from ..backend import GCSBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import GCSURIMapper
from .handlers import get_file_handlers

POSIX_PREFIX = "/"


def use_gcs_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    project_id: str | None = None,
    cache_file: str | pl.Path | None = None,
    handlers: list[DataHandler] | None = None,
    expire_after: float | None = None,
    **client_kwargs: tp.Any,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a Google Cloud Storage.

    Configura un backend de almacenamiento GCS con un mapeador
    determinista y optimización de listado mediante caché de escaneo.
    Soporta autenticación mediante Application Default Credentials (ADC)
    o parámetros explícitos.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de GCS.
    root_path : str, optional
        Prefijo raíz dentro del bucket para este Datasource. Por defecto
        None (raíz del bucket).
    project_id : str, optional
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de las operaciones
        'scan'. Crucial para buckets con miles de objetos para evitar
        latencia y costes de API.
    handlers : list[DataHandler], optional
        Lista de handlers personalizados. Si es None, se cargan los por
        defecto.
    expire_after : float, optional
        Tiempo en segundos tras el cual expira la caché de escaneo. Si
        es None, la caché no expira automáticamente.
    **client_kwargs : Any
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    DatasourceContract
        Objeto orquestador configurado para Google Cloud Storage.
    """
    # 1. Configuración del cliente de GCS
    # Se instancia el cliente nativo usando el project_id y argumentos extra
    # como credenciales explícitas si se proveen.
    client = storage.Client(project=project_id, **client_kwargs)

    # 2. Inicialización de la Caché de Listado (ScanCache)
    # GCS se beneficia de ScanCache para evitar listar buckets grandes
    # repetidamente.
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedScanCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    # 3. Resolución de Rutas (Lógica Simétrica a AWS)
    # Resolvemos el base_path relativo a la raíz lógica para calcular
    # el punto de montaje exacto.
    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath(POSIX_PREFIX)
    mountpoint = local_root / base_path.as_posix()

    # 4. Instanciación de componentes
    # El Mapper es determinista: solo necesita saber el bucket
    mapper = GCSURIMapper(bucket=bucket)

    # El Backend recibe el cliente instanciado y la caché de escaneo
    backend = GCSBackend(
        bucket=bucket,
        client=client,
        scan_cache=scan_cache,
    )

    # 5. Configuración de Handlers
    if handlers is None:
        handlers = get_file_handlers()

    # 6. Retorno del Orquestador
    # Pasamos scan_cache como la caché principal del Datasource
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        handlers=handlers,
        cache=scan_cache,
    )
