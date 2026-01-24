"""
Manage Google Cloud Storage authentication and client creation.

This module provides utilities to create Google Cloud Storage (GCS)
clients with appropriate authentication strategies. It supports creating
anonymous clients for public buckets, using explicit credentials, or
authenticating via user credentials and Application Default Credentials
(ADC).

Functions
---------
get_gcs_client
    Create a Google Cloud Storage client.

Classes
-------
GCSAuthArgs
    Define the configuration arguments for Google Cloud Storage client.
"""

import contextlib
import typing
from typing import TypedDict, Unpack

from .gutils import AuthConfig, TokenManager, authenticate_user


if typing.TYPE_CHECKING:
    from google.api_core.client_info import ClientInfo
    from google.api_core.client_options import ClientOptions
    from google.auth.credentials import Credentials
    from google.cloud.storage.client import Client
    from requests import Session


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


class GCSAuthArgs(TypedDict, total=False):
    """
    Define the configuration arguments for Google Cloud Storage client.

    Provide the set of optional keys accepted by functions that build
    a `storage.Client`. All keys are optional; the TypedDict is
    non-total.

    Attributes
    ----------
    client_info : ClientInfo | None
        Information about the client library.
    client_options : ClientOptions | None
        Client options including the API endpoint and other settings.
    use_auth_w_custom_endpoint : bool
        Whether to send credentials when using a custom endpoint.
    extra_headers : dict[str, str]
        Additional HTTP headers to include in requests.
    api_key : str | None
        The API key to use for authentication.
    """

    _http: "Session | None"
    client_info: "ClientInfo | None"
    client_options: "ClientOptions | None"
    use_auth_w_custom_endpoint: bool
    extra_headers: dict[str, str]
    api_key: str | None


def _is_public(bucket: str, config: AuthConfig) -> bool:
    """
    Check if a Google Cloud Storage bucket is publicly accessible.

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket to check.
    config : AuthConfig
        The authentication configuration containing timeout settings.

    Returns
    -------
    bool
        True if the bucket is public (HTTP 200 OK), False otherwise.
    """
    import requests

    # Endpoint de la API XML de GCS para el bucket
    url = f"https://storage.googleapis.com/{bucket}"

    with contextlib.suppress(Exception):
        # Petición simple SIN cabeceras de autorización
        response = requests.get(url, timeout=config.timeout)
        return response.status_code == HTTP_200_OK

    return False


def _get_gcs_anonymous_client(
    project: str | None, **kwargs: Unpack[GCSAuthArgs]
) -> "Client":
    """
    Create an anonymous Google Cloud Storage client.

    Parameters
    ----------
    project : str | None
        The Google Cloud project ID. If not specified, the library will
        attempt to infer it from the environment.
    **kwargs : Unpack[GCSAuthArgs]
        Additional arguments for `storage.Client`. See `GCSAuthArgs`
        for details.

    Returns
    -------
    Client
        The anonymous GCS client.
    """
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import storage

    if project is not None:
        return storage.Client(
            project=project, credentials=AnonymousCredentials(), **kwargs
        )

    return storage.Client.create_anonymous_client()


def _get_gcs_default_client(
    project: str | None,
    credentials: "Credentials | None",
    **kwargs: Unpack[GCSAuthArgs],
) -> "Client":
    """
    Create a Google Cloud Storage client with specified credentials.

    Parameters
    ----------
    project : str | None
        The Google Cloud project ID. If not specified, the library will
        attempt to infer it from the credentials or the environment.
    credentials : Credentials | None
        Explicit credentials for authentication. If provided, they are
        used instead of the default Application Default Credentials.
    **kwargs : Unpack[GCSAuthArgs]
        Additional arguments for `storage.Client`. See `GCSAuthArgs`
        for details.

    Returns
    -------
    Client
        The authenticated GCS client.
    """
    from google.cloud import storage

    client = storage.Client(project=project, credentials=credentials, **kwargs)

    # Validar credenciales haciendo una llamada simple. Esto es
    # necesario porque storage.Client es "lazy" y no falla hasta
    # que se hace una llamada real.
    _ = list(client.list_buckets())

    return client


def get_gcs_client(
    bucket: str,
    project: str | None,
    credentials: "Credentials | None",
    **kwargs: Unpack[GCSAuthArgs],
) -> "Client":
    """
    Create a Google Cloud Storage client.

    This function initializes a client by determining the appropriate
    authentication method. It prioritizes explicit credentials, then
    checks for public bucket access (anonymous client), and finally
    attempts to authenticate the user or use Application Default
    Credentials.

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket. This is used to check if the bucket
        is publicly accessible.
    project : str | None
        The Google Cloud project ID. If not specified, the library will
        attempt to infer it from the credentials or the environment.
    credentials : Credentials | None
        Explicit credentials for authentication. If provided, these are
        used immediately without checking for public access or other
        authentication methods.
    **kwargs : Unpack[GCSAuthArgs]
        Additional arguments passed to the `storage.Client` constructor.
        See `GCSAuthArgs` for available options.

    Returns
    -------
    Client
        The initialized (authenticated or anonymous) GCS client.
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


__all__ = ["get_gcs_client"]
