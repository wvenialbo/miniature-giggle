import os
import warnings

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


class ColabFileSystemMounter:
    """
    Clase para montar y desmontar Google Drive en Google Colab.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para Google Drive.  Por defecto es
        "/content/drive".

    Attributes
    ----------
    mountpoint : str
        Punto de montaje para Google Drive.

    Methods
    -------
    is_mounted() -> bool
        Verifica si Google Drive está montado.
    mount(fail: bool = True) -> None
        Monta Google Drive si aún no está montado.
    unmount(fail: bool = True) -> None
        Desmonta Google Drive y guarda todos los cambios.

    Raises
    ------
    RuntimeError
        Si no se puede montar o desmontar Google Drive y `fail` es True.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        if not running_on_colab():
            colab_not_found_error()

        self.mountpoint = mountpoint

    def is_mounted(self) -> bool:
        """
        Verifica si Google Drive está montado.

        Returns
        -------
        bool
            True si Google Drive está montado, False en caso contrario.
        """
        return os.path.exists(self.mountpoint) and os.path.isdir(
            self.mountpoint
        )

    def mount(self, *, fail: bool = True) -> None:
        """
        Monta Google Drive si aún no está montado.

        Si no se puede montar Google Drive y `fail` es True, se lanza
        una excepción RuntimeError. Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede montar Google
            Drive.  Por defecto es True.

        Returns
        -------
        None
        """
        if self.is_mounted():
            return

        colab_drive_mount(self.mountpoint)

        if not self.is_mounted():
            self._report_failure("No se pudo montar Google Drive", fail)

    def unmount(self, *, fail: bool = True) -> None:
        """
        Desmonta Google Drive y guarda todos los cambios.

        Si no se puede desmontar Google Drive y `fail` es True, se lanza
        una excepción RuntimeError. Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede desmontar
            Google Drive.  Por defecto es True.

        Returns
        -------
        None
        """
        if not self.is_mounted():
            return

        colab_drive_flush_and_unmount()

        if self.is_mounted():
            self._report_failure("No se pudo desmontar Google Drive", fail)

    def _report_failure(self, error_message: str, fail: bool) -> None:
        if fail:
            raise RuntimeError(error_message)
        warnings.warn(error_message, RuntimeWarning)
