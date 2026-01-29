"""
Provide package-level metadata and identification constants.

This module retrieves the version information from the package
distribution and defines identifying names used across the system.

Symbols
-------
__version__ : str
    The current version of the package.
__package_id__ : str
    The uppercase identifier for the package.
__package_name__ : str
    The full descriptive name of the package.
__package_root__ : str
    The root module name for the package.

"""

import importlib.metadata

try:
    # "tfg-wvv" debe ser igual al 'name' en tu pyproject.toml
    __version__ = importlib.metadata.version("tfg-wvv")
except importlib.metadata.PackageNotFoundError:
    __version__ = "v0.1.5-dev0"

__package_id__ = "TFG-WVV"

__package_name__ = (
    f"{__package_id__} — Código del proyecto de Trabajo de Fin de Grado"
)

__package_root__ = "tfg"

__all__ = [
    "__package_id__",
    "__package_name__",
    "__package_root__",
    "__version__",
]
