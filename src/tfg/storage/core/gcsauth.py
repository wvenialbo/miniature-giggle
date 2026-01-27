"""
Provide Google Cloud Storage authentication and client creation.

This module provides utilities to create Google Cloud Storage clients
with appropriate authentication strategies. It supports creating
anonymous clients for public buckets, using explicit credentials, or
authenticating via user credentials and Application Default Credentials.

Functions
---------
get_gcs_client(bucket, project, credentials, **kwargs)
    Create a Google Cloud Storage client.

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
    Define the configuration arguments for Google Cloud Storage clients.

    Attributes
    ----------
    client_info : ClientInfo | None, optional
        The information about the client library.
    client_options : ClientOptions | None, optional
        The client options including the API endpoint and other
        settings.
    use_auth_w_custom_endpoint : bool, optional
        The flag indicating whether to send credentials when using a
        custom endpoint.
    extra_headers : dict[str, str], optional
        The additional HTTP headers to include in requests.
    api_key : str | None, optional
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
        The name of the Google Cloud Storage bucket to check.
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
    project : str | None, optional
        The Google Cloud project ID.
    **kwargs : Unpack[GCSAuthArgs]
        The additional keyword arguments for the client constructor.

    Returns
    -------
    Client
        The anonymous Google Cloud Storage client.
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
    project : str | None, optional
        The Google Cloud project ID.
    credentials : Credentials | None, optional
        The explicit credentials for authentication.
    **kwargs : Unpack[GCSAuthArgs]
        The additional keyword arguments for the client constructor.

    Returns
    -------
    Client
        The authenticated Google Cloud Storage client.
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

    This function provides a unified interface for creating Google Cloud
    Storage (GCS) clients, handling the transition from public to
    private access seamlessly. It abstracts the complexity of credential
    discovery and provides support for various authentication flows
    based on the bucket accessibility and provided credentials.

    Parameters
    ----------
    bucket : str
        The name of the GCS bucket.
    project : str | None, optional
        The Google Cloud project ID.
    credentials : Credentials | None, optional
        The explicit credentials for authentication.
    **kwargs : Unpack[GCSAuthArgs]
        The additional keyword arguments for the client constructor.

    Returns
    -------
    Client
        The initialized authenticated or anonymous GCS client.

    Notes
    -----
    This function initializes a client by determining the appropriate
    authentication method. It prioritizes explicit credentials, then
    checks for public bucket access (anonymous client), and finally
    attempts to authenticate the user or use Application Default
    Credentials (ADC).

    Examples
    --------
    Create a client for a public Google Cloud Storage bucket:

    >>> from tfg.storage.core.gcsauth import get_gcs_client
    >>> client = get_gcs_client(
    ...     bucket="public-bucket",
    ...     project=None,
    ...     credentials=None,
    ... )  # doctest: +SKIP
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
