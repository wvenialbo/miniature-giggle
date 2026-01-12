import pathlib as pl


class URIComposer:
    """
    Clase para componer URIs basadas en un path base.

    Parameters
    ----------
    path : str
        El path base para la composición de URIs.

    Attributes
    ----------
    base_path : pl.PosixPath
        El path base almacenado como un objeto PosixPath.
    """

    def __init__(self, path: str) -> None:
        base_path = pl.PosixPath(f"/{path.lstrip('/')}")
        self.base_path = base_path.resolve(strict=True)

    def __repr__(self) -> str:
        return f"URIComposer(path='{self.base_path}')"

    def __str__(self) -> str:
        return f"{self.base_path}"

    def join(self, path: str) -> str:
        """
        Une el path base con el path proporcionado.

        El path resultante se expresa tomando `base_path` como raíz y se
        resuelve para eliminar referencias redundantes como "." y "..".

        Parameters
        ----------
        path : str
            El path a unir con el path base.

        Returns
        -------
        str
            El path unido y resuelto.
        """
        stem = pl.PosixPath(f"/{path.lstrip('/')}")
        path = str(stem.resolve(strict=False))
        target = self.base_path / path.lstrip("/")
        return str(target.resolve(strict=False))
