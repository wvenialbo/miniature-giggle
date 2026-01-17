from .base import URIMapper

KAGGLE_PREFIX = "kaggle://"
KAGGLE_SEPARATOR = "/"
POSIX_SEPARATOR = "/"


class KaggleURIMapper(URIMapper):
    """
    Mapeador de rutas lógicas en URIs de la API de Kaggle.

    Parameters
    ----------
    dataset : str
        Identificador del dataset en formato 'owner/dataset-slug'.
        Ejemplo: 'zillow/zecon'.

    Attributes
    ----------
    dataset : str
        Identificador del dataset de Kaggle que actúa como raíz nativa.
    prefix : str
        Prefijo de las URIs nativas para este dataset.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa absoluta a una URI genérica absoluta.
    to_native(uri: str) -> str
        Convierte una URI genérica absoluta a una URI nativa absoluta.
    """

    def __init__(self, dataset: str) -> None:
        self.dataset = dataset
        # Aseguramos que el dataset tenga el formato esperado owner/slug
        if KAGGLE_SEPARATOR not in dataset:
            raise ValueError(
                f"Formato de dataset inválido: '{dataset}'. "
                "Se esperaba 'owner/dataset-slug'."
            )
        self.prefix = f"{KAGGLE_PREFIX}{dataset}{KAGGLE_SEPARATOR}"

    def __repr__(self) -> str:
        return f"KaggleURIMapper(dataset='{self.dataset}')"

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa absoluta a una URI genérica absoluta.

        Parameters
        ----------
        uri : str
            URI nativa absoluta (ej: 'kaggle://owner/dataset/file.csv').

        Returns
        -------
        str
            URI genérica absoluta en formato POSIX.
        """
        if not uri.startswith(self.prefix):
            raise ValueError(
                f"La URI '{uri}' no pertenece al dataset '{self.dataset}'"
            )
        return uri[len(self.prefix) - 1 :]

    def to_native(self, uri: str) -> str:
        """
        Convierte una ruta lógica en una URI de la API de Kaggle.

        Parameters
        ----------
        uri : str
            La URI lógica (genérica absoluta) proporcionada por el
            usuario.

        Returns
        -------
        str
            La URI nativa absoluta transformada (esquema kaggle://).
        """
        clean_path = uri.lstrip(POSIX_SEPARATOR)
        return f"{self.prefix}{clean_path}"
