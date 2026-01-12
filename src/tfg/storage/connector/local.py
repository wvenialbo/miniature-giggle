import pathlib as pl

from .base import BasicConnectionManager


class LocalConnectionManager(BasicConnectionManager):
    """
    Gestionar la conexión con el sistema de almacenamiento local.

    Parameters
    ----------
    mountpoint : str, optional
        Punto de montaje para el sistema de almacenamiento.  Por
        defecto es "/".

    Methods
    -------
    close(fail: bool = True) -> bool
        Cierra la conexión con el sistema de almacenamiento.
    ensure_mounted() -> None
        Asegura que el sistema de almacenamiento esté montado.
    is_mounted() -> bool
        Verifica si el sistema de almacenamiento está montado.
    open(fail: bool = True) -> bool
        Abre la conexión con el sistema de almacenamiento.
    """

    def __init__(self, *, mountpoint: str = "/") -> None:
        super().__init__(mountpoint=mountpoint)

        self._already_mounted = False

    def __repr__(self) -> str:
        return f"LocalConnectionManager(mountpoint='{self.mountpoint}')"

    def close(self, *, fail: bool = True) -> bool:  # NOSONAR(S1172)
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
            True.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            cerrada después de la llamada, False en caso contrario.

        Notes
        -----
        Dado que el sistema de almacenamiento es local, esta operación
        siempre debería tener éxito y devolver True.
        """
        if self._already_mounted:
            self._already_mounted = False
            return True

        self._report_failure(
            f"El sistema de almacenamiento local en "
            f"'{self.mountpoint}' no estaba montado",
            fail,
        )

        # El sistema de almacenamiento local siempre debería estar
        # montado, y la operación siempre debería tener éxito, pero
        # devolvemos False en caso de que el estado sea inconsistente.
        return self.is_mounted()

    def ensure_mounted(self) -> None:
        """
        Asegura que el sistema de almacenamiento esté montado.

        Si el sistema de almacenamiento no está montado, lo monta.  Si
        ya está montado, no hace nada.

        Returns
        -------
        None

        Notes
        -----
        Dado que el sistema de almacenamiento es local, esta operación
        siempre debería tener éxito.
        """
        if not self._already_mounted:
            self.open(fail=True)

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de almacenamiento está montado.

        Explícitamente verifica si el punto de montaje existe y es un
        directorio.

        Returns
        -------
        bool
            True si el sistema de almacenamiento está montado, False en
            caso contrario.

        Notes
        -----
        Dado que el sistema de almacenamiento es local, esta operación
        siempre debería devolver True.
        """
        return pl.Path(self.mountpoint).is_dir()

    def open(self, *, fail: bool = True) -> bool:
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
            True.

        Returns
        -------
        bool
            True si la conexión con el sistema de almacenamiento está
            abierta después de la llamada, False en caso contrario.

        Notes
        -----
        Dado que el sistema de almacenamiento es local, esta operación
        siempre debería tener éxito.
        """
        if self._already_mounted:
            # should be fail=False because it's already mounted?
            self._report_failure(
                "El sistema de almacenamiento local ya está "
                f"montado en '{self.mountpoint}'",
                fail,
            )
            return True

        if not self.is_mounted():
            self._report_failure(
                "El sistema de almacenamiento local no se pudo montar "
                f"en '{self.mountpoint}'",
                fail,
            )
            return False

        self._already_mounted = True

        return True
