import os


class LocalBackend:
    """
    Backend para sistema de archivos local.

    Esta clase proporciona métodos para interactuar con el sistema de
    archivos local, incluyendo operaciones para leer, escribir, eliminar
    y listar archivos.

    Parameters
    ----------
    base_path : str | None
        Ruta base para todas las URIs. Si no se proporciona, se usará la
        ruta actual.

    Attributes
    ----------
    base_path : str
        Ruta base para todas las URIs.

    Methods
    -------
    delete(uri: str) -> None
        Elimina datos en la URI especificada.
    exists(uri: str) -> bool
        Verifica si los datos existen en la URI especificada.
    list_files(prefix: str) -> list[str]
        Lista las URIs que comienzan con el prefijo especificado.
    read(uri: str) -> bytes
        Lee datos desde la URI especificada.
    write(uri: str, data: bytes) -> None
        Escribe datos en la URI especificada.
    """

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = base_path or ""

    def delete(self, *, uri: str) -> None:
        """
        Elimina datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a eliminar.
        """
        path = self._resolve_path(uri)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, *, uri: str) -> bool:
        """
        Verifica si los datos existen en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a verificar.

        Returns
        -------
        bool
            True si los datos existen, False en caso contrario.
        """
        path = self._resolve_path(uri)
        return os.path.exists(path)

    def list_files(self, *, prefix: str) -> list[str]:
        """
        Lista las URIs que comienzan con el prefijo especificado.

        Parameters
        ----------
        prefix : str
            El prefijo para filtrar las URIs.

        Returns
        -------
        tp.List[str]
            Una lista de URIs que comienzan con el prefijo dado.
        """
        base_dir = self._resolve_path(prefix)

        if not (os.path.exists(base_dir) and os.path.isdir(base_dir)):
            raise ValueError(
                "La ruta especificada no existe "
                f"o no es un directorio: {base_dir}"
            )

        uris: list[str] = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.base_path)
                uris.append(relative_path)

        return uris

    def read(self, *, uri: str) -> bytes:
        """
        Lee datos desde la URI especificada.

        Parameters
        ----------
        uri : str
            La URI de los datos a leer.
        """
        path = self._resolve_path(uri)
        with open(path, "rb") as f:
            return f.read()

    def _resolve_path(self, uri: str) -> str:
        """
        Resuelve la URI a una ruta de archivo absoluta.

        Parameters
        ----------
        uri : str
            La URI a resolver.

        Returns
        -------
        str
            La ruta de archivo absoluta correspondiente a la URI.
        """
        return os.path.join(self.base_path, uri) if self.base_path else uri

    def write(self, *, uri: str, data: bytes) -> None:
        """
        Escribe datos en la URI especificada.

        Parameters
        ----------
        uri : str
            La URI donde se escribirán los datos.
        data : bytes
            Los datos a escribir.
        """
        path = self._resolve_path(uri)

        # Crear directorios si no existen
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            f.write(data)
