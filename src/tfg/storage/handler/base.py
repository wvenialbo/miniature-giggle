import io
import typing as tp


class DataHandler(tp.Protocol):
    """
    Protocolo para manejar la carga y guardado de archivos.

    Define los métodos requeridos para cualquier implementación de
    handler de datos según su formato.

    Methods
    -------
    copy() -> DataHandler
        Crea una copia del handler de datos.
    load(stream: io.BytesIO) -> tp.Any
        Carga datos desde un flujo binario.
    save(data: tp.Any, stream: io.BytesIO) -> None
        Guarda datos en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este
        handler.
    """

    def copy(self) -> "DataHandler":
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        ...

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos desde un flujo binario.

        Parameters
        ----------
        stream : io.BytesIO
            Flujo binario desde el cual cargar los datos.

        Returns
        -------
        tp.Any
            Datos cargados desde el flujo.
        """
        ...

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos en un flujo binario.

        Parameters
        ----------
        data : tp.Any
            Datos a guardar en el flujo.
        stream : io.BytesIO
            Flujo binario donde se guardarán los datos.
        """
        ...

    @property
    def format_id(self) -> list[str]:
        """
        Identificadores formato.

        Devuelve una lista con los identificadores de formato de datos
        manejado por este handler.

        Returns
        -------
        list[str]
            Identificadores del formato de datos.
        """
        ...
