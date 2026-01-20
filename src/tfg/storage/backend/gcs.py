import collections.abc as col
import contextlib
import typing as tp

from ..cache import CacheBase, DummyCache
from .base import ReadWriteBackend

Client = tp.Any

# Definición de tipos para el caché
GCSCache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]

# Constantes de contexto
ID_PREFIX = "gs://"
SEPARATOR = "/"


class GCSBackend(ReadWriteBackend):
    """
    Backend de almacenamiento para Google Cloud Storage.

    Esta clase gestiona operaciones de lectura, escritura, eliminación y
    listado de objetos en buckets de GCS. Utiliza `google-cloud-storage`
    como SDK subyacente y cumple con el protocolo `StorageBackend`.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de GCS sobre el cual opera esta instancia.
    client : Client
        Cliente autenticado de Google Cloud Storage.
    scan_cache : CacheBase[list[str]] | None, optional
        Estrategia de caché para los resultados de `scan`. Si es None,
        se utiliza un `DummyCache` (sin caché).

    Attributes
    ----------
    bucket_name : str
        Nombre del bucket de GCS sobre el cual opera esta instancia.
    client : Client
        Cliente autenticado de Google Cloud Storage.
    scan_cache : CacheBase[list[str]]
        Instancia de caché para optimizar operaciones de listado (scan).

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
    """

    def __init__(
        self,
        bucket: str,
        client: Client,
        scan_cache: GCSCache | None = None,
    ) -> None:
        from google.cloud import storage

        self.bucket_name = bucket
        self.client: storage.Client = client
        self.scan_cache: GCSCache = scan_cache or NoopCache()

    def __repr__(self) -> str:
        return (
            f"GCSBackend(bucket='{self.bucket_name}', "
            f"client={repr(self.client)}, "
            f"scan_cache={repr(self.scan_cache)})"
        )

    def create_path(self, *, uri: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

        En GCS, al ser un almacenamiento de objetos plano, no existen
        directorios reales. Este método actúa como un no-op idempotente
        para cumplir con el protocolo.

        Parameters
        ----------
        uri : str
            URI nativa o ruta genérica.

        Returns
        ----------
        str
            La misma URI proporcionada.
        """
        return uri

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Es una operación idempotente; no falla si el objeto no existe.

        Parameters
        ----------
        uri : str
            URI nativa absoluta.
        """
        from google.cloud.exceptions import NotFound

        blob = self._get_blob(uri)

        with contextlib.suppress(NotFound):
            blob.delete()

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta (ej: 'gs://bucket/data.csv').

        Returns
        -------
        bool
            True si el blob existe, False en caso contrario.
        """
        from google.cloud import storage

        blob: storage.Blob = self._get_blob(uri)

        return bool(blob.exists())

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta.

        Returns
        -------
        bytes
            Contenido binario del objeto.

        Raises
        ------
        FileNotFoundError
            Si el objeto no existe en GCS (captura `NotFound`).
        """
        from google.cloud import storage

        blob: storage.Blob = self._get_blob(uri)

        return bytes(blob.download_as_bytes())

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
        from google.cloud import storage

        blob: storage.Blob = self._get_blob(uri)
        with blob.open("rb", chunk_size=chunk_size) as f:
            while chunk := tp.cast(bytes, f.read(chunk_size)):
                yield chunk

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista las URI que comienzan con el prefijo especificado.

        Consulta primero el caché inyectado. Si no hay aciertos, realiza
        la petición a GCS y actualiza el caché.

        Parameters
        ----------
        prefix : str
            Prefijo de URI nativa absoluta.

        Returns
        -------
        list[str]
            Lista de URIs nativas absolutas encontradas.
        """
        from google.cloud import storage

        # Intentar recuperar de caché
        cached = self.scan_cache.get(prefix)
        if cached is not None:
            return cached

        bucket_name, blob_prefix = self._split_uri(prefix)
        # Obtener referencia al bucket sin llamada de red explícita aquí
        bucket = self.client.bucket(bucket_name)

        # list_blobs maneja la paginación automáticamente
        blobs = tp.cast(
            col.Iterator[storage.Blob],
            self.client.list_blobs(
                bucket, prefix=blob_prefix, fields="items(name),nextPageToken"
            ),
        )

        results: list[str] = []

        blob: storage.Blob
        for blob in blobs:
            # Construir la URI nativa completa
            full_uri = f"{ID_PREFIX}{bucket_name}{SEPARATOR}{blob.name}"
            results.append(full_uri)

        # Actualizar caché
        self.scan_cache.set(prefix, results)

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
        blob = self._get_blob(uri)
        blob.reload()  # Carga los metadatos desde la API
        return blob.size if blob.size is not None else 0

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta.
        data : bytes
            Contenido binario a escribir.
        """
        blob = self._get_blob(uri)

        # upload_from_string acepta bytes si se pasan como tal
        blob.upload_from_string(data)

    def _get_blob(self, uri: str) -> tp.Any:
        bucket_name, blob_name = self._split_uri(uri)
        bucket = self.client.bucket(bucket_name)
        return bucket.blob(blob_name)

    def _split_uri(self, uri: str) -> tuple[str, str]:
        """
        Separa la URI nativa en nombre del bucket y nombre del blob.

        Parameters
        ----------
        uri : str
            URI completa (ej: 'gs://mi-bucket/ruta/archivo.txt').

        Returns
        -------
        tuple[str, str]
            Tupla conteniendo (bucket_name, blob_name).

        Raises
        ------
        ValueError
            Si la URI no comienza con el prefijo 'gs://'.
        """
        if not uri.startswith(ID_PREFIX):
            raise ValueError(f"URI inválida para GCS: '{uri}'")

        # Eliminar prefijo y separar por el primer '/'
        # uri[5:] salta "gs://"
        parts = uri[len(ID_PREFIX) :].split(SEPARATOR, 1)

        bucket_name = parts[0]
        # Si no hay parte después del bucket, el blob_name es cadena vacía
        blob_name = parts[1] if len(parts) > 1 else ""

        return bucket_name, blob_name
