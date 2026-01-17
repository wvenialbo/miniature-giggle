import collections.abc as col
import re
import urllib.parse as url

import requests

from ..backend import StorageBackend
from ..cache import CacheBase, DummyCache

NCEICache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]


class NCEIBackend(StorageBackend):
    """
    Backend de solo lectura para repositorios HTTP de NCEI.

    Esta clase gestiona operaciones de lectura y listado de archivos
    desde repositorios HTTP públicos de NCEI. No soporta operaciones de
    escritura, eliminación o creación de rutas. Utiliza la librería
    `requests` para manejar las solicitudes HTTP y cumple con el
    protocolo `StorageBackend`.

    Parameters
    ----------
    session : requests.Session
        Sesión HTTP configurada para realizar solicitudes al repositorio
        NCEI.
    scan_cache : CacheBase[list[str]] | None, optional
        Estrategia de caché para los resultados de `scan`. Si es None,
        se utiliza un `DummyCache` (sin caché).

    Attributes
    ----------
    scan_cache : CacheBase[list[str]]
        Instancia de caché para optimizar operaciones de listado (scan).
    session : requests.Session
        Sesión HTTP configurada para realizar solicitudes al repositorio
        NCEI.

    Methods
    -------
    create_path(uri: str) -> str
        No soportado. Lanza RuntimeError.
    delete(uri: str) -> None
        No soportado. Lanza RuntimeError.
    exists(uri: str) -> bool
        Verifica si un recurso existe en la URI dada.
    read(uri: str) -> bytes
        Lee y devuelve el contenido del recurso en la URI dada.
    read_chunks(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Lee los datos desde la URI especificada de forma segmentada.
    scan(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    write(uri: str, data: bytes) -> None
        No soportado. Lanza RuntimeError.
    """

    def __init__(
        self, session: requests.Session, scan_cache: NCEICache | None = None
    ) -> None:
        self.scan_cache = scan_cache or NoopCache()
        self.session = session

    def __repr__(self) -> str:
        return f"NCEIBackend(scan_cache={repr(self.scan_cache)})"

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
        raise RuntimeError("NCEIBackend no soporta creación de rutas.")

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
        raise RuntimeError(
            "NCEIBackend no soporta operaciones de eliminación."
        )

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
        response = self.session.head(uri, timeout=10)
        return response.status_code == 200

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
        response = self.session.get(uri, timeout=15)
        response.raise_for_status()
        return response.content

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
        if chunk_size < 1024 * 1024:
            raise ValueError("chunk_size debe ser al menos 1MB.")

        # Es vital usar stream=True para no descargar el archivo al hacer el get
        response = self.session.get(uri, timeout=15, stream=True)
        response.raise_for_status()

        # iter_content se encarga de ir pidiendo fragmentos al socket
        # conforme los necesitamos
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # Filtrar keep-alive chunks
                yield chunk

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
        # El prefijo en este caso es una URL de directorio
        folder_url = prefix if prefix.endswith("/") else f"{prefix}/"

        # Intentar recuperar de caché si existe
        if self.scan_cache:
            cached = self.scan_cache.get(folder_url)
            if cached is not None:
                return cached

        response = self.session.get(folder_url, timeout=15)
        if response.status_code != 200:
            return []

        # Extraer enlaces href del HTML (lógica heredada de
        # DatasourceNCEI)
        href_links: list[str] = re.findall(
            r'<a\s+href="([^"]+)"', response.text
        )

        # Normalizar URLs: filtrar las que suben de nivel y convertir a
        # absolutas
        results: list[str] = []
        for href in href_links:
            if href.startswith("?") or ".." in href:
                continue

            # Unir para asegurar URIs absolutas nativas
            full_url = url.urljoin(folder_url, href)
            results.append(full_url)

        if self.scan_cache:
            self.scan_cache.set(folder_url, results)

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
        response = self.session.head(uri, timeout=10)
        response.raise_for_status()

        # El header puede no existir si el servidor usa chunked encoding,
        # en ese caso devolvemos 0 o manejamos la incertidumbre.
        return int(response.headers.get("Content-Length", 0))

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
        raise RuntimeError("NCEIBackend no soporta operaciones de escritura.")
