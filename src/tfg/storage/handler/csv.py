import csv
import io
import typing as tp

from .base import DataHandler


class CSVHandler(DataHandler):
    """
    Handler para archivos CSV (.csv).

    Parameters
    ----------
    delimiter : str, optional
        Carácter delimitador entre columnas. Por defecto es ','.
    quotechar : str, optional
        Carácter usado para encerrar campos que contienen delimitadores.
        Por defecto es '"'.
    has_header : bool, optional
        Indica si el CSV contiene fila de cabecera. Por defecto True.

    Atributes
    ---------
    delimiter : str
        Carácter delimitador usado al leer y guardar CSV.
    quotechar : str
        Carácter de comillas usado al leer y guardar CSV.
    has_header : bool
        Indica si el CSV contiene fila de cabecera.

    Methods
    -------
    load(stream: tp.BinaryIO) -> list[dict[str, str]] | list[list[str]]
        Carga datos CSV desde un flujo binario.
    save(data: list[dict[str, str]] | list[list[str]], stream: tp.BinaryIO) -> None
        Guarda datos CSV en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este handler.
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
    ) -> None:
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.has_header = has_header

    def __repr__(self) -> str:
        return (
            f"CSVHandler(delimiter={self.delimiter!r}, "
            f"quotechar={self.quotechar!r}, has_header={self.has_header})"
        )

    def copy(self) -> DataHandler:
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        return CSVHandler(
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            has_header=self.has_header,
        )

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos CSV desde un flujo binario.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los datos CSV.

        Returns
        -------
        list[dict[str, str]] | list[list[str]]
            Lista de filas cargadas desde el CSV. Si `has_header` es True,
            cada fila es un diccionario {columna: valor}, sino es lista de strings.
        """
        stream.seek(0)
        text_stream = io.TextIOWrapper(stream, encoding="utf-8")
        if self.has_header:
            reader = csv.DictReader(
                text_stream, delimiter=self.delimiter, quotechar=self.quotechar
            )
        else:
            reader = csv.reader(
                text_stream, delimiter=self.delimiter, quotechar=self.quotechar
            )

        return list(reader)

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos CSV en un flujo binario.

        Parameters
        ----------
        data : list[dict[str, str]] | list[list[str]]
            Datos a guardar en formato CSV.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos CSV.
        """
        stream.seek(0)
        text_stream = io.TextIOWrapper(
            stream, encoding="utf-8", write_through=True
        )

        if self.has_header and data and isinstance(data[0], dict):
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(
                text_stream,
                fieldnames=fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            writer.writeheader()
        else:
            writer = csv.writer(
                text_stream,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
        writer.writerows(data)
        stream.truncate()

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
        return [".csv"]
