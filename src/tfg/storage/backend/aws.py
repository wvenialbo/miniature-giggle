import typing as tp

import boto3
from botocore.exceptions import ClientError

from ..cache import CacheBase, DummyCache
from .base import StorageBackend

if tp.TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

AWSCache = CacheBase[list[str]]
NoopCache = DummyCache[list[str]]

S3_PREFIX = "s3://"
S3_SEPARATOR = "/"


class AWSBackend(StorageBackend):
    def __init__(
        self,
        bucket: str,
        session: boto3.Session,
        scan_cache: AWSCache | None = None,
    ) -> None:
        self.bucket_name = bucket
        self.s3: "S3Client" = self._create_client(session)
        self.scan_cache: AWSCache = scan_cache or NoopCache()

    def _create_client(self, session: boto3.Session) -> "S3Client":
        return session.client("s3")

    def create_path(self, *, uri: str) -> str:
        # S3 es un espacio plano; no necesita crear directorios.
        # Solo verificamos que la URI sea válida para este backend.
        return uri

    def exists(self, *, uri: str) -> bool:
        bucket, key = self._split_uri(uri)
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def read(self, *, uri: str) -> bytes:
        bucket, key = self._split_uri(uri)
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        except ClientError as e:
            raise FileNotFoundError(
                f"Objeto no encontrado en AWS: '{uri}'"
            ) from e

    def write(self, *, uri: str, data: bytes) -> None:
        bucket, key = self._split_uri(uri)
        # Inferencia simple de ContentType podría ir aquí o en el handler
        self.s3.put_object(Bucket=bucket, Key=key, Body=data)
        # Importante: Invalidar el cache de scan ya que la estructura cambió
        self.scan_cache.clear()

    def scan(self, *, prefix: str) -> list[str]:
        # Intentar recuperar de caché
        cached = self.scan_cache.get(prefix)
        if cached is not None:
            return cached

        bucket, key_prefix = self._split_uri(prefix)
        paginator = self.s3.get_paginator("list_objects_v2")
        results: list[str] = []

        for page in paginator.paginate(Bucket=bucket, Prefix=key_prefix):
            if "Contents" in page:
                results.extend(
                    f"{S3_PREFIX}{bucket}/{obj.get('Key')}"
                    for obj in page["Contents"]
                )
        self.scan_cache.set(prefix, results)
        return results

    def delete(self, *, uri: str) -> None:
        bucket, key = self._split_uri(uri)
        self.s3.delete_object(Bucket=bucket, Key=key)
        self.scan_cache.clear()

    def _split_uri(self, uri: str) -> tuple[str, str]:
        if not uri.startswith(S3_PREFIX):
            raise ValueError(f"URI inválida para AWS: '{uri}'")
        parts = uri[len(S3_PREFIX) :].split(S3_SEPARATOR, 1)
        return parts[0], parts[1] if len(parts) > 1 else ""
