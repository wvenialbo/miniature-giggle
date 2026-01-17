import typing as tp


class URIMapper(tp.Protocol):
    """
    Protocolo para mapeadores de rutas lógicas a URIs nativas.

    Define la interfaz para convertir entre rutas lógicas (genéricas)
    utilizadas por los clientes y identificadores nativos específicos
    del backend de almacenamiento. Trabaja en conjunto con
    `StorageBackend` para proporcionar una capa de abstracción completa
    que permite a los clientes operar con rutas lógicas independientes
    del backend de almacenamiento subyacente.

    Las URI genéricas siguen el formato POSIX/Unix, usando '/' como
    separador de componentes. Estas rutas se definen respecto a una raíz
    lógica que puede corresponder a diferentes ubicaciones nativas en
    cada combinación de backend y cliente.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.

    Notes
    -----
    Dependencias:
        Los recursos necesarios (clientes SDK, sesiones, caché de
        mapeos) son inyectados en el constructor de la implementación
        concreta mediante funciones factoría de orquestación.

    Thread-safety:
        Las implementaciones deben ser thread-safe cuando el backend lo
        permita. Las mismas consideraciones sobre sesiones no
        thread-safe de `StorageBackend` aplican aquí. Las operaciones de
        mapeo deben poder ejecutarse concurrentemente si el SDK del
        backend lo soporta.

    Caché:
        Las implementaciones pueden utilizar un caché de mapeos para
        mejorar el rendimiento cuando la consulta al backend es costosa
        (ejemplo: Google Drive, AWS S3). El caché es de lectura y
        escritura, y puede configurarse con persistencia (ejemplo:
        archivo local) o sin ella, según preferencias del usuario y
        capacidades del backend.

    Flujo de trabajo:
        Para operaciones de lectura (exists, read, delete, scan):
            1. El cliente proporciona una URI genérica.
            2. `to_native()` la convierte a una URI nativa si el objeto
               existe, o devuelve la misma ruta POSIX si no existe.
            3. El orquestador ejecuta la operación correspondiente:
                 - Si se obtuvo una URI nativa, la operación se realiza
                   sobre ella.
                 - Si no se obtuvo una URI nativa (objeto inexistente):
                     * `delete`: es idempotente, no falla.
                     * `exists`: devuelve False.
                     * `read`: falla con FileNotFoundError o similar.
                     * `scan`: no aplica (trabaja con prefijos).

        Para operaciones de escritura (write):
            1. El cliente proporciona una URI genérica.
            2. `to_native()` devuelve la URI nativa (si el objeto
               existe) o la misma ruta POSIX (si no existe).
            3. Si no se obtuvo una URI nativa (objeto nuevo), el
               orquestador llama a `StorageBackend.create_path()` con la
               ruta POSIX para crear los contenedores y obtener una URI
               nativa.
            4. Si ya existe una URI nativa, se omite el paso anterior.
            5. Se ejecuta `write()` con la URI nativa obtenida.
            6. Opcionalmente, se actualiza el caché del URIMapper con el
               nuevo mapeo (depende de la implementación).

    Consideraciones de implementación:
        - Las implementaciones deben definir la lógica de transformación
          específica en los métodos `to_generic()` y `to_native()`.
        - Para objetos existentes, `to_native()` devuelve el ID nativo
          correspondiente.
        - Para objetos inexistentes o nuevos, `to_native()` devuelve la
          misma ruta POSIX o un formato especial que
          `StorageBackend.create_path()` pueda interpretar. La
          distinción entre ambos casos la realiza el orquestador según
          la operación a ejecutar.
        - El mapeo debe ser bidireccional y consistente, pero la
          unicidad depende del backend (ejemplo: Google Drive permite
          nombres duplicados, en cuyo caso se devuelve el primero
          encontrado).
        - No valida la corrección de URI genéricas; esta validación
          ocurre en capas superiores.
        - Los symlinks/aliases son manejados por el backend, no por el
          mapeador.
    """

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Transforma un identificador nativo del backend (clave S3, ID de
        Google Drive, ruta de sistema de archivos) en una ruta lógica
        POSIX para presentación al usuario.

        Parameters
        ----------
        uri : str
            URI nativa absoluta proporcionada por el backend.

            Ejemplos: 's3://bucket/experimentos/data.csv',
                      '1A2B3C4D5E6F' (Google Drive ID),
                      '/mnt/storage/experimentos/data.csv'

        Returns
        -------
        str
            URI genérica absoluta en formato POSIX.

            Ejemplo: '/experimentos/data.csv'

        Raises
        ------
        ValueError
            Si la URI nativa no puede mapearse a una ruta genérica
            (ejemplo: está fuera del alcance configurado).

        Notes
        -----
        Este método se utiliza típicamente después de operaciones de
        listado para presentar al cliente una ruta lógica.
        """
        ...

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica absoluta a una URI nativa absoluta.

        Transforma una ruta lógica POSIX en un identificador nativo del
        backend. Para objetos existentes, devuelve el ID nativo; para
        objetos inexistentes o nuevos, devuelve información que
        `StorageBackend.create_path()` pueda interpretar para generar un
        ID nativo cuando sea necesario.

        Parameters
        ----------
        uri : str
            URI genérica absoluta en formato POSIX.

            Ejemplo: '/experimentos/data.csv'

        Returns
        -------
        str
            URI nativa absoluta (para objetos existentes) o una
            ruta/formato especial (para objetos inexistentes o nuevos)
            que `StorageBackend.create_path()` pueda interpretar.

            Ejemplos:
                - Existente:
                    * 's3://bucket/experimentos/data.csv',
                    * '1A2B3C4D5E6F' (Google Drive ID)
                - Inexistente/Nuevo:
                    * '/experimentos/data.csv' (misma ruta POSIX),
                    * 'path:/experimentos/data.csv' (formato especial)

        Notes
        -----
        - Este método no distingue entre objetos inexistentes y nuevos;
          ambos casos devuelven la misma ruta/formato. La distinción la
          realiza el orquestador según la operación a ejecutar.
        - Se pueden establecer convenciones específicas con el backend
          para manejar casos especiales, como devolver la misma ruta con
          prefijos o formatos especiales que
          `StorageBackend.create_path()` pueda interpretar,
          particularmente cuando un identificador no puede obtenerse
          hasta después de crear el objeto.
        - En backends que permiten nombres duplicados (ejemplo: Google
          Drive), devuelve el primer objeto encontrado con ese nombre.
        - No valida la existencia del objeto; `StorageBackend.exists()`
          debe usarse para verificación explícita.
        """
        ...
