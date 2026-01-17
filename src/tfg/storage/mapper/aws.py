from .base import URIMapper

S3_PREFIX = "s3://"
S3_SEPARATOR = "/"
POSIX_SEPARATOR = "/"


class AWSURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en URIs de Amazon Web Services S3.

    Parameters
    ----------
    bucket : str
        Nombre del bucket de S3 que actúa como raíz nativa.

    Attributes
    ----------
    bucket : str
        Nombre del bucket de S3 que actúa como raíz nativa.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def __repr__(self) -> str:
        return f"AWSURIMapper(bucket='{self.bucket}')"

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Parameters
        ----------
        uri : str
            URI nativa absoluta proporcionada por el backend.

        Returns
        -------
        str
            URI genérica absoluta en formato POSIX.
        """
        # uri: s3://my-bucket/base/data/file.csv -> /data/file.csv
        prefix = f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}"
        if not uri.startswith(prefix):
            raise ValueError(
                f"La URI '{uri}' no pertenece al bucket '{self.bucket}'"
            )

        path = uri[len(prefix) :]

        return f"{POSIX_SEPARATOR}{path.lstrip(POSIX_SEPARATOR)}"

    def to_native(self, uri: str) -> str:
        """
        Convierte una ruta lógica en una URI de Amazon Web Services S3.

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
        # uri: /data/file.csv -> s3://my-bucket/base/data/file.csv
        clean_path = uri.lstrip(POSIX_SEPARATOR)
        return f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}{clean_path}"
