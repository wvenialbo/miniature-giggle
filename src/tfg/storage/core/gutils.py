import contextlib
import pathlib as pl
import typing as tp
from dataclasses import dataclass

from ... import __package_id__, __package_root__
from ...utils import running_on_colab, running_on_notebook


if tp.TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from google.oauth2.credentials import Credentials as Credentials2


CLIENT_ID = (
    "794699822558-9h359ba9l0cagh0avgk3ph86ptn92sce.apps.googleusercontent.com"
)
CLIENT_KEY = "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"

CLIENT_CONFIG = {
    "installed": {
        "client_id": CLIENT_ID,
        "project_id": "goes-dl",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": (
            "https://www.googleapis.com/oauth2/v1/certs"
        ),
        "client_secret": CLIENT_KEY,
        "redirect_uris": ["http://localhost"],
    }
}


class SecretsNotFoundError(Exception):
    """No se encuentra el archivo secrets.json."""

    pass


@dataclass(frozen=True)
class AuthConfig:
    scopes: tuple[str, ...]
    token_name: str
    app_name: str = __package_root__
    app_author: str = __package_id__
    secrets_name: str = "secrets.json"
    secrets_package: str = "tfg.config"
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

    def load(self) -> "Credentials2 | None":
        from google.oauth2.credentials import Credentials as Credentials2

        path = self.config.token_path
        if path.exists():
            credentials = Credentials2.from_authorized_user_file(
                str(path), self.config.scopes
            )
            return self._validate(credentials)

        return None

    def save(self, credentials: "Credentials2") -> None:
        path = self.config.token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(credentials.to_json())

    def _validate(
        self, credentials: "Credentials2 | None"
    ) -> "Credentials2 | None":
        if not credentials:
            return None

        try:
            # Verificamos si el token guardado NO tiene todos
            # los scopes requeridos
            if not credentials.has_scopes(self.config.scopes):
                self.config.token_path.unlink()
                return None

            return credentials

        except OSError:
            # Si el archivo está corrupto o no se puede leer,
            # lo borramos por seguridad
            self.config.token_path.unlink(missing_ok=True)
            return None


def _get_user_credentials(tokens: TokenManager) -> "Credentials | None":
    """
    Intenta cargar las credenciales del usuario.

    Returns
    -------
    Credentials | None
        Credenciales del usuario si existen y son válidas,
        None en caso contrario.
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


def _get_default_credentials(config: AuthConfig) -> "Credentials | None":
    """
    Intenta obtener credenciales por defecto del entorno.

    Returns
    -------
    Credentials | None
        Credenciales por defecto si existen y son válidas,
        None en caso contrario.
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
) -> "Credentials":
    """
    Intenta obtener credenciales mediante un flujo interactivo.

    Returns
    -------
    Credentials
        Credenciales obtenidas mediante el flujo interactivo.

    Raises
    ------
    RuntimeError
        Si no se puede iniciar el flujo interactivo en el entorno
        actual.
    """
    if running_on_colab():
        return _run_colab_interactive_auth(project_id, config)

    if running_on_notebook():
        return _run_local_interactive_auth(config=config)

    # En entornos sin navegador (como algunos notebooks remotos o
    # scripts en servidores).

    raise RuntimeError(
        "No se pudo iniciar el flujo de autenticación interactivo. "
        "Asegúrate de estar ejecutando el código en un entorno "
        "compatible con flujos interactivos (como Jupyter Notebooks "
        "locales)."
    )


def _run_colab_interactive_auth(
    project_id: str | None, config: AuthConfig
) -> "Credentials":
    """
    Flujo interactivo específico para Google Colab.

    Returns
    -------
    Credentials
        Credenciales obtenidas mediante el flujo interactivo en Colab.
    """
    from google.auth import default
    from google.colab.auth import authenticate_user as colab_auth

    colab_auth(project_id=project_id)

    credentials, _ = default(scopes=list(config.scopes))

    return credentials


def _run_local_interactive_auth(config: AuthConfig) -> "Credentials":
    """
    Flujo interactivo para entornos locales/notebooks.

    Returns
    -------
    Credentials
        Credenciales obtenidas mediante el flujo interactivo local.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        client_config=CLIENT_CONFIG, scopes=list(config.scopes)
    )

    return flow.run_local_server(port=0)


def _is_refreshable(credentials: "Credentials") -> bool:
    return bool(
        hasattr(credentials, "refresh")
        and getattr(credentials, "expired", False)
        and getattr(credentials, "refresh_token", False)
    )


def _is_serializable(
    credentials: "Credentials",
) -> tp.TypeGuard["Credentials2"]:
    return hasattr(credentials, "to_json")


def authenticate_user(
    project_id: str | None, config: AuthConfig, tokens: TokenManager
) -> "Credentials":
    """
    Autentica al usuario y obtiene credenciales válidas.

    Returns
    -------
    Credentials
        Credenciales válidas para acceder a los servicios de Google.

    Raises
    ------
    RuntimeError
        Si no se pueden obtener credenciales válidas mediante ninguno
        de los métodos disponibles.
    """
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

    if not credentials:
        raise RuntimeError(
            "No se pudieron obtener credenciales de autenticación. "
            "Asegúrate de tener acceso a internet y de proveer "
            "credenciales válidas"
        )

    # Guarda las credenciales obtenidas si son válidas
    if _is_serializable(credentials):
        tokens.save(credentials)

    return credentials
