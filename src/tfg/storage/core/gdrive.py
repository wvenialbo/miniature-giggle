import contextlib
import pathlib as pl
from importlib import resources
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build  # type: ignore
from platformdirs import user_data_dir

from ... import __package_id__, __package_root__
from ..backend import GoogleDriveBackend
from ..cache import DriveCache, TimedDriveCache
from ..datasource import Datasource, DatasourceContract
from ..mapper import GoogleDriveURIMapper

# Scope necesario para lectura/escritura completa en Drive
_SCOPES = ["https://www.googleapis.com/auth/drive"]
_CLIENT_SECRETS = "secrets.json"
_USER_SECRETS = "token.json"
_SECRETS_LOCATION = "tfg.config"

_APP_AUTHOR = __package_id__
_APP_NAME = __package_root__


def _get_token_path() -> pl.Path:
    """
    Resuelve la ubicación del token de manera programática según el OS.
    """
    # user_data_dir resuelve el protocolo nativo de cada OS automáticamente
    path = pl.Path(user_data_dir(_APP_NAME, _APP_AUTHOR))
    return path / _USER_SECRETS


def _get_user_credentials(token_path: pl.Path) -> Any:
    """Intenta cargar credenciales de usuario desde un token persistente."""
    creds = UserCredentials.from_authorized_user_file(str(token_path), _SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def _run_interactive_auth(
    creds_path: pl.Path | None, token_path: pl.Path
) -> Any:
    """Lanza el flujo OAuth interactivo y guarda el token."""
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    return creds


def _get_gdrive_credentials() -> Any:
    """Gestiona la resolución de credenciales con control de flujo."""
    # 1. Prioridad: Token de usuario existente
    token_path = _get_token_path()
    if token_path.exists():
        with contextlib.suppress(Exception):
            return _get_user_credentials(token_path)

    # 2. Caída a flujo interactivo si no es Service Account
    source = resources.files(_SECRETS_LOCATION).joinpath(_CLIENT_SECRETS)
    with resources.as_file(source) as creds_path:
        return _run_interactive_auth(creds_path, token_path)


def use_google_drive(
    *,
    root_path: str | None = None,
    cache_file: str | pl.Path | None = None,
    expire_after: float | None = None,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a Google Drive vía API.

    Utiliza una cuenta de servicio (Service Account) para la autenticación
    y configura un mapeo de rutas POSIX sobre la estructura de archivos
    de Drive.

    Parameters
    ----------
    root_path : str, optional
        Ruta raíz dentro de Google Drive para el contexto. Si es None,
        se utiliza la raíz del Drive.
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de IDs. Si es None,
        el caché será volátil (en memoria).
    expire_after : float, optional
        Tiempo en segundos tras el cual las entradas del caché expiran.
        Si es None, el caché no expira.

    Returns
    -------
    Datasource
        Objeto orquestador configurado con el backend de Drive API.
    """
    # 1. Validación y Carga de Credenciales
    creds = _get_gdrive_credentials()

    # 2. Construcción del Cliente de API (Service)
    # cache_discovery=False evita advertencias en ciertos entornos y
    # mejora el tiempo de inicio en implementaciones stateless.
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    # 3. Inicialización del Cache
    # Si cache_file es None, NamesCache trabajará en memoria.
    cache_path_str = str(cache_file) if cache_file else None

    if expire_after is not None:
        drive_cache = TimedDriveCache(
            cache_file=cache_path_str, expire_after=expire_after
        )
    else:
        drive_cache = DriveCache(cache_file=cache_path_str)

    base_path = pl.Path("/" if root_path is None else root_path).resolve()
    base_path = base_path.relative_to(base_path.anchor)

    local_root = pl.PurePosixPath("/")
    mountpoint = local_root / base_path.as_posix()

    # 4. Instanciación de Protocolos (Inyección de Dependencias)
    # Ambos componentes comparten la misma instancia de 'service'.
    backend = GoogleDriveBackend(service=service)

    mapper = GoogleDriveURIMapper(service=service, cache=drive_cache)

    # 6. Retorno del Datasource Orquestador
    return Datasource(
        mountpoint=str(mountpoint),
        backend=backend,
        mapper=mapper,
        cache=drive_cache,
    )


__all__ = ["use_google_drive"]
