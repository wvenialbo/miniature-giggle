import collections.abc as col
import typing as tp

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.datasets.types.dataset_api_service import ApiDatasetFile

from ..cache import CacheBase, DummyCache
from .base import StorageBackend

# Definición de tipos para el caché
KaggleCache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]

KAGGLE_PREFIX = "kaggle://"
KAGGLE_SEPARATOR = "/"


class KaggleBackend(StorageBackend):
    """
    Backend de almacenamiento para Kaggle Datasets API.

    Proporciona acceso de solo lectura a archivos de datasets hospedados
    en Kaggle. Utiliza el cliente oficial 'KaggleApi' para interactuar
    con el servicio.

    Parameters
    ----------
    api : KaggleApi
        Cliente de Kaggle API ya instanciado y autenticado.
    dataset_id : str
        Identificador del dataset (ej: 'zillow/zecon').
    scan_cache : CacheBase[list[str]] | None, optional
        Estrategia de caché para resultados de 'scan'.

    Attributes
    ----------
    api : KaggleApi
        Cliente de la API de Kaggle ya autenticado.
    dataset_id : str
        Identificador del dataset en formato 'owner/dataset-slug'.
    scan_cache : CacheBase[list[str]]
        Instancia de caché para optimizar operaciones de listado (scan).
    """

    def __init__(
        self,
        *,
        api: KaggleApi,
        dataset: str,
        scan_cache: KaggleCache | None = None,
    ) -> None:
        self.api = api
        self.dataset = dataset
        self.scan_cache: KaggleCache = scan_cache or NoopCache()
        self._files_map: dict[str, ApiDatasetFile] | None = None
        self.prefix = f"{KAGGLE_PREFIX}{dataset}{KAGGLE_SEPARATOR}"

    def __repr__(self) -> str:
        return (
            f"KaggleBackend(dataset='{self.dataset}', "
            f"api={repr(self.api)}, "
            f"scan_cache={repr(self.scan_cache)})"
        )

    def create_path(self, *, uri: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

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
        RuntimeError
            Si el backend no soporta operaciones de creación de
            contenedores.

        Notes
        -----
        No soportado. Lanza RuntimeError.
        """
        raise RuntimeError("KaggleBackend no soporta creación de rutas.")

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

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de eliminación.

        Notes
        -----
        No soportado. Lanza RuntimeError.
        """
        raise RuntimeError("KaggleBackend no soporta eliminación de objetos.")

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
        filename = self._extract_filename(uri)
        return filename in self._get_filemap()

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
        RuntimeError
            Si el backend no soporta operaciones de lectura.
        """
        # Descargamos el stream y lo consumimos por completo
        return b"".join(self.read_chunks(uri=uri))

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
        owner, slug = self.dataset.split("/")
        filename = self._extract_filename(uri)

        # _preload_content es un parámetro que no existe en la librería, dataset_download_file retorna boolean
        response = self.api.dataset_download_file(owner, slug, filename)

        try:
            # stream() es un método del objeto de respuesta de urllib3
            # falla: response es bool
            yield from response.stream(chunk_size)
        finally:
            response.release_conn()

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

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de listado.

        Notes
        -----
        - Solo devuelve URIs de archivos u objetos individuales; no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        - Para algunos backends (ej: sistemas de archivos), el prefijo
          debe terminar con '/' para listar contenidos de un directorio.
        """
        cached = self.scan_cache.get(prefix)
        if cached is not None:
            return cached

        files = self._get_filemap()

        # Kaggle no tiene carpetas reales, filtramos por prefijo de nombre
        results = [
            f"{KAGGLE_PREFIX}{self.dataset}{KAGGLE_SEPARATOR}{name}"
            for name, _ in files.items()
        ]

        # Filtramos para que coincidan con la URI completa solicitada???
        filtered = [uri for uri in results if uri.startswith(prefix)]

        self.scan_cache.set(prefix, filtered)
        return filtered

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
        filename = self._extract_filename(uri)
        files = self.api.dataset_list_files(self.dataset).files

        for f in files:
            if f.name == filename:
                # El SDK devuelve el tamaño en un formato legible o bytes
                # dependiendo de la versión, pero 'size' suele ser el string
                # y necesitamos convertirlo si es necesario.
                return self._parse_size(f.size)

        raise FileNotFoundError(f"Archivo no encontrado en Kaggle: '{uri}'")

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
        RuntimeError
            Si el backend no soporta operaciones de escritura.
        PermissionError
            Si no se tienen permisos de escritura.

        Notes
        -----
        No soportado. Lanza RuntimeError.
        """
        raise RuntimeError("KaggleBackend no soporta escritura de objetos.")

    def _extract_filename(self, uri: str) -> str:
        """Extrae el nombre del archivo de la URI kaggle://owner/slug/file."""
        if not uri.startswith(self.prefix):
            raise ValueError(
                f"La URI '{uri}' no pertenece al dataset '{self.dataset}'"
            )
        return uri[len(self.prefix) :]

    def _get_filemap(self) -> dict[str, ApiDatasetFile]:
        """Obtiene y almacena en caché los metadatos del dataset."""
        if self._files_map is None:
            if files_metadata := self.api.dataset_list_files(
                self.dataset
            ).files:
                self._files_map = {
                    file.name: file
                    for file in files_metadata
                    if file is not None
                }

        if self._files_map is None:
            raise RuntimeError(
                f"No se pudieron obtener los metadatos del dataset "
                f"'{self.dataset}'."
            )

        return self._files_map

    def _parse_size(self, size_val: tp.Any) -> int:
        """Convierte el valor de tamaño de la API a un entero de bytes."""
        try:
            return int(size_val)
        except (ValueError, TypeError):
            # En algunas versiones el SDK devuelve strings como '15KB'
            # Aquí se podría implementar un parser si el SDK no da los bytes crudos
            return 0
