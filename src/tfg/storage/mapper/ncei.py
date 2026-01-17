from ..mapper import URIMapper


class NCEIURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en URLs de NCEI Archive.

    Parameters
    ----------
    base_url : str
        URL base del NCEI Archive.
        Ejemplo: 'https://www.ncei.noaa.gov/data'.

    Attributes
    ----------
    base_url : str
        URL base del NCEI Archive.

    Methods
    -------
    to_native(uri: str) -> str
        Convierte una ruta lógica en una URL absoluta de NCEI.
    to_generic(uri: str) -> str
        Convierte una URL de NCEI en una ruta lógica POSIX.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def to_native(self, uri: str) -> str:
        """
        Convierte una ruta lógica en una URL absoluta de NCEI.

        Parameters
        ----------
        uri : str
            Ruta lógica en formato POSIX.
            Ejemplo: '/data/file.csv'.

        Returns
        -------
        str
            URL absoluta de NCEI.
            Ejemplo: 'https://www.ncei.noaa.gov/data/file.csv'.

        Notes
        -----
        La ruta lógica puede comenzar con '/' o no.
        """
        relative_path = uri.lstrip("/")
        return (
            f"{self.base_url}/{relative_path}"
            if relative_path
            else self.base_url
        )

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URL de NCEI en una ruta lógica POSIX.

        Parameters
        ----------
        uri : str
            URL absoluta de NCEI.
            Ejemplo: 'https://www.ncei.noaa.gov/data/file.csv'.

        Returns
        -------
        str
            Ruta lógica en formato POSIX.
            Ejemplo: '/data/file.csv'.

        Raises
        ------
        ValueError
            Si la URL no pertenece a la base del mapeador.
        """
        if not uri.startswith(self.base_url):
            raise ValueError(
                f"La URL '{uri}' no pertenece a la base '{self.base_url}'"
            )

        path = uri.replace(self.base_url, "", 1)
        return "/" + path.lstrip("/")
