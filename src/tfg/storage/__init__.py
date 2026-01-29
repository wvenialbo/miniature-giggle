"""
Implement the storage and persistence layer for the project.

This subpackage provides a multi-backend storage abstraction, including
local filesystem, cloud providers (AWS, GCS), and specialised archives
(NCEI). It also includes caching and mapping functionalities.

Subpackages
-----------
backend : Concrete storage backend implementations.
cache : Data caching systems (timed, GDrive).
core : Global storage configuration and context management.
datasource : High-level data access and service abstractions.
mapper : Path and object mapping for various backends.

"""

from . import backend, cache, core, datasource, mapper
from .core import (
    release_colab_drive,
    use_aws_cloud,
    use_colab_drive,
    use_gcs_cloud,
    use_google_drive,
    use_local_drive,
    use_ncei_archive,
)

__all__ = [
    "backend",
    "cache",
    "core",
    "datasource",
    "mapper",
    "release_colab_drive",
    "use_aws_cloud",
    "use_colab_drive",
    "use_gcs_cloud",
    "use_google_drive",
    "use_local_drive",
    "use_ncei_archive",
]
