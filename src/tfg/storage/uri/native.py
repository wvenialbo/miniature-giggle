import pathlib as pl

from .base import URIMapper


class NativeURIMapper(URIMapper):
    """
    Transforma entre URIs lógicas (del usuario) y nativas (del backend).

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones específicas del backend, mientras exponen URIs lógicas
    consistentes al usuario.  Esto es útil para backends que requieren
    estructuras de URI específicas o prefijos.

    Methods
    -------
    to_native(uri: str) -> str
        Convierte una URI lógica a una URI nativa.
    to_logical(uri: str) -> str
        Convierte una URI nativa del backend a una lógica.
    """

    def __init__(self, path: str) -> None:
        base_path = pl.Path(f"/{path.lstrip('/')}")
        self.base_path = base_path.resolve(strict=True)

    def __repr__(self) -> str:
        return f"NativeURIMapper(path='{self.base_path}')"

    def __str__(self) -> str:
        return f"{self.base_path}"

    def to_logical(self, *, uri: str) -> str:
        """
        Convierte una URI nativa a una lógica.

        Parameters
        ----------
        uri : str
            La URI nativa absoluta proporcionada por el backend.

        Returns
        -------
        str
            La URI lógica relativa transformada para el usuario.
        """
        path = pl.Path(uri).resolve(strict=False)
        relative_path = path.relative_to(self.base_path)
        return str(relative_path)

    def to_native(self, *, uri: str) -> str:
        """
        Convierte una URI lógica a una URI nativa.

        Parameters
        ----------
        uri : str
            La URI lógica (POSIX) proporcionada por el usuario.

        Returns
        -------
        str
            La URI nativa transformada para el backend.
        """
        return str(pl.Path(uri).resolve())
