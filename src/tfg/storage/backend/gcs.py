import contextlib
import typing as tp
from collections.abc import Iterator

from google.cloud import storage
from google.cloud.exceptions import NotFound

from ..cache import CacheBase, DummyCache
from .base import StorageBackend

# Definición de tipos para el caché
GCSCache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]

# Constantes de contexto
ID_PREFIX = "gs://"
SEPARATOR = "/"


class GCSBackend(StorageBackend):
    """
    Backend de almacenamiento para Google Cloud Storage.

    Esta clase gestiona operaciones de lectura, escritura, eliminación y
    listado de objetos en buckets de GCS. Utiliza `google-cloud-storage`
    como SDK subyacente y cumple con el protocolo `StorageBackend`.

    Attributes
    ----------
    bucket_name : str
        Nombre del bucket de GCS sobre el cual opera esta instancia.
    client : storage.Client
        Cliente autenticado de Google Cloud Storage.
    scan_cache : CacheBase[list[str]]
        Instancia de caché para optimizar operaciones de listado (scan).
    """

    def __init__(
        self,
        bucket: str,
        client: "storage.Client",
        scan_cache: GCSCache | None = None,
    ) -> None:
        """
        Inicializa el backend de GCS.

        Parameters
        ----------
        bucket : str
            Nombre del bucket de GCS.
        client : storage.Client
            Cliente de Google Cloud Storage ya instanciado y
            autenticado.
        scan_cache : CacheBase[list[str]] | None, optional
            Estrategia de caché para los resultados de `scan`. Si es
            None, se utiliza un `DummyCache` (sin caché).
        """
        self.bucket_name = bucket
        self.client = client
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
        blob = self._get_blob(uri)

        with contextlib.suppress(NotFound):
            blob.delete()

        # Importante: Invalidar el caché al modificar la estructura
        self.scan_cache.clear()

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
        blob = self._get_blob(uri)
        # blob.exists() realiza una llamada a la API
        return blob.exists()

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
        blob = self._get_blob(uri)
        try:
            return blob.download_as_bytes()
        except NotFound as e:
            raise FileNotFoundError(
                f"Objeto no encontrado en GCS: '{uri}'"
            ) from e

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
        # Intentar recuperar de caché
        cached = self.scan_cache.get(prefix)
        if cached is not None:
            return cached

        bucket_name, blob_prefix = self._split_uri(prefix)
        # Obtener referencia al bucket sin llamada de red explícita aquí
        bucket = self.client.bucket(bucket_name)

        # list_blobs maneja la paginación automáticamente
        blobs = tp.cast(
            Iterator[storage.Blob],
            self.client.list_blobs(bucket, prefix=blob_prefix),
        )

        results: list[str] = []

        for blob in blobs:
            blob: storage.Blob
            # Construir la URI nativa completa
            full_uri = f"{ID_PREFIX}{bucket_name}{SEPARATOR}{blob.name}"
            results.append(full_uri)

        # Actualizar caché
        self.scan_cache.set(prefix, results)

        return results

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

        # Importante: Invalidar el caché de scan ya que la estructura cambió
        self.scan_cache.clear()

    def _get_blob(self, uri: str) -> storage.Blob:
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
