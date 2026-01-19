import pathlib as pl
import typing as tp

from google.auth.credentials import AnonymousCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage

from ..backend import GCSBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import GCSURIMapper

POSIX_PREFIX = "/"


def _get_gcs_anonymous_client(
    project_id: str | None = None,
) -> storage.Client:
    """
    Crea un cliente anónimo de Google Cloud Storage.

    Parameters
    ----------
    project_id : str, optional
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo del entorno.

    Returns
    -------
    storage.Client
        Cliente anónimo de GCS.
    """
    if project_id is not None:
        return storage.Client(
            project=project_id, credentials=AnonymousCredentials()
        )
    return storage.Client.create_anonymous_client()


def _get_gcs_default_client(
    project_id: str | None = None,
    **client_kwargs: tp.Any,
) -> storage.Client:
    """
    Crea un cliente de Google Cloud Storage usando credenciales por
    defecto o las pasadas en client_kwargs.

    Parameters
    ----------
    project_id : str, optional
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    **client_kwargs : Any
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente de GCS autenticado.
    """
    return storage.Client(project=project_id, **client_kwargs)


def _get_gcs_client(
    project_id: str | None = None,
    **client_kwargs: tp.Any,
) -> storage.Client:
    """
    Crea un cliente de Google Cloud Storage, intentando primero con
    credenciales por defecto y haciendo fallback a un cliente anónimo
    si no se encuentran credenciales.

    Parameters
    ----------
    project_id : str, optional
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    **client_kwargs : Any
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente de GCS (autenticado o anónimo).
    """
    # Se instancia el cliente nativo usando el project_id y
    # argumentos extra como credenciales explícitas si se proveen.
    try:
        # Intentamos instanciar el cliente "normal" (usa las
        # credenciales provistas o busca las ADC del entorno).
        print("intentando credenciales normales")
        return _get_gcs_default_client(
            project_id,
            **client_kwargs,
        )
    except DefaultCredentialsError:
        # Si falla porque no hay credenciales, verificamos si el usuario
        # intentó pasar credenciales explícitas que fallaron.
        if "credentials" in client_kwargs:
            # Si el usuario pasó credenciales y fallaron, relanzamos el
            # error.
            raise
        # Si no pasó credenciales explícitas, asumimos que quiere acceso
        # público.
        print("usando credenciales anónimas")
        return _get_gcs_anonymous_client(
            project_id,
        )


def use_gcs_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    project_id: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
    **client_kwargs: tp.Any,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a Google Cloud Storage.

    Configura un backend de almacenamiento GCS con un mapeador
    determinista y optimización de listado mediante caché de escaneo.

    Soporta autenticación mediante Application Default Credentials (ADC)
    o parámetros explícitos.

    Manejo de Autenticación:
        1. Intenta usar credenciales por defecto (ADC) o las pasadas en
           client_kwargs.
        2. Si no encuentra credenciales, hace fallback automático a un
           cliente ANÓNIMO (útil para buckets públicos como
           gcp-public-data).

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
    client = _get_gcs_client(project=project_id, **client_kwargs)

    # 2. Inicialización de la Caché de Listado (ScanCache)
    #    GCS se beneficia de ScanCache para evitar listar buckets
    #    grandes repetidamente.
    cache_path_str = str(cache_file) if cache_file else None
    scan_cache = TimedScanCache(
        cache_file=cache_path_str, expire_after=expire_after
    )

    # 3. Resolución de Rutas (Lógica Simétrica a AWS)
    #    Resolvemos el base_path relativo a la raíz lógica para calcular
    #    el punto de montaje exacto.
    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath(POSIX_PREFIX)
    mountpoint = local_root / base_path.as_posix()

    # 4. Instanciación de componentes
    #    El Mapper es determinista: solo necesita saber el bucket
    mapper = GCSURIMapper(bucket=bucket)

    #    El Backend recibe el cliente instanciado y la caché de escaneo
    backend = GCSBackend(
        bucket=bucket,
        client=client,
        scan_cache=scan_cache,
    )

    # 6. Retorno del Orquestador
    #    Pasamos scan_cache como la caché principal del Datasource
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=scan_cache,
    )
