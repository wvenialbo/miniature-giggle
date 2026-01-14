import typing as tp


class StorageBackend(tp.Protocol):
    """
    Protocolo para backends de almacenamiento de datos.

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

    Methods
    -------
    create_path(path: str) -> str
        Crea una ruta o contenedor en el backend de almacenamiento.
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
    Dependencias:
        Los recursos necesarios (clientes SDK, sesiones, credenciales)
        deben ser inyectados en el constructor de la implementación
        concreta, típicamente mediante una función factoría que crea el
        objeto orquestador.

    Thread-safety:
        Las implementaciones deben ser thread-safe en la medida que el
        backend subyacente lo permita. Si el SDK del backend no es
        thread-safe por defecto, la implementación debe garantizar
        seguridad mediante mecanismos de sincronización apropiados.  El
        acceso concurrente a diferentes objetos debe ser soportado
        cuando el SDK lo permita. Las limitaciones específicas deben
        documentarse en la implementación concreta.

    Excepciones:
        - Para operaciones NO soportadas nativamente por el backend, se
          debe lanzar `RuntimeError` (ej: escritura en backend de solo
          lectura).
        - Para errores en operaciones soportadas, deben propagarse las
          excepciones nativas del backend.
        - Operaciones idempotentes (delete, create_path) no deben lanzar
          error cuando el recurso no existe o ya existe respectivamente.

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
        `create_path()` recibe un ID nativo (que indica que el recurso
        ya existe), devuelve el mismo ID. Si recibe una ruta POSIX, crea
        los contenedores necesarios y devuelve el nuevo ID nativo. Este
        ID se utiliza posteriormente en `write()`.
    """

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
            URI nativa absoluta completa válida para el backend.  Ej:
            'ftp://bucket/experimentos/data.csv'.

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
        - Solo devuelve URIs de archivos u objetos individuales, no
          incluye contenedores o directorios vacíos.
        - Maneja internamente toda la paginación del backend.
        - Devuelve resultados completos sin límites de memoria.
        - Para algunos backends (ej: sistemas de archivos), el prefijo
          debe terminar con '/' para listar contenidos de un directorio.
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
