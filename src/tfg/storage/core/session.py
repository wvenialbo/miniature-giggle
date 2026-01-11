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
        self, backend: StorageBackend, handlers: list[DataHandler]
    ) -> None:
        self.backend = backend
        handlers_mapping = [
            (fmt_id, handler)
            for handler in handlers
            for fmt_id in handler.format_id
        ]
        self.handlers = dict(handlers_mapping)

    def get_handler(self, format_id: str) -> DataHandler:
        """
        Obtiene el handler para un formato de datos específico.

        Parameters
        ----------
        format_id : str
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
        if format_id not in self.handlers:
            raise ValueError(
                f"No se encontró handler para el formato: {format_id}"
            )
        return self.handlers[format_id]
