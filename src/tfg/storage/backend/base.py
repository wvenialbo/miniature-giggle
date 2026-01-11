import typing as tp


class StorageBackend(tp.Protocol):
    """
    Protocolo para el backend de almacenamiento.

    Define los métodos requeridos para cualquier implementación de
    backend de almacenamiento.

    Methods
    -------
    delete(uri: str) -> None
        Elimina datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    list_files(prefix: str) -> list[str]
        Lista las URIs que comienzan con el prefijo especificado.
    read(uri: str) -> bytes
        Lee datos desde la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe datos en la URI especificada.
    """

    def delete(self, *, uri: str) -> None:
        """
        Elimina datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        ...

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        ...

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las URIs que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URIs.

        Returns
        -------
        tp.List[str]
            Una lista de URIs que comienzan con el prefijo dado.
        """
        ...

    def read(self, *, uri: str) -> bytes:
        """
        Lee datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        """
        ...

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        ...


class MountableStorageBackend(tp.Protocol):

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
