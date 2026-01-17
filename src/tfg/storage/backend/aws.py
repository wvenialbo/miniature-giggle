import collections.abc as col
import typing as tp

from botocore.config import Config
from botocore.exceptions import ClientError

from ..cache import CacheBase, DummyCache
from .base import StorageBackend

if tp.TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

AWSCache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]

S3_PREFIX = "s3://"
S3_SEPARATOR = "/"


class AWSBackend(StorageBackend):
    """
    Backend de almacenamiento para Amazon Web Services S3.

    Esta clase gestiona operaciones de lectura, escritura, eliminación y
    listado de objetos en buckets de S3. Utiliza `boto3` como SDK
    subyacente y cumple con el protocolo `StorageBackend`.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de S3 sobre el cual opera esta instancia.
    client : S3Client
        Cliente de Amazon S3 ya instanciado y autenticado.
    scan_cache : CacheBase[list[str]] | None, optional
        Estrategia de caché para los resultados de `scan`. Si es None,
        se utiliza un `DummyCache` (sin caché).

    Attributes
    ----------
    bucket_name : str
        Nombre del bucket de S3 sobre el cual opera esta instancia.
    s3 : S3Client
        Cliente autenticado de Amazon S3.
    scan_cache : CacheBase[list[str]]
        Instancia de caché para optimizar operaciones de listado (scan).

    Methods
    -------
    create_path(uri: str) -> str
        Crea una ruta o contenedor en el backend de almacenamiento.
    delete(uri: str) -> None
        Elimina un objeto en el backend de almacenamiento.
    exists(uri: str) -> bool
        Verifica si un objeto existe en el backend de almacenamiento.
    read(uri: str) -> bytes
        Lee un objeto desde el backend de almacenamiento.
    read_chunk(uri: str, chunk_size: int = 1024 * 1024) -> Iterable[bytes]
        Lee los datos desde la URI especificada de forma segmentada.
    scan(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    size(uri: str) -> int
        Obtiene el tamaño en bytes del objeto en la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe un objeto en el backend de almacenamiento.
    """

    def __init__(
        self,
        bucket: str,
        client: "S3Client",
        scan_cache: AWSCache | None = None,
        config: Config | None = None,
    ) -> None:
        self.bucket_name = bucket
        self.s3 = client
        self.scan_cache = scan_cache or NoopCache()

    def __repr__(self) -> str:
        return (
            f"AWSBackend(bucket='{self.bucket_name}', "
            f"client={repr(self.s3)}, "
            f"scan_cache={repr(self.scan_cache)})"
        )

    def create_path(self, *, uri: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

        En AWS S3, al ser un almacenamiento de objetos plano, no existen
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
        Elimina un objeto en el backend de almacenamiento.

        Parameters
        ----------
        uri : str
            URI nativa o ruta genérica del objeto a eliminar.
        """
        bucket, key = self._split_uri(uri)
        self.s3.delete_object(Bucket=bucket, Key=key)
        self.scan_cache.clear()

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si un objeto existe en el backend de almacenamiento.

        Parameters
        ----------
        uri : str
            URI nativa o ruta genérica del objeto a verificar.

        Returns
        -------
        bool
            True si el objeto existe, False en caso contrario.
        """
        bucket, key = self._split_uri(uri)
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def read(self, *, uri: str) -> bytes:
        """
        Lee un objeto desde el backend de almacenamiento.

        Parameters
        ----------
        uri : str
            URI nativa o ruta genérica del objeto a leer.

        Returns
        -------
        bytes
            Contenido del objeto leído.
        """
        bucket, key = self._split_uri(uri)
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        except ClientError as e:
            raise FileNotFoundError(
                f"Objeto no encontrado en AWS: '{uri}'"
            ) from e

    def read_chunk(
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
            entero positivo con valor mínimo de 1MB. Por defecto 1MB.

        Yields
        ------
        bytes
            Fragmentos del contenido binario del archivo.
        """
        if chunk_size < 1024 * 1024:
            raise ValueError("chunk_size debe ser al menos 1MB.")

        bucket, key = self._split_uri(uri)
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)

            # StreamingBody de boto3 tiene este método optimizado para
            # streaming
            yield from response["Body"].iter_chunks(chunk_size=chunk_size)

        except ClientError as e:
            raise FileNotFoundError(
                f"Objeto no encontrado en AWS para streaming: '{uri}'"
            ) from e

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista las URI que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            Prefijo para filtrar los objetos a escanear.

        Returns
        -------
        list[str]
            Lista de URIs de los objetos que coinciden con el prefijo.
        """
        # Intentar recuperar de caché
        cached = self.scan_cache.get(prefix)
        if cached is not None:
            return cached

        bucket, key_prefix = self._split_uri(prefix)
        paginator = self.s3.get_paginator("list_objects_v2")
        results: list[str] = []

        for page in paginator.paginate(Bucket=bucket, Prefix=key_prefix):
            if "Contents" in page:
                results.extend(
                    f"{S3_PREFIX}{bucket}/{obj.get('Key')}"
                    for obj in page["Contents"]
                )
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
        bucket, key = self._split_uri(uri)
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            return response["ContentLength"]
        except ClientError as e:
            raise FileNotFoundError(
                f"No se pudo obtener el tamaño de: '{uri}'"
            ) from e

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe un objeto en el backend de almacenamiento.

        Parameters
        ----------
        uri : str
            URI nativa o ruta genérica donde se escribirá el objeto.
        data : bytes
            Contenido del objeto a escribir.
        """
        bucket, key = self._split_uri(uri)
        # Inferencia simple de ContentType podría ir aquí o en el handler
        self.s3.put_object(Bucket=bucket, Key=key, Body=data)
        # Importante: Invalidar el cache de scan ya que la estructura cambió
        self.scan_cache.clear()

    def _split_uri(self, uri: str) -> tuple[str, str]:
        if not uri.startswith(S3_PREFIX):
            raise ValueError(f"URI inválida para AWS: '{uri}'")
        parts = uri[len(S3_PREFIX) :].split(S3_SEPARATOR, 1)
        return parts[0], parts[1] if len(parts) > 1 else ""
