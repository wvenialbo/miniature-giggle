"""
Provide Google Drive authentication helpers.

Offer utilities to create an authorized Google Drive API
service client and manage the authentication configuration and
runtime token manager. The module exposes `get_gdrive_client`
for public consumption and an internal helper
`_get_gdrive_default_client`.

Functions
---------
get_gdrive_client(credentials)
    Create and return an authorized Google Drive API client.

_get_gdrive_default_client(credentials)
    Build the Drive service and validate credentials with a
    minimal request.

"""

import typing as tp

from .gutils import AuthConfig, TokenManager, authenticate_user


if tp.TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from googleapiclient._apis.drive.v3.resources import DriveResource


_CONFIG = AuthConfig(
    (
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
    ),
    "gdrive.json",
)
_tokens = TokenManager(_CONFIG)


def _get_gdrive_default_client(credentials: "Credentials") -> "DriveResource":
    """
    Create a default Google Drive API service client.

    Build and return an authorized Google Drive ``Drive`` service using
    the provided `credentials`. A lightweight request is executed to
    validate that the credentials are usable and that token refresh
    behavior is correct before returning the service.

    Parameters
    ----------
    credentials : Credentials
        The OAuth2 credentials to use for the API client.

    Returns
    -------
    DriveResource
        An authorized Google Drive API service client.
    """
    from googleapiclient import discovery

    # Construcción del cliente de API (Service)
    # cache_discovery=False evita advertencias en ciertos entornos y
    # mejora el tiempo de inicio en implementaciones stateless.
    service = discovery.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )

    # Validar credenciales haciendo una llamada simple. Esto es
    # necesario porque al usar discovery.build, a veces el objeto
    # credentials puede quedar en un estado donde el token está presente
    # pero la librería no detecta que debe refrescarlo automáticamente
    # antes de la llamada.
    _ = service.files().list(pageSize=1, fields="files(id)").execute()

    return service


def get_gdrive_client(credentials: "Credentials | None") -> "DriveResource":
    """Create and return a Google Drive API client.

    If `credentials` are not provided, this function will attempt to
    authenticate the user using the default configuration.

    Parameters
    ----------
    credentials : google.auth.credentials.Credentials | None
        The OAuth 2.0 credentials to use for the client. If `None`,
        user authentication will be initiated.

    Returns
    -------
    DriveResource
        An authorized Google Drive API service client.
    """
    if not credentials:
        credentials = authenticate_user(
            project_id=None, config=_CONFIG, tokens=_tokens
        )
    return _get_gdrive_default_client(credentials=credentials)


__all__ = ["get_gdrive_client"]
