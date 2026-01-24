"""
Manage Google Cloud Storage authentication and client creation.

This module provides utilities to create Google Cloud Storage (GCS)
clients with appropriate authentication strategies. It supports creating
anonymous clients for public buckets, using explicit credentials, or
authenticating via user credentials and Application Default Credentials
(ADC).

Functions
---------
get_gcs_client(bucket, project, credentials, **kwargs)
    Create a Google Cloud Storage client.

Classes
-------
GCSAuthArgs
    Define the configuration arguments for Google Cloud Storage client.
"""

import contextlib
from typing import TYPE_CHECKING, TypedDict, Unpack

from .gutils import AuthConfig, TokenManager, authenticate_user


if TYPE_CHECKING:
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
        The authentication configuration.

    Returns
    -------
    bool
        ``True`` if the bucket is public, ``False`` otherwise.
    """
    import requests

    # Endpoint for the GCS XML API.
    url = f"https://storage.googleapis.com/{bucket}"

    with contextlib.suppress(Exception):
        # A simple request WITHOUT authorization headers determines if
        # the bucket is public.
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
        Additional arguments for the client constructor.

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
        Additional arguments for the client constructor.

    Returns
    -------
    Client
        The authenticated GCS client.
    """
    from google.cloud import storage

    client = storage.Client(project=project, credentials=credentials, **kwargs)

    # Validate credentials by making a simple call. This is necessary
    # because storage.Client is "lazy" and does not fail until a real
    # call is made.
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

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket.
    project : str | None
        The Google Cloud project ID. If not specified, the library will
        attempt to infer it from the credentials or the environment.
    credentials : Credentials | None
        Explicit credentials for authentication. If provided, these are
        used immediately without checking for public access or other
        authentication methods.
    **kwargs : Unpack[GCSAuthArgs]
        Additional arguments for the client constructor.

    Returns
    -------
    Client
        The initialized (authenticated or anonymous) GCS client.

    Notes
    -----
    This function initializes a client by determining the appropriate
    authentication method. It prioritizes explicit credentials, then
    checks for public bucket access (anonymous client), and finally
    attempts to authenticate the user or use Application Default
    Credentials.
    """
    if credentials is not None:
        return _get_gcs_default_client(
            project=project, credentials=credentials, **kwargs
        )

    if _is_public(bucket=bucket, config=_CONFIG):
        return _get_gcs_anonymous_client(project=project, **kwargs)

    # Establish user identity for private access.
    credentials = authenticate_user(
        project_id=project, config=_CONFIG, tokens=_tokens
    )

    return _get_gcs_default_client(
        project=project, credentials=credentials, **kwargs
    )


__all__ = ["get_gcs_client"]
