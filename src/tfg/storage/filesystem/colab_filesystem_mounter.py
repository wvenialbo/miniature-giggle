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


from .base_filesystem_mounter import BaseFileSystemMounter


class ColabFileSystemMounter(BaseFileSystemMounter):
    """
    Clase para montar Google Drive en Google Colab.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para Google Drive.  Por defecto es
        "/content/drive".

    Methods
    -------
    mount(fail: bool = True) -> bool
        Monta el sistema de archivos.
    unmount(fail: bool = True) -> bool
        Desmonta el sistema de archivos.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        if not running_on_colab():
            colab_not_found_error()

        super().__init__(mountpoint=mountpoint)

    def __repr__(self) -> str:
        return f"ColabFileSystemMounter(mountpoint='{self.mountpoint}')"

    def mount(self, *, fail: bool = True) -> bool:
        """
        Monta el sistema de archivos.

        Si no se puede montar el sistema de archivos y `fail` es True,
        se lanza una excepción RuntimeError. Si `fail` es False, se
        emite una advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede montar el
            sistema de archivos.  Por defecto es True.

        Returns
        -------
        bool
            True si el sistema de archivos está montado después de la
            llamada, False en caso contrario.
        """
        if self.is_mounted():
            return True

        colab_drive_mount(self.mountpoint)

        if not self.is_mounted():
            self._report_failure(
                f"No se pudo montar Google Drive en '{self.mountpoint}'", fail
            )
            return False

        return True

    def unmount(self, *, fail: bool = True) -> bool:
        """
        Desmonta el sistema de archivos.

        Si no se puede desmontar el sistema de archivos y `fail` es
        True, se lanza una excepción RuntimeError. Si `fail` es False,
        se emite una advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede desmontar el
            sistema de archivos.  Por defecto es True.

        Returns
        -------
        bool
            True si el sistema de archivos está desmontado después de la
            llamada, False en caso contrario.
        """
        if not self.is_mounted():
            return True

        colab_drive_flush_and_unmount()

        if self.is_mounted():
            self._report_failure("No se pudo desmontar Google Drive", fail)
            return False

        return True
