import typing as tp


class URIMapper(tp.Protocol):
    """
    Transforma entre URI genéricas y URI nativas del backend.

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones nativas específicas, mientras los clientes exponen rutas
    genéricas logicas para el usuario.  Facilitando la interoperabilidad
    entre distintos backends abstrayendo las diferencias estructurales
    en sus modelos de URI.

    Se adopta el formato POSIX/Unix para las URI genéricas, usando '/'
    como separador de componentes de rutas. Las URI lógicas se definen
    respecto a una raíz genérica, que puede corresponder a diferentes
    ubicaciones nativas en cada backend y cliente.  Es decir, el
    parámetro `uri` en los métodos `to_generic` y `to_native` se
    interpreta como una ruta absoluta o una relativa respecto a la raíz
    del sistema de archivos nativo o la raíz lógica genérica,
    respectivamente.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.

    Notes
    -----
    Las implementaciones concretas:

    - Deben definir la lógica de transformación específica en los
      métodos `to_generic` y `to_native`.
    - Pueden requerir el acceso a configuraciones o funcionalidades
      adicionales del backend para realizar las transformaciones
      adecuadamente, como la conversión de una ruta a un identificador.
    - Pueden establecer convenciones específicas con el backend para
      manejar casos especiales, como rutas raíz o prefijos o, por
      ejemplo, cuando un idenficador no puede obtenerse hasta después de
      crear el objeto.
    """

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Parameters
        ----------
        uri : str
            La URI nativa absoluta proporcionada por el backend.

        Returns
        -------
        str
            La URI lógica (genérica absoluta) transformada para el
            usuario.
        """
        ...

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica absoluta a una URI nativa absoluta.

        Parameters
        ----------
        uri : str
            La URI lógica (genérica absoluta) proporcionada por el
            usuario.

        Returns
        -------
        str
            La URI nativa absoluta transformada para el backend.
        """
        ...
