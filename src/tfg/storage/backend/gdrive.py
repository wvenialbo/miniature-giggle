import collections.abc as col
import contextlib
import io
import mimetypes
import pathlib as pl
import typing as tp

from ..cache import CacheBase
from .base import ReadWriteBackend


if tp.TYPE_CHECKING:
    from googleapiclient._apis.drive.v3.resources import DriveResource


type DriveCache = CacheBase[tuple[str, str]]
type ScanCache = CacheBase[list[str]]


EMPTY_VALUE = ""
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
ID_PREFIX = "id://"
PATH_PREFIX = "path://"
PATH_ID_SEPARATOR = "|"

HTTP_404_NOT_FOUND = 404


class GoogleDriveBackend(ReadWriteBackend):
    """
    Backend de almacenamiento para Google Drive API v3.

    Esta clase proporciona métodos para interactuar con Google Drive API
    v3, incluyendo operaciones de E/S para leer, escribir, eliminar y
    listar archivos.  No conoce rutas lógicas, realiza operaciones
    crudas de E/S sobre una ruta nativa absoluta.

    Parameters
    ----------
    service : Resource
        Instancia del cliente de Google Drive API v3.
    drive_cache : DriveCache
        Caché para mapeo de rutas lógicas a IDs nativos de Drive.
    scan_cache : ScanCache
        Caché para resultados de escaneo de directorios.

    Methods
    -------
    create_path(uri: str) -> str
        Crea una ruta o contenedor en el backend de almacenamiento.
    delete(uri: str) -> None
        Elimina los datos en el URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en el URI especificada.
    read(uri: str) -> bytes
        Lee los datos desde el URI especificada.
    read_chunks(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Lee los datos desde el URI especificada de forma segmentada.
    scan(prefix: str) -> list[str]
        Lista los URI que comienzan con el prefijo especificado.
    size(uri: str) -> int
        Obtiene el tamaño en bytes del objeto en el URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en el URI especificada.

    Notes
    -----
    - Implementa operaciones de E/S utilizando identificadores nativos
      ('id://...') y maneja la creación de rutas inexistentes mediante
      prefijos especiales ('path://...').
    """

    def __init__(
        self,
        service: "DriveResource",
        drive_cache: DriveCache,
        scan_cache: ScanCache,
    ) -> None:
        self._service = service
        self._drive_cache = drive_cache
        self._scan_cache = scan_cache

    def __repr__(self) -> str:
        return f"GoogleDriveBackend({self._service!r})"

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
            Si el URI no tiene un esquema soportado.
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
        Elimina los datos en el URI especificada.

        Elimina archivos u objetos individuales. No elimina contenedores
        o directorios completos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
            Ejemplo: 's3://bucket/experimentos/data.csv'.

        Raises
        ------
        googleapiclient.errors.HttpError
            Si el URI no existe.

        Notes
        -----
        - Operación idempotente: si el URI no existe, no se genera
          error.
        - No debe utilizarse para eliminar contenedores/directorios.
        """
        from googleapiclient.errors import HttpError

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
            if e.resp.status == HTTP_404_NOT_FOUND:
                return
            raise

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en el URI especificada.

        Verifica la existencia de un archivo u objeto individual, no de
        contenedores o prefijos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bool
            True si existe un archivo u objeto en el URI, False en caso
            contrario (incluyendo cuando el URI apunta a un contenedor o
            no existe).
        """
        # Si el Mapper devolvió un 'path://', definitivamente no existe.
        if not uri.startswith(ID_PREFIX):
            return False

        # Si tenemos un ID, debemos verificar que no sea una carpeta.
        with contextlib.suppress(Exception):
            # Consultamos el mimeType para asegurar que no es una
            # carpeta.  Un objeto "existe" para nosotros solo si
            # tiene bytes (no es carpeta)
            _, _, mime_type = self._split_id(uri)
            return mime_type != FOLDER_MIME_TYPE

        # Si hay error, el objeto no "existe" para nosotros.
        return False

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde el URI especificada.

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
            Si el URI no existe.
        """
        from googleapiclient.http import MediaIoBaseDownload

        object_id, _, object_mime = self._split_id(uri)

        if object_mime == FOLDER_MIME_TYPE:
            raise FileNotFoundError(
                f"El URI corresponde a una carpeta: '{uri}'"
            )

        request = self._service.files().get_media(
            fileId=object_id, supportsAllDrives=True
        )

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
        Lee los datos desde el URI especificada de forma segmentada.

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

        Raises
        ------
        FileNotFoundError
            Si el URI no existe.
        """
        from googleapiclient.http import MediaIoBaseDownload

        object_id, _, object_mime = self._split_id(uri)

        if object_mime == FOLDER_MIME_TYPE:
            raise FileNotFoundError(
                f"El URI corresponde a una carpeta: '{uri}'"
            )

        request = self._service.files().get_media(
            fileId=object_id, supportsAllDrives=True
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
        Lista los URI que comienzan con el prefijo especificado.

        Este método debe manejar internamente la paginación del backend
        y devolver una lista completa de los URI que coinciden con el
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
            Lista de los URI nativas absolutas que comienzan con el
            prefijo.  Solo incluye archivos/objetos, no contenedores
            vacíos.

        Raises
        ------
        FileNotFoundError
            Si el URI no corresponde a una carpeta válida.

        Notes
        -----
        - Solo devuelve los URI de archivos u objetos individuales; no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        """
        # 1. Extraer ID y ruta lógica base, formato esperado
        # id://{id}|{logical_path}
        root_folder_id, root_logical_path_str, mime_type = self._split_id(
            prefix
        )

        if mime_type != FOLDER_MIME_TYPE:
            raise FileNotFoundError(
                f"El URI no corresponde a una carpeta: '{prefix}'"
            )

        root_logical_path = pl.PurePosixPath(root_logical_path_str)

        # 2. Consultar Scan Cache (aceleración de consulta de
        #    contenedor)
        if cached_results := self._scan_cache.get(root_folder_id):
            return cached_results

        # Buscamos archivos que no sean carpetas y que estén en
        # cualquier lugar de la jerarquía bajo este prefijo.
        #
        # NOTA: Google Drive no permite filtrar por "ancestro" de forma
        # nativa fácilmente en una sola query si no es padre directo.
        #
        # Estrategia: Búsqueda por BFS (Breadth-First Search) para
        # mantener consistencia con el modelo de carpetas de Drive.

        return self._get_folder_content(root_folder_id, root_logical_path)

    def _get_folder_content(
        self, root_folder_id: str, root_logical_path: pl.PurePosixPath
    ) -> list[str]:
        all_file_uris: list[str] = []
        folders_to_scan: list[tuple[str, pl.PurePosixPath]] = [
            (root_folder_id, root_logical_path)
        ]

        while folders_to_scan:
            current_id, current_path = folders_to_scan.pop(0)
            page_token = EMPTY_VALUE

            current_container_files: list[str] = []

            # Query que trae tanto archivos como carpetas
            query = f"'{current_id}' in parents and trashed = false"

            while True:
                response = (
                    self._service
                    .files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name, mimeType)",
                        pageToken=page_token,
                        includeItemsFromAllDrives=True,
                        supportsAllDrives=True,
                    )
                    .execute()
                )

                for f in response.get("files", []):
                    f_id = f.get("id")
                    f_name = f.get("name")

                    if f_id is None or f_name is None:
                        continue

                    # Evitamos que el Mapper tenga que buscar esto en el
                    # futuro
                    f_logical_path = current_path / f_name
                    f_logical_str = str(f_logical_path)
                    f_mime = f.get("mimeType") or ""
                    self._drive_cache.set(f_logical_str, (f_id, f_mime))

                    # Si es carpeta, la agregamos a la cola para seguir
                    # bajando
                    if f_mime == FOLDER_MIME_TYPE:
                        folders_to_scan.append((f_id, f_logical_path))

                    else:
                        # Si es archivo, lo agregamos al resultado
                        # Formato nativo: id://{id}|{logical_path}
                        f_uri: str = (
                            f"{ID_PREFIX}{f_id}"
                            f"{PATH_ID_SEPARATOR}{f_logical_str}"
                            f"{PATH_ID_SEPARATOR}{f_mime}"
                        )
                        all_file_uris.append(f_uri)
                        current_container_files.append(f_uri)

                page_token = response.get("nextPageToken") or ""
                if not page_token:
                    break

            # Guardamos el contenido de esta carpeta específica para
            # futuros scans
            self._scan_cache.set(current_id, current_container_files)

        return all_file_uris

    def size(self, *, uri: str) -> int:
        """
        Obtiene el tamaño en bytes del objeto en el URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        int
            Tamaño en bytes.

        Raises
        ------
        FileNotFoundError
            Si el URI no existe.
        """
        object_id, _, object_mime = self._split_id(uri)

        if object_mime == FOLDER_MIME_TYPE:
            raise FileNotFoundError(
                f"El URI corresponde a una carpeta: '{uri}'"
            )

        file = (
            self._service
            .files()
            .get(fileId=object_id, fields="size", supportsAllDrives=True)
            .execute()
        )
        return int(file.get("size", 0))

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en el URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        data : bytes
            Contenido binario a escribir.

        Raises
        ------
        FileNotFoundError
            Si el URI no existe.
        ValueError
            Si el URI no tiene un esquema soportado.

        Notes
        -----
        - Si el contenedor padre no existe, el comportamiento depende
          del backend. Algunos lo crearán automáticamente, otros
          fallarán.  Se recomienda llamar a `create_path()` primero.
        - Operación atómica: o se escriben todos los datos o falla.
        - Al finalizar una operación exitosa, el URI debe apuntar a un
          archivo u objeto individual.
        """
        from googleapiclient.http import MediaIoBaseUpload

        if tp.TYPE_CHECKING:
            from googleapiclient._apis.drive.v3.resources import File

        # Preparar el stream de datos
        file_mime = self._guess_mime_type(uri) or "application/octet-stream"
        media_body = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype=file_mime,
            resumable=True,
        )

        # CASO 1: Actualización de archivo existente
        if uri.startswith(ID_PREFIX):
            file_id, _, file_mime = self._split_id(uri)

            if file_mime == FOLDER_MIME_TYPE:
                raise FileNotFoundError(
                    f"El URI corresponde a una carpeta: '{uri}'"
                )

            self._service.files().update(
                fileId=file_id, media_body=media_body, supportsAllDrives=True
            ).execute()

            return

        # CASO 2: Creación de archivo nuevo
        if uri.startswith(PATH_PREFIX):
            # Formato esperado:
            #   path://root/path/to/parent|filename.txt|parent_id
            parent_path, filename, parent_id = self._split_path(uri)

            # Crear el archivo final
            file_metadata: File = {"name": filename, "parents": [parent_id]}

            response = (
                self._service
                .files()
                .create(
                    body=file_metadata,
                    media_body=media_body,
                    supportsAllDrives=True,
                )
                .execute()
            )

            full_logical_path = pl.PurePosixPath(parent_path) / filename
            file_id = response.get("id") or ""  # patched!
            self._drive_cache.set(str(full_logical_path), (file_id, file_mime))

            return

        raise ValueError(f"Esquema de URI no soportado: '{uri}'")

    def _do_create_path(self, uri: str) -> str:
        # Formato esperado: "path://sub/ruta/archivo.ext|parent_id"
        parent_path, child_path, parent_id = self._split_path(uri)

        # Separar carpetas del nombre del archivo final
        path_obj = pl.PurePosixPath(child_path)
        filename = path_obj.name
        folders = path_obj.parent.parts

        # Crear carpetas intermedias y obtener el ID final donde alojar
        # el archivo
        target_folder_id = self._mkdir_recursive(
            parent_path, folders, parent_id
        )

        return (
            f"{PATH_PREFIX}{parent_path}"
            f"{PATH_ID_SEPARATOR}{filename}"
            f"{PATH_ID_SEPARATOR}{target_folder_id}"
        )

    def _find_folder_id(self, parent_id: str, name: str) -> str | None:
        safe_name = name.replace("'", "\\'")
        query = (
            f"name = '{safe_name}' and "
            f"'{parent_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        response = (
            self._service
            .files()
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

    @staticmethod
    def _guess_mime_type(uri: str) -> str | None:
        # Limpiamos el URI para quedarnos solo con el nombre/ruta final
        if PATH_ID_SEPARATOR in uri:
            # Caso path://ruta/archivo|id -> ruta/archivo
            clean_path = uri.split(PATH_ID_SEPARATOR, maxsplit=1)[0].replace(
                PATH_PREFIX, ""
            )
        else:
            # Caso id://123 -> no hay nombre, difícil adivinar.
            # Intentamos ver si el URI original traía info, pero
            # el backend trabaja con IDs opacos. Aquí dependemos de que
            # la capa superior o el proceso de upload maneje esto.
            # Si es id://, retornamos None y se usará octet-stream.
            return None

        mime_type, _ = mimetypes.guess_type(clean_path)
        return mime_type

    def _mkdir_recursive(
        self, parent: str, folders: tuple[str, ...], root_id: str
    ) -> str:
        """
        Recorre y crea carpetas si no existen.

        Parameters
        ----------
        parent : str
            Ruta lógica POSIX del contenedor raíz.
        folders : tuple[str, ...]
            Nombres de las carpetas a crear en orden.
        root_id : str
            ID nativo del contenedor raíz.

        Returns
        -------
        str
            ID nativo de la carpeta más profunda creada o existente.

        Raises
        ------
        RuntimeError
            Si no se pudo crear alguna carpeta intermedia.
        """
        if tp.TYPE_CHECKING:
            from googleapiclient._apis.drive.v3.resources import File

        current_parent_id: str = root_id
        current_logical_path = pl.PurePosixPath(parent)

        for folder_name in folders:
            if found_id := self._find_folder_id(
                current_parent_id, folder_name
            ):
                current_parent_id = found_id
            else:
                # Crear carpeta
                file_metadata: File = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [current_parent_id],
                }
                folder = (
                    self._service
                    .files()
                    .create(
                        body=file_metadata, fields="id", supportsAllDrives=True
                    )
                    .execute()
                )

                created_id = folder.get("id")

                if created_id is None:
                    raise RuntimeError(
                        "No se pudo crear la carpeta "
                        f"'{current_logical_path / folder_name}'"
                    )

                current_parent_id = created_id

            current_logical_path /= folder_name
            self._drive_cache.set(
                str(current_logical_path),
                (current_parent_id, FOLDER_MIME_TYPE),
            )

        return current_parent_id

    def _split_id(self, uri: str) -> tuple[str, str, str]:
        try:
            clean_uri = self._strip_prefix(uri, ID_PREFIX)
            object_id, object_path, object_mime = clean_uri.split(
                PATH_ID_SEPARATOR, 2
            )
            return object_id, object_path, object_mime

        except Exception as e:
            raise ValueError(f"URI de objeto malformado: '{uri}'") from e

    def _split_path(self, uri: str) -> tuple[str, str, str]:
        try:
            clean_uri = self._strip_prefix(uri, PATH_PREFIX)
            parent_path, child_path, parent_id = clean_uri.split(
                PATH_ID_SEPARATOR, 2
            )
            return parent_path, child_path, parent_id

        except Exception as e:
            raise ValueError(f"URI de contenedor malformado: '{uri}'") from e

    @staticmethod
    def _strip_prefix(uri: str, prefix: str) -> str:
        if not uri.startswith(prefix):
            raise ValueError(
                f"Se esperaba un URI '{prefix}', se recibió: '{uri}'"
            )
        return uri[len(prefix) :]
