import pathlib as pl
import typing as tp

from ..cache.simple import NamesCache
from .base import URIMapper

if tp.TYPE_CHECKING:
    # Importamos el tipo específico para Drive v3
    from googleapiclient._apis.drive.v3.resources import DriveResource

ID_PREFIX = "id://"
PATH_PREFIX = "path://"
PATH_ID_SEPARATOR = "|"
MAX_DEPTH = 50
PATH_SEP = "/"


class GoogleDriveURIMapper(URIMapper):
    """
    Implementación de URIMapper para la API de Google Drive.

    Traduce rutas estilo POSIX a identificadores opacos de Drive.
    Maneja la ambigüedad de nombres tomando el primer resultado encontrado.

    Parameters
    ----------
    service : DriveResource
        Cliente autenticado de la API de Google Drive (v3).
    cache : DriveCache
        Instancia del gestor de caché.
    """

    def __init__(self, service: "DriveResource", cache: NamesCache) -> None:
        self._service = service
        self._cache = cache

    def to_generic(self, uri: str) -> str:
        """
        Convierte un ID nativo (id://xxx) a una ruta lógica aproximada.
        Nota: Esta operación es costosa (camina hacia arriba) y puede ser
        ambigua (múltiples padres).
        """
        file_id = self._strip_prefix(uri, ID_PREFIX)
        path_parts: list[str] = []
        current_id = file_id

        # Loop de seguridad para evitar ciclos infinitos en estructuras corruptas
        for _ in range(MAX_DEPTH):
            if current_id == "root":
                break

            try:
                file_meta = (
                    self._service.files()
                    .get(
                        fileId=current_id,
                        fields="name, parents",
                        supportsAllDrives=True,
                    )
                    .execute()
                )
            except Exception:
                # Si falla la lectura (permisos o no existe), retornamos el ID crudo
                return uri

            name = file_meta.get("name", "unknown")
            path_parts.append(name)

            if parents := file_meta.get("parents", []):
                # Tomamos el primer padre arbitrariamente
                current_id = parents[0]

            else:
                # Llegamos a la cima accesible o es huérfano
                break

        # Invertimos porque caminamos de hijo a padre
        full_path = PATH_SEP + PATH_SEP.join(reversed(path_parts))

        # Opcional: Actualizar caché con la ruta descubierta
        self._cache.set(full_path, file_id)

        return full_path

    def to_native(self, uri: str) -> str:
        """
        Convierte una ruta lógica POSIX a un ID nativo de Drive.

        Si la ruta existe, devuelve "id:<file_id>".
        Si la ruta NO existe (parcialmente), devuelve:
        "path:<parte_faltante>|<id_ultimo_padre_conocido>"
        """
        # Normalización básica
        if uri == PATH_SEP:
            return f"{ID_PREFIX}root"

        if cached_id := self._cache.get(uri):
            return f"{ID_PREFIX}{cached_id}"

        # 2. Caminata por la jerarquía
        parts = pl.PurePosixPath(uri).parts
        # Filtramos la raiz '/' si path.parts la incluye
        parts = [p for p in parts if p != PATH_SEP]

        current_id = "root"
        resolved_path = ""  # Para ir construyendo la llave del caché

        for i, segment in enumerate(parts):
            # Construir ruta parcial actual para consultar/guardar caché
            resolved_path = (
                f"{resolved_path}{PATH_SEP}{segment}"
                if resolved_path
                else segment
            )

            if cached_step := self._cache.get(resolved_path):
                current_id = cached_step
                continue

            if found_id := self._find_child_id(
                parent_id=current_id, name=segment
            ):
                current_id = found_id
                self._cache.set(resolved_path, current_id)
            else:
                # No encontrado. Preparamos el retorno especial.
                # Resto de la ruta que falta por crear
                remaining_path = PATH_SEP.join(parts[i:])
                return f"{PATH_PREFIX}{remaining_path}{PATH_ID_SEPARATOR}{current_id}"

        return f"{ID_PREFIX}{current_id}"

    def _find_child_id(self, parent_id: str, name: str) -> str | None:
        """Ayudante para buscar un archivo por nombre dentro de un padre."""
        # Escapar comillas simples en el nombre por seguridad en el query
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
                fields="files(id)",
                pageSize=1,  # Solo nos interesa el primero
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )

        files = response.get("files", [])
        return files[0]["id"] if files else None  # type: ignore

    @staticmethod
    def _strip_prefix(uri: str, prefix: str) -> str:
        """Ayudante para remover un prefijo de una URI."""
        if not uri.startswith(prefix):
            raise ValueError(
                f"La URI no comienza con el prefijo esperado: {prefix}"
            )
        return uri[len(prefix) :]
