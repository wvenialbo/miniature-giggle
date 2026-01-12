import typing as tp


class StorageBackend(tp.Protocol):
    """
    Protocolo para el backend de almacenamiento.

    Define los métodos requeridos para cualquier implementación de
    backend de almacenamiento. No conoce rutas lógicas, realiza
    operaciones crudas de E/S sobre una URI física.

    Methods
    -------
    delete(uri: str) -> None
        Elimina los datos en la URI física especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI física especificada.
    content(prefix: str) -> list[str]
        Lista las URI físicas que comienzan con el prefijo especificado.
    read(uri: str) -> bytes
        Lee los datos desde la URI física especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI física especificada.
    """

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI física especificada.

        Elimina archivos u objetos individuales si existen. No elimina
        contenedores o directorios. La operación es idempotente.

        Parameters
        ----------
        uri : str
            La URI física de los datos a eliminar.
        """
        ...

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        ...

    def content(self, *, prefix: str) -> list[str]:
        """
        Lista las URI físicas que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI físicas.

        Returns
        -------
        tp.List[str]
            Una lista de URI físicas que comienzan con el prefijo dado.
        """
        ...

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física de los datos a leer.
        """
        ...

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI física especificada.

        Parameters
        ----------
        uri : str
            La URI física donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        ...
