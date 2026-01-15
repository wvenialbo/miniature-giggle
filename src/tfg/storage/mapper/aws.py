from ..mapper import URIMapper

S3_PREFIX = "s3://"
S3_SEPARATOR = "/"
POSIX_SEPARATOR = "/"


class AWSURIMapper(URIMapper):
    """
    Mapeador determinista para AWS S3.

    Convierte entre rutas lógicas y URIs nativas
    s3://bucket/prefix/path.
    """

    def __init__(self, bucket: str, base_prefix: str = "") -> None:
        self.bucket = bucket
        # Normalizamos el prefijo para que no termine en / innecesariamente
        self.base_prefix = base_prefix.strip(POSIX_SEPARATOR)

    def to_generic(self, uri: str) -> str:
        # uri: s3://my-bucket/base/data/file.csv -> /data/file.csv
        prefix = f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}"
        if not uri.startswith(prefix):
            raise ValueError(
                f"La URI '{uri}' no pertenece al bucket '{self.bucket}'"
            )

        path = uri[len(prefix) :]
        if self.base_prefix and path.startswith(self.base_prefix):
            path = path[len(self.base_prefix) :]

        return f"{POSIX_SEPARATOR}{path.lstrip(POSIX_SEPARATOR)}"

    def to_native(self, uri: str) -> str:
        # uri: /data/file.csv -> s3://my-bucket/base/data/file.csv
        clean_path = uri.lstrip(POSIX_SEPARATOR)
        full_key = f"{self.base_prefix}{S3_SEPARATOR}{clean_path}"
        return f"{S3_PREFIX}{self.bucket}{S3_SEPARATOR}{full_key}"
