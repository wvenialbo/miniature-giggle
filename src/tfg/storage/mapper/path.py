import pathlib as pl

from .base import URIMapper


class PathURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en rutas del sistema de archivos.

    Convierte entre URI genéricas y rutas absolutas del sistema de
    archivos.

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones nativas específicas, mientras los clientes exponen rutas
    genéricas logicas para el usuario.  Facilitando la interoperabilidad
    entre distintos backends abstrayendo las diferencias estructurales
    en sus modelos de URI.

    Se adopta el formato POSIX/Unix para las URI genéricas, usando '/'
    como separador de componentes de rutas. Las URI lógicas se definen
    respecto a una raíz genérica, que puede corresponder a diferentes
    ubicaciones nativas en cada backend y cliente.  Es decir, el
    parámetro `uri` en los métodos `to_generic` y `to_native` se
    interpreta como una ruta absoluta o una relativa respecto a la raíz
    del sistema de archivos nativo o la raíz lógica genérica,
    respectivamente.

    Attributes
    ----------
    native_root : pathlib.Path
        La raíz absoluta del sistema de archivos nativo.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.

    Notes
    -----
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    """

    def __init__(self) -> None:
        self.native_root = pl.Path("/").resolve(strict=False)

    def __repr__(self) -> str:
        return "PathURIMapper()"

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Parameters
        ----------
        uri : str
            La URI nativa absoluta proporcionada por el backend.

        Returns
        -------
        str
            La URI lógica (genérica absoluta) transformada para el
            usuario.
        """
        return f"/{pl.Path(uri).relative_to(self.native_root).as_posix()}"

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica absoluta a una URI nativa absoluta.

        Parameters
        ----------
        uri : str
            La URI lógica (genérica absoluta) proporcionada por el
            usuario.

        Returns
        -------
        str
            La URI nativa absoluta transformada para el backend.
        """
        return str(self.native_root / uri)


__all__ = ["PathURIMapper"]
