"""
Implement concrete storage backend providers.

This subpackage defines the specific implementations for various storage
technologies, including local disk and major cloud service providers.

Modules
-------
aws : Amazon S3 storage backend.
base : Abstract base protocol for all backends.
filesystem : Local filesystem storage backend.
gcs : Google Cloud Storage backend.
gdrive : Google Drive storage backend.
ncei : National Centers for Environmental Information archive backend.

"""

from .aws import AWSBackend
from .base import StorageBackend
from .filesystem import FilesystemBackend
from .gcs import GCSBackend
from .gdrive import GoogleDriveBackend
from .ncei import NCEIBackend

__all__ = [
    "AWSBackend",
    "FilesystemBackend",
    "GCSBackend",
    "GoogleDriveBackend",
    "NCEIBackend",
    "StorageBackend",
]
