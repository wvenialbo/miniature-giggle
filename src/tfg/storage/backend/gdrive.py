import collections.abc as col
import io
import mimetypes
import pathlib as pl
import typing as tp

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from ..cache import CacheBase

if tp.TYPE_CHECKING:
    # Importamos el tipo específico para Drive v3
    from googleapiclient._apis.drive.v3.resources import DriveResource, File

from .base import StorageBackend

DriveCache = CacheBase[str]

ID_PREFIX = "id://"
PATH_PREFIX = "path://"
PATH_ID_SEPARATOR = "|"
EMPTY_VALUE = ""


class GoogleDriveBackend(StorageBackend):
    """
    Backend de almacenamiento para Google Drive API v3.

    Esta clase proporciona métodos para interactuar con Google Drive API
    v3, incluyendo operaciones de E/S para leer, escribir, eliminar y
    listar archivos.  No conoce rutas lógicas, realiza operaciones
    crudas de E/S sobre una ruta nativa absoluta.

    Methods
    -------
    create_path(uri: str) -> str
        Crea una ruta o contenedor en el backend de almacenamiento.
    delete(uri: str) -> None
        Elimina los datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    read(uri: str) -> bytes
        Lee los datos desde la URI especificada.
    read_chunks(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Lee los datos desde la URI especificada de forma segmentada.
    scan(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    size(uri: str) -> int
        Obtiene el tamaño en bytes del objeto en la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI especificada.

    Notes
    -----
    - Implementa operaciones de E/S utilizando identificadores nativos
      ('id://...') y maneja la creación de rutas inexistentes mediante
      prefijos especiales ('path://...').
    """

    def __init__(self, service: Resource, cache: DriveCache) -> None:
        self._service = tp.cast("DriveResource", service)
        self._cache = cache

    def __repr__(self) -> str:
        return f"GoogleDriveBackend({repr(self._service)})"

    def create_path(self, *, uri: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

        Este método puede recibir dos tipos de entrada:
            1. Un ID nativo del backend (cuando el recurso ya existe).
            2. Una ruta POSIX (cuando el recurso no existe y se va a
               crear).

        - En el primer caso, el método es idempotente y devuelve el
          mismo ID.
        - En el segundo caso, crea recursivamente todos los contenedores
          intermedios necesarios, emulando el comportamiento de `mkdir
          -p`.  Esta operación es llamada por capas superiores antes de
          `write()` para garantizar que exista el contenedor destino.

        Parameters
        ----------
        uri : str
            Puede ser un ID nativo del backend (si el recurso ya existe)
            o una ruta genérica (POSIX). Ej:
            'experimentos/2024/dataset1'.

        Returns
        -------
        str
            URI nativa absoluta del contenedor creado o existente en el
            backend.  Ej: 's3://bucket/experimentos/2024/dataset1/' o la
            clave equivalente.

        Raises
        ------
        ValueError
            Si la URI no tiene un esquema soportado.
        """
        # Caso 1: ID ya existe, retornamos tal cual
        if uri.startswith(ID_PREFIX):
            return uri

        # CASO 2: Creación de archivo nuevo (requiere mkdir recursivo)
        if uri.startswith(PATH_PREFIX):
            return self._do_create_path(uri)

        raise ValueError(f"Esquema de URI no soportado: '{uri}'")

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Elimina archivos u objetos individuales. No elimina contenedores
        o directorios completos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
            Ejemplo: 's3://bucket/experimentos/data.csv'.

        Notes
        -----
        - Operación idempotente: si la URI no existe, no se genera
          error.
        - No debe utilizarse para eliminar contenedores/directorios.
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
        Verifica si los datos existen en la URI especificada.

        Verifica la existencia de un archivo u objeto individual, no de
        contenedores o prefijos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bool
            True si existe un archivo u objeto en la URI, False en caso
            contrario (incluyendo cuando la URI apunta a un contenedor o
            no existe).
        """
        return uri.startswith(ID_PREFIX)

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bytes
            Contenido binario del archivo u objeto.

        Raises
        ------
        FileNotFoundError
            Si la URI no existe.
        """
        uri = self._check_uri(uri)
        file_id = self._strip_prefix(uri, ID_PREFIX)
        request = self._service.files().get_media(fileId=file_id)

        # Buffer en memoria para recibir los bytes
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return fh.getvalue()

    def read_chunks(
        self, *, uri: str, chunk_size: int = 1024 * 1024
    ) -> col.Iterable[bytes]:
        """
        Lee los datos desde la URI especificada de forma segmentada.

        Permite procesar archivos grandes sin cargarlos por completo en
        RAM y facilita el reporte de progreso en tiempo real.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        chunk_size : int, optional
            Tamaño sugerido de cada fragmento en bytes. Debe ser un
            entero positivo con valor mínimo de 1MiB. Por defecto 1MiB.

        Yields
        ------
        bytes
            Fragmentos del contenido binario del archivo.
        """
        uri = self._check_uri(uri)
        file_id = self._strip_prefix(uri, ID_PREFIX)

        request = self._service.files().get_media(
            fileId=file_id, supportsAllDrives=True
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)

        done = False
        while not done:
            _, done = downloader.next_chunk()
            yield fh.getvalue()
            fh.seek(0)
            fh.truncate(0)

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista las URI que comienzan con el prefijo especificado.

        Este método debe manejar internamente la paginación del backend
        y devolver una lista completa de URIs que coinciden con el
        prefijo.

        Parameters
        ----------
        prefix : str
            Prefijo de URI nativa absoluta (completa o parcial) válida
            para el backend. Puede incluir o no el separador de
            contenedor.

        Returns
        -------
        list[str]
            Lista de URIs nativas absolutas que comienzan con el
            prefijo.  Solo incluye archivos/objetos, no contenedores
            vacíos.

        Notes
        -----
        - Solo devuelve URIs de archivos u objetos individuales; no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        """
        # Si el prefijo es un path inexistente, no hay nada que listar
        if prefix.startswith(PATH_PREFIX):
            return []

        folder_id = self._strip_prefix(prefix, ID_PREFIX)
        results: list[str] = []
        page_token = EMPTY_VALUE

        query = f"'{folder_id}' in parents and trashed = false"

        while True:
            response = (
                self._service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id)",
                    pageToken=page_token,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                )
                .execute()
            )

            files = response.get("files", [])
            ids = [f"{ID_PREFIX}{f.get('id')}" for f in files]
            results.extend(ids)

            page_token = response.get("nextPageToken") or ""
            if not page_token:
                break

        return results

    def size(self, *, uri: str) -> int:
        """
        Obtiene el tamaño en bytes del objeto en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        int
            Tamaño en bytes.
        """
        uri = self._check_uri(uri)
        file_id = self._strip_prefix(uri, ID_PREFIX)

        file = (
            self._service.files()
            .get(fileId=file_id, fields="size", supportsAllDrives=True)
            .execute()
        )
        return int(file.get("size", 0))

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        data : bytes
            Contenido binario a escribir.

        Raises
        ------
        ValueError
            Si la URI no tiene un esquema soportado.

        Notes
        -----
        - Si el contenedor padre no existe, el comportamiento depende
          del backend. Algunos lo crearán automáticamente, otros
          fallarán.  Se recomienda llamar a `create_path()` primero.
        - Operación atómica: o se escriben todos los datos o falla.
        - Al finalizar una operación exitosa, la URI debe apuntar a un
          archivo u objeto individual.
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
                raise ValueError(f"URI de creación malformada: '{uri}'")

            parent_path, filename, parent_id = clean_uri.split(
                PATH_ID_SEPARATOR, 2
            )

            # Crear el archivo final
            file_metadata: "File" = {"name": filename, "parents": [parent_id]}

            response = (
                self._service.files()
                .create(
                    body=file_metadata,
                    media_body=media_body,
                    supportsAllDrives=True,
                )
                .execute()
            )

            full_logical_path = pl.PurePosixPath(parent_path) / filename
            file_id = response.get("id") or ""  # patched!
            self._cache.set(str(full_logical_path), file_id)

            return

        raise ValueError(f"Esquema de URI no soportado: '{uri}'")

    def _check_uri(self, uri: str) -> str:
        if uri.startswith(PATH_PREFIX):
            raise FileNotFoundError(f"El objeto no existe: '{uri}'")
        return uri

    def _do_create_path(self, uri: str) -> str:
        # Formato esperado: "path://sub/ruta/archivo.ext|parent_id"
        clean_uri = self._strip_prefix(uri, PATH_PREFIX)
        if PATH_ID_SEPARATOR not in clean_uri:
            raise ValueError(f"URI de creación malformada: '{uri}'")

        parent_path, child_path, parent_id = clean_uri.split(
            PATH_ID_SEPARATOR, 2
        )

        # Separar carpetas del nombre del archivo final
        path_obj = pl.PurePosixPath(child_path)
        filename = path_obj.name
        folders = path_obj.parent.parts

        # Crear carpetas intermedias y obtener el ID final donde alojar
        # el archivo
        target_folder_id = self._mkdir_recursive(
            parent_path, folders, parent_id
        )

        return f"{PATH_PREFIX}{filename}{PATH_ID_SEPARATOR}{target_folder_id}"

    def _mkdir_recursive(
        self, parent: str, folders: tuple[str, ...], root_id: str
    ) -> str:
        """
        Recorre y crea carpetas si no existen.
        Retorna el ID de la carpeta más profunda.
        """
        current_parent_id: str = root_id
        current_logical_path = pl.PurePosixPath(parent)

        for folder_name in folders:
            if found_id := self._find_folder_id(
                current_parent_id, folder_name
            ):
                current_parent_id = found_id
            else:
                # Crear carpeta
                file_metadata: "File" = {
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

                created_id = folder.get("id")

                if created_id is None:
                    raise RuntimeError(
                        f"No se pudo crear la carpeta "
                        f"'{current_logical_path / folder_name}'"
                    )

                current_parent_id = created_id

            current_logical_path = current_logical_path / folder_name
            self._cache.set(str(current_logical_path), current_parent_id)

        return current_parent_id

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
        return files[0].get("id") if files else None

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
                f"Se esperaba una URI '{prefix}', se recibió: '{uri}'"
            )
        return uri[len(prefix) :]
