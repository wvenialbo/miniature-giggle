from .aws import AWSURIMapper
from .base import URIMapper
from .generic import GenericURIMapper
from .google import GoogleDriveURIMapper
from .path import PathURIMapper

__all__ = [
    "AWSURIMapper",
    "GenericURIMapper",
    "GoogleDriveURIMapper",
    "PathURIMapper",
    "URIMapper",
]
