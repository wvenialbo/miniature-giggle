from .base import URIMapper

S3_PREFIX = "s3://"
S3_SEPARATOR = "/"
POSIX_SEPARATOR = "/"


class AWSURIMapper(URIMapper):
    """
    Mapeador determinista para AWS S3.

    Convierte entre rutas lógicas y URIs nativas
    s3://bucket/prefix/path.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def to_generic(self, uri: str) -> str:
        # uri: s3://my-bucket/base/data/file.csv -> /data/file.csv
        prefix = f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}"
        if not uri.startswith(prefix):
            raise ValueError(
                f"La URI '{uri}' no pertenece al bucket '{self.bucket}'"
            )

        path = uri[len(prefix) :]

        return f"{POSIX_SEPARATOR}{path.lstrip(POSIX_SEPARATOR)}"

    def to_native(self, uri: str) -> str:
        # uri: /data/file.csv -> s3://my-bucket/base/data/file.csv
        clean_path = uri.lstrip(POSIX_SEPARATOR)
        return f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}{clean_path}"
