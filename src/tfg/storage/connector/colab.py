import os
import pathlib as pl

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


from .base import BasicConnectionManager


class ColabDriveConnectionManager(BasicConnectionManager):
    """
    Gestionar la conexión con Google Drive desde Google Colab.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para el sistema de almacenamiento.  Por
        defecto es "/content/drive".

    Methods
    -------
    close(fail: bool = False) -> bool
        Cierra la conexión con el sistema de almacenamiento.
    ensure_mounted() -> None
        Asegura que el sistema de almacenamiento esté montado.
    is_mounted() -> bool
        Verifica si el sistema de almacenamiento está montado.
    open(fail: bool = False) -> bool
        Abre la conexión con el sistema de almacenamiento.
    """

    def __init__(self, *, mountpoint: str = "/content/drive") -> None:
        super().__init__(mountpoint=mountpoint)

    def __repr__(self) -> str:
        return f"ColabDriveConnectionManager(mountpoint='{self.mountpoint}')"

    def close(self, *, fail: bool = False) -> bool:
        """
        Cierra la conexión con el sistema de almacenamiento.

        Desmonta y cierra la conexión con el sistema de almacenamiento
        local o remoto.

        Si no se puede cerrar la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede cerrar la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            cerrada después de la llamada, False en caso contrario.
        """
        if not self.is_mounted():
            return True

        colab_drive_flush_and_unmount()

        if self.is_mounted():
            self._report_failure("Google Drive no se pudo desmontar", fail)
            return False

        return True

    def ensure_mounted(self) -> None:
        """
        Asegura que el sistema de almacenamiento esté montado.

        Si el sistema de almacenamiento no está montado, lo monta.
        Si ya está montado, no hace nada.

        Returns
        -------
        None
        """
        if not self.is_mounted():
            self.open(fail=True)

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de almacenamiento está montado.

        Returns
        -------
        bool
            True si el sistema de almacenamiento está montado, False en
            caso contrario.
        """
        return running_on_colab() and pl.Path(self.mountpoint).is_mount()

    def open(self, *, fail: bool = False) -> bool:
        """
        Abre la conexión con el sistema de almacenamiento.

        Abre la conexión con el sistema de almacenamiento remoto y lo
        monta en el punto de montaje obtenido por `get_mountpoint()`.

        Si no se puede abrir la conexión y `fail` es True, se lanza una
        excepción RuntimeError.  Si `fail` es False, se emite una
        advertencia en su lugar.

        Parameters
        ----------
        fail : bool, optional
            Si es True, lanza una excepción si no se puede abrir la
            conexión con el sistema de almacenamiento.  Por defecto es
            False.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            abierta después de la llamada, False en caso contrario.
        """
        if self.is_mounted():
            return True

        colab_drive_mount(self.mountpoint)

        if not self.is_mounted():
            self._report_failure(
                f"Google Drive no se pudo montar en '{self.mountpoint}'", fail
            )
            return False

        return True
