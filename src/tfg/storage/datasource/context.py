import io
import pathlib as pl
import typing as tp

from ..backend import StorageBackend
from ..handler import DataHandler
from ..uri import URIMapper
from .base import DatasourceContract


class Datasource(DatasourceContract):
    """
    Contexto de datos que orquesta el acceso al almacenamiento.

    Utiliza un StorageBackend para operaciones de E/S sobre un almacen
    de datos, un URIMapper para convertir entre URIs genéricas (formato
    POSIX) y nativas, y una lista de DataHandlers para manejar formatos
    específicos.  Es el núcleo del sistema de almacenamiento.

    Los métodos que reciben URI esperan una URI genérica relativa a la
    ruta base (`base_path`).  El mapeador convierte la URI genérica al
    identificador o a la ruta absoluta respecto al punto de montaje del
    backend.  Esto permite que el mismo código funcione con diferentes
    backends de almacenamiento sin cambios.

    Las URIs genéricas siguen el formato POSIX con '/' como separador y
    son relativas a la raíz del contexto, que está determinado por el
    punto de montaje del ConnectionManager.

    Por ejemplo, si el punto de montaje es '/content/drive', una URI
    genérica '/dataset/profiles.npz' correspondería a la ruta nativa
    '/content/drive/dataset/profiles.npz'.

    Parameters
    ----------
    base_path : str
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
    base_path : str
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
    delete(uri: str) -> None
        Elimina el recurso con la URI especificada.
    exists(uri: str) -> bool
        Verifica si existe el recurso en la URI especificada.
    load(uri: str) -> Any
        Carga un objeto desde la URI especificada.
    register_handler(handler: DataHandler, replace: bool = False) ->
    None
        Registra un manejador de formato o reemplaza uno existente.
    remove_handler(format_id: str) -> None
        Elimina el handler para una extensión.
    replace_handler(handler: DataHandler) -> None
        Reemplaza un manejador de formato o reemplaza uno existente.
    save(data: Any, uri: str) -> None
        Guarda un objeto en la URI especificada.
    scan(prefix: str = "") -> list[str]
        Enumera objetos cuya URI comienza con el prefijo especificado.
    """

    def __init__(
        self,
        *,
        base_path: str = "/",
        backend: StorageBackend,
        mapper: URIMapper,
        handlers: list[DataHandler],
    ) -> None:
        self.base_path = base_path
        self.backend = backend
        self.mapper = mapper
        self.handlers = self._build_handler_mapper(handlers)

    def __repr__(self) -> str:
        handlers = ", ".join([repr(h) for h in self.handlers])
        return (
            "DataSourceContext("
            f"base_path='{self.base_path}', "
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
            La URI genérica de los datos a eliminar.
        """
        native_uri = self.mapper.to_native(uri)
        self.backend.delete(uri=native_uri)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si existe el recurso en la URI especificada.

        Verifica si un archivo u objeto existe en la URI dada.  La URI
        debe apuntar a un archivo u objeto individual.  `uri` debe ser
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
        native_uri = self.mapper.to_native(uri)
        return self.backend.exists(uri=native_uri)

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
        archivo u objeto individual.  `uri` debe ser una URI genérica
        respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI genérica de los datos a leer.

        Returns
        -------
        bytes
            Los datos leídos desde la URI dada.
        """
        handler = self._get_handler_for_uri(uri)

        native_uri = self.mapper.to_native(uri)
        raw_data = self.backend.read(uri=native_uri)

        return handler.load(stream=io.BytesIO(raw_data))

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
        ser una URI genérica respecto el punto de montaje del backend.

        Parameters
        ----------
        uri : str
            La URI genérica donde se escribirán los datos.
        data : bytes
            Los datos a escribir en la URI dada.
        """
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
        el prefijo dado.  `prefix` debe ser una URI genérica, completa,
        o parcial, respecto el punto de montaje del backend.  Devuelve
        una lista de URI genéricas respecto el punto de montaje del
        backend.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI listadas.  Debe ser una URI
            genérica. Por defecto es una cadena vacía, que lista todas
            las URI.

        Returns
        -------
        tp.List[str]
            Una lista de URI que comienzan con el prefijo dado.
        """
        normalized_prefix = prefix or "/"
        native_prefix = self.mapper.to_native(normalized_prefix)

        # Obtener URIs nativas del backend
        native_items = self.backend.scan(prefix=native_prefix)

        # Convertir a URIs genéricas
        return [self.mapper.to_generic(item) for item in native_items]
