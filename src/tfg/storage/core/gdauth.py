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
    if not credentials:
        credentials = authenticate_user(
            project_id=None, config=_CONFIG, tokens=_tokens
        )
    return _get_gdrive_default_client(credentials=credentials)
