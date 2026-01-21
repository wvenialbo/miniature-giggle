import contextlib
import pathlib as pl
import typing as tp
from dataclasses import dataclass

from ... import __package_id__, __package_root__
from ...utils import running_on_colab

Client = tp.Any
Credentials = tp.Any


class SecretsNotFoundError(Exception):
    """No se encuentra el archivo secrets.json."""

    pass


@dataclass(frozen=True)
class AuthConfig:
    scopes: tuple[str, ...]
    app_name: str = __package_root__
    app_author: str = __package_id__
    secrets_name: str = "secrets.json"
    secrets_package: str = "tfg.config"
    token_name: str = "token.json"
    timeout: int = 60

    @property
    def token_path(self) -> pl.Path:
        from platformdirs import user_data_dir

        path = pl.Path(user_data_dir(self.app_name, self.app_author))
        return path / self.token_name


class TokenManager:
    """Encapsula solo la interacción con el sistema de archivos."""

    def __init__(self, config: AuthConfig) -> None:
        self.config = config

    def load(self) -> Credentials | None:
        from google.oauth2.credentials import Credentials as OAuthCredentials

        path = self.config.token_path
        if path.exists():
            return OAuthCredentials.from_authorized_user_file(
                str(path), self.config.scopes
            )

        return None

    def save(self, credentials: tp.Any) -> None:
        from google.oauth2.credentials import Credentials as OAuthCredentials

        oauth2_credentials: OAuthCredentials = credentials

        path = self.config.token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(oauth2_credentials.to_json())


def _get_user_credentials(tokens: TokenManager) -> Credentials | None:
    """Intenta cargar las credenciales del usuario."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuthCredentials

    credentials: OAuthCredentials | None = None

    with contextlib.suppress(RefreshError, ValueError, OSError):
        credentials = tokens.load()

        if not credentials:
            return None

        if credentials.valid:
            return credentials

        if _is_refreshable(credentials):
            credentials.refresh(Request())
            return credentials

        credentials = None

    return credentials


def _get_default_credentials(config: AuthConfig) -> Credentials | None:
    """Intenta obtener credenciales por defecto del entorno."""
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError, RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuthCredentials

    credentials: OAuthCredentials | None = None

    with contextlib.suppress(
        DefaultCredentialsError, RefreshError, ValueError
    ):
        default_credentials = default(scopes=list(config.scopes))

        credentials = tp.cast(OAuthCredentials | None, default_credentials[0])

        if not credentials:
            return None

        if credentials.valid:
            return credentials

        if _is_refreshable(credentials):
            credentials.refresh(Request())
            return credentials

        credentials = None

    return credentials


def _get_interactive_credentials(
    project_id: str | None, config: AuthConfig
) -> Credentials:
    """Intenta obtener credenciales mediante un flujo interactivo."""
    # if running_on_colab():
    #     return _run_colab_interactive_auth(project_id, config)

    # En entornos sin navegador (como algunos notebooks remotos o
    # scripts en servidores) el flujo interactivo suele imprimir un
    # enlace para que el usuario proceda con la autenticación.
    return _run_local_interactive_auth(config=config)


def _run_colab_interactive_auth(
    project_id: str | None, config: AuthConfig
) -> Credentials:
    """Flujo interactivo específico para Google Colab."""
    from google.auth import default
    from google.colab.auth import authenticate_user as colab_auth

    colab_auth(project_id=project_id)

    credentials, _ = default(scopes=list(config.scopes))

    return tp.cast(Credentials, credentials)


def _run_local_interactive_auth(config: AuthConfig) -> Credentials:
    """Flujo interactivo para entornos locales/notebooks."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    secrets_path = _get_secrets_path(config)

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file=str(secrets_path), scopes=list(config.scopes)
    )

    return flow.run_local_server(port=0)


def _get_secrets_path(
    config: AuthConfig,
) -> pl.Path:
    from importlib import resources

    secrets_file = resources.files(config.secrets_package).joinpath(
        config.secrets_name
    )
    with resources.as_file(secrets_file) as secrets_path:
        if not secrets_path.exists():
            raise SecretsNotFoundError(
                "No se encontró el archivo de configuración de cliente "
                f"en '{secrets_file}'. Asegúrate de que la librería se "
                "instaló correctamente con los recursos incluidos."
            )

    return secrets_path


def _is_refreshable(credentials: tp.Any) -> bool:
    return bool(
        hasattr(credentials, "refresh")
        and getattr(credentials, "expired", False)
        and getattr(credentials, "refresh_token", False)
    )


def _is_serializable(credentials: tp.Any) -> bool:
    return hasattr(credentials, "to_json")


def authenticate_user(
    project_id: str | None, config: AuthConfig, tokens: TokenManager
) -> Credentials:
    # Flujo de autenticación unificado:
    #
    # 1. Token persistente (si existe y es válido): Intenta obtener
    #    credenciales persistente del usuario
    # 2. Credenciales por defecto del entorno: Intenta obtener
    #    credenciales por defecto del entorno
    # 3. Flujo interactivo (adaptado al entorno): Intenta obtener
    #    credenciales en un flujo interactivo

    credentials = _get_user_credentials(tokens)

    if credentials:
        return credentials

    credentials = _get_default_credentials(
        config
    ) or _get_interactive_credentials(project_id, config)

    # Guarda las credenciales obtenidas si son válidas
    if _is_serializable(credentials):
        tokens.save(credentials)
        return credentials

    raise RuntimeError(
        "No se pudieron obtener credenciales de autenticación. "
        "Asegúrate de tener acceso a internet y de proveer "
        "credenciales válidas"
    )
