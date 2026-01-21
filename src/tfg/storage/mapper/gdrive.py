import pathlib as pl
import typing as tp

from ..cache import CacheBase
from .base import URIMapper

Resource = tp.Any

DriveCache = CacheBase[tuple[str, str]]

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
ID_PREFIX = "id://"
PATH_PREFIX = "path://"
PATH_ID_SEPARATOR = "|"
MAX_DEPTH = 50
PATH_SEP = "/"
ROOT_ID = "root"


class GoogleDriveURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en ID nativos de Google Drive.

    Traduce rutas estilo POSIX a identificadores opacos de Drive.
    Maneja la ambigüedad de nombres tomando el primer resultado
    encontrado.

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones nativas específicas, mientras los clientes exponen rutas
    genéricas logicas para el usuario.  Facilitando la interoperabilidad
    entre distintos backends abstrayendo las diferencias estructurales
    en sus modelos de URI.

    Se adopta el formato POSIX/Unix para las URI genéricas, usando '/'
    como separador de componentes de rutas. Las URI lógicas se definen
    respecto a una raíz genérica, que puede corresponder a diferentes
    ubicaciones nativas en cada backend y cliente.  Es decir, el
    parámetro `uri` en los métodos `to_generic` y `to_native` se
    interpreta como una ruta absoluta o una relativa respecto a la raíz
    del sistema de archivos nativo o la raíz lógica genérica,
    respectivamente.

    Parameters
    ----------
    service : DriveResource
        Cliente autenticado de la API de Google Drive (v3).
    cache : DriveCache
        Instancia del gestor de caché.

    Attributes
    ----------
    _service : DriveResource
        Cliente autenticado de la API de Google Drive (v3).
    _cache : DriveCache
        Instancia del gestor de caché.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.

    Notes
    -----
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    """

    def __init__(self, service: Resource, drive_cache: DriveCache) -> None:
        if tp.TYPE_CHECKING:
            from googleapiclient._apis.drive.v3.resources import DriveResource

        self._service: "DriveResource" = service
        self._drive_cache = drive_cache

    def __repr__(self) -> str:
        return (
            "GoogleDriveURIMapper"
            f"({repr(self._service)}, {repr(self._drive_cache)})"
        )

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Transforma un ID nativo (id://xxx) a una ruta lógica aproximada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta proporcionada por el backend.

        Returns
        -------
        str
            URI genérica absoluta en formato POSIX.

        Notes
        -----
        Esta operación es costosa (camina hacia arriba) y puede ser
        ambigua (múltiples padres).
        """
        _, logical_path, _ = self._split_id(uri)

        return logical_path

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica absoluta a una URI nativa absoluta.

        Transforma una ruta lógica POSIX a un ID nativo de Google Drive.

        Si la ruta existe, devuelve "id://<file_id>".
        Si la ruta NO existe (parcialmente), devuelve:
        "path://<parte_faltante>|<id_ultimo_padre_conocido>"

        Parameters
        ----------
        uri : str
            URI genérica absoluta en formato POSIX.

        Returns
        -------
        str
            URI nativa absoluta (para objetos existentes) o una
            ruta/formato especial (para objetos inexistentes o nuevos)
            que `StorageBackend.create_path()` pueda interpretar.

        Notes
        -----
        - Este método no distingue entre objetos inexistentes y nuevos;
          ambos casos devuelven la misma ruta/formato. La distinción la
          realiza el orquestador según la operación a ejecutar.
        - En backends que permiten nombres duplicados (ejemplo: Google
          Drive), devuelve el primer objeto encontrado con ese nombre.
        - No valida la existencia del objeto; `StorageBackend.exists()`
          debe usarse para verificación explícita.
        """
        if uri == PATH_SEP:
            return (
                f"{ID_PREFIX}{ROOT_ID}"
                f"{PATH_ID_SEPARATOR}{uri}"
                f"{PATH_ID_SEPARATOR}{FOLDER_MIME_TYPE}"
            )

        if cached := self._drive_cache.get(uri):
            cached_id, cached_mime = cached
            return (
                f"{ID_PREFIX}{cached_id}"
                f"{PATH_ID_SEPARATOR}{uri}"
                f"{PATH_ID_SEPARATOR}{cached_mime}"
            )

        # 2. Caminata por la jerarquía
        parts = list(pl.PurePosixPath(uri).parts)

        # Filtramos la raiz '/' si path.parts la incluye
        parts = [p for p in parts if p != PATH_SEP]

        parent_id = ROOT_ID
        parent_mime = FOLDER_MIME_TYPE

        current_logical_path = pl.PurePosixPath(PATH_SEP)

        for i, segment in enumerate(parts):
            # Construir ruta parcial actual para consultar/guardar caché
            current_logical_path = current_logical_path / segment
            parent_path = str(current_logical_path)

            if cached_step := self._drive_cache.get(parent_path):
                parent_id, _ = cached_step
                continue

            found_id, found_mime = self._find_child_id(
                parent_id=parent_id, name=segment
            )

            if found_id:
                parent_id = found_id
                parent_mime = found_mime or ""
                self._drive_cache.set(parent_path, (parent_id, parent_mime))
            else:
                # No encontrado. Preparamos el retorno especial.
                # Ruta existente, resto de la ruta que falta por crear,
                # e ID de la ruta existente.
                child_path = PATH_SEP.join(parts[i:])
                return (
                    f"{PATH_PREFIX}{parent_path}"
                    f"{PATH_ID_SEPARATOR}{child_path}"
                    f"{PATH_ID_SEPARATOR}{parent_id}"
                )

        return (
            f"{ID_PREFIX}{parent_id}"
            f"{PATH_ID_SEPARATOR}{uri}"
            f"{PATH_ID_SEPARATOR}{parent_mime}"
        )

    def _find_child_id(
        self, parent_id: str, name: str
    ) -> tuple[str | None, str | None]:
        """
        Ayudante para buscar un archivo por nombre dentro de un padre.
        """
        # Escapar comillas simples en el nombre por seguridad en el
        # query
        safe_name = name.replace("'", "\\'")

        query = (
            f"name = '{safe_name}' and "
            f"'{parent_id}' in parents and "
            f"trashed = false"
        )

        response = (
            self._service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, mimeType)",
                pageSize=1,  # Solo nos interesa el primero
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )

        if files := response.get("files", []):
            return files[0].get("id"), files[0].get("mimeType")

        return None, None

    def _split_id(self, uri: str) -> tuple[str, str, str]:
        """Divide un URI de objeto en sus componentes."""
        try:
            clean_uri = self._strip_prefix(uri, ID_PREFIX)
            object_id, object_path, object_mime = clean_uri.split(
                PATH_ID_SEPARATOR, 2
            )
            return object_id, object_path, object_mime

        except Exception as e:
            raise ValueError(f"URI de objeto malformado: '{uri}'") from e

    @staticmethod
    def _strip_prefix(uri: str, prefix: str) -> str:
        """Ayudante para remover un prefijo de un URI."""
        if not uri.startswith(prefix):
            raise ValueError(
                f"Se esperaba un URI '{prefix}', se recibió: '{uri}'"
            )
        return uri[len(prefix) :]
