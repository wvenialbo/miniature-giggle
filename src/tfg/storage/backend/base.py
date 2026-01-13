import typing as tp


class StorageBackend(tp.Protocol):
    """
    Protocolo para el backend de almacenamiento.

    Define los métodos requeridos para cualquier implementación de
    backend de almacenamiento, incluyendo operaciones para leer,
    escribir, eliminar y listar archivos.  No conoce rutas lógicas,
    realiza operaciones crudas de E/S sobre una URI física (rutas
    absolutas, claves, etc.).

    Methods
    -------
    delete(uri: str) -> None
        Elimina los datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    read(uri: str) -> bytes
        Lee los datos desde la URI especificada.
    scan(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI especificada.

    Notes
    -----
    Todas las URI pasadas a sus métodos deben ser rutas absolutas o
    claves nativas del backend.  Las URI devueltas por los métodos
    también serán rutas absolutas o claves nativas del backend.
    """

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Elimina archivos u objetos individuales si existen.  No elimina
        contenedores o directorios.  La operación es idempotente, la URI
        puede no existir sin que se genere un error.  `uri` debe ser una
        URI nativa absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        ...

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Verifica si un archivo u objeto existe en la URI dada.  La URI
        debe apuntar a un archivo u objeto individual.  `uri` debe ser
        una URI nativa absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen en la URI dada, False en caso
            contrario.
        """
        ...

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Carga los datos desde la URI dada.  La URI debe apuntar a un
        archivo u objeto individual.  `uri` debe ser una URI nativa
        absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.

        Returns
        -------
        bytes
            Los datos leídos desde la URI dada.
        """
        ...

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista las URI que comienzan con el prefijo especificado.

        Obteniene la lista de todos los objetos cuyas URI comienzan con
        el prefijo dado.  `prefix` debe ser una URI nativa absoluta
        completa, o parcial, válida para el backend.  Devuelve una lista
        de URI nativas absolutas del backend.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URI listadas.

        Returns
        -------
        tp.List[str]
            Una lista de URI que comienzan con el prefijo dado.
        """
        ...

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Guarda los datos en la URI dada.  Al finalizar la operación, la
        URI debe apuntar a un archivo u objeto individual.  `uri` debe
        ser una URI nativa absoluta completa válida para el backend.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir en la URI dada.
        """
        ...
