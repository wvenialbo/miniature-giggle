import typing as tp


class DataHandler(tp.Protocol):
    """
    Protocolo para el manejo de formatos de datos.

    Define los métodos requeridos para cualquier implementación de
    handler de datos.

    Methods
    -------
    load(stream: tp.BinaryIO) -> tp.Any
        Carga datos desde un flujo binario.
    save(data: tp.Any, stream: tp.BinaryIO) -> None
        Guarda datos en un flujo binario.
    format_id -> str
        Identificador único del formato de datos manejado por este
        handler.
    """

    def load(self, stream: tp.BinaryIO) -> tp.Any:
        """
        Carga datos desde un flujo binario.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los datos.

        Returns
        -------
        tp.Any
            Datos cargados desde el flujo.
        """
        ...

    def save(self, data: tp.Any, stream: tp.BinaryIO) -> None:
        """
        Guarda datos en un flujo binario.

        Parameters
        ----------
        data : tp.Any
            Datos a guardar en el flujo.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos.
        """
        ...

    @property
    def format_id(self) -> str:
        """
        Identificador único del formato de datos manejado por este
        handler.

        Returns
        -------
        str
            Identificador del formato de datos.
        """
        ...
