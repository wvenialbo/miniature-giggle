import os
import pathlib as pl
import typing as tp
from dataclasses import dataclass

from ... import __package_id__, __package_root__

Client = tp.Any
Credentials = tp.Any


@dataclass(frozen=True)
class _AuthConfig:
    app_name: str = __package_root__
    app_author: str = __package_id__
    secrets_name: str = "secrets.json"
    secrets_package: str = "tfg.config"
    token_name: str = "token.json"
    timeout: int = 15

    # Define los scopes necesarios para GCS
    scopes: tuple[str, ...] = (
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/devstorage.full_control",
    )

    @property
    def token_path(self) -> pl.Path:
        from platformdirs import user_data_dir

        path = pl.Path(user_data_dir(self.app_name, self.app_author))
        return path / self.token_name


class _TokenManager:
    """Encapsula solo la interacción con el sistema de archivos."""

    def __init__(self, config: _AuthConfig):
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

        target = tp.cast(OAuthCredentials, credentials)

        path = self.config.token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(target.to_json())


_CONFIG = _AuthConfig()
_tokens = _TokenManager(_CONFIG)


def _is_interactive() -> bool:
    """
    Detecta si el código se está ejecutando en una notebook.
    """
    try:
        from IPython.core.getipython import get_ipython

        return get_ipython() is not None  # type: ignore

    except ImportError:
        return False


def _is_public(bucket: str, config: _AuthConfig) -> bool:
    import requests

    # Endpoint de la API XML de GCS para el bucket
    url = f"https://storage.googleapis.com/{bucket}"

    try:
        # Petición simple SIN cabeceras de autorización
        response = requests.get(url, timeout=config.timeout)

        return response.status_code == 200

    except Exception:
        return False


def _running_on_colab() -> bool:
    return bool(os.getenv("COLAB_RELEASE_TAG"))


def _run_interactive_auth(config: _AuthConfig) -> Credentials:
    from importlib import resources

    from google_auth_oauthlib.flow import InstalledAppFlow

    source = resources.files(config.secrets_package).joinpath(
        config.secrets_name
    )
    with resources.as_file(source) as creds_path:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file=str(creds_path), scopes=config.scopes
        )

    return flow.run_local_server(port=0)


def _authenticate_interactive(
    config: _AuthConfig, tokens: _TokenManager
) -> Credentials:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuthCredentials

    credentials = tp.cast(OAuthCredentials, tokens.load())

    # Lógica de decisión: Refrescar vs. Nuevo Flow
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    # Abre una ventana en el navegador o da un link para pegar un código
    if not credentials or not credentials.valid:
        credentials = _run_interactive_auth(config)

    tokens.save(credentials)

    return credentials


def _authenticate_user(
    project_id: str | None, config: _AuthConfig, tokens: _TokenManager
) -> Credentials | None:
    """
    Autentica el usuario en Google Colab para acceder a GCS.

    Parameters
    ----------
    project_id : str | None
        ID del proyecto de Google Cloud. No es obligatorio.
    """
    if _running_on_colab():
        from google.colab.auth import authenticate_user

        authenticate_user(project_id=project_id)
        return None

    if _is_interactive():
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError

        try:
            # Intentamos ver si ya existen credenciales para no molestar al usuario
            credentials, _ = default(scopes=config.scopes)  # type: ignore

            return credentials

        except DefaultCredentialsError:
            return _authenticate_interactive(config=config, tokens=tokens)

    return None


def _get_gcs_anonymous_client(
    project: str | None, **client_kwargs: tp.Any
) -> Client:
    """
    Crea un cliente anónimo de Google Cloud Storage.

    Parameters
    ----------
    project : str | None
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo del entorno.
    **client_kwargs : Any
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente anónimo de GCS.
    """
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import storage

    if project is not None:
        return storage.Client(
            project=project,
            credentials=AnonymousCredentials(),
            **client_kwargs,
        )
    return storage.Client.create_anonymous_client()


def _get_gcs_default_client(
    project: str | None,
    credentials: Credentials | None,
    **client_kwargs: tp.Any,
) -> Client:
    """
    Crea un cliente de Google Cloud Storage usando credenciales por
    defecto o las pasadas en client_kwargs.

    Parameters
    ----------
    project : str | None
        ID del proyecto de Google Cloud. Si no se especifica, la
        librería intentará inferirlo de las credenciales o del entorno.
    credentials: Credentials | None, optional
        Credenciales explícitas para autenticación. Si se proporcionan,
        se usan en lugar de las ADC.
    **client_kwargs : Any
        Argumentos adicionales para `storage.Client` (credentials,
        client_info, client_options, etc.).

    Returns
    -------
    storage.Client
        Cliente de GCS autenticado.
    """
    from google.cloud import storage

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
    credentials: Credentials | None,
    **client_kwargs: tp.Any,
) -> Client:
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
    **client_kwargs : Any
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
            project=project, credentials=credentials, **client_kwargs
        )

    # Para buckets públicos, usamos un cliente anónimo.
    if _is_public(bucket=bucket, config=_CONFIG):
        return _get_gcs_anonymous_client(project=project, **client_kwargs)

    # Si se proveyeron credenciales explícitas y el bucket no es
    # público, forzamos autenticación de usuario (no anónimo).
    credentials = _authenticate_user(
        project_id=project, config=_CONFIG, tokens=_tokens
    )

    # Intentamos instanciar el cliente con credenciales por defecto;
    # busca las ADC del entorno.
    return _get_gcs_default_client(
        project=project, credentials=credentials, **client_kwargs
    )
