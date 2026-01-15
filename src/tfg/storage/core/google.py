import pathlib as pl
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build  # type: ignore

from ..backend import GoogleDriveBackend
from ..cache import DriveCache, TimedDriveCache
from ..datasource import Datasource, DatasourceContract
from ..handler import DataHandler
from ..mapper import GoogleDriveURIMapper
from .handlers import get_file_handlers

# Scope necesario para lectura/escritura completa en Drive
_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_gdrive_credentials(credentials: str | pl.Path) -> Any:
    """Extraído de la Sección 1: Validación y Carga de Credenciales."""
    creds_path = pl.Path(credentials)
    if not creds_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales: {creds_path}"
        )

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=_SCOPES
        )
    except ValueError as e:
        raise ValueError(
            f"Error al leer las credenciales de servicio: {e}"
        ) from e

    return creds


def use_google_drive(
    *,
    credentials: str | pl.Path,
    cache_file: str | pl.Path | None = None,
    mountpoint: str = "gdrive://",
    handlers: list[DataHandler] | None = None,
    expire_after: float | None = None,
) -> DatasourceContract:
    """
    Crea un contexto de Datasource conectado a Google Drive vía API.

    Utiliza una cuenta de servicio (Service Account) para la autenticación
    y configura un mapeo de rutas POSIX sobre la estructura de archivos
    de Drive.

    Parameters
    ----------
    credentials : str | Path
        Ruta al archivo JSON de credenciales de la cuenta de servicio.
    cache_file : str | Path, optional
        Ruta al archivo para persistir el caché de IDs. Si es None,
        el caché será volátil (en memoria).
    mountpoint : str, optional
        Identificador lógico para el punto de montaje en el Datasource.
        Por defecto "gdrive://".
    handlers : list[DataHandler], optional
        Lista de handlers personalizados. Si es None, se cargan los
        valores por defecto.
    expire_after : float, optional
        Tiempo en segundos tras el cual las entradas del caché expiran.
        Si es None, el caché no expira.

    Returns
    -------
    Datasource
        Objeto orquestador configurado con el backend de Drive API.

    Raises
    ------
    FileNotFoundError
        Si el archivo de credenciales no existe.
    ValueError
        Si las credenciales no son válidas.
    """

    # 1. Validación y Carga de Credenciales
    creds = _get_gdrive_credentials(credentials)

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

    # 4. Instanciación de Protocolos (Inyección de Dependencias)
    # Ambos componentes comparten la misma instancia de 'service'.
    mapper = GoogleDriveURIMapper(service=service, cache=drive_cache)
    backend = GoogleDriveBackend(service=service)

    # 5. Configuración de Handlers
    if handlers is None:
        handlers = get_file_handlers()

    # 6. Retorno del Datasource Orquestador
    return Datasource(
        mountpoint=mountpoint,
        backend=backend,
        mapper=mapper,
        handlers=handlers,
        cache=drive_cache,
    )
