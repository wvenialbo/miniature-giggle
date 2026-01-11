import typing as tp


class FileSystemMounter(tp.Protocol):
    """
    Protocolo para montar sistemas de archivos.

    Methods
    -------
    get_mountpoint() -> str
        Obtiene el punto de montaje del sistema de archivos.
    is_mounted() -> bool
        Verifica si el sistema de archivos está montado.
    mount(fail: bool = True) -> bool
        Monta el sistema de archivos.
    unmount(fail: bool = True) -> bool
        Desmonta el sistema de archivos.
    """

    def get_mountpoint(self) -> str:
        """
        Obtiene el punto de montaje del sistema de archivos.

        Returns
        -------
        str
            Punto de montaje del sistema de archivos.
        """
        ...

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de archivos está montado.

        Returns
        -------
        bool
            True si el sistema de archivos está montado, False en caso
            contrario.
        """
        ...

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
        ...

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
        ...
