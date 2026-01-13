import io
import json
import typing as tp

from .base import DataHandler


class NJSONHandler(DataHandler):
    """
    Handler para múltiples objetos JSON dentro de un solo flujo binario.

    Cada objeto se guarda como un JSON separado, permitiendo almacenar
    colecciones grandes de objetos sin cargar todo en memoria.

    Parameters
    ----------
    indent : int, optional
        Número de espacios para la indentación al guardar JSON. Por
        defecto None (sin indentación).
    ensure_ascii : bool, optional
        Si se asegura que todos los caracteres sean ASCII. Por defecto True.

    Attributes
    ----------
    indent : int | None
        Indentación usada al guardar JSON.
    ensure_ascii : bool
        Controla si se asegura ASCII en el JSON guardado.

    Methods
    -------
    load(stream: tp.BinaryIO) -> dict[str, tp.Any]
        Carga todos los objetos JSON de un flujo y los devuelve como un diccionario.
    save(data: dict[str, tp.Any], stream: tp.BinaryIO) -> None
        Guarda múltiples objetos JSON en un flujo binario.
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
            f"NJSONHandler(indent={self.indent}, "
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
        return NJSONHandler(
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
        )

    def load(self, *, stream: io.BytesIO) -> dict[str, tp.Any]:
        """
        Carga múltiples objetos JSON desde un flujo binario.

        Cada objeto JSON debe estar asociado a una clave única en el
        diccionario final.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los objetos JSON.

        Returns
        -------
        dict[str, tp.Any]
            Diccionario con todos los objetos JSON cargados.
        """
        stream.seek(0)
        result: dict[str, tp.Any] = {}

        text_stream = io.TextIOWrapper(stream, encoding="utf-8")
        try:
            # Intentar leer un objeto JSON por clave
            temp_data = json.load(text_stream)
            if isinstance(temp_data, dict):
                result |= temp_data
            else:
                raise ValueError(
                    "El flujo JSON debe contener un objeto dict raíz"
                )
        except json.JSONDecodeError as e:
            # Si el flujo contiene múltiples objetos JSON secuenciales
            stream.seek(0)
            text_stream = io.TextIOWrapper(stream, encoding="utf-8")
            for line in text_stream:
                if line.strip():
                    obj: tp.Any = json.loads(line)
                    if isinstance(obj, dict):
                        result |= obj
                    else:
                        raise ValueError(
                            "Cada objeto JSON dentro del flujo debe ser un dict"
                        ) from e

        return result

    def save(self, *, data: dict[str, tp.Any], stream: io.BytesIO) -> None:
        """
        Guarda múltiples objetos JSON en un flujo binario.

        Cada clave del diccionario `data` se guarda como un objeto JSON
        independiente dentro del flujo.

        Parameters
        ----------
        data : dict[str, tp.Any]
            Diccionario de objetos JSON a guardar.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los objetos JSON.
        """
        stream.seek(0)
        text_stream = io.TextIOWrapper(
            stream, encoding="utf-8", write_through=True
        )

        for key, obj in data.items():
            json_obj = {key: obj}
            json.dump(
                json_obj,
                text_stream,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
            )
            text_stream.write("\n")  # Separador de objetos

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
        return [".jsonmulti"]
