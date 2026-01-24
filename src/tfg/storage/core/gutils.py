"""
Manage Google Cloud authentication and credentials.

This module provides utilities to manage authentication credentials for
Google Cloud services. It handles token storage, retrieval, and various
authentication flows including persistent tokens, Application Default
Credentials (ADC), and interactive flows for local and Colab
environments.

Classes
-------
AuthConfig
    Configuration for authentication parameters.
TokenManager
    Manage storage and retrieval of authentication tokens.

Exceptions
----------
ClientConfigurationNotFoundError
    Raise when the client configuration file is not found.

Functions
---------
authenticate_user(project_id, config, tokens)
    Authenticate the user and obtain valid credentials.
"""

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeGuard

from ... import __package_id__, __package_root__
from ...utils import running_on_colab, running_on_notebook


if TYPE_CHECKING:
    from google.auth.credentials import Credentials as AuthCredentials
    from google.oauth2.credentials import Credentials as OAuthCredentials


_CLIENT_ID = (
    "794699822558-9h359ba9l0cagh0avgk3ph86ptn92sce.apps.googleusercontent.com"
)
_CLIENT_KEY = "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"

_CLIENT_CONFIG = {
    "installed": {
        "client_id": _CLIENT_ID,
        "project_id": "goes-dl",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": (
            "https://www.googleapis.com/oauth2/v1/certs"
        ),
        "client_secret": _CLIENT_KEY,
        "redirect_uris": ["http://localhost"],
    }
}


class ClientConfigurationNotFoundError(Exception):
    """Raise when the client configuration file is not found."""

    pass


@dataclass(frozen=True)
class AuthConfig:
    """
    Configuration for authentication parameters.

    Attributes
    ----------
    scopes : tuple[str, ...]
        The list of OAuth 2.0 scopes required for the application.
    token_name : str
        The name of the file to store the authentication token.
    app_name : str, default=`__package_root__`
        The name of the application, used for directory resolution.
    app_author : str, default=`__package_id__`
        The author of the application, used for directory resolution.
    config_name : str, default='client_info.json'
        The name of the client secrets file.
    config_package : str, default='tfg.config'
        The package where the client secrets file is located.
    timeout : int, default=60
        Timeout for network requests in seconds.
    """

    scopes: tuple[str, ...]
    token_name: str
    app_name: str = __package_root__
    app_author: str = __package_id__
    config_name: str = "client_info.json"
    config_package: str = "tfg.config"
    timeout: int = 60

    @property
    def token_path(self) -> Path:
        """
        Get the path to the stored token file.

        Returns
        -------
        pathlib.Path
            The full path to the token file in the user data directory.
        """
        from platformdirs import user_data_dir

        path = Path(user_data_dir(self.app_name, self.app_author))
        return path / self.token_name


class TokenManager:
    """
    Manage storage and retrieval of authentication tokens.

    This class handles the file system interactions for saving and
    loading OAuth2 credentials locally.

    Parameters
    ----------
    config : AuthConfig
        Configuration containing authentication parameters.

    Methods
    -------
    load()
        Load stored credentials from the file system.
    save(credentials)
        Save credentials to the file system.
    """

    def __init__(self, config: AuthConfig) -> None:
        self.config = config

    def load(self) -> "OAuthCredentials | None":
        """
        Load stored credentials from the file system.

        Returns
        -------
        OAuthCredentials | None
            Loaded credentials if found and valid, otherwise ``None``.
        """
        from google.oauth2.credentials import Credentials as OAuthCredentials

        path = self.config.token_path
        if path.exists():
            credentials = OAuthCredentials.from_authorized_user_file(
                str(path), self.config.scopes
            )
            return self._validate(credentials)

        return None

    def save(self, credentials: "OAuthCredentials") -> None:
        """
        Save credentials to the file system.

        Parameters
        ----------
        credentials : OAuthCredentials
            The credentials to serialize and store.
        """
        path = self.config.token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(credentials.to_json())

    def _validate(
        self, credentials: "OAuthCredentials | None"
    ) -> "OAuthCredentials | None":
        """
        Validate loaded credentials.

        Checks if `credentials` is not ``None`` and satisfies the
        configuration requirements. If invalid or corrupted, the token
        file is referenced and removed.

        Parameters
        ----------
        credentials : OAuthCredentials | None
            The credentials to validate.

        Returns
        -------
        OAuthCredentials | None
            The credentials if valid, otherwise ``None``.
        """
        if not credentials:
            return None

        try:
            # Ensure the token has sufficient permissions.
            if not credentials.has_scopes(self.config.scopes):
                self.config.token_path.unlink()
                return None

            return credentials

        except OSError:
            # Remove potentially corrupted files to prevent persistent
            # errors.
            self.config.token_path.unlink(missing_ok=True)
            return None


def _get_user_credentials(tokens: TokenManager) -> "AuthCredentials | None":
    """
    Attempt to load and refresh user credentials from the token manager.

    Parameters
    ----------
    tokens : TokenManager
        The token manager.

    Returns
    -------
    AuthCredentials | None
        Valid user credentials if found, otherwise ``None``.
    """
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request

    with contextlib.suppress(RefreshError, ValueError, OSError):
        credentials = tokens.load()

        if not credentials:
            return None

        if credentials.valid:
            return credentials

        if _is_refreshable(credentials):
            credentials.refresh(Request())
            return credentials

    return None


