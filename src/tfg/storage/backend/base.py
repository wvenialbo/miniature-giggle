import collections.abc as col
import typing as tp


class StorageBackend(tp.Protocol):
    """
    Protocolo para backends de almacenamiento de datos crudos.

    Define la interfaz requerida para cualquier implementación de
    backend de almacenamiento utilizado por la librería.  Las
    operaciones son de bajo nivel: lectura, escritura, eliminación y
    listado sobre URIs nativas del backend (rutas absolutas, claves,
    etc.).

    Las implementaciones concretas no realizan cálculos de
    identificadores lógicos; reciben URIs precalculadas por un
    `URIMapper` en capas superiores.  La única excepción es
    `create_path()`, que acepta rutas genéricas para creación de
    contenedores.

    Attributes
    ----------
    read_only : bool
        Indica si el backend es de solo lectura.

    Methods
    -------
    create_path(uri: str) -> str
        Crea una ruta o contenedor en el backend de almacenamiento.
    delete(uri: str) -> None
        Elimina los datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    read(uri: str) -> bytes
        Lee los datos desde la URI especificada.
    read_chunks(uri: str, chunk_size: int = 1MiB) -> Iterable[bytes]
        Lee los datos desde la URI especificada de forma segmentada.
    scan(prefix: str) -> list[str]
        Lista las URI que comienzan con el prefijo especificado.
    size(uri: str) -> int
        Obtiene el tamaño en bytes del objeto en la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe los datos en la URI especificada.

    Notes
    -----
    Dependencias:
        Los recursos necesarios (clientes SDK, sesiones, credenciales)
        deben inyectarse en el constructor de la implementación concreta,
        típicamente mediante una función factoría que cree el objeto
        orquestador.

    Thread-safety:
        Las implementaciones deben ser thread-safe en la medida en que el
        backend subyacente lo permita. Si el SDK del backend no es
        thread-safe por defecto, la implementación debe garantizar
        seguridad mediante mecanismos de sincronización apropiados.  El
        acceso concurrente a diferentes objetos debe ser soportado
        cuando el SDK lo permita. Las limitaciones específicas deben
        documentarse en la implementación concreta.

    Excepciones:
        - Para operaciones NO soportadas nativamente por el backend, se
          debe lanzar `RuntimeError` (ejemplo: escritura en backend de
          solo lectura).
        - Para errores en operaciones soportadas, deben propagarse las
          excepciones nativas del backend (ejemplo: BotoCoreError para
          AWS, GoogleCloudError para Google Cloud).
        - Las operaciones idempotentes (delete, create_path) no deben
          lanzar error cuando el recurso no existe o ya existe,
          respectivamente.

    Paginación:
        `scan()` debe manejar internamente toda la paginación del
        backend, devolviendo la lista completa de URIs. No hay límites
        de memoria o tiempo en esta versión de la librería.

    URIs:
        Todas las URIs recibidas (excepto en `create_path()`) son
        nativas del backend y absolutas. Las URIs devueltas también son
        nativas y absolutas.

    Flujo de creación:
        Las capas superiores utilizan un `URIMapper` para convertir
        rutas lógicas en URIs nativas. Si el `URIMapper` no encuentra un
        ID existente, devuelve la ruta POSIX original. Luego, el
        orquestador llama a `create_path()` con este valor. Si
        `create_path()` recibe un ID nativo (lo que indica que el
        recurso ya existe), devuelve el mismo ID. Si recibe una ruta
        POSIX, crea los contenedores necesarios y devuelve el nuevo ID
        nativo. Este ID se utiliza posteriormente en `write()`.
    """

    def create_path(self, *, uri: str) -> str:
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
        uri : str
            Puede ser un ID nativo del backend (si el recurso ya existe)
            o una ruta genérica (POSIX). Ej:
            'experimentos/2024/dataset1'.

        Returns
        -------
        str
            URI nativa absoluta del contenedor creado o existente en el
            backend.  Ej: 's3://bucket/experimentos/2024/dataset1/' o la
            clave equivalente.

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de creación de
            contenedores.

        Notes
        -----
        - Operación idempotente: si el contenedor ya existe (o se recibe
          un ID nativo), no se realiza ninguna acción y se devuelve la
          URI correspondiente.
        - Para backends que requieren contenedores preexistentes, estos
          deben existir previamente; este método crea solo "prefijos" o
          "directorios virtuales".
        """
        ...

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Elimina archivos u objetos individuales. No elimina contenedores
        o directorios completos.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
            Ejemplo: 's3://bucket/experimentos/data.csv'.

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de eliminación.

        Notes
        -----
        - Operación idempotente: si la URI no existe, no se genera
          error.
        - No debe utilizarse para eliminar contenedores/directorios.
        """
        ...

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
        ...

    def read(self, *, uri: str) -> bytes:
        """
        Lee los datos desde la URI especificada.

        Carga los datos desde la URI dada en un bloque único, todo el
        contenido de una vez.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        bytes
            Contenido binario del archivo u objeto.

        Raises
        ------
        FileNotFoundError
            Si la URI no existe.
        RuntimeError
            Si el backend no soporta operaciones de lectura.
        """
        ...

    def read_chunks(
        self, *, uri: str, chunk_size: int = 1024 * 1024
    ) -> col.Iterable[bytes]:
        """
        Lee los datos desde la URI especificada de forma segmentada.

        Permite procesar archivos grandes sin cargarlos por completo en
        RAM y facilita el reporte de progreso en tiempo real.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        chunk_size : int, optional
            Tamaño sugerido de cada fragmento en bytes. Debe ser un
            entero positivo con valor mínimo de 1MiB. Por defecto 1MiB.

        Yields
        ------
        bytes
            Fragmentos del contenido binario del archivo.

        Raises
        ------
        FileNotFoundError
            Si la URI no existe.
        RuntimeError
            Si el backend no soporta operaciones de lectura o streaming.
        """
        ...

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

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de listado.

        Notes
        -----
        - Solo devuelve URIs de archivos u objetos individuales; no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        - Para algunos backends (ej: sistemas de archivos), el prefijo
          debe terminar con '/' para listar contenidos de un directorio.
        """
        ...

    def size(self, *, uri: str) -> int:
        """
        Obtiene el tamaño en bytes del objeto en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.

        Returns
        -------
        int
            Tamaño en bytes.
        """
        ...

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Parameters
        ----------
        uri : str
            URI nativa absoluta completa válida para el backend.
        data : bytes
            Contenido binario a escribir.

        Raises
        ------
        RuntimeError
            Si el backend no soporta operaciones de escritura.
        PermissionError
            Si no se tienen permisos de escritura.

        Notes
        -----
        - Si el contenedor padre no existe, el comportamiento depende
          del backend. Algunos lo crearán automáticamente, otros
          fallarán.  Se recomienda llamar a `create_path()` primero.
        - Operación atómica: o se escriben todos los datos o falla.
        - Al finalizar una operación exitosa, la URI debe apuntar a un
          archivo u objeto individual.
        """
        ...

    @property
    def read_only(self) -> bool:
        """
        Indica si el backend es de solo lectura.

        Returns
        -------
        bool
            True si el backend no soporta operaciones de escritura o
            eliminación, False en caso contrario.
        """
        ...


