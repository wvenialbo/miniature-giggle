import contextlib
import os
import pathlib as pl
import typing as tp
from dataclasses import dataclass

from ... import __package_id__, __package_root__

Client = tp.Any
Credentials = tp.Any


@dataclass(frozen=True)
class AuthConfig:
    scopes: tuple[str, ...]
    app_name: str = __package_root__
    app_author: str = __package_id__
    secrets_name: str = "secrets.json"
    secrets_package: str = "tfg.config"
    token_name: str = "token.json"
    timeout: int = 15

    @property
    def token_path(self) -> pl.Path:
        from platformdirs import user_data_dir

        path = pl.Path(user_data_dir(self.app_name, self.app_author))
        return path / self.token_name


class TokenManager:
    """Encapsula solo la interacción con el sistema de archivos."""

    def __init__(self, config: AuthConfig):
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


def _is_interactive() -> bool:
    """
    Detecta si el código se está ejecutando en una notebook.
    """
    try:
        from IPython.core.getipython import get_ipython

        return get_ipython() is not None

    except ImportError:
        return False


def _running_on_colab() -> bool:
    return bool(os.getenv("COLAB_RELEASE_TAG"))


def _get_user_credentials(tokens: TokenManager) -> Credentials:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuthCredentials

    credentials: OAuthCredentials | None = tokens.load()

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return credentials


def _run_interactive_auth(config: AuthConfig) -> Credentials:
    from importlib import resources

    from google_auth_oauthlib.flow import InstalledAppFlow

    source = resources.files(config.secrets_package).joinpath(
        config.secrets_name
    )
    with resources.as_file(source) as creds_path:
        if not creds_path.exists():
            raise FileNotFoundError(
                "No se encontró el archivo de configuración de cliente "
                f"en '{source}'. Asegúrate de que la librería se instaló "
                "correctamente con los recursos incluidos."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=str(creds_path), scopes=list(config.scopes)
        )

    return flow.run_local_server(port=0)


def _authenticate_interactive(
    config: AuthConfig, tokens: TokenManager
) -> Credentials:
    from google.oauth2.credentials import Credentials as OAuthCredentials

    credentials: OAuthCredentials | None = None

    # 1. Prioridad: Token de usuario existente
    with contextlib.suppress(Exception):
        credentials = _get_user_credentials(tokens)

    # 2. Caída a flujo interactivo
    if not credentials or not credentials.valid:
        credentials = _run_interactive_auth(config)

    tokens.save(credentials)

    return credentials


def authenticate_user(
    project_id: str | None, config: AuthConfig, tokens: TokenManager
) -> Credentials | None:
    if _running_on_colab():
        from google.colab.auth import authenticate_user

        authenticate_user(project_id=project_id)
        return None

    if _is_interactive():
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError

        try:
            # Intentamos ver si ya existen credenciales para no molestar al usuario
            credentials, _ = default(scopes=config.scopes)

            return credentials

        except DefaultCredentialsError:
            return _authenticate_interactive(config=config, tokens=tokens)

    return None
