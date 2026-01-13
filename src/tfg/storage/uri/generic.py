import pathlib as pl

from .base import URIMapper


class GenericURIMapper(URIMapper):
    """
    Transforma URIs genéricas respecto a una ruta base.

    Parameters
    ----------
    path : str
        Ruta base para las URIs lógicas.

    Methods
    -------
    to_native(uri: str) -> str
        Convierte una URI lógica a una URI nativa.
    to_logical(uri: str) -> str
        Convierte una URI nativa del backend a una lógica.
    """

    def __init__(self, path: str) -> None:
        base_path = pl.PosixPath(f"/{path.lstrip('/')}")
        self.base_path = base_path.resolve(strict=False)

    def __repr__(self) -> str:
        return f"GenericURIMapper(path='{self.base_path}')"

    def __str__(self) -> str:
        return f"{self.base_path}"

    def to_logical(self, uri: str) -> str:
        """
        Convierte una URI nativa a una lógica.

        Parameters
        ----------
        uri : str
            La URI nativa proporcionada por el backend.

        Returns
        -------
        str
            La URI lógica transformada para el usuario.
        """
        path = pl.PosixPath(uri).resolve(strict=False)
        relative_path = path.relative_to(self.base_path)
        return str(relative_path)

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI lógica a una URI nativa.

        Parameters
        ----------
        uri : str
            La URI lógica proporcionada por el usuario.

        Returns
        -------
        str
            La URI nativa transformada para el backend.
        """
        stem = pl.PosixPath(f"/{uri.lstrip('/')}")
        path = str(stem.resolve(strict=False))
        target = self.base_path / path.lstrip("/")
        return str(target.resolve(strict=False))
