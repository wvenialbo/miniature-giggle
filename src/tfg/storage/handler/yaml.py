import io
import typing as tp

import yaml  # PyYAML

from .base import DataHandler


class YAMLHandler(DataHandler):
    """
    Handler para archivos YAML (.yaml, .yml).

    Parameters
    ----------
    default_flow_style : bool, optional
        Indica si se usa el estilo de flujo compacto o el estilo de bloque
        al guardar YAML. Por defecto False (estilo bloque).
    allow_unicode : bool, optional
        Permite caracteres Unicode al guardar YAML. Por defecto True.

    Attributes
    ----------
    default_flow_style : bool
        Controla el estilo de flujo al guardar YAML.
    allow_unicode : bool
        Indica si se permiten caracteres Unicode al guardar YAML.

    Methods
    -------
    load(stream: tp.BinaryIO) -> tp.Any
        Carga datos YAML desde un flujo binario.
    save(data: tp.Any, stream: tp.BinaryIO) -> None
        Guarda datos YAML en un flujo binario.
    format_id -> list[str]
        Identificadores únicos del formato de datos manejado por este handler.
    """

    def __init__(
        self,
        *,
        default_flow_style: bool = False,
        allow_unicode: bool = True,
    ) -> None:
        self.default_flow_style = default_flow_style
        self.allow_unicode = allow_unicode

    def __repr__(self) -> str:
        return (
            f"YAMLHandler(default_flow_style={self.default_flow_style}, "
            f"allow_unicode={self.allow_unicode})"
        )

    def load(self, *, stream: io.BytesIO) -> tp.Any:
        """
        Carga datos YAML desde un flujo binario.

        Parameters
        ----------
        stream : tp.BinaryIO
            Flujo binario desde el cual cargar los datos YAML.

        Returns
        -------
        tp.Any
            Datos YAML cargados desde el flujo.
        """
        stream.seek(0)
        text_stream = io.TextIOWrapper(stream, encoding="utf-8")
        return yaml.safe_load(text_stream)

    def save(self, *, data: tp.Any, stream: io.BytesIO) -> None:
        """
        Guarda datos YAML en un flujo binario.

        Parameters
        ----------
        data : tp.Any
            Datos a guardar en formato YAML.
        stream : tp.BinaryIO
            Flujo binario donde se guardarán los datos YAML.
        """
        stream.seek(0)
        text_stream = io.TextIOWrapper(
            stream, encoding="utf-8", write_through=True
        )
        yaml.safe_dump(
            data,
            text_stream,
            default_flow_style=self.default_flow_style,
            allow_unicode=self.allow_unicode,
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
        return [".yaml", ".yml"]
