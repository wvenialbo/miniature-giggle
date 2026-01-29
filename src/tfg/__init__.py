"""
TFG-WVV: Cloud top diurnal cycle characterisation code
======================================================

Provide the functionality required to execute and replicate the
research project experiments:

Characterisation of the cloud top diurnal cycle of tropical cyclones in
the North Atlantic Ocean using machine learning and satellite data.

Subpackages
-----------
imaging : Image processing and container classes.
storage : Data persistence and caching systems.

Modules
-------
dataset : Dataset management and iteration.
info : Package metadata and identification.

"""

from . import dataset, imaging, storage
from .info import (
    __package_id__,
    __package_name__,
    __package_root__,
    __version__,
)

__all__ = [
    "__package_id__",
    "__package_name__",
    "__package_root__",
    "__version__",
    "dataset",
    "imaging",
    "storage",
]
