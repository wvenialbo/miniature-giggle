import typing as tp


class URIMapper(tp.Protocol):
    """
    Transforma entre URIs genéricas y nativas del backend.

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones nativas específicas del backend, mientras exponen rutas
    genéricas logicas para el usuario.  Esto es útil para backends que
    requieren estructuras de URI específicas o prefijos.

    Se adopta el formato POSIX/Unix para las URI lógicas, utilizando '/'
    como separador de componentes de rutas.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa a una URI genérica.
    to_native(uri: str) -> str
        Convierte una URI genérica a una URI nativa.
    """

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI genérica a una URI nativa.

        Parameters
        ----------
        uri : str
            La URI nativa proporcionada por el backend.

        Returns
        -------
        str
            La URI lógica transformada para el usuario.
        """
        ...

    def to_native(self, uri: str) -> str:
        """
        Convierte una URI genérica a una URI nativa.

        Parameters
        ----------
        uri : str
            La URI lógica proporcionada por el usuario.

        Returns
        -------
        str
            La URI nativa transformada para el backend.
        """
        ...
