from .aws import AWSURIMapper
from .base import URIMapper
from .gcs import GCSURIMapper
from .gdrive import GoogleDriveURIMapper
from .generic import GenericURIMapper
from .path import PathURIMapper

__all__ = [
    "AWSURIMapper",
    "GCSURIMapper",
    "GenericURIMapper",
    "GoogleDriveURIMapper",
    "PathURIMapper",
    "URIMapper",
]
