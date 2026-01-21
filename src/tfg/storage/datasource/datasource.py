import collections.abc as col
import io
import typing as tp

from ..backend import StorageBackend
from ..cache import AbstractCache, DummyCache
from ..mapper import GenericURIMapper, URIMapper
from .base import Datasource
from .utils import ProgressTracker, StreamAdapter

NoopCache = DummyCache[tp.Any]

GENERIC_SUFFIX = ".*"


class DataService(Datasource):
    """
    Contexto de datos que orquesta el acceso al almacenamiento.

    Utiliza un StorageBackend para operaciones de E/S sobre un almacen
    de datos, un URIMapper para convertir entre URIs genéricas (formato
    POSIX) y nativas, y una lista de DataHandlers para manejar formatos
    específicos. Es el núcleo del sistema de almacenamiento.

    Los métodos que reciben URI esperan una URI genérica relativa a la
    ruta base (`mountpoint`). El mapeador convierte la URI genérica al
    identificador o a la ruta absoluta respecto al punto de montaje del
    backend. Esto permite que el mismo código funcione con diferentes
    backends de almacenamiento sin cambios.

    Las URIs genéricas siguen el formato POSIX con '/' como separador y
    son relativas a la raíz del contexto, que está determinado por el
    punto de montaje del ConnectionManager.

    Por ejemplo, si el punto de montaje es '/content/drive', una URI
    genérica '/dataset/profiles.npz' correspondería a la ruta nativa
    '/content/drive/dataset/profiles.npz'.

    Parameters
    ----------
    mountpoint : str
        Ruta base dentro del sistema de almacenamiento. Todas las URIs
        genéricas son relativas a esta ruta.
    backend : StorageBackend
        Backend para operaciones de E/S crudas.
    mapper : URIMapper
        Mapeador entre URIs genéricas y nativas.
    handlers : list[DataHandler]
        Lista de manejadores de formatos disponibles.

    Attributes
    ----------
    mountpoint : str
        Ruta base dentro del sistema de almacenamiento. Todas las URIs
        genéricas son relativas a esta ruta.
    backend : StorageBackend
        Backend para operaciones de E/S crudas.
    mapper : URIMapper
        Mapeador entre URIs genéricas y nativas.
    handlers : dict[str, DataHandler]
        Diccionario de manejadores de formatos disponibles, indexados
        por extensión.

    Methods
    -------
    clear_cache() -> None
        Limpia todos los objetos almacenados en la caché.
    delete(uri: str) -> None
        Elimina el recurso con la URI especificada.
    exists(uri: str) -> bool
        Verifica si existe el recurso en la URI especificada.
    get_buffer() -> io.BytesIO
        Obtiene un buffer de bytes vacío.
    get_size(uri: str) -> int
        Obtiene el tamaño en bytes del objeto en la URI especificada.
    list(prefix: str = "") -> list[str]
        Enumera objetos cuya URI comienza con el prefijo especificado.
    load(uri: str) -> io.BytesIO
        Carga un objeto desde la URI especificada.
    load_stream(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Carga un objeto desde la URI especificada en fragmentos.
    open(uri: str, chunk_size: int = 1MiB,
         tracker: ProgressTracker | None = None) -> io.BufferedReader
        Abre un stream de lectura (lazy) desde la URI especificada.
    purge_cache() -> None
        Elimina entradas expiradas de la caché.
    save(uri: str, data: io.BytesIO) -> None
        Guarda un objeto en la URI especificada.
    """

    def __init__(
        self,
        *,
        mountpoint: str = "/",
        backend: StorageBackend,
        mapper: URIMapper,
        cache: AbstractCache | None = None,
    ) -> None:
        self.mountpoint = mountpoint
        self.backend = backend
        self.mapper = mapper
        self.local_mapper = GenericURIMapper(base_path=mountpoint)
        self.cache = cache or NoopCache()

    def __repr__(self) -> str:
        return (
            "DataService("
            f"mountpoint='{self.mountpoint}', "
            f"backend={repr(self.backend)}, "
            f"mapper={repr(self.mapper)}, "
            f"cache={repr(self.cache)})"
        )

    def clear_cache(self) -> None:
        """
        Limpia todos los objetos almacenados en la caché.

        Esta operación elimina todos los objetos actualmente almacenados
        en la caché.
        """
        self.cache.clear()

    def delete(self, *, uri: str) -> None:
        """
        Elimina el recurso con la URI especificada.

        Elimina archivos u objetos individuales si existen. No elimina
        contenedores o directorios. La operación es idempotente, la URI
        puede no existir sin que se genere un error. `uri` debe ser una
        URI genérica respecto el punto de montaje del backend.

        Si el recurso se elimina correctamente, también se invalida la
        entrada correspondiente en la caché.

        Parameters
        ----------
        uri : str
            La URI genérica de los datos a eliminar.
        """
        self.backend.delete(uri=self._to_native_uri(uri))
        self.cache.invalidate(path=uri)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si existe el recurso en la URI especificada.

        Verifica si un archivo u objeto existe en la URI dada. La URI
        debe apuntar a un archivo u objeto individual. `uri` debe ser
        una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI genérica de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen en la URI dada, False en caso
            contrario.
        """
        return self.backend.exists(uri=self._to_native_uri(uri))

    def get_buffer(self) -> io.BytesIO:
        """
        Obtiene un buffer de bytes vacío.

        Returns
        -------
        io.BytesIO
            Un buffer de bytes vacío para operaciones de E/S en memoria.
        """
        return io.BytesIO()

    def get_size(self, *, uri: str) -> int:
        """
        Obtiene el tamaño en bytes del objeto en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI genérica de los datos a verificar.

        Returns
        -------
        int
            Tamaño en bytes del objeto en la URI dada.
        """
        return self.backend.size(uri=self._to_native_uri(uri))

    def is_read_only(self) -> bool:
        """
        Indica si la fuente de datos es de solo lectura.

        Returns
        -------
        bool
            True si la fuente de datos es de solo lectura, False en
            caso contrario.
        """
        return self.backend.read_only

    def list(self, *, prefix: str = "") -> list[str]:
        """
        Enumera objetos cuya URI comienza con el prefijo especificado.

        Obteniene la lista de todos los objetos cuyas URI comienzan con
        el prefijo dado. `prefix` debe ser una URI genérica, completa,
        o parcial, respecto el punto de montaje del backend. Devuelve
        una lista de URI genéricas respecto el punto de montaje del
        backend.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI listadas. Debe ser una URI
            genérica. Por defecto es una cadena vacía, que lista todas
            las URI.

        Returns
        -------
        tp.List[str]
            Una lista de URI que comienzan con el prefijo dado.
        """
        native_prefix = self._to_native_uri(uri=prefix or "/")

        return [
            self._to_generic_uri(item)
            for item in self.backend.scan(prefix=native_prefix)
        ]

    def load(self, *, uri: str) -> io.BytesIO:
        """
        Carga un objeto desde la URI especificada.

        Ideal para archivos pequeños, acceso rápido, todo en RAM. La URI
        debe apuntar a un archivo u objeto individual. `uri` debe ser
        una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI genérica de los datos a leer.

        Returns
        -------
        io.BytesIO
            Los datos leídos desde la URI dada.
        """
        native_uri = self._to_native_uri(uri)
        return io.BytesIO(self.backend.read(uri=native_uri))

    def open(
        self,
        *,
        uri: str,
        chunk_size: int = 1024 * 1024,
        tracker: ProgressTracker | None = None,
    ) -> io.BufferedReader:
        """
        Abre un stream de lectura (lazy) desde la URI especificada.

        Ideal para archivos grandes que se pasan a funcioness que pueden
        trabajar con streams de bytes en memoria. La URI debe apuntar a
        un archivo u objeto individual. `uri` debe ser una URI genérica
        respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a abrir.
        chunk_size : int, optional
            Tamaño sugerido de cada fragmento en bytes. Debe ser un
            entero positivo con valor mínimo de 1MiB. Por defecto 1MiB.
        tracker : ProgressTracker | None, optional
            Una función que encapsula un iterable de bytes y reporta el
            progreso de la operación de lectura. Si es None, no se
            reporta el progreso.  Por defecto None.

        Returns
        -------
        io.BufferedReader
            Un objeto de flujo de E/S para los datos en la URI dada.
        """
        iterator = self.stream(uri=uri, chunk_size=chunk_size)

        if tracker is not None:
            total_size = self.get_size(uri=uri)
            description = uri.split("/")[-1]
            iterator = tracker(
                iterable=iterator,
                total_size=total_size,
                description=description,
            )

        return io.BufferedReader(StreamAdapter(iterator))

    def purge_cache(self) -> None:
        """
        Elimina entradas expiradas de la caché.

        Las implementaciones pueden definir políticas de expiración para
        los objetos almacenados en la caché (ejemplo: tiempo de vida
        máximo). Esta función elimina todos los objetos que hayan
        expirado según dichas políticas.
        """
        self.cache.purge()

    def save(self, *, uri: str, data: io.BytesIO) -> None:
        """
        Guarda un objeto en la URI especificada.

        Guarda los datos en la URI dada. Al finalizar la operación, la
        URI debe apuntar a un archivo u objeto individual. `uri` debe
        ser una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI genérica donde se escribirán los datos.
        data : io.BytesIO
            Los datos a escribir en la URI dada.
        """
        native_uri = self._to_native_uri(uri)
        native_uri = self.backend.create_path(uri=native_uri)
        self.backend.write(uri=native_uri, data=data.getvalue())

    def stream(
        self, *, uri: str, chunk_size: int = 1024 * 1024
    ) -> col.Iterable[bytes]:
        """
        Carga un objeto desde la URI especificada en fragmentos.

        Carga los datos desde la URI dada en fragmentos de tamaño
        `chunk_size`. La URI debe apuntar a un archivo u objeto
        individual. `uri` debe ser una URI genérica respecto el punto
        de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        chunk_size : int, optional
            Tamaño sugerido de cada fragmento en bytes. Debe ser un
            entero positivo con valor mínimo de 1MiB. Por defecto 1MiB.

        Yields
        ------
        bytes
            Fragmentos de datos leídos desde la URI dada.
        """
        native_uri = self._to_native_uri(uri)
        yield from self.backend.read_chunks(
            uri=native_uri, chunk_size=chunk_size
        )

    def _to_generic_uri(self, uri: str) -> str:
        """Convierte una URI nativa a genérica respecto el punto de montaje."""
        absolute_uri = self.mapper.to_generic(uri)
        return self.local_mapper.to_relative(absolute_uri)

    def _to_native_uri(self, uri: str) -> str:
        """Convierte una URI genérica a nativa respecto el punto de montaje."""
        absolute_uri = self.local_mapper.to_absolute(uri)
        return self.mapper.to_native(absolute_uri)
