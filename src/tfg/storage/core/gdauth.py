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
        "https://www.googleapis.com/auth/devstorage.full_control",
    )
)
_tokens = TokenManager(_CONFIG)


def _get_gdrive_default_client(credentials: Credentials | None) -> Client:
    import httplib2
    from googleapiclient import discovery

    # Crea un objeto httplib2.Http con el timeout global
    # http_transport = httplib2.Http(timeout=_CONFIG.timeout)

    # Construcción del cliente de API (Service)
    # cache_discovery=False evita advertencias en ciertos entornos y
    # mejora el tiempo de inicio en implementaciones stateless.
    service = discovery.build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
        # http=http_transport,
    )

    # Validar credenciales haciendo una llamada simple. Esto es
    # necesario porque al usar discovery.build, a veces el objeto
    # credentials puede quedar en un estado donde el token está presente
    # pero la librería no detecta que debe refrescarlo automáticamente
    # antes de la llamada.
    _ = service.files().list(pageSize=1, fields="files(id)").execute()

    return service


def get_gdrive_client(credentials: Credentials | None) -> Client:
    # Si se proveyeron, usamos las credenciales del usuario.
    if credentials is not None:
        return _get_gdrive_default_client(credentials=credentials)

    # Si se proveyeron credenciales explícitas y el bucket no es
    # público, forzamos autenticación de usuario (no anónimo).
    credentials = authenticate_user(
        project_id=None, config=_CONFIG, tokens=_tokens
    )

    # Intentamos instanciar el cliente con credenciales por defecto;
    # busca las ADC del entorno.
    return _get_gdrive_default_client(credentials=credentials)
