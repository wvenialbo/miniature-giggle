import io
import mimetypes
import pathlib as pl
import typing as tp

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

if tp.TYPE_CHECKING:
    # Importamos el tipo específico para Drive v3
    from googleapiclient._apis.drive.v3.resources import DriveResource

from .base import StorageBackend

ID_PREFIX = "id://"
PATH_PREFIX = "path://"
PATH_ID_SEPARATOR = "|"


class GoogleDriveBackend(StorageBackend):
    """
    Backend de almacenamiento para Google Drive API v3.

    Implementa operaciones de E/S utilizando identificadores nativos
    ('id://...') y maneja la creación de rutas inexistentes mediante
    prefijos especiales ('path://...').
    """

    def __init__(self, service: "DriveResource") -> None:
        self._service = service

    def delete(self, *, uri: str) -> None:
        """
        Elimina un archivo o carpeta. Operación idempotente.
        """
        # Si recibimos un 'path://', significa que el Mapper determinó
        # que el objeto no existe. Por idempotencia, no hacemos nada.
        if uri.startswith(PATH_PREFIX):
            return

        file_id = self._strip_prefix(uri, ID_PREFIX)
        try:
            self._service.files().delete(
                fileId=file_id, supportsAllDrives=True
            ).execute()
        except HttpError as e:
            # 404 Not Found se considera éxito (idempotencia)
            if e.resp.status == 404:
                return
            raise

    def exists(self, *, uri: str) -> bool:
        """
        Verifica la existencia mediante metadatos.
        """
        if uri.startswith(PATH_PREFIX):
            return False

        file_id = self._strip_prefix(uri, ID_PREFIX)
        try:
            self._service.files().get(
                fileId=file_id, fields="id", supportsAllDrives=True
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return False
            raise

    def read(self, *, uri: str) -> bytes:
        """
        Descarga el contenido de un archivo en memoria.
        """
        if uri.startswith(PATH_PREFIX):
            raise FileNotFoundError(f"El objeto no existe: {uri}")

        file_id = self._strip_prefix(uri, ID_PREFIX)
        request = self._service.files().get_media(fileId=file_id)

        # Buffer en memoria para recibir los bytes
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return fh.getvalue()

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista los hijos directos de un ID de carpeta dado como prefijo.
        Maneja la paginación de la API.
        """
        # Si el prefijo es un path inexistente, no hay nada que listar
        if prefix.startswith(PATH_PREFIX):
            return []

        folder_id = self._strip_prefix(prefix, ID_PREFIX)
        results: list[str] = []
        page_token = None

        query = f"'{folder_id}' in parents and trashed = false"

        while True:
            response = (
                self._service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id)",
                    pageToken=page_token,  # type: ignore
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                )
                .execute()
            )

            files = response.get("files", [])
            ids = [f"{ID_PREFIX}{f['id']}" for f in files]  # type: ignore
            results.extend(ids)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe datos. Crea directorios intermedios si recibe una
        instrucción PATH_PREFIX.  Actualiza el archivo si recibe un
        ID_PREFIX.
        """
        # Preparar el stream de datos
        media_body = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype=self._guess_mime_type(uri) or "application/octet-stream",
            resumable=True,
        )

        # CASO 1: Actualización de archivo existente
        if uri.startswith(ID_PREFIX):
            file_id = self._strip_prefix(uri, ID_PREFIX)
            self._service.files().update(
                fileId=file_id, media_body=media_body, supportsAllDrives=True
            ).execute()

            return

        # CASO 2: Creación de archivo nuevo
        if uri.startswith(PATH_PREFIX):
            # Formato esperado: "path://sub/ruta/archivo.ext|parent_id"
            clean_uri = self._strip_prefix(uri, PATH_PREFIX)
            if PATH_ID_SEPARATOR not in clean_uri:
                raise ValueError(f"URI de creación malformada: {uri}")

            filename, parent_id = clean_uri.split(PATH_ID_SEPARATOR, 1)

            # Crear el archivo final
            file_metadata = {"name": filename, "parents": [parent_id]}

            self._service.files().create(
                body=file_metadata,  # type: ignore
                media_body=media_body,
                supportsAllDrives=True,
            ).execute()

            return

        raise ValueError(f"Esquema de URI no soportado: {uri}")

    def create_path(self, *, path: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.
        """
        # Caso 1: ID ya existe, retornamos tal cual
        if path.startswith(ID_PREFIX):
            return path

        # CASO 2: Creación de archivo nuevo (requiere mkdir recursivo)
        if path.startswith(PATH_PREFIX):
            return self._do_create_path(path)

        raise ValueError(f"Esquema de URI no soportado: {path}")

    def _do_create_path(self, path: str) -> str:
        # Formato esperado: "path://sub/ruta/archivo.ext|parent_id"
        clean_uri = self._strip_prefix(path, PATH_PREFIX)
        if PATH_ID_SEPARATOR not in clean_uri:
            raise ValueError(f"URI de creación malformada: {path}")

        relative_path, parent_id = clean_uri.split(PATH_ID_SEPARATOR, 1)

        # Separar carpetas del nombre del archivo final
        path_obj = pl.Path(relative_path)
        filename = path_obj.name
        folders = path_obj.parent.parts

        # Crear carpetas intermedias y obtener el ID final donde alojar
        # el archivo
        target_folder_id = self._mkdir_recursive(folders, parent_id)

        return f"{PATH_PREFIX}{filename}{PATH_ID_SEPARATOR}{target_folder_id}"

    def _mkdir_recursive(self, folders: tuple[str, ...], root_id: str) -> str:
        """
        Recorre y crea carpetas si no existen.
        Retorna el ID de la carpeta más profunda.
        """
        current_parent_id = root_id

        for folder_name in folders:
            if found_id := self._find_folder_id(
                current_parent_id, folder_name  # type: ignore
            ):
                current_parent_id = found_id
            else:
                # Crear carpeta
                file_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [current_parent_id],
                }
                folder = (
                    self._service.files()
                    .create(
                        body=file_metadata, fields="id", supportsAllDrives=True
                    )
                    .execute()
                )
                current_parent_id = folder.get("id")

        return current_parent_id  # type: ignore

    def _find_folder_id(self, parent_id: str, name: str) -> str | None:
        """Busca una carpeta específica dentro de un padre."""
        safe_name = name.replace("'", "\\'")
        query = (
            f"name = '{safe_name}' and "
            f"'{parent_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        response = (
            self._service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id)",
                pageSize=1,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )

        files = response.get("files", [])
        return files[0]["id"] if files else None  # type: ignore

    def _guess_mime_type(self, uri: str) -> str | None:
        """Intenta adivinar el mimetype basado en la extensión."""
        # Limpiamos la URI para quedarnos solo con el nombre/ruta final
        if PATH_ID_SEPARATOR in uri:
            # Caso path://ruta/archivo|id -> ruta/archivo
            clean_path = uri.split(PATH_ID_SEPARATOR)[0].replace(
                PATH_PREFIX, ""
            )
        else:
            # Caso id://123 -> no hay nombre, difícil adivinar.
            # Intentamos ver si la URI original traía info, pero
            # el backend trabaja con IDs opacos. Aquí dependemos de que
            # la capa superior o el proceso de upload maneje esto.
            # Si es id://, retornamos None y se usará octet-stream.
            return None

        mime_type, _ = mimetypes.guess_type(clean_path)
        return mime_type

    @staticmethod
    def _strip_prefix(uri: str, prefix: str) -> str:
        """Ayudante para remover un prefijo de una URI."""
        if not uri.startswith(prefix):
            raise ValueError(
                f"Se esperaba una URI '{prefix}', se recibió: {uri}"
            )
        return uri[len(prefix) :]
