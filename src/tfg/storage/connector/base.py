import typing as tp
import warnings


class ConnectionManager(tp.Protocol):
    """
    Protocolo para gestionar la conexión con sistemas de almacenamiento.

    Methods
    -------
    close(fail: bool = True) -> bool
        Cierra la conexión con el sistema de almacenamiento.
    ensure_mounted() -> None
        Asegura que el sistema de almacenamiento esté montado.
    get_mountpoint() -> str
        Obtiene el punto de montaje del sistema de almacenamiento.
    is_mounted() -> bool
        Verifica si el sistema de almacenamiento está montado.
    open(fail: bool = True) -> bool
        Abre la conexión con el sistema de almacenamiento.
    """

    def close(self, *, fail: bool = True) -> bool:
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
        """
        ...

    def ensure_mounted(self) -> None:
        """
        Asegura que el sistema de almacenamiento esté montado.

        Si el sistema de almacenamiento no está montado, lo monta.
        Si ya está montado, no hace nada.

        Returns
        -------
        None
        """
        ...

    def get_mountpoint(self) -> str:
        """
        Obtiene el punto de montaje del sistema de almacenamiento.

        Devuelve la ruta del directorio dentro del sistema de archivos
        local donde se montó el sistema de almacenamiento.

        Returns
        -------
        str
            La ruta del punto de montaje del sistema de almacenamiento.
        """
        ...

    def is_mounted(self) -> bool:
        """
        Verifica si el sistema de almacenamiento está montado.

        Returns
        -------
        bool
            True si el sistema de almacenamiento está montado, False en
            caso contrario.
        """
        ...

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
        """
        ...


class BasicConnectionManager(ConnectionManager):
    """
    Clase base para gestores de conexión con sistemas de almacenamiento.

    Proporciona una implementación básica de algunos métodos del
    protocolo ConnectionManager que pueden ser reutilizados por
    subclases.

    Parameters
    ----------
    mountpoint : str
        Punto de montaje para el sistema de almacenamiento.

    Attributes
    ----------
    mountpoint : str
        Punto de montaje para el sistema de almacenamiento.

    Methods
    -------
    get_mountpoint() -> str
        Obtiene el punto de montaje del sistema de almacenamiento.
    _report_failure(error_message: str, fail: bool) -> None
        Informa de un fallo lanzando una excepción o emitiendo una
        advertencia.
    """

    def __init__(self, *, mountpoint: str) -> None:
        self.mountpoint = mountpoint

    def get_mountpoint(self) -> str:
        """
        Obtiene el punto de montaje del sistema de almacenamiento.

        Devuelve la ruta del directorio dentro del sistema de archivos
        local donde se montó el sistema de almacenamiento.

        Returns
        -------
        str
            La ruta del punto de montaje del sistema de almacenamiento.
        """
        return self.mountpoint

    def _report_failure(self, error_message: str, fail: bool) -> None:
        """
        Informa de un fallo lanzando una excepción o emitiendo una
        advertencia.

        Parameters
        ----------
        error_message : str
            Mensaje de error a utilizar en la excepción o advertencia.
        fail : bool
            Si es True, lanza una excepción RuntimeError con el mensaje
            de error.  Si es False, emite una advertencia RuntimeWarning
            con el mensaje de error.

        Returns
        -------
        None
        """
        if fail:
            raise RuntimeError(error_message)

        warnings.warn(error_message, RuntimeWarning)
