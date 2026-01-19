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
