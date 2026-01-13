import pathlib as pl

from .base import URIMapper


class PathURIMapper(URIMapper):
    """
    Transforma entre URI genéricas y rutas del sistema de archivos.

    Convierte entre URI lógicas y rutas absolutas del sistema de
    archivos utilizando una ruta base especificada como raíz.

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
        válida en el sistema de archivos local. Puede ser relativa o
        absoluta y es resuelta a una ruta absoluta durante la
        inicialización.

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

    Notes
    -----
    - La clase utiliza la biblioteca `pathlib` para manejar rutas de
      archivos de manera eficiente y portátil.
    """

    def __init__(self, base_path: str) -> None:
        cwd = pl.Path().resolve(strict=False)
        crd = cwd / base_path
        self.base_path = f"/{crd.relative_to(crd.anchor).as_posix()}"

    def __repr__(self) -> str:
        return f"PathURIMapper(base_path='{self.base_path}')"

    def to_generic(self, uri: str) -> str:
        """
        Convierte una URI nativa a una URI genérica.

        Parameters
        ----------
        uri : str
            La URI nativa proporcionada por el sistema de archivos.

        Returns
        -------
        str
            La URI lógica transformada para el usuario.
        """
        root_path = pl.Path(self.root).resolve(strict=False)
        native_path = pl.Path(uri).relative_to(root_path)
        generic_path = pl.PurePosixPath(f"/{native_path.as_posix()}")
        return str(generic_path)

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
            La URI nativa transformada para el sistema de archivos.
        """
        generic_path = self.root / uri.lstrip("/")
        native_path = pl.Path(generic_path)
        return str(native_path.resolve(strict=False))

    @property
    def root(self) -> pl.PurePosixPath:
        """Ruta base absoluta utilizada para las conversiones de URI."""
        return pl.PurePosixPath(f"/{self.base_path.lstrip('/')}")
