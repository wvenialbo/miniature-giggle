import pathlib as pl

from .base import URIMapper


class NativeURIMapper(URIMapper):
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
        root = f"/{crd.relative_to(crd.anchor).as_posix()}"
        self.base_path = root.rstrip("/")
        self.native_root = pl.Path(self.base_path).resolve(strict=False)

    def __repr__(self) -> str:
        return f"NativeURIMapper(base_path='{str(self.base_path)}')"

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
        return f"/{pl.Path(uri).relative_to(self.native_root).as_posix()}"

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
        return str(
            pl.Path(f"{self.base_path}/{uri.lstrip('/')}").resolve(
                strict=False
            )
        )
