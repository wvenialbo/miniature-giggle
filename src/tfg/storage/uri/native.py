import pathlib as pl

from .base import URIMapper


class NativeURIMapper(URIMapper):
    """
    A URI mapper for native file system paths.

    Parameters
    ----------
    base_path : str, optional
        The base path for the URI mapper. Defaults to the current
        working directory.
    strict : bool, optional
        Whether to raise an error if the base path does not exist.
        Defaults to True.

    Attributes
    ----------
    base_path : pl.Path
        The resolved base path.

    Methods
    -------
    get_base_path() -> str
        Get the base path of the URI mapper.
    relative_to(absolute_uri: str) -> str
        Get the relative URI from an absolute URI.
    resolve(logical_uri: str, strict: bool = False) -> str
        Resolve logical URI to absolute URI.
    """

    def __init__(self, *, base_path: str = ".", strict: bool = True) -> None:
        self.base_path = pl.Path(base_path).resolve(strict=strict)

    def __repr__(self) -> str:
        return f"NativeURIMapper(base_path={self.base_path!r})"

    def get_base_path(self) -> str:
        """
        Get the base path of the URI mapper.

        Returns
        -------
        str
            The base path.
        """
        return str(self.base_path)

    def relative_to(self, *, absolute_uri: str) -> str:
        """
        Get the relative URI from an absolute URI.

        Parameters
        ----------
        absolute_uri : str
            The absolute URI to convert.

        Returns
        -------
        str
            The relative URI.
        """
        return str(pl.Path(absolute_uri).relative_to(self.base_path))

    def resolve(self, *, logical_uri: str, strict: bool = False) -> str:
        """
        Resolve logical URI to absolute URI.

        Parameters
        ----------
        logical_uri : str
            The logical URI to resolve.
        strict : bool, optional
            Whether to raise an error if the resolved path does not
            exist. Defaults to False.

        Returns
        -------
        str
            The resolved absolute URI.
        """
        return str((self.base_path / logical_uri).resolve(strict=strict))
