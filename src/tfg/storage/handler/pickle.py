import io
import pickle  # nosec
import typing as tp
import warnings

from .base import DataHandler


class PickleHandler(DataHandler):
    """
    Manejador para archivos pickle (.pkl, .pickle).

    Parameters
    ----------
    protocol : int, optional
        Protocolo de pickle a usar. Por defecto es el protocolo por defecto
        de pickle.

    Atributes
    ---------
    protocol : int
        Protocolo de pickle a usar.

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

    def __init__(self, protocol: int = pickle.DEFAULT_PROTOCOL) -> None:
        self.protocol = protocol

    def __repr__(self) -> str:
        return f"PickleHandler(protocol={self.protocol})"

    def copy(self) -> DataHandler:
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        return PickleHandler(protocol=self.protocol)

    @staticmethod
    def _issue_warning() -> None:
        warnings.warn(
            "El uso de archivos pickle puede ser inseguro. "
            "Asegúrese de que el archivo provenga de una "
            "fuente confiable",
            UserWarning,
        )

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
        self._issue_warning()
        stream.seek(0)

        return pickle.load(stream)  # nosec

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
        self._issue_warning()
        stream.seek(0)
        pickle.dump(data, stream, protocol=self.protocol)
        stream.truncate()

    @property
    def format_id(self) -> list[str]:
        return [".pkl"]
