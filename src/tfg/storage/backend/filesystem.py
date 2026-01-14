import pathlib as pl

from .base import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Backend de almacenamiento para el sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones de E/S para leer, escribir,
    eliminar y listar archivos.  No conoce rutas lógicas, realiza
    operaciones crudas de E/S sobre una ruta nativa absoluta.

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
    - Todas las URI pasadas a sus métodos deben ser rutas absolutas
      nativas del sistema de archivos.  Las URI devueltas por los
      métodos también serán rutas absolutas nativas del sistema de
      archivos.
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    - Asegura que los directorios intermedios necesarios se creen al
      escribir datos para emular el comportamiento típico de un backend
      de almacenamiento de objetos.
    """

    def __repr__(self) -> str:
        return "FilesystemBackend()"

    def create_path(self, *, path: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

        Este método puede recibir dos tipos de entrada:
            1. Un ID nativo del backend (cuando el recurso ya existe).
            2. Una ruta POSIX (cuando el recurso no existe y se va a
               crear).

        - En el primer caso, el método es idempotente y devuelve el
          mismo ID.
        - En el segundo caso, crea recursivamente todos los contenedores
          intermedios necesarios, emulando el comportamiento de `mkdir
          -p`.  Esta operación es llamada por capas superiores antes de
          `write()` para garantizar que exista el contenedor destino.

        Parameters
        ----------
        path : str
            Puede ser un ID nativo del backend (si el recurso ya existe)
            o una ruta genérica (POSIX). Ej:
            'experimentos/2024/dataset1'.

        Returns
        -------
        str
            URI nativa absoluta del contenedor creado o existente en el
            backend.  Ej: 's3://bucket/experimentos/2024/dataset1/' o la
            clave equivalente.

        Notes
        -----
        - Operación idempotente: si el contenedor ya existe (o se recibe
          un ID nativo), no se realiza ninguna acción y se devuelve la
          URI correspondiente.
        - Para backends que requieren contenedores preexistentes, estos
          deben existir previamente; este método crea solo "prefijos" o
          "directorios virtuales".
        """
        target = _check_uri(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return str(target)

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Elimina archivos u objetos individuales. No elimina contenedores
        o directorios completos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.  Ej:
            'ftp://bucket/experimentos/data.csv'.

        Notes
        -----
        - Operación idempotente: si la URI no existe, no se genera
          error.
        - No debe utilizarse para eliminar contenedores/directorios.
        """
        path = _check_uri(uri)
        if path.is_file():
            path.unlink(missing_ok=True)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Verifica la existencia de un archivo u objeto individual, no de
        contenedores o prefijos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bool
            True si existe un archivo u objeto en la URI, False en caso
            contrario (incluyendo cuando la URI apunta a un contenedor o
            no existe).
        """
        path = _check_uri(uri)
        return path.exists()

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bytes
            Contenido binario del archivo u objeto.
        """
        path = _check_uri(uri)
        return path.read_bytes()

    def scan(self, *, prefix: str) -> list[str]:
        """
        Lista las URI que comienzan con el prefijo especificado.

        Este método debe manejar internamente la paginación del backend
        y devolver una lista completa de URIs que coinciden con el
        prefijo.

        Parameters
        ----------
        prefix : str
            Prefijo de URI nativa absoluta (completa o parcial) válida
            para el backend. Puede incluir o no el separador de
            contenedor.

        Returns
        -------
        list[str]
            Lista de URIs nativas absolutas que comienzan con el
            prefijo.  Solo incluye archivos/objetos, no contenedores
            vacíos.

        Notes
        -----
        - Solo devuelve URIs de archivos u objetos individuales, no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        - Para algunos backends (ej: sistemas de archivos), el prefijo
          debe terminar con '/' para listar contenidos de un directorio.
        """
        path = _check_uri(prefix)
        base = path.parent

        files = [
            str(entry)
            for entry in base.glob(f"{path.name}*")
            if entry.is_file()
        ]

        folders = [
            entry for entry in base.glob(f"{path.name}*") if entry.is_dir()
        ]

        return files + [
            str(entry)
            for folder in folders
            for entry in folder.rglob("*")
            if entry.is_file()
        ]

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        data : bytes
            Contenido binario a escribir.

        Notes
        -----
        - Si el contenedor padre no existe, el comportamiento depende
          del backend. Algunos lo crearán automáticamente, otros
          fallarán.  Se recomienda llamar a `create_path()` primero.
        - Operación atómica: o se escriben todos los datos o falla.
        - Al finalizar una operación exitosa, la URI debe apuntar a un
          archivo u objeto individual.
        """
        target = _check_uri(uri)
        target.write_bytes(data)


def _check_uri(uri: str) -> pl.Path:
    """Verifica que la URI sea una ruta absoluta válida."""
    path = pl.Path(uri)
    if not path.is_absolute():
        raise ValueError(
            f"El prefijo debe ser una ruta absoluta. Se recibió: '{uri}'. "
            "Posible error en la capa superior (URIMapper o DataContext)."
        )
    return path
