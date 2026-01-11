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

    def delete(self, uri: str) -> None:
        """
        Elimina datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        ...

    def exists(self, uri: str) -> bool:
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

    def list_files(self, prefix: str) -> list[str]:
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

    def read(self, uri: str) -> bytes:
        """
        Lee datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        """
        ...

    def write(self, uri: str, data: bytes) -> None:
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