def _get_default_credentials(config: AuthConfig) -> "AuthCredentials | None":
    """
    Attempt to obtain Application Default Credentials (ADC).

    Parameters
    ----------
    config : AuthConfig
        The authentication configuration.

    Returns
    -------
    AuthCredentials | None
        Default credentials if available and valid, otherwise ``None``.
    """
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError, RefreshError
    from google.auth.transport.requests import Request

    with contextlib.suppress(
        DefaultCredentialsError, RefreshError, ValueError
    ):
        default_credentials = default(scopes=list(config.scopes))

        credentials = default_credentials[0]

        if not credentials:
            return None

        if credentials.valid:
            return credentials

        if _is_refreshable(credentials):
            credentials.refresh(Request())
            return credentials

    return None


def _get_interactive_credentials(
    project_id: str | None, config: AuthConfig
) -> "AuthCredentials":
    """
    Attempt to obtain credentials via interactive flow.

    Dispatches to the appropriate interactive flow based on the
    execution environment (Colab or local).

    Parameters
    ----------
    project_id : str | None
        The Google Cloud project ID.
    config : AuthConfig
        The authentication configuration.

    Returns
    -------
    AuthCredentials
        Interactive credentials obtained from the user.

    Raises
    ------
    RuntimeError
        If the interactive flow cannot be initiated (e.g. running in a
        headless environment).
    """
    if running_on_colab():
        return _run_colab_interactive_auth(project_id, config)

    if running_on_notebook():
        return _run_local_interactive_auth(config=config)

    # Inform the user why authentication fails in headless environments.

    raise RuntimeError(
        "Interactive authentication failed. Ensure the environment "
        "supports interactive flows (e.g. local Jupyter Notebooks)."
    )


def _run_colab_interactive_auth(
    project_id: str | None, config: AuthConfig
) -> "AuthCredentials":
    """
    Run interactive authentication for Google Colab.

    Parameters
    ----------
    project_id : str | None
        The Google Cloud project ID.
    config : AuthConfig
        The authentication configuration.

    Returns
    -------
    AuthCredentials
        Credentials obtained via Colab authentication.
    """
    from google.auth import default
    from google.colab.auth import authenticate_user as colab_auth

    colab_auth(project_id=project_id)

    credentials, _ = default(scopes=list(config.scopes))

    return credentials


def _run_local_interactive_auth(config: AuthConfig) -> "AuthCredentials":
    """
    Run interactive authentication for local environments.

    Uses a local server flow to obtain user credentials.

    Parameters
    ----------
    config : AuthConfig
        The authentication configuration.

    Returns
    -------
    AuthCredentials
        Credentials obtained via local interactive flow.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    try:
        secrets_path = _get_client_configuration_path(config)

        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=str(secrets_path), scopes=list(config.scopes)
        )

    except ClientConfigurationNotFoundError:
        flow = InstalledAppFlow.from_client_config(
            client_config=_CLIENT_CONFIG, scopes=list(config.scopes)
        )

    return flow.run_local_server(port=0)


def _get_client_configuration_path(config: AuthConfig) -> Path:
    """
    Retrieve the path to the client secrets file.

    Parameters
    ----------
    config : AuthConfig
        The authentication configuration.

    Returns
    -------
    Path
        Path to the client secrets file.

    Raises
    ------
    ClientConfigurationNotFoundError
        If the secrets file does not exist in the package resources.
    """
    from importlib import resources

    secrets_file = resources.files(config.config_package).joinpath(
        config.config_name
    )
    with resources.as_file(secrets_file) as secrets_path:
        if not secrets_path.exists():
            raise ClientConfigurationNotFoundError(
                "Client configuration file not found. Verify package "
                "installation."
            )

    return secrets_path


def _is_refreshable(credentials: "AuthCredentials") -> bool:
    """
    Check if credentials support refreshing.

    Parameters
    ----------
    credentials : AuthCredentials
        The credentials to check.

    Returns
    -------
    bool
        ``True`` if `credentials` has a `refresh` method, is `expired`,
        and has a `refresh_token`; ``False`` otherwise.
    """
    return bool(
        hasattr(credentials, "refresh")
        and getattr(credentials, "expired", False)
        and getattr(credentials, "refresh_token", False)
    )


def _is_serializable(
    credentials: "AuthCredentials",
) -> TypeGuard["OAuthCredentials"]:
    """
    Check if credentials can be serialized to JSON.

    Parameters
    ----------
    credentials : AuthCredentials
        The credentials to check.

    Returns
    -------
    bool
        ``True`` if `credentials` can be serialized; ``False``
        otherwise.
    """
    return hasattr(credentials, "to_json")


def authenticate_user(
    project_id: str | None, config: AuthConfig, tokens: TokenManager
) -> "AuthCredentials":
    """
    Authenticate the user and obtain valid credentials.

    This function attempts to obtain valid credentials using the
    following strategy:
    1.  Check for stored credentials in the persistent storage.
    2.  Attempt to use Application Default Credentials (ADC).
    3.  Initiate an interactive authentication flow.

    Parameters
    ----------
    project_id : str | None
        The Google Cloud project ID.
    config : AuthConfig
        The authentication configuration.
    tokens : TokenManager
        The token manager.

    Returns
    -------
    AuthCredentials
        Valid credentials for accessing Google Cloud services.

    Raises
    ------
    RuntimeError
        If valid credentials cannot be obtained by any method.
    """
    credentials = _get_user_credentials(tokens)

    if credentials:
        return credentials

    credentials = _get_default_credentials(
        config
    ) or _get_interactive_credentials(project_id, config)

    if not credentials:
        raise RuntimeError(
            "Failed to obtain authentication credentials. Verify "
            "network connectivity and credential validity."
        )

    if _is_serializable(credentials):
        tokens.save(credentials)

    return credentials


__all__ = ["AuthConfig", "TokenManager", "authenticate_user"]
