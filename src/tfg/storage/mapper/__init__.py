from .aws import AWSURIMapper
from .base import URIMapper
from .gcs import GCSURIMapper
from .gdrive import GoogleDriveURIMapper
from .generic import GenericURIMapper
from .kaggle import KaggleURIMapper
from .ncei import NCEIURIMapper
from .path import PathURIMapper

__all__ = [
    "AWSURIMapper",
    "GCSURIMapper",
    "GenericURIMapper",
    "GoogleDriveURIMapper",
    "KaggleURIMapper",
    "NCEIURIMapper",
    "PathURIMapper",
    "URIMapper",
]
