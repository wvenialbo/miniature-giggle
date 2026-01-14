import contextlib
import io
import typing as tp

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .base import StorageBackend


class GoogleDriveAPIBackend(StorageBackend):
    """
    Backend de almacenamiento para Google Drive vía API.

    Interpreta URI nativas con prefijos 'id://' (recurso existente) o
    'path://' (recurso inexistente) para realizar operaciones de E/S.
    Implementa creación recursiva de carpetas para emular el
    comportamiento de un sistema de archivos.

    Parameters
    ----------
    service : Resource
        Objeto de servicio autenticado de la API de Google Drive.
    """

    ID_PREFIX = "id://"
    PATH_PREFIX = "path://"

    def __init__(self, service: Resource) -> None:
        self.service = service

    def __repr__(self) -> str:
        return "GoogleDriveAPIBackend()"

    def delete(self, *, uri: str) -> None:
        """
        Elimina el archivo en Drive si existe.
        Operación idempotente.
        """
        if not uri.startswith(self.ID_PREFIX):
            return

        file_id = uri.replace(self.ID_PREFIX, "", 1)
        with contextlib.suppress(Exception):
            (
                self.service.files()  # type: ignore
                .delete(fileId=file_id)
                .execute()
            )

    def exists(self, *, uri: str) -> bool:
        """Verifica la existencia basada en el prefijo del mapper."""
        return uri.startswith(self.ID_PREFIX)

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos del ID especificado.

        Raises
        ------
        FileNotFoundError
            Si la URI tiene prefijo 'path://', indicando que no existe.
        """
        if uri.startswith(self.PATH_PREFIX):
            clean_path = uri.replace(self.PATH_PREFIX, "", 1)
            raise FileNotFoundError(
                f"El archivo no existe en Drive: {clean_path}"
            )

        file_id = uri.replace(self.ID_PREFIX, "", 1)
        request = self.service.files().get_media(  # type: ignore
            fileId=file_id
        )

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(
            buffer,
            request,  # type: ignore
        )

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buffer.getvalue()

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en Drive.

        Si la URI es 'id://', actualiza el archivo existente.
        Si la URI es 'path://', crea las carpetas necesarias y el archivo.
        """
        media = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype="application/octet-stream",
            resumable=True,
        )

        # CASO 1: El archivo ya existe (Actualización)
        if uri.startswith(self.ID_PREFIX):
            file_id = uri.replace(self.ID_PREFIX, "", 1)
            self.service.files().update(  # type: ignore
                fileId=file_id, media_body=media
            ).execute()
            return

        # CASO 2: El archivo no existe (Creación con mkdir -p)
        clean_path = uri.replace(self.PATH_PREFIX, "", 1)
        parts = [p for p in clean_path.strip("/").split("/") if p]
        file_name = parts.pop()  # El último elemento es el archivo

        # Resolver/Crear estructura de carpetas
        parent_id = self._ensure_path_exists(parts)

        # Crear el archivo final en la carpeta destino
        file_metadata = {"name": file_name, "parents": [parent_id]}
        self.service.files().create(  # type: ignore
            body=file_metadata, media_body=media, fields="id"
        ).execute()

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista IDs de archivos bajo un prefijo.
        Devuelve los IDs con el prefijo 'id://' para que el mapper
        pueda reconvertirlos a rutas lógicas.
        """
        # Nota: scan es complejo en Drive API sin rutas.
        # Aquí se asume que 'prefix' es un ID de carpeta tras ser procesado por el mapper.
        if not prefix.startswith(self.ID_PREFIX):
            return []

        folder_id = prefix.replace(self.ID_PREFIX, "", 1)
        query = f"'{folder_id}' in parents and trashed = false"

        results = (  # type: ignore
            self.service.files()  # type: ignore
            .list(q=query, fields="files(id, mimeType)")
            .execute()
            .get("files", [])
        )

        uris: list[str] = []
        for f in results:  # type: ignore
            if f["mimeType"] != "application/vnd.google-apps.folder":
                full_id = f"{self.ID_PREFIX}{f['id']}"
                uris.append(full_id)

        return uris

    def _ensure_path_exists(self, folder_parts: list[str]) -> str:
        """
        Implementación de mkdir -p para Google Drive.
        Retorna el ID de la última carpeta de la jerarquía.
        """
        current_parent = "root"

        for part in folder_parts:
            query = (
                f"name = '{part}' and '{current_parent}' in parents "
                "and mimeType = 'application/vnd.google-apps.folder' "
                "and trashed = false"
            )
            if results := (
                self.service.files()  # type: ignore
                .list(q=query, fields="files(id)")
                .execute()
                .get("files", [])
            ):
                current_parent = results[0]["id"]
            else:
                # Crear la carpeta si no existe
                meta = {
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [current_parent],
                }
                folder = (
                    self.service.files()  # type: ignore
                    .create(body=meta, fields="id")
                    .execute()
                )
                current_parent = folder.get("id")

        return tp.cast(str, current_parent)
