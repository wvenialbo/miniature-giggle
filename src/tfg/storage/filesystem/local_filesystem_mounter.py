import os

from .base_filesystem_mounter import BaseFileSystemMounter


class LocalFileSystemMounter(BaseFileSystemMounter):
    """
    Clase para manejar el sistema de archivos local.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para el sistema de archivos local.  Por defecto
        es el directorio de trabajo actual.

    Attributes
    ----------
    mountpoint : str
        Punto de montaje para el sistema de archivos local.

    Methods
    -------
    is_mounted() -> bool
        Verifica si el sistema de archivos local está montado.
    mount(fail: bool = True) -> bool
        "Monta" el sistema de archivos local (verifica su existencia).
    unmount(fail: bool = True) -> bool
        "Desmonta" el sistema de archivos local (operación no
        necesaria).

    Raises
    ------
    RuntimeError
        Si no se puede "montar" el sistema de archivos local y `fail` es
        True.
    """

    def __init__(self, *, mountpoint: str = os.getcwd()) -> None:
        self.mountpoint = mountpoint

    def __repr__(self) -> str:
        return f"LocalFileSystemMounter(mountpoint='{self.mountpoint}')"

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de archivos local está montado.

        Returns
        -------
        bool
            True si el sistema de archivos local está montado, False en
            caso contrario.
        """
        return os.path.exists(self.mountpoint) and os.path.isdir(
            self.mountpoint
        )

    def mount(self, *, fail: bool = True) -> bool:
        """
        Monta el sistema de archivos local.

        Si no se puede montar el sistema de archivos y `fail` es True,
        se lanza una excepción RuntimeError. Si `fail` es False, se
        emite una advertencia en su lugar.

        Returns
        -------
        bool
            True si el sistema de archivos local está montado después de
            la llamada, False en caso contrario.
        """
        if self.is_mounted():
            return True

        self._report_failure(f"No se pudo montar '{self.mountpoint}'", fail)

        return False

    def unmount(self, *, fail: bool = True) -> bool:  # NOSONAR(S1172)
        """
        Desmonta el sistema de archivos local.

        Si no se puede desmontar el sistema de archivos y `fail` es True,
        se lanza una excepción RuntimeError. Si `fail` es False, se
        emite una advertencia en su lugar.

        Returns
        -------
        bool
            True siempre, ya que no es necesario desmontar el sistema de
            archivos local.
        """
        return True
