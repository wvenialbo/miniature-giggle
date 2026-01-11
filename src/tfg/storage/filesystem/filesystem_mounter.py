import typing as tp


class FileSystemMounter(tp.Protocol):
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

        Si no se puede desmontar el sistema de archivos y `fail` es True,
        se lanza una excepción RuntimeError. Si `fail` es False, se
        emite una advertencia en su lugar.

        Returns
        -------
        bool
            True si el sistema de archivos está desmontado después de la
            llamada, False en caso contrario.
        """
        ...
