import typing as tp

from ..handler import DataHandler


class Datasource(tp.Protocol):
    """
    Protocolo para operaciones sobre fuentes de datos.

    Utiliza un ConnectionManager para gestionar la conexión con un
    almacen de datos, un StorageBackend para operaciones de E/S, un
    URIMapper para convertir entre URIs genéricas y nativas, y una lista
    de DataHandlers para manejar formatos específicos.

    Las URIs genéricas siguen el formato POSIX con '/' como separador y
    son relativas a la raíz del contexto, que está determinado por el
    punto de montaje del ConnectionManager.

    Por ejemplo, si el punto de montaje es '/content/drive', una URI
    genérica '/dataset/profiles.npz' correspondería a la ruta nativa
    '/content/drive/dataset/profiles.npz'.

    Methods
    -------
    close(fail: bool = False) -> None
        Cierra la conexión con la fuente de datos y libera recursos.
    delete(generic_uri: str) -> None
        Elimina el recurso con la URI especificada.
    exists(generic_uri: str) -> bool
        Verifica si existe el recurso en la URI especificada.
    get_handler(format_id: str) -> DataHandler | None
        Obtiene el handler para una extensión.
    load(generic_uri: str) -> Any
        Carga un objeto desde la URI especificada.
    open(fail: bool = False) -> None
        Abre la conexión con la fuente de datos.
    register_handler(handler: DataHandler, replace: bool = False) -> None
        Registra un manejador de formato o reemplaza uno existente.
    replace_handler(handler: DataHandler) -> None
        Reemplaza un manejador de formato o reemplaza uno existente.
    save(data: Any, generic_uri: str) -> None
        Guarda un objeto en la URI especificada.
    scan(prefix: str = "") -> list[str]
        Enumera objetos cuya URI comienza con el prefijo especificado.
    """

    def close(self, *, fail: bool = False) -> None:
        """
        Cierra la conexión con la fuente de datos y libera recursos.

        Desmonta y cierra la conexión con el sistema de almacenamiento
        local o remoto.

        Si no se puede cerrar la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede cerrar la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.
        """
        ...

    def delete(self, *, uri: str) -> None:
        """
        Elimina el recurso con la URI especificada.

        Elimina archivos u objetos individuales si existen.  No elimina
        contenedores o directorios.  La operación es idempotente, la URI
        puede no existir sin que se genere un error.  `uri` debe ser una
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

        Verifica si un archivo u objeto existe en la URI dada.  La URI
        debe apuntar a un archivo u objeto individual.  `uri` debe ser
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

    def get_handler(self, *, format_id: str) -> DataHandler | None:
        """
        Obtiene el handler para una extensión.

        Parameters
        ----------
        format_id : str
            Identificador del formato (extensión) del handler.

        Returns
        -------
        DataHandler | None
            El handler registrado para la extensión dada, o None si no
            existe.
        """
        ...

    def load(self, *, uri: str) -> tp.Any:
        """
        Carga un objeto desde la URI especificada.

        Carga los datos desde la URI dada.  La URI debe apuntar a un
        archivo u objeto individual.  `uri` debe ser una URI genérica
        respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.

        Returns
        -------
        bytes
            Los datos leídos desde la URI dada.
        """
        ...

    def open(self, *, fail: bool = False) -> None:
        """
        Abre la conexión con con la fuente de datos.

        Abre la conexión con el sistema de almacenamiento remoto y lo
        monta en el punto de montaje obtenido por `get_mountpoint()`.

        Si no se puede abrir la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede abrir la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.
        """
        ...

    def register_handler(
        self, *, handler: DataHandler, replace: bool = False
    ) -> None:
        """
        Registra un manejador de formato o reemplaza uno existente.

        Parameters
        ----------
        handler : DataHandler
            Manejador de datos a registrar.
        replace : bool, optional
            Si es True, reemplaza un manejador existente con el mismo
            formato.  Si False, lanza error al encontrar conflictos.
            Por defecto es False.
        """
        ...

    def remove_handler(self, *, format_id: str) -> None:
        """
        Elimina el handler para una extensión.

        Parameters
        ----------
        format_id : str
            Identificador del formato (extensión) del handler a eliminar.
        """
        ...

    def replace_handler(self, *, handler: DataHandler) -> None:
        """
        Reemplaza un manejador de formato o reemplaza uno existente.

        Reemplaza handlers existentes para las extensiones del nuevo
        handler.  Si no existe, lo añade.
        """
        ...

    def save(self, *, data: tp.Any, uri: str) -> None:
        """
        Guarda un objeto en la URI especificada.

        Guarda los datos en la URI dada.  Al finalizar la operación, la
        URI debe apuntar a un archivo u objeto individual.  `uri` debe
        ser una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir en la URI dada.
        """
        ...

    def scan(self, *, prefix: str = "") -> list[str]:
        """
        Enumera objetos cuya URI comienza con el prefijo especificado.

        Obteniene la lista de todos los objetos cuyas URI comienzan con
        el prefijo dado.  `prefix` debe ser una URI genérica, completa,
        o parcial, respecto el punto de montaje del backend.  Devuelve
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
