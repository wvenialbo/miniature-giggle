import pathlib as pl


class UserURIMapper:
    """
    Transforma entre URIs del usuario y del repositorio.

    Methods
    -------
    to_native(uri: str) -> str
        Convierte una URI lógica a una URI nativa.
    to_logical(uri: str) -> str
        Convierte una URI nativa del backend a una lógica.
    """

    def __init__(self, path: str) -> None:
        base_path = pl.PosixPath(f"/{path.lstrip('/')}")
        self.base_path = base_path.resolve(strict=True)

    def __repr__(self) -> str:
        return f"URIComposer(path='{self.base_path}')"

    def __str__(self) -> str:
        return f"{self.base_path}"

    def to_native(self, *, uri: str) -> str:
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
