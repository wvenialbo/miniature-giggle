from .base import URIMapper


# Constantes de protocolo para GCS
_GCS_PREFIX = "gs://"
_GCS_SEPARATOR = "/"
_POSIX_SEPARATOR = "/"


class GCSURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en URIs de Google Cloud Storage.

    Convierte entre rutas genéricas absolutas (POSIX) y URIs nativas
    de Google Cloud Storage con el formato 'gs://bucket/path'.

    Este mapeador es determinista y no requiere realizar llamadas a la
    API de Google Cloud, ya que la estructura de objetos en GCS es
    plana y basada en prefijos.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de GCS que actúa como raíz nativa.

    Attributes
    ----------
    bucket : str
        Nombre del bucket de GCS que actúa como raíz nativa.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.
    """

    def __init__(self, *, bucket: str) -> None:
        self.bucket = bucket

    def __repr__(self) -> str:
        return f"GCSURIMapper(bucket='{self.bucket}')"

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa de GCS a una URI genérica absoluta.

        Transforma una cadena 'gs://bucket/path/to/obj' en una ruta
        lógica '/path/to/obj'.

        Parameters
        ----------
        uri : str
            URI nativa absoluta (ej: 'gs://mi-bucket/datos/file.csv').

        Returns
        -------
        str
            URI genérica absoluta en formato POSIX (ej:
            '/datos/file.csv').

        Raises
        ------
        ValueError
            Si la URI no pertenece al bucket configurado o no comienza
            con el prefijo 'gs://'.
        """
        prefix = f"{_GCS_PREFIX}{self.bucket}{_GCS_SEPARATOR}"

        if not uri.startswith(prefix):
            raise ValueError(
                f"La URI '{uri}' no es válida para "
                f"el bucket de GCS: '{self.bucket}'"
            )

        # Extraemos la ruta eliminando el prefijo del bucket
        path = uri[len(prefix) :]

        # Aseguramos que comience con el separador POSIX
        return f"{_POSIX_SEPARATOR}{path.lstrip(_POSIX_SEPARATOR)}"

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica absoluta a una URI nativa de GCS.

        Transforma una ruta lógica '/datos/file.csv' en la URI
        nativa 'gs://mi-bucket/datos/file.csv'.

        Parameters
        ----------
        uri : str
            URI genérica absoluta en formato POSIX.

        Returns
        -------
        str
            URI nativa absoluta de GCS.
        """
        # Limpiamos el separador inicial para evitar doble slash tras el
        # bucket
        clean_path = uri.lstrip(_POSIX_SEPARATOR)

        return f"{_GCS_PREFIX}{self.bucket}{_GCS_SEPARATOR}{clean_path}"


__all__ = ["GCSURIMapper"]
