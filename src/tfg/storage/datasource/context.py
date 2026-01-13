import io
import pathlib as pl
import types
import typing as tp

from ..backend import StorageBackend
from ..connector import ConnectionManager
from ..handler import DataHandler
from ..uri import URIMapper
from .base import Datasource


class DatasourceContext(Datasource):
    """
    Contexto de datos que orquesta el acceso al almacenamiento.

    Coordina un ConnectionManager, StorageBackend, URIMapper y
    DataHandlers para proporcionar operaciones de alto nivel con URIs
    genéricas (formato POSIX). Es el núcleo del sistema de
    almacenamiento.

    Parameters
    ----------
    connection : ConnectionManager
        Gestor de la conexión con el sistema de almacenamiento.
    backend : StorageBackend
        Backend para operaciones de E/S crudas.
    mapper : URIMapper
        Mapeador entre URIs genéricas y nativas.
    handlers : list[DataHandler]
        Lista de manejadores de formatos disponibles.

    Attributes
    ----------
    connection : ConnectionManager
        Gestor de la conexión con el sistema de almacenamiento.
    backend : StorageBackend
        Backend para operaciones de E/S crudas.
    mapper : URIMapper
        Mapeador entre URIs genéricas y nativas.
    handlers : dict[str, DataHandler]
        Diccionario de manejadores de formatos disponibles, indexados
        por extensión.

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

    def __init__(
        self,
        *,
        connection: ConnectionManager,
        backend: StorageBackend,
        mapper: URIMapper,
        handlers: list[DataHandler],
    ) -> None:
        self.connection = connection
        self.backend = backend
        self.mapper = mapper
        self.handlers = self._build_handler_mapper(handlers)

    def __enter__(self) -> tp.Self:
        """
        Entra en el contexto del datasource.

        Returns
        -------
        tp.Self
            La instancia del datasource.
        """
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None:
        """
        Garantiza el cierre al salir del bloque with.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Tipo de excepción si se produjo una.
        exc_val : BaseException | None
            Valor de la excepción si se produjo una.
        exc_tb : types.TracebackType | None
            Rastreo de la excepción si se produjo.

        Returns
        -------
        bool | None
            True para suprimir la excepción, False o None para
            propagarla.
        """
        self.close()

    def __repr__(self) -> str:
        handlers = ", ".join([repr(h) for h in self.handlers])
        return (
            "DataSourceContext("
            f"connection={repr(self.connection)}, "
            f"backend={repr(self.backend)}, "
            f"mapper={repr(self.mapper)}, "
            f"handlers=[{handlers}])"
        )

    def _build_handler_mapper(
        self, handlers: list[DataHandler]
    ) -> dict[str, DataHandler]:
        """Construye diccionario extensión -> handler."""
        format_ids = [
            fmt_id for handler in handlers for fmt_id in handler.format_id
        ]

        if len(format_ids) != len(set(format_ids)):
            repeated = sorted(
                {
                    fmt_id
                    for fmt_id in format_ids
                    if format_ids.count(fmt_id) > 1
                }
            )
            duplicates = "', '".join(repeated)
            raise ValueError(
                "Múltiples handlers para el mismo formato de datos. "
                f"Formatos duplicados: '{duplicates}'"
            )

        return {
            fmt_id: handler
            for handler in handlers
            for fmt_id in handler.format_id
        }

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
        self.connection.close(fail=fail)

    def delete(self, *, uri: str) -> None:
        """
        Elimina el recurso con la URI especificada.

        Elimina archivos u objetos individuales si existen.  No elimina
        contenedores o directorios.  La operación es idempotente, la URI
        puede no existir sin que se genere un error.  `uri` debe ser una
        URI nativa absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        self._ensure_mounted()
        native_uri = self.mapper.to_native(uri)
        self.backend.delete(uri=native_uri)

    def _ensure_mounted(self) -> None:
        """Garantiza que el almacenamiento esté montado."""
        self.connection.ensure_mounted()

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si existe el recurso en la URI especificada.

        Verifica si un archivo u objeto existe en la URI dada.  La URI
        debe apuntar a un archivo u objeto individual.  `uri` debe ser
        una URI nativa absoluta completa válida para el backend.

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
        self._ensure_mounted()
        native_uri = self.mapper.to_native(uri)
        return self.backend.exists(uri=native_uri)

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
        return self.handlers.get(format_id)

    def _get_handler_for_uri(self, uri: str) -> DataHandler:
        """Obtiene el handler apropiado para una URI genérica."""
        suffix = pl.PurePosixPath(uri).suffix

        if not suffix:
            raise ValueError(
                f"La URI '{uri}' no tiene extensión de archivo reconocida."
            )

        if suffix not in self.handlers:
            available_formats = ", ".join(self.handlers.keys())
            raise ValueError(
                f"No hay un handler registrado para la extensión '{suffix}'. "
                f"Formatos disponibles: '{available_formats}'"
            )

        return self.handlers[suffix]

    def load(self, *, uri: str) -> tp.Any:
        """
        Carga un objeto desde la URI especificada.

        Carga los datos desde la URI dada.  La URI debe apuntar a un
        archivo u objeto individual.  `uri` debe ser una URI nativa
        absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.

        Returns
        -------
        bytes
            Los datos leídos desde la URI dada.
        """
        self._ensure_mounted()

        handler = self._get_handler_for_uri(uri)

        native_uri = self.mapper.to_native(uri)
        raw_data = self.backend.read(uri=native_uri)

        return handler.load(stream=io.BytesIO(raw_data))

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

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            abierta después de la llamada, False en caso contrario.
        """
        self.connection.open(fail=fail)

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
        repeated = set(handler.format_id) & set(self.handlers.keys())
        if repeated and not replace:
            duplicates = "', '".join(sorted(repeated))
            raise ValueError(
                "Ya existe un handler para alguna de las extensiones: "
                f"'{duplicates}'. Use un formato diferente o reemplace "
                "el handler existente."
            )

        self.handlers |= dict.fromkeys(handler.format_id, handler)

    def remove_handler(self, *, format_id: str) -> None:
        """
        Elimina el handler para una extensión.

        Parameters
        ----------
        format_id : str
            Identificador del formato (extensión) del handler a eliminar.
        """
        self.handlers.pop(format_id, None)

    def replace_handler(self, *, handler: DataHandler) -> None:
        """
        Reemplaza un manejador de formato o reemplaza uno existente.

        Reemplaza handlers existentes para las extensiones del nuevo
        handler.  Si no existe, lo añade.
        """
        self.register_handler(handler=handler, replace=True)

    def save(self, *, data: tp.Any, uri: str) -> None:
        """
        Guarda un objeto en la URI especificada.

        Guarda los datos en la URI dada.  Al finalizar la operación, la
        URI debe apuntar a un archivo u objeto individual.  `uri` debe
        ser una URI nativa absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir en la URI dada.
        """
        self._ensure_mounted()

        handler = self._get_handler_for_uri(uri)
        stream = io.BytesIO()
        handler.save(data=data, stream=stream)
        bytes_data = stream.getvalue()

        native_uri = self.mapper.to_native(uri)
        self.backend.write(uri=native_uri, data=bytes_data)

    def scan(self, *, prefix: str = "") -> list[str]:
        """
        Enumera objetos cuya URI comienza con el prefijo especificado.

        Obteniene la lista de todos los objetos cuyas URI comienzan con
        el prefijo dado.  `prefix` debe ser una URI nativa absoluta
        completa, o parcial, válida para el backend.  Devuelve una lista
        de URI nativas absolutas del backend.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI listadas.

        Returns
        -------
        tp.List[str]
            Una lista de URI que comienzan con el prefijo dado.
        """
        self._ensure_mounted()

        normalized_prefix = prefix or "/"
        native_prefix = self.mapper.to_native(normalized_prefix)

        # Obtener URIs nativas del backend
        native_items = self.backend.scan(prefix=native_prefix)

        # Convertir a URIs genéricas
        return [self.mapper.to_generic(item) for item in native_items]
