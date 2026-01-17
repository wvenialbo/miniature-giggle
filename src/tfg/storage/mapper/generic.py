import pathlib as pl


class GenericURIMapper:
    """
    Mapeador de rutas lógicas respecto a una ruta base.

    Convierte entre URI genéricas absolutas y relativas (lógicas)
    respecto a una ruta base fija especificada como raíz.  La finalidad
    es proporcionar una abstracción simple para manejar rutas relativas
    dentro de un espacio de nombres definido.  Es usado en componentes
    de capas altas que requieren una referencia común para las rutas,
    como, por ejemplo, en manejadores de repositorios o fuentes de
    datos.

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

    def to_relative(self, uri: str) -> str:
        """
        Convierte una URI absoluta a una URI relativa (lógica).

        Parameters
        ----------
        uri : str
            La URI absoluta proporcionada por el backend.

        Returns
        -------
        str
            La URI relativa (lógica) transformada para el usuario.
        """
        native_root = pl.PurePosixPath(self.base_path)
        generic_path = pl.PurePosixPath(uri).relative_to(native_root)
        return f"/{str(generic_path)}"

    def to_absolute(self, uri: str) -> str:
        """
        Convierte una URI relativa (lógica) a una URI absoluta.

        Parameters
        ----------
        uri : str
            La URI relativa (lógica) proporcionada por el usuario.

        Returns
        -------
        str
            La URI absoluta transformada para el backend.
        """
        generic_root = pl.PurePosixPath(self.base_path)
        native_path = generic_root / uri.lstrip("/")
        return str(native_path)
