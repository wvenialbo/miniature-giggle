import typing as tp


class URIMapper(tp.Protocol):
    """
    Transforma entre URIs lógicas (del usuario) y nativas (del backend).

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones específicas del backend, mientras exponen URIs lógicas
    consistentes al usuario.  Esto es útil para backends que requieren
    estructuras de URI específicas o prefijos.

    Methods
    -------
    to_native(uri: str) -> str
        Convierte una URI lógica a una URI nativa.
    to_logical(uri: str) -> str
        Convierte una URI nativa del backend a una lógica.
    """

    def to_native(self, *, uri: str) -> str:
        """
        Convierte una URI lógica a una URI nativa.

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

    def to_logical(self, *, uri: str) -> str:
        """
        Convierte una URI nativa a una lógica.

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
