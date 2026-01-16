import pathlib as pl
import typing as tp

import boto3
from botocore import UNSIGNED
from botocore.config import Config

from ..backend import AWSBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import AWSURIMapper
from .handlers import get_file_handlers

S3_PREFIX = "s3://"
POSIX_PREFIX = "/"


def use_aws_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    profile_name: str | None = None,
    region_name: str | None = None,
    cache_file: str | pl.Path | None = None,
    handlers: list[DataHandler] | None = None,
    expire_after: float | None = None,
    **session_kwargs: tp.Any,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a AWS S3.

    Configura un backend de objetos S3 con un mapeador determinista y
    optimización de listado mediante caché de escaneo.  Soporta acceso
    autenticado y anónimo (público).

    Parameters
    ----------
    bucket : str
        Nombre del bucket de S3.
    root_path : str, optional
        Prefijo raíz dentro del bucket para este Datasource.  Por
        defecto None (raíz del bucket).
    profile_name : str, optional
        Nombre del perfil de AWS configurado en la máquina local.
    region_name : str, optional
        Región de AWS (ej: 'us-east-1').
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de las operaciones
        'scan'.  Crucial para buckets con miles de objetos.
    handlers : list[DataHandler], optional
        Lista de handlers personalizados. Si es None, se cargan los por
        defecto.
    expire_after : float, optional
        Tiempo en segundos tras el cual expira la caché de escaneo. Si es
        None, la caché no expira automáticamente.
    **session_kwargs : Any
        Argumentos adicionales para boto3.Session (aws_access_key_id,
        etc.)

    Returns
    -------
    DatasourceContract
        Objeto orquestador configurado para AWS S3.
    """
    # 1. Configuración de la Sesión de AWS y del cliente S3
    # Acceso Anónimo vs Autenticado: Esto permite flexibilidad total,
    # desde perfiles hasta llaves directas

    # 1.1. Intentar crear sesión con lo que haya
    session = boto3.Session(
        profile_name=profile_name, region_name=region_name, **session_kwargs
    )
    creds = session.get_credentials()

    # 1.2. Determinar si debemos usar modo UNSIGNED
    if creds is None:
        # Si no hay credenciales en la sesión Y no se pasaron
        # argumentos, es anónimo.
        if profile_name or session_kwargs:
            raise ValueError(
                "No se pudieron obtener credenciales de AWS. "
                "Por favor, revise la configuración de su perfil o las "
                "credenciales proporcionadas."
            )
        # Configuración UNSIGNED para acceso público sin credenciales
        config = Config(signature_version=UNSIGNED)
        # Forzamos una sesión vacía para evitar que boto3 busque
        # archivos config
        session = boto3.Session(region_name=region_name)

    else:
        config = None

    s3_client = session.client("s3", config=config)

    # 2. Inicialización de la Caché de Listado (ScanCache)
    # S3 no necesita DriveCache (IDs), pero se beneficia enormemente de
    # ScanCache
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedScanCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath(POSIX_PREFIX)
    mountpoint = local_root / base_path.as_posix()

    # 3. Instanciación de componentes
    # El Mapper es determinista: solo necesita saber el bucket y el
    # prefijo
    mapper = AWSURIMapper(bucket=bucket)

    # El Backend recibe la sesión y la caché de escaneo
    backend = AWSBackend(
        bucket=bucket,
        client=s3_client,
        scan_cache=scan_cache,
        config=config,
    )

    # 4. Configuración de Handlers
    if handlers is None:
        handlers = get_file_handlers()

    # 5. Retorno del Orquestador
    # Pasamos scan_cache como la caché principal del Datasource
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        handlers=handlers,
        cache=scan_cache,
    )
