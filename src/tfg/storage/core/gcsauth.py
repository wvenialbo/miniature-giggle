import contextlib
import typing as tp

from .gutils import AuthConfig, TokenManager, authenticate_user


if tp.TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from google.cloud.storage.client import Client


_CONFIG = AuthConfig(
    (
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/cloud-platform",
    ),
    "gcloud.json",
)
_tokens = TokenManager(_CONFIG)

HTTP_200_OK = 200


def _is_public(bucket: str, config: AuthConfig) -> bool:
    import requests

    # Endpoint de la API XML de GCS para el bucket
    url = f"https://storage.googleapis.com/{bucket}"

    with contextlib.suppress(Exception):
        # Petición simple SIN cabeceras de autorización
        response = requests.get(url, timeout=config.timeout)
        return response.status_code == HTTP_200_OK

    return False


def _get_gcs_anonymous_client(
    project: str | None, **kwargs: object | str | bool | None
) -> "Client":
    """
    Crea un cliente anónimo de Google Cloud Storage.

    Parameters
    ----------
    project : str | None
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo del entorno.
    **client_kwargs : object | str | bool | None
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente anónimo de GCS.
    """
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import storage

    client_kwargs: dict[str, tp.Any] = kwargs
    if project is not None:
        return storage.Client(
            project=project,
            credentials=AnonymousCredentials(),
            **client_kwargs,
        )
    return storage.Client.create_anonymous_client()


def _get_gcs_default_client(
    project: str | None,
    credentials: "Credentials | None",
    **kwargs: object | str | bool | None,
) -> "Client":
    """
    Crea un cliente de Google Cloud Storage.

    Parameters
    ----------
    project : str | None
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    credentials: Credentials | None, optional
        Credenciales explícitas para autenticación. Si se proporcionan,
        se usan en lugar de las ADC.
    **kwargs : object | str | bool | None
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente de GCS autenticado.
    """
    from google.cloud import storage

    client_kwargs: dict[str, tp.Any] = kwargs
    client = storage.Client(
        project=project, credentials=credentials, **client_kwargs
    )

    # Validar credenciales haciendo una llamada simple. Esto es
    # necesario porque storage.Client es "lazy" y no falla hasta
    # que se hace una llamada real.
    _: list[tp.Any] = list(client.list_buckets())

    return client


def get_gcs_client(
    bucket: str,
    project: str | None,
    credentials: "Credentials | None",
    **kwargs: object | str | bool | None,
) -> "Client":
    """
    Crea un cliente de Google Cloud Storage.

    Intentando primero con credenciales por defecto y haciendo fallback
    a un cliente anónimo si no se encuentran credenciales.

    En Colab, para buckets públicos, fuerza credenciales anónimas.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de GCS.
    project : str | None
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    credentials: Credentials | None, optional
        Credenciales explícitas para autenticación. Si se proporcionan,
        se usan en lugar de las ADC.
    **kwargs : object | str | bool | None
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente de GCS (autenticado o anónimo).
    """
    # Si se proveyeron, usamos las credenciales del usuario.
    if credentials is not None:
        return _get_gcs_default_client(
            project=project, credentials=credentials, **kwargs
        )

    # Para buckets públicos, usamos un cliente anónimo.
    if _is_public(bucket=bucket, config=_CONFIG):
        return _get_gcs_anonymous_client(project=project, **kwargs)

    # Si se proveyeron credenciales explícitas y el bucket no es
    # público, forzamos autenticación de usuario (no anónimo).
    credentials = authenticate_user(
        project_id=project, config=_CONFIG, tokens=_tokens
    )

    # Intentamos instanciar el cliente con credenciales por defecto;
    # busca las ADC del entorno.
    return _get_gcs_default_client(
        project=project, credentials=credentials, **kwargs
    )
