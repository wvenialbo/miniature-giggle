import os
import pathlib as pl
import typing as tp

from google.auth.credentials import AnonymousCredentials
from google.auth.exceptions import RefreshError
from google.cloud import storage  # type: ignore

from ..backend import GCSBackend
from ..cache import TimedScanCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import GCSURIMapper

try:
    from google.colab import auth

    def _authenticate_user(project_id: str | None = None) -> None:
        """
        Autentica el usuario en Google Colab para acceder a GCS.

        Parameters
        ----------
        project_id : str, optional
            ID del proyecto de Google Cloud. No es obligatorio.

        Returns
        -------
        None
        """
        auth.authenticate_user(project_id=project_id)

    def running_on_colab() -> bool:
        return bool(os.getenv("COLAB_RELEASE_TAG"))

except ImportError:

    def _authenticate_user(project_id: str | None = None) -> None:
        # No-op function for environments outside Google Colab.
        pass

    def running_on_colab() -> bool:
        return False


POSIX_PREFIX = "/"


def _get_gcs_anonymous_client(
    project: str | None, **client_kwargs: tp.Any
) -> storage.Client:
    """
    Crea un cliente anónimo de Google Cloud Storage.

    Parameters
    ----------
    project : str, optional
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo del entorno.

    Returns
    -------
    storage.Client
        Cliente anónimo de GCS.
    """
    if project is not None:
        print("intentando credenciales anónimas")
        return storage.Client(
            project=project,
            credentials=AnonymousCredentials(),
            **client_kwargs,
        )
    print("usando credenciales anónimas")
    return storage.Client.create_anonymous_client()


def _get_gcs_default_client(
    project: str | None, **client_kwargs: tp.Any
) -> storage.Client:
    """
    Crea un cliente de Google Cloud Storage usando credenciales por
    defecto o las pasadas en client_kwargs.

    Parameters
    ----------
    project : str, optional
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
    print("intentando credenciales normales")
    client = storage.Client(project=project, **client_kwargs)
    _: list[tp.Any] = list(client.list_buckets())
    return client


def _get_gcs_client(
    project: str | None, **client_kwargs: tp.Any
) -> storage.Client:
    """
    Crea un cliente de Google Cloud Storage.

    Intentando primero con credenciales por defecto y haciendo fallback
    a un cliente anónimo si no se encuentran credenciales.

    En Colab, para buckets públicos, fuerza credenciales anónimas.

    Parameters
    ----------
    project : str, optional
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
    # Si el usuario pasó credenciales explícitas, confiar en ellas; usar
    # las credenciales provistas.
    if "credentials" in client_kwargs:
        return _get_gcs_default_client(project=project, **client_kwargs)

    # Forzar autenticación de usuario (no anónimo), si el usuario se
    # rehusa a autenticarse, caerá en un sesión anónima.
    _authenticate_user(project_id=project)

    # Si no hay credenciales explícitas, se instancia el cliente nativo
    # usando el `project` y argumentos extra.
    try:
        # Intentamos instanciar el cliente con credenciales por defecto;
        # busca las ADC del entorno.
        return _get_gcs_default_client(project=project, **client_kwargs)

    except RefreshError:

        # Asumimos que el usuario quiere acceso público.
        return _get_gcs_anonymous_client(project=project, **client_kwargs)


def use_gcs_cloud(
    *,
    bucket: str,
    root_path: str | None = None,
    project: str | None = None,
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
    project : str, optional
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
    print(project)
    print(client_kwargs)
    # 1. Configuración del cliente de GCS
    client = _get_gcs_client(project=project, **client_kwargs)

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
