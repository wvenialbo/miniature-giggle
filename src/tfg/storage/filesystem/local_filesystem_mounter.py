import os

from .base_filesystem_mounter import BaseFileSystemMounter


class LocalFileSystemMounter(BaseFileSystemMounter):
    """
    Clase para 'montar' el sistema de archivos local.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para el sistema de archivos local.  Por defecto
        es el directorio de trabajo actual.

    Methods
    -------
    mount(fail: bool = True) -> bool
        Monta el sistema de archivos.
    unmount(fail: bool = True) -> bool
        Desmonta el sistema de archivos.
    """

    def __init__(self, *, mountpoint: str = os.getcwd()) -> None:
        super().__init__(mountpoint=mountpoint)

    def __repr__(self) -> str:
        return f"LocalFileSystemMounter(mountpoint='{self.mountpoint}')"

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

        self._report_failure(f"No se pudo montar '{self.mountpoint}'", fail)

        return False

    def unmount(self, *, fail: bool = True) -> bool:  # NOSONAR(S1172)
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
            llamada, False en caso contrario.  (True siempre, ya que no
            es necesario desmontar el sistema de archivos local.)
        """
        return True
