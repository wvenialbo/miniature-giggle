"""
Provide core storage handlers and backend selection functionality.

Modules
-------
aws : AWS storage interface.
colab : Google Colab storage interface.
gcs : Google Cloud Storage (GCS) interface.
gcsauth : GCS authentication utilities.
gdauth : Google Drive authentication utilities.
gdrive : Google Drive storage interface.
gutils : Generic Google API utilities.
local : Local filesystem storage interface.
ncei : NOAA NCEI archive access interface.
utils : Storage core utilities.

Functions
---------
release_colab_drive(*, fail=False)
    Unmount Google Drive and flush pending writes in Colab.
use_aws_cloud(*, bucket, root_path=None, cache_file=None,
              expire_after=None, **kwargs)
    Create a data source context for Amazon Web Services S3 bucket.
use_colab_drive(*, root_path=None)
    Create a data source context for Google Drive in Colab.
use_gcs_cloud(*, bucket, root_path=None, cache_file=None,
              expire_after=None, **kwargs)
    Create a data source context for a Google Cloud Storage bucket.
use_google_drive(*, root_path=None, credentials=None,
                 cache_file=None, expire_after=None)
    Create a data source context for Google Drive access.
use_local_drive(*, root_path=None)
    Create a data source context for the local filesystem.
use_ncei_archive(*, dataset_path, root_path=None,
                 cache_file=None, expire_after=None)
    Create a data source context for NOAA's NCEI Archive server.

"""

from .aws import use_aws_cloud
from .colab import release_colab_drive, use_colab_drive
from .gcs import use_gcs_cloud
from .gdrive import use_google_drive
from .local import use_local_drive
from .ncei import use_ncei_archive


__all__ = [
    "release_colab_drive",
    "use_aws_cloud",
    "use_colab_drive",
    "use_gcs_cloud",
    "use_google_drive",
    "use_local_drive",
    "use_ncei_archive",
]
