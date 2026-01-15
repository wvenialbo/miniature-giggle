import io
import typing as tp

from .base import DataHandler


class BypassHandler(DataHandler):
    """
    Manejador genérico para archivos binarios.

    Methods
    -------
    load(stream: tp.BinaryIO) -> tp.Any
        Carga datos pickle desde un flujo binario.
    save(data: tp.Any, stream: tp.BinaryIO) -> None
        Guarda datos pickle en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este
        handler.
    """

    def __repr__(self) -> str:
        return "BypassHandler()"

    def copy(self) -> DataHandler:
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        return BypassHandler()

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos pickle desde un stream de bytes.

        Parameters
        ----------
        stream : io.BytesIO
            Stream de bytes desde donde se cargarán los datos.

        Returns
        -------
        Any
            Datos cargados desde el stream.
        """
        stream.seek(0)
        return stream.read()

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos pickle en un stream de bytes.

        Parameters
        ----------
        data : Any
            Datos a guardar.
        stream : io.BytesIO
            Stream de bytes donde se guardarán los datos.

        Returns
        -------
        None
        """
        stream.seek(0)
        stream.write(data)
        stream.truncate()

    @property
    def format_id(self) -> list[str]:
        return [".*"]
