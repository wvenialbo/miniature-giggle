from .gutils import (
    AuthConfig,
    Client,
    Credentials,
    TokenManager,
    authenticate_user,
)

_CONFIG = AuthConfig(
    (
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.readonly",
    )
)
_tokens = TokenManager(_CONFIG)


def _get_gdrive_default_client(
    credentials: Credentials, config: AuthConfig
) -> Client:
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient import discovery
    from httplib2 import Http

    # Crea un objeto httplib2.Http con el timeout global
    http_transport = Http(timeout=config.timeout)

    authorized_http = AuthorizedHttp(credentials, http=http_transport)

    # Construcción del cliente de API (Service)
    # cache_discovery=False evita advertencias en ciertos entornos y
    # mejora el tiempo de inicio en implementaciones stateless.
    service = discovery.build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
        http=authorized_http,
    )

    # Validar credenciales haciendo una llamada simple. Esto es
    # necesario porque al usar discovery.build, a veces el objeto
    # credentials puede quedar en un estado donde el token está presente
    # pero la librería no detecta que debe refrescarlo automáticamente
    # antes de la llamada.
    _ = service.files().list(pageSize=1, fields="files(id)").execute()

    return service


def get_gdrive_client(credentials: Credentials | None) -> Client:
    if not credentials:
        credentials = authenticate_user(
            project_id=None, config=_CONFIG, tokens=_tokens
        )
    return _get_gdrive_default_client(credentials=credentials, config=_CONFIG)
