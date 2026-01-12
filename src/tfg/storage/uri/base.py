import typing as tp


class URIMapper(tp.Protocol):
    """
    A protocol for URI mappers.

    Methods
    -------
    get_base_path() -> str
        Get the base path of the URI mapper.
    relative_to(absolute_uri: str) -> str
        Get the relative URI from an absolute URI.
    resolve(logical_uri: str, strict: bool = False) -> str
        Resolve logical URI to absolute URI.
    """

    def get_base_path(self) -> str:
        """
        Get the base path of the URI mapper.

        Returns
        -------
        str
            The base path.
        """
        ...

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
        ...

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
        ...
