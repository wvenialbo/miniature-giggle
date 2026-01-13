import io
import json
import typing as tp

from .base import DataHandler


class JSONHandler(DataHandler):
    """
    Handler para archivos JSON (.json).

    Parameters
    ----------
    indent : int, optional
        Número de espacios para la indentación al guardar JSON. Por
        defecto es None (sin indentación).
    ensure_ascii : bool, optional
        Si se asegura que todos los caracteres sean ASCII. Por defecto True.

    Atributes
    ---------
    indent : int | None
        Indentación usada al guardar JSON.
    ensure_ascii : bool
        Controla si se asegura ASCII en el JSON guardado.

    Methods
    -------
    load(stream: tp.BinaryIO) -> tp.Any
        Carga datos JSON desde un flujo binario.
    save(data: tp.Any, stream: tp.BinaryIO) -> None
        Guarda datos JSON en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este handler.
    """

    def __init__(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = True,
    ) -> None:
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def __repr__(self) -> str:
        return (
            f"JSONHandler(indent={self.indent}, "
            f"ensure_ascii={self.ensure_ascii})"
        )

    def copy(self) -> DataHandler:
        """
        Crea una copia del handler de datos.

        Returns
        -------
        DataHandler
            Nueva instancia del handler de datos.
        """
        return JSONHandler(
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
        )

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos JSON desde un flujo binario.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los datos JSON.

        Returns
        -------
        tp.Any
            Datos JSON cargados desde el flujo.
        """
        stream.seek(0)
        return json.load(io.TextIOWrapper(stream, encoding="utf-8"))

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos JSON en un flujo binario.

        Parameters
        ----------
        data : tp.Any
            Datos a guardar en formato JSON.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos JSON.
        """
        stream.seek(0)
        with io.TextIOWrapper(
            stream, encoding="utf-8", write_through=True
        ) as wrapper:
            json.dump(
                data,
                wrapper,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
            )
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
        return [".json"]
