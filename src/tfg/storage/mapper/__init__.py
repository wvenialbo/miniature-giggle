from .aws import AWSURIMapper
from .base import URIMapper
from .gcs import GCSURIMapper
from .generic import GenericURIMapper
from .google import GoogleDriveURIMapper
from .path import PathURIMapper

__all__ = [
    "AWSURIMapper",
    "GCSURIMapper",
    "GenericURIMapper",
    "GoogleDriveURIMapper",
    "PathURIMapper",
    "URIMapper",
]
