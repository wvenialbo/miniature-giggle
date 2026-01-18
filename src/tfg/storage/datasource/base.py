import collections.abc as col
import io
import typing as tp

from .utils import ProgressTracker


class DatasourceContract(tp.Protocol):
    """
    Protocolo para operaciones sobre fuentes de datos.

    Utiliza un StorageBackend para operaciones de E/S sobre un almacen
    de datos, un URIMapper para convertir entre URIs genéricas (formato
    POSIX) y nativas, y una lista de DataHandlers para manejar formatos
    específicos.

    Las URIs genéricas siguen el formato POSIX con '/' como separador y
    son relativas a la raíz del contexto, que está determinado por el
    punto de montaje del ConnectionManager.

    Por ejemplo, si el punto de montaje es '/content/drive', una URI
    genérica '/dataset/profiles.npz' correspondería a la ruta nativa
    '/content/drive/dataset/profiles.npz'.

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
    open(uri: str, chunk_size: int = 1MiB,
         tracker: ProgressTracker | None = None) -> io.BufferedReader
        Abre un stream de lectura (lazy) desde la URI especificada.
    purge_cache() -> None
        Elimina entradas expiradas de la caché.
    save(uri: str, data: io.BytesIO) -> None
        Guarda un objeto en la URI especificada.
    stream(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Carga un objeto desde la URI especificada en fragmentos.
    """

    def clear_cache(self) -> None:
        """
        Limpia todos los objetos almacenados en la caché.

        Esta operación elimina todos los objetos actualmente almacenados
        en la caché.
        """
        ...

    def delete(self, *, uri: str) -> None:
        """
        Elimina el recurso con la URI especificada.

        Elimina archivos u objetos individuales si existen. No elimina
        contenedores o directorios. La operación es idempotente, la URI
        puede no existir sin que se genere un error. `uri` debe ser una
        URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        ...

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si existe el recurso en la URI especificada.

        Verifica si un archivo u objeto existe en la URI dada. La URI
        debe apuntar a un archivo u objeto individual. `uri` debe ser
        una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen en la URI dada, False en caso
            contrario.
        """
        ...

    def get_buffer(self) -> io.BytesIO:
        """
        Obtiene un buffer de bytes vacío.

        Returns
        -------
        io.BytesIO
            Un buffer de bytes vacío para operaciones de E/S en memoria.
        """
        ...

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
        ...

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
            El prefijo para filtrar las URI listadas.

        Returns
        -------
        tp.List[str]
            Una lista de URI que comienzan con el prefijo dado.
        """
        ...

    def load(self, *, uri: str) -> io.BytesIO:
        """
        Carga un objeto desde la URI especificada.

        Carga los datos desde la URI dada. La URI debe apuntar a un
        archivo u objeto individual. `uri` debe ser una URI genérica
        respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.

        Returns
        -------
        io.BytesIO
            Los datos leídos desde la URI dada.
        """
        ...

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
        ...

    def purge_cache(self) -> None:
        """
        Elimina entradas expiradas de la caché.

        Las implementaciones pueden definir políticas de expiración para
        los objetos almacenados en la caché (ejemplo: tiempo de vida
        máximo). Esta función elimina todos los objetos que hayan
        expirado según dichas políticas.
        """
        ...

    def save(self, *, uri: str, data: io.BytesIO) -> None:
        """
        Guarda un objeto en la URI especificada.

        Guarda los datos en la URI dada. Al finalizar la operación, la
        URI debe apuntar a un archivo u objeto individual. `uri` debe
        ser una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : io.BytesIO
            Los datos a escribir en la URI dada.
        """
        ...

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
        ...
