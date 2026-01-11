import os
import warnings


class BaseFileSystemMounter:
    """
    Clase base para montar sistemas de archivos.

    Parameters
    ----------
    mountpoint : str
        Punto de montaje para el sistema de archivos.

    Attributes
    ----------
    mountpoint : str
        Punto de montaje para el sistema de archivos.

    Methods
    -------
    get_mountpoint() -> str
        Obtiene el punto de montaje del sistema de archivos.
    is_mounted() -> bool
        Verifica si el sistema de archivos está montado.
    """

    def __init__(self, *, mountpoint: str) -> None:
        self.mountpoint = mountpoint

    def get_mountpoint(self) -> str:
        """
        Obtiene el punto de montaje del sistema de archivos.

        Returns
        -------
        str
            Punto de montaje del sistema de archivos.
        """
        return self.mountpoint

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de archivos está montado.

        Returns
        -------
        bool
            True si el sistema de archivos está montado, False en caso
            contrario.
        """
        return os.path.exists(self.mountpoint) and os.path.isdir(
            self.mountpoint
        )

    def _report_failure(self, error_message: str, fail: bool) -> None:
        if fail:
            raise RuntimeError(error_message)
        warnings.warn(error_message, RuntimeWarning)