class ReadOnlyBackend(StorageBackend):
    """
    Implementación base para backends de solo lectura.

    Attributes
    ----------
    read_only : bool
        Indica si el backend es de solo lectura. Siempre True.

    Methods
    -------
    create_path(uri: str) -> str
        No soportado. Lanza RuntimeError.
    delete(uri: str) -> None
        No soportado. Lanza RuntimeError.
    write(uri: str, data: bytes) -> None
        No soportado. Lanza RuntimeError.
    """

    _RO_MSG = "Este backend es de solo lectura."

    def create_path(self, *, uri: str) -> str:
        """
        Crea una ruta o contenedor en el backend de almacenamiento.

        Notes
        -----
        El backend no soporta operaciones de creación de rutas.
        Lanza PermissionError.
        """
        raise PermissionError(self._RO_MSG)

    def delete(self, *, uri: str) -> None:
        """
        Elimina los datos en la URI especificada.

        Notes
        -----
        El backend no soporta operaciones de eliminación. Lanza
        PermissionError.
        """
        raise PermissionError(self._RO_MSG)

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe los datos en la URI especificada.

        Notes
        -----
        El backend no soporta operaciones de escritura. Lanza
        PermissionError.
        """
        raise PermissionError(self._RO_MSG)

    @property
    def read_only(self) -> bool:
        return True


class ReadWriteBackend(StorageBackend):
    """
    Implementación base para backends de lectura y escritura.

    Attributes
    ----------
    read_only : bool
        Indica si el backend es de solo lectura. Siempre False.
    """

    @property
    def read_only(self) -> bool:
        return False
