import pathlib as pl
import typing as tp

import boto3

from ..backend import AWSBackend
from ..cache import ScanCache, TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import AWSURIMapper
from .handlers import get_file_handlers


def use_aws(
    *,
    bucket: str,
    base_prefix: str = "",
    profile_name: str | None = None,
    region_name: str | None = None,
    cache_file: str | pl.Path | None = None,
    mountpoint: str = "s3://",
    handlers: list[DataHandler] | None = None,
    expire_after: float | None = None,
    **session_kwargs: tp.Any,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a AWS S3.

    Configura un backend de objetos S3 con un mapeador determinista y
    optimización de listado mediante caché de escaneo.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de S3.
    base_prefix : str, optional
        Prefijo raíz dentro del bucket para este Datasource.
        Por defecto "" (raíz del bucket).
    profile_name : str, optional
        Nombre del perfil de AWS configurado en la máquina local.
    region_name : str, optional
        Región de AWS (ej: 'us-east-1').
    scan_cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de las operaciones 'scan'.
        Crucial para buckets con miles de objetos.
    mountpoint : str, optional
        Identificador lógico para el punto de montaje. Por defecto "s3://".
    handlers : list[DataHandler], optional
        Lista de handlers personalizados. Si es None, se cargan los por defecto.
    **session_kwargs : Any
        Argumentos adicionales para boto3.Session (aws_access_key_id, etc.)

    Returns
    -------
    DatasourceContract
        Objeto orquestador configurado para AWS S3.
    """

    # 1. Configuración de la Sesión de AWS
    # Esto permite flexibilidad total: desde perfiles hasta llaves
    # directas
    session = boto3.Session(
        profile_name=profile_name, region_name=region_name, **session_kwargs
    )

    # 2. Inicialización de la Caché de Listado (ScanCache)
    # S3 no necesita DriveCache (IDs), pero se beneficia enormemente de
    # ScanCache
    cache_path_str = str(cache_file) if cache_file else None

    if expire_after is not None:
        scan_cache = TimedScanCache(
            cache_file=cache_path_str, expire_after=expire_after
        )
    else:
        scan_cache = ScanCache(cache_file=cache_path_str)

    # 3. Instanciación de componentes
    # El Mapper es determinista: solo necesita saber el bucket y el
    # prefijo
    mapper = AWSURIMapper(bucket=bucket, base_prefix=base_prefix)

    # El Backend recibe la sesión y la caché de escaneo
    backend = AWSBackend(bucket=bucket, session=session, scan_cache=scan_cache)

    # 4. Configuración de Handlers
    if handlers is None:
        handlers = get_file_handlers()

    # 5. Retorno del Orquestador
    # Pasamos s3_scan_cache como la caché principal del Datasource
    return Datasource(
        mountpoint=mountpoint,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
        cache=scan_cache,
    )
