import pathlib as pl
import typing as tp

from ..backend import AWSBackend
from ..cache import TimedScanCache
from ..datasource import DataService, Datasource
from ..mapper import AWSURIMapper


if tp.TYPE_CHECKING:
    from boto3 import Session
    from botocore.config import Config
    from mypy_boto3_s3.client import S3Client as Client


S3_PREFIX = "s3://"
POSIX_PREFIX = "/"


def _get_s3_client(
    profile_name: str | None = None,
    region_name: str | None = None,
    **kwargs: "Session | str | None",
) -> "tuple[Client, Config | None]":
    """
    Crea un cliente de S3 para acceso autenticado o anónimo.

    Parameters
    ----------
    profile_name : str, optional
        Nombre del perfil de AWS configurado en la máquina local.
    region_name : str, optional
        Región de AWS (ej: 'us-east-1').
    **kwargs : "Session | str | None"
        Argumentos adicionales para boto3.Session (aws_access_key_id,
        etc.)

    Returns
    -------
    boto3.client
        Cliente de S3 configurado.

    Raises
    ------
    ValueError
        Si no se pueden obtener credenciales de AWS cuando se espera
        acceso autenticado.
    """
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    session_kwargs: dict[str, tp.Any] = kwargs

    # 1. Intentar crear sesión con lo que haya
    session = boto3.Session(
        profile_name=profile_name, region_name=region_name, **session_kwargs
    )
    creds = session.get_credentials()

    # 2. Determinar si debemos usar modo UNSIGNED
    if creds is None:
        # Si no hay credenciales en la sesión Y no se pasaron
        # argumentos, es anónimo.
        if profile_name or session_kwargs:
            raise ValueError(
                "No se pudieron obtener credenciales de AWS. "
                "Por favor, revise la configuración de su perfil "
                "o las credenciales proporcionadas."
            )
        # Configuración UNSIGNED para acceso público sin credenciales
        config = Config(signature_version=UNSIGNED)
        # Forzamos una sesión vacía para evitar que boto3 busque
        # archivos config
        session = boto3.Session(region_name=region_name)

    else:
        config = None

    return session.client("s3", config=config), config


def use_aws_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
    **kwargs: "Session | str | None",
) -> Datasource:
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
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de las operaciones
        'scan'.  Crucial para buckets con miles de objetos.
    expire_after : float, optional
        Tiempo en segundos tras el cual expira la caché de escaneo. Si
        es None, la caché no expira automáticamente.
    **kwargs : Session | str | None
        Argumentos adicionales para boto3.Session (profile_name,
        region_name, aws_access_key_id, etc.)

    Returns
    -------
    DatasourceContract
        Objeto orquestador configurado para AWS S3.
    """
    # 1. Configuración de la Sesión de AWS y del cliente S3
    # Acceso Anónimo vs Autenticado: Esto permite flexibilidad total,
    # desde perfiles hasta llaves directas
    session_kwargs: dict[str, tp.Any] = kwargs
    client, config = _get_s3_client(
        **session_kwargs,
    )

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
        client=client,
        scan_cache=scan_cache,
        config=config,
    )

    # 5. Retorno del Orquestador
    # Pasamos scan_cache como la caché principal del Datasource
    return DataService(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )
