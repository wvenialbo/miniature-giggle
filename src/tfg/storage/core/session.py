from ..backend import StorageBackend
from ..handlers import DataHandler


class Session:
    """
    Sessión de almacenamiento de datos.

    Gestiona la interacción con el backend de almacenamiento y los
    handlers de datos.

    Parameters
    ----------
    backend : StorageBackend
        El backend de almacenamiento a utilizar.
    handlers : list[DataHandler]
        Lista de handlers de datos disponibles en la sesión.

    Attributes
    ----------
    backend : StorageBackend
        El backend de almacenamiento utilizado en la sesión.
    handlers : dict[str, DataHandler]
        Diccionario que mapea identificadores de formatos de datos a sus
        respectivos handlers.

    Methods
    -------
    get_handler(format_id: str) -> DataHandler
        Obtiene el handler para un formato de datos específico.
    """

    def __init__(
        self, *, backend: StorageBackend, handlers: list[DataHandler]
    ) -> None:
        self.backend = backend
        self.handlers = handlers

        handlers_mapping = [
            (fmt_id, handler)
            for handler in handlers
            for fmt_id in handler.format_id
        ]
        self.handler_map = dict(handlers_mapping)

    def __repr__(self) -> str:
        handlers = ", ".join([repr(h) for h in self.handlers])
        return f"Session(backend={repr(self.backend)}, handlers=[{handlers}])"

    def get_handler(self, *, id: str) -> DataHandler:
        """
        Obtiene el handler para un formato de datos específico.

        Parameters
        ----------
        id : str
            Identificador del formato de datos.

        Returns
        -------
        DataHandler
            El handler correspondiente al formato solicitado.

        Raises
        ------
        ValueError
            Si no se encuentra un handler para el formato solicitado.
        """
        if id not in self.handler_map:
            raise ValueError(f"No se encontró handler para el formato: {id}")
        return self.handler_map[id]
