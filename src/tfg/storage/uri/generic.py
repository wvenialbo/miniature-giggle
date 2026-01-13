import pathlib as pl

from .base import URIMapper


class GenericURIMapper(URIMapper):
    """
    Transforma URI genéricas respecto a una ruta base.

    Convierte entre URI lógicas y respecto a una ruta base especificada
    como raíz.  La finalidad es proporcionar una abstracción simple para
    manejar rutas relativas dentro de un espacio de nombres definido.
    Este mapeador no realiza conversiones complejas, sino que
    simplemente ajusta las rutas relativas a una base fija.  Es usado en
    componentes de alto nivel que requieren una referencia común para
    las rutas, como, por ejemplo, en manejadores de repositorios.

    Los mapeadores de URI permiten que los backends almacenen datos en
    ubicaciones nativas específicas del backend, mientras exponen rutas
    genéricas logicas para el usuario.  Esto es útil para backends que
    requieren estructuras de URI específicas o prefijos.

    Se adopta el formato POSIX/Unix para las URI lógicas, utilizando '/'
    como separador de componentes de rutas.

    Parameters
    ----------
    base_path : str
        Ruta base para las URI genéricas.  Debe ser una ruta genérica
        válida en el backend. Puede ser relativa o absoluta y es
        resuelta a una ruta absoluta durante la inicialización.

    Attributes
    ----------
    base_path : pathlib.Path
        La ruta base absoluta utilizada para las conversiones de URI.
        Es una ruta en formato POSIX.

    Methods
    -------
    to_generic(uri: str) -> str
        Convierte una URI nativa a una URI genérica.
    to_native(uri: str) -> str
        Convierte una URI genérica a una URI nativa.
    """

    def __init__(self, base_path: str) -> None:
        cwd = pl.Path().resolve(strict=False)
        crd = cwd / base_path
        self.base_path = f"/{crd.relative_to(crd.anchor).as_posix()}"

    def __repr__(self) -> str:
        return f"GenericURIMapper(base_path='{self.base_path}')"

    def to_logical(self, uri: str) -> str:
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
        native_root = pl.PurePosixPath(self.base_path)
        generic_path = pl.PurePosixPath(uri).relative_to(native_root)
        return str(generic_path)

    def to_native(self, uri: str) -> str:
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
        generic_root = pl.PurePosixPath(self.base_path)
        native_path = generic_root / uri.lstrip("/")
        return str(native_path)
