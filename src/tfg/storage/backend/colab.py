import os

try:
    from google import colab

    def colab_drive_flush_and_unmount() -> None:  # type: ignore
        colab.drive.flush_and_unmount()

    def colab_drive_mount(mountpoint: str) -> None:  # type: ignore
        colab.drive.mount(mountpoint)

    def running_on_colab() -> bool:
        return bool(os.getenv("COLAB_RELEASE_TAG"))

except ImportError:

    def colab_drive_flush_and_unmount() -> None:
        colab_not_found_error()

    def colab_drive_mount(_: str) -> None:
        colab_not_found_error()

    def colab_not_found_error() -> None:
        raise RuntimeError(
            "El módulo 'colab' de Google no está disponible. "
            "Asegúrate de estar ejecutando este código en "
            "Google Colab"
        )

    def running_on_colab() -> bool:
        return False


from .filesystem import FilesystemBackend


class ColabDriveBackend(FilesystemBackend):
    """
    Backend para Google Drive en Google Colab.

    Esta clase proporciona métodos para interactuar con Google Drive
    montado en Google Colab, incluyendo operaciones para leer, escribir,
    eliminar y listar archivos.

    Parameters
    ----------
    mountpoint : str
        Ruta base para todas las URIs. Por defecto es '/content/drive'.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        super().__init__(mountpoint=mountpoint)

    def __repr__(self) -> str:
        return f"ColabDriveBackend(mountpoint='{self.mountpoint}')"

    def _check_ready(self) -> None:
        """
        Verifica si el backend está listo para usarse.

        Raises
        ------
        RuntimeError
            Si el backend no está listo.
        """
        if not running_on_colab():
            colab_not_found_error()

        super()._check_ready()
